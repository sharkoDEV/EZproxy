from __future__ import annotations

import logging

import aiohttp
from bs4 import BeautifulSoup

from backend.app.core.config import ProxySource, get_settings
from backend.app.models.proxy import Proxy
from backend.app.services.utils import dedupe_proxies, extract_proxies_with_regex, normalize_proxy_type

logger = logging.getLogger(__name__)


def parse_sslproxies(html: str) -> list[Proxy]:
    soup = BeautifulSoup(html, "lxml")
    table = soup.find("table")
    proxies: list[Proxy] = []
    if not table:
        return extract_proxies_with_regex(html)

    for row in table.select("tbody tr"):
        cells = [cell.get_text(strip=True) for cell in row.find_all("td")]
        if len(cells) < 2:
            continue
        try:
            proxy = Proxy(
                ip=cells[0],
                port=int(cells[1]),
                country=cells[2] if len(cells) > 2 else None,
                anonymity=cells[4].lower() if len(cells) > 4 else None,
                type=normalize_proxy_type(cells[6] if len(cells) > 6 else "http"),
            )
            proxies.append(proxy)
        except ValueError:
            continue
    return proxies or extract_proxies_with_regex(html)


def parse_spysone(html: str) -> list[Proxy]:
    soup = BeautifulSoup(html, "lxml")
    proxies: list[Proxy] = []
    for row in soup.select("tr"):
        text = " ".join(row.stripped_strings)
        for proxy in extract_proxies_with_regex(text):
            proxy.type = "http"
            proxies.append(proxy)
    return proxies or extract_proxies_with_regex(html)


def parse_proxydownload(body: str) -> list[Proxy]:
    return extract_proxies_with_regex(body, proxy_type="http")


PARSERS = {
    "sslproxies": parse_sslproxies,
    "spysone": parse_spysone,
    "proxydownload": parse_proxydownload,
}


async def fetch_source(session: aiohttp.ClientSession, source: ProxySource) -> list[Proxy]:
    try:
        async with session.get(source.url) as response:
            response.raise_for_status()
            body = await response.text()
    except Exception as exc:  # noqa: BLE001
        logger.warning("Source %s unavailable: %s", source.name, exc)
        return []

    parser = PARSERS[source.parser]
    parsed = parser(body)
    logger.info("Scraped %s proxies from %s", len(parsed), source.name)
    return parsed


async def scrape_all_sources() -> list[Proxy]:
    settings = get_settings()
    timeout = aiohttp.ClientTimeout(total=settings.config.test.timeout)
    async with aiohttp.ClientSession(timeout=timeout, headers={"User-Agent": "ezProxy/1.0"}) as session:
        results = [await fetch_source(session, source) for source in settings.config.sources]

    proxies = [proxy for group in results for proxy in group]
    return dedupe_proxies(proxies)

