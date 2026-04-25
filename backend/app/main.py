from __future__ import annotations

import asyncio
import logging
from contextlib import asynccontextmanager, suppress

import socketio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import Session

from backend.app.api.v1.deps import engine, init_db
from backend.app.api.v1.routes import admin, health, proxies
from backend.app.api.websocket import emit_stats, sio
from backend.app.core.config import get_settings
from backend.app.core.logger import configure_logging
from backend.app.services.pipeline import (
    scrape_gfp_once_with_single_worker,
    scrape_test_and_store_alive,
    update_stock_stats,
)
from backend.app.services.runtime import finish_cycle, start_cycle, update_runtime_stats
from backend.app.services.tester import select_expired_proxies, test_proxy_batch

logger = logging.getLogger(__name__)
pipeline_lock = asyncio.Lock()


async def proxy_cycle_loop() -> None:
    settings = get_settings()
    interval_seconds = settings.config.test.cycle_interval_minutes * 60
    if not settings.config.test.scrape_on_startup:
        await asyncio.sleep(interval_seconds)

    while True:
        async with pipeline_lock:
            with Session(engine) as session:
                expired = select_expired_proxies(session)
                if expired:
                    start_cycle("rechecking")
                    update_runtime_stats(queued=len(expired), tested=0, valid=0)
                    update_stock_stats(session)
                    await emit_stats()
                    logger.info("Rechecking %s stored proxies before scrape", len(expired))
                    await test_proxy_batch(session, expired)
                    update_stock_stats(session)
                    finish_cycle()
                    await emit_stats()

                logger.info("Scraping and validating fresh proxy candidates")
                await scrape_test_and_store_alive(session)
        await asyncio.sleep(interval_seconds)


async def gfp_worker_once() -> None:
    logger.info("Starting one-shot GFP worker with a single tester")
    with Session(engine) as session:
        try:
            await scrape_gfp_once_with_single_worker(session)
        except Exception:  # noqa: BLE001
            logger.exception("GFP one-shot worker failed")


@asynccontextmanager
async def lifespan(_: FastAPI):
    configure_logging()
    init_db()
    with Session(engine) as session:
        update_stock_stats(session)
    tasks = [
        asyncio.create_task(proxy_cycle_loop()),
        asyncio.create_task(gfp_worker_once()),
    ]
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
fastapi_app.include_router(admin.router, prefix=settings.api_prefix)
fastapi_app.include_router(proxies.router, prefix=settings.api_prefix)

app = socketio.ASGIApp(sio, other_asgi_app=fastapi_app, socketio_path="socket.io")
