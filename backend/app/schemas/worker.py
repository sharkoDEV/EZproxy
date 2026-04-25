from __future__ import annotations

from pydantic import BaseModel, Field


class WorkerClaimRequest(BaseModel):
    worker_id: str = Field(min_length=1, max_length=128)
    password: str = Field(min_length=1)
    capacity: int = Field(default=100, ge=1, le=1000)


class WorkerJobRead(BaseModel):
    job_id: str
    ip: str
    port: int
    type: str


class WorkerClaimResponse(BaseModel):
    jobs: list[WorkerJobRead]
    timeout: float
    test_urls: list[str]


class WorkerProxyResult(BaseModel):
    job_id: str
    ip: str
    port: int
    type: str
    status: str
    latency_ms: float | None = None


class WorkerReportRequest(BaseModel):
    worker_id: str = Field(min_length=1, max_length=128)
    password: str = Field(min_length=1)
    results: list[WorkerProxyResult]


class WorkerReportResponse(BaseModel):
    accepted: int
    alive: int
    stored: int
    pending: int
    assigned: int
