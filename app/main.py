"""Acme Mutual auto-insurance demo app: quotes, policies and claims (REST API + minimal UI)."""

from __future__ import annotations

import uuid
from datetime import date, timedelta
from pathlib import Path
from typing import Literal

from fastapi import FastAPI, Form, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field

from app import pricing
from app.pricing import RuleViolation

app = FastAPI(title="Acme Mutual Insurance API", version="1.0.0")
templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))
templates.env.filters["money"] = lambda v: f"${v:,.2f}"

Tier = Literal["basic", "standard", "premium"]

# In-memory stores: fine for an ephemeral per-PR sandbox.
QUOTES: dict[str, dict] = {}
POLICIES: dict[str, dict] = {}
CLAIMS: dict[str, dict] = {}


# ---------- Models ----------
class QuoteRequest(BaseModel):
    driver_age: int = Field(ge=0, le=120)
    vehicle_value: float = Field(gt=0, le=500_000)
    prior_accidents: int = Field(ge=0, default=0)
    tier: Tier


class Quote(BaseModel):
    id: str
    tier: Tier
    annual_premium: float
    coverage_limit: float
    deductible: float
    expires_on: date


class PolicyRequest(BaseModel):
    quote_id: str
    start_date: date | None = None


class Policy(BaseModel):
    id: str
    quote_id: str
    tier: Tier
    annual_premium: float
    coverage_limit: float
    deductible: float
    start_date: date
    end_date: date
    status: Literal["active"]


class ClaimRequest(BaseModel):
    policy_id: str
    incident_date: date
    amount: float = Field(gt=0)
    description: str = ""


class Claim(BaseModel):
    id: str
    policy_id: str
    incident_date: date
    amount: float
    payout: float
    status: Literal["approved", "under_review", "denied_below_deductible"]
    description: str


# ---------- Domain operations (shared by API and UI) ----------
def _new_id(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:8]}"


def create_quote(req: QuoteRequest) -> dict:
    premium = pricing.annual_premium(
        req.driver_age, req.vehicle_value, req.prior_accidents, req.tier
    )
    tier = pricing.TIERS[req.tier]
    quote = {
        "id": _new_id("Q"),
        "tier": req.tier,
        "annual_premium": premium,
        "coverage_limit": tier["limit"],
        "deductible": tier["deductible"],
        "expires_on": date.today() + timedelta(days=pricing.QUOTE_VALID_DAYS),
    }
    QUOTES[quote["id"]] = quote
    return quote


def bind_policy(req: PolicyRequest) -> dict:
    quote = QUOTES.get(req.quote_id)
    if quote is None:
        raise HTTPException(404, {"code": "QUOTE_NOT_FOUND", "message": "Unknown quote."})
    start = req.start_date or date.today()
    if start < date.today():
        raise RuleViolation("START_DATE_IN_PAST", "Policy start date cannot be in the past.")
    policy = {
        "id": _new_id("P"),
        "quote_id": quote["id"],
        "tier": quote["tier"],
        "annual_premium": quote["annual_premium"],
        "coverage_limit": quote["coverage_limit"],
        "deductible": quote["deductible"],
        "start_date": start,
        "end_date": start + timedelta(days=pricing.POLICY_TERM_DAYS),
        "status": "active",
    }
    POLICIES[policy["id"]] = policy
    return policy


def file_claim(req: ClaimRequest) -> dict:
    policy = POLICIES.get(req.policy_id)
    if policy is None:
        raise HTTPException(404, {"code": "POLICY_NOT_FOUND", "message": "Unknown policy."})
    if not policy["start_date"] <= req.incident_date <= policy["end_date"]:
        raise RuleViolation(
            "INCIDENT_OUTSIDE_COVERAGE",
            "Incident date is outside the policy coverage period.",
        )
    status, payout = pricing.assess_claim(req.amount, policy["tier"])
    claim = {
        "id": _new_id("C"),
        "policy_id": policy["id"],
        "incident_date": req.incident_date,
        "amount": req.amount,
        "payout": payout,
        "status": status,
        "description": req.description,
    }
    CLAIMS[claim["id"]] = claim
    return claim


# ---------- REST API ----------
@app.exception_handler(RuleViolation)
async def _rule_violation(_: Request, exc: RuleViolation):
    from fastapi.responses import JSONResponse

    return JSONResponse(
        status_code=422, content={"detail": {"code": exc.code, "message": exc.message}}
    )


@app.get("/healthz")
def healthz() -> dict:
    return {"status": "ok"}


@app.post("/quotes", response_model=Quote, status_code=201)
def api_create_quote(req: QuoteRequest):
    return create_quote(req)


@app.get("/quotes/{quote_id}", response_model=Quote)
def api_get_quote(quote_id: str):
    if quote_id not in QUOTES:
        raise HTTPException(404, {"code": "QUOTE_NOT_FOUND", "message": "Unknown quote."})
    return QUOTES[quote_id]


@app.post("/policies", response_model=Policy, status_code=201)
def api_bind_policy(req: PolicyRequest):
    return bind_policy(req)


@app.get("/policies/{policy_id}", response_model=Policy)
def api_get_policy(policy_id: str):
    if policy_id not in POLICIES:
        raise HTTPException(404, {"code": "POLICY_NOT_FOUND", "message": "Unknown policy."})
    return POLICIES[policy_id]


@app.post("/claims", response_model=Claim, status_code=201)
def api_file_claim(req: ClaimRequest):
    return file_claim(req)


@app.get("/claims/{claim_id}", response_model=Claim)
def api_get_claim(claim_id: str):
    if claim_id not in CLAIMS:
        raise HTTPException(404, {"code": "CLAIM_NOT_FOUND", "message": "Unknown claim."})
    return CLAIMS[claim_id]


# ---------- UI ----------
@app.get("/", response_class=HTMLResponse)
def ui_quote_form(request: Request):
    return templates.TemplateResponse(request, "quote_form.html", {"tiers": pricing.TIERS})


@app.post("/ui/quote", response_class=HTMLResponse)
def ui_quote(
    request: Request,
    driver_age: int = Form(...),
    vehicle_value: float = Form(...),
    prior_accidents: int = Form(0),
    tier: Tier = Form(...),
):
    try:
        quote = create_quote(
            QuoteRequest(
                driver_age=driver_age,
                vehicle_value=vehicle_value,
                prior_accidents=prior_accidents,
                tier=tier,
            )
        )
    except RuleViolation as e:
        return templates.TemplateResponse(
            request, "quote_form.html", {"tiers": pricing.TIERS, "error": e.message},
            status_code=422,
        )
    return templates.TemplateResponse(request, "quote_result.html", {"quote": quote})


@app.post("/ui/bind", response_class=HTMLResponse)
def ui_bind(request: Request, quote_id: str = Form(...)):
    policy = bind_policy(PolicyRequest(quote_id=quote_id))
    return templates.TemplateResponse(request, "policy_result.html", {"policy": policy})


@app.get("/ui/claims/new", response_class=HTMLResponse)
def ui_claim_form(request: Request, policy_id: str = ""):
    return templates.TemplateResponse(
        request, "claim_form.html", {"policy_id": policy_id, "today": date.today()}
    )


@app.post("/ui/claims", response_class=HTMLResponse)
def ui_file_claim(
    request: Request,
    policy_id: str = Form(...),
    incident_date: date = Form(...),
    amount: float = Form(...),
    description: str = Form(""),
):
    try:
        claim = file_claim(
            ClaimRequest(
                policy_id=policy_id,
                incident_date=incident_date,
                amount=amount,
                description=description,
            )
        )
    except (RuleViolation, HTTPException) as e:
        message = e.message if isinstance(e, RuleViolation) else e.detail["message"]
        return templates.TemplateResponse(
            request, "claim_form.html",
            {"policy_id": policy_id, "today": date.today(), "error": message},
            status_code=422,
        )
    return templates.TemplateResponse(request, "claim_result.html", {"claim": claim})
