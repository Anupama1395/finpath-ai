"""
tools/savings_tool.py
---------------------
Thin ADK @tool wrapper for the savings headroom calculation.
All math is delegated to tools/core/finance.py — no logic lives here.

Import into Orchestrate with:
  orchestrate tools import --kind python \
    --file tools/savings_tool.py \
    --package-root tools/ \
    --requirements-file tools/requirements.txt
"""

from ibm_watsonx_orchestrate.agent_builder.tools import tool

from core.finance import savings_headroom as _sh


@tool
def savings_headroom(
    income: float,
    expenses: float,
    current_savings_contribution: float,
) -> dict:
    """Calculate how much additional monthly savings capacity the user has available.

    Use this tool when the user asks whether they can save more each month,
    how much extra they could put aside, or whether increasing their savings is feasible.

    Args:
        income: Monthly take-home income in dollars (must be > 0).
        expenses: Monthly essential living expenses in dollars (must be >= 0).
        current_savings_contribution: Current monthly savings or investment amount
                                      in dollars (must be >= 0).

    Returns:
        Dict containing:
            free_cash (float):               Monthly surplus after expenses and current savings.
                                             Negative means the user is already over-committed.
            can_save_more (bool):            True when free_cash > 0.
            max_additional_savings (float):  Maximum additional monthly savings possible (0 if none).
            summary (str):                   Plain-language sentence — quote this in your response.

    Quote the summary field directly. State all input values used as assumptions.
    """
    return _sh(
        income=income,
        expenses=expenses,
        current_savings_contribution=current_savings_contribution,
    )
