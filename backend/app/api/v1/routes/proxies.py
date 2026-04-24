from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, col, select

from backend.app.api.v1.deps import get_session
from backend.app.models.proxy import Proxy
from backend.app.schemas.proxy import (
    BatchTestRequest,
    ProxyCreate,
    ProxyIds,
    ProxyList,
    ProxyRead,
    ProxyStats,
    ProxyUpdate,
)
from backend.app.services.pipeline import scrape_test_and_store_alive
from backend.app.services.tester import test_proxy, test_proxy_batch

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
    return ProxyStats(total=total, alive=alive, dead=dead, unknown=unknown, avg_latency_ms=avg_latency)


@router.get("/ids", response_model=ProxyIds)
def list_proxy_ids(
    session: Session = Depends(get_session),
    type: str | None = None,  # noqa: A002
    country: str | None = None,
    anonymity: str | None = None,
    max_latency: float | None = None,
    search: str | None = None,
) -> ProxyIds:
    statement = filtered_proxy_statement(type, country, anonymity, max_latency, search)
    ids = [proxy.id for proxy in session.exec(statement).all() if proxy.id is not None]
    return ProxyIds(ids=ids, total=len(ids))


@router.post("", response_model=ProxyRead, status_code=status.HTTP_201_CREATED)
async def create_proxy(payload: ProxyCreate, session: Session = Depends(get_session)) -> Proxy:
    proxy = Proxy.model_validate(payload)
    tested = await test_proxy(proxy)
    if tested.status != "alive":
        raise HTTPException(status_code=422, detail="Proxy is not alive, not stored")

    session.add(proxy)
    try:
        session.commit()
    except IntegrityError as exc:
        session.rollback()
        raise HTTPException(status_code=409, detail="Proxy already exists") from exc
    session.refresh(proxy)
    return proxy


@router.patch("/{proxy_id}", response_model=ProxyRead)
def update_proxy(proxy_id: int, payload: ProxyUpdate, session: Session = Depends(get_session)) -> Proxy:
    proxy = session.get(Proxy, proxy_id)
    if not proxy:
        raise HTTPException(status_code=404, detail="Proxy not found")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(proxy, key, value)
    session.add(proxy)
    session.commit()
    session.refresh(proxy)
    return proxy


@router.delete("/{proxy_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_proxy(proxy_id: int, session: Session = Depends(get_session)) -> Response:
    proxy = session.get(Proxy, proxy_id)
    if not proxy:
        raise HTTPException(status_code=404, detail="Proxy not found")
    session.delete(proxy)
    session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/{proxy_id}/test", response_model=ProxyRead)
async def test_one_proxy(proxy_id: int, session: Session = Depends(get_session)) -> Proxy:
    proxy = session.get(Proxy, proxy_id)
    if not proxy:
        raise HTTPException(status_code=404, detail="Proxy not found")
    tested = await test_proxy(proxy)
    if tested.status == "dead":
        session.delete(tested)
        session.commit()
        return tested
    session.add(tested)
    session.commit()
    session.refresh(tested)
    return tested


@router.post("/test-batch", response_model=list[ProxyRead])
async def test_batch(payload: BatchTestRequest, session: Session = Depends(get_session)) -> list[Proxy]:
    proxies = list(session.exec(select(Proxy).where(Proxy.id.in_(payload.ids))).all())  # type: ignore[attr-defined]
    return await test_proxy_batch(session, proxies)


@router.post("/scrape", response_model=list[ProxyRead])
async def scrape_sources(session: Session = Depends(get_session)) -> list[Proxy]:
    return await scrape_test_and_store_alive(session)


@router.delete("/invalid", response_model=dict[str, int])
def delete_invalid_proxies(session: Session = Depends(get_session)) -> dict[str, int]:
    invalid = list(session.exec(select(Proxy).where(Proxy.status != "alive")).all())
    for proxy in invalid:
        session.delete(proxy)
    session.commit()
    return {"deleted": len(invalid)}


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
        rows = ["ip,port,type,country,anonymity,latency_ms,status"]
        rows.extend(
            f"{p.ip},{p.port},{p.type},{p.country or ''},{p.anonymity or ''},{p.latency_ms or ''},{p.status}"
            for p in proxies
        )
        return Response("\n".join(rows), media_type="text/csv")
    return Response("\n".join(f"{p.ip}:{p.port}" for p in proxies), media_type="text/plain")


@router.get("/{proxy_id}", response_model=ProxyRead)
def get_proxy(proxy_id: int, session: Session = Depends(get_session)) -> Proxy:
    proxy = session.get(Proxy, proxy_id)
    if not proxy:
        raise HTTPException(status_code=404, detail="Proxy not found")
    return proxy
