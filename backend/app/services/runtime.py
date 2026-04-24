from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any


@dataclass
class RuntimeStats:
    phase: str = "idle"
    cycle_active: bool = False
    cycle_started_at: str | None = None
    source: str | None = None
    scraped: int = 0
    queued: int = 0
    tested: int = 0
    valid: int = 0
    stored: int = 0
    valid_stock: int = 0
    total_stock: int = 0
    last_error: str | None = None
    updated_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())

    def as_dict(self) -> dict[str, Any]:
        return {
            "phase": self.phase,
            "cycle_active": self.cycle_active,
            "cycle_started_at": self.cycle_started_at,
            "source": self.source,
            "scraped": self.scraped,
            "queued": self.queued,
            "tested": self.tested,
            "valid": self.valid,
            "stored": self.stored,
            "valid_stock": self.valid_stock,
            "total_stock": self.total_stock,
            "last_error": self.last_error,
            "updated_at": self.updated_at,
        }


runtime_stats = RuntimeStats()


def update_runtime_stats(**kwargs: Any) -> RuntimeStats:
    for key, value in kwargs.items():
        if hasattr(runtime_stats, key):
            setattr(runtime_stats, key, value)
    runtime_stats.updated_at = datetime.now(UTC).isoformat()
    return runtime_stats


def start_cycle(phase: str) -> RuntimeStats:
    now = datetime.now(UTC).isoformat()
    return update_runtime_stats(
        phase=phase,
        cycle_active=True,
        cycle_started_at=now,
        source=None,
        scraped=0,
        queued=0,
        tested=0,
        valid=0,
        stored=0,
        last_error=None,
    )


def finish_cycle(phase: str = "idle") -> RuntimeStats:
    return update_runtime_stats(phase=phase, cycle_active=False, source=None)
