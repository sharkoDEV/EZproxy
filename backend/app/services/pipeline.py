from __future__ import annotations

import logging

from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select

from backend.app.core.config import get_settings
from backend.app.models.proxy import Proxy
from backend.app.services.scraper import scrape_all_sources
from backend.app.services.tester import test_proxy_candidates

logger = logging.getLogger(__name__)


async def scrape_test_and_store_alive(session: Session) -> list[Proxy]:
    settings = get_settings()
    scraped = await scrape_all_sources()
    candidates: list[Proxy] = []

    for proxy in scraped:
        existing = session.exec(select(Proxy).where(Proxy.ip == proxy.ip, Proxy.port == proxy.port)).first()
        if not existing:
            candidates.append(proxy)

    limit = settings.config.test.scrape_candidate_limit
    if limit > 0:
        candidates = candidates[:limit]

    if not candidates:
        return []

    logger.info("Testing %s scraped candidates before storing", len(candidates))
    tested = await test_proxy_candidates(candidates)
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

    logger.info("Stored %s alive proxies from %s tested candidates", len(stored), len(tested))
    return stored
