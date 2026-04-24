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
    pass


class ProxyUpdate(BaseModel):
    type: str | None = None
    country: str | None = None
    anonymity: str | None = None
    status: str | None = None


class ProxyRead(ProxyBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    latency_ms: float | None = None
    last_checked: datetime | None = None
    status: str


class ProxyList(BaseModel):
    items: list[ProxyRead]
    total: int
    page: int
    page_size: int


class BatchTestRequest(BaseModel):
    ids: list[int]


class ProgressEvent(BaseModel):
    tested: int
    total: int
    valid: int
