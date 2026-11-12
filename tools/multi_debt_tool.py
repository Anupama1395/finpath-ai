"""tools/multi_debt_tool.py — Thin @tool wrapper for multi_debt_plan."""
from typing import Any
from ibm_watsonx_orchestrate.agent_builder.tools import tool
from core.finance import multi_debt_plan as _multi_debt_plan


@tool
def multi_debt_plan(
    debts: list[dict[str, Any]],
    extra_monthly: float = 0.0,
) -> dict:
    """Compare avalanche vs snowball debt payoff strategies for multiple debts.

    Use when the user has more than one debt. Both strategies use the same total
    monthly budget (sum of all minimum payments + extra_monthly).

    Avalanche: puts extra toward the highest-APR debt first (minimises interest).
    Snowball:  puts extra toward the smallest balance first (motivational wins).

    Args:
        debts: List of debt objects. Each must have:
            name (str):          Human-readable label (e.g. "Credit Card").
            balance (float):     Current outstanding balance in dollars (>= 0).
            apr (float):         Annual interest rate as decimal (e.g. 0.18 for 18%).
            min_payment (float): Minimum monthly payment in dollars (> 0).
        extra_monthly: Additional dollars per month applied on top of minimums (>= 0).

    Returns:
        Dict with:
            avalanche (dict): payoff_order, months, total_interest.
            snowball (dict):  payoff_order, months, total_interest.
            better_strategy (str): "avalanche", "snowball", or "tie".
            interest_saved (float): Interest saved by the better strategy.
            summary (str): Quote this field directly — do not paraphrase the numbers.

    Quote the summary verbatim. State all debt names, balances and APRs as assumptions.
    """
    return _multi_debt_plan(debts=debts, extra_monthly=extra_monthly)
