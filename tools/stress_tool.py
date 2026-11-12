"""
tools/stress_tool.py
--------------------
Thin ADK @tool wrapper for the financial stress test.
All math is delegated to tools/core/finance.py — no logic lives here.

Import into Orchestrate with:
  orchestrate tools import --kind python \
    --file tools/stress_tool.py \
    --package-root tools/ \
    --requirements-file tools/requirements.txt
"""

from ibm_watsonx_orchestrate.agent_builder.tools import tool

from core.finance import DEFAULT_EMERGENCY_TARGET
from core.finance import stress_test as _st


@tool
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
    """Re-run a financial scenario under an income or expense shock to test resilience.

    Use this tool when the user asks "what if I lost 10% of my income?" or
    "what if my expenses increased by 10%?" after a scenario comparison.
    Apply a shock to income and/or expenses, then report whether the scenario
    still produces a positive cash flow and still meets the emergency fund target.

    Args:
        income: Monthly take-home income in dollars (must be > 0).
        expenses: Monthly essential living expenses in dollars (must be >= 0).
        debt_payments: Monthly debt service payments in dollars (must be >= 0).
        savings_contribution: Monthly savings contribution in dollars (must be >= 0).
        current_savings: Current liquid savings balance in dollars (must be >= 0).
        income_shock_pct: Percentage change applied to income.
                          Use -10 for a 10% income drop, +10 for a 10% raise.
                          Default 0 (no income shock).
        expenses_shock_pct: Percentage change applied to expenses.
                            Use +10 for 10% higher costs, -10 for 10% lower.
                            Default 0 (no expense shock).
        emergency_target_months: Minimum months of expenses that must be covered
                                 by current_savings to be considered adequate.
                                 Default 3 months.

    Returns:
        Dict containing:
            shocked_income (float):            Income after applying the shock.
            shocked_expenses (float):          Expenses after applying the shock.
            shocked_cash_flow (float):         Monthly surplus/deficit after shock.
            shocked_emergency_months (float):  Emergency fund coverage after shock.
            still_feasible (bool):             True if shocked_cash_flow >= 0.
            still_meets_target (bool):         True if shocked_emergency_months
                                               >= emergency_target_months.
            income_shock_pct (float):          Echoed for transparency.
            expenses_shock_pct (float):        Echoed for transparency.
            emergency_target_months (float):   Echoed for transparency.

    Always state all shock percentages and the emergency target in your response.
    """
    return _st(
        income=income,
        expenses=expenses,
        debt_payments=debt_payments,
        savings_contribution=savings_contribution,
        current_savings=current_savings,
        income_shock_pct=income_shock_pct,
        expenses_shock_pct=expenses_shock_pct,
        emergency_target_months=emergency_target_months,
    )
