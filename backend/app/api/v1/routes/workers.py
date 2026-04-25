from __future__ import annotations

import hmac

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

from backend.app.api.v1.deps import get_session
from backend.app.core.config import get_settings
from backend.app.schemas.worker import (
    WorkerClaimRequest,
    WorkerClaimResponse,
    WorkerReportRequest,
    WorkerReportResponse,
)
from backend.app.services.distributed import distributed_queue

router = APIRouter(prefix="/workers", tags=["workers"])


def require_worker_password(password: str) -> None:
    expected = get_settings().config.workers.password
    if not hmac.compare_digest(password, expected):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid worker password")


@router.post("/claim", response_model=WorkerClaimResponse)
async def claim_worker_jobs(payload: WorkerClaimRequest) -> WorkerClaimResponse:
    settings = get_settings()
    require_worker_password(payload.password)
    jobs = await distributed_queue.claim(
        worker_id=payload.worker_id,
        capacity=min(payload.capacity, settings.config.workers.claim_size),
        assignment_timeout_seconds=settings.config.workers.assignment_timeout_seconds,
    )
    test_urls = list(dict.fromkeys([settings.config.test.url, *settings.config.test.urls]))
    return WorkerClaimResponse(jobs=jobs, timeout=settings.config.test.timeout, test_urls=test_urls)


@router.post("/report", response_model=WorkerReportResponse)
async def report_worker_jobs(
    payload: WorkerReportRequest,
    session: Session = Depends(get_session),
) -> WorkerReportResponse:
    require_worker_password(payload.password)
    accepted, alive, stored = await distributed_queue.report(session, payload.worker_id, payload.results)
    pending, assigned = await distributed_queue.stats()
    return WorkerReportResponse(
        accepted=accepted,
        alive=alive,
        stored=stored,
        pending=pending,
        assigned=assigned,
    )
