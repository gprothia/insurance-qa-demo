"""INS-102: File a claim, UI acceptance tests (Playwright).

Generated from GitHub issue gprothia/insurance-qa-demo#2 following GEMINI.md.
"""

import pytest
from playwright.sync_api import Page, expect

pytestmark = pytest.mark.jira("INS-102")


def test_INS_102_AC8_policyholder_files_claim_in_browser(page: Page, app_url, make_policy):
    policy = make_policy("standard")

    page.goto(f"{app_url}/ui/claims/new?policy_id={policy['id']}")
    expect(page.get_by_label("Policy ID")).to_have_value(policy["id"])
    page.get_by_label("Claim amount").fill("3000")
    page.get_by_label("What happened?").fill("Another driver reversed into my car")
    page.get_by_role("button", name="Submit claim").click()

    expect(page.get_by_test_id("claim-status")).to_have_text("approved")
    expect(page.get_by_test_id("payout")).to_have_text("$2,500.00")
