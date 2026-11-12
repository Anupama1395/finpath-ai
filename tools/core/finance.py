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


# ── Financial health check ─────────────────────────────────────────────────────


def financial_health_check(
    income: float,
    expenses: float,
    monthly_savings_contribution: float,
    current_savings: float,
    debt_balance: float,
    annual_debt_rate: float,
    monthly_debt_payment: float,
    assumed_invest_rate: float = 0.05,
) -> dict:
    """Compute an overall financial health score (0–100) with a sub-score breakdown.

    Sub-scores (each 0–25, summed to 0–100):

    1. Cash-flow score (0–25):
       - cash_flow = income - expenses - monthly_debt_payment - monthly_savings_contribution
       - cash_flow >= 0                   → 25
       - cash_flow >= -income * 0.05      → 15  (mild deficit, < 5% of income)
       - cash_flow < -income * 0.05       → 0   (significant deficit)

    2. Emergency-fund score (0–25):
       - months = current_savings / expenses  (0 when expenses == 0)
       - months >= 6                          → 25
       - months >= 3                          → 20
       - months >= 1                          → 10
       - months < 1                           → 0

    3. Debt-burden score (0–25):
       - dti = monthly_debt_payment / income  (0 when income == 0)
       - dti == 0                             → 25
       - dti <= 0.15                          → 22
       - dti <= 0.28                          → 15
       - dti <= 0.36                          → 8
       - dti > 0.36                           → 0

    4. Savings-rate score (0–25):
       - rate = monthly_savings_contribution / income  (0 when income == 0)
       - rate >= 0.20                         → 25
       - rate >= 0.10                         → 18
       - rate >= 0.05                         → 10
       - rate > 0                             → 5
       - rate == 0                            → 0

    Priority rules (deterministic, applied in order, first match wins):
      1. cash_flow < 0                       → "Cut expenses or raise income first"
      2. ef_months < 1                       → "Build a 1-month starter emergency fund"
      3. annual_debt_rate > assumed_invest_rate → "Put extra cash toward high-interest debt"
      4. ef_months < 3                       → "Grow emergency fund to 3 months"
      5. (default)                           → "Start investing the surplus"

    Args:
        income: Monthly take-home income (> 0).
        expenses: Monthly essential living expenses (>= 0).
        monthly_savings_contribution: Current monthly savings/investment amount (>= 0).
        current_savings: Current liquid savings balance (>= 0).
        debt_balance: Outstanding debt balance (>= 0).
        annual_debt_rate: Annual interest rate on debt as a decimal (>= 0, e.g. 0.07).
        monthly_debt_payment: Monthly debt payment (>= 0).
        assumed_invest_rate: Expected annual investment return as decimal (>= 0, default 0.05).

    Returns:
        Dict with keys:
            score (int):                    Overall score 0–100.
            cash_flow_score (int):          Sub-score 0–25.
            emergency_fund_score (int):     Sub-score 0–25.
            debt_burden_score (int):        Sub-score 0–25.
            savings_rate_score (int):       Sub-score 0–25.
            cash_flow (float):              Monthly surplus/deficit.
            emergency_fund_months (float):  Months of expenses covered.
            debt_to_income_ratio (float):   Monthly debt payment / income.
            savings_rate (float):           Monthly savings / income.
            priorities (list[str]):         Top priorities in order (up to 3).
            summary (str):                  Plain-language one-liner for the agent.

    Raises:
        ValueError: For clearly invalid inputs.
    """
    if income <= 0:
        raise ValueError(f"income must be > 0, got {income}")
    for name, val in [
        ("expenses", expenses),
        ("monthly_savings_contribution", monthly_savings_contribution),
        ("current_savings", current_savings),
        ("debt_balance", debt_balance),
        ("annual_debt_rate", annual_debt_rate),
        ("monthly_debt_payment", monthly_debt_payment),
        ("assumed_invest_rate", assumed_invest_rate),
    ]:
        if val < 0:
            raise ValueError(f"{name} must be >= 0, got {val}")

    # ── Derived metrics ────────────────────────────────────────────────────────
    cash_flow = round(
        income - expenses - monthly_debt_payment - monthly_savings_contribution, 2
    )
    ef_months = round(current_savings / expenses, 2) if expenses > 0 else 0.0
    dti       = round(monthly_debt_payment / income, 4)
    srate     = round(monthly_savings_contribution / income, 4)

    # ── Sub-scores ─────────────────────────────────────────────────────────────
    # 1. Cash-flow score
    if cash_flow >= 0:
        cf_score = 25
    elif cash_flow >= -income * 0.05:
        cf_score = 15
    else:
        cf_score = 0

    # 2. Emergency-fund score
    if ef_months >= 6:
        ef_score = 25
    elif ef_months >= 3:
        ef_score = 20
    elif ef_months >= 1:
        ef_score = 10
    else:
        ef_score = 0

    # 3. Debt-burden score
    if dti == 0:
        db_score = 25
    elif dti <= 0.15:
        db_score = 22
    elif dti <= 0.28:
        db_score = 15
    elif dti <= 0.36:
        db_score = 8
    else:
        db_score = 0

    # 4. Savings-rate score
    if srate >= 0.20:
        sr_score = 25
    elif srate >= 0.10:
        sr_score = 18
    elif srate >= 0.05:
        sr_score = 10
    elif srate > 0:
        sr_score = 5
    else:
        sr_score = 0

    score = cf_score + ef_score + db_score + sr_score

    # ── Priorities (first-match, up to 3) ─────────────────────────────────────
    all_priorities = []
    if cash_flow < 0:
        all_priorities.append("Cut expenses or raise income first")
    if ef_months < 1:
        all_priorities.append("Build a 1-month starter emergency fund")
    if annual_debt_rate > assumed_invest_rate:
        all_priorities.append("Put extra cash toward high-interest debt")
    if ef_months < 3:
        all_priorities.append("Grow emergency fund to 3 months")
    if not all_priorities:
        all_priorities.append("Start investing the surplus")
    priorities = all_priorities[:3]

    # ── Summary ────────────────────────────────────────────────────────────────
    if score >= 75:
        health_label = "strong"
    elif score >= 50:
        health_label = "moderate"
    elif score >= 25:
        health_label = "needs attention"
    else:
        health_label = "critical"

    summary = (
        f"Financial health score: {score}/100 ({health_label}). "
        f"Cash flow: ${cash_flow:,.2f}/mo | "
        f"Emergency fund: {ef_months:.1f} months | "
        f"Debt-to-income: {dti*100:.1f}% | "
        f"Savings rate: {srate*100:.1f}%. "
        f"Top priority: {priorities[0]}."
    )

    return {
        "score":                  score,
        "cash_flow_score":        cf_score,
        "emergency_fund_score":   ef_score,
        "debt_burden_score":      db_score,
        "savings_rate_score":     sr_score,
        "cash_flow":              cash_flow,
        "emergency_fund_months":  ef_months,
        "debt_to_income_ratio":   dti,
        "savings_rate":           srate,
        "priorities":             priorities,
        "summary":                summary,
    }


# ── Goal plan ──────────────────────────────────────────────────────────────────


def goal_plan(
    target_amount: float,
    months_to_goal: int,
    current_saved: float,
    monthly_headroom: float,
    annual_rate: float = 0.0,
) -> dict:
    """Calculate whether a savings goal is feasible and what monthly amount is needed.

    Assumes end-of-month contributions compounding at annual_rate / 12 per month.
    If annual_rate == 0, uses simple accumulation (no compounding).

    Args:
        target_amount:    Dollar amount to reach (> 0).
        months_to_goal:   Number of months until the target date (> 0).
        current_saved:    Amount already saved toward this goal (>= 0).
        monthly_headroom: Free cash available each month to allocate (>= 0).
        annual_rate:      Expected annual growth rate as decimal (>= 0, default 0.0).

    Returns:
        Dict with keys:
            required_monthly (float):           Monthly saving needed to reach target.
            feasible (bool):                    True if monthly_headroom >= required_monthly.
            shortfall_per_month (float):        required_monthly − monthly_headroom (0 if feasible).
            months_needed_at_current_headroom (int | None):
                                                Months needed at current headroom; None if
                                                headroom is 0 and more saving is needed.
            projected_at_headroom (float):      Amount accumulated if saving at headroom rate.
            summary (str):                      Plain-language one-liner for the agent.

    Raises:
        ValueError: For clearly invalid inputs.
    """
    if target_amount <= 0:
        raise ValueError(f"target_amount must be > 0, got {target_amount}")
    if months_to_goal <= 0:
        raise ValueError(f"months_to_goal must be > 0, got {months_to_goal}")
    if current_saved < 0:
        raise ValueError(f"current_saved must be >= 0, got {current_saved}")
    if monthly_headroom < 0:
        raise ValueError(f"monthly_headroom must be >= 0, got {monthly_headroom}")
    if annual_rate < 0:
        raise ValueError(f"annual_rate must be >= 0, got {annual_rate}")

    remaining = max(0.0, target_amount - current_saved)
    monthly_rate = annual_rate / 12

    # ── Required monthly to hit target in exactly months_to_goal ──────────────
    if monthly_rate == 0:
        required_monthly = round(remaining / months_to_goal, 2)
    else:
        # Future value of annuity: FV = PMT * ((1+r)^n - 1) / r
        # Solve for PMT: PMT = FV * r / ((1+r)^n - 1)
        fv_factor = ((1 + monthly_rate) ** months_to_goal - 1) / monthly_rate
        required_monthly = round(remaining / fv_factor, 2)

    # ── Feasibility ────────────────────────────────────────────────────────────
    feasible = monthly_headroom >= required_monthly
    shortfall = round(max(0.0, required_monthly - monthly_headroom), 2)

    # ── How long at current headroom ──────────────────────────────────────────
    if monthly_headroom <= 0:
        months_at_headroom: int | None = None
        projected = round(current_saved, 2)
    elif monthly_rate == 0:
        months_at_headroom = (
            int(-(-remaining // monthly_headroom))  # ceiling division
            if remaining > 0 else 0
        )
        projected = round(current_saved + monthly_headroom * months_to_goal, 2)
    else:
        # Find n such that PMT * ((1+r)^n - 1)/r >= remaining
        # Solve numerically: n = log(1 + remaining*r/PMT) / log(1+r)
        import math
        if monthly_headroom * (1 / monthly_rate) > remaining:
            n_exact = math.log(1 + remaining * monthly_rate / monthly_headroom) / math.log(1 + monthly_rate)
            months_at_headroom = int(math.ceil(n_exact))
        else:
            months_at_headroom = None  # never reaches goal at this headroom
        projected = round(
            current_saved + monthly_headroom * ((1 + monthly_rate) ** months_to_goal - 1) / monthly_rate,
            2,
        )

    # ── Summary ────────────────────────────────────────────────────────────────
    if feasible:
        surplus = round(monthly_headroom - required_monthly, 2)
        summary = (
            f"Goal of ${target_amount:,.0f} in {months_to_goal} months is FEASIBLE. "
            f"Required: ${required_monthly:,.2f}/mo. "
            f"Your headroom: ${monthly_headroom:,.2f}/mo (${surplus:,.2f} to spare)."
        )
    else:
        summary = (
            f"Goal of ${target_amount:,.0f} in {months_to_goal} months needs ${required_monthly:,.2f}/mo "
            f"but you only have ${monthly_headroom:,.2f}/mo free — "
            f"shortfall of ${shortfall:,.2f}/mo. "
            + (
                f"At current headroom you'd reach it in {months_at_headroom} months."
                if months_at_headroom is not None
                else "At current headroom this goal may not be reachable."
            )
        )

    return {
        "required_monthly":                   required_monthly,
        "feasible":                            feasible,
        "shortfall_per_month":                 shortfall,
        "months_needed_at_current_headroom":   months_at_headroom,
        "projected_at_headroom":               projected,
        "summary":                             summary,
    }


# ── Debt and savings schedules ─────────────────────────────────────────────────


def debt_schedule(
    balance: float,
    monthly_payment: float,
    annual_rate: float,
    months: int = 60,
) -> list[float]:
    """Return a list of month-end debt balances over `months` months.

    Stops at 0.0 once the debt is paid off (remaining entries stay 0.0).
    If monthly_payment <= monthly interest the debt never pays off;
    balances will grow — include all `months` entries.

    Args:
        balance:         Starting debt balance (>= 0).
        monthly_payment: Fixed monthly payment amount (>= 0).
        annual_rate:     Annual interest rate as decimal (>= 0).
        months:          Number of months to project (> 0, default 60).

    Returns:
        List of `months` floats representing end-of-month balances.
    """
    if balance < 0:
        raise ValueError(f"balance must be >= 0, got {balance}")
    if monthly_payment < 0:
        raise ValueError(f"monthly_payment must be >= 0, got {monthly_payment}")
    if annual_rate < 0:
        raise ValueError(f"annual_rate must be >= 0, got {annual_rate}")
    if months <= 0:
        raise ValueError(f"months must be > 0, got {months}")

    monthly_rate = annual_rate / 12
    result: list[float] = []
    remaining = float(balance)

    for _ in range(months):
        if remaining <= 0:
            result.append(0.0)
            continue
        interest = remaining * monthly_rate
        remaining = remaining + interest - monthly_payment
        remaining = max(0.0, remaining)
        result.append(round(remaining, 2))

    return result


def savings_schedule(
    start: float,
    monthly_contribution: float,
    annual_rate: float,
    months: int = 60,
) -> list[float]:
    """Return a list of month-end savings balances over `months` months.

    Each month: balance = (balance + monthly_contribution) * (1 + monthly_rate).

    Args:
        start:                Starting savings balance (>= 0).
        monthly_contribution: Amount added each month (>= 0).
        annual_rate:          Annual growth rate as decimal (>= 0).
        months:               Number of months to project (> 0, default 60).

    Returns:
        List of `months` floats representing end-of-month balances.
    """
    if start < 0:
        raise ValueError(f"start must be >= 0, got {start}")
    if monthly_contribution < 0:
        raise ValueError(f"monthly_contribution must be >= 0, got {monthly_contribution}")
    if annual_rate < 0:
        raise ValueError(f"annual_rate must be >= 0, got {annual_rate}")
    if months <= 0:
        raise ValueError(f"months must be > 0, got {months}")

    monthly_rate = annual_rate / 12
    result: list[float] = []
    balance = float(start)

    for _ in range(months):
        balance = (balance + monthly_contribution) * (1 + monthly_rate)
        result.append(round(balance, 2))

    return result


# ── Multi-debt plan ────────────────────────────────────────────────────────────


def multi_debt_plan(
    debts: list[dict],
    extra_monthly: float = 0.0,
) -> dict:
    """Simulate avalanche and snowball debt payoff strategies.

    Both strategies use the same total monthly budget:
        sum of all min_payments + extra_monthly

    Avalanche: apply extra to highest-APR debt first.
    Snowball:  apply extra to smallest-balance debt first.

    Each debt dict must have:
        name (str):        Human-readable label.
        balance (float):   Current outstanding balance (>= 0).
        apr (float):       Annual interest rate as decimal (>= 0, e.g. 0.18).
        min_payment (float): Minimum monthly payment (> 0).

    Args:
        debts:         List of debt dicts (1–10 debts).
        extra_monthly: Extra monthly dollars applied on top of min payments (>= 0).

    Returns:
        Dict with keys:
            avalanche (dict):   payoff_order, months, total_interest, schedule.
            snowball (dict):    payoff_order, months, total_interest, schedule.
            better_strategy (str): "avalanche" or "snowball" or "tie".
            interest_saved (float): Interest saved by choosing the better strategy.
            summary (str):      Plain-language one-liner.

    Raises:
        ValueError: For invalid inputs.
    """
    if not debts:
        raise ValueError("debts must not be empty")
    if len(debts) > 10:
        raise ValueError(f"maximum 10 debts supported, got {len(debts)}")
    if extra_monthly < 0:
        raise ValueError(f"extra_monthly must be >= 0, got {extra_monthly}")

    for i, d in enumerate(debts):
        for key in ("name", "balance", "apr", "min_payment"):
            if key not in d:
                raise ValueError(f"debt[{i}] missing required key '{key}'")
        if d["balance"] < 0:
            raise ValueError(f"debt[{i}] balance must be >= 0")
        if d["apr"] < 0:
            raise ValueError(f"debt[{i}] apr must be >= 0")
        if d["min_payment"] <= 0:
            raise ValueError(f"debt[{i}] min_payment must be > 0")

    def _simulate(debts_in: list[dict], priority_key: str, reverse: bool) -> dict:
        """Run one payoff simulation with debts sorted by priority_key."""
        import copy
        state = copy.deepcopy(debts_in)
        for d in state:
            d["remaining"] = float(d["balance"])
            d["paid_interest"] = 0.0

        total_budget = sum(d["min_payment"] for d in state) + extra_monthly
        payoff_order: list[str] = []
        month = 0
        MAX_MONTHS = 600  # 50-year cap to prevent infinite loop

        while any(d["remaining"] > 0 for d in state) and month < MAX_MONTHS:
            month += 1
            # Accrue interest
            for d in state:
                if d["remaining"] > 0:
                    interest = d["remaining"] * (d["apr"] / 12)
                    d["remaining"] += interest
                    d["paid_interest"] += interest

            # Pay minimums first
            available = total_budget
            for d in state:
                if d["remaining"] > 0:
                    pay = min(d["min_payment"], d["remaining"])
                    d["remaining"] = max(0.0, d["remaining"] - pay)
                    available -= pay
                    if d["remaining"] == 0 and d["name"] not in payoff_order:
                        payoff_order.append(d["name"])

            # Apply extra to priority debt
            active = [d for d in state if d["remaining"] > 0]
            if active and available > 0:
                active_sorted = sorted(active, key=lambda x: x[priority_key], reverse=reverse)
                target = active_sorted[0]
                pay = min(available, target["remaining"])
                target["remaining"] = max(0.0, target["remaining"] - pay)
                if target["remaining"] == 0 and target["name"] not in payoff_order:
                    payoff_order.append(target["name"])

        return {
            "payoff_order":    payoff_order,
            "months":          month,
            "total_interest":  round(sum(d["paid_interest"] for d in state), 2),
        }

    avalanche = _simulate(debts, "apr", reverse=True)
    snowball   = _simulate(debts, "balance", reverse=False)

    av_int = avalanche["total_interest"]
    sn_int = snowball["total_interest"]

    if av_int < sn_int:
        better = "avalanche"
        saved  = round(sn_int - av_int, 2)
    elif sn_int < av_int:
        better = "snowball"
        saved  = round(av_int - sn_int, 2)
    else:
        better = "tie"
        saved  = 0.0

    mo_diff   = abs(avalanche["months"] - snowball["months"])
    int_saved_str = f"${saved:,.2f}" if saved > 0 else "the same amount"

    summary = (
        f"Avalanche: {avalanche['months']} months, ${av_int:,.2f} total interest. "
        f"Snowball: {snowball['months']} months, ${sn_int:,.2f} total interest. "
        + (
            f"Avalanche saves {int_saved_str} in interest"
            + (f" and is {mo_diff} month(s) faster." if avalanche["months"] < snowball["months"] else ".")
            if better == "avalanche"
            else (
                f"Snowball saves {int_saved_str} in interest"
                + (f" and is {mo_diff} month(s) faster." if snowball["months"] < avalanche["months"] else ".")
                if better == "snowball"
                else "Both strategies cost the same."
            )
        )
    )

    return {
        "avalanche":        avalanche,
        "snowball":         snowball,
        "better_strategy":  better,
        "interest_saved":   saved,
        "summary":          summary,
    }
