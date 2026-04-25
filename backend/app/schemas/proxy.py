from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ProxyBase(BaseModel):
    ip: str
    port: int = Field(ge=1, le=65535)
    type: str = "http"
    country: str | None = None
    anonymity: str | None = None


class ProxyCreate(ProxyBase):
    test_now: bool = True


class ProxyBulkCreate(BaseModel):
    proxies: str = Field(min_length=1)
    type: str = "http"
    country: str | None = None
    anonymity: str | None = None
    test_now: bool = False


class ProxyBulkResult(BaseModel):
    added: int
    updated: int
    skipped: int
    total_parsed: int


class ProxyRead(ProxyBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    latency_ms: float | None = None
    last_checked: datetime | None = None
    status: str
    is_manual: bool = False


class ProxyList(BaseModel):
    items: list[ProxyRead]
    total: int
    page: int
    page_size: int


class ProxyStats(BaseModel):
    total: int
    alive: int
    dead: int
    unknown: int
    to_test: int = 0
    cycle_tested: int = 0
    cycle_valid: int = 0
    cycle_active: bool = False
    phase: str = "idle"
    source: str | None = None
    scraped: int = 0
    queued: int = 0
    tested: int = 0
    valid: int = 0
    stored: int = 0
    valid_stock: int = 0
    total_stock: int = 0
    worker_pending: int = 0
    worker_assigned: int = 0
    worker_active: int = 0
    worker_reported: int = 0
    worker_valid: int = 0
    worker_stored: int = 0
    worker_clients: list[dict] = Field(default_factory=list)
    avg_latency_ms: float | None = None


class ProgressEvent(BaseModel):
    tested: int
    total: int
    valid: int
