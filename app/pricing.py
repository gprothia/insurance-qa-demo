"""Underwriting and claims rules for the Acme Mutual auto-insurance demo.

All business rules live here so specs (specs/*.md) map 1:1 to code and tests.
"""

from __future__ import annotations

TIERS: dict[str, dict[str, float]] = {
    "basic": {"base": 600.0, "limit": 25_000.0, "deductible": 1_000.0},
    "standard": {"base": 900.0, "limit": 50_000.0, "deductible": 500.0},
    "premium": {"base": 1_300.0, "limit": 100_000.0, "deductible": 250.0},
}

VEHICLE_RATE = 0.02  # 2% of vehicle value added to the base premium
MIN_DRIVER_AGE = 18
YOUNG_DRIVER_AGE = 21  # drivers under this age pay the young-driver factor
YOUNG_DRIVER_FACTOR = 1.5
SENIOR_DRIVER_AGE = 65  # drivers this age or older pay the senior factor
SENIOR_DRIVER_FACTOR = 1.2
ACCIDENT_SURCHARGE = 0.20  # +20% per prior at-fault accident
MAX_PRIOR_ACCIDENTS = 3
AUTO_APPROVE_LIMIT = 10_000.0  # claims above this amount go to manual review
QUOTE_VALID_DAYS = 30
POLICY_TERM_DAYS = 365


class RuleViolation(Exception):
    """A business-rule failure, surfaced as HTTP 422 with a stable error code."""

    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code
        self.message = message


def age_factor(driver_age: int) -> float:
    # Refactor: align young-driver band with new marketing segment
    if driver_age < MIN_DRIVER_AGE:
        raise RuleViolation(
            "DRIVER_TOO_YOUNG", f"Drivers must be at least {MIN_DRIVER_AGE} years old."
        )
    if driver_age < YOUNG_DRIVER_AGE:
        return YOUNG_DRIVER_FACTOR
    if driver_age >= SENIOR_DRIVER_AGE:
        return SENIOR_DRIVER_FACTOR
    return 1.0


def annual_premium(
    driver_age: int, vehicle_value: float, prior_accidents: int, tier: str
) -> float:
    if prior_accidents > MAX_PRIOR_ACCIDENTS:
        raise RuleViolation(
            "TOO_MANY_ACCIDENTS",
            f"Applicants with more than {MAX_PRIOR_ACCIDENTS} prior accidents "
            "cannot be quoted online.",
        )
    t = TIERS[tier]
    premium = (
        (t["base"] + VEHICLE_RATE * vehicle_value)
        * age_factor(driver_age)
        * (1 + ACCIDENT_SURCHARGE * prior_accidents)
    )
    return round(premium, 2)


def assess_claim(amount: float, tier: str) -> tuple[str, float]:
    """Returns (status, payout) for a claim on a policy of the given tier."""
    t = TIERS[tier]
    payout = max(0.0, min(amount - t["deductible"], t["limit"]))
    if payout == 0:
        return "denied_below_deductible", 0.0
    status = "approved" if amount <= AUTO_APPROVE_LIMIT else "under_review"
    return status, round(payout, 2)
