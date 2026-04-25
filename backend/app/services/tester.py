from __future__ import annotations

import asyncio
import logging
import time
from collections.abc import Awaitable, Callable
from datetime import UTC, datetime, timedelta

import aiohttp
from aiohttp_socks import ProxyConnector
from sqlmodel import Session, select

from backend.app.api.websocket import emit_progress, emit_proxy_status, emit_stats
from backend.app.core.config import get_settings
from backend.app.models.proxy import Proxy
from backend.app.services.runtime import update_runtime_stats

logger = logging.getLogger(__name__)


def _proxy_url(proxy: Proxy, proxy_type: str | None = None) -> str:
    resolved_type = proxy_type or proxy.type
    scheme = "http" if resolved_type in {"http", "https"} else resolved_type
    return f"{scheme}://{proxy.ip}:{proxy.port}"


def _looks_like_http_reply_to_socks(exc: Exception) -> bool:
    message = repr(exc).lower()
    return "unexpected reply version" in message and "0x48" in message


async def _fetch_test_url(test_url: str, proxy: Proxy, proxy_type: str, timeout_value: float) -> None:
    proxy_url = _proxy_url(proxy, proxy_type)
    client_timeout = aiohttp.ClientTimeout(total=timeout_value)
    if proxy_type in {"socks4", "socks5"}:
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

    last_error: Exception | None = None
    proxy_types = [proxy.type]
    tested_types: set[str] = set()
    alive_type: str | None = None

    while proxy_types:
        proxy_type = proxy_types.pop(0)
        tested_types.add(proxy_type)
        if proxy_type != proxy.type:
            logger.debug("Retrying %s:%s as %s after SOCKS protocol mismatch", proxy.ip, proxy.port, proxy_type)

        for test_url in _test_urls():
            try:
                await _fetch_test_url(test_url, proxy, proxy_type, timeout_value)
                alive_type = proxy_type
                break
            except Exception as exc:  # noqa: BLE001
                last_error = exc
                if (
                    proxy_type in {"socks4", "socks5"}
                    and "http" not in tested_types
                    and "http" not in proxy_types
                    and _looks_like_http_reply_to_socks(exc)
                ):
                    proxy_types.append("http")
                    break

        if alive_type:
            break

    if alive_type:
        proxy.type = alive_type
        proxy.status = "alive"
        proxy.latency_ms = round((time.perf_counter() - start) * 1000, 2)
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


async def test_proxy_candidates(
    proxies: list[Proxy],
    on_result: Callable[[Proxy, int, int, int], Awaitable[None]] | None = None,
) -> list[Proxy]:
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
        if on_result is not None:
            await on_result(proxy, tested, total, valid)
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
