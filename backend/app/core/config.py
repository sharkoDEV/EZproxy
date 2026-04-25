from __future__ import annotations

import json
import os
from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field

PROJECT_ROOT = Path(__file__).resolve().parents[3]
CONFIG_PATH = PROJECT_ROOT / "config.json"


class ProxySource(BaseModel):
    name: str
    url: str
    parser: Literal["sslproxies", "spysone", "proxydownload", "plaintext", "geonode"]
    type: str = "http"


class TestSettings(BaseModel):
    url: str = "http://httpbin.org/ip"
    urls: list[str] = Field(
        default_factory=lambda: [
            "http://httpbin.org/ip",
            "https://httpbin.org/ip",
            "https://api.ipify.org?format=json",
        ]
    )
    timeout: float = 8.0
    max_workers: int = 200
    cycle_interval_minutes: int = 180
    scrape_on_startup: bool = True
    store_only_alive: bool = True
    delete_dead_after_check: bool = True


class FilterSettings(BaseModel):
    type: list[str] = Field(default_factory=list)
    country: list[str] = Field(default_factory=list)
    anonymity: list[str] = Field(default_factory=list)
    max_latency_ms: float | None = None


class WorkerSettings(BaseModel):
    enabled: bool = False
    password: str = Field(default_factory=lambda: os.getenv("WORKER_PASSWORD", "change-me"))
    claim_size: int = 100
    assignment_timeout_seconds: int = 120


class AppConfig(BaseModel):
    sources: list[ProxySource]
    test: TestSettings = Field(default_factory=TestSettings)
    filters: FilterSettings = Field(default_factory=FilterSettings)
    workers: WorkerSettings = Field(default_factory=WorkerSettings)


class Settings(BaseModel):
    app_name: str = "ezProxy"
    api_prefix: str = "/api/v1"
    database_url: str = Field(default_factory=lambda: os.getenv("DATABASE_URL", "sqlite:///./ezproxy.db"))
    cors_origins: list[str] = Field(default_factory=lambda: os.getenv("CORS_ORIGINS", "*").split(","))
    admin_password: str = Field(default_factory=lambda: os.getenv("ADMIN_PASSWORD", "admin"))
    admin_token_secret: str = Field(
        default_factory=lambda: os.getenv("ADMIN_TOKEN_SECRET", os.getenv("ADMIN_PASSWORD", "admin"))
    )
    config: AppConfig


def _load_config_file() -> AppConfig:
    if not CONFIG_PATH.exists():
        raise FileNotFoundError(f"Missing configuration file: {CONFIG_PATH}")
    with CONFIG_PATH.open("r", encoding="utf-8") as handle:
        return AppConfig.model_validate(json.load(handle))


@lru_cache
def get_settings() -> Settings:
    return Settings(config=_load_config_file())
