from __future__ import annotations

import asyncio
import logging
import time
from datetime import UTC, datetime, timedelta

import aiohttp
from aiohttp_socks import ProxyConnector
from sqlmodel import Session, select

from backend.app.api.websocket import emit_progress, emit_proxy_status, emit_stats
from backend.app.core.config import get_settings
from backend.app.models.proxy import Proxy
from backend.app.services.runtime import update_runtime_stats

logger = logging.getLogger(__name__)


def _proxy_url(proxy: Proxy) -> str:
    scheme = "http" if proxy.type in {"http", "https"} else proxy.type
    return f"{scheme}://{proxy.ip}:{proxy.port}"


async def _fetch_test_url(test_url: str, proxy: Proxy, proxy_url: str, timeout_value: float) -> None:
    client_timeout = aiohttp.ClientTimeout(total=timeout_value)
    if proxy.type in {"socks4", "socks5"}:
        connector = ProxyConnector.from_url(proxy_url)
        async with aiohttp.ClientSession(timeout=client_timeout, connector=connector) as session:
            async with session.get(test_url) as response:
                if response.status >= 400:
                    raise aiohttp.ClientResponseError(
                        request_info=response.request_info,
                        history=response.history,
                        status=response.status,
                        message="Proxy returned an error",
                    )
                await response.text()
        return

    async with aiohttp.ClientSession(timeout=client_timeout) as session:
        async with session.get(test_url, proxy=proxy_url) as response:
            if response.status >= 400:
                raise aiohttp.ClientResponseError(
                    request_info=response.request_info,
                    history=response.history,
                    status=response.status,
                    message="Proxy returned an error",
                )
            await response.text()


def _test_urls() -> list[str]:
    settings = get_settings()
    urls = [settings.config.test.url, *settings.config.test.urls]
    return list(dict.fromkeys(urls))


async def test_proxy(proxy: Proxy, timeout: float | None = None) -> Proxy:
    settings = get_settings()
    timeout_value = timeout or settings.config.test.timeout
    start = time.perf_counter()
    proxy_url = _proxy_url(proxy)

    last_error: Exception | None = None
    for test_url in _test_urls():
        try:
            await _fetch_test_url(test_url, proxy, proxy_url, timeout_value)
            proxy.status = "alive"
            proxy.latency_ms = round((time.perf_counter() - start) * 1000, 2)
            break
        except Exception as exc:  # noqa: BLE001
            last_error = exc
    else:
        exc = last_error or RuntimeError("Proxy test failed")
        logger.info("Proxy %s:%s failed: %r", proxy.ip, proxy.port, exc)
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
        if (
            settings.config.test.delete_dead_after_check
            and proxy.status == "dead"
            and proxy.id is not None
            and not proxy.is_manual
        ):
            session.delete(proxy)
            session.commit()
        else:
            session.add(proxy)
            session.commit()
            session.refresh(proxy)
        update_runtime_stats(phase="rechecking", queued=total, tested=tested, valid=valid)
        await emit_progress(tested, total, valid)
        await emit_stats()
        results.append(proxy)
    return results


async def test_proxy_candidates(proxies: list[Proxy]) -> list[Proxy]:
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
        update_runtime_stats(phase="testing", queued=total, tested=tested, valid=valid)
        await emit_progress(tested, total, valid)
        await emit_stats()
        results.append(proxy)
    return results


def select_expired_proxies(session: Session) -> list[Proxy]:
    settings = get_settings()
    interval = timedelta(minutes=settings.config.test.cycle_interval_minutes)
    threshold = datetime.now(UTC) - interval
    statement = select(Proxy).where((Proxy.last_checked == None) | (Proxy.last_checked < threshold))  # noqa: E711
    return list(session.exec(statement).all())
