from __future__ import annotations

import logging

from sqlalchemy.exc import SQLAlchemyError
from sqlmodel import Session, select

from backend.app.api.websocket import emit_proxy_added, emit_stats
from backend.app.core.config import get_settings
from backend.app.models.proxy import Proxy
from backend.app.services.distributed import distributed_queue
from backend.app.services.runtime import finish_cycle, start_cycle, update_runtime_stats
from backend.app.services.scraper import scrape_all_sources, scrape_gfp_sources
from backend.app.services.tester import test_proxy_candidates

logger = logging.getLogger(__name__)


def proxy_event_payload(proxy: Proxy) -> dict:
    return {
        "id": proxy.id,
        "ip": proxy.ip,
        "port": proxy.port,
        "type": proxy.type,
        "country": proxy.country,
        "anonymity": proxy.anonymity,
        "latency_ms": proxy.latency_ms,
        "last_checked": proxy.last_checked.isoformat() if proxy.last_checked else None,
        "status": proxy.status,
        "is_manual": proxy.is_manual,
    }


async def scrape_test_and_store_alive(session: Session) -> list[Proxy]:
    start_cycle("scraping")
    await emit_stats()
    scraped = await scrape_all_sources()
    update_runtime_stats(phase="deduping", scraped=len(scraped), queued=0, tested=0, valid=0)
    await emit_stats()
    logger.info("Deduping %s scraped proxies against stored database", len(scraped))

    existing_keys = set(session.exec(select(Proxy.ip, Proxy.port)).all())
    candidates = [proxy for proxy in scraped if (proxy.ip, proxy.port) not in existing_keys]
    logger.info(
        "Deduped scraped proxies: %s new candidates, %s already stored",
        len(candidates),
        len(scraped) - len(candidates),
    )

    if not candidates:
        update_stock_stats(session)
        finish_cycle()
        await emit_stats()
        return []

    update_runtime_stats(phase="testing", scraped=len(scraped), queued=len(candidates), tested=0, valid=0)
    await emit_stats()

    settings = get_settings()
    if settings.config.workers.enabled:
        await distributed_queue.enqueue(candidates)
        update_runtime_stats(
            phase="distributed_testing",
            scraped=len(scraped),
            queued=len(candidates),
            tested=0,
            valid=0,
        )
        await emit_stats()
        logger.info("Queued %s candidates for distributed worker clients", len(candidates))
        return []

    logger.info("Testing %s scraped candidates before storing", len(candidates))
    stored: list[Proxy] = []

    async def store_live_result(proxy: Proxy, tested_count: int, total: int, valid_count: int) -> None:
        if settings.config.test.store_only_alive and proxy.status != "alive":
            return
        session.add(proxy)
        try:
            session.commit()
        except SQLAlchemyError:
            session.rollback()
            return
        session.refresh(proxy)
        stored.append(proxy)
        await emit_proxy_added(proxy_event_payload(proxy))
        update_stock_stats(session)
        update_runtime_stats(stored=len(stored), tested=tested_count, queued=total, valid=valid_count)
        await emit_stats()

    tested = await test_proxy_candidates(candidates, on_result=store_live_result)
    alive_count = sum(1 for proxy in tested if proxy.status == "alive")
    update_stock_stats(session)
    update_runtime_stats(stored=len(stored), tested=len(tested), valid=alive_count)
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


async def scrape_gfp_once_with_single_worker(session: Session) -> None:
    update_runtime_stats(
        gfp_active=True,
        gfp_scraped=0,
        gfp_queued=0,
        gfp_tested=0,
        gfp_valid=0,
        gfp_stored=0,
    )
    await emit_stats()
    scraped = await scrape_gfp_sources()
    existing_keys = set(session.exec(select(Proxy.ip, Proxy.port)).all())
    candidates = [proxy for proxy in scraped if (proxy.ip, proxy.port) not in existing_keys]
    update_runtime_stats(gfp_scraped=len(scraped), gfp_queued=len(candidates))
    await emit_stats()

    tested = 0
    valid = 0
    stored = 0
    from backend.app.services.tester import test_proxy

    for proxy in candidates:
        tested += 1
        tested_proxy = await test_proxy(proxy)
        if tested_proxy.status == "alive":
            valid += 1
            session.add(tested_proxy)
            try:
                session.commit()
            except SQLAlchemyError:
                session.rollback()
            else:
                session.refresh(tested_proxy)
                stored += 1
                await emit_proxy_added(proxy_event_payload(tested_proxy))
        if tested % 25 == 0 or tested == len(candidates):
            update_stock_stats(session)
            update_runtime_stats(gfp_tested=tested, gfp_valid=valid, gfp_stored=stored)
            await emit_stats()

    update_stock_stats(session)
    update_runtime_stats(gfp_active=False, gfp_tested=tested, gfp_valid=valid, gfp_stored=stored)
    await emit_stats()
