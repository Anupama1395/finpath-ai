"""
tools/core/finance.py
---------------------
Pure financial math functions.  No ADK or third-party imports.

All functions raise ValueError for clearly invalid inputs so that the
@tool wrappers (and the agent) receive an explicit error rather than
a silently wrong number.
"""

from __future__ import annotations

import math
from typing import Any

# ── Constants ────────────────────────────────────────────────────────────────

DEFAULT_ANNUAL_RATE: float = 0.05  # 5 % p.a. — stated in every agent response
MAX_SCENARIOS: int = 3


# ── Core functions ────────────────────────────────────────────────────────────


def emergency_fund_months(savings: float, monthly_expenses: float) -> float:
    """Return how many months of expenses the current savings balance covers.

    Args:
        savings: Current liquid savings balance (>= 0).
        monthly_expenses: Total monthly essential expenses (> 0).

    Returns:
        Months covered, rounded to two decimal places.

    Raises:
        ValueError: If monthly_expenses <= 0 or savings < 0.
    """
    if savings < 0:
        raise ValueError(f"savings must be >= 0, got {savings}")
    if monthly_expenses <= 0:
        raise ValueError(f"monthly_expenses must be > 0, got {monthly_expenses}")

    return round(savings / monthly_expenses, 2)


def monthly_cash_flow(
    income: float,
    expenses: float,
    debt_payments: float,
    savings_contribution: float,
) -> float:
    """Return the net monthly surplus after all outflows.

    A negative result means the scenario is not cash-flow feasible at the
    given contribution level.

    Args:
        income: Gross monthly take-home income (> 0).
        expenses: Total monthly essential living expenses (>= 0).
        debt_payments: Total monthly debt service payments (>= 0).
        savings_contribution: Proposed monthly savings/investment amount (>= 0).

    Returns:
        Net surplus (income - expenses - debt_payments - savings_contribution),
        rounded to two decimal places.  Negative means infeasible.

    Raises:
        ValueError: If income <= 0 or any outflow is negative.
    """
    if income <= 0:
        raise ValueError(f"income must be > 0, got {income}")
    for name, val in [
        ("expenses", expenses),
        ("debt_payments", debt_payments),
        ("savings_contribution", savings_contribution),
    ]:
        if val < 0:
            raise ValueError(f"{name} must be >= 0, got {val}")

    return round(income - expenses - debt_payments - savings_contribution, 2)


def project_savings_growth(
    principal: float,
    monthly_contribution: float,
    annual_rate: float = DEFAULT_ANNUAL_RATE,
    months: int = 12,
) -> float:
    """Project future savings value using monthly compound interest.

    Formula:
        FV = principal * (1 + r)^n  +  contribution * ((1 + r)^n - 1) / r
    where r = annual_rate / 12 and n = months.

    When annual_rate == 0 the formula simplifies to:
        FV = principal + contribution * months

    Args:
        principal: Starting balance (>= 0).
        monthly_contribution: Amount added each month (>= 0).
        annual_rate: Annual interest/growth rate as a decimal (>= 0).
                     Defaults to DEFAULT_ANNUAL_RATE (5 % p.a.).
        months: Projection horizon in months (> 0).

    Returns:
        Projected future value, rounded to two decimal places.

    Raises:
        ValueError: For out-of-range inputs.
    """
    if principal < 0:
        raise ValueError(f"principal must be >= 0, got {principal}")
    if monthly_contribution < 0:
        raise ValueError(f"monthly_contribution must be >= 0, got {monthly_contribution}")
    if annual_rate < 0:
        raise ValueError(f"annual_rate must be >= 0, got {annual_rate}")
    if months <= 0:
        raise ValueError(f"months must be > 0, got {months}")

    r = annual_rate / 12

    if r == 0:
        fv = principal + monthly_contribution * months
    else:
        growth = math.pow(1 + r, months)
        fv = principal * growth + monthly_contribution * (growth - 1) / r

    return round(fv, 2)


# ── Scenario comparison ───────────────────────────────────────────────────────

# Required keys every scenario dict must supply.
_REQUIRED_KEYS: frozenset[str] = frozenset(
    ["label", "income", "expenses", "debt_payments", "savings_contribution"]
)

# Optional keys with their defaults.
_OPTIONAL_DEFAULTS: dict[str, Any] = {
    "annual_rate": DEFAULT_ANNUAL_RATE,
    "months": 12,
    "current_savings": 0.0,
}


def compare_scenarios(scenarios: list[dict]) -> list[dict]:
    """Run all three financial calculations for each scenario and return results.

    The agent is responsible for deciding which 2–3 scenarios to compare and
    for supplying their parameters.  This function never invents scenarios.

    Each scenario dict must contain:
        label (str):                  Human-readable scenario name
        income (float):               Monthly take-home income
        expenses (float):             Monthly essential expenses
        debt_payments (float):        Monthly debt service
        savings_contribution (float): Proposed monthly savings amount

    Optional keys (defaults applied if absent):
        annual_rate (float):    Annual growth rate, default 0.05
        months (int):           Projection horizon, default 12
        current_savings (float): Starting savings balance, default 0.0

    Args:
        scenarios: List of 1–MAX_SCENARIOS scenario dicts.

    Returns:
        List of result dicts, each containing the input scenario plus:
            cash_flow (float):          Monthly surplus/deficit
            emergency_fund_months (float): Months covered by current savings
            projected_savings (float):  Future value after `months`
            feasible (bool):            True when cash_flow >= 0
            assumed_annual_rate (float): Rate used (echoed for transparency)
            assumed_months (int):       Horizon used (echoed for transparency)

    Raises:
        ValueError: If scenarios is empty, exceeds MAX_SCENARIOS, or any
                    scenario dict is missing required keys.
    """
    if not scenarios:
        raise ValueError("scenarios must contain at least one entry")
    if len(scenarios) > MAX_SCENARIOS:
        raise ValueError(
            f"compare_scenarios accepts at most {MAX_SCENARIOS} scenarios, "
            f"got {len(scenarios)}"
        )

    results: list[dict] = []

    for i, scenario in enumerate(scenarios):
        # Validate required keys
        missing = _REQUIRED_KEYS - scenario.keys()
        if missing:
            raise ValueError(
                f"Scenario {i} ('{scenario.get('label', '<no label>')}') "
                f"is missing required keys: {sorted(missing)}"
            )

        # Apply optional defaults
        s = {**_OPTIONAL_DEFAULTS, **scenario}

        cf = monthly_cash_flow(
            income=float(s["income"]),
            expenses=float(s["expenses"]),
            debt_payments=float(s["debt_payments"]),
            savings_contribution=float(s["savings_contribution"]),
        )

        ef = emergency_fund_months(
            savings=float(s["current_savings"]),
            monthly_expenses=float(s["expenses"]),
        )

        psg = project_savings_growth(
            principal=float(s["current_savings"]),
            monthly_contribution=float(s["savings_contribution"]),
            annual_rate=float(s["annual_rate"]),
            months=int(s["months"]),
        )

        results.append(
            {
                "label": s["label"],
                "income": float(s["income"]),
                "expenses": float(s["expenses"]),
                "debt_payments": float(s["debt_payments"]),
                "savings_contribution": float(s["savings_contribution"]),
                "current_savings": float(s["current_savings"]),
                "cash_flow": cf,
                "emergency_fund_months": ef,
                "projected_savings": psg,
                "feasible": cf >= 0,
                "assumed_annual_rate": float(s["annual_rate"]),
                "assumed_months": int(s["months"]),
            }
        )

    return results
