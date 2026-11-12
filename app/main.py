"""
app/main.py
-----------
FinPath AI — Streamlit frontend (3-step wizard + chat).

Steps:
  1  Profile   — pick a sample profile or enter manually; live health card
  2  Question  — suggestion chips + free-form textarea
  3  Results   — multi-turn chat with tool-trace chips per reply

Start with:
    streamlit run app/main.py
"""

from __future__ import annotations

import json
import logging
import sys
from pathlib import Path

import streamlit as st

# ── Local import for inline health card (no agent call needed) ────────────────
try:
    _tools_path = str(Path(__file__).parent.parent)
    if _tools_path not in sys.path:
        sys.path.insert(0, _tools_path)
    from tools.core.finance import financial_health_check as _fhc
    _HEALTH_AVAILABLE = True
except Exception:
    _HEALTH_AVAILABLE = False

# ── sys.path for api_client ───────────────────────────────────────────────────
ROOT    = Path(__file__).parent.parent
APP_DIR = Path(__file__).parent
for _p in (str(ROOT), str(APP_DIR)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from api_client import ask_agent  # noqa: E402

_log = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# PAGE CONFIG  (must be first Streamlit call)
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

/* ── design tokens ── */
:root{
  --bg:       #0B0D10;
  --surface:  #131720;
  --surface2: #1A1F28;
  --surface3: #1E2430;
  --border:   rgba(255,255,255,.07);
  --border2:  rgba(255,255,255,.12);
  --text:     #ECE8E1;
  --muted:    #A6ACB4;
  --dim:      #6B737D;
  --orange:   #E8603C;
  --orange2:  #C94E2C;
  --orangeA:  rgba(232,96,60,.12);
  --orangeB:  rgba(232,96,60,.24);
  --gold:     #D4A84B;
  --green:    #4EA86B;
  --greenA:   rgba(78,168,107,.12);
  --red:      #D95F5F;
  --blue:     #5B9BD5;

  --serif: 'Fraunces', Georgia, serif;
  --sans:  'Inter', -apple-system, system-ui, sans-serif;
  --mono:  'JetBrains Mono', 'Courier New', monospace;

  --radius: 8px;
  --radius-sm: 4px;
}

/* ── reset / base ── */
html, body, [class*="css"]{
  font-family: var(--sans) !important;
  -webkit-font-smoothing: antialiased;
}
.stApp{ background: var(--bg) !important; color: var(--text) !important; }
header[data-testid="stHeader"], footer, #MainMenu{ display:none !important; }

.block-container{
  max-width: 860px !important;
  padding: 2.2rem 1.4rem 4rem !important;
}

/* ── scrollbar ── */
::-webkit-scrollbar{ width:5px; height:5px; }
::-webkit-scrollbar-track{ background:transparent; }
::-webkit-scrollbar-thumb{ background:rgba(255,255,255,.12); border-radius:3px; }

/* ── typography helpers ── */
.label-micro{
  font-family: var(--mono) !important;
  font-size: .58rem !important;
  letter-spacing: .1em !important;
  text-transform: uppercase !important;
  color: var(--dim) !important;
}

/* ── ALL inputs: dark surface ── */
[data-baseweb="base-input"],
[data-baseweb="input"],
[data-baseweb="textarea"]{
  background: var(--surface2) !important;
  border-color: var(--border) !important;
  border-radius: var(--radius-sm) !important;
}
[data-baseweb="base-input"] input,
[data-baseweb="input"] input,
[data-baseweb="textarea"] textarea, textarea{
  background: var(--surface2) !important;
  color: var(--text) !important;
  font-family: var(--mono) !important;
  font-size: .82rem !important;
  caret-color: var(--orange) !important;
}
[data-baseweb="base-input"]:focus-within,
[data-baseweb="input"]:focus-within,
[data-baseweb="textarea"]:focus-within{
  border-color: rgba(232,96,60,.45) !important;
  box-shadow: 0 0 0 2px rgba(232,96,60,.12) !important;
}
input::placeholder, textarea::placeholder{
  color: var(--dim) !important;
  opacity: 1 !important;
}
/* stepper buttons on number inputs */
[data-baseweb="base-input"] button{
  background: var(--surface2) !important;
  color: var(--muted) !important;
  border-color: var(--border) !important;
}

/* ── labels ── */
label, .stNumberInput label, .stTextInput label,
.stTextArea label, .stSelectbox label{
  font-family: var(--mono) !important;
  font-size: .62rem !important;
  letter-spacing: .07em !important;
  text-transform: uppercase !important;
  color: var(--muted) !important;
  margin-bottom: .2rem !important;
}

/* ── buttons ── */
.stButton button{
  background: var(--surface2) !important;
  border: 1px solid var(--border2) !important;
  color: var(--text) !important;
  font-family: var(--mono) !important;
  font-size: .66rem !important;
  letter-spacing: .07em !important;
  text-transform: uppercase !important;
  border-radius: var(--radius-sm) !important;
  padding: .5rem 1.1rem !important;
  transition: all .15s !important;
}
.stButton button:hover{
  background: var(--surface3) !important;
  border-color: rgba(255,255,255,.22) !important;
}

/* primary — orange fill */
.stButton button[kind="primary"]{
  background: var(--orange) !important;
  border-color: var(--orange) !important;
  color: #fff !important;
  font-weight: 600 !important;
}
.stButton button[kind="primary"]:hover{
  background: var(--orange2) !important;
  border-color: var(--orange2) !important;
}
.stButton button[kind="primary"]:disabled{
  background: rgba(232,96,60,.28) !important;
  border-color: transparent !important;
  color: rgba(255,255,255,.35) !important;
  cursor: not-allowed !important;
}

/* tertiary — ghost / link */
.stButton button[kind="tertiary"]{
  background: transparent !important;
  border-color: transparent !important;
  color: var(--dim) !important;
  font-size: .62rem !important;
  padding: .2rem .5rem !important;
}
.stButton button[kind="tertiary"]:hover{ color: var(--muted) !important; }

/* selected profile chip */
.profile-selected .stButton button{
  border-color: var(--orange) !important;
  background: var(--orangeA) !important;
  color: var(--orange) !important;
}

/* suggestion chips */
.sug-btn .stButton button{
  background: var(--surface2) !important;
  border: 1px solid var(--border) !important;
  color: var(--muted) !important;
  font-size: .65rem !important;
  padding: .55rem .9rem !important;
  text-align: left !important;
  white-space: normal !important;
  height: auto !important;
  line-height: 1.45 !important;
  border-radius: var(--radius-sm) !important;
}
.sug-btn .stButton button:hover{
  border-color: var(--orangeB) !important;
  color: var(--text) !important;
  background: rgba(232,96,60,.05) !important;
}

/* ── expander ── */
.streamlit-expanderHeader{
  font-family: var(--mono) !important;
  font-size: .62rem !important;
  letter-spacing: .07em !important;
  text-transform: uppercase !important;
  color: var(--muted) !important;
  background: var(--surface) !important;
  border-radius: var(--radius-sm) !important;
}
[data-testid="stExpanderDetails"]{
  background: var(--surface) !important;
  border: 1px solid var(--border) !important;
  border-top: none !important;
  border-radius: 0 0 var(--radius-sm) var(--radius-sm) !important;
}

/* ── chat messages ── */
[data-testid="stChatMessage"]{
  background: var(--surface) !important;
  border: 1px solid var(--border) !important;
  border-radius: var(--radius) !important;
  padding: 1rem 1.1rem !important;
  margin-bottom: .7rem !important;
}
[data-testid="stChatMessage"] p{ font-size: .92rem !important; line-height: 1.7 !important; }

/* chat input */
[data-testid="stChatInput"] textarea{
  background: var(--surface2) !important;
  border-color: var(--border2) !important;
  color: var(--text) !important;
  font-size: .88rem !important;
}

/* ── divider ── */
hr{ border-color: var(--border) !important; margin: 1.5rem 0 !important; }

/* ── altair / vega ── */
.vega-embed{ background: transparent !important; }
.vega-embed .marks path{ stroke-opacity: .9 !important; }

/* ── st.caption override ── */
.stCaption{
  font-family: var(--mono) !important;
  font-size: .62rem !important;
  color: var(--dim) !important;
  margin-top: -.15rem !important;
}
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

# ─────────────────────────────────────────────────────────────────────────────
# SESSION STATE
# ─────────────────────────────────────────────────────────────────────────────
def _init_state() -> None:
    defaults: dict = {
        "step":            1,
        "profile":         None,
        "income":          5000,
        "expenses":        3000,
        "savings":         6000,
        "savings_contrib": 200,
        "debt_bal":        10000,
        "debt_payment":    300,
        "debt_rate":       6.0,
        "goal":            "",
        "question":        "",
        "messages":        [],
        "thread_id":       None,
        "pending_send":    None,
        "error":           None,
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
    "in_income", "in_expenses", "in_savings", "in_savings_contrib",
    "in_debt_bal", "in_debt_payment", "in_debt_rate", "in_goal",
]

def _reset_input_widgets() -> None:
    for k in _INPUT_KEYS:
        st.session_state.pop(k, None)

def _load_profile(p: dict) -> None:
    # Write both the session-state aliases AND the widget keys directly.
    # Writing the widget key is what actually updates the displayed value —
    # Streamlit ignores value= on reruns if the key already exists in state.
    income   = int(p["monthly_income"])
    expenses = int(p["monthly_expenses"])
    savings  = int(p["cash_savings"])
    contrib  = int(p.get("monthly_savings_contribution", 0))
    debt_bal = int(p["debt_balance"])
    debt_pmt = int(p.get("monthly_debt_payment", 0))
    rate     = float(p["debt_rate"] * 100)
    goal     = p["savings_goal"]

    # Session-state aliases (used by _build_profile_dict and health card)
    S.profile         = p
    S.income          = income
    S.expenses        = expenses
    S.savings         = savings
    S.savings_contrib = contrib
    S.debt_bal        = debt_bal
    S.debt_payment    = debt_pmt
    S.debt_rate       = rate
    S.goal            = goal

    # Widget keys — writing these directly is the only reliable way to
    # update displayed number_input / text_input values on a rerun.
    st.session_state["in_income"]         = income
    st.session_state["in_expenses"]       = expenses
    st.session_state["in_savings"]        = savings
    st.session_state["in_savings_contrib"]= contrib
    st.session_state["in_debt_bal"]       = debt_bal
    st.session_state["in_debt_payment"]   = debt_pmt
    st.session_state["in_debt_rate"]      = rate
    st.session_state["in_goal"]           = goal

def _clear_profile() -> None:
    S.profile = None
    S.income = 5000; S.expenses = 3000; S.savings = 6000
    S.savings_contrib = 200; S.debt_bal = 10000
    S.debt_payment = 300; S.debt_rate = 6.0; S.goal = ""
    # Write widget keys directly so displayed values reset immediately
    st.session_state["in_income"]          = 5000
    st.session_state["in_expenses"]        = 3000
    st.session_state["in_savings"]         = 6000
    st.session_state["in_savings_contrib"] = 200
    st.session_state["in_debt_bal"]        = 10000
    st.session_state["in_debt_payment"]    = 300
    st.session_state["in_debt_rate"]       = 6.0
    st.session_state["in_goal"]            = ""

def _build_profile_dict() -> dict:
    return {
        "monthly_income":               S.income,
        "monthly_expenses":             S.expenses,
        "monthly_savings_contribution": S.savings_contrib,
        "monthly_debt_payment":         S.debt_payment,
        "current_savings":              S.savings,
        "debt_balance":                 S.debt_bal,
        "annual_debt_rate_pct":         S.debt_rate,
        "goal":                         S.goal or "not specified",
    }


# ─────────────────────────────────────────────────────────────────────────────
# SHARED CHROME
# ─────────────────────────────────────────────────────────────────────────────
def _wordmark() -> None:
    st.markdown(
        '<div style="margin-bottom:1.6rem">'
        '<p style="font:italic 400 2.6rem/.85 var(--serif);'
        'text-transform:uppercase;letter-spacing:-.025em;'
        'color:var(--text);margin:0">'
        'Fin<span style="color:var(--orange)">Path</span></p>'
        '<p style="font-family:var(--mono);font-size:.6rem;letter-spacing:.14em;'
        'text-transform:uppercase;color:var(--dim);margin:.2rem 0 0">'
        'IBM SkillsBuild · Banking &amp; Financial Services</p>'
        '</div>',
        unsafe_allow_html=True,
    )

def _stepper(current: int) -> None:
    labels = ["Profile", "Question", "Results"]
    parts: list[str] = []
    for i, label in enumerate(labels, 1):
        if i < current:
            dot_s = "background:var(--orange);border-color:var(--orange);color:#fff"
            lbl_c = "var(--muted)"; dot_t = "✓"
        elif i == current:
            dot_s = "border-color:var(--text);color:var(--text)"; lbl_c = "var(--text)"; dot_t = str(i)
        else:
            dot_s = "border-color:var(--border2);color:var(--dim)"; lbl_c = "var(--dim)"; dot_t = str(i)

        parts.append(
            f'<div style="display:flex;align-items:center;gap:.4rem;'
            f'font-family:var(--mono);font-size:.6rem;letter-spacing:.08em;text-transform:uppercase">'
            f'<div style="width:20px;height:20px;border-radius:50%;border:1.5px solid;'
            f'display:flex;align-items:center;justify-content:center;'
            f'font-size:.62rem;flex-shrink:0;{dot_s}">{dot_t}</div>'
            f'<span style="color:{lbl_c};white-space:nowrap">{label}</span></div>'
        )
        if i < 3:
            parts.append(
                f'<div style="flex:1;height:1px;background:var(--border);'
                f'margin:0 .5rem;min-width:10px;opacity:{"1" if i < current else ".4"}"></div>'
            )
    st.markdown(
        f'<div style="display:flex;align-items:center;margin-bottom:1.6rem">'
        f'{"".join(parts)}</div>',
        unsafe_allow_html=True,
    )

def _section_label(text: str, margin_top: str = "1.1rem") -> None:
    st.markdown(
        f'<p style="font-family:var(--mono);font-size:.58rem;letter-spacing:.1em;'
        f'text-transform:uppercase;color:var(--dim);margin:{margin_top} 0 .5rem">'
        f'{text}</p>',
        unsafe_allow_html=True,
    )

def _disclaimer() -> None:
    st.markdown(
        '<div style="margin-top:2rem;padding:.6rem 1rem;'
        'border-left:3px solid var(--orange);'
        'background:rgba(232,96,60,.05);border-radius:0 6px 6px 0;">'
        '<span style="font-family:var(--mono);font-size:.63rem;'
        'color:var(--muted);letter-spacing:.03em">'
        'Educational tool · Not financial advice · '
        'All projections are illustrative only.</span>'
        '</div>',
        unsafe_allow_html=True,
    )

def _tool_chips(tools: list[str]) -> None:
    if not tools:
        return
    chips = "".join(
        f'<span style="display:inline-flex;align-items:center;gap:.3rem;'
        f'padding:.18rem .55rem;margin:.2rem .2rem 0 0;'
        f'background:var(--orangeA);border:1px solid var(--orangeB);'
        f'border-radius:3px;font-family:var(--mono);font-size:.6rem;color:var(--orange)">'
        f'<span style="font-size:.65rem;opacity:.7">⚙</span>{n}</span>'
        for n in tools
    )
    st.markdown(
        f'<div style="margin:.5rem 0 .15rem">'
        f'<span style="font-family:var(--mono);font-size:.56rem;letter-spacing:.1em;'
        f'text-transform:uppercase;color:var(--dim);margin-right:.4rem">Tools used</span>'
        f'{chips}</div>',
        unsafe_allow_html=True,
    )

def _assumptions_expander() -> None:
    with st.expander("📋 Assumptions used"):
        rows = [
            ("Monthly income",        f"${S.income:,}"),
            ("Monthly expenses",      f"${S.expenses:,}"),
            ("Currently saving/mo",   f"${S.savings_contrib:,}"),
            ("Monthly debt payment",  f"${S.debt_payment:,}"),
            ("Cash savings",          f"${S.savings:,}"),
            ("Debt balance",          f"${S.debt_bal:,}"),
            ("Debt interest rate",    f"{S.debt_rate:.1f}% p.a."),
            ("Growth rate (default)", "5% p.a."),
            ("Projection horizon",    "12 months"),
            ("EF target (guideline)", "3–6 months of expenses"),
        ]
        html = "".join(
            f'<div style="display:flex;justify-content:space-between;'
            f'padding:.32rem 0;border-bottom:1px solid var(--border)">'
            f'<span style="font-family:var(--mono);font-size:.63rem;color:var(--muted)">{l}</span>'
            f'<span style="font-family:var(--mono);font-size:.63rem;color:var(--text)">{v}</span>'
            f'</div>'
            for l, v in rows
        )
        st.markdown(html, unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# HEALTH CARD  (Step 1, local compute — no agent call)
# ─────────────────────────────────────────────────────────────────────────────
def _health_card() -> None:
    try:
        h = _fhc(
            income=S.income, expenses=S.expenses,
            monthly_savings_contribution=S.savings_contrib,
            current_savings=S.savings, debt_balance=S.debt_bal,
            annual_debt_rate=S.debt_rate / 100,
            monthly_debt_payment=S.debt_payment,
        )
    except Exception:
        return

    score = h["score"]
    color = "#4EA86B" if score >= 75 else ("#D4A84B" if score >= 50 else ("#E8603C" if score >= 25 else "#D95F5F"))
    label = "Strong" if score >= 75 else ("Moderate" if score >= 50 else ("Needs attention" if score >= 25 else "Critical"))

    # SVG ring
    r = 32; circ = 2 * 3.14159 * r
    offset = circ * (1 - score / 100)
    ring = (
        f'<svg width="88" height="88" viewBox="0 0 88 88">'
        f'<circle cx="44" cy="44" r="{r}" fill="none" stroke="rgba(255,255,255,.06)" stroke-width="8"/>'
        f'<circle cx="44" cy="44" r="{r}" fill="none" stroke="{color}" stroke-width="8"'
        f' stroke-dasharray="{circ:.1f}" stroke-dashoffset="{offset:.1f}"'
        f' stroke-linecap="round" transform="rotate(-90 44 44)"/>'
        f'<text x="44" y="48" text-anchor="middle" font-family="JetBrains Mono,monospace"'
        f' font-size="18" font-weight="600" fill="{color}">{score}</text>'
        f'</svg>'
    )

    # sub-score bars
    def _bar(lbl: str, val: int) -> str:
        pct = val / 25 * 100
        c = "#4EA86B" if pct >= 80 else ("#D4A84B" if pct >= 44 else "#E8603C")
        return (
            f'<div style="margin-bottom:.5rem">'
            f'<div style="display:flex;justify-content:space-between;margin-bottom:.22rem">'
            f'<span style="font-family:var(--mono);font-size:.58rem;letter-spacing:.06em;'
            f'text-transform:uppercase;color:var(--muted)">{lbl}</span>'
            f'<span style="font-family:var(--mono);font-size:.6rem;color:{c}">{val}/25</span>'
            f'</div>'
            f'<div style="height:4px;background:rgba(255,255,255,.06);border-radius:2px">'
            f'<div style="width:{pct:.0f}%;height:100%;background:{c};border-radius:2px;'
            f'transition:width .4s ease"></div></div></div>'
        )

    bars = (
        _bar("Cash flow",       h["cash_flow_score"])
        + _bar("Emergency fund", h["emergency_fund_score"])
        + _bar("Debt burden",    h["debt_burden_score"])
        + _bar("Savings rate",   h["savings_rate_score"])
    )

    # key stats row
    cf    = h["cash_flow"]
    cf_c  = "#4EA86B" if cf >= 0 else "#D95F5F"
    ef    = h["emergency_fund_months"]
    ef_c  = "#4EA86B" if ef >= 3 else ("#D4A84B" if ef >= 1 else "#D95F5F")
    dti   = h["debt_to_income_ratio"] * 100
    dti_c = "#4EA86B" if dti <= 15 else ("#D4A84B" if dti <= 28 else "#D95F5F")
    sr    = h["savings_rate"] * 100
    sr_c  = "#4EA86B" if sr >= 10 else ("#D4A84B" if sr >= 5 else "#D95F5F")

    def _stat(label: str, value: str, color: str) -> str:
        return (
            f'<div style="flex:1;min-width:0;padding:.55rem .6rem;'
            f'background:var(--surface2);border-radius:var(--radius-sm);'
            f'border:1px solid var(--border)">'
            f'<div style="font-family:var(--mono);font-size:.54rem;letter-spacing:.08em;'
            f'text-transform:uppercase;color:var(--dim);margin-bottom:.25rem">{label}</div>'
            f'<div style="font-family:var(--mono);font-size:.9rem;font-weight:600;color:{color}">{value}</div>'
            f'</div>'
        )

    stats = (
        f'<div style="display:flex;gap:.4rem;margin-bottom:.9rem;flex-wrap:wrap">'
        + _stat("Surplus/mo", f"${cf:+,.0f}", cf_c)
        + _stat("EF coverage", f"{ef:.1f} mo", ef_c)
        + _stat("Debt/income", f"{dti:.0f}%", dti_c)
        + _stat("Saving rate", f"{sr:.0f}%", sr_c)
        + '</div>'
    )

    # priority list
    pri_items = "".join(
        f'<div style="display:flex;align-items:flex-start;gap:.55rem;'
        f'padding:.4rem .65rem;margin-bottom:.28rem;'
        f'background:var(--surface2);border-radius:var(--radius-sm);'
        f'border:1px solid var(--border)">'
        f'<span style="color:var(--orange);font-size:.8rem;margin-top:.05rem;flex-shrink:0">›</span>'
        f'<span style="font-family:var(--mono);font-size:.63rem;color:var(--muted);line-height:1.4">{p}</span>'
        f'</div>'
        for p in h["priorities"][:3]
    )

    st.markdown(
        f'<div style="margin:1.2rem 0 0;padding:1rem 1.1rem 1.1rem;'
        f'background:var(--surface);border:1px solid var(--border2);'
        f'border-radius:var(--radius)">'

        # Header row: score label + ring
        f'<div style="display:flex;align-items:center;justify-content:space-between;'
        f'margin-bottom:.9rem">'
        f'<div>'
        f'<p style="font-family:var(--mono);font-size:.58rem;letter-spacing:.1em;'
        f'text-transform:uppercase;color:var(--dim);margin:0 0 .2rem">Financial health</p>'
        f'<p style="font:italic 400 1.35rem/1 var(--serif);color:{color};margin:0">{label}</p>'
        f'</div>'
        f'<div>{ring}</div>'
        f'</div>'

        # 4 stat pills
        + stats

        # sub-score bars
        + bars

        # priorities
        + f'<p style="font-family:var(--mono);font-size:.58rem;letter-spacing:.1em;'
        f'text-transform:uppercase;color:var(--dim);margin:.7rem 0 .4rem">Priorities</p>'
        + pri_items

        + '</div>',
        unsafe_allow_html=True,
    )


# ─────────────────────────────────────────────────────────────────────────────
# STEP 1 — PROFILE
# ─────────────────────────────────────────────────────────────────────────────
def render_step1() -> None:
    _wordmark()
    _stepper(1)

    st.markdown(
        '<h2 style="font:italic 400 1.65rem/1.1 var(--serif);margin:0 0 .2rem">'
        'Your <span style="color:var(--orange)">profile</span></h2>'
        '<p style="font-family:var(--mono);font-size:.62rem;letter-spacing:.05em;'
        'text-transform:uppercase;color:var(--muted);margin-bottom:1.4rem">'
        'Step 1 of 3 · Select a sample or fill in your own numbers</p>',
        unsafe_allow_html=True,
    )

    # ── Sample profiles grid ──────────────────────────────────────────────────
    _section_label("Sample profiles", margin_top="0")
    rows = [PROFILES[i:i+3] for i in range(0, len(PROFILES), 3)]
    for row in rows:
        cols = st.columns(3)
        for col, p in zip(cols, row):
            is_sel = S.profile is not None and S.profile["id"] == p["id"]
            name   = p["label"].split("—")[0].strip()
            desc   = p["label"].split("—")[1].strip() if "—" in p["label"] else ""
            with col:
                wrap = '<div class="profile-selected">' if is_sel else '<div>'
                st.markdown(wrap, unsafe_allow_html=True)
                st.button(name, key=f"chip_{p['id']}", use_container_width=True,
                          on_click=_load_profile, args=(p,))
                if desc:
                    st.caption(desc)
                st.markdown('</div>', unsafe_allow_html=True)

    col_clear, _ = st.columns([1, 3])
    with col_clear:
        st.button("↺ Clear", key="chip_manual", type="tertiary", on_click=_clear_profile)

    if S.profile:
        st.markdown(
            f'<p style="font-family:var(--mono);font-size:.62rem;color:var(--orange);'
            f'margin:.3rem 0 .8rem">✓ {S.profile["label"]}</p>',
            unsafe_allow_html=True,
        )

    st.markdown('<hr>', unsafe_allow_html=True)

    # ── Two-column form layout ────────────────────────────────────────────────
    left_col, right_col = st.columns([1, 1], gap="large")

    with left_col:
        _section_label("Income & expenses", margin_top="0")
        S.income = st.number_input(
            "Monthly take-home income ($)", min_value=0, step=100,
            value=int(S.income), key="in_income",
        )
        S.expenses = st.number_input(
            "Monthly essential expenses ($)", min_value=0, step=100,
            value=int(S.expenses), key="in_expenses",
        )

    with right_col:
        _section_label("Savings", margin_top="0")
        S.savings = st.number_input(
            "Current cash savings ($)", min_value=0, step=500,
            value=int(S.savings), key="in_savings",
        )
        S.savings_contrib = st.number_input(
            "Currently saving per month ($)", min_value=0, step=50,
            value=int(S.savings_contrib), key="in_savings_contrib",
        )

    left2, right2 = st.columns([1, 1], gap="large")

    with left2:
        _section_label("Debt", margin_top=".8rem")
        S.debt_bal = st.number_input(
            "Total debt balance ($)", min_value=0, step=1000,
            value=int(S.debt_bal), key="in_debt_bal",
        )
        S.debt_payment = st.number_input(
            "Monthly debt payment ($)", min_value=0, step=50,
            value=int(S.debt_payment), key="in_debt_payment",
        )

    with right2:
        _section_label("Rate & goal", margin_top=".8rem")
        S.debt_rate = st.number_input(
            "Debt interest rate (% p.a.)", min_value=0.0, max_value=50.0,
            step=0.5, value=float(S.debt_rate), key="in_debt_rate", format="%.1f",
        )
        S.goal = st.text_input(
            "Goal (optional)",
            value=S.goal,
            placeholder="e.g. Pay off debt in 3 years",
            key="in_goal",
        )

    # ── Live health card ──────────────────────────────────────────────────────
    if _HEALTH_AVAILABLE and S.income > 0 and S.expenses > 0:
        _health_card()

    st.markdown('<hr>', unsafe_allow_html=True)

    _, btn_col = st.columns([3, 1])
    with btn_col:
        st.button(
            "Next →", key="step1_next", use_container_width=True, type="primary",
            disabled=(S.income == 0 or S.expenses == 0),
            on_click=lambda: _go(2),
        )

    _disclaimer()


# ─────────────────────────────────────────────────────────────────────────────
# STEP 2 — QUESTION
# ─────────────────────────────────────────────────────────────────────────────
def _set_question(q: str) -> None:
    st.session_state["in_question"] = q
    st.session_state["question"]    = q


def render_step2() -> None:
    _wordmark()
    _stepper(2)

    st.markdown(
        '<h2 style="font:italic 400 1.65rem/1.1 var(--serif);margin:0 0 .2rem">'
        'Your <span style="color:var(--orange)">question</span></h2>'
        '<p style="font-family:var(--mono);font-size:.62rem;letter-spacing:.05em;'
        'text-transform:uppercase;color:var(--muted);margin-bottom:1.2rem">'
        'Step 2 of 3 · Ask about your financial situation</p>',
        unsafe_allow_html=True,
    )

    # Profile pills
    pill = (
        'display:inline-flex;align-items:center;gap:.3rem;'
        'padding:.2rem .6rem;margin:.12rem .18rem;'
        'background:var(--surface2);border:1px solid var(--border);'
        'border-radius:20px;font-family:var(--mono);font-size:.6rem;'
        'color:var(--muted);white-space:nowrap'
    )
    vs = 'color:var(--text);font-weight:500'
    st.markdown(
        f'<div style="display:flex;flex-wrap:wrap;margin-bottom:1.3rem">'
        f'<span style="{pill}">Income <b style="{vs}">${S.income:,}</b></span>'
        f'<span style="{pill}">Expenses <b style="{vs}">${S.expenses:,}</b></span>'
        f'<span style="{pill}">Savings <b style="{vs}">${S.savings:,}</b></span>'
        f'<span style="{pill}">Saving/mo <b style="{vs}">${S.savings_contrib:,}</b></span>'
        f'<span style="{pill}">Debt pmt <b style="{vs}">${S.debt_payment:,}</b></span>'
        f'<span style="{pill}">Debt <b style="{vs}">${S.debt_bal:,} @ {S.debt_rate:.1f}%</b></span>'
        f'</div>',
        unsafe_allow_html=True,
    )

    # Suggestion chips 2-col
    _section_label("Quick suggestions", margin_top="0")
    c1, c2 = st.columns(2, gap="small")
    for i, s in enumerate(SUGGESTIONS):
        col = c1 if i % 2 == 0 else c2
        with col:
            st.markdown('<div class="sug-btn">', unsafe_allow_html=True)
            st.button(s, key=f"sug_{i}", use_container_width=True,
                      on_click=_set_question, args=(s,))
            st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div style="margin-top:1rem"></div>', unsafe_allow_html=True)

    # Question input
    if "in_question" not in st.session_state:
        st.session_state["in_question"] = st.session_state.get("question", "")
    S.question = st.text_area(
        "Or type your own question",
        height=90,
        placeholder="e.g. Should I pay extra on my debt or put it in savings?",
        key="in_question",
    )
    S.question = st.session_state["in_question"]

    st.markdown('<hr>', unsafe_allow_html=True)

    back_col, go_col = st.columns([1, 1])
    with back_col:
        if st.button("← Edit profile", key="step2_back", use_container_width=True):
            _go(1)
    with go_col:
        if st.button(
            "Ask FinPath →", key="step2_run", use_container_width=True, type="primary",
            disabled=not S.question.strip(),
        ):
            S.messages = []; S.thread_id = None
            S.pending_send = None; S.error = None
            _go(3)

    _disclaimer()


# ─────────────────────────────────────────────────────────────────────────────
# STEP 3 — CHAT
# ─────────────────────────────────────────────────────────────────────────────
def _send_message(text: str) -> None:
    S.messages.append({"role": "user", "content": text, "tools": []})
    S.pending_send = text
    S.error = None

def _run_agent() -> None:
    if not S.pending_send:
        return
    user_text = S.pending_send
    S.pending_send = None
    with st.spinner("FinPath AI is thinking…"):
        try:
            res = ask_agent(message=user_text, profile=_build_profile_dict(),
                            thread_id=S.thread_id)
            S.thread_id = res["thread_id"]
            S.messages.append({"role": "assistant",
                                "content": res["reply"], "tools": res["tools"]})
        except (RuntimeError, TimeoutError) as e:
            S.error = str(e)
            if S.messages and S.messages[-1]["role"] == "user":
                S.messages.pop()
        except Exception as e:
            S.error = "Unexpected error. Check that your Orchestrate environment is active."
            _log.debug("Agent call failed", exc_info=True)
            if S.messages and S.messages[-1]["role"] == "user":
                S.messages.pop()
    st.rerun()


def render_step3() -> None:
    _wordmark()
    _stepper(3)

    st.markdown(
        '<h2 style="font:italic 400 1.65rem/1.1 var(--serif);margin:0 0 .2rem">'
        'Your <span style="color:var(--orange)">results</span></h2>'
        '<p style="font-family:var(--mono);font-size:.62rem;letter-spacing:.05em;'
        'text-transform:uppercase;color:var(--muted);margin-bottom:1rem">'
        'Step 3 of 3 · Illustrative projections — not financial advice</p>',
        unsafe_allow_html=True,
    )

    # Seed first turn from the question
    if not S.messages and S.question:
        _send_message(S.question)

    _run_agent()

    # Error
    if S.error:
        st.markdown(
            f'<div style="padding:.7rem 1rem;background:rgba(217,95,95,.10);'
            f'border:1px solid rgba(217,95,95,.28);border-radius:var(--radius);'
            f'font-family:var(--mono);font-size:.75rem;color:#D95F5F;margin-bottom:.8rem">'
            f'⚠ {S.error}</div>',
            unsafe_allow_html=True,
        )
        if st.button("Dismiss ×", key="err_dismiss"):
            S.error = None; st.rerun()

    # Chat history
    for msg in S.messages:
        if msg["role"] == "user":
            with st.chat_message("user"):
                st.markdown(msg["content"])
        else:
            with st.chat_message("assistant"):
                st.markdown(msg["content"])
                if msg.get("tools"):
                    _tool_chips(msg["tools"])

    # Follow-up chips
    if S.messages and S.messages[-1]["role"] == "assistant" and not S.pending_send:
        _section_label("Follow-up suggestions", margin_top=".8rem")
        fc = st.columns(len(FOLLOWUP_SUGGESTIONS), gap="small")
        for col, sug in zip(fc, FOLLOWUP_SUGGESTIONS):
            with col:
                st.markdown('<div class="sug-btn">', unsafe_allow_html=True)
                st.button(sug, key=f"fu_{sug[:18]}", use_container_width=True,
                          on_click=_send_message, args=(sug,))
                st.markdown('</div>', unsafe_allow_html=True)

    # Chat input
    inp = st.chat_input("Ask a follow-up…")
    if inp and inp.strip():
        _send_message(inp.strip()); st.rerun()

    # Assumptions
    if S.messages:
        _assumptions_expander()

    st.markdown('<hr>', unsafe_allow_html=True)

    l_col, r_col = st.columns([1, 1])
    with l_col:
        if st.button("← Edit profile", key="res_back"):
            S.error = None; _go(1)
    with r_col:
        if st.button("New conversation", key="res_new", use_container_width=True):
            S.messages = []; S.thread_id = None
            S.question = ""; S.error = None; S.pending_send = None
            st.session_state.pop("in_question", None)
            _go(2)

    _disclaimer()


# ─────────────────────────────────────────────────────────────────────────────
# ROUTER
# ─────────────────────────────────────────────────────────────────────────────
if   S.step == 1: render_step1()
elif S.step == 2: render_step2()
elif S.step == 3: render_step3()
