import pytest
from playwright.sync_api import Page, expect

pytestmark = pytest.mark.jira("INS-101")


def _fill_quote_form(page: Page, app_url: str, age: str) -> None:
    page.goto(f"{app_url}/")
    page.get_by_label("Driver age").fill(age)
    page.get_by_label("Vehicle value").fill("20000")
    page.get_by_label("Prior accidents").fill("0")
    page.get_by_label("Coverage tier").select_option("standard")
    page.get_by_role("button", name="Get quote").click()


def test_INS_101_AC8_quote_via_ui(page: Page, app_url):
    _fill_quote_form(page, app_url, "30")
    expect(page.get_by_test_id("premium")).to_have_text("$1,300.00")
    expect(page.get_by_test_id("tier")).to_have_text("Standard")


def test_INS_101_AC2_young_driver_quote_via_ui(page: Page, app_url):
    _fill_quote_form(page, app_url, "22")
    expect(page.get_by_test_id("premium")).to_have_text("$1,950.00")


def test_INS_101_AC9_underage_error_via_ui(page: Page, app_url):
    _fill_quote_form(page, app_url, "17")
    expect(page.get_by_test_id("error")).to_contain_text("at least 18")
