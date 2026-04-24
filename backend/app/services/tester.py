from __future__ import annotations

import asyncio
import logging
import time
from datetime import UTC, datetime, timedelta

import aiohttp
from sqlmodel import Session, select

from backend.app.api.websocket import emit_progress, emit_proxy_status
from backend.app.core.config import get_settings
from backend.app.models.proxy import Proxy

logger = logging.getLogger(__name__)


def _proxy_url(proxy: Proxy) -> str:
    scheme = "http" if proxy.type in {"http", "https"} else proxy.type
    return f"{scheme}://{proxy.ip}:{proxy.port}"


async def test_proxy(proxy: Proxy, timeout: float | None = None) -> Proxy:
    settings = get_settings()
    timeout_value = timeout or settings.config.test.timeout
    start = time.perf_counter()
    proxy_url = _proxy_url(proxy)

    try:
        client_timeout = aiohttp.ClientTimeout(total=timeout_value)
        async with aiohttp.ClientSession(timeout=client_timeout) as session:
            async with session.get(settings.config.test.url, proxy=proxy_url) as response:
                if response.status >= 400:
                    raise aiohttp.ClientResponseError(
                        request_info=response.request_info,
                        history=response.history,
                        status=response.status,
                        message="Proxy returned an error",
                    )
                await response.text()
        proxy.status = "alive"
        proxy.latency_ms = round((time.perf_counter() - start) * 1000, 2)
    except Exception as exc:  # noqa: BLE001
        logger.info("Proxy %s:%s failed: %s", proxy.ip, proxy.port, exc)
        proxy.status = "dead"
        proxy.latency_ms = None

    proxy.last_checked = datetime.now(UTC)
    await emit_proxy_status(proxy.id, proxy.status, proxy.latency_ms)
    return proxy


async def test_proxy_batch(session: Session, proxies: list[Proxy]) -> list[Proxy]:
    settings = get_settings()
    semaphore = asyncio.Semaphore(settings.config.test.max_workers)
    total = len(proxies)
    tested = 0
    valid = 0
    results: list[Proxy] = []

    async def run_one(proxy: Proxy) -> Proxy:
        async with semaphore:
            return await test_proxy(proxy)

    for task in asyncio.as_completed([run_one(proxy) for proxy in proxies]):
        proxy = await task
        tested += 1
        valid += 1 if proxy.status == "alive" else 0
        session.add(proxy)
        session.commit()
        session.refresh(proxy)
        await emit_progress(tested, total, valid)
        results.append(proxy)
    return results


def select_expired_proxies(session: Session) -> list[Proxy]:
    settings = get_settings()
    interval = timedelta(minutes=settings.config.test.recheck_interval_minutes)
    threshold = datetime.now(UTC) - interval
    statement = select(Proxy).where((Proxy.last_checked == None) | (Proxy.last_checked < threshold))  # noqa: E711
    return list(session.exec(statement).all())

