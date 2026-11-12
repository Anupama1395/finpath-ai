"""
tools/debt_tool.py
------------------
Thin ADK @tool wrappers for debt payoff and debt-vs-invest calculations.
All math is delegated to tools/core/finance.py — no logic lives here.

Import into Orchestrate with:
  orchestrate tools import --kind python \
    --file tools/debt_tool.py \
    --package-root tools/ \
    --requirements-file tools/requirements.txt
"""

from ibm_watsonx_orchestrate.agent_builder.tools import tool

from core.finance import DEFAULT_ANNUAL_RATE
from core.finance import debt_payoff_months as _dpm
from core.finance import debt_vs_invest as _dvi


@tool
def debt_payoff_months(
    balance: float,
    monthly_payment: float,
    annual_rate: float,
) -> dict:
    """Calculate how many months it takes to pay off a debt and the total interest paid.

    Use this tool when the user asks how long it will take to pay off a loan,
    credit card, or any fixed-rate debt, or how much interest they will pay in total.

    Args:
        balance: Outstanding debt balance in dollars (must be > 0).
        monthly_payment: Fixed monthly payment in dollars (must be > 0 and must
                         exceed the monthly interest charge, otherwise the debt
                         can never be paid off).
        annual_rate: Annual interest rate on the debt as a decimal
                     (e.g. 0.055 for 5.5%). Must be >= 0.

    Returns:
        Dict containing:
            months (int):           Number of months to full payoff.
            total_interest (float): Total interest paid over the life of the debt.
            total_paid (float):     Total amount paid (principal + interest).

    Always state the annual_rate assumption in your response.
    """
    return _dpm(
        balance=balance,
        monthly_payment=monthly_payment,
        annual_rate=annual_rate,
    )


@tool
def debt_vs_invest(
    balance: float,
    annual_debt_rate: float,
    monthly_surplus: float,
    annual_invest_rate: float = DEFAULT_ANNUAL_RATE,
    months: int = 60,
) -> dict:
    """Compare the net-worth outcome of paying down debt first versus investing immediately.

    Use this tool when the user has available monthly cash and asks whether they
    should prioritise paying off debt or start investing. Call this proactively
    after compare_scenarios when annual_debt_rate exceeds the assumed investment rate.

    Strategy A (debt first): put the full monthly surplus toward the debt until paid off,
    then invest that amount for the remainder of the horizon. Net worth includes
    investment growth plus interest saved on the debt.

    Strategy B (invest first): invest the surplus immediately for the full horizon
    while carrying the debt balance unpaid.

    Args:
        balance: Outstanding debt balance in dollars (must be > 0).
        annual_debt_rate: Annual interest rate on the debt as a decimal (>= 0).
        monthly_surplus: Monthly cash available above living expenses in dollars (must be > 0).
        annual_invest_rate: Expected annual investment return as a decimal (>= 0).
                            Defaults to 0.05 (5% p.a.). Always state this assumption.
        months: Comparison horizon in months (must be > 0). Default 60 (5 years).

    Returns:
        Dict containing:
            strategy_a_net_worth (float): Net worth at horizon if debt is paid first.
            strategy_b_net_worth (float): Net worth at horizon if investing immediately.
            recommended (str):            "debt_first" | "invest_first" | "neutral"
            payoff_months (int | None):   Months to pay off debt under Strategy A,
                                          or None if the surplus cannot cover monthly interest.
            assumed_invest_rate (float):  Investment rate used (always state this).
            assumed_months (int):         Horizon used (always state this).

    Never recommend specific investment products. Present as an illustrative comparison only.
    """
    return _dvi(
        balance=balance,
        annual_debt_rate=annual_debt_rate,
        monthly_surplus=monthly_surplus,
        annual_invest_rate=annual_invest_rate,
        months=months,
    )
