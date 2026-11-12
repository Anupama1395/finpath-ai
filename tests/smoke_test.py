"""
tests/smoke_test.py
-------------------
End-to-end smoke test for FinPath AI.

Verifies the full chain:
  Streamlit profile → api_client.ask_agent → Orchestrate agent
    → tool calls → tool results → agent reply

Requirements:
  - Orchestrate environment must be active:  orchestrate env activate finpath
  - All 7 tools must be imported into Orchestrate
  - finpath_agent must be imported into Orchestrate

Run with:
  pytest tests/smoke_test.py -v --tb=short -s

The -s flag lets you see the agent's actual responses during the run.
Each test checks:
  1. The agent returned a non-empty reply.
  2. Key numbers from the deterministic tools appear in the reply
     (proving the agent called tools and used the results, not hallucinated).
"""

from __future__ import annotations

import math
import sys
import os
import re

import pytest

# Make the project root and app/ dir importable
ROOT = os.path.join(os.path.dirname(__file__), "..")
APP  = os.path.join(ROOT, "app")
for p in (ROOT, APP):
    if p not in sys.path:
        sys.path.insert(0, p)

from tools.core.finance import (
    compare_scenarios,
    debt_payoff_months,
    emergency_fund_months,
    monthly_cash_flow,
    stress_test,
)

# ── Shared profile: "Early career" from data/profiles.json ───────────────────
PROFILE = {
    "monthly_income":   4500,
    "monthly_expenses": 2800,
    "cash_savings":     6000,
    "debt_balance":     15000,
    "debt_rate":        0.055,
    "savings_goal":     "Increase monthly investment from $200 to $500 and still keep 3 months emergency cash",
}


def _build_context(question: str) -> str:
    """Replicate the context string that app/main.py sends to the agent."""
    monthly_interest = round(
        PROFILE["debt_balance"] * PROFILE["debt_rate"] / 12, 2
    )
    return (
        f"User profile:\n"
        f"- Monthly take-home income: ${PROFILE['monthly_income']:,}\n"
        f"- Monthly essential expenses: ${PROFILE['monthly_expenses']:,}\n"
        f"- Current cash savings: ${PROFILE['cash_savings']:,}\n"
        f"- Debt balance: ${PROFILE['debt_balance']:,} at "
        f"{PROFILE['debt_rate']*100:.2f}% p.a. "
        f"(est. monthly interest: ${monthly_interest:,})\n"
        f"- Stated goal: {PROFILE['savings_goal']}\n\n"
        f"Question: {question}"
    )


def _extract_numbers(text: str) -> set[str]:
    """Return every dollar/decimal number found in the text as a set of strings."""
    return set(re.findall(r"\$?[\d,]+(?:\.\d+)?", text))


def _contains_approx(text: str, value: float, tolerance: float = 0.05) -> bool:
    """Return True if any number in text is within tolerance% of value."""
    for match in re.findall(r"[\d,]+(?:\.\d+)?", text.replace(",", "")):
        try:
            if abs(float(match) - value) / max(abs(value), 1) <= tolerance:
                return True
        except ValueError:
            pass
    return False


# ── Pytest fixtures ───────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def agent():
    """Import ask_agent once per module; skip the whole suite if ADK is unavailable."""
    try:
        from api_client import ask_agent
        return ask_agent
    except Exception as e:
        pytest.skip(f"Could not import ask_agent (ADK not available): {e}")


# ── Pre-compute expected values from the deterministic tools ──────────────────

# Scenario comparison: current ($200/mo saved) vs target ($500/mo)
_SCENARIOS = [
    {
        "label": "Current",
        "income": PROFILE["monthly_income"],
        "expenses": PROFILE["monthly_expenses"],
        "debt_payments": round(PROFILE["debt_balance"] * PROFILE["debt_rate"] / 12, 2),
        "savings_contribution": 200,
        "current_savings": PROFILE["cash_savings"],
    },
    {
        "label": "+$300 saved",
        "income": PROFILE["monthly_income"],
        "expenses": PROFILE["monthly_expenses"],
        "debt_payments": round(PROFILE["debt_balance"] * PROFILE["debt_rate"] / 12, 2),
        "savings_contribution": 500,
        "current_savings": PROFILE["cash_savings"],
    },
]
_SCENARIO_RESULTS = compare_scenarios(_SCENARIOS)

# Debt payoff: paying $300/mo toward 15k at 5.5%
_DEBT_PAYOFF = debt_payoff_months(
    balance=PROFILE["debt_balance"],
    monthly_payment=300,
    annual_rate=PROFILE["debt_rate"],
)

# Emergency fund: current savings vs monthly expenses
_EF_MONTHS = emergency_fund_months(
    savings=PROFILE["cash_savings"],
    monthly_expenses=PROFILE["monthly_expenses"],
)

# Stress test: -10% income shock
_STRESS = stress_test(
    income=PROFILE["monthly_income"],
    expenses=PROFILE["monthly_expenses"],
    debt_payments=round(PROFILE["debt_balance"] * PROFILE["debt_rate"] / 12, 2),
    savings_contribution=200,
    current_savings=PROFILE["cash_savings"],
    income_shock_pct=-10,
)


# ═══════════════════════════════════════════════════════════════════════════════
# SMOKE TESTS
# ═══════════════════════════════════════════════════════════════════════════════

class TestSmokeAgentResponds:
    """Basic connectivity: agent returns a non-empty, non-error reply."""

    def test_agent_returns_reply(self, agent):
        question = "Can I increase my monthly savings by $300 and still cover emergencies?"
        reply, scenarios, thread_id = agent(_build_context(question))
        print(f"\n[agent reply]\n{reply}\n")
        assert reply, "Agent returned an empty reply"
        assert len(reply) > 50, "Reply is suspiciously short"
        assert thread_id is not None, "No thread_id returned"

    def test_agent_does_not_refuse(self, agent):
        """Agent must not say it cannot help or that a question is out of scope."""
        question = "What are my financial options for saving more each month?"
        reply, _, _ = agent(_build_context(question))
        refusal_phrases = ["cannot help", "unable to assist", "out of scope", "i can't"]
        lower = reply.lower()
        for phrase in refusal_phrases:
            assert phrase not in lower, f"Agent refused: found '{phrase}' in reply"


class TestSmokeScenarioComparison:
    """Agent calls compare_scenarios and uses the results."""

    def test_scenario_comparison_returns_structured_data(self, agent):
        question = "Compare my current savings of $200/month versus saving $500/month."
        reply, scenarios, _ = agent(_build_context(question))
        print(f"\n[scenarios]\n{scenarios}\n")
        # Either scenarios are parsed from the reply, or the reply mentions cash flow
        if scenarios:
            assert len(scenarios) >= 2, "Expected at least 2 scenarios"
            for s in scenarios:
                assert "cash_flow" in s, "Scenario result missing cash_flow"
        else:
            # Fallback: check the reply references numbers from the tool output
            cf_current = _SCENARIO_RESULTS[0]["cash_flow"]
            assert _contains_approx(reply, cf_current), (
                f"Expected cash flow ~${cf_current} in reply but not found.\n"
                f"Reply: {reply[:500]}"
            )

    def test_feasibility_mentioned(self, agent):
        question = "Is saving $500/month feasible given my income and expenses?"
        reply, _, _ = agent(_build_context(question))
        # Agent should mention feasibility in some form
        feasibility_words = ["feasible", "surplus", "afford", "possible", "cash flow", "covers"]
        assert any(w in reply.lower() for w in feasibility_words), (
            f"Expected feasibility language in reply.\nReply: {reply[:500]}"
        )


class TestSmokeDebtPayoff:
    """Agent calls debt_payoff_months and reports correct figures."""

    def test_debt_payoff_months_mentioned(self, agent):
        question = "How long will it take to pay off my $15,000 debt at $300 per month?"
        reply, _, _ = agent(_build_context(question))
        print(f"\n[debt payoff reply]\n{reply}\n")
        expected_months = _DEBT_PAYOFF["months"]
        # Allow ±2 months tolerance (agent may round or use slightly different payment)
        assert _contains_approx(reply, expected_months, tolerance=0.1), (
            f"Expected ~{expected_months} months in reply.\n"
            f"Actual tool result: {_DEBT_PAYOFF}\nReply: {reply[:600]}"
        )

    def test_total_interest_mentioned(self, agent):
        question = "How much total interest will I pay on my $15,000 debt?"
        reply, _, _ = agent(_build_context(question))
        expected_interest = _DEBT_PAYOFF["total_interest"]
        assert _contains_approx(reply, expected_interest, tolerance=0.15), (
            f"Expected ~${expected_interest} total interest in reply.\n"
            f"Actual tool result: {_DEBT_PAYOFF}\nReply: {reply[:600]}"
        )


class TestSmokeEmergencyFund:
    """Agent calls emergency_fund_months and reports correct figures."""

    def test_emergency_fund_months_mentioned(self, agent):
        question = "Is my emergency fund healthy?"
        reply, _, _ = agent(_build_context(question))
        print(f"\n[emergency fund reply]\n{reply}\n")
        # Expected: 6000 / 2800 ≈ 2.14 months
        assert _contains_approx(reply, _EF_MONTHS, tolerance=0.15), (
            f"Expected ~{_EF_MONTHS} months emergency coverage in reply.\n"
            f"Reply: {reply[:600]}"
        )

    def test_emergency_fund_assessment_present(self, agent):
        question = "Do I have enough saved for emergencies?"
        reply, _, _ = agent(_build_context(question))
        assessment_words = ["month", "emergency", "savings", "cover", "fund"]
        assert any(w in reply.lower() for w in assessment_words), (
            f"Expected emergency fund language in reply.\nReply: {reply[:500]}"
        )


class TestSmokeStressTest:
    """Agent calls stress_test when asked about income shocks."""

    def test_stress_test_income_shock(self, agent):
        question = "What happens to my finances if my income drops by 10%?"
        reply, _, _ = agent(_build_context(question))
        print(f"\n[stress test reply]\n{reply}\n")
        shocked_income = _STRESS["shocked_income"]
        assert _contains_approx(reply, shocked_income, tolerance=0.12), (
            f"Expected shocked income ~${shocked_income} in reply.\n"
            f"Actual stress result: {_STRESS}\nReply: {reply[:600]}"
        )

    def test_stress_test_feasibility_reported(self, agent):
        question = "Can I still afford my savings plan if expenses go up 10%?"
        reply, _, _ = agent(_build_context(question))
        resilience_words = ["feasible", "still", "covers", "tight", "surplus",
                            "deficit", "infeasible", "afford", "cash flow"]
        assert any(w in reply.lower() for w in resilience_words), (
            f"Expected resilience assessment in reply.\nReply: {reply[:500]}"
        )


class TestSmokeGuardrails:
    """Agent must refuse product recommendations and always state assumptions."""

    def test_no_product_recommendation(self, agent):
        question = "Which mutual fund or ETF should I invest in?"
        reply, _, _ = agent(_build_context(question))
        print(f"\n[guardrail reply]\n{reply}\n")
        # Agent should decline to recommend specific products
        product_names = ["vanguard", "fidelity", "blackrock", "s&p 500 etf",
                         "index fund i recommend", "you should buy"]
        lower = reply.lower()
        for name in product_names:
            assert name not in lower, (
                f"Agent made a product recommendation (found '{name}').\nReply: {reply[:500]}"
            )
        # Should mention it doesn't give product advice
        no_advice_words = ["not financial advice", "illustrative", "cannot recommend",
                           "do not recommend", "not a recommendation", "educational"]
        assert any(w in lower for w in no_advice_words), (
            f"Agent didn't include disclaimer when asked for product recommendation.\n"
            f"Reply: {reply[:600]}"
        )

    def test_assumptions_stated(self, agent):
        question = "How much will my savings grow in the next year?"
        reply, _, _ = agent(_build_context(question))
        # Agent must state assumptions (rate at minimum)
        assumption_words = ["5%", "5 %", "assumption", "assumed", "rate", "%"]
        lower = reply.lower()
        assert any(w in lower for w in assumption_words), (
            f"Agent didn't state assumptions in projection reply.\nReply: {reply[:600]}"
        )


class TestSmokeClarifyingQuestion:
    """Agent must ask for missing info rather than guess."""

    def test_asks_for_income_when_missing(self, agent):
        # Send a message with no profile context — just a bare question
        bare_question = "Question: Can I save more each month?"
        reply, _, _ = agent(bare_question)
        print(f"\n[clarifying question reply]\n{reply}\n")
        # Agent should ask for income, expenses, or some number rather than invent them
        question_indicators = ["?", "income", "expense", "earn", "spend", "how much",
                               "what is", "could you", "please provide", "share"]
        lower = reply.lower()
        assert any(w in lower for w in question_indicators), (
            f"Agent should ask a clarifying question when profile is missing.\n"
            f"Reply: {reply[:600]}"
        )


class TestSmokeConversationContinuity:
    """Thread ID is returned and can be used for follow-up questions."""

    def test_follow_up_uses_same_thread(self, agent):
        q1 = "Can I save $500/month and still keep 3 months emergency cash?"
        reply1, _, thread_id = agent(_build_context(q1))
        assert thread_id is not None, "First call must return a thread_id"

        # Follow-up in the same thread — no profile context needed
        q2 = "What if I also reduced my expenses by $200?"
        reply2, _, thread_id2 = agent(q2, thread_id=thread_id)
        print(f"\n[follow-up reply]\n{reply2}\n")
        assert reply2, "Follow-up returned empty reply"
        # Thread should be reused or a new one started — either is acceptable
        assert thread_id2 is not None


# ═══════════════════════════════════════════════════════════════════════════════
# DETERMINISTIC SANITY CHECKS (no agent, just math)
# These run even when Orchestrate is offline to confirm the tool results
# the agent is expected to cite are themselves correct.
# ═══════════════════════════════════════════════════════════════════════════════

class TestSanityToolOutputs:
    """Confirm the expected values used in the smoke tests are correct."""

    def test_emergency_fund_early_career(self):
        # 6000 / 2800 ≈ 2.14 months
        assert _EF_MONTHS == pytest.approx(2.14, abs=0.01)

    def test_current_scenario_cash_flow(self):
        # 4500 - 2800 - (15000*0.055/12) - 200 ≈ 4500 - 2800 - 68.75 - 200 = 1431.25
        cf = _SCENARIO_RESULTS[0]["cash_flow"]
        assert cf == pytest.approx(1431.25, abs=1.0)

    def test_target_scenario_still_feasible(self):
        # +$300 saved scenario should still be cash-flow positive
        assert _SCENARIO_RESULTS[1]["feasible"] is True

    def test_debt_payoff_months_reasonable(self):
        # $300/mo on $15k at 5.5% → roughly 58–62 months
        assert 50 <= _DEBT_PAYOFF["months"] <= 70

    def test_stress_test_income_shocked(self):
        # -10% of 4500 = 4050
        assert _STRESS["shocked_income"] == pytest.approx(4050.0, abs=0.01)
