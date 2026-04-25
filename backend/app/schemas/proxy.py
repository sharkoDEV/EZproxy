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
    avg_latency_ms: float | None = None


class ProgressEvent(BaseModel):
    tested: int
    total: int
    valid: int
