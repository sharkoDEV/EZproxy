from __future__ import annotations

import pytest

from backend.app.models.proxy import Proxy
from backend.app.services import tester


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
