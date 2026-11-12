"""
tools/scenarios_tool.py
-----------------------
Thin ADK @tool wrapper for side-by-side scenario comparison.
All math is delegated to tools/core/finance.py — no logic lives here.

Import into Orchestrate with:
  orchestrate tools import --kind python \
    --file tools/scenarios_tool.py \
    --package-root tools/ \
    --requirements-file tools/requirements.txt
"""

from typing import Any

from ibm_watsonx_orchestrate.agent_builder.tools import tool

from core.finance import compare_scenarios as _cs


@tool
def compare_scenarios(scenarios: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Compare 1–3 financial scenarios side-by-side.

    You (the agent) are responsible for deciding which scenarios to compare and
    for constructing the scenario parameters based on the user's goal.
    Do NOT ask the user to supply pre-formed dicts.

    Each scenario dict MUST contain:
        label (str):                  Short human-readable name, e.g. "Current" or "+$200/mo"
        income (float):               Monthly take-home income in dollars
        expenses (float):             Monthly essential living expenses in dollars
        debt_payments (float):        Monthly debt service payments in dollars
        savings_contribution (float): Proposed monthly savings or investment amount in dollars

    Each scenario dict MAY also contain (defaults applied when absent):
        current_savings (float):  Starting liquid savings balance; default 0.0
        annual_rate (float):      Annual growth rate as a decimal; default 0.05 (5% p.a.)
        months (int):             Projection horizon in months; default 12

    Args:
        scenarios: List of 1–3 scenario dicts as described above.

    Returns:
        List of result dicts, one per scenario, each containing:
            label (str):                    The scenario label
            income / expenses / debt_payments / savings_contribution / current_savings (float): echoed inputs
            cash_flow (float):              Monthly surplus (negative = infeasible)
            emergency_fund_months (float):  Months of expenses covered by current_savings
            projected_savings (float):      Future value of savings after `months`
            feasible (bool):                True when cash_flow >= 0
            assumed_annual_rate (float):    Rate used (always state this in your response)
            assumed_months (int):           Horizon used (always state this in your response)

    Always present results as a comparison table and state all assumed values explicitly.
    Never recommend specific financial products, securities, or buy/sell actions.
    """
    return _cs(scenarios=scenarios)
