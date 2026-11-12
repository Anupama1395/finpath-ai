"""
app/app.py
----------
FinPath AI — Streamlit frontend.

Start with:
    streamlit run app/app.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import streamlit as st

# ── Make project root importable so app/api_client can find the ADK ──────────
ROOT = Path(__file__).parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.api_client import ask_agent  # noqa: E402  (after sys.path fixup)

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="FinPath AI",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded",
)

DISCLAIMER = (
    "**Educational tool. Not financial advice.** "
    "All projections are illustrative and based on the figures you supply."
)

# ── Load synthetic profiles ───────────────────────────────────────────────────
@st.cache_data
def load_profiles() -> list[dict]:
    profiles_path = ROOT / "data" / "profiles.json"
    with open(profiles_path) as f:
        return json.load(f)


PROFILES = load_profiles()
PROFILE_MAP = {p["label"]: p for p in PROFILES}

# ── Session state defaults ────────────────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []          # list of {"role", "content", "scenarios"}
if "thread_id" not in st.session_state:
    st.session_state.thread_id = None


# ═══════════════════════════════════════════════════════════════════════════════
# SIDEBAR — profile selector + manual field editor
# ═══════════════════════════════════════════════════════════════════════════════

with st.sidebar:
    st.title("👤 Your Profile")

    profile_labels = ["(enter manually)"] + [p["label"] for p in PROFILES]
    selected_label = st.selectbox("Load a sample profile", profile_labels)

    if selected_label != "(enter manually)":
        p = PROFILE_MAP[selected_label]
        defaults = {
            "income":    p["monthly_income"],
            "expenses":  p["monthly_expenses"],
            "savings":   p["cash_savings"],
            "debt_bal":  p["debt_balance"],
            "debt_rate": p["debt_rate"] * 100,
            "goal":      p["savings_goal"],
        }
    else:
        defaults = {
            "income":    5000,
            "expenses":  3000,
            "savings":   6000,
            "debt_bal":  10000,
            "debt_rate": 6.0,
            "goal":      "Increase my monthly savings",
        }

    st.markdown("---")

    monthly_income = st.number_input(
        "Monthly take-home income ($)",
        min_value=0, step=100,
        value=int(defaults["income"]),
    )
    monthly_expenses = st.number_input(
        "Monthly essential expenses ($)",
        min_value=0, step=100,
        value=int(defaults["expenses"]),
    )
    cash_savings = st.number_input(
        "Current cash savings ($)",
        min_value=0, step=500,
        value=int(defaults["savings"]),
    )
    debt_balance = st.number_input(
        "Total debt balance ($)",
        min_value=0, step=1000,
        value=int(defaults["debt_bal"]),
    )
    debt_rate_pct = st.slider(
        "Debt interest rate (%)",
        min_value=0.0, max_value=30.0, step=0.25,
        value=float(defaults["debt_rate"]),
    )
    savings_goal = st.text_area(
        "Your savings / investment goal",
        value=defaults["goal"],
        height=100,
    )

    st.markdown("---")

    if st.button("🔄 Clear conversation", use_container_width=True):
        st.session_state.messages = []
        st.session_state.thread_id = None
        st.rerun()

    st.caption(DISCLAIMER)


# ═══════════════════════════════════════════════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════════════════════════════════════════════

def _build_context_message(user_question: str) -> str:
    """Prepend profile snapshot to the user's question."""
    monthly_debt_payment = round(debt_balance * (debt_rate_pct / 100) / 12, 2)
    profile_block = (
        f"**User profile:**\n"
        f"- Monthly take-home income: ${monthly_income:,}\n"
        f"- Monthly essential expenses: ${monthly_expenses:,}\n"
        f"- Current cash savings: ${cash_savings:,}\n"
        f"- Debt balance: ${debt_balance:,} at {debt_rate_pct:.2f}% p.a. "
        f"(est. monthly interest: ${monthly_debt_payment:,})\n"
        f"- Stated goal: {savings_goal}\n\n"
        f"**Question:** {user_question}"
    )
    return profile_block


def _render_scenario_table(scenarios: list[dict]) -> None:
    """Render a markdown comparison table from compare_scenarios output."""
    st.markdown("#### 📊 Scenario Comparison")

    headers = ["", "Monthly Surplus", "Emergency Fund (months)", "Projected Savings (12 mo)", "Feasible?"]
    rows = []
    for s in scenarios:
        feasible = "✅ Yes" if s.get("feasible") else "❌ No"
        rows.append([
            s.get("label", "—"),
            f"${s.get('cash_flow', 0):,.2f}",
            f"{s.get('emergency_fund_months', 0):.1f}",
            f"${s.get('projected_savings', 0):,.2f}",
            feasible,
        ])

    # Build markdown table
    header_row = "| " + " | ".join(headers) + " |"
    sep_row    = "| " + " | ".join(["---"] * len(headers)) + " |"
    data_rows  = "\n".join("| " + " | ".join(r) + " |" for r in rows)
    st.markdown(f"{header_row}\n{sep_row}\n{data_rows}")


def _render_scenario_chart(scenarios: list[dict]) -> None:
    """Render a grouped bar chart for the three key metrics."""
    import pandas as pd
    import altair as alt

    labels = [s.get("label", f"S{i}") for i, s in enumerate(scenarios)]

    records = []
    for s in scenarios:
        lbl = s.get("label", "—")
        records += [
            {"Scenario": lbl, "Metric": "Monthly Surplus ($)", "Value": s.get("cash_flow", 0)},
            {"Scenario": lbl, "Metric": "Emergency Fund (months)", "Value": s.get("emergency_fund_months", 0)},
            {"Scenario": lbl, "Metric": "Projected Savings ($, 12 mo)", "Value": s.get("projected_savings", 0)},
        ]

    df = pd.DataFrame(records)

    chart = (
        alt.Chart(df)
        .mark_bar()
        .encode(
            x=alt.X("Scenario:N", axis=alt.Axis(labelAngle=0)),
            y=alt.Y("Value:Q"),
            color="Scenario:N",
            facet=alt.Facet("Metric:N", columns=3),
            tooltip=["Scenario", "Metric", "Value"],
        )
        .properties(width=200, height=200)
        .resolve_scale(y="independent")
    )
    st.altair_chart(chart, use_container_width=True)


def _render_assumptions(scenarios: list[dict]) -> None:
    """Show the Assumptions section that the agent / compare_scenarios echoes."""
    if not scenarios:
        return
    s = scenarios[0]  # assumptions are shared across the run
    rate_pct = s.get("assumed_annual_rate", 0.05) * 100
    months   = s.get("assumed_months", 12)

    with st.expander("📋 Assumptions"):
        st.markdown(
            f"- **Annual growth rate:** {rate_pct:.1f}% p.a.  \n"
            f"- **Projection horizon:** {months} months  \n"
            f"- **Income / expenses / debt payments:** as entered in the sidebar  \n"
            f"- Projections use monthly compound interest.  \n"
            f"- Emergency fund target of 3–6 months is a conventional guideline, "
            f"not a product recommendation."
        )


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN AREA — chat
# ═══════════════════════════════════════════════════════════════════════════════

st.title("💰 FinPath AI")
st.caption(DISCLAIMER)
st.markdown("---")

# Replay conversation history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg.get("scenarios"):
            _render_scenario_table(msg["scenarios"])
            _render_scenario_chart(msg["scenarios"])
            _render_assumptions(msg["scenarios"])

# Chat input
user_input = st.chat_input("Ask FinPath AI about your financial scenarios…")

if user_input:
    # Show user bubble immediately
    with st.chat_message("user"):
        st.markdown(user_input)
    st.session_state.messages.append({"role": "user", "content": user_input, "scenarios": None})

    # Build context-enriched message (profile + question)
    enriched = _build_context_message(user_input)

    # Call agent
    with st.chat_message("assistant"):
        with st.spinner("FinPath AI is thinking…"):
            try:
                reply, scenarios, new_thread_id = ask_agent(
                    enriched,
                    thread_id=st.session_state.thread_id,
                )
                st.session_state.thread_id = new_thread_id
            except (RuntimeError, TimeoutError) as exc:
                reply = f"⚠️ **Could not reach the agent.** {exc}"
                scenarios = None
            except Exception as exc:
                reply = (
                    "⚠️ **An unexpected error occurred.** "
                    "Please check that your Orchestrate environment is active and try again."
                )
                scenarios = None
                logger_msg = f"Unexpected error in Streamlit: {exc}"
                # Use st.exception only in debug; avoid stack trace in prod UI
                import logging as _logging
                _logging.getLogger(__name__).debug(logger_msg, exc_info=True)

        st.markdown(reply)
        if scenarios:
            _render_scenario_table(scenarios)
            _render_scenario_chart(scenarios)
            _render_assumptions(scenarios)

    st.session_state.messages.append({
        "role": "assistant",
        "content": reply,
        "scenarios": scenarios,
    })
