# Test-generation rules for Gemini / Antigravity agents

You turn specs (Jira stories via the Atlassian MCP server, or `specs/*.md`) into
executable tests for the Acme Mutual app. Follow these rules exactly.

## Inputs
- The spec's **acceptance criteria (ACn)** are the source of truth. Read `openapi.json`
  (`GET /openapi.json` on the running app) for request/response shapes.
- Never change app code to make a test pass. If the spec and app disagree, report it.

## Layout and naming
- API tests: `tests/api/test_<JIRA_KEY_WITH_UNDERSCORES>_<slug>.py` (e.g. `test_INS_102_file_claim.py`).
- UI tests: `tests/ui/test_<JIRA_KEY>_<slug>_ui.py`.
- One test per acceptance criterion: `test_<JIRA_KEY>_AC<n>_<short_description>`.
- Mark every module with `pytestmark = pytest.mark.jira("<JIRA-KEY>")`.

## API tests
- Use the `client` fixture (an `httpx.Client` pointed at `BASE_URL`) and `make_policy`
  from `tests/conftest.py`. Do not hardcode hosts or ports.
- Assert the status code first (include `r.text` in the message), then the body.
- Compare money with `pytest.approx`. Compare error codes via `r.json()["detail"]["code"]`.
- Create the data each test needs through the API; tests must not depend on each other.

## UI tests (Playwright, pytest-playwright)
- Use the `page` fixture and `app_url`. Locate elements with `get_by_label`, `get_by_role`
  and `get_by_test_id` only; no CSS/XPath selectors and no `wait_for_timeout`/sleeps.
- Assert with `playwright.sync_api.expect` (it auto-waits).

## Definition of done
- `pytest tests/api` and `pytest tests/ui --browser chromium` pass against the local app
  (`make run`) with every AC covered. Print an AC → test table when finished.
