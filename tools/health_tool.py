"""
tools/health_tool.py
--------------------
Thin ADK @tool wrapper for financial_health_check.
All math is in tools/core/finance.py — no logic lives here.

Import into Orchestrate with:
  orchestrate tools import --kind python \\
    --file tools/health_tool.py \\
    --package-root tools/ \\
    --requirements-file tools/requirements.txt
"""

from ibm_watsonx_orchestrate.agent_builder.tools import tool

from core.finance import financial_health_check as _fhc


@tool
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

    Use this tool when the user asks "how am I doing financially?", "what is my
    financial health?", or any broad question about their overall situation.
    Chain this tool first to identify the top priority, then call the matching
    tool to explain it (e.g. debt_payoff_months if priority is debt-related).

    Args:
        income: Monthly take-home income in dollars (must be > 0).
        expenses: Monthly essential living expenses in dollars (>= 0).
        monthly_savings_contribution: Current monthly savings/investment amount (>= 0).
        current_savings: Current liquid savings balance in dollars (>= 0).
        debt_balance: Outstanding debt balance in dollars (>= 0).
        annual_debt_rate: Annual interest rate on debt as a decimal (>= 0, e.g. 0.07 for 7%).
        monthly_debt_payment: Current monthly debt payment in dollars (>= 0).
        assumed_invest_rate: Expected annual investment return as decimal (default 0.05).

    Returns:
        Dict with:
            score (int):                  Overall score 0–100.
            cash_flow_score (int):        Sub-score 0–25 for monthly cash flow.
            emergency_fund_score (int):   Sub-score 0–25 for emergency fund coverage.
            debt_burden_score (int):      Sub-score 0–25 for debt-to-income ratio.
            savings_rate_score (int):     Sub-score 0–25 for savings rate.
            cash_flow (float):            Monthly surplus/deficit in dollars.
            emergency_fund_months (float): Months of expenses covered by current savings.
            debt_to_income_ratio (float): Monthly debt payment divided by income.
            savings_rate (float):         Monthly savings contribution divided by income.
            priorities (list[str]):       Top 3 recommended priorities in order.
            summary (str):                Plain-language one-liner — quote this in your response.

    Quote the summary field directly. State all input values used as assumptions.
    After calling this tool, call the tool relevant to the top priority to give
    specific numbers (e.g. debt_payoff_months, emergency_fund_check, savings_headroom).
    """
    return _fhc(
        income=income,
        expenses=expenses,
        monthly_savings_contribution=monthly_savings_contribution,
        current_savings=current_savings,
        debt_balance=debt_balance,
        annual_debt_rate=annual_debt_rate,
        monthly_debt_payment=monthly_debt_payment,
        assumed_invest_rate=assumed_invest_rate,
    )
