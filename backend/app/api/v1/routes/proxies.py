from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, col, select

from backend.app.api.v1.deps import get_session
from backend.app.models.proxy import Proxy
from backend.app.schemas.proxy import BatchTestRequest, ProxyCreate, ProxyList, ProxyRead, ProxyUpdate
from backend.app.services.scraper import scrape_all_sources
from backend.app.services.tester import test_proxy, test_proxy_batch

router = APIRouter(prefix="/proxies", tags=["proxies"])


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

    all_items = list(session.exec(statement.order_by(Proxy.id.desc())).all())
    start = (page - 1) * page_size
    return ProxyList(items=all_items[start : start + page_size], total=len(all_items), page=page, page_size=page_size)


@router.post("", response_model=ProxyRead, status_code=status.HTTP_201_CREATED)
def create_proxy(payload: ProxyCreate, session: Session = Depends(get_session)) -> Proxy:
    proxy = Proxy.model_validate(payload)
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
    scraped = await scrape_all_sources()
    created: list[Proxy] = []
    for proxy in scraped:
        existing = session.exec(select(Proxy).where(Proxy.ip == proxy.ip, Proxy.port == proxy.port)).first()
        if existing:
            continue
        session.add(proxy)
        created.append(proxy)
    session.commit()
    for proxy in created:
        session.refresh(proxy)
    return created


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
