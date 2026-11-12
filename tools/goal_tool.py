"""tools/goal_tool.py — Thin @tool wrapper for goal_plan."""
from ibm_watsonx_orchestrate.agent_builder.tools import tool
from core.finance import goal_plan as _goal_plan


@tool
def goal_plan(
    target_amount: float,
    months_to_goal: int,
    current_saved: float,
    monthly_headroom: float,
    annual_rate: float = 0.0,
) -> dict:
    """Calculate whether a savings goal is feasible and the monthly amount required.

    Call savings_headroom first to determine monthly_headroom, then call this tool.
    Use for questions like "Can I save $X by [date]?" or "How much do I need to save
    each month to reach my goal?"

    Args:
        target_amount:    The dollar amount the user wants to reach (must be > 0).
        months_to_goal:   Number of months until the target date (must be > 0).
        current_saved:    Amount already saved toward this specific goal (>= 0).
        monthly_headroom: Free monthly cash available to allocate (>= 0).
                          Get this from savings_headroom tool.
        annual_rate:      Expected annual growth rate as decimal (default 0.0).

    Returns:
        Dict with:
            required_monthly (float): Monthly saving needed to hit the target.
            feasible (bool):          True if headroom >= required_monthly.
            shortfall_per_month (float): Gap to close if not feasible.
            months_needed_at_current_headroom (int | None): Months at current rate.
            projected_at_headroom (float): Projected amount at current headroom.
            summary (str): Quote this field directly in your response.

    Quote the summary verbatim. State all input values as assumptions.
    """
    return _goal_plan(
        target_amount=target_amount,
        months_to_goal=months_to_goal,
        current_saved=current_saved,
        monthly_headroom=monthly_headroom,
        annual_rate=annual_rate,
    )
