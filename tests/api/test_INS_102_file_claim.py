"""INS-102: File a first notice of loss (FNOL) claim, API acceptance tests.

Generated from GitHub issue gprothia/insurance-qa-demo#2 following GEMINI.md.
"""

from datetime import date, timedelta

import pytest

pytestmark = pytest.mark.jira("INS-102")


def file_claim(client, policy_id: str, amount: float, incident_date: date | None = None):
    return client.post(
        "/claims",
        json={
            "policy_id": policy_id,
            "incident_date": (incident_date or date.today()).isoformat(),
            "amount": amount,
            "description": "Collision in parking lot",
        },
    )


def test_INS_102_AC1_standard_policy_small_claim_approved(client, make_policy):
    policy = make_policy("standard")
    r = file_claim(client, policy["id"], 3000)
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["status"] == "approved"
    assert body["payout"] == pytest.approx(2500.00)


def test_INS_102_AC2_claim_over_10k_goes_to_review(client, make_policy):
    policy = make_policy("standard")
    r = file_claim(client, policy["id"], 12000)
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["status"] == "under_review"
    assert body["payout"] == pytest.approx(11500.00)


def test_INS_102_AC3_claim_below_deductible_denied(client, make_policy):
    policy = make_policy("standard")
    r = file_claim(client, policy["id"], 400)
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["status"] == "denied_below_deductible"
    assert body["payout"] == pytest.approx(0)


def test_INS_102_AC4_basic_policy_payout_capped_at_limit(client, make_policy):
    policy = make_policy("basic")
    r = file_claim(client, policy["id"], 40000)
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["status"] == "under_review"
    assert body["payout"] == pytest.approx(25000.00)


def test_INS_102_AC5_incident_before_coverage_rejected(client, make_policy):
    policy = make_policy("standard", start_date=date.today())
    r = file_claim(client, policy["id"], 3000, incident_date=date.today() - timedelta(days=1))
    assert r.status_code == 422, r.text
    assert r.json()["detail"]["code"] == "INCIDENT_OUTSIDE_COVERAGE"


def test_INS_102_AC6_unknown_policy_not_found(client):
    r = file_claim(client, "P-unknown0", 3000)
    assert r.status_code == 404, r.text
    assert r.json()["detail"]["code"] == "POLICY_NOT_FOUND"


def test_INS_102_AC7_retrieve_claim_and_unknown_claim(client, make_policy):
    policy = make_policy("standard")
    created = file_claim(client, policy["id"], 3000)
    assert created.status_code == 201, created.text
    claim = created.json()

    r = client.get(f"/claims/{claim['id']}")
    assert r.status_code == 200, r.text
    assert r.json()["status"] == claim["status"]
    assert r.json()["payout"] == pytest.approx(claim["payout"])

    missing = client.get("/claims/C-unknown0")
    assert missing.status_code == 404, missing.text
