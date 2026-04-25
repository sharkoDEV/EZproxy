from __future__ import annotations

import pytest

from backend.app.models.proxy import Proxy
from backend.app.services import tester


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


@pytest.mark.anyio
async def test_socks_http_reply_falls_back_to_http(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[str] = []

    async def fake_fetch_test_url(test_url: str, proxy: Proxy, proxy_type: str, timeout_value: float) -> None:
        calls.append(proxy_type)
        if proxy_type == "socks5":
            raise RuntimeError("ProxyError(ReplyError('Unexpected reply version: 0X48'))")

    async def fake_emit_proxy_status(proxy_id: int | None, status: str, latency_ms: float | None) -> None:
        return None

    monkeypatch.setattr(tester, "_test_urls", lambda: ["http://example.test/ip"])
    monkeypatch.setattr(tester, "_fetch_test_url", fake_fetch_test_url)
    monkeypatch.setattr(tester, "emit_proxy_status", fake_emit_proxy_status)

    proxy = Proxy(ip="203.0.113.10", port=80, type="socks5")
    tested = await tester.test_proxy(proxy, timeout=1)

    assert calls == ["socks5", "http"]
    assert tested.type == "http"
    assert tested.status == "alive"


@pytest.mark.anyio
async def test_candidate_batch_calls_live_result_callback(monkeypatch: pytest.MonkeyPatch) -> None:
    seen: list[tuple[str, int, int, int]] = []

    async def fake_test_proxy(proxy: Proxy) -> Proxy:
        proxy.status = "alive" if proxy.ip.endswith(".1") else "dead"
        return proxy

    async def fake_emit_progress(tested: int, total: int, valid: int) -> None:
        return None

    async def fake_emit_stats() -> None:
        return None

    async def on_result(proxy: Proxy, tested: int, total: int, valid: int) -> None:
        seen.append((proxy.status, tested, total, valid))

    monkeypatch.setattr(tester, "test_proxy", fake_test_proxy)
    monkeypatch.setattr(tester, "emit_progress", fake_emit_progress)
    monkeypatch.setattr(tester, "emit_stats", fake_emit_stats)

    proxies = [
        Proxy(ip="192.0.2.1", port=8080, type="http"),
        Proxy(ip="192.0.2.2", port=8080, type="http"),
    ]
    await tester.test_proxy_candidates(proxies, on_result=on_result)

    assert len(seen) == 2
    assert seen[-1][2] == 2
    assert seen[-1][3] == 1
