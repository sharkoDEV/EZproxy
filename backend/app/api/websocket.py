from __future__ import annotations

import socketio

from backend.app.services.runtime import runtime_stats

sio = socketio.AsyncServer(async_mode="asgi", cors_allowed_origins="*")


@sio.event(namespace="/ws/proxies")
async def connect(sid, environ, auth):  # noqa: ANN001
    await sio.emit("connected", {"message": "connected to ezProxy"}, to=sid, namespace="/ws/proxies")
    await sio.emit("stats", runtime_stats.as_dict(), to=sid, namespace="/ws/proxies")


@sio.event(namespace="/ws/proxies")
async def disconnect(sid):  # noqa: ANN001
    return None


async def emit_proxy_status(proxy_id: int | None, status: str, latency_ms: float | None) -> None:
    await sio.emit(
        "proxy_status",
        {"id": proxy_id, "status": status, "latency_ms": latency_ms},
        namespace="/ws/proxies",
    )


async def emit_progress(tested: int, total: int, valid: int) -> None:
    await sio.emit("progress", {"tested": tested, "total": total, "valid": valid}, namespace="/ws/proxies")


async def emit_stats() -> None:
    await sio.emit("stats", runtime_stats.as_dict(), namespace="/ws/proxies")
