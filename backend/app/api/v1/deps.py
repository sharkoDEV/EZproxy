from __future__ import annotations

from collections.abc import Generator

from sqlalchemy.engine import Engine
from sqlmodel import Session, SQLModel, create_engine

from backend.app.core.config import get_settings


def _build_engine() -> Engine:
    settings = get_settings()
    connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}
    return create_engine(settings.database_url, echo=False, connect_args=connect_args)


engine = _build_engine()
_initialized = False


def init_db() -> None:
    global _initialized
    if _initialized:
        return
    SQLModel.metadata.create_all(engine)
    _initialized = True


def get_session() -> Generator[Session, None, None]:
    init_db()
    with Session(engine) as session:
        yield session
