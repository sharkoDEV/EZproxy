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


class DistributedCheckQueue:
    def __init__(self) -> None:
        self._lock = asyncio.Lock()
        self._pending: deque[WorkerAssignment] = deque()
        self._assigned: dict[str, WorkerAssignment] = {}
        self._workers_seen: dict[str, datetime] = {}
        self._reported = 0
        self._valid = 0
        self._stored = 0

    async def enqueue(self, proxies: list[Proxy]) -> None:
        async with self._lock:
            self._pending.clear()
            self._assigned.clear()
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
            self._workers_seen[worker_id] = datetime.now(UTC)
            jobs: list[WorkerJobRead] = []
            for _ in range(min(capacity, len(self._pending))):
                assignment = self._pending.popleft()
                assignment.worker_id = worker_id
                assignment.assigned_at = datetime.now(UTC)
                self._assigned[assignment.job.job_id] = assignment
                jobs.append(assignment.job)
            self._update_runtime_locked()
            return jobs

    async def report(self, session: Session, worker_id: str, results: list[WorkerProxyResult]) -> tuple[int, int, int]:
        accepted = 0
        alive = 0
        stored = 0
        async with self._lock:
            self._workers_seen[worker_id] = datetime.now(UTC)
            for result in results:
                assignment = self._assigned.pop(result.job_id, None)
                if assignment is None or assignment.worker_id != worker_id:
                    continue
                accepted += 1
                self._reported += 1
                if result.status != "alive":
                    continue

                alive += 1
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
            assignment.worker_id = None
            assignment.assigned_at = None
            self._pending.appendleft(assignment)

    def _active_workers_locked(self) -> int:
        threshold = datetime.now(UTC) - timedelta(minutes=2)
        return sum(1 for seen_at in self._workers_seen.values() if seen_at >= threshold)

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
        )


distributed_queue = DistributedCheckQueue()
