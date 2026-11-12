"""
tools/projections_tool.py
-------------------------
Thin ADK @tool wrapper for savings growth projection.
All math is delegated to tools/core/finance.py — no logic lives here.

Import into Orchestrate with:
  orchestrate tools import --kind python \
    --file tools/projections_tool.py \
    --package-root tools/ \
    --requirements-file tools/requirements.txt
"""

from ibm_watsonx_orchestrate.agent_builder.tools import tool

from core.finance import DEFAULT_ANNUAL_RATE
from core.finance import project_savings_growth as _psg


@tool
def project_savings_growth(
    principal: float,
    monthly_contribution: float,
    months: int,
    annual_rate: float = DEFAULT_ANNUAL_RATE,
) -> float:
    """Project the future value of savings using monthly compound interest.

    Use this tool to show a user how their savings balance will grow over a
    chosen time horizon under a given monthly contribution and interest rate.
    Always state the assumed annual_rate in your response.

    Args:
        principal: Current savings balance in dollars (must be >= 0).
        monthly_contribution: Amount added to savings each month in dollars (must be >= 0).
        months: Number of months to project forward (must be > 0).
        annual_rate: Annual interest or growth rate as a decimal (e.g. 0.05 for 5%).
                     Defaults to 0.05 (5% p.a.) when not supplied by the user.
                     Always state this assumption explicitly in your response.

    Returns:
        Projected future value in dollars, rounded to two decimal places.
    """
    return _psg(
        principal=principal,
        monthly_contribution=monthly_contribution,
        annual_rate=annual_rate,
        months=months,
    )
