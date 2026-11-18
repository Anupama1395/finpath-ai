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

import base64
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
# (short chip label, full question sent to the agent)
FOLLOWUP_SUGGESTIONS = [
    ("+$100/mo debt payment?", "What if I paid $100 more a month toward my debt?"),
    ("Income down 10%?",       "What if my income dropped 10%?"),
    ("Invest vs pay debt?",    "Should I invest instead of paying debt?"),
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
        "step":            0,
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
        "agent_offline":   False,   # True when agent is unreachable (demo mode)
        "initial_sent":    False,
        "last_failed":     None,
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

    # Income breakdown — use profile fields if present, else put total in salary
    inc = p.get("income_breakdown", {})
    S.inc_salary   = int(inc.get("salary",       income))
    S.inc_side     = int(inc.get("side_income",  0))
    S.inc_other    = int(inc.get("other",         0))
    # Guard: if breakdown doesn't sum to income, fall back to total-in-salary
    if S.inc_salary + S.inc_side + S.inc_other != income:
        S.inc_salary = income; S.inc_side = 0; S.inc_other = 0

    # Expense breakdown — use profile fields if present, else put total in housing
    exp = p.get("expense_breakdown", {})
    S.exp_housing   = int(exp.get("housing",       expenses if not exp else 0))
    S.exp_food      = int(exp.get("food",          0))
    S.exp_transport = int(exp.get("transport",     0))
    S.exp_subs      = int(exp.get("subscriptions", 0))
    S.exp_other     = int(exp.get("other",         0))
    if S.exp_housing + S.exp_food + S.exp_transport + S.exp_subs + S.exp_other != expenses:
        S.exp_housing = expenses; S.exp_food = 0; S.exp_transport = 0; S.exp_subs = 0; S.exp_other = 0

    # Savings breakdown — use profile fields if present, else put total in emergency
    sav = p.get("savings_breakdown", {})
    S.sav_emergency = int(sav.get("emergency_fund", savings if not sav else 0))
    S.sav_invest    = int(sav.get("investments",    0))
    S.sav_other     = int(sav.get("other",          0))
    if S.sav_emergency + S.sav_invest + S.sav_other != savings:
        S.sav_emergency = savings; S.sav_invest = 0; S.sav_other = 0

    # Seed an Emergency fund goal: target = 3 × expenses, saved = cash_savings
    ef_target = expenses * 3
    S.goals = [{"name": "Emergency fund", "target": ef_target, "current_saved": savings, "months": 12}]
    # Write goal widget keys directly (same pattern as all other inputs).
    # Deleting keys doesn't work reliably for widgets that are currently rendered;
    # explicitly setting them is the only way to guarantee the new value appears.
    st.session_state["g_name_0"]   = "Emergency fund"
    st.session_state["g_target_0"] = ef_target
    st.session_state["g_saved_0"]  = savings
    st.session_state["g_months_0"] = 12
    # Remove any extra goal rows that may have been added in a previous session
    for extra in range(1, 10):
        for pfx in ("g_name_", "g_target_", "g_saved_", "g_months_"):
            st.session_state.pop(f"{pfx}{extra}", None)

    # Write widget keys directly
    st.session_state["in_income"]=income; st.session_state["in_expenses"]=expenses
    st.session_state["in_savings"]=savings; st.session_state["in_savings_contrib"]=contrib
    st.session_state["in_debt_bal"]=debt_bal; st.session_state["in_debt_payment"]=debt_pmt
    st.session_state["in_debt_rate"]=rate; st.session_state["in_goal"]=goal
    st.session_state["in_inc_salary"]=S.inc_salary; st.session_state["in_inc_side"]=S.inc_side; st.session_state["in_inc_other"]=S.inc_other
    st.session_state["in_exp_housing"]=S.exp_housing; st.session_state["in_exp_food"]=S.exp_food
    st.session_state["in_exp_transport"]=S.exp_transport; st.session_state["in_exp_subs"]=S.exp_subs; st.session_state["in_exp_other"]=S.exp_other
    st.session_state["in_sav_emergency"]=S.sav_emergency; st.session_state["in_sav_invest"]=S.sav_invest; st.session_state["in_sav_other"]=S.sav_other

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


def _ticker_items() -> list[tuple[str, str, str]]:
    """Return (label, value_str, hex_colour) tuples derived from current session state.

    All values come from S.* (session state) + local finance functions — never
    hard-coded.  Called only on render_step0(); recomputed on every Streamlit
    rerun so values always reflect the selected profile.
    """
    TEAL   = "#2DB4A0"
    ORANGE = "#E8603C"
    GOLD   = "#D4A84B"

    items: list[tuple[str, str, str]] = []
    if S.income <= 0:
        return items

    # ── Cash flow ──
    cf = S.income - S.expenses - S.debt_payment - S.savings_contrib
    cf_col = TEAL if cf >= 0 else ORANGE
    cf_str = f"+${cf:,.0f}/mo" if cf >= 0 else f"-${abs(cf):,.0f}/mo"
    items.append(("Cash Flow", cf_str, cf_col))

    # ── Monthly savings contribution ──
    if S.savings_contrib > 0:
        items.append(("Savings", f"+${S.savings_contrib:,.0f}/mo", TEAL))

    # ── Savings rate ──
    sr = S.savings_contrib / S.income * 100
    sr_col = TEAL if sr >= 10 else (GOLD if sr >= 5 else ORANGE)
    items.append(("Savings Rate", f"{sr:.0f}%", sr_col))

    # ── Debt-to-income ──
    if S.income > 0:
        dti = S.debt_payment / S.income * 100
        dti_col = TEAL if dti <= 15 else (GOLD if dti <= 28 else ORANGE)
        items.append(("Debt-to-Income", f"{dti:.0f}%", dti_col))

    # ── Emergency fund coverage ──
    if S.expenses > 0:
        ef_mo = S.savings / S.expenses
        ef_col = TEAL if ef_mo >= 3 else (GOLD if ef_mo >= 1 else ORANGE)
        items.append(("Emergency Fund", f"{ef_mo:.1f} mo", ef_col))

    # ── EF target (3 × expenses) ──
    if S.expenses > 0:
        ef_target = S.expenses * 3
        items.append(("EF Target", f"${ef_target:,.0f}", GOLD))

    # ── Debt balance ──
    if S.debt_bal > 0:
        items.append(("Debt Balance", f"${S.debt_bal:,.0f} @ {S.debt_rate:.0f}%", ORANGE))

    # ── Debt payoff months ──
    if S.debt_bal > 0 and S.debt_payment > 0 and _LOCAL_MATH:
        try:
            sched = _debt_schedule(S.debt_bal, S.debt_payment, S.debt_rate / 100, 360)
            payoff = next((i + 1 for i, v in enumerate(sched) if v == 0), None)
            if payoff:
                po_col = TEAL if payoff <= 36 else (GOLD if payoff <= 60 else ORANGE)
                items.append(("Debt Payoff", f"{payoff} mo", po_col))
        except Exception:
            pass

    return items


def _ticker_html(items: list[tuple[str, str, str]]) -> str:
    """Render one pass of ticker items as HTML spans (caller duplicates for loop)."""
    parts = []
    for label, val, col in items:
        parts.append(
            f'<span class="tick-item">'
            f'<span class="tick-label">{label}</span>'
            f'<span class="tick-val" style="color:{col}">{val}</span>'
            f'</span>'
            f'<span class="tick-sep">&bull;</span>'
        )
    return "".join(parts)


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
        # ── Goals: show every goal in full — no truncation ───────────────────
        active_goals = [g for g in S.goals if g.get("target", 0) > 0 or g.get("name", "").strip()]
        if active_goals:
            st.markdown(
                '<p style="font-family:var(--mono);font-size:.56rem;letter-spacing:.1em;'
                'text-transform:uppercase;color:var(--dim);margin:.7rem 0 .3rem">Goals</p>',
                unsafe_allow_html=True,
            )
            for g in active_goals:
                name    = g.get("name", "") or "Unnamed goal"
                target  = g.get("target", 0)
                saved   = g.get("current_saved", 0)
                months  = g.get("months", 12)
                g_html  = (
                    f'<div style="padding:.3rem 0;border-bottom:1px solid var(--border)">'
                    f'<span style="font-family:var(--mono);font-size:.63rem;color:var(--text)">{name}</span>'
                    f'<span style="font-family:var(--mono);font-size:.6rem;color:var(--muted);margin-left:.5rem">'
                    f'— target ${target:,} in {months} mo, saved ${saved:,}</span></div>'
                )
                st.markdown(g_html, unsafe_allow_html=True)


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
# STEP 0 — LANDING
# ─────────────────────────────────────────────────────────────────────────────
def _gif_data_uri() -> str:
    """Return the dot_path.gif as a base64 data URI so it loads on Streamlit Cloud."""
    gif_path = ROOT / "assets" / "dot_path.gif"
    if gif_path.exists():
        b64 = base64.b64encode(gif_path.read_bytes()).decode()
        return f"data:image/gif;base64,{b64}"
    return ""

def render_step0() -> None:
    import streamlit.components.v1 as components

    # ── Reset block-container padding so the iframe fills width ──────────────
    st.markdown("""
<style>
/* Match outer Streamlit background to the landing iframe so any gap is invisible */
.stApp,[data-testid="stAppViewContainer"],[data-testid="stMain"]{
  background:#07090D!important;
}
.block-container{
  padding:0!important;
  max-width:100%!important;
  overflow:hidden!important;
}
/* Collapse all vertical gaps around the iframe */
[data-testid="stVerticalBlock"]{gap:0!important}
[data-testid="stVerticalBlock"] > div{padding:0!important;margin:0!important}
iframe{display:block!important;border:0!important;margin:0!important}
</style>
""", unsafe_allow_html=True)

    # ── Detect query-param navigation from the in-iframe CTA ─────────────────
    if st.query_params.get("go") == "1":
        st.query_params.clear()
        _go(1)
        return

    # ── Ticker: labels only, no numbers ──────────────────────────────────────
    _TICKER_LABELS = [
        ("SAVINGS",        "#2DB4A0"),
        ("DEBT",           "#E8603C"),
        ("EMERGENCY FUND", "#2DB4A0"),
        ("GOALS",          "#D4A84B"),
        ("CASH FLOW",      "#2DB4A0"),
        ("WHAT-IF",        "#D4A84B"),
    ]
    _one_pass = "".join(
        f'<span class="tick-item" style="color:{c}">{l}</span>'
        f'<span class="tick-sep">&bull;</span>'
        for l, c in _TICKER_LABELS
    )
    ticker_inner = _one_pass + _one_pass    # duplicate for seamless CSS loop

    # ── Entire landing page rendered as a self-contained components.html ─────
    # height is set large enough to show all content without a scrollbar.
    # The "Get Started" button inside posts a message to the parent; a tiny
    # hidden st.button below listens for the query-param trick via st.query_params.
    html_page = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
*{{box-sizing:border-box;margin:0;padding:0}}
:root{{
  --orange:#E8603C;--orange2:#C94E2C;
  --teal:#2DB4A0;
  --text:#ECE8E1;--muted:#A6ACB4;--dim:#6B737D;
  --serif:'Georgia',serif;
  --mono:'Courier New',monospace;
}}
html,body{{
  width:100%;height:100%;
  background:#07090D;
  color:var(--text);
  font-family:var(--sans,system-ui,sans-serif);
  overflow-x:hidden;
}}

/* ── Aurora layer ── */
.aurora{{
  position:fixed;inset:0;z-index:0;pointer-events:none;
  background:
    radial-gradient(ellipse 65% 50% at 15% 25%, rgba(232,96,60,.20) 0%, transparent 65%),
    radial-gradient(ellipse 50% 45% at 82% 65%, rgba(45,180,160,.14) 0%, transparent 60%),
    radial-gradient(ellipse 45% 55% at 50% 5%,  rgba(91,155,213,.10) 0%, transparent 55%),
    radial-gradient(ellipse 60% 40% at 90% 15%, rgba(212,168,75,.07) 0%, transparent 55%);
}}
/* Dark gradient overlay so text is always readable */
.overlay{{
  position:fixed;inset:0;z-index:1;pointer-events:none;
  background:linear-gradient(160deg,rgba(7,9,13,.30) 0%,rgba(7,9,13,.60) 60%,rgba(7,9,13,.82) 100%);
}}

/* ── Main content ── */
.wrap{{
  position:relative;z-index:10;
  width:100%;max-width:980px;margin:0 auto;
  padding:2.4rem 2.8rem 4rem;
  box-sizing:border-box;
  height:calc(100vh - 2rem);
  display:flex;flex-direction:column;
  justify-content:space-between;
}}

/* Title */
h1{{
  font:italic 400 3.4rem/.95 var(--serif);
  letter-spacing:-.03em;
  color:var(--text);
  margin-bottom:.9rem;
}}
h1 span{{color:var(--orange)}}

/* Tagline / typing */
.tagline-wrap{{
  font:italic 400 1.3rem/1.2 var(--serif);
  color:var(--orange);
  min-height:1.7rem;
  margin-bottom:.8rem;
}}
.cursor{{
  display:inline-block;width:2px;height:1.1em;
  background:var(--orange);vertical-align:text-bottom;
  margin-left:3px;
  animation:blink .7s step-end infinite;
}}
@keyframes blink{{0%,100%{{opacity:1}}50%{{opacity:0}}}}

/* Sub-line */
.sub{{
  font-family:var(--mono);font-size:.72rem;line-height:1.65;
  color:var(--muted);max-width:640px;
  margin-bottom:1.8rem;
}}

/* CTA button */
.cta{{
  display:inline-block;
  background:var(--orange);color:#fff;
  font-family:var(--mono);font-size:.82rem;font-weight:700;
  letter-spacing:.04em;
  padding:.65rem 2rem;
  border:none;border-radius:8px;
  cursor:pointer;
  transition:background .15s,transform .1s;
  margin-bottom:0;
  text-decoration:none;
}}
.cta:hover{{background:var(--orange2);transform:translateY(-1px)}}
.cta:active{{transform:translateY(0)}}

/* Cards */
.cards{{display:flex;gap:.8rem;flex-wrap:nowrap;margin-bottom:1.6rem}}
.card{{
  flex:1;min-width:0;
  padding:1rem 1.1rem;
  background:rgba(19,23,32,.78);
  border:1px solid rgba(255,255,255,.09);
  border-radius:12px;
  backdrop-filter:blur(8px);
  -webkit-backdrop-filter:blur(8px);
}}
.card-num{{
  font-family:var(--mono);font-size:.58rem;letter-spacing:.12em;
  text-transform:uppercase;color:var(--orange);margin-bottom:.4rem;
}}
.card-title{{
  font:italic 400 .95rem/1.25 var(--serif);
  color:var(--text);margin-bottom:.35rem;
}}
.card-body{{
  font-family:var(--mono);font-size:.6rem;line-height:1.6;color:var(--muted);
}}

/* How it works strip */
.how-strip{{
  display:flex;gap:0;margin-bottom:1.4rem;
  border:1px solid rgba(255,255,255,.07);
  border-radius:10px;overflow:hidden;
}}
.how-step{{
  flex:1;padding:.65rem .9rem;
  background:rgba(19,23,32,.60);
  display:flex;align-items:center;gap:.6rem;
}}
.how-step+.how-step{{border-left:1px solid rgba(255,255,255,.07);}}
.how-num{{
  font-family:var(--mono);font-size:.6rem;letter-spacing:.1em;
  color:var(--orange);flex-shrink:0;
}}
.how-text{{font-family:var(--mono);font-size:.62rem;color:var(--muted);line-height:1.4;}}

/* Hero question box */
.hero-q{{
  margin-bottom:1.2rem;
  padding:.8rem 1.1rem;
  background:rgba(45,180,160,.06);
  border:1px solid rgba(45,180,160,.18);
  border-left:3px solid var(--teal);
  border-radius:0 8px 8px 0;
  font:italic 400 .95rem/1.5 var(--serif);
  color:var(--text);
}}

/* Guardrails line */
.guardrails{{
  font-family:var(--mono);font-size:.56rem;
  color:var(--dim);letter-spacing:.04em;
  margin-top:0;
  margin-bottom:.5rem;
  line-height:1.6;
}}

/* ── Ticker tape ── */
.ticker-wrap{{
  position:fixed;bottom:0;left:0;right:0;
  z-index:50;
  background:rgba(7,9,13,.92);
  border-top:1px solid rgba(232,96,60,.20);
  overflow:hidden;
  height:2rem;
  display:flex;align-items:center;
}}
.ticker-track{{
  display:flex;
  white-space:nowrap;
  animation:ticker-scroll 38s linear infinite;
  will-change:transform;
}}
.ticker-track:hover{{animation-play-state:paused}}
@keyframes ticker-scroll{{
  0%{{transform:translateX(0)}}
  100%{{transform:translateX(-50%)}}
}}
.tick-item{{
  display:inline-flex;align-items:center;gap:.45rem;
  padding:0 1.6rem;
  font-family:'Courier New',monospace;font-size:.6rem;letter-spacing:.08em;
}}
.tick-label{{color:rgba(236,232,225,.55);text-transform:uppercase}}
.tick-val{{font-weight:700}}
.tick-sep{{color:rgba(255,255,255,.12);margin:0 .2rem}}
</style>
</head>
<body>
<div class="aurora"></div>
<div class="overlay"></div>

<div class="wrap">

  <!-- Top block: brand + hero copy + CTA -->
  <div>
    <p style="font-family:'Courier New',monospace;font-size:.55rem;letter-spacing:.14em;text-transform:uppercase;color:#6B737D;margin:0 0 1.6rem">IBM SkillsBuild &middot; Banking &amp; Financial Services</p>

    <!-- Title -->
    <h1>FinPath <span>AI</span></h1>

    <!-- Typing tagline -->
    <div class="tagline-wrap">
      <span id="typed"></span><span class="cursor" id="cursor"></span>
    </div>

    <!-- Sub-line -->
    <p class="sub">Ask a money question in plain English, get a clear answer with the numbers —
and see what changes if you try something different.</p>

    <!-- Get Started CTA -->
    <button class="cta" id="cta-btn" onclick="handleStart()">Get Started &rarr;</button>
  </div>

  <!-- Bottom block: cards + new sections anchored to bottom -->
  <div style="padding-bottom:1.6rem">
    <!-- 3 cards -->
    <div class="cards">
      <div class="card">
        <div class="card-num">01</div>
        <div class="card-title">Ask a money question</div>
        <div class="card-body">Type anything in plain English — &ldquo;Can I save $200 more?&rdquo; or &ldquo;How long to pay off my debt?&rdquo;</div>
      </div>
      <div class="card">
        <div class="card-num">02</div>
        <div class="card-title">See the numbers</div>
        <div class="card-body">Every answer is backed by a verified calculation &mdash; debt schedule, savings projection, health score.</div>
      </div>
      <div class="card">
        <div class="card-num">03</div>
        <div class="card-title">Try a what-if</div>
        <div class="card-body">Slide income or extra payments and watch your projections update in real time.</div>
      </div>
    </div>

    <!-- How it works strip -->
    <div class="how-strip">
      <div class="how-step">
        <span class="how-num">1&nbsp;&mdash;</span>
        <span class="how-text">Pick a profile</span>
      </div>
      <div class="how-step">
        <span class="how-num">2&nbsp;&mdash;</span>
        <span class="how-text">Ask a question</span>
      </div>
      <div class="how-step">
        <span class="how-num">3&nbsp;&mdash;</span>
        <span class="how-text">See the numbers &amp; try a what-if</span>
      </div>
    </div>

    <!-- Hero question example -->
    <div class="hero-q">
      &ldquo;Can I invest $300 more a month and still keep three months of emergency cash?&rdquo;
    </div>

    <!-- Guardrails -->
    <div class="guardrails">
      No real money &middot; no real accounts &middot; no product recommendations &middot; Synthetic profiles only &middot; Educational tool &mdash; not financial advice.
    </div>
  </div>

</div>

<!-- Ticker tape — values injected server-side from session state -->
<div class="ticker-wrap" aria-hidden="true">
  <div class="ticker-track" id="ticker">
    {ticker_inner}
  </div>
</div>

<script>
// ── Typing animation ──────────────────────────────────────────────────────
(function(){{
  var TEXT = "Every dollar has a path. Find yours.";
  var HOLD=1800, T=62, D=36;
  var el = document.getElementById('typed');
  var i=0, del=false;
  function tick(){{
    if(!del){{
      el.textContent = TEXT.slice(0,++i);
      if(i===TEXT.length){{del=true;setTimeout(tick,HOLD);return;}}
    }}else{{
      el.textContent = TEXT.slice(0,--i);
      if(i===0){{del=false;setTimeout(tick,500);return;}}
    }}
    setTimeout(tick, del?D:T);
  }}
  tick();
}})();

// ── CTA: set query param on parent so Streamlit navigates to step 1 ───────
function handleStart(){{
  try{{
    var url = new URL(window.parent.location.href);
    url.searchParams.set('go','1');
    window.parent.history.replaceState(null,'',url.toString());
    // Trigger a Streamlit rerun by dispatching a storage event (Streamlit polls)
    window.parent.dispatchEvent(new Event('popstate'));
  }}catch(e){{}}
  // Fallback: scroll down so the user sees the Streamlit button (should not be needed)
  try{{ window.parent.scrollTo({{top:99999,behavior:'smooth'}}); }}catch(e){{}}
}}
</script>
</body>
</html>"""

    # Render the full landing page — sized to fill the viewport without scrolling
    components.html(html_page, height=820, scrolling=False)


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
        uploaded = st.file_uploader(
            "⬆ Upload a saved FinPath AI profile (JSON)",
            type="json", key="profile_upload",
            label_visibility="visible",
            help="Upload a profile you previously saved from FinPath AI — a small JSON file, usually a few KB.",
        )
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
            width="stretch",
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
                st.button(name, key=f"chip_{p['id']}", width="stretch", on_click=_load_profile, args=(p,))
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
            S.inc_salary = st.number_input("Salary / wages ($)", min_value=0, step=100, value=int(S.inc_salary), key="in_inc_salary",
                help="Your regular take-home pay from employment. Enter the net (after-tax) monthly amount.")
        with ib:
            S.inc_side = st.number_input("Side income ($)", min_value=0, step=50, value=int(S.inc_side), key="in_inc_side",
                help="Freelance, gig work, consulting, or any irregular income. Leave at 0 if none.")
        with ic:
            S.inc_other = st.number_input("Other income ($)", min_value=0, step=50, value=int(S.inc_other), key="in_inc_other",
                help="Rental income, dividends, benefits, or any other monthly income not covered above.")
        S.income = int(S.inc_salary + S.inc_side + S.inc_other)
        # keep legacy widget key in sync
        st.session_state["in_income"] = S.income
        st.caption(f"Total monthly income: ${S.income:,}")

    # ── Expense breakdown ─────────────────────────────────────────────────────
    with st.expander(f"💸 Expenses  —  total ${S.expenses:,}/mo", expanded=True):
        ea, eb = st.columns(2, gap="small")
        with ea:
            S.exp_housing   = st.number_input("Housing / rent ($)",   min_value=0, step=50, value=int(S.exp_housing),   key="in_exp_housing",
                help="Rent or mortgage payment, plus any regular housing fees (e.g. HOA, insurance included in payment).")
            S.exp_food      = st.number_input("Food & groceries ($)", min_value=0, step=50, value=int(S.exp_food),      key="in_exp_food",
                help="Groceries, dining out, coffee, and any other food spending per month.")
            S.exp_transport = st.number_input("Transport ($)",        min_value=0, step=50, value=int(S.exp_transport), key="in_exp_transport",
                help="Car payment, fuel, insurance, public transit passes, or ride-shares — total monthly transport spend.")
        with eb:
            S.exp_subs  = st.number_input("Subscriptions ($)", min_value=0, step=10, value=int(S.exp_subs),  key="in_exp_subs",
                help="Streaming, gym, software, and any recurring monthly subscriptions.")
            S.exp_other = st.number_input("Other expenses ($)", min_value=0, step=50, value=int(S.exp_other), key="in_exp_other",
                help="Everything else — clothing, healthcare out-of-pocket, entertainment, miscellaneous. If unsure, use a rough estimate.")
        S.expenses = int(S.exp_housing + S.exp_food + S.exp_transport + S.exp_subs + S.exp_other)
        st.session_state["in_expenses"] = S.expenses
        st.caption(f"Total monthly expenses: ${S.expenses:,}")

    # ── Savings breakdown ─────────────────────────────────────────────────────
    with st.expander(f"🏦 Savings  —  total ${S.savings:,}", expanded=False):
        sa, sb, sc = st.columns(3, gap="small")
        with sa:
            S.sav_emergency = st.number_input("Emergency fund ($)", min_value=0, step=500, value=int(S.sav_emergency), key="in_sav_emergency",
                help="Cash in a savings account you could access immediately in an emergency — typically 3–6 months of expenses.")
        with sb:
            S.sav_invest = st.number_input("Investments ($)", min_value=0, step=500, value=int(S.sav_invest), key="in_sav_invest",
                help="Brokerage accounts, 401(k)/IRA balances, stocks, or any investment account value.")
        with sc:
            S.sav_other = st.number_input("Other savings ($)", min_value=0, step=100, value=int(S.sav_other), key="in_sav_other",
                help="Any other savings not counted above — e.g. a house deposit fund, education fund, or unallocated cash.")
        S.savings = int(S.sav_emergency + S.sav_invest + S.sav_other)
        st.session_state["in_savings"] = S.savings
        st.caption(f"Total savings: ${S.savings:,}")

    # ── Savings contribution & debt ───────────────────────────────────────────
    lc2, rc2 = st.columns([1,1], gap="large")
    with lc2:
        _section_label("Savings contribution", mt=".8rem")
        S.savings_contrib = st.number_input("Currently saving per month ($)", min_value=0, step=50, value=int(S.savings_contrib), key="in_savings_contrib",
            help="How much you actively transfer into savings or investments each month — not counting debt payments.")
    with rc2:
        _section_label("Goal context", mt=".8rem")
        S.goal = st.text_area("Goal summary (optional)", value=S.goal, placeholder="e.g. Pay off debt in 3 years", key="in_goal", height=68,
            help="A brief description of your top financial goal. The structured goal rows below are used for the calculations; this is for extra context.")

    lc3, rc3 = st.columns([1,1], gap="large")
    with lc3:
        _section_label("Debt", mt=".8rem")
        S.debt_bal    = st.number_input("Total debt balance ($)",    min_value=0, step=1000, value=int(S.debt_bal),     key="in_debt_bal",
            help="Total outstanding debt across all loans and credit cards — the amount you still owe today.")
        S.debt_payment= st.number_input("Monthly debt payment ($)", min_value=0, step=50,   value=int(S.debt_payment),  key="in_debt_payment",
            help="The total you pay toward debt each month (minimum payments across all accounts combined).")
    with rc3:
        _section_label("Debt rate", mt=".8rem")
        S.debt_rate = st.number_input("Interest rate (% p.a.)", min_value=0.0, max_value=50.0, step=0.5, value=float(S.debt_rate), key="in_debt_rate", format="%.1f",
            help="The blended annual interest rate across your debts. If you have multiple debts at different rates, use a rough average.")

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
        edited = st.data_editor(df, num_rows="dynamic", width="stretch", key="debt_table",
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
        st.button("Next →", key="step1_next", width="stretch", type="primary",
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
    # ── Hero question chip ────────────────────────────────────────────────────
    _HERO_QUESTION = "Can I invest $300 more a month and still keep three months of emergency cash?"
    st.markdown(
        '<p style="font-family:var(--mono);font-size:.58rem;letter-spacing:.1em;'
        'text-transform:uppercase;color:var(--dim);margin:0 0 .4rem">Try this</p>',
        unsafe_allow_html=True,
    )
    st.markdown('<div class="sug-btn">', unsafe_allow_html=True)
    st.button(
        f'💡 {_HERO_QUESTION}',
        key="hero_chip",
        width="stretch",
        on_click=_set_question,
        args=(_HERO_QUESTION,),
    )
    st.markdown('</div>', unsafe_allow_html=True)

    _section_label("Quick suggestions", mt=".9rem")
    c1, c2 = st.columns(2, gap="small")
    for i, s in enumerate(SUGGESTIONS):
        col = c1 if i%2==0 else c2
        with col:
            st.markdown('<div class="sug-btn">', unsafe_allow_html=True)
            st.button(s, key=f"sug_{i}", width="stretch", on_click=_set_question, args=(s,))
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
        if st.button("← Edit profile", key="step2_back", width="stretch"): _go(1)
    with gc:
        if st.button("Ask FinPath →", key="step2_run", width="stretch", type="primary", disabled=not S.question.strip()):
            S.messages=[]; S.thread_id=None; S.pending_send=None; S.error=None; S.initial_sent=False; _go(3)
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
            S.thread_id    = res["thread_id"]
            verified       = res.get("verified", None)
            S.agent_offline = False
            S.messages.append({"role":"assistant","content":res["reply"],
                                "tools":res["tools"],"verified":verified})
        except (RuntimeError, TimeoutError):
            S.agent_offline = True
            S.last_failed   = user_text
            if S.messages and S.messages[-1]["role"]=="user": S.messages.pop()
        except Exception:
            S.agent_offline = True
            S.last_failed   = user_text
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
        ).properties(title=alt.TitleParams("Debt balance — 36 months", color="#A6ACB4", fontSize=11), height=180)
        .configure_view(strokeOpacity=0, fill="#131720").configure(background="#0B0D10"))

        ch_sav = (alt.Chart(df_sav).mark_line(point=False).encode(
            x=alt.X("Month:Q", axis=alt.Axis(labelColor="#A6ACB4", gridColor="rgba(255,255,255,.05)", domainColor="rgba(0,0,0,0)", tickColor="rgba(0,0,0,0)")),
            y=alt.Y("Savings ($):Q", axis=alt.Axis(labelColor="#A6ACB4", gridColor="rgba(255,255,255,.05)", domainColor="rgba(0,0,0,0)", tickColor="rgba(0,0,0,0)", format="$,.0f")),
            color=alt.Color("Scenario:N", scale=alt.Scale(range=["#A6ACB4","#5B9BD5"]), legend=alt.Legend(labelColor="#ECE8E1", titleColor="#ECE8E1")),
            tooltip=["Month:Q","Savings ($):Q","Scenario:N"],
        ).properties(title=alt.TitleParams("Savings over 36 months", color="#A6ACB4", fontSize=11), height=180)
        .configure_view(strokeOpacity=0, fill="#131720").configure(background="#0B0D10"))

        col_d, col_s = st.columns(2)
        with col_d: st.altair_chart(ch_debt, width="stretch")
        with col_s: st.altair_chart(ch_sav,  width="stretch")


def _rule_suggestions() -> list[str]:
    """Return 2–3 short, deterministic suggestions derived from the user's numbers only.

    Rules are applied in priority order; at most 3 are returned.
    No product names, no named financial products — numbers and ratios only.
    """
    tips: list[str] = []

    cf   = S.income - S.expenses - S.debt_payment - S.savings_contrib
    sr   = S.savings_contrib / S.income if S.income > 0 else 0.0
    dti  = S.debt_payment / S.income if S.income > 0 else 0.0
    ef   = S.savings / S.expenses if S.expenses > 0 else 0.0

    # 1. Negative cash flow — most urgent
    if cf < 0:
        tips.append(
            f"Your outflows exceed your income by ${abs(cf):,.0f}/mo. "
            "Closing this gap — by trimming expenses or boosting income — is the first priority before any other move."
        )

    # 2. Emergency fund below 3 months
    if ef < 3 and len(tips) < 3:
        ef_target = S.expenses * 3
        ef_gap    = max(0, ef_target - S.savings)
        tips.append(
            f"Your emergency fund covers {ef:.1f} month(s) of expenses; the 3-month guideline is ${ef_target:,.0f}. "
            f"You need ${ef_gap:,.0f} more to reach it."
        )

    # 3. Savings rate below 10 %
    if sr < 0.10 and cf > 0 and len(tips) < 3:
        gap_to_10pct = round(S.income * 0.10 - S.savings_contrib)
        tips.append(
            f"Your savings rate is {sr*100:.0f}% (${S.savings_contrib:,}/mo). "
            f"Raising it to 10% would add ${gap_to_10pct:,}/mo to savings — still leaving ${cf - gap_to_10pct:,.0f}/mo of surplus."
        )

    # 4. Debt-to-income above 28 %
    if dti > 0.28 and len(tips) < 3:
        tips.append(
            f"Your debt payment is {dti*100:.0f}% of income. "
            "The common guideline is 28% or below; reducing this ratio frees up cash flow for other goals."
        )

    # 5. Positive cash flow but no extra debt payment modelled — nudge
    if cf > 0 and S.debt_bal > 0 and len(tips) < 3 and dti <= 0.28:
        tips.append(
            f"You have ${cf:,.0f}/mo of surplus. Even a small extra payment toward your "
            f"${S.debt_bal:,.0f} balance reduces total interest paid over time."
        )

    return tips[:3]


def _download_summary() -> str:
    """Build a markdown download of the full conversation with health score and what-if."""
    lines = ["# FinPath AI — Session Report\n"]
    lines.append(f"**Date:** {date.today().isoformat()}\n")

    # ── Profile summary ──────────────────────────────────────────────────────
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

    # ── Goals ────────────────────────────────────────────────────────────────
    active_goals = [g for g in S.goals if g.get("target", 0) > 0]
    if active_goals:
        lines.append("### Goals\n")
        for g in active_goals:
            lines.append(
                f"- {g.get('name', 'Goal')}: target ${g.get('target', 0):,} "
                f"in {g.get('months', 12)} months, saved ${g.get('current_saved', 0):,}"
            )
        lines.append("")

    # ── Financial health score ───────────────────────────────────────────────
    if _LOCAL_MATH and S.income > 0 and S.expenses > 0:
        try:
            h = _fhc(
                income=S.income, expenses=S.expenses,
                monthly_savings_contribution=S.savings_contrib,
                current_savings=S.savings, debt_balance=S.debt_bal,
                annual_debt_rate=S.debt_rate / 100,
                monthly_debt_payment=S.debt_payment,
            )
            score = h["score"]
            label = "Strong" if score >= 75 else ("Moderate" if score >= 50 else ("Needs attention" if score >= 25 else "Critical"))
            lines.append("## Financial Health Score\n")
            lines += [
                f"- **Overall:** {score}/100 — {label}",
                f"- Cash-flow sub-score: {h['cash_flow_score']}/25",
                f"- Emergency-fund sub-score: {h['emergency_fund_score']}/25",
                f"- Debt-burden sub-score: {h['debt_burden_score']}/25",
                f"- Savings-rate sub-score: {h['savings_rate_score']}/25",
                f"- Monthly surplus: ${h['cash_flow']:+,.0f}",
                f"- Emergency fund coverage: {h['emergency_fund_months']:.1f} months",
                f"- Debt-to-income ratio: {h['debt_to_income_ratio']*100:.0f}%",
                f"- Savings rate: {h['savings_rate']*100:.0f}%",
                "",
            ]
            if h.get("priorities"):
                lines.append("### Priorities (from health check)\n")
                for p in h["priorities"]:
                    lines.append(f"- {p}")
                lines.append("")
        except Exception:
            pass

    # ── What-if tried ────────────────────────────────────────────────────────
    if S.wi_extra_pmt != 0 or S.wi_income_chg != 0:
        lines.append("## What-If Scenario Explored\n")
        if S.wi_extra_pmt:
            lines.append(f"- Extra debt payment modelled: +${S.wi_extra_pmt:,}/mo")
        if S.wi_income_chg:
            lines.append(f"- Income change modelled: {S.wi_income_chg:+.0f}%")
        lines.append("")

    # ── Question and agent answer ────────────────────────────────────────────
    lines.append("## Conversation\n")
    for msg in S.messages:
        role = "**You**" if msg["role"] == "user" else "**FinPath AI**"
        tools_str = f"\n*Tools used: {', '.join(msg['tools'])}*" if msg.get("tools") else ""
        verified = msg.get("verified")
        verified_str = ""
        if verified is True:
            verified_str = "\n*✓ Figures verified against calculations*"
        elif verified is False:
            verified_str = "\n*⚠ Some figures could not be verified*"
        lines.append(f"{role}: {msg['content']}{tools_str}{verified_str}\n")

    # ── Rule-based suggestions ───────────────────────────────────────────────
    suggestions = _rule_suggestions()
    if suggestions:
        lines.append("## Suggestions (rule-based, illustrative)\n")
        for tip in suggestions:
            lines.append(f"- {tip}")
        lines.append("")

    lines.append(
        "---\n"
        "*Educational tool — not financial advice. "
        "All projections are illustrative only.*"
    )
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

    if not S.initial_sent and S.question:
        S.initial_sent = True
        _send_message(S.question)

    _run_agent()

    if S.agent_offline:
        st.markdown(
            '<div style="padding:.75rem 1rem 1rem;background:rgba(212,168,75,.08);'
            'border:1px solid rgba(212,168,75,.30);border-radius:var(--radius);'
            'margin-bottom:1.1rem">'
            '<p style="font-family:var(--mono);font-size:.62rem;letter-spacing:.1em;'
            'text-transform:uppercase;color:#D4A84B;margin:0 0 .35rem">Demo mode · agent offline</p>'
            '<p style="font-family:var(--mono);font-size:.72rem;color:var(--muted);margin:0;line-height:1.5">'
            'The watsonx Orchestrate agent could not be reached. '
            'Your financial health card and what-if projections below are computed locally '
            'and are fully accurate — only the AI chat responses are unavailable.</p>'
            '</div>',
            unsafe_allow_html=True,
        )
        # Show local tools in demo mode: health card + what-if explorer
        _health_card()
        # What-if is rendered further down once there are messages; avoid a duplicate-key crash
        if _LOCAL_MATH and not S.messages:
            _whatiif_section()
        col_retry, _ = st.columns([1, 2])
        with col_retry:
            if st.button("↺ Retry connection", key="err_retry"):
                if S.last_failed:
                    S.agent_offline = False; _send_message(S.last_failed); S.last_failed = None; st.rerun()

    # Sidebar history
    with st.sidebar:
        st.markdown('<p style="font-family:var(--mono);font-size:.6rem;letter-spacing:.1em;text-transform:uppercase;color:var(--dim)">This conversation</p>', unsafe_allow_html=True)
        user_msgs = [m for m in S.messages if m["role"]=="user"]
        if user_msgs:
            for i, m in enumerate(user_msgs):
                st.markdown(f'<div style="font-family:var(--mono);font-size:.65rem;color:var(--muted);padding:.25rem 0;border-bottom:1px solid var(--border)">{i+1}. {m["content"][:60]}{"…" if len(m["content"])>60 else ""}</div>', unsafe_allow_html=True)
        else:
            st.markdown('<p style="font-family:var(--mono);font-size:.62rem;color:var(--dim)">No questions yet</p>', unsafe_allow_html=True)

    # ── Hero takeaway: first plain-English answer sentence ───────────────────
    first_reply = next((m for m in S.messages if m["role"] == "assistant"), None)
    if first_reply:
        _HEADER_WORDS = {
            "assumptions", "analysis", "result", "summary", "profile",
            "input", "breakdown", "overview", "note", "disclaimer",
            "educational", "advice", "tool", "output", "parameters",
        }
        # Data-label pattern: 'Some Label: $value' or 'Key: 7%' — not a sentence
        _DATA_LABEL_RE = re.compile(r"^[A-Za-z][A-Za-z ,/()\-%]*:\s*[\$\d]")
        # A real sentence contains at least one verb/predicate word
        _SENTENCE_RE = re.compile(
            r"\b(will|is|are|was|were|has|have|had|can|could|would|should|"
            r"covers|paid|takes|gives|shows|means|puts|needs)\b", re.I
        )
        _takeaway = ""
        for _raw in first_reply["content"].splitlines():
            _l = _raw.strip()
            if not _l:
                continue
            # Skip markdown headings (# / ## / ###)
            if _l.startswith("#"):
                continue
            # Strip all markdown bold/italic markers to get plain text
            _plain = re.sub(r"\*{1,3}", "", _l).strip()
            if not _plain:
                continue
            # Skip lines that consist solely of section-label words
            # e.g. "Debt Payoff Analysis", "Assumptions used", "Result"
            _lower = _plain.lower()
            _words = set(re.sub(r"[^a-z ]", " ", _lower).split())
            if _words and _words.issubset(
                _HEADER_WORDS | {"used", "and", "the", "a", "of", "for", "with", "in", "is", "are"}
            ):
                continue
            # Skip very short fragments (< 20 chars) — likely a label, not a sentence
            if len(_plain) < 20:
                continue
            # Skip data-label lines like "Monthly income: $5,000" or "Debt rate: 7%"
            if _DATA_LABEL_RE.match(_plain):
                continue
            # Must look like a real sentence — contains a verb or predicate word
            if not _SENTENCE_RE.search(_plain):
                continue
            _takeaway = _plain
            break

        if _takeaway:
            st.markdown(
                f'<div style="margin:0 0 1.2rem;padding:.85rem 1.1rem;'
                f'background:rgba(78,168,107,.07);border:1px solid rgba(78,168,107,.22);'
                f'border-left:3px solid var(--green);border-radius:0 var(--radius) var(--radius) 0">'
                f'<p style="font-family:var(--mono);font-size:.56rem;letter-spacing:.1em;'
                f'text-transform:uppercase;color:var(--green);margin:0 0 .3rem;opacity:.8">FinPath AI says</p>'
                f'<p style="font:italic 400 1.05rem/1.5 var(--serif);color:var(--text);margin:0">'
                f'{_takeaway}</p></div>',
                unsafe_allow_html=True,
            )

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

    # Follow-up chips — use full question text so nothing is truncated
    if S.messages and S.messages[-1]["role"]=="assistant" and not S.pending_send:
        _section_label("Follow-up suggestions", mt=".8rem")
        fc = st.columns(len(FOLLOWUP_SUGGESTIONS), gap="small")
        for col, (label, question) in zip(fc, FOLLOWUP_SUGGESTIONS):
            with col:
                st.markdown('<div class="sug-btn">', unsafe_allow_html=True)
                st.button(question, key=f"fu_{label[:18]}", width="stretch", on_click=_send_message, args=(question,))
                st.markdown('</div>', unsafe_allow_html=True)

    # Rule-based suggestions
    if S.messages and S.messages[-1]["role"] == "assistant" and not S.pending_send:
        suggestions = _rule_suggestions()
        if suggestions:
            _section_label("Suggestions based on your numbers", mt="1rem")
            for tip in suggestions:
                st.markdown(
                    f'<div style="display:flex;align-items:flex-start;gap:.6rem;padding:.55rem .8rem;'
                    f'margin-bottom:.4rem;background:var(--surface);border:1px solid var(--border);'
                    f'border-left:3px solid var(--gold);border-radius:0 var(--radius-sm) var(--radius-sm) 0">'
                    f'<span style="color:var(--gold);font-size:.8rem;flex-shrink:0;margin-top:.05rem">›</span>'
                    f'<span style="font-family:var(--mono);font-size:.65rem;color:var(--muted);line-height:1.5">'
                    f'{tip}</span></div>',
                    unsafe_allow_html=True,
                )
            st.markdown(
                '<p style="font-family:var(--mono);font-size:.58rem;color:var(--dim);'
                'margin:.2rem 0 .8rem">Rule-based · illustrative only · Educational tool — not financial advice</p>',
                unsafe_allow_html=True,
            )

    # Chat input
    inp = st.chat_input("Ask a follow-up…")
    if inp and inp.strip(): _send_message(inp.strip()); st.rerun()

    # What-if sliders + charts
    if S.messages and _LOCAL_MATH:
        _whatiif_section()

    # Assumptions expander (includes full goals list)
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
        if st.button("New conversation", key="res_new", width="stretch"):
            S.messages=[]; S.thread_id=None; S.question=""; S.error=None; S.pending_send=None; S.initial_sent=False
            st.session_state.pop("in_question", None); _go(2)

    # Download button
    if S.messages:
        summary_md = _download_summary()
        st.download_button(
            label="⬇ Download summary",
            data=summary_md.encode(),
            file_name=f"finpath_summary_{date.today().isoformat()}.md",
            mime="text/markdown",
            width="stretch",
        )

    _disclaimer()


# ─────────────────────────────────────────────────────────────────────────────
# ROUTER
# ─────────────────────────────────────────────────────────────────────────────
if   S.step == 0: render_step0()
elif S.step == 1: render_step1()
elif S.step == 2: render_step2()
elif S.step == 3: render_step3()
