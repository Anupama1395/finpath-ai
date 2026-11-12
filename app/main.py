"""
app/main.py
-----------
FinPath AI — Streamlit frontend (3-step wizard + chat).

Steps:
  1  Profile   — pick a sample profile or enter manually
  2  Question  — type a goal / pick a suggestion chip
  3  Results   — multi-turn chat with tool trace per reply

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
# Inserted into sys.path at runtime, so guard against import errors at startup.
try:
    _tools_path = str(Path(__file__).parent.parent)
    if _tools_path not in sys.path:
        sys.path.insert(0, _tools_path)
    from tools.core.finance import financial_health_check as _fhc
    _HEALTH_AVAILABLE = True
except Exception:
    _HEALTH_AVAILABLE = False

# ── sys.path ──────────────────────────────────────────────────────────────────
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
@import url('https://fonts.googleapis.com/css2?family=Fraunces:ital,wght@0,400;1,400&family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@400;500&display=swap');

/* ── design tokens ── */
:root{
  --bg:      #0B0D10;
  --surface: #171B21;
  --surface2:#1E232B;
  --border:  rgba(236,232,225,.10);
  --text:    #ECE8E1;
  --muted:   #A6ACB4;
  --dim:     #7D848D;
  --orange:  #E8603C;
  --orange2: #C94E2C;
  --gold:    #D4A84B;
  --green:   #5BB87A;
  --ice:     #7EB8C9;

  --serif: 'Fraunces', Georgia, serif;
  --sans:  'Inter', -apple-system, system-ui, sans-serif;
  --mono:  'JetBrains Mono', 'Courier New', monospace;
}

/* ── base ── */
html, body, [class*="css"]{
  font-family: var(--sans) !important;
  -webkit-font-smoothing: antialiased;
}
.stApp{
  background: var(--bg) !important;
  color: var(--text) !important;
}
header[data-testid="stHeader"],
footer,
#MainMenu{ display:none !important; }

/* content column */
.block-container{
  max-width: 880px !important;
  padding: 2rem 1.2rem 3rem !important;
}

/* ── ALL inputs: dark bg, light text ── */
[data-baseweb="base-input"],
[data-baseweb="input"],
[data-baseweb="textarea"]{
  background: var(--surface) !important;
  border-color: var(--border) !important;
}
[data-baseweb="base-input"] input,
[data-baseweb="input"] input,
[data-baseweb="textarea"] textarea,
textarea{
  background: var(--surface) !important;
  color: var(--text) !important;
  font-family: var(--mono) !important;
  caret-color: var(--orange) !important;
}
input::placeholder, textarea::placeholder{
  color: var(--dim) !important;
  opacity: 1 !important;
}
/* stepper arrows on number inputs */
[data-baseweb="base-input"] button{
  background: var(--surface) !important;
  color: var(--muted) !important;
  border-color: var(--border) !important;
  letter-spacing: normal !important;
  text-transform: none !important;
  font-size: .8rem !important;
  padding: .15rem .5rem !important;
}

/* ── labels ── */
label, .stSlider label, .stNumberInput label,
.stTextInput label, .stTextArea label,
.stSelectbox label{
  font-family: var(--mono) !important;
  font-size: .65rem !important;
  letter-spacing: .07em !important;
  text-transform: uppercase !important;
  color: var(--muted) !important;
}

/* ── Streamlit buttons: dark base ── */
.stButton button{
  background: var(--surface) !important;
  border: 1px solid var(--border) !important;
  color: var(--text) !important;
  font-family: var(--mono) !important;
  font-size: .68rem !important;
  letter-spacing: .07em !important;
  text-transform: uppercase !important;
  border-radius: 4px !important;
  padding: .45rem 1.1rem !important;
  transition: background .15s, border-color .15s !important;
}
.stButton button:hover{
  background: var(--surface2) !important;
  border-color: var(--muted) !important;
  color: var(--text) !important;
}
/* primary — orange */
[data-testid="stButton"] button[kind="primary"],
.btn-primary .stButton button{
  background: var(--orange) !important;
  border-color: var(--orange) !important;
  color: #fff !important;
}
[data-testid="stButton"] button[kind="primary"]:hover,
.btn-primary .stButton button:hover{
  background: var(--orange2) !important;
  border-color: var(--orange2) !important;
}
/* selected profile card */
.profile-selected .stButton button{
  border-color: var(--orange) !important;
  background: rgba(232,96,60,.12) !important;
  color: var(--orange) !important;
}
/* link button */
.stButton button[kind="tertiary"]{
  background: transparent !important;
  border-color: transparent !important;
  color: var(--dim) !important;
  font-size: .65rem !important;
  text-decoration: underline !important;
  padding: .2rem .4rem !important;
}
.stButton button[kind="tertiary"]:hover{
  color: var(--muted) !important;
}
/* suggestion chip buttons */
.suggestion-btn .stButton button{
  background: var(--surface) !important;
  border: 1px solid var(--border) !important;
  color: var(--muted) !important;
  font-size: .67rem !important;
  padding: .4rem .9rem !important;
  text-align: left !important;
  white-space: normal !important;
  height: auto !important;
  line-height: 1.4 !important;
}
.suggestion-btn .stButton button:hover{
  border-color: var(--orange) !important;
  color: var(--text) !important;
}

/* ── slider ── */
.stSlider [data-baseweb="slider"] [role="slider"]{
  background: var(--orange) !important;
  border-color: var(--orange) !important;
}

/* ── expander ── */
.streamlit-expanderHeader{
  font-family: var(--mono) !important;
  font-size: .65rem !important;
  letter-spacing: .07em !important;
  text-transform: uppercase !important;
  color: var(--muted) !important;
}

/* ── markdown tables ── */
.stMarkdown table{
  width: 100%; border-collapse: collapse; font-size: .85rem; margin: .6rem 0;
}
.stMarkdown th{
  background: var(--surface); color: var(--muted);
  font-family: var(--mono); font-size: .62rem; letter-spacing: .08em; text-transform: uppercase;
  padding: .5rem .8rem; border: 1px solid var(--border);
}
.stMarkdown td{ padding: .5rem .8rem; border: 1px solid var(--border); color: var(--text); }
.stMarkdown tr:nth-child(even) td{ background: rgba(255,255,255,.02); }

/* ── divider ── */
hr{ border-color: var(--border) !important; margin: 1.4rem 0 !important; }

/* ── chat messages ── */
[data-testid="stChatMessage"]{
  background: var(--surface) !important;
  border: 1px solid var(--border) !important;
  border-radius: 6px !important;
  margin-bottom: .6rem !important;
}

/* ── chart ── */
.vega-embed{ background: transparent !important; }
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
    "How long will it take to pay off my debt?",
    "Is my emergency fund healthy?",
    "Should I pay off debt first or start investing?",
    "What if my income dropped by 10%?",
    "What if my expenses rose by 15%?",
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
        # chat state
        "messages":        [],   # list of {role, content, tools}
        "thread_id":       None,
        "pending_send":    None, # set to trigger an agent call on next rerun
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


# Widget keys that mirror the session-state fields on Step 1.
# Deleting them before writing new values forces Streamlit to re-initialise
# the widgets from the updated value= arguments.
_INPUT_KEYS = [
    "in_income", "in_expenses", "in_savings", "in_savings_contrib",
    "in_debt_bal", "in_debt_payment", "in_debt_rate", "in_goal",
]

def _reset_input_widgets() -> None:
    for k in _INPUT_KEYS:
        st.session_state.pop(k, None)


def _load_profile(p: dict) -> None:
    S.profile         = p
    S.income          = int(p["monthly_income"])
    S.expenses        = int(p["monthly_expenses"])
    S.savings         = int(p["cash_savings"])
    S.savings_contrib = int(p.get("monthly_savings_contribution", 0))
    S.debt_bal        = int(p["debt_balance"])
    S.debt_payment    = int(p.get("monthly_debt_payment", 0))
    S.debt_rate       = float(p["debt_rate"] * 100)
    S.goal            = p["savings_goal"]
    _reset_input_widgets()


def _clear_profile() -> None:
    S.profile         = None
    S.income          = 5000
    S.expenses        = 3000
    S.savings         = 6000
    S.savings_contrib = 200
    S.debt_bal        = 10000
    S.debt_payment    = 300
    S.debt_rate       = 6.0
    S.goal            = ""
    _reset_input_widgets()


def _build_profile_dict() -> dict:
    """Build the profile dict that api_client.ask_agent expects."""
    return {
        "monthly_income":               S.income,
        "monthly_expenses":             S.expenses,
        "monthly_savings_contribution": S.savings_contrib,
        "monthly_debt_payment":         S.debt_payment,
        "current_savings":              S.savings,
        "debt_balance":                 S.debt_bal,
        "annual_debt_rate_pct":         S.debt_rate,   # percentage, e.g. 7.0
        "goal":                         S.goal or "not specified",
    }


def _pick_highlighted(scenarios: list[dict]) -> int:
    feasible = [(i, s) for i, s in enumerate(scenarios) if s.get("feasible")]
    if not feasible:
        return 0
    best_i, _ = max(feasible, key=lambda x: x[1].get("savings_contribution", 0))
    return best_i


# ─────────────────────────────────────────────────────────────────────────────
# SHARED WIDGETS
# ─────────────────────────────────────────────────────────────────────────────
def _render_wordmark() -> None:
    st.markdown(
        '<p style="font:italic 400 clamp(1.9rem,5vw,3rem)/.9 var(--serif);'
        'text-transform:uppercase;letter-spacing:-.02em;color:var(--text);margin:0 0 .15rem">'
        'Fin<span style="color:var(--orange)">Path</span> AI</p>'
        '<p style="font-family:var(--mono);font-size:.62rem;letter-spacing:.12em;'
        'text-transform:uppercase;color:var(--dim);margin-bottom:1.8rem">'
        'IBM SkillsBuild · Banking &amp; Financial Services</p>',
        unsafe_allow_html=True,
    )


def _render_step_indicator(current: int) -> None:
    labels = ["Profile", "Question", "Results"]
    parts: list[str] = []
    for i, label in enumerate(labels, 1):
        if i < current:
            cls, dot = "done", "✓"
        elif i == current:
            cls, dot = "active", str(i)
        else:
            cls, dot = "inactive", str(i)

        done_style   = "background:var(--orange);border-color:var(--orange);color:#fff;"
        active_style = "border-color:var(--text);color:var(--text);"
        off_style    = "border-color:var(--border);color:var(--dim);"
        dot_style    = done_style if cls == "done" else (active_style if cls == "active" else off_style)
        label_color  = "var(--text)" if cls == "active" else ("var(--muted)" if cls == "done" else "var(--dim)")

        parts.append(
            f'<div style="display:flex;align-items:center;gap:.4rem;'
            f'font-family:var(--mono);font-size:.62rem;letter-spacing:.08em;text-transform:uppercase;">'
            f'<div style="width:22px;height:22px;border-radius:50%;border:1px solid;'
            f'display:flex;align-items:center;justify-content:center;font-size:.68rem;flex-shrink:0;{dot_style}">'
            f'{dot}</div>'
            f'<span style="color:{label_color};white-space:nowrap">{label}</span>'
            f'</div>'
        )
        if i < 3:
            parts.append(
                '<div style="flex:1;height:1px;background:var(--border);'
                'margin:0 .4rem;min-width:12px"></div>'
            )

    st.markdown(
        f'<div style="display:flex;align-items:center;margin-bottom:1.8rem">'
        f'{"".join(parts)}</div>',
        unsafe_allow_html=True,
    )


def _render_disclaimer() -> None:
    st.markdown(
        '<div style="margin-top:1.8rem;padding:.65rem .9rem;'
        'border-left:3px solid var(--orange);'
        'background:rgba(232,96,60,.06);border-radius:0 4px 4px 0;">'
        '<span style="font-family:var(--mono);font-size:.65rem;letter-spacing:.04em;'
        'color:var(--muted);">Educational tool · Not financial advice · '
        'All projections are illustrative and based on the figures you supply.</span>'
        '</div>',
        unsafe_allow_html=True,
    )


def _render_tool_chips(tool_steps: list[str]) -> None:
    if not tool_steps:
        return
    chips = "".join(
        f'<span style="display:inline-block;padding:.22rem .65rem;margin:.2rem .25rem .2rem 0;'
        f'background:rgba(232,96,60,.10);border:1px solid rgba(232,96,60,.28);border-radius:3px;'
        f'font-family:var(--mono);font-size:.62rem;letter-spacing:.06em;color:var(--orange)">'
        f'{name}()</span>'
        for name in tool_steps
    )
    st.markdown(
        f'<div style="margin:.4rem 0 .2rem">'
        f'<span style="font-family:var(--mono);font-size:.58rem;letter-spacing:.1em;'
        f'text-transform:uppercase;color:var(--dim);margin-right:.5rem">Tools:</span>'
        f'{chips}</div>',
        unsafe_allow_html=True,
    )


def _render_assumptions_expander() -> None:
    with st.expander("Assumptions used"):
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
            ("Emergency fund target", "3–6 months of expenses (guideline)"),
        ]
        row_html = "".join(
            f'<div style="display:flex;justify-content:space-between;padding:.35rem 0;'
            f'border-bottom:1px solid var(--border);">'
            f'<span style="color:var(--muted);font-family:var(--mono);font-size:.65rem;'
            f'letter-spacing:.04em">{label}</span>'
            f'<span style="color:var(--text);font-family:var(--mono);font-size:.65rem">{value}</span>'
            f'</div>'
            for label, value in rows
        )
        st.markdown(row_html, unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# HEALTH CARD (Step 1, computed locally — no agent call)
# ─────────────────────────────────────────────────────────────────────────────

def _render_health_card() -> None:
    """Render a financial health score card using local math (no agent call)."""
    try:
        h = _fhc(
            income=S.income,
            expenses=S.expenses,
            monthly_savings_contribution=S.savings_contrib,
            current_savings=S.savings,
            debt_balance=S.debt_bal,
            annual_debt_rate=S.debt_rate / 100,
            monthly_debt_payment=S.debt_payment,
        )
    except Exception:
        return  # silently skip if inputs are invalid mid-edit

    score  = h["score"]
    # Colour gradient: red→amber→green
    if score >= 75:
        ring_color = "#5BB87A"  # green
    elif score >= 50:
        ring_color = "#D4A84B"  # amber/gold
    elif score >= 25:
        ring_color = "#E8603C"  # orange
    else:
        ring_color = "#C94E2C"  # red

    # SVG score ring
    radius       = 28
    circumference = 2 * 3.14159 * radius
    dash_offset  = circumference * (1 - score / 100)

    ring_svg = f"""
    <svg width="80" height="80" viewBox="0 0 80 80">
      <circle cx="40" cy="40" r="{radius}" fill="none"
        stroke="rgba(236,232,225,.08)" stroke-width="7"/>
      <circle cx="40" cy="40" r="{radius}" fill="none"
        stroke="{ring_color}" stroke-width="7"
        stroke-dasharray="{circumference:.1f}"
        stroke-dashoffset="{dash_offset:.1f}"
        stroke-linecap="round"
        transform="rotate(-90 40 40)"/>
      <text x="40" y="44" text-anchor="middle"
        font-family="JetBrains Mono,monospace"
        font-size="16" font-weight="600" fill="{ring_color}">{score}</text>
    </svg>"""

    # Sub-score bars
    def _bar(label: str, value: int, max_val: int = 25) -> str:
        pct = value / max_val * 100
        bar_color = "#5BB87A" if pct >= 80 else ("#D4A84B" if pct >= 40 else "#E8603C")
        return (
            f'<div style="margin-bottom:.55rem">'
            f'<div style="display:flex;justify-content:space-between;'
            f'font-family:var(--mono);font-size:.6rem;letter-spacing:.06em;'
            f'text-transform:uppercase;color:var(--muted);margin-bottom:.2rem">'
            f'<span>{label}</span><span style="color:var(--text)">{value}/{max_val}</span></div>'
            f'<div style="height:5px;background:rgba(236,232,225,.08);border-radius:3px">'
            f'<div style="width:{pct:.0f}%;height:100%;background:{bar_color};border-radius:3px"></div>'
            f'</div></div>'
        )

    bars = (
        _bar("Cash flow",       h["cash_flow_score"])
        + _bar("Emergency fund", h["emergency_fund_score"])
        + _bar("Debt burden",    h["debt_burden_score"])
        + _bar("Savings rate",   h["savings_rate_score"])
    )

    # Priority chips
    priority_chips = "".join(
        f'<div style="display:flex;align-items:center;gap:.5rem;padding:.35rem .7rem;'
        f'margin-bottom:.3rem;background:var(--surface2);border-radius:4px;'
        f'font-family:var(--mono);font-size:.63rem;color:var(--muted)">'
        f'<span style="color:var(--orange);font-size:.75rem">›</span>'
        f'<span>{p}</span></div>'
        for p in h["priorities"][:3]
    )

    st.markdown(
        f'<div style="margin:1rem 0;padding:1rem 1.1rem;'
        f'background:var(--surface);border:1px solid var(--border);border-radius:6px">'

        # Header
        f'<p style="font-family:var(--mono);font-size:.6rem;letter-spacing:.1em;'
        f'text-transform:uppercase;color:var(--dim);margin-bottom:.8rem">'
        f'Your financial health</p>'

        # Score ring + bars side by side
        f'<div style="display:flex;gap:1.2rem;align-items:flex-start;margin-bottom:.9rem">'
        f'<div style="flex-shrink:0">{ring_svg}</div>'
        f'<div style="flex:1;min-width:0">{bars}</div>'
        f'</div>'

        # Priorities
        f'<p style="font-family:var(--mono);font-size:.6rem;letter-spacing:.1em;'
        f'text-transform:uppercase;color:var(--dim);margin:.2rem 0 .4rem">'
        f'Top priorities</p>'
        f'{priority_chips}'
        f'</div>',
        unsafe_allow_html=True,
    )


# ─────────────────────────────────────────────────────────────────────────────
# STEP 1 — PROFILE
# ─────────────────────────────────────────────────────────────────────────────
def render_step1() -> None:
    _render_wordmark()
    _render_step_indicator(1)

    st.markdown(
        '<h2 style="font:italic 400 1.7rem/1.1 var(--serif);margin:0 0 .25rem">'
        'Your <span style="color:var(--orange)">profile</span></h2>'
        '<p style="font-family:var(--mono);font-size:.65rem;letter-spacing:.06em;'
        'text-transform:uppercase;color:var(--muted);margin-bottom:1.4rem">'
        'Step 1 of 3 · Select a sample or enter your own figures</p>',
        unsafe_allow_html=True,
    )

    # ── Profile grid: 3 per row ───────────────────────────────────────────────
    st.markdown(
        '<p style="font-family:var(--mono);font-size:.6rem;letter-spacing:.1em;'
        'text-transform:uppercase;color:var(--dim);margin-bottom:.7rem">'
        'Sample profiles</p>',
        unsafe_allow_html=True,
    )

    rows = [PROFILES[i:i+3] for i in range(0, len(PROFILES), 3)]
    for row in rows:
        cols = st.columns(3)
        for col, p in zip(cols, row):
            is_selected = S.profile is not None and S.profile["id"] == p["id"]
            name_part = p["label"].split("—")[0].strip()
            desc_part = p["label"].split("—")[1].strip() if "—" in p["label"] else ""
            with col:
                if is_selected:
                    st.markdown('<div class="profile-selected">', unsafe_allow_html=True)
                # on_click runs before next render so widget keys are cleared first
                st.button(
                    name_part,
                    key=f"chip_{p['id']}",
                    use_container_width=True,
                    on_click=_load_profile,
                    args=(p,),
                )
                if desc_part:
                    st.caption(desc_part)
                if is_selected:
                    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div style="margin-top:.5rem;margin-bottom:1rem">', unsafe_allow_html=True)
    st.button(
        "Clear and enter my own →",
        key="chip_manual",
        type="tertiary",
        on_click=_clear_profile,
    )
    st.markdown('</div>', unsafe_allow_html=True)

    if S.profile:
        st.markdown(
            f'<p style="font-family:var(--mono);font-size:.65rem;letter-spacing:.05em;'
            f'color:var(--orange);margin-bottom:.6rem">Loaded: {S.profile["label"]}</p>',
            unsafe_allow_html=True,
        )

    st.markdown('<hr>', unsafe_allow_html=True)

    # ── Income & expenses ─────────────────────────────────────────────────────
    st.markdown(
        '<p style="font-family:var(--mono);font-size:.6rem;letter-spacing:.1em;'
        'text-transform:uppercase;color:var(--dim);margin-bottom:.5rem">'
        'Income &amp; expenses</p>',
        unsafe_allow_html=True,
    )
    col_a, col_b = st.columns(2)
    with col_a:
        S.income = st.number_input(
            "Monthly take-home income ($)", min_value=0, step=100,
            value=int(S.income), key="in_income",
        )
    with col_b:
        S.expenses = st.number_input(
            "Monthly essential expenses ($)", min_value=0, step=100,
            value=int(S.expenses), key="in_expenses",
        )

    # ── Savings & debt ────────────────────────────────────────────────────────
    st.markdown(
        '<p style="font-family:var(--mono);font-size:.6rem;letter-spacing:.1em;'
        'text-transform:uppercase;color:var(--dim);margin:.9rem 0 .5rem">'
        'Savings &amp; debt</p>',
        unsafe_allow_html=True,
    )
    col_c, col_d = st.columns(2)
    with col_c:
        S.savings = st.number_input(
            "Current cash savings ($)", min_value=0, step=500,
            value=int(S.savings), key="in_savings",
        )
        S.savings_contrib = st.number_input(
            "Currently saving per month ($)", min_value=0, step=50,
            value=int(S.savings_contrib), key="in_savings_contrib",
        )
    with col_d:
        S.debt_bal = st.number_input(
            "Total debt balance ($)", min_value=0, step=1000,
            value=int(S.debt_bal), key="in_debt_bal",
        )
        S.debt_payment = st.number_input(
            "Monthly debt payment ($)", min_value=0, step=50,
            value=int(S.debt_payment), key="in_debt_payment",
        )

    col_e, _ = st.columns([1, 1])
    with col_e:
        S.debt_rate = st.number_input(
            "Debt interest rate (% per year)", min_value=0.0, max_value=50.0,
            step=0.5, value=float(S.debt_rate), key="in_debt_rate",
            format="%.1f",
        )

    # ── Goal ─────────────────────────────────────────────────────────────────
    st.markdown(
        '<p style="font-family:var(--mono);font-size:.6rem;letter-spacing:.1em;'
        'text-transform:uppercase;color:var(--dim);margin:.9rem 0 .5rem">'
        'Goal (optional)</p>',
        unsafe_allow_html=True,
    )
    S.goal = st.text_input(
        "What are you working towards?",
        value=S.goal,
        placeholder="e.g. Pay off debt in 3 years and build a 6-month emergency fund",
        key="in_goal",
    )

    # ── Financial health card (computed locally, no agent call) ───────────────
    if _HEALTH_AVAILABLE and S.income > 0 and S.expenses > 0:
        _render_health_card()

    st.markdown('<hr>', unsafe_allow_html=True)

    _, right = st.columns([3, 1])
    with right:
        st.button(
            "Next →", key="step1_next", use_container_width=True,
            type="primary",
            disabled=(S.income == 0 or S.expenses == 0),
            on_click=lambda: _go(2),
        )

    _render_disclaimer()


# ─────────────────────────────────────────────────────────────────────────────
# STEP 2 — QUESTION
# ─────────────────────────────────────────────────────────────────────────────
def _set_question(q: str) -> None:
    st.session_state["in_question"] = q
    st.session_state["question"]    = q


def render_step2() -> None:
    _render_wordmark()
    _render_step_indicator(2)

    st.markdown(
        '<h2 style="font:italic 400 1.7rem/1.1 var(--serif);margin:0 0 .25rem">'
        'Your <span style="color:var(--orange)">question</span></h2>'
        '<p style="font-family:var(--mono);font-size:.65rem;letter-spacing:.06em;'
        'text-transform:uppercase;color:var(--muted);margin-bottom:1.2rem">'
        'Step 2 of 3 · Ask about your financial situation</p>',
        unsafe_allow_html=True,
    )

    # Profile summary pills
    pill      = ('display:inline-block;padding:.22rem .65rem;margin:.15rem .2rem;'
                 'background:var(--surface);border:1px solid var(--border);border-radius:20px;'
                 'font-family:var(--mono);font-size:.62rem;color:var(--muted);white-space:nowrap')
    val_style = 'color:var(--text);font-weight:500'
    st.markdown(
        f'<div style="display:flex;flex-wrap:wrap;gap:.1rem;margin-bottom:1.2rem;">'
        f'<span style="{pill}">Income <span style="{val_style}">${S.income:,}</span></span>'
        f'<span style="{pill}">Expenses <span style="{val_style}">${S.expenses:,}</span></span>'
        f'<span style="{pill}">Savings <span style="{val_style}">${S.savings:,}</span></span>'
        f'<span style="{pill}">Saving/mo <span style="{val_style}">${S.savings_contrib:,}</span></span>'
        f'<span style="{pill}">Debt pmt <span style="{val_style}">${S.debt_payment:,}/mo</span></span>'
        f'<span style="{pill}">Debt <span style="{val_style}">${S.debt_bal:,} @ {S.debt_rate:.1f}%</span></span>'
        f'</div>',
        unsafe_allow_html=True,
    )

    # Suggestion chips in 2 columns
    st.markdown(
        '<p style="font-family:var(--mono);font-size:.6rem;letter-spacing:.1em;'
        'text-transform:uppercase;color:var(--dim);margin-bottom:.5rem">'
        'Suggestions</p>',
        unsafe_allow_html=True,
    )
    sc1, sc2 = st.columns(2)
    for idx, suggestion in enumerate(SUGGESTIONS):
        col = sc1 if idx % 2 == 0 else sc2
        with col:
            st.markdown('<div class="suggestion-btn">', unsafe_allow_html=True)
            st.button(
                suggestion,
                key=f"sug_{idx}",
                use_container_width=True,
                on_click=_set_question,
                args=(suggestion,),
            )
            st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div style="margin-top:.9rem"></div>', unsafe_allow_html=True)

    # Question textarea — key owns the value; init guard seeds it on first visit
    if "in_question" not in st.session_state:
        st.session_state["in_question"] = st.session_state.get("question", "")
    S.question = st.text_area(
        "Or type your own question",
        height=96,
        placeholder="e.g. Should I put extra cash towards debt or into savings?",
        key="in_question",
    )
    # keep S.question in sync for the next step
    S.question = st.session_state["in_question"]

    st.markdown('<hr>', unsafe_allow_html=True)

    left, right = st.columns([1, 1])
    with left:
        if st.button("← Edit profile", key="step2_back", use_container_width=True):
            _go(1)
    with right:
        if st.button(
            "Ask FinPath →", key="step2_run", use_container_width=True,
            type="primary",
            disabled=not S.question.strip(),
        ):
            # Reset conversation so a fresh thread starts on Step 3
            S.messages     = []
            S.thread_id    = None
            S.pending_send = None
            S.error        = None
            _go(3)

    _render_disclaimer()


# ─────────────────────────────────────────────────────────────────────────────
# STEP 3 — CHAT
# ─────────────────────────────────────────────────────────────────────────────

def _send_message(text: str) -> None:
    """Append a user message and flag it for agent processing on next rerun."""
    S.messages.append({"role": "user", "content": text, "tools": []})
    S.pending_send = text
    S.error = None


def _run_agent_for_pending() -> None:
    """If pending_send is set, call the agent and append the assistant reply."""
    if not S.pending_send:
        return
    user_text      = S.pending_send
    S.pending_send = None

    with st.spinner("FinPath AI is thinking…"):
        try:
            result = ask_agent(
                message=user_text,
                profile=_build_profile_dict(),
                thread_id=S.thread_id,
            )
            S.thread_id = result["thread_id"]
            S.messages.append({
                "role":    "assistant",
                "content": result["reply"],
                "tools":   result["tools"],
            })
        except (RuntimeError, TimeoutError) as exc:
            S.error = str(exc)
            if S.messages and S.messages[-1]["role"] == "user":
                S.messages.pop()
        except Exception as exc:
            S.error = "An unexpected error occurred. Check your Orchestrate environment is active."
            _log.debug("Agent call failed", exc_info=True)
            if S.messages and S.messages[-1]["role"] == "user":
                S.messages.pop()
    st.rerun()


def render_step3() -> None:
    _render_wordmark()
    _render_step_indicator(3)

    st.markdown(
        '<h2 style="font:italic 400 1.7rem/1.1 var(--serif);margin:0 0 .25rem">'
        'Your <span style="color:var(--orange)">conversation</span></h2>'
        '<p style="font-family:var(--mono);font-size:.65rem;letter-spacing:.06em;'
        'text-transform:uppercase;color:var(--muted);margin-bottom:1rem">'
        'Step 3 of 3 · Illustrative projections — not financial advice</p>',
        unsafe_allow_html=True,
    )

    # Seed first user message from the question entered on Step 2
    if not S.messages and S.question:
        _send_message(S.question)

    # Process any pending agent call
    _run_agent_for_pending()

    # Error banner
    if S.error:
        st.error(S.error)
        if st.button("Dismiss", key="err_dismiss"):
            S.error = None
            st.rerun()

    # Conversation history
    for msg in S.messages:
        if msg["role"] == "user":
            with st.chat_message("user"):
                st.markdown(msg["content"])
        else:
            with st.chat_message("assistant"):
                st.markdown(msg["content"])
                if msg.get("tools"):
                    _render_tool_chips(msg["tools"])

    # Follow-up suggestion buttons (only after last assistant reply)
    if S.messages and S.messages[-1]["role"] == "assistant" and not S.pending_send:
        st.markdown(
            '<p style="font-family:var(--mono);font-size:.6rem;letter-spacing:.1em;'
            'text-transform:uppercase;color:var(--dim);margin:.8rem 0 .35rem">'
            'Follow-up suggestions</p>',
            unsafe_allow_html=True,
        )
        sug_cols = st.columns(len(FOLLOWUP_SUGGESTIONS))
        for col, suggestion in zip(sug_cols, FOLLOWUP_SUGGESTIONS):
            with col:
                st.markdown('<div class="suggestion-btn">', unsafe_allow_html=True)
                st.button(
                    suggestion,
                    key=f"followup_{suggestion[:20]}",
                    use_container_width=True,
                    on_click=_send_message,
                    args=(suggestion,),
                )
                st.markdown('</div>', unsafe_allow_html=True)

    # Chat input for free-form follow-ups
    user_input = st.chat_input("Ask a follow-up, e.g. what if I paid $100 more a month?")
    if user_input and user_input.strip():
        _send_message(user_input.strip())
        st.rerun()

    # Assumptions expander
    if S.messages:
        _render_assumptions_expander()

    st.markdown('<hr>', unsafe_allow_html=True)

    left, right = st.columns([1, 1])
    with left:
        if st.button("← Edit profile", key="res_edit_profile"):
            # Keep thread alive — next message will include updated profile
            S.error = None
            _go(1)
    with right:
        if st.button("New conversation", key="res_new_convo", use_container_width=True):
            S.messages     = []
            S.thread_id    = None
            S.question     = ""
            S.error        = None
            S.pending_send = None
            st.session_state.pop("in_question", None)
            _go(2)

    _render_disclaimer()


# ─────────────────────────────────────────────────────────────────────────────
# ROUTER
# ─────────────────────────────────────────────────────────────────────────────
if   S.step == 1: render_step1()
elif S.step == 2: render_step2()
elif S.step == 3: render_step3()
