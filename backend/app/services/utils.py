from __future__ import annotations

import re

from backend.app.core.config import FilterSettings
from backend.app.models.proxy import Proxy

PROXY_RE = re.compile(r"(?P<ip>(?:\d{1,3}\.){3}\d{1,3})[:\s](?P<port>\d{2,5})")


def normalize_proxy_type(value: str | None) -> str:
    if not value:
        return "http"
    lowered = value.strip().lower()
    if lowered in {"yes", "https"}:
        return "https"
    if lowered in {"socks4", "socks5"}:
        return lowered
    return "http"


def extract_proxies_with_regex(text: str, proxy_type: str = "http", limit: int | None = None) -> list[Proxy]:
    proxies: list[Proxy] = []
    for match in PROXY_RE.finditer(text):
        port = int(match.group("port"))
        if 1 <= port <= 65535:
            proxies.append(Proxy(ip=match.group("ip"), port=port, type=proxy_type))
            if limit is not None and len(proxies) >= limit:
                break
    return proxies


def dedupe_proxies(proxies: list[Proxy]) -> list[Proxy]:
    seen: set[tuple[str, int]] = set()
    deduped: list[Proxy] = []
    for proxy in proxies:
        key = (proxy.ip, proxy.port)
        if key not in seen:
            seen.add(key)
            deduped.append(proxy)
    return deduped


def filter_proxy(proxy: Proxy, filters: FilterSettings) -> bool:
    if filters.type and proxy.type not in filters.type:
        return False
    if filters.country and proxy.country not in filters.country:
        return False
    if filters.anonymity and proxy.anonymity not in filters.anonymity:
        return False
    if filters.max_latency_ms is not None and proxy.latency_ms is not None:
        return proxy.latency_ms <= filters.max_latency_ms
    return True
