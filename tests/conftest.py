import os
from datetime import date

import httpx
import pytest


@pytest.fixture(scope="session")
def app_url() -> str:
    """Base URL of the app under test (local, or the per-PR sandbox Service)."""
    return os.environ.get("BASE_URL", "http://localhost:8000").rstrip("/")


@pytest.fixture
def client(app_url):
    with httpx.Client(base_url=app_url, timeout=10) as c:
        yield c


STANDARD_APPLICANT = {
    "driver_age": 30,
    "vehicle_value": 20000,
    "prior_accidents": 0,
    "tier": "standard",
}


@pytest.fixture
def make_policy(client):
    """Creates a quote and binds it; returns the policy JSON."""

    def _make(tier: str = "standard", start_date: date | None = None) -> dict:
        q = client.post("/quotes", json={**STANDARD_APPLICANT, "tier": tier})
        assert q.status_code == 201, q.text
        body = {"quote_id": q.json()["id"]}
        if start_date:
            body["start_date"] = start_date.isoformat()
        p = client.post("/policies", json=body)
        assert p.status_code == 201, p.text
        return p.json()

    return _make
