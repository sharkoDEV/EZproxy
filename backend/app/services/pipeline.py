from __future__ import annotations

import logging

from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select

from backend.app.api.websocket import emit_proxy_added, emit_stats
from backend.app.models.proxy import Proxy
from backend.app.services.runtime import finish_cycle, start_cycle, update_runtime_stats
from backend.app.services.scraper import scrape_all_sources
from backend.app.services.tester import test_proxy_candidates

logger = logging.getLogger(__name__)


async def scrape_test_and_store_alive(session: Session) -> list[Proxy]:
    start_cycle("scraping")
    await emit_stats()
    scraped = await scrape_all_sources()
    candidates: list[Proxy] = []

    for proxy in scraped:
        existing = session.exec(select(Proxy).where(Proxy.ip == proxy.ip, Proxy.port == proxy.port)).first()
        if not existing:
            candidates.append(proxy)

    if not candidates:
        update_stock_stats(session)
        finish_cycle()
        await emit_stats()
        return []

    update_runtime_stats(phase="testing", scraped=len(scraped), queued=len(candidates), tested=0, valid=0)
    await emit_stats()
    logger.info("Testing %s scraped candidates before storing", len(candidates))
    tested = await test_proxy_candidates(candidates)
    from backend.app.core.config import get_settings

    settings = get_settings()
    alive = [proxy for proxy in tested if proxy.status == "alive"] if settings.config.test.store_only_alive else tested

    stored: list[Proxy] = []
    for proxy in alive:
        session.add(proxy)
        try:
            session.commit()
        except IntegrityError:
            session.rollback()
            continue
        session.refresh(proxy)
        stored.append(proxy)
        await emit_proxy_added(
            {
                "id": proxy.id,
                "ip": proxy.ip,
                "port": proxy.port,
                "type": proxy.type,
                "country": proxy.country,
                "anonymity": proxy.anonymity,
                "latency_ms": proxy.latency_ms,
                "last_checked": proxy.last_checked.isoformat() if proxy.last_checked else None,
                "status": proxy.status,
            }
        )
        update_stock_stats(session)
        update_runtime_stats(stored=len(stored))
        await emit_stats()

    update_stock_stats(session)
    update_runtime_stats(stored=len(stored), tested=len(tested), valid=len(alive))
    finish_cycle()
    await emit_stats()
    logger.info("Stored %s alive proxies from %s tested candidates", len(stored), len(tested))
    return stored


def update_stock_stats(session: Session) -> None:
    proxies = session.exec(select(Proxy.status)).all()
    update_runtime_stats(
        total_stock=len(proxies),
        valid_stock=sum(1 for status in proxies if status == "alive"),
    )
