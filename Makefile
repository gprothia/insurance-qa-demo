.PHONY: install run test test-api test-ui

install:
	python3 -m venv .venv
	.venv/bin/pip install -r requirements.txt -r requirements-test.txt
	.venv/bin/playwright install chromium

run:
	.venv/bin/uvicorn app.main:app --reload --port 8000

test-api:
	.venv/bin/pytest tests/api -v

test-ui:
	.venv/bin/pytest tests/ui -v --browser chromium

test:
	.venv/bin/pytest -v --browser chromium
