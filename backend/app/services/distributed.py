from __future__ import annotations

import asyncio
import logging
from collections import deque
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from uuid import uuid4

from sqlalchemy import func
from sqlalchemy.exc import SQLAlchemyError
from sqlmodel import Session, select

from backend.app.api.websocket import emit_proxy_added, emit_stats
from backend.app.models.proxy import Proxy
from backend.app.schemas.proxy import ProxyRead
from backend.app.schemas.worker import WorkerJobRead, WorkerProxyResult
from backend.app.services.runtime import finish_cycle, update_runtime_stats

logger = logging.getLogger(__name__)


@dataclass
class WorkerAssignment:
    job: WorkerJobRead
    worker_id: str | None = None
    assigned_at: datetime | None = None


@dataclass
class WorkerClientStats:
    worker_id: str
    last_seen: datetime
    assigned_total: int = 0
    in_flight: int = 0
    reported: int = 0
    valid: int = 0
    stored: int = 0


class DistributedCheckQueue:
    def __init__(self) -> None:
        self._lock = asyncio.Lock()
        self._pending: deque[WorkerAssignment] = deque()
        self._assigned: dict[str, WorkerAssignment] = {}
        self._workers_seen: dict[str, datetime] = {}
        self._worker_clients: dict[str, WorkerClientStats] = {}
        self._reported = 0
        self._valid = 0
        self._stored = 0

    async def enqueue(self, proxies: list[Proxy]) -> None:
        async with self._lock:
            self._pending.clear()
            self._assigned.clear()
            self._worker_clients.clear()
            self._reported = 0
            self._valid = 0
            self._stored = 0
            for proxy in proxies:
                self._pending.append(
                    WorkerAssignment(
                        job=WorkerJobRead(
                            job_id=uuid4().hex,
                            ip=proxy.ip,
                            port=proxy.port,
                            type=proxy.type,
                        )
                    )
                )
            self._update_runtime_locked()

    async def claim(self, worker_id: str, capacity: int, assignment_timeout_seconds: int) -> list[WorkerJobRead]:
        async with self._lock:
            self._requeue_stale_locked(assignment_timeout_seconds)
            worker = self._touch_worker_locked(worker_id)
            jobs: list[WorkerJobRead] = []
            for _ in range(min(capacity, len(self._pending))):
                assignment = self._pending.popleft()
                assignment.worker_id = worker_id
                assignment.assigned_at = datetime.now(UTC)
                self._assigned[assignment.job.job_id] = assignment
                worker.assigned_total += 1
                worker.in_flight += 1
                jobs.append(assignment.job)
            self._update_runtime_locked()
            return jobs

    async def report(self, session: Session, worker_id: str, results: list[WorkerProxyResult]) -> tuple[int, int, int]:
        accepted = 0
        alive = 0
        stored = 0
        async with self._lock:
            worker = self._touch_worker_locked(worker_id)
            for result in results:
                assignment = self._assigned.pop(result.job_id, None)
                if assignment is None or assignment.worker_id != worker_id:
                    continue
                accepted += 1
                worker.reported += 1
                worker.in_flight = max(worker.in_flight - 1, 0)
                self._reported += 1
                if result.status != "alive":
                    continue

                alive += 1
                worker.valid += 1
                self._valid += 1
                proxy = session.exec(select(Proxy).where(Proxy.ip == result.ip, Proxy.port == result.port)).first()
                if proxy is None:
                    proxy = Proxy(ip=result.ip, port=result.port)
                proxy.type = result.type
                proxy.status = "alive"
                proxy.latency_ms = result.latency_ms
                proxy.last_checked = datetime.now(UTC)
                session.add(proxy)
                try:
                    session.commit()
                except SQLAlchemyError:
                    session.rollback()
                    continue
                session.refresh(proxy)
                stored += 1
                worker.stored += 1
                self._stored += 1
                await emit_proxy_added(ProxyRead.model_validate(proxy).model_dump(mode="json"))

            self._update_runtime_locked()

        total_stock = session.exec(select(func.count()).select_from(Proxy)).one()
        valid_stock = session.exec(select(func.count()).select_from(Proxy).where(Proxy.status == "alive")).one()
        update_runtime_stats(total_stock=total_stock, valid_stock=valid_stock)
        if accepted:
            await emit_stats()
        if self.is_empty:
            finish_cycle("idle")
            await emit_stats()
            logger.info(
                "Distributed worker queue finished: %s reported, %s valid, %s stored",
                self._reported,
                self._valid,
                self._stored,
            )
        return accepted, alive, stored

    async def stats(self) -> tuple[int, int]:
        async with self._lock:
            return len(self._pending), len(self._assigned)

    @property
    def is_empty(self) -> bool:
        return not self._pending and not self._assigned

    def _requeue_stale_locked(self, assignment_timeout_seconds: int) -> None:
        threshold = datetime.now(UTC) - timedelta(seconds=assignment_timeout_seconds)
        stale_ids = [
            job_id
            for job_id, assignment in self._assigned.items()
            if assignment.assigned_at is not None and assignment.assigned_at < threshold
        ]
        for job_id in stale_ids:
            assignment = self._assigned.pop(job_id)
            if assignment.worker_id and assignment.worker_id in self._worker_clients:
                worker = self._worker_clients[assignment.worker_id]
                worker.in_flight = max(worker.in_flight - 1, 0)
            assignment.worker_id = None
            assignment.assigned_at = None
            self._pending.appendleft(assignment)

    def _touch_worker_locked(self, worker_id: str) -> WorkerClientStats:
        now = datetime.now(UTC)
        self._workers_seen[worker_id] = now
        worker = self._worker_clients.get(worker_id)
        if worker is None:
            worker = WorkerClientStats(worker_id=worker_id, last_seen=now)
            self._worker_clients[worker_id] = worker
        worker.last_seen = now
        return worker

    def _active_workers_locked(self) -> int:
        threshold = datetime.now(UTC) - timedelta(minutes=2)
        return sum(1 for seen_at in self._workers_seen.values() if seen_at >= threshold)

    def _worker_clients_payload_locked(self) -> list[dict[str, object]]:
        threshold = datetime.now(UTC) - timedelta(minutes=2)
        clients = sorted(self._worker_clients.values(), key=lambda worker: worker.last_seen, reverse=True)
        return [
            {
                "worker_id": worker.worker_id,
                "active": worker.last_seen >= threshold,
                "last_seen": worker.last_seen.isoformat(),
                "assigned_total": worker.assigned_total,
                "in_flight": worker.in_flight,
                "reported": worker.reported,
                "valid": worker.valid,
                "stored": worker.stored,
            }
            for worker in clients
        ]

    def _update_runtime_locked(self) -> None:
        update_runtime_stats(
            phase="distributed_testing" if self._pending or self._assigned else "idle",
            queued=len(self._pending) + len(self._assigned),
            tested=self._reported,
            valid=self._valid,
            stored=self._stored,
            worker_pending=len(self._pending),
            worker_assigned=len(self._assigned),
            worker_active=self._active_workers_locked(),
            worker_reported=self._reported,
            worker_valid=self._valid,
            worker_stored=self._stored,
            worker_clients=self._worker_clients_payload_locked(),
        )


distributed_queue = DistributedCheckQueue()
