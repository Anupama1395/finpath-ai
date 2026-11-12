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

# ── Debt math ─────────────────────────────────────────────────────────────────

# Maximum months to iterate before declaring a payment insufficient
_MAX_PAYOFF_MONTHS: int = 1200  # 100 years


def debt_payoff_months(
    balance: float,
    monthly_payment: float,
    annual_rate: float,
) -> dict:
    """Calculate months to pay off a debt and the total interest paid.

    Uses the standard amortisation formula.  When annual_rate == 0 the
    payoff is simply ceil(balance / monthly_payment).

    Args:
        balance: Outstanding debt balance (> 0).
        monthly_payment: Fixed monthly payment amount (> 0).
        annual_rate: Annual interest rate as a decimal (>= 0, e.g. 0.055).

    Returns:
        Dict with keys:
            months_to_payoff (int):       Number of full months to pay off the debt.
            total_interest_paid (float):  Total interest paid, rounded to 2 dp.
            total_paid (float):           Total amount paid (balance + interest), 2 dp.
            summary (str):                Plain-language one-liner for the agent.

    Raises:
        ValueError: If balance <= 0, monthly_payment <= 0, annual_rate < 0.
                    If monthly_payment does not exceed monthly interest, returns a
                    "never pays off" result instead of raising (per plan requirement).
    """
    if balance <= 0:
        raise ValueError(f"balance must be > 0, got {balance}")
    if monthly_payment <= 0:
        raise ValueError(f"monthly_payment must be > 0, got {monthly_payment}")
    if annual_rate < 0:
        raise ValueError(f"annual_rate must be >= 0, got {annual_rate}")

    r = annual_rate / 12

    if r == 0:
        n = math.ceil(balance / monthly_payment)
        total_paid = round(monthly_payment * (n - 1) + (balance % monthly_payment or monthly_payment), 2)
        return {
            "months_to_payoff": n,
            "total_interest_paid": 0.0,
            "total_paid": total_paid,
            "summary": (
                f"At ${monthly_payment:,.2f}/month with no interest, the debt of "
                f"${balance:,.2f} will be paid off in {n} months "
                f"with no interest charged."
            ),
        }

    monthly_interest_charge = balance * r
    if monthly_payment <= monthly_interest_charge:
        # Per plan: return a clear result instead of raising or looping infinitely
        return {
            "months_to_payoff": None,
            "total_interest_paid": None,
            "total_paid": None,
            "summary": (
                f"The monthly payment of ${monthly_payment:,.2f} does not cover the "
                f"first month's interest of ${monthly_interest_charge:,.2f}. "
                f"At this payment level, the debt will never be paid off."
            ),
        }

    # Analytical formula: n = -log(1 - r*B/P) / log(1+r)
    n_exact = -math.log(1 - r * balance / monthly_payment) / math.log(1 + r)
    n = math.ceil(n_exact)

    # Simulate to get exact totals
    remaining = balance
    total_paid_acc = 0.0
    for _ in range(n):
        ic = remaining * r
        pp = min(monthly_payment - ic, remaining)
        total_paid_acc += ic + pp
        remaining -= pp
        if remaining <= 0:
            break

    total_paid = round(total_paid_acc, 2)
    total_interest_paid = round(total_paid - balance, 2)

    return {
        "months_to_payoff": n,
        "total_interest_paid": total_interest_paid,
        "total_paid": total_paid,
        "summary": (
            f"Paying ${monthly_payment:,.2f}/month, the debt of ${balance:,.2f} "
            f"at {annual_rate*100:.2f}% APR will be paid off in {n} months "
            f"({n // 12} yr {n % 12} mo) with ${total_interest_paid:,.2f} total interest."
        ),
    }


def debt_vs_invest(
    balance: float,
    annual_debt_rate: float,
    monthly_surplus: float,
    min_monthly_payment: float,
    annual_invest_rate: float = DEFAULT_ANNUAL_RATE,
    months: int = 60,
) -> dict:
    """Compare paying down debt first vs. investing the surplus immediately.

    Both strategies receive the **same total monthly budget** (monthly_surplus)
    for the **same horizon** (months).  Net worth = investments − remaining debt
    (with accrued interest) at the end of the horizon.

    Strategy A — Debt first:
      Each month: put the entire budget on the debt until it reaches zero,
      then invest the entire budget for the remainder of the horizon.

    Strategy B — Invest first:
      Each month: pay only min_monthly_payment on the debt and invest the rest
      (budget − min_monthly_payment).  The debt accrues interest every month.

    Both strategies accrue investment growth and debt interest each month before
    making payments.  Net worth is computed the same way for both.

    Args:
        balance: Outstanding debt balance (> 0).
        annual_debt_rate: Annual interest rate on the debt (>= 0).
        monthly_surplus: Total monthly budget available (must be > min_monthly_payment
                         for Strategy B to be viable).
        min_monthly_payment: Minimum monthly debt payment under Strategy B (> 0 and
                             must cover the first month's interest, otherwise Strategy B
                             is not viable and a ValueError is raised).
        annual_invest_rate: Expected annual investment return as a decimal (>= 0).
                            Defaults to DEFAULT_ANNUAL_RATE (5% p.a.).
        months: Comparison horizon in months (> 0). Default 60 (5 years).

    Returns:
        Dict with keys:
            strategy_a_net_worth (float): Net worth at end of horizon under Strategy A.
            strategy_b_net_worth (float): Net worth at end of horizon under Strategy B.
            recommended (str):            "debt_first" | "invest_first" | "neutral"
            payoff_months_a (int | None): Month in which debt reaches zero under A,
                                          or None if it is not paid off within the horizon.
            payoff_months_b (int | None): Month in which debt reaches zero under B,
                                          or None if it is not paid off within the horizon.
            assumed_invest_rate (float):  Rate used (echoed for transparency).
            assumed_months (int):         Horizon used (echoed for transparency).

    Raises:
        ValueError: For invalid inputs or when Strategy B is not viable.
    """
    if balance <= 0:
        raise ValueError(f"balance must be > 0, got {balance}")
    if annual_debt_rate < 0:
        raise ValueError(f"annual_debt_rate must be >= 0, got {annual_debt_rate}")
    if monthly_surplus <= 0:
        raise ValueError(f"monthly_surplus must be > 0, got {monthly_surplus}")
    if min_monthly_payment <= 0:
        raise ValueError(f"min_monthly_payment must be > 0, got {min_monthly_payment}")
    if annual_invest_rate < 0:
        raise ValueError(f"annual_invest_rate must be >= 0, got {annual_invest_rate}")
    if months <= 0:
        raise ValueError(f"months must be > 0, got {months}")
    if monthly_surplus <= min_monthly_payment:
        raise ValueError(
            f"monthly_surplus ({monthly_surplus}) must be greater than "
            f"min_monthly_payment ({min_monthly_payment}) so there is something to invest."
        )
    # Check Strategy B is viable: min payment must cover first month's interest
    first_month_interest = balance * (annual_debt_rate / 12)
    if annual_debt_rate > 0 and min_monthly_payment <= first_month_interest:
        raise ValueError(
            f"min_monthly_payment (${min_monthly_payment:.2f}) must exceed the first "
            f"month's interest (${first_month_interest:.2f}) to prevent the debt from growing."
        )

    r_d = annual_debt_rate / 12
    r_i = annual_invest_rate / 12

    def _simulate(debt_first: bool) -> tuple[float, int | None]:
        """Run one strategy and return (net_worth, payoff_month_or_None)."""
        debt = float(balance)
        invest = 0.0
        payoff_month: int | None = None
        for m in range(1, months + 1):
            # 1. Accrue interest on both sides
            debt   *= (1 + r_d)
            invest *= (1 + r_i)
            # 2. Decide payment
            if debt_first:
                pay = min(debt, monthly_surplus)
            else:
                pay = min(debt, min_monthly_payment)
            # 3. Apply payment and invest the rest
            debt   -= pay
            invest += monthly_surplus - pay
            # 4. Record payoff
            if debt <= 0 and payoff_month is None:
                debt = 0.0
                payoff_month = m
        net_worth = round(invest - debt, 2)
        return net_worth, payoff_month

    nw_a, pm_a = _simulate(debt_first=True)
    nw_b, pm_b = _simulate(debt_first=False)

    delta = nw_a - nw_b
    if abs(delta) < 1.0:
        recommended = "neutral"
    elif delta > 0:
        recommended = "debt_first"
    else:
        recommended = "invest_first"

    return {
        "strategy_a_net_worth": nw_a,
        "strategy_b_net_worth": nw_b,
        "recommended": recommended,
        "payoff_months_a": pm_a,
        "payoff_months_b": pm_b,
        "assumed_invest_rate": annual_invest_rate,
        "assumed_months": months,
    }


# ── Stress test ───────────────────────────────────────────────────────────────

DEFAULT_EMERGENCY_TARGET: float = 3.0  # months


def stress_test(
    income: float,
    expenses: float,
    debt_payments: float,
    savings_contribution: float,
    current_savings: float,
    income_shock_pct: float = 0.0,
    expenses_shock_pct: float = 0.0,
    emergency_target_months: float = DEFAULT_EMERGENCY_TARGET,
) -> dict:
    """Re-run cash flow and emergency fund under an income or expense shock.

    Applies percentage shocks to income and/or expenses, then recalculates
    monthly_cash_flow and emergency_fund_months to assess resilience.

    Args:
        income: Monthly take-home income (> 0).
        expenses: Monthly essential expenses (>= 0).
        debt_payments: Monthly debt service payments (>= 0).
        savings_contribution: Monthly savings/investment contribution (>= 0).
        current_savings: Current liquid savings balance (>= 0).
        income_shock_pct: % change to income, e.g. -10 for a 10% income drop.
                          Default 0 (no income shock).
        expenses_shock_pct: % change to expenses, e.g. +10 for 10% higher costs.
                            Default 0 (no expense shock).
        emergency_target_months: Minimum months of emergency coverage considered
                                 adequate. Default 3.

    Returns:
        Dict with keys:
            shocked_income (float):            Income after shock.
            shocked_expenses (float):          Expenses after shock.
            shocked_cash_flow (float):         Monthly surplus after shock.
            shocked_emergency_months (float):  Emergency coverage after shock.
            still_feasible (bool):             shocked_cash_flow >= 0.
            still_meets_target (bool):         shocked_emergency_months >= emergency_target_months.
            income_shock_pct (float):          Echoed for transparency.
            expenses_shock_pct (float):        Echoed for transparency.
            emergency_target_months (float):   Echoed for transparency.

    Raises:
        ValueError: For out-of-range base inputs (delegates to called functions).
    """
    shocked_income   = round(income   * (1 + income_shock_pct   / 100), 2)
    shocked_expenses = round(expenses * (1 + expenses_shock_pct / 100), 2)

    # Clamp to avoid negative values being passed to the inner functions
    shocked_income   = max(shocked_income,   0.01)
    shocked_expenses = max(shocked_expenses, 0.0)

    cf = monthly_cash_flow(
        income=shocked_income,
        expenses=shocked_expenses,
        debt_payments=debt_payments,
        savings_contribution=savings_contribution,
    )

    ef = emergency_fund_months(
        savings=current_savings,
        monthly_expenses=max(shocked_expenses, 0.01),
    )

    return {
        "shocked_income":           shocked_income,
        "shocked_expenses":         shocked_expenses,
        "shocked_cash_flow":        cf,
        "shocked_emergency_months": ef,
        "still_feasible":           cf >= 0,
        "still_meets_target":       ef >= emergency_target_months,
        "income_shock_pct":         income_shock_pct,
        "expenses_shock_pct":       expenses_shock_pct,
        "emergency_target_months":  emergency_target_months,
    }


# ── Savings headroom ──────────────────────────────────────────────────────────


def savings_headroom(
    income: float,
    expenses: float,
    current_savings_contribution: float,
) -> dict:
    """Calculate how much additional monthly savings capacity is available.

    Args:
        income: Monthly take-home income (> 0).
        expenses: Monthly essential living expenses (>= 0).
        current_savings_contribution: Current monthly savings/investment amount (>= 0).

    Returns:
        Dict with keys:
            free_cash (float):               Income minus expenses minus current contribution.
            can_save_more (bool):            True when free_cash > 0.
            max_additional_savings (float):  Maximum additional monthly savings (0 if negative).
            summary (str):                   Plain-language one-liner for the agent.

    Raises:
        ValueError: For invalid inputs.
    """
    if income <= 0:
        raise ValueError(f"income must be > 0, got {income}")
    if expenses < 0:
        raise ValueError(f"expenses must be >= 0, got {expenses}")
    if current_savings_contribution < 0:
        raise ValueError(
            f"current_savings_contribution must be >= 0, got {current_savings_contribution}"
        )

    free_cash = round(income - expenses - current_savings_contribution, 2)
    max_additional = round(max(0.0, free_cash), 2)
    can_save_more = free_cash > 0

    if can_save_more:
        summary = (
            f"After expenses (${expenses:,.2f}) and your current savings contribution "
            f"(${current_savings_contribution:,.2f}), you have ${free_cash:,.2f}/month "
            f"free — you could save up to ${max_additional:,.2f}/month more."
        )
    else:
        summary = (
            f"Your current expenses (${expenses:,.2f}) and savings contribution "
            f"(${current_savings_contribution:,.2f}) already consume all of your income. "
            f"There is no additional headroom to save more right now."
        )

    return {
        "free_cash": free_cash,
        "can_save_more": can_save_more,
        "max_additional_savings": max_additional,
        "summary": summary,
    }


# ── Emergency fund check ──────────────────────────────────────────────────────


def emergency_fund_check(
    current_savings: float,
    monthly_expenses: float,
) -> dict:
    """Assess whether current savings provide an adequate emergency fund.

    Standard guideline: 3–6 months of essential expenses.

    Args:
        current_savings: Current liquid savings balance (>= 0).
        monthly_expenses: Monthly essential living expenses (> 0).

    Returns:
        Dict with keys:
            months_covered (float):   Months of expenses covered (rounded to 2 dp).
            status (str):             "low" (< 3 mo), "ok" (3–6 mo), "strong" (> 6 mo).
            gap_to_3_months (float):  Additional savings needed to reach 3 months (0 if already there).
            summary (str):            Plain-language one-liner for the agent.

    Raises:
        ValueError: For invalid inputs.
    """
    if current_savings < 0:
        raise ValueError(f"current_savings must be >= 0, got {current_savings}")
    if monthly_expenses <= 0:
        raise ValueError(f"monthly_expenses must be > 0, got {monthly_expenses}")

    months_covered = round(current_savings / monthly_expenses, 2)
    gap = round(max(0.0, 3 * monthly_expenses - current_savings), 2)

    if months_covered < 3:
        status = "low"
        summary = (
            f"Your savings cover only {months_covered} months of expenses — "
            f"below the 3-month minimum guideline. "
            f"You need ${gap:,.2f} more to reach 3 months of coverage."
        )
    elif months_covered <= 6:
        status = "ok"
        summary = (
            f"Your savings cover {months_covered} months of expenses — "
            f"within the healthy 3–6 month range."
        )
    else:
        status = "strong"
        summary = (
            f"Your savings cover {months_covered} months of expenses — "
            f"above the 6-month upper guideline. Your emergency fund is strong."
        )

    return {
        "months_covered": months_covered,
        "status": status,
        "gap_to_3_months": gap,
        "summary": summary,
    }
