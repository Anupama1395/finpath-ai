"""
app/main.py — FinPath AI Streamlit UI (all features)

Steps:
  1  Profile   — sample profiles, 2-col form, goal inputs, multi-debt table,
                 live health card, goal feasibility card
  2  Question  — suggestion chips + free-form textarea
  3  Results   — multi-turn chat, tool chips, what-if sliders + charts,
                 verified badge, download summary, assumptions expander
"""

from __future__ import annotations

import io
import json
import logging
import re
import sys
from datetime import date, timedelta
from pathlib import Path

import streamlit as st

# ── Local imports (no agent call needed for health card / schedules) ──────────
try:
    _tools_path = str(Path(__file__).parent.parent)
    if _tools_path not in sys.path:
        sys.path.insert(0, _tools_path)
    from tools.core.finance import (
        financial_health_check as _fhc,
        goal_plan             as _goal_plan,
        savings_headroom      as _savings_headroom,
        debt_schedule         as _debt_schedule,
        savings_schedule      as _savings_schedule,
    )
    _LOCAL_MATH = True
except Exception:
    _LOCAL_MATH = False

ROOT    = Path(__file__).parent.parent
APP_DIR = Path(__file__).parent
for _p in (str(ROOT), str(APP_DIR)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from api_client import ask_agent  # noqa: E402

_log = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="FinPath AI",
    page_icon="💰",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# ─────────────────────────────────────────────────────────────────────────────
# GLOBAL CSS
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Fraunces:ital,opsz,wght@0,9..144,400;1,9..144,400&family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@400;500&display=swap');

:root{
  --bg:#0B0D10; --surface:#131720; --surface2:#1A1F28; --surface3:#1E2430;
  --border:rgba(255,255,255,.07); --border2:rgba(255,255,255,.12);
  --text:#ECE8E1; --muted:#A6ACB4; --dim:#6B737D;
  --orange:#E8603C; --orange2:#C94E2C;
  --orangeA:rgba(232,96,60,.12); --orangeB:rgba(232,96,60,.24);
  --gold:#D4A84B; --green:#4EA86B; --greenA:rgba(78,168,107,.12);
  --red:#D95F5F; --blue:#5B9BD5;
  --serif:'Fraunces',Georgia,serif;
  --sans:'Inter',-apple-system,system-ui,sans-serif;
  --mono:'JetBrains Mono','Courier New',monospace;
  --radius:8px; --radius-sm:4px;
}
html,body,[class*="css"]{font-family:var(--sans)!important;-webkit-font-smoothing:antialiased}
.stApp{background:var(--bg)!important;color:var(--text)!important}
header[data-testid="stHeader"],footer,#MainMenu{display:none!important}
.block-container{max-width:860px!important;padding:2.2rem 1.4rem 4rem!important}
::-webkit-scrollbar{width:5px;height:5px}
::-webkit-scrollbar-thumb{background:rgba(255,255,255,.12);border-radius:3px}

[data-baseweb="base-input"],[data-baseweb="input"],[data-baseweb="textarea"]{
  background:var(--surface2)!important;border-color:var(--border)!important;
  border-radius:var(--radius-sm)!important}
[data-baseweb="base-input"] input,[data-baseweb="input"] input,
[data-baseweb="textarea"] textarea,textarea{
  background:var(--surface2)!important;color:var(--text)!important;
  font-family:var(--mono)!important;font-size:.82rem!important;caret-color:var(--orange)!important}
[data-baseweb="base-input"]:focus-within,[data-baseweb="input"]:focus-within,
[data-baseweb="textarea"]:focus-within{
  border-color:rgba(232,96,60,.45)!important;box-shadow:0 0 0 2px rgba(232,96,60,.12)!important}
input::placeholder,textarea::placeholder{color:var(--dim)!important;opacity:1!important}
[data-baseweb="base-input"] button{background:var(--surface2)!important;color:var(--muted)!important;border-color:var(--border)!important}

label,.stNumberInput label,.stTextInput label,.stTextArea label,.stSelectbox label,.stSlider label{
  font-family:var(--mono)!important;font-size:.62rem!important;letter-spacing:.07em!important;
  text-transform:uppercase!important;color:var(--muted)!important;margin-bottom:.2rem!important}

.stButton button{
  background:var(--surface2)!important;border:1px solid var(--border2)!important;
  color:var(--text)!important;font-family:var(--mono)!important;font-size:.66rem!important;
  letter-spacing:.07em!important;text-transform:uppercase!important;
  border-radius:var(--radius-sm)!important;padding:.5rem 1.1rem!important;transition:all .15s!important}
.stButton button:hover{background:var(--surface3)!important;border-color:rgba(255,255,255,.22)!important}
.stButton button[kind="primary"]{background:var(--orange)!important;border-color:var(--orange)!important;color:#fff!important;font-weight:600!important}
.stButton button[kind="primary"]:hover{background:var(--orange2)!important;border-color:var(--orange2)!important}
.stButton button[kind="primary"]:disabled{background:rgba(232,96,60,.28)!important;border-color:transparent!important;color:rgba(255,255,255,.35)!important}
.stButton button[kind="tertiary"]{background:transparent!important;border-color:transparent!important;color:var(--dim)!important;font-size:.62rem!important;padding:.2rem .5rem!important}
.stButton button[kind="tertiary"]:hover{color:var(--muted)!important}

.profile-selected .stButton button{border-color:var(--orange)!important;background:var(--orangeA)!important;color:var(--orange)!important}
.sug-btn .stButton button{
  background:var(--surface2)!important;border:1px solid var(--border)!important;color:var(--muted)!important;
  font-size:.65rem!important;padding:.55rem .9rem!important;text-align:left!important;
  white-space:normal!important;height:auto!important;line-height:1.45!important;border-radius:var(--radius-sm)!important}
.sug-btn .stButton button:hover{border-color:var(--orangeB)!important;color:var(--text)!important;background:rgba(232,96,60,.05)!important}

.streamlit-expanderHeader{font-family:var(--mono)!important;font-size:.62rem!important;letter-spacing:.07em!important;text-transform:uppercase!important;color:var(--muted)!important;background:var(--surface)!important;border-radius:var(--radius-sm)!important}
[data-testid="stExpanderDetails"]{background:var(--surface)!important;border:1px solid var(--border)!important;border-top:none!important;border-radius:0 0 var(--radius-sm) var(--radius-sm)!important}

[data-testid="stChatMessage"]{background:var(--surface)!important;border:1px solid var(--border)!important;border-radius:var(--radius)!important;padding:1rem 1.1rem!important;margin-bottom:.7rem!important}
[data-testid="stChatMessage"] p{font-size:.92rem!important;line-height:1.7!important}
[data-testid="stChatInput"] textarea{background:var(--surface2)!important;border-color:var(--border2)!important;color:var(--text)!important;font-size:.88rem!important}

hr{border-color:var(--border)!important;margin:1.5rem 0!important}
.vega-embed{background:transparent!important}
.stCaption{font-family:var(--mono)!important;font-size:.62rem!important;color:var(--dim)!important;margin-top:-.15rem!important}

/* data editor */
[data-testid="stDataFrame"],[data-testid="stDataEditor"]{background:var(--surface)!important;border:1px solid var(--border)!important;border-radius:var(--radius-sm)!important}
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# DATA
# ─────────────────────────────────────────────────────────────────────────────
@st.cache_data
def load_profiles() -> list[dict]:
    with open(ROOT / "data" / "profiles.json") as f:
        return json.load(f)

PROFILES = load_profiles()

SUGGESTIONS = [
    "Can I save $200 more each month?",
    "How long to pay off my debt?",
    "Is my emergency fund healthy?",
    "Pay off debt first or start investing?",
    "What if my income dropped by 10%?",
    "What if expenses rose by 15%?",
]
FOLLOWUP_SUGGESTIONS = [
    "What if I paid $100 more a month?",
    "What if my income dropped 10%?",
    "Should I invest instead of paying debt?",
]

DEFAULT_DEBTS = [
    {"Name": "Primary Debt", "Balance ($)": 10000, "APR (%)": 6.0, "Min Payment ($)": 300},
]

# ─────────────────────────────────────────────────────────────────────────────
# SESSION STATE
# ─────────────────────────────────────────────────────────────────────────────
def _default_goals() -> list[dict]:
    return [{"name": "", "target": 0, "current_saved": 0, "months": 12}]

def _init_state() -> None:
    defaults: dict = {
        "step":            1,
        "profile":         None,
        # totals (derived from breakdown on save, or entered directly)
        "income":          5000,
        "expenses":        3000,
        "savings":         6000,
        "savings_contrib": 200,
        "debt_bal":        10000,
        "debt_payment":    300,
        "debt_rate":       6.0,
        "goal":            "",
        # income breakdown
        "inc_salary":      5000,
        "inc_side":        0,
        "inc_other":       0,
        # expense breakdown
        "exp_housing":     1200,
        "exp_food":        600,
        "exp_transport":   400,
        "exp_subs":        200,
        "exp_other":       600,
        # savings breakdown
        "sav_emergency":   3000,
        "sav_invest":      2000,
        "sav_other":       1000,
        # multiple goals (list of dicts)
        "goals":           _default_goals(),
        # multi-debt
        "use_multi_debt":  False,
        "multi_debts":     DEFAULT_DEBTS.copy(),
        # question / chat
        "question":        "",
        "messages":        [],
        "thread_id":       None,
        "pending_send":    None,
        "error":           None,
        # what-if slider state
        "wi_extra_pmt":    0,
        "wi_income_chg":   0,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

_init_state()
S = st.session_state

# ─────────────────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────────────────
def _go(step: int) -> None:
    S.step = step
    st.rerun()

_INPUT_KEYS = [
    "in_income","in_expenses","in_savings","in_savings_contrib",
    "in_debt_bal","in_debt_payment","in_debt_rate","in_goal",
    # breakdown keys
    "in_inc_salary","in_inc_side","in_inc_other",
    "in_exp_housing","in_exp_food","in_exp_transport","in_exp_subs","in_exp_other",
    "in_sav_emergency","in_sav_invest","in_sav_other",
]

def _sync_totals_from_breakdown() -> None:
    """Recompute S.income, S.expenses, S.savings from their breakdown sub-fields."""
    S.income   = int(S.inc_salary + S.inc_side + S.inc_other)
    S.expenses = int(S.exp_housing + S.exp_food + S.exp_transport + S.exp_subs + S.exp_other)
    S.savings  = int(S.sav_emergency + S.sav_invest + S.sav_other)

def _load_profile(p: dict) -> None:
    income   = int(p["monthly_income"])
    expenses = int(p["monthly_expenses"])
    savings  = int(p["cash_savings"])
    contrib  = int(p.get("monthly_savings_contribution", 0))
    debt_bal = int(p["debt_balance"])
    debt_pmt = int(p.get("monthly_debt_payment", 0))
    rate     = float(p["debt_rate"] * 100)
    goal     = p["savings_goal"]

    S.profile=p; S.income=income; S.expenses=expenses; S.savings=savings
    S.savings_contrib=contrib; S.debt_bal=debt_bal; S.debt_payment=debt_pmt
    S.debt_rate=rate; S.goal=goal

    # Put totals into the primary breakdown field, zero the rest
    S.inc_salary=income; S.inc_side=0; S.inc_other=0
    S.exp_housing=expenses; S.exp_food=0; S.exp_transport=0; S.exp_subs=0; S.exp_other=0
    S.sav_emergency=savings; S.sav_invest=0; S.sav_other=0

    # Seed one goal from the profile goal text
    S.goals = [{"name": goal[:40] if goal else "My goal", "target": 0, "current_saved": 0, "months": 12}]

    # Write widget keys directly
    st.session_state["in_income"]=income; st.session_state["in_expenses"]=expenses
    st.session_state["in_savings"]=savings; st.session_state["in_savings_contrib"]=contrib
    st.session_state["in_debt_bal"]=debt_bal; st.session_state["in_debt_payment"]=debt_pmt
    st.session_state["in_debt_rate"]=rate; st.session_state["in_goal"]=goal
    st.session_state["in_inc_salary"]=income; st.session_state["in_inc_side"]=0; st.session_state["in_inc_other"]=0
    st.session_state["in_exp_housing"]=expenses; st.session_state["in_exp_food"]=0
    st.session_state["in_exp_transport"]=0; st.session_state["in_exp_subs"]=0; st.session_state["in_exp_other"]=0
    st.session_state["in_sav_emergency"]=savings; st.session_state["in_sav_invest"]=0; st.session_state["in_sav_other"]=0

    # Reset multi-debt
    S.multi_debts = [{"Name":"Primary Debt","Balance ($)":debt_bal,"APR (%)":rate,"Min Payment ($)":debt_pmt}]

def _clear_profile() -> None:
    S.profile=None; S.income=5000; S.expenses=3000; S.savings=6000
    S.savings_contrib=200; S.debt_bal=10000; S.debt_payment=300; S.debt_rate=6.0; S.goal=""
    S.inc_salary=5000; S.inc_side=0; S.inc_other=0
    S.exp_housing=1200; S.exp_food=600; S.exp_transport=400; S.exp_subs=200; S.exp_other=600
    S.sav_emergency=3000; S.sav_invest=2000; S.sav_other=1000
    S.goals = _default_goals()
    for k,v in [
        ("in_income",5000),("in_expenses",3000),("in_savings",6000),
        ("in_savings_contrib",200),("in_debt_bal",10000),("in_debt_payment",300),
        ("in_debt_rate",6.0),("in_goal",""),
        ("in_inc_salary",5000),("in_inc_side",0),("in_inc_other",0),
        ("in_exp_housing",1200),("in_exp_food",600),("in_exp_transport",400),
        ("in_exp_subs",200),("in_exp_other",600),
        ("in_sav_emergency",3000),("in_sav_invest",2000),("in_sav_other",1000),
    ]:
        st.session_state[k]=v
    S.multi_debts = DEFAULT_DEBTS.copy()

def _build_profile_dict() -> dict:
    goals_summary = "; ".join(
        f'{g["name"]} (${g["target"]:,} in {g["months"]} mo, saved ${g["current_saved"]:,})'
        for g in S.goals if g.get("target", 0) > 0
    ) or S.goal or "not specified"

    return {
        "monthly_income":               S.income,
        "monthly_expenses":             S.expenses,
        "monthly_savings_contribution": S.savings_contrib,
        "monthly_debt_payment":         S.debt_payment,
        "current_savings":              S.savings,
        "debt_balance":                 S.debt_bal,
        "annual_debt_rate_pct":         S.debt_rate,
        "goal":                         goals_summary,
        # breakdown detail for richer agent context
        "income_breakdown":  {"salary": S.inc_salary, "side_income": S.inc_side, "other": S.inc_other},
        "expense_breakdown": {"housing": S.exp_housing, "food": S.exp_food, "transport": S.exp_transport,
                              "subscriptions": S.exp_subs, "other": S.exp_other},
        "savings_breakdown": {"emergency_fund": S.sav_emergency, "investments": S.sav_invest, "other": S.sav_other},
        "goals":             S.goals,
    }

def _headroom() -> float:
    try:
        r = _savings_headroom(
            monthly_income=S.income, monthly_expenses=S.expenses,
            monthly_debt_payment=S.debt_payment,
            current_monthly_savings=S.savings_contrib,
        )
        return float(r.get("free_cash", 0))
    except Exception:
        return max(0.0, S.income - S.expenses - S.debt_payment - S.savings_contrib)


# ─────────────────────────────────────────────────────────────────────────────
# SHARED CHROME
# ─────────────────────────────────────────────────────────────────────────────
def _wordmark() -> None:
    st.markdown(
        '<div style="margin-bottom:1.6rem">'
        '<p style="font:italic 400 2.6rem/.85 var(--serif);text-transform:uppercase;'
        'letter-spacing:-.025em;color:var(--text);margin:0">'
        'Fin<span style="color:var(--orange)">Path</span></p>'
        '<p style="font-family:var(--mono);font-size:.6rem;letter-spacing:.14em;'
        'text-transform:uppercase;color:var(--dim);margin:.2rem 0 0">'
        'IBM SkillsBuild · Banking &amp; Financial Services</p></div>',
        unsafe_allow_html=True,
    )

def _stepper(current: int) -> None:
    labels = ["Profile","Question","Results"]
    parts: list[str] = []
    for i, label in enumerate(labels, 1):
        if i < current:
            ds="background:var(--orange);border-color:var(--orange);color:#fff"; lc="var(--muted)"; dt="✓"
        elif i == current:
            ds="border-color:var(--text);color:var(--text)"; lc="var(--text)"; dt=str(i)
        else:
            ds="border-color:var(--border2);color:var(--dim)"; lc="var(--dim)"; dt=str(i)
        parts.append(
            f'<div style="display:flex;align-items:center;gap:.4rem;font-family:var(--mono);'
            f'font-size:.6rem;letter-spacing:.08em;text-transform:uppercase">'
            f'<div style="width:20px;height:20px;border-radius:50%;border:1.5px solid;'
            f'display:flex;align-items:center;justify-content:center;font-size:.62rem;flex-shrink:0;{ds}">{dt}</div>'
            f'<span style="color:{lc};white-space:nowrap">{label}</span></div>'
        )
        if i < 3:
            parts.append(f'<div style="flex:1;height:1px;background:var(--border);margin:0 .5rem;min-width:10px;opacity:{"1" if i < current else ".4"}"></div>')
    st.markdown(f'<div style="display:flex;align-items:center;margin-bottom:1.6rem">{"".join(parts)}</div>', unsafe_allow_html=True)

def _section_label(text: str, mt: str = "1.1rem") -> None:
    st.markdown(f'<p style="font-family:var(--mono);font-size:.58rem;letter-spacing:.1em;text-transform:uppercase;color:var(--dim);margin:{mt} 0 .5rem">{text}</p>', unsafe_allow_html=True)

def _disclaimer() -> None:
    st.markdown(
        '<div style="margin-top:2rem;padding:.6rem 1rem;border-left:3px solid var(--orange);'
        'background:rgba(232,96,60,.05);border-radius:0 6px 6px 0">'
        '<span style="font-family:var(--mono);font-size:.63rem;color:var(--muted);letter-spacing:.03em">'
        'Educational tool · Not financial advice · All projections are illustrative only.</span></div>',
        unsafe_allow_html=True,
    )

def _tool_chips(tools: list[str]) -> None:
    if not tools: return
    chips = "".join(
        f'<span style="display:inline-flex;align-items:center;gap:.3rem;padding:.18rem .55rem;'
        f'margin:.2rem .2rem 0 0;background:var(--orangeA);border:1px solid var(--orangeB);'
        f'border-radius:3px;font-family:var(--mono);font-size:.6rem;color:var(--orange)">'
        f'<span style="font-size:.65rem;opacity:.7">⚙</span>{n}</span>'
        for n in tools
    )
    st.markdown(f'<div style="margin:.5rem 0 .15rem"><span style="font-family:var(--mono);font-size:.56rem;letter-spacing:.1em;text-transform:uppercase;color:var(--dim);margin-right:.4rem">Tools used</span>{chips}</div>', unsafe_allow_html=True)

def _assumptions_expander() -> None:
    with st.expander("📋 Assumptions used"):
        rows = [
            ("Monthly income",f"${S.income:,}"),("Monthly expenses",f"${S.expenses:,}"),
            ("Saving/mo",f"${S.savings_contrib:,}"),("Debt payment/mo",f"${S.debt_payment:,}"),
            ("Cash savings",f"${S.savings:,}"),("Debt balance",f"${S.debt_bal:,}"),
            ("Debt rate",f"{S.debt_rate:.1f}% p.a."),("Growth rate","5% p.a. (default)"),
            ("Horizon","12 months (default)"),("EF target","3–6 months (guideline)"),
        ]
        html = "".join(
            f'<div style="display:flex;justify-content:space-between;padding:.32rem 0;border-bottom:1px solid var(--border)">'
            f'<span style="font-family:var(--mono);font-size:.63rem;color:var(--muted)">{l}</span>'
            f'<span style="font-family:var(--mono);font-size:.63rem;color:var(--text)">{v}</span></div>'
            for l,v in rows
        )
        st.markdown(html, unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# HEALTH CARD  (local compute)
# ─────────────────────────────────────────────────────────────────────────────
def _health_card() -> None:
    if not _LOCAL_MATH or S.income <= 0 or S.expenses <= 0: return
    try:
        h = _fhc(income=S.income, expenses=S.expenses,
                 monthly_savings_contribution=S.savings_contrib,
                 current_savings=S.savings, debt_balance=S.debt_bal,
                 annual_debt_rate=S.debt_rate/100, monthly_debt_payment=S.debt_payment)
    except Exception: return

    score = h["score"]
    color = "#4EA86B" if score>=75 else ("#D4A84B" if score>=50 else ("#E8603C" if score>=25 else "#D95F5F"))
    label = "Strong" if score>=75 else ("Moderate" if score>=50 else ("Needs attention" if score>=25 else "Critical"))

    r=32; circ=2*3.14159*r; offset=circ*(1-score/100)
    ring = (f'<svg width="88" height="88" viewBox="0 0 88 88">'
            f'<circle cx="44" cy="44" r="{r}" fill="none" stroke="rgba(255,255,255,.06)" stroke-width="8"/>'
            f'<circle cx="44" cy="44" r="{r}" fill="none" stroke="{color}" stroke-width="8"'
            f' stroke-dasharray="{circ:.1f}" stroke-dashoffset="{offset:.1f}"'
            f' stroke-linecap="round" transform="rotate(-90 44 44)"/>'
            f'<text x="44" y="48" text-anchor="middle" font-family="JetBrains Mono,monospace"'
            f' font-size="18" font-weight="600" fill="{color}">{score}</text></svg>')

    def _bar(lbl,val):
        pct=val/25*100; c="#4EA86B" if pct>=80 else ("#D4A84B" if pct>=44 else "#E8603C")
        return (f'<div style="margin-bottom:.5rem"><div style="display:flex;justify-content:space-between;margin-bottom:.22rem">'
                f'<span style="font-family:var(--mono);font-size:.58rem;letter-spacing:.06em;text-transform:uppercase;color:var(--muted)">{lbl}</span>'
                f'<span style="font-family:var(--mono);font-size:.6rem;color:{c}">{val}/25</span></div>'
                f'<div style="height:4px;background:rgba(255,255,255,.06);border-radius:2px">'
                f'<div style="width:{pct:.0f}%;height:100%;background:{c};border-radius:2px;transition:width .4s"></div></div></div>')

    bars = _bar("Cash flow",h["cash_flow_score"])+_bar("Emergency fund",h["emergency_fund_score"])+_bar("Debt burden",h["debt_burden_score"])+_bar("Savings rate",h["savings_rate_score"])

    cf=h["cash_flow"]; cf_c="#4EA86B" if cf>=0 else "#D95F5F"
    ef=h["emergency_fund_months"]; ef_c="#4EA86B" if ef>=3 else ("#D4A84B" if ef>=1 else "#D95F5F")
    dti=h["debt_to_income_ratio"]*100; dti_c="#4EA86B" if dti<=15 else ("#D4A84B" if dti<=28 else "#D95F5F")
    sr=h["savings_rate"]*100; sr_c="#4EA86B" if sr>=10 else ("#D4A84B" if sr>=5 else "#D95F5F")

    def _stat(lbl,val,c):
        return (f'<div style="flex:1;min-width:0;padding:.55rem .6rem;background:var(--surface2);'
                f'border-radius:var(--radius-sm);border:1px solid var(--border)">'
                f'<div style="font-family:var(--mono);font-size:.54rem;letter-spacing:.08em;text-transform:uppercase;color:var(--dim);margin-bottom:.25rem">{lbl}</div>'
                f'<div style="font-family:var(--mono);font-size:.9rem;font-weight:600;color:{c}">{val}</div></div>')

    stats=(f'<div style="display:flex;gap:.4rem;margin-bottom:.9rem;flex-wrap:wrap">'
           +_stat("Surplus/mo",f"${cf:+,.0f}",cf_c)+_stat("EF coverage",f"{ef:.1f} mo",ef_c)
           +_stat("Debt/income",f"{dti:.0f}%",dti_c)+_stat("Saving rate",f"{sr:.0f}%",sr_c)+'</div>')

    pri_items="".join(
        f'<div style="display:flex;align-items:flex-start;gap:.55rem;padding:.4rem .65rem;'
        f'margin-bottom:.28rem;background:var(--surface2);border-radius:var(--radius-sm);border:1px solid var(--border)">'
        f'<span style="color:var(--orange);font-size:.8rem;margin-top:.05rem;flex-shrink:0">›</span>'
        f'<span style="font-family:var(--mono);font-size:.63rem;color:var(--muted);line-height:1.4">{p}</span></div>'
        for p in h["priorities"][:3]
    )

    st.markdown(
        f'<div style="margin:1.2rem 0 0;padding:1rem 1.1rem 1.1rem;background:var(--surface);border:1px solid var(--border2);border-radius:var(--radius)">'
        f'<div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:.9rem">'
        f'<div><p style="font-family:var(--mono);font-size:.58rem;letter-spacing:.1em;text-transform:uppercase;color:var(--dim);margin:0 0 .2rem">Financial health</p>'
        f'<p style="font:italic 400 1.35rem/1 var(--serif);color:{color};margin:0">{label}</p></div>'
        f'<div>{ring}</div></div>'
        +stats+bars
        +f'<p style="font-family:var(--mono);font-size:.58rem;letter-spacing:.1em;text-transform:uppercase;color:var(--dim);margin:.7rem 0 .4rem">Priorities</p>'
        +pri_items+'</div>',
        unsafe_allow_html=True,
    )


# ─────────────────────────────────────────────────────────────────────────────
# GOAL CARDS  (local compute, one per goal)
# ─────────────────────────────────────────────────────────────────────────────
def _one_goal_card(goal: dict, headroom_per_goal: float) -> None:
    """Render a single goal feasibility card."""
    if not _LOCAL_MATH: return
    target  = goal.get("target", 0)
    months  = goal.get("months", 12)
    saved   = goal.get("current_saved", 0)
    name    = goal.get("name", "") or "Goal"
    if target <= 0 or months <= 0: return
    try:
        g = _goal_plan(target_amount=float(target), months_to_goal=int(months),
                       current_saved=float(saved), monthly_headroom=headroom_per_goal)
    except Exception: return

    ok    = g["feasible"]
    color = "#4EA86B" if ok else "#D95F5F"
    icon  = "✓" if ok else "✗"
    lbl   = "Feasible" if ok else "Not feasible"
    req   = g["required_monthly"]
    mn    = g["months_needed_at_current_headroom"]

    detail = (f'${req:,.0f}/mo needed · ${headroom_per_goal:,.0f}/mo available · ${req-headroom_per_goal:+,.0f}/mo to close'
              if not ok else f'${req:,.0f}/mo needed · ${headroom_per_goal-req:,.0f}/mo to spare')
    extra  = (f'<div style="font-family:var(--mono);font-size:.6rem;color:var(--dim);margin-top:.3rem">At current headroom: {mn} months</div>'
              if not ok and mn else "")

    st.markdown(
        f'<div style="margin:.5rem 0;padding:.6rem .85rem;background:var(--surface);'
        f'border:1px solid var(--border);border-left:3px solid {color};border-radius:0 var(--radius-sm) var(--radius-sm) 0">'
        f'<div style="display:flex;align-items:center;gap:.45rem;margin-bottom:.15rem">'
        f'<span style="font-family:var(--mono);font-size:.8rem;color:{color};font-weight:600">{icon}</span>'
        f'<span style="font-family:var(--mono);font-size:.65rem;color:{color};font-weight:600;text-transform:uppercase;letter-spacing:.06em">{name}</span>'
        f'<span style="font-family:var(--mono);font-size:.6rem;color:var(--dim);margin-left:auto">{lbl}</span></div>'
        f'<div style="font-family:var(--mono);font-size:.6rem;color:var(--muted)">{detail}</div>'
        f'{extra}</div>',
        unsafe_allow_html=True,
    )

def _goal_cards() -> None:
    """Render feasibility cards for all goals with targets."""
    active = [g for g in S.goals if g.get("target", 0) > 0]
    if not active: return
    headroom      = _headroom()
    headroom_each = max(0.0, headroom / len(active))
    for goal in active:
        _one_goal_card(goal, headroom_each)


# ── Save / Load profile helpers ───────────────────────────────────────────────
def _export_profile_json() -> str:
    """Serialise all financial session state to JSON (no chat history, no thread_id)."""
    return json.dumps({
        "income": S.income, "expenses": S.expenses, "savings": S.savings,
        "savings_contrib": S.savings_contrib, "debt_bal": S.debt_bal,
        "debt_payment": S.debt_payment, "debt_rate": S.debt_rate, "goal": S.goal,
        "inc_salary": S.inc_salary, "inc_side": S.inc_side, "inc_other": S.inc_other,
        "exp_housing": S.exp_housing, "exp_food": S.exp_food,
        "exp_transport": S.exp_transport, "exp_subs": S.exp_subs, "exp_other": S.exp_other,
        "sav_emergency": S.sav_emergency, "sav_invest": S.sav_invest, "sav_other": S.sav_other,
        "goals": S.goals, "multi_debts": S.multi_debts, "use_multi_debt": S.use_multi_debt,
    }, indent=2)

def _load_profile_from_dict(d: dict) -> None:
    """Restore session state from an exported profile dict."""
    for key in ["income","expenses","savings","savings_contrib","debt_bal",
                "debt_payment","debt_rate","goal",
                "inc_salary","inc_side","inc_other",
                "exp_housing","exp_food","exp_transport","exp_subs","exp_other",
                "sav_emergency","sav_invest","sav_other"]:
        if key in d:
            setattr(S, key, d[key])
            # also write the widget key so inputs update
            wk = f"in_{key}"
            st.session_state[wk] = d[key]
    if "goals" in d and isinstance(d["goals"], list):
        S.goals = d["goals"]
    if "multi_debts" in d:
        S.multi_debts = d["multi_debts"]
    if "use_multi_debt" in d:
        S.use_multi_debt = d["use_multi_debt"]
    S.profile = None  # mark as custom

# ─────────────────────────────────────────────────────────────────────────────
# STEP 1 — PROFILE
# ─────────────────────────────────────────────────────────────────────────────
def render_step1() -> None:
    _wordmark(); _stepper(1)
    st.markdown(
        '<h2 style="font:italic 400 1.65rem/1.1 var(--serif);margin:0 0 .2rem">'
        'Your <span style="color:var(--orange)">profile</span></h2>'
        '<p style="font-family:var(--mono);font-size:.62rem;letter-spacing:.05em;'
        'text-transform:uppercase;color:var(--muted);margin-bottom:1.4rem">'
        'Step 1 of 3 · Select a sample or fill in your own numbers</p>',
        unsafe_allow_html=True,
    )

    # ── Load / Save profile row ───────────────────────────────────────────────
    _section_label("Load or save profile", mt="0")
    ld_col, sv_col = st.columns([1, 1], gap="small")
    with ld_col:
        uploaded = st.file_uploader("⬆ Load a saved profile", type="json", key="profile_upload",
                                    label_visibility="collapsed")
        if uploaded is not None:
            try:
                d = json.load(uploaded)
                _load_profile_from_dict(d)
                st.rerun()
            except Exception:
                st.markdown('<div style="font-family:var(--mono);font-size:.63rem;color:#D95F5F;margin-top:.3rem">Could not read file — make sure it was saved by FinPath AI.</div>', unsafe_allow_html=True)
    with sv_col:
        st.download_button(
            "⬇ Save my profile",
            data=_export_profile_json().encode(),
            file_name=f"finpath_profile_{date.today().isoformat()}.json",
            mime="application/json",
            use_container_width=True,
            key="btn_save_profile",
        )

    # ── Sample profiles grid ──────────────────────────────────────────────────
    _section_label("Sample profiles", mt=".9rem")
    rows = [PROFILES[i:i+3] for i in range(0, len(PROFILES), 3)]
    for row in rows:
        cols = st.columns(3)
        for col, p in zip(cols, row):
            is_sel = S.profile is not None and S.profile["id"] == p["id"]
            name = p["label"].split("—")[0].strip()
            desc = p["label"].split("—")[1].strip() if "—" in p["label"] else ""
            with col:
                st.markdown('<div class="profile-selected">' if is_sel else '<div>', unsafe_allow_html=True)
                st.button(name, key=f"chip_{p['id']}", use_container_width=True, on_click=_load_profile, args=(p,))
                if desc: st.caption(desc)
                st.markdown('</div>', unsafe_allow_html=True)

    cc, _ = st.columns([1,3])
    with cc:
        st.button("↺ Clear", key="chip_manual", type="tertiary", on_click=_clear_profile)
    if S.profile:
        st.markdown(f'<p style="font-family:var(--mono);font-size:.62rem;color:var(--orange);margin:.3rem 0 .8rem">✓ {S.profile["label"]}</p>', unsafe_allow_html=True)

    st.markdown('<hr>', unsafe_allow_html=True)

    # ── Income breakdown ──────────────────────────────────────────────────────
    with st.expander(f"💵 Income  —  total ${S.income:,}/mo", expanded=True):
        ia, ib, ic = st.columns(3, gap="small")
        with ia:
            S.inc_salary = st.number_input("Salary / wages ($)", min_value=0, step=100, value=int(S.inc_salary), key="in_inc_salary")
        with ib:
            S.inc_side = st.number_input("Side income ($)", min_value=0, step=50, value=int(S.inc_side), key="in_inc_side")
        with ic:
            S.inc_other = st.number_input("Other income ($)", min_value=0, step=50, value=int(S.inc_other), key="in_inc_other")
        S.income = int(S.inc_salary + S.inc_side + S.inc_other)
        # keep legacy widget key in sync
        st.session_state["in_income"] = S.income
        st.caption(f"Total monthly income: ${S.income:,}")

    # ── Expense breakdown ─────────────────────────────────────────────────────
    with st.expander(f"💸 Expenses  —  total ${S.expenses:,}/mo", expanded=True):
        ea, eb = st.columns(2, gap="small")
        with ea:
            S.exp_housing   = st.number_input("Housing / rent ($)",     min_value=0, step=50, value=int(S.exp_housing),   key="in_exp_housing")
            S.exp_food      = st.number_input("Food & groceries ($)",   min_value=0, step=50, value=int(S.exp_food),      key="in_exp_food")
            S.exp_transport = st.number_input("Transport ($)",          min_value=0, step=50, value=int(S.exp_transport), key="in_exp_transport")
        with eb:
            S.exp_subs  = st.number_input("Subscriptions ($)",  min_value=0, step=10, value=int(S.exp_subs),  key="in_exp_subs")
            S.exp_other = st.number_input("Other expenses ($)", min_value=0, step=50, value=int(S.exp_other), key="in_exp_other")
        S.expenses = int(S.exp_housing + S.exp_food + S.exp_transport + S.exp_subs + S.exp_other)
        st.session_state["in_expenses"] = S.expenses
        st.caption(f"Total monthly expenses: ${S.expenses:,}")

    # ── Savings breakdown ─────────────────────────────────────────────────────
    with st.expander(f"🏦 Savings  —  total ${S.savings:,}", expanded=False):
        sa, sb, sc = st.columns(3, gap="small")
        with sa:
            S.sav_emergency = st.number_input("Emergency fund ($)", min_value=0, step=500, value=int(S.sav_emergency), key="in_sav_emergency")
        with sb:
            S.sav_invest = st.number_input("Investments ($)", min_value=0, step=500, value=int(S.sav_invest), key="in_sav_invest")
        with sc:
            S.sav_other = st.number_input("Other savings ($)", min_value=0, step=100, value=int(S.sav_other), key="in_sav_other")
        S.savings = int(S.sav_emergency + S.sav_invest + S.sav_other)
        st.session_state["in_savings"] = S.savings
        st.caption(f"Total savings: ${S.savings:,}")

    # ── Savings contribution & debt ───────────────────────────────────────────
    lc2, rc2 = st.columns([1,1], gap="large")
    with lc2:
        _section_label("Savings contribution", mt=".8rem")
        S.savings_contrib = st.number_input("Currently saving per month ($)", min_value=0, step=50, value=int(S.savings_contrib), key="in_savings_contrib")
    with rc2:
        _section_label("Goal context", mt=".8rem")
        S.goal = st.text_input("Goal summary (optional)", value=S.goal, placeholder="e.g. Pay off debt in 3 years", key="in_goal")

    lc3, rc3 = st.columns([1,1], gap="large")
    with lc3:
        _section_label("Debt", mt=".8rem")
        S.debt_bal    = st.number_input("Total debt balance ($)",    min_value=0, step=1000, value=int(S.debt_bal),     key="in_debt_bal")
        S.debt_payment= st.number_input("Monthly debt payment ($)", min_value=0, step=50,   value=int(S.debt_payment),  key="in_debt_payment")
    with rc3:
        _section_label("Debt rate", mt=".8rem")
        S.debt_rate = st.number_input("Interest rate (% p.a.)", min_value=0.0, max_value=50.0, step=0.5, value=float(S.debt_rate), key="in_debt_rate", format="%.1f")

    # ── Multiple goals ────────────────────────────────────────────────────────
    st.markdown('<hr style="margin:.8rem 0">', unsafe_allow_html=True)
    _section_label("My goals", mt="0")

    # Render each goal row
    for idx, goal in enumerate(S.goals):
        g1, g2, g3, g4, g_rm = st.columns([2, 1.2, 1.2, 1, 0.5], gap="small")
        with g1:
            S.goals[idx]["name"] = st.text_input(
                "Goal name", value=goal.get("name", ""), placeholder="e.g. Emergency fund",
                key=f"g_name_{idx}", label_visibility="collapsed" if idx > 0 else "visible",
            )
        with g2:
            S.goals[idx]["target"] = st.number_input(
                "Target ($)", min_value=0, step=500, value=int(goal.get("target", 0)),
                key=f"g_target_{idx}", label_visibility="collapsed" if idx > 0 else "visible",
            )
        with g3:
            S.goals[idx]["current_saved"] = st.number_input(
                "Already saved ($)", min_value=0, step=100, value=int(goal.get("current_saved", 0)),
                key=f"g_saved_{idx}", label_visibility="collapsed" if idx > 0 else "visible",
            )
        with g4:
            S.goals[idx]["months"] = st.number_input(
                "Months", min_value=1, max_value=360, step=1, value=int(goal.get("months", 12)),
                key=f"g_months_{idx}", label_visibility="collapsed" if idx > 0 else "visible",
            )
        with g_rm:
            if idx == 0:
                st.markdown('<div style="height:1.6rem"></div>', unsafe_allow_html=True)  # align with labels
            if st.button("✕", key=f"g_rm_{idx}", disabled=(len(S.goals) <= 1)):
                S.goals.pop(idx); st.rerun()

    if len(S.goals) < 5:
        if st.button("＋ Add goal", key="g_add", type="tertiary"):
            S.goals.append({"name": "", "target": 0, "current_saved": 0, "months": 12})
            st.rerun()

    _goal_cards()

    # ── Multi-debt table ──────────────────────────────────────────────────────
    st.markdown('<hr style="margin:.8rem 0">', unsafe_allow_html=True)
    S.use_multi_debt = st.checkbox("I have multiple debts", value=S.use_multi_debt)
    if S.use_multi_debt:
        _section_label("Debt table — avalanche vs snowball will be computed for you", mt=".4rem")
        import pandas as pd
        df = pd.DataFrame(S.multi_debts)
        edited = st.data_editor(df, num_rows="dynamic", use_container_width=True, key="debt_table",
                                column_config={
                                    "Name": st.column_config.TextColumn("Name"),
                                    "Balance ($)": st.column_config.NumberColumn("Balance ($)", min_value=0, step=100),
                                    "APR (%)": st.column_config.NumberColumn("APR (%)", min_value=0, max_value=50, step=0.5),
                                    "Min Payment ($)": st.column_config.NumberColumn("Min Payment ($)", min_value=1, step=10),
                                })
        S.multi_debts = edited.to_dict("records")

    # Health card
    _health_card()

    st.markdown('<hr>', unsafe_allow_html=True)
    _, bc = st.columns([3,1])
    with bc:
        st.button("Next →", key="step1_next", use_container_width=True, type="primary",
                  disabled=(S.income==0 or S.expenses==0), on_click=lambda: _go(2))
    _disclaimer()


# ─────────────────────────────────────────────────────────────────────────────
# STEP 2 — QUESTION
# ─────────────────────────────────────────────────────────────────────────────
def _set_question(q: str) -> None:
    st.session_state["in_question"] = q
    st.session_state["question"]    = q

def render_step2() -> None:
    _wordmark(); _stepper(2)
    st.markdown(
        '<h2 style="font:italic 400 1.65rem/1.1 var(--serif);margin:0 0 .2rem">'
        'Your <span style="color:var(--orange)">question</span></h2>'
        '<p style="font-family:var(--mono);font-size:.62rem;letter-spacing:.05em;'
        'text-transform:uppercase;color:var(--muted);margin-bottom:1.2rem">'
        'Step 2 of 3 · Ask about your financial situation</p>',
        unsafe_allow_html=True,
    )
    pill='display:inline-flex;align-items:center;gap:.3rem;padding:.2rem .6rem;margin:.12rem .18rem;background:var(--surface2);border:1px solid var(--border);border-radius:20px;font-family:var(--mono);font-size:.6rem;color:var(--muted);white-space:nowrap'
    vs='color:var(--text);font-weight:500'
    st.markdown(
        f'<div style="display:flex;flex-wrap:wrap;margin-bottom:1.3rem">'
        f'<span style="{pill}">Income <b style="{vs}">${S.income:,}</b></span>'
        f'<span style="{pill}">Expenses <b style="{vs}">${S.expenses:,}</b></span>'
        f'<span style="{pill}">Savings <b style="{vs}">${S.savings:,}</b></span>'
        f'<span style="{pill}">Saving/mo <b style="{vs}">${S.savings_contrib:,}</b></span>'
        f'<span style="{pill}">Debt <b style="{vs}">${S.debt_bal:,} @ {S.debt_rate:.1f}%</b></span>'
        f'</div>', unsafe_allow_html=True,
    )
    _section_label("Quick suggestions", mt="0")
    c1, c2 = st.columns(2, gap="small")
    for i, s in enumerate(SUGGESTIONS):
        col = c1 if i%2==0 else c2
        with col:
            st.markdown('<div class="sug-btn">', unsafe_allow_html=True)
            st.button(s, key=f"sug_{i}", use_container_width=True, on_click=_set_question, args=(s,))
            st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div style="margin-top:1rem"></div>', unsafe_allow_html=True)
    if "in_question" not in st.session_state:
        st.session_state["in_question"] = st.session_state.get("question","")
    S.question = st.text_area("Or type your own question", height=90,
                               placeholder="e.g. Should I pay extra on my debt or put it in savings?", key="in_question")
    S.question = st.session_state["in_question"]

    st.markdown('<hr>', unsafe_allow_html=True)
    bc, gc = st.columns([1,1])
    with bc:
        if st.button("← Edit profile", key="step2_back", use_container_width=True): _go(1)
    with gc:
        if st.button("Ask FinPath →", key="step2_run", use_container_width=True, type="primary", disabled=not S.question.strip()):
            S.messages=[]; S.thread_id=None; S.pending_send=None; S.error=None; _go(3)
    _disclaimer()


# ─────────────────────────────────────────────────────────────────────────────
# STEP 3 — CHAT + WHAT-IF + VERIFIED BADGE
# ─────────────────────────────────────────────────────────────────────────────
def _send_message(text: str) -> None:
    S.messages.append({"role":"user","content":text,"tools":[],"verified":None})
    S.pending_send = text; S.error = None

def _run_agent() -> None:
    if not S.pending_send: return
    user_text = S.pending_send; S.pending_send = None
    with st.spinner("FinPath AI is thinking…"):
        try:
            res = ask_agent(message=user_text, profile=_build_profile_dict(), thread_id=S.thread_id)
            S.thread_id = res["thread_id"]
            verified    = res.get("verified", None)
            S.messages.append({"role":"assistant","content":res["reply"],
                                "tools":res["tools"],"verified":verified})
        except (RuntimeError, TimeoutError) as e:
            S.error = str(e)
            if S.messages and S.messages[-1]["role"]=="user": S.messages.pop()
        except Exception:
            S.error = "Unexpected error. Check your Orchestrate environment is active."
            if S.messages and S.messages[-1]["role"]=="user": S.messages.pop()
    st.rerun()


def _verified_badge(verified: bool | None) -> None:
    if verified is None: return
    if verified:
        badge_html = ('<span style="display:inline-flex;align-items:center;gap:.3rem;'
                      'padding:.18rem .6rem;background:var(--greenA);border:1px solid rgba(78,168,107,.3);'
                      'border-radius:3px;font-family:var(--mono);font-size:.6rem;color:var(--green)">'
                      '✓ All figures verified against calculations</span>')
    else:
        badge_html = ('<span style="display:inline-flex;align-items:center;gap:.3rem;'
                      'padding:.18rem .6rem;background:rgba(217,95,95,.10);border:1px solid rgba(217,95,95,.28);'
                      'border-radius:3px;font-family:var(--mono);font-size:.6rem;color:#D95F5F">'
                      '⚠ Some figures could not be verified</span>')
    st.markdown(f'<div style="margin:.4rem 0">{badge_html}</div>', unsafe_allow_html=True)


def _whatiif_section() -> None:
    """What-if sliders + Altair charts — all local math, no agent call."""
    if not _LOCAL_MATH: return
    try:
        import pandas as pd
        import altair as alt
    except ImportError:
        return

    with st.expander("🔀 What-if explorer"):
        s1, s2 = st.columns(2, gap="large")
        with s1:
            extra_pmt = st.slider("Extra debt payment ($/mo)", 0, 1000, int(S.wi_extra_pmt), step=50, key="sl_extra")
            S.wi_extra_pmt = extra_pmt
        with s2:
            income_chg = st.slider("Income change (%)", -30, 30, int(S.wi_income_chg), step=5, key="sl_income")
            S.wi_income_chg = income_chg

        MONTHS = 36
        base_pmt = S.debt_payment
        adj_pmt  = base_pmt + extra_pmt
        adj_inc  = S.income * (1 + income_chg / 100)
        adj_contrib = max(0, S.savings_contrib + (adj_inc - S.income))

        debt_base = _debt_schedule(S.debt_bal, base_pmt, S.debt_rate/100, MONTHS)
        debt_adj  = _debt_schedule(S.debt_bal, adj_pmt,  S.debt_rate/100, MONTHS)
        sav_base  = _savings_schedule(S.savings, S.savings_contrib, 0.05, MONTHS)
        sav_adj   = _savings_schedule(S.savings, adj_contrib,       0.05, MONTHS)

        # Captions
        try:
            payoff_base = next((i+1 for i,v in enumerate(debt_base) if v==0), None)
            payoff_adj  = next((i+1 for i,v in enumerate(debt_adj)  if v==0), None)
            int_base = S.debt_bal - sum(max(0, debt_base[i-1] - debt_base[i]) for i in range(1, MONTHS)) if payoff_base else None
            months_saved = (payoff_base - payoff_adj) if payoff_base and payoff_adj else None
            if extra_pmt > 0 and months_saved and months_saved > 0:
                int_diff = (sum(S.debt_bal*(S.debt_rate/100/12)*(S.debt_bal/S.debt_bal) for _ in range(1)) or 0)
                st.caption(f"🎯 Debt-free {months_saved} month(s) sooner with extra ${extra_pmt}/mo")
            elif income_chg != 0:
                st.caption(f"{'📈' if income_chg > 0 else '📉'} Income {income_chg:+.0f}% → adjusted saving: ${adj_contrib:,.0f}/mo")
        except Exception:
            pass

        months_x = list(range(1, MONTHS+1))
        df_debt = pd.DataFrame({
            "Month": months_x + months_x,
            "Debt Balance ($)": debt_base + debt_adj,
            "Scenario": ["Baseline"]*MONTHS + [f"{'Extra $' + str(extra_pmt) if extra_pmt else 'Baseline'}"]*MONTHS,
        })
        df_sav = pd.DataFrame({
            "Month": months_x + months_x,
            "Savings ($)": sav_base + sav_adj,
            "Scenario": ["Baseline"]*MONTHS + [f"{'Income ' + str(income_chg) + '%' if income_chg else 'Baseline'}"]*MONTHS,
        })

        ch_debt = (alt.Chart(df_debt).mark_line(point=False).encode(
            x=alt.X("Month:Q", axis=alt.Axis(labelColor="#A6ACB4", gridColor="rgba(255,255,255,.05)", domainColor="rgba(0,0,0,0)", tickColor="rgba(0,0,0,0)")),
            y=alt.Y("Debt Balance ($):Q", axis=alt.Axis(labelColor="#A6ACB4", gridColor="rgba(255,255,255,.05)", domainColor="rgba(0,0,0,0)", tickColor="rgba(0,0,0,0)", format="$,.0f")),
            color=alt.Color("Scenario:N", scale=alt.Scale(range=["#A6ACB4","#E8603C"]), legend=alt.Legend(labelColor="#ECE8E1", titleColor="#ECE8E1")),
            tooltip=["Month:Q","Debt Balance ($):Q","Scenario:N"],
        ).properties(title=alt.TitleParams("Debt balance over 36 months", color="#A6ACB4", fontSize=11), height=180)
        .configure_view(strokeOpacity=0, fill="#131720").configure(background="#0B0D10"))

        ch_sav = (alt.Chart(df_sav).mark_line(point=False).encode(
            x=alt.X("Month:Q", axis=alt.Axis(labelColor="#A6ACB4", gridColor="rgba(255,255,255,.05)", domainColor="rgba(0,0,0,0)", tickColor="rgba(0,0,0,0)")),
            y=alt.Y("Savings ($):Q", axis=alt.Axis(labelColor="#A6ACB4", gridColor="rgba(255,255,255,.05)", domainColor="rgba(0,0,0,0)", tickColor="rgba(0,0,0,0)", format="$,.0f")),
            color=alt.Color("Scenario:N", scale=alt.Scale(range=["#A6ACB4","#5B9BD5"]), legend=alt.Legend(labelColor="#ECE8E1", titleColor="#ECE8E1")),
            tooltip=["Month:Q","Savings ($):Q","Scenario:N"],
        ).properties(title=alt.TitleParams("Savings over 36 months", color="#A6ACB4", fontSize=11), height=180)
        .configure_view(strokeOpacity=0, fill="#131720").configure(background="#0B0D10"))

        col_d, col_s = st.columns(2)
        with col_d: st.altair_chart(ch_debt, use_container_width=True)
        with col_s: st.altair_chart(ch_sav,  use_container_width=True)


def _download_summary() -> None:
    """Build a markdown download of the full conversation."""
    lines = ["# FinPath AI — Conversation Summary\n"]
    lines.append(f"**Date:** {date.today().isoformat()}\n")
    lines.append("## Profile\n")
    lines += [
        f"- Monthly income: ${S.income:,}",
        f"- Monthly expenses: ${S.expenses:,}",
        f"- Currently saving/mo: ${S.savings_contrib:,}",
        f"- Cash savings: ${S.savings:,}",
        f"- Debt balance: ${S.debt_bal:,} @ {S.debt_rate:.1f}% p.a.",
        f"- Monthly debt payment: ${S.debt_payment:,}",
        f"- Goal: {S.goal or 'not specified'}",
        "",
    ]
    lines.append("## Conversation\n")
    for msg in S.messages:
        role = "**You**" if msg["role"]=="user" else "**FinPath AI**"
        tools_str = f"\n*Tools used: {', '.join(msg['tools'])}*" if msg.get("tools") else ""
        lines.append(f"{role}: {msg['content']}{tools_str}\n")
    lines.append("\n---\n*FinPath AI provides illustrative projections only. Not financial advice.*")
    return "\n".join(lines)


def render_step3() -> None:
    _wordmark(); _stepper(3)
    st.markdown(
        '<h2 style="font:italic 400 1.65rem/1.1 var(--serif);margin:0 0 .2rem">'
        'Your <span style="color:var(--orange)">results</span></h2>'
        '<p style="font-family:var(--mono);font-size:.62rem;letter-spacing:.05em;'
        'text-transform:uppercase;color:var(--muted);margin-bottom:1rem">'
        'Step 3 of 3 · Illustrative projections — not financial advice</p>',
        unsafe_allow_html=True,
    )

    if not S.messages and S.question:
        _send_message(S.question)

    _run_agent()

    if S.error:
        st.markdown(
            f'<div style="padding:.7rem 1rem;background:rgba(217,95,95,.10);'
            f'border:1px solid rgba(217,95,95,.28);border-radius:var(--radius);'
            f'font-family:var(--mono);font-size:.75rem;color:#D95F5F;margin-bottom:.8rem">'
            f'⚠ {S.error}</div>', unsafe_allow_html=True,
        )
        if st.button("Dismiss ×", key="err_dismiss"): S.error=None; st.rerun()

    # Sidebar history
    with st.sidebar:
        st.markdown('<p style="font-family:var(--mono);font-size:.6rem;letter-spacing:.1em;text-transform:uppercase;color:var(--dim)">This conversation</p>', unsafe_allow_html=True)
        user_msgs = [m for m in S.messages if m["role"]=="user"]
        if user_msgs:
            for i, m in enumerate(user_msgs):
                st.markdown(f'<div style="font-family:var(--mono);font-size:.65rem;color:var(--muted);padding:.25rem 0;border-bottom:1px solid var(--border)">{i+1}. {m["content"][:60]}{"…" if len(m["content"])>60 else ""}</div>', unsafe_allow_html=True)
        else:
            st.markdown('<p style="font-family:var(--mono);font-size:.62rem;color:var(--dim)">No questions yet</p>', unsafe_allow_html=True)

    # Chat history
    for msg in S.messages:
        if msg["role"]=="user":
            with st.chat_message("user"):
                st.markdown(msg["content"])
        else:
            with st.chat_message("assistant"):
                st.markdown(msg["content"])
                if msg.get("tools"):     _tool_chips(msg["tools"])
                if msg.get("verified") is not None: _verified_badge(msg["verified"])

    # Follow-up chips
    if S.messages and S.messages[-1]["role"]=="assistant" and not S.pending_send:
        _section_label("Follow-up suggestions", mt=".8rem")
        fc = st.columns(len(FOLLOWUP_SUGGESTIONS), gap="small")
        for col, sug in zip(fc, FOLLOWUP_SUGGESTIONS):
            with col:
                st.markdown('<div class="sug-btn">', unsafe_allow_html=True)
                st.button(sug, key=f"fu_{sug[:18]}", use_container_width=True, on_click=_send_message, args=(sug,))
                st.markdown('</div>', unsafe_allow_html=True)

    # Chat input
    inp = st.chat_input("Ask a follow-up…")
    if inp and inp.strip(): _send_message(inp.strip()); st.rerun()

    # What-if sliders + charts
    if S.messages and _LOCAL_MATH:
        _whatiif_section()

    # Assumptions expander
    if S.messages: _assumptions_expander()

    # How it works
    with st.expander("ℹ️ How FinPath AI works"):
        st.markdown(
            "**Every number comes from a verified tool call** — the agent (IBM watsonx Orchestrate) "
            "never computes figures itself. Your question and profile are sent to the agent, which calls "
            "deterministic Python functions (`debt_payoff_months`, `savings_headroom`, etc.) and quotes "
            "their output directly.\n\n"
            "```\nYour question + profile\n  → IBM watsonx Orchestrate agent\n    → @tool functions\n"
            "      → deterministic math (pure Python, no AI)\n        → verified numbers\n"
            "          → plain-language explanation\n```\n\n"
            "All projections are illustrative. This is not financial advice."
        )

    st.markdown('<hr>', unsafe_allow_html=True)

    lc, rc = st.columns([1,1])
    with lc:
        if st.button("← Edit profile", key="res_back"): S.error=None; _go(1)
    with rc:
        if st.button("New conversation", key="res_new", use_container_width=True):
            S.messages=[]; S.thread_id=None; S.question=""; S.error=None; S.pending_send=None
            st.session_state.pop("in_question", None); _go(2)

    # Download button
    if S.messages:
        summary_md = _download_summary()
        st.download_button(
            label="⬇ Download summary",
            data=summary_md.encode(),
            file_name=f"finpath_summary_{date.today().isoformat()}.md",
            mime="text/markdown",
            use_container_width=True,
        )

    _disclaimer()


# ─────────────────────────────────────────────────────────────────────────────
# ROUTER
# ─────────────────────────────────────────────────────────────────────────────
if   S.step == 1: render_step1()
elif S.step == 2: render_step2()
elif S.step == 3: render_step3()
