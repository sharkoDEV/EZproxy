from __future__ import annotations

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy import func
from sqlmodel import Session, col, select

from backend.app.api.v1.deps import get_session
from backend.app.api.v1.routes.admin import require_admin
from backend.app.api.websocket import emit_proxy_added, emit_stats
from backend.app.models.proxy import Proxy
from backend.app.schemas.proxy import (
    ProxyCreate,
    ProxyList,
    ProxyRead,
    ProxyStats,
)
from backend.app.services.pipeline import update_stock_stats
from backend.app.services.runtime import runtime_stats
from backend.app.services.tester import test_proxy
from backend.app.services.utils import normalize_proxy_type

router = APIRouter(prefix="/proxies", tags=["proxies"])


def filtered_proxy_statement(
    type: str | None = None,  # noqa: A002
    country: str | None = None,
    anonymity: str | None = None,
    max_latency: float | None = None,
    search: str | None = None,
):
    statement = select(Proxy)
    if type:
        statement = statement.where(Proxy.type == type)
    if country:
        statement = statement.where(Proxy.country == country)
    if anonymity:
        statement = statement.where(Proxy.anonymity == anonymity)
    if max_latency is not None:
        statement = statement.where(Proxy.latency_ms <= max_latency)
    if search:
        statement = statement.where(col(Proxy.ip).contains(search))
    return statement


@router.get("", response_model=ProxyList)
def list_proxies(
    session: Session = Depends(get_session),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=500),
    type: str | None = None,  # noqa: A002
    country: str | None = None,
    anonymity: str | None = None,
    max_latency: float | None = None,
    search: str | None = None,
) -> ProxyList:
    statement = filtered_proxy_statement(type, country, anonymity, max_latency, search)
    all_items = list(session.exec(statement.order_by(Proxy.id.desc())).all())
    start = (page - 1) * page_size
    return ProxyList(items=all_items[start : start + page_size], total=len(all_items), page=page, page_size=page_size)


@router.get("/stats", response_model=ProxyStats)
def proxy_stats(session: Session = Depends(get_session)) -> ProxyStats:
    total = session.exec(select(func.count()).select_from(Proxy)).one()
    alive = session.exec(select(func.count()).select_from(Proxy).where(Proxy.status == "alive")).one()
    dead = session.exec(select(func.count()).select_from(Proxy).where(Proxy.status == "dead")).one()
    unknown = session.exec(select(func.count()).select_from(Proxy).where(Proxy.status == "unknown")).one()
    avg_latency = session.exec(select(func.avg(Proxy.latency_ms)).where(Proxy.status == "alive")).one()
    return ProxyStats(
        total=total,
        alive=alive,
        dead=dead,
        unknown=unknown,
        to_test=max(runtime_stats.queued - runtime_stats.tested, 0),
        cycle_tested=runtime_stats.tested,
        cycle_valid=runtime_stats.valid,
        cycle_active=runtime_stats.cycle_active,
        phase=runtime_stats.phase,
        avg_latency_ms=avg_latency,
    )


@router.post("", response_model=ProxyRead, status_code=status.HTTP_201_CREATED)
async def add_manual_proxy(
    payload: ProxyCreate,
    _: bool = Depends(require_admin),
    session: Session = Depends(get_session),
) -> ProxyRead:
    proxy_type = normalize_proxy_type(payload.type)
    proxy = session.exec(select(Proxy).where(Proxy.ip == payload.ip, Proxy.port == payload.port)).first()

    if proxy is None:
        proxy = Proxy(ip=payload.ip, port=payload.port)

    proxy.type = proxy_type
    proxy.country = payload.country or None
    proxy.anonymity = payload.anonymity or None
    proxy.is_manual = True

    if payload.test_now:
        proxy = await test_proxy(proxy)

    session.add(proxy)
    session.commit()
    session.refresh(proxy)
    update_stock_stats(session)
    await emit_proxy_added(ProxyRead.model_validate(proxy).model_dump(mode="json"))
    await emit_stats()
    return ProxyRead.model_validate(proxy)


@router.get("/export", response_model=None)
def export_proxies(
    session: Session = Depends(get_session),
    format: str = Query(default="txt", pattern="^(txt|csv|json)$"),  # noqa: A002
    only_alive: bool = True,
):
    statement = select(Proxy)
    if only_alive:
        statement = statement.where(Proxy.status == "alive")
    proxies = list(session.exec(statement.order_by(Proxy.ip)).all())

    if format == "json":
        return [ProxyRead.model_validate(proxy) for proxy in proxies]
    if format == "csv":
        rows = ["ip,port,type,country,anonymity,latency_ms,status,is_manual"]
        rows.extend(
            (
                f"{p.ip},{p.port},{p.type},{p.country or ''},{p.anonymity or ''},"
                f"{p.latency_ms or ''},{p.status},{p.is_manual}"
            )
            for p in proxies
        )
        return Response("\n".join(rows), media_type="text/csv")
    return Response("\n".join(f"{p.ip}:{p.port}" for p in proxies), media_type="text/plain")
