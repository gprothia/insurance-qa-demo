from datetime import date, timedelta

import pytest

from tests.conftest import STANDARD_APPLICANT

pytestmark = pytest.mark.jira("INS-101")


def _quote(client, **overrides):
    return client.post("/quotes", json={**STANDARD_APPLICANT, **overrides})


def test_INS_101_AC1_standard_quote(client):
    r = _quote(client)
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["annual_premium"] == pytest.approx(1300.00)
    assert body["coverage_limit"] == pytest.approx(50000)
    assert body["deductible"] == pytest.approx(500)
    assert body["expires_on"] == (date.today() + timedelta(days=30)).isoformat()


def test_INS_101_AC2_young_driver_factor(client):
    r = _quote(client, driver_age=22)
    assert r.status_code == 201, r.text
    assert r.json()["annual_premium"] == pytest.approx(1950.00)


def test_INS_101_AC3_senior_driver_factor(client):
    r = _quote(client, driver_age=70)
    assert r.status_code == 201, r.text
    assert r.json()["annual_premium"] == pytest.approx(1560.00)


def test_INS_101_AC4_prior_accident_surcharge(client):
    r = _quote(client, prior_accidents=2)
    assert r.status_code == 201, r.text
    assert r.json()["annual_premium"] == pytest.approx(1820.00)


def test_INS_101_AC5_driver_too_young(client):
    r = _quote(client, driver_age=17)
    assert r.status_code == 422, r.text
    assert r.json()["detail"]["code"] == "DRIVER_TOO_YOUNG"


def test_INS_101_AC6_too_many_accidents(client):
    r = _quote(client, prior_accidents=4)
    assert r.status_code == 422, r.text
    assert r.json()["detail"]["code"] == "TOO_MANY_ACCIDENTS"


def test_INS_101_AC7_unknown_tier_rejected(client):
    r = _quote(client, tier="gold")
    assert r.status_code == 422, r.text
