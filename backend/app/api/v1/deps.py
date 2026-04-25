from __future__ import annotations

from collections.abc import Generator

from sqlalchemy import inspect, text
from sqlalchemy.engine import Engine
from sqlmodel import Session, SQLModel, create_engine

from backend.app.core.config import get_settings


def _build_engine() -> Engine:
    settings = get_settings()
    connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}
    return create_engine(settings.database_url, echo=False, connect_args=connect_args)


engine = _build_engine()
_initialized = False


def _ensure_schema_columns() -> None:
    inspector = inspect(engine)
    if not inspector.has_table("proxy"):
        return

    columns = {column["name"] for column in inspector.get_columns("proxy")}
    if "is_manual" in columns:
        return

    default = "false" if engine.dialect.name == "postgresql" else "0"
    with engine.begin() as connection:
        connection.execute(text(f"ALTER TABLE proxy ADD COLUMN is_manual BOOLEAN NOT NULL DEFAULT {default}"))


def init_db() -> None:
    global _initialized
    if _initialized:
        return
    SQLModel.metadata.create_all(engine)
    _ensure_schema_columns()
    _initialized = True


def get_session() -> Generator[Session, None, None]:
    init_db()
    with Session(engine) as session:
        yield session
