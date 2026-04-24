from __future__ import annotations

import asyncio
import logging
from contextlib import asynccontextmanager, suppress

import socketio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import Session

from backend.app.api.v1.deps import engine, init_db
from backend.app.api.v1.routes import health, proxies
from backend.app.api.websocket import sio
from backend.app.core.config import get_settings
from backend.app.core.logger import configure_logging
from backend.app.services.tester import select_expired_proxies, test_proxy_batch

logger = logging.getLogger(__name__)


async def recheck_loop() -> None:
    settings = get_settings()
    interval_seconds = settings.config.test.recheck_interval_minutes * 60
    while True:
        await asyncio.sleep(interval_seconds)
        with Session(engine) as session:
            expired = select_expired_proxies(session)
            if expired:
                logger.info("Rechecking %s stored proxies", len(expired))
                await test_proxy_batch(session, expired)


@asynccontextmanager
async def lifespan(_: FastAPI):
    configure_logging()
    init_db()
    task = asyncio.create_task(recheck_loop())
    try:
        yield
    finally:
        task.cancel()
        with suppress(asyncio.CancelledError):
            await task


settings = get_settings()
fastapi_app = FastAPI(title=settings.app_name, version="0.1.0", lifespan=lifespan)
fastapi_app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
fastapi_app.include_router(health.router, prefix=settings.api_prefix)
fastapi_app.include_router(proxies.router, prefix=settings.api_prefix)

app = socketio.ASGIApp(sio, other_asgi_app=fastapi_app, socketio_path="socket.io")

