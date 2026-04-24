from __future__ import annotations

import asyncio
import logging
from contextlib import asynccontextmanager, suppress

import socketio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import func
from sqlmodel import Session, select

from backend.app.api.v1.deps import engine, init_db
from backend.app.api.v1.routes import health, proxies
from backend.app.api.websocket import emit_stats, sio
from backend.app.core.config import get_settings
from backend.app.core.logger import configure_logging
from backend.app.models.proxy import Proxy
from backend.app.services.pipeline import scrape_test_and_store_alive, update_stock_stats
from backend.app.services.runtime import finish_cycle, start_cycle, update_runtime_stats
from backend.app.services.tester import select_expired_proxies, test_proxy_batch

logger = logging.getLogger(__name__)
pipeline_lock = asyncio.Lock()


async def recheck_loop() -> None:
    settings = get_settings()
    interval_seconds = settings.config.test.recheck_interval_minutes * 60
    while True:
        async with pipeline_lock:
            with Session(engine) as session:
                expired = select_expired_proxies(session)
                if expired:
                    start_cycle("rechecking")
                    update_runtime_stats(queued=len(expired), tested=0, valid=0)
                    update_stock_stats(session)
                    await emit_stats()
                    logger.info("Rechecking %s stored proxies", len(expired))
                    await test_proxy_batch(session, expired)
                    update_stock_stats(session)
                    finish_cycle()
                    await emit_stats()
        await asyncio.sleep(interval_seconds)


async def scrape_loop() -> None:
    settings = get_settings()
    interval_seconds = settings.config.test.scrape_interval_minutes * 60
    if not settings.config.test.scrape_on_startup:
        await asyncio.sleep(interval_seconds)

    while True:
        async with pipeline_lock:
            with Session(engine) as session:
                logger.info("Scraping and validating fresh proxy candidates")
                await scrape_test_and_store_alive(session)
        await asyncio.sleep(interval_seconds)


async def stock_guard_loop() -> None:
    settings = get_settings()
    interval_seconds = settings.config.test.stock_guard_interval_seconds
    while True:
        await asyncio.sleep(interval_seconds)
        if pipeline_lock.locked():
            continue
        async with pipeline_lock:
            with Session(engine) as session:
                update_stock_stats(session)
                await emit_stats()
                valid_stock = session.exec(select(func.count()).select_from(Proxy).where(Proxy.status == "alive")).one()
                if valid_stock < settings.config.test.min_valid_proxies:
                    logger.info(
                        "Valid proxy stock below target (%s/%s), starting refill cycle",
                        valid_stock,
                        settings.config.test.min_valid_proxies,
                    )
                    await scrape_test_and_store_alive(session)


@asynccontextmanager
async def lifespan(_: FastAPI):
    configure_logging()
    init_db()
    with Session(engine) as session:
        update_stock_stats(session)
    tasks = [
        asyncio.create_task(recheck_loop()),
        asyncio.create_task(scrape_loop()),
        asyncio.create_task(stock_guard_loop()),
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
fastapi_app.include_router(proxies.router, prefix=settings.api_prefix)

app = socketio.ASGIApp(sio, other_asgi_app=fastapi_app, socketio_path="socket.io")
