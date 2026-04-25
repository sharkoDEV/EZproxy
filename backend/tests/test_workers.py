from __future__ import annotations

import asyncio

from fastapi.testclient import TestClient
from sqlmodel import Session, select

from backend.app.api.v1.deps import engine, init_db
from backend.app.main import app
from backend.app.models.proxy import Proxy
from backend.app.services.distributed import distributed_queue


def test_worker_claim_and_report_alive_proxy() -> None:
    asyncio.run(distributed_queue.enqueue([Proxy(ip="192.0.2.201", port=8080, type="http")]))
    client = TestClient(app)

    claim = client.post(
        "/api/v1/workers/claim",
        json={"worker_id": "pytest-worker", "password": "change-me", "capacity": 1},
    )
    assert claim.status_code == 200
    jobs = claim.json()["jobs"]
    assert len(jobs) == 1

    report = client.post(
        "/api/v1/workers/report",
        json={
            "worker_id": "pytest-worker",
            "password": "change-me",
            "results": [{**jobs[0], "status": "alive", "latency_ms": 10.5}],
        },
    )
    assert report.status_code == 200
    assert report.json()["stored"] == 1

    init_db()
    with Session(engine) as session:
        proxy = session.exec(select(Proxy).where(Proxy.ip == "192.0.2.201", Proxy.port == 8080)).first()
        assert proxy is not None
        assert proxy.status == "alive"
        session.delete(proxy)
        session.commit()
