"""
tools/emergency_tool.py
-----------------------
Thin ADK @tool wrapper for the emergency fund check.
All math is delegated to tools/core/finance.py — no logic lives here.

Import into Orchestrate with:
  orchestrate tools import --kind python \
    --file tools/emergency_tool.py \
    --package-root tools/ \
    --requirements-file tools/requirements.txt
"""

from ibm_watsonx_orchestrate.agent_builder.tools import tool

from core.finance import emergency_fund_check as _efc


@tool
def emergency_fund_check(
    current_savings: float,
    monthly_expenses: float,
) -> dict:
    """Check whether the user's savings provide an adequate emergency fund.

    Use this tool when the user asks if their emergency fund is healthy,
    how many months of expenses their savings cover, or how much more they
    need to save to reach the 3-month minimum.

    Standard guideline: 3–6 months of essential expenses is considered healthy.
    This is an educational guideline, not financial advice.

    Args:
        current_savings: Current liquid savings balance in dollars (must be >= 0).
        monthly_expenses: Monthly essential living expenses in dollars (must be > 0).

    Returns:
        Dict containing:
            months_covered (float):   Number of months of expenses currently covered.
            status (str):             "low" (< 3 months), "ok" (3–6 months), "strong" (> 6 months).
            gap_to_3_months (float):  Additional dollars needed to reach 3 months coverage (0 if already there).
            summary (str):            Plain-language sentence — quote this in your response.

    Quote the summary field directly. Always state that this is a conventional guideline,
    not a specific product recommendation or financial advice.
    """
    return _efc(
        current_savings=current_savings,
        monthly_expenses=monthly_expenses,
    )
