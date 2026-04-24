from __future__ import annotations

from celery import Celery

celery_app = Celery("ezproxy", broker="redis://localhost:6379/0")


@celery_app.task
def ping() -> str:
    return "pong"

