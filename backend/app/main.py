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
from backend.app.services.pipeline import scrape_test_and_store_alive
from backend.app.services.tester import select_expired_proxies, test_proxy_batch

logger = logging.getLogger(__name__)


async def recheck_loop() -> None:
    settings = get_settings()
    interval_seconds = settings.config.test.recheck_interval_minutes * 60
    while True:
        with Session(engine) as session:
            expired = select_expired_proxies(session)
            if expired:
                logger.info("Rechecking %s stored proxies", len(expired))
                await test_proxy_batch(session, expired)
        await asyncio.sleep(interval_seconds)


async def scrape_loop() -> None:
    settings = get_settings()
    interval_seconds = settings.config.test.scrape_interval_minutes * 60
    if not settings.config.test.scrape_on_startup:
        await asyncio.sleep(interval_seconds)

    while True:
        with Session(engine) as session:
            logger.info("Scraping and validating fresh proxy candidates")
            await scrape_test_and_store_alive(session)
        await asyncio.sleep(interval_seconds)


@asynccontextmanager
async def lifespan(_: FastAPI):
    configure_logging()
    init_db()
    tasks = [asyncio.create_task(recheck_loop()), asyncio.create_task(scrape_loop())]
    try:
        yield
    finally:
        for task in tasks:
            task.cancel()
        for task in tasks:
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
