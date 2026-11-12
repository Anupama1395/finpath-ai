"""
tools/cash_flow_tool.py
-----------------------
Thin ADK @tool wrappers for cash-flow and emergency-fund calculations.
All math is delegated to tools/core/finance.py — no logic lives here.

Import into Orchestrate with:
  orchestrate tools import --kind python \
    --file tools/cash_flow_tool.py \
    --package-root tools/ \
    --requirements-file tools/requirements.txt
"""

from ibm_watsonx_orchestrate.agent_builder.tools import tool

from core.finance import emergency_fund_months as _efm
from core.finance import monthly_cash_flow as _mcf


@tool
def emergency_fund_months(savings: float, monthly_expenses: float) -> float:
    """Calculate how many months of essential expenses the current savings balance covers.

    Use this tool when the user asks whether their savings provide adequate
    emergency coverage, or before evaluating whether a scenario is financially safe.

    Args:
        savings: Current liquid savings balance in dollars (must be >= 0).
        monthly_expenses: Total monthly essential living expenses in dollars (must be > 0).

    Returns:
        Number of months covered, rounded to two decimal places.
        A value >= 3 is conventionally considered an adequate emergency fund.
    """
    return _efm(savings=savings, monthly_expenses=monthly_expenses)


@tool
def monthly_cash_flow(
    income: float,
    expenses: float,
    debt_payments: float,
    savings_contribution: float,
) -> float:
    """Calculate the net monthly surplus after all outflows.

    Use this tool to check whether a proposed savings contribution leaves the
    user with a non-negative cash flow. A negative result means the scenario
    is not feasible at the proposed contribution level.

    Args:
        income: Monthly take-home income in dollars (must be > 0).
        expenses: Total monthly essential living expenses in dollars (must be >= 0).
        debt_payments: Total monthly debt service payments in dollars (must be >= 0).
        savings_contribution: Proposed monthly savings or investment amount in dollars (must be >= 0).

    Returns:
        Net monthly surplus (income minus all outflows), rounded to two decimal places.
        Negative values indicate the scenario is cash-flow infeasible.
    """
    return _mcf(
        income=income,
        expenses=expenses,
        debt_payments=debt_payments,
        savings_contribution=savings_contribution,
    )
