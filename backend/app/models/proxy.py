from __future__ import annotations

from datetime import datetime

from sqlalchemy import UniqueConstraint
from sqlmodel import Field, SQLModel


class Proxy(SQLModel, table=True):
    __table_args__ = (UniqueConstraint("ip", "port", name="uq_proxy_ip_port"),)

    id: int | None = Field(default=None, primary_key=True)
    ip: str = Field(index=True)
    port: int = Field(index=True)
    type: str = Field(default="http", index=True)
    country: str | None = Field(default=None, index=True)
    anonymity: str | None = Field(default=None, index=True)
    latency_ms: float | None = None
    last_checked: datetime | None = None
    status: str = Field(default="unknown", index=True)

