"""
app/main.py
-----------
FinPath AI — Streamlit frontend (3-step wizard).

Steps:
  1  Profile   — pick a sample profile or enter manually
  2  Question  — type a goal / pick a suggestion chip
  3  Results   — agent reply, tool trace, scenario cards, assumptions

Start with:
    streamlit run app/main.py
"""

from __future__ import annotations

import json
import logging
import sys
from pathlib import Path

import streamlit as st

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

/* ── ALL inputs: dark bg, light text (belt-and-suspenders on top of config.toml) ── */
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
.stSlider [data-testid="stTickBarMin"],
.stSlider [data-testid="stTickBarMax"]{
  color: var(--dim) !important;
  font-family: var(--mono) !important;
  font-size: .6rem !important;
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

/* ── chart background ── */
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

# ─────────────────────────────────────────────────────────────────────────────
# SESSION STATE
# ─────────────────────────────────────────────────────────────────────────────
def _init_state() -> None:
    defaults: dict = {
        "step":          1,
        "profile":       None,
        "income":        5000,
        "expenses":      3000,
        "savings":       6000,
        "savings_contrib": 200,
        "debt_bal":      10000,
        "debt_payment":  300,
        "debt_rate":     6.0,
        "goal":          "",
        "question":      "",
        "reply":         None,
        "scenarios":     None,
        "tool_steps":    [],
        "thread_id":     None,
        "error":         None,
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


def _build_context() -> str:
    return (
        f"User profile:\n"
        f"- Monthly take-home income: ${S.income:,}\n"
        f"- Monthly essential expenses: ${S.expenses:,}\n"
        f"- Currently saving per month: ${S.savings_contrib:,}\n"
        f"- Monthly debt payment: ${S.debt_payment:,}\n"
        f"- Current cash savings: ${S.savings:,}\n"
        f"- Debt balance: ${S.debt_bal:,} at {S.debt_rate:.2f}% p.a.\n"
        f"- Stated goal: {S.goal}\n\n"
        f"Question: {S.question}"
    )


def _extract_tool_steps(thread_id: str) -> list[str]:
    try:
        from ibm_watsonx_orchestrate.client.threads.threads_client import ThreadsClient
        from ibm_watsonx_orchestrate.client.utils import instantiate_client
        tc = instantiate_client(ThreadsClient)
        resp = tc.get_thread_messages(thread_id)
        messages = (
            resp if isinstance(resp, list)
            else resp.get("data", []) if isinstance(resp, dict)
            else []
        )
        for msg in reversed(messages):
            if isinstance(msg, dict) and msg.get("role") == "assistant":
                steps: list[str] = []
                for step in msg.get("step_history", []):
                    for detail in step.get("step_details", []):
                        if detail.get("type") == "tool_calls":
                            for t in detail.get("tool_calls", []):
                                name = t.get("name") or t.get("function", {}).get("name", "")
                                if name:
                                    steps.append(name)
                return steps
    except Exception:
        _log.debug("Could not extract tool steps", exc_info=True)
    return []


def _pick_highlighted(scenarios: list[dict]) -> int:
    feasible = [(i, s) for i, s in enumerate(scenarios) if s.get("feasible")]
    if not feasible:
        return 0
    best_i, _ = max(feasible, key=lambda x: x[1].get("savings_contribution", 0))
    return best_i


def _fmt_pct(v: float) -> str:
    return f"{v:.1f}%"

def _fmt_dollar(v: float) -> str:
    return f"${v:,.0f}"


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
        'IBM SkillsBuild · Banking &amp; Financial Services · Track 2</p>',
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

        label_color = "var(--text)" if cls == "active" else ("var(--muted)" if cls == "done" else "var(--dim)")

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


# ─────────────────────────────────────────────────────────────────────────────
# STEP 1 — PROFILE
# ─────────────────────────────────────────────────────────────────────────────
def render_step1() -> None:
    _render_wordmark()
    _render_step_indicator(1)

    # Heading
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
                btn_label = f"{name_part}\n{desc_part}" if desc_part else name_part
                if st.button(btn_label, key=f"chip_{p['id']}", use_container_width=True):
                    _load_profile(p)
                    st.rerun()
                if is_selected:
                    st.markdown('</div>', unsafe_allow_html=True)

    # Clear / manual entry link
    st.markdown('<div style="margin-top:.5rem;margin-bottom:1rem">', unsafe_allow_html=True)
    if st.button("Clear and enter my own →", key="chip_manual", type="tertiary"):
        _clear_profile()
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

    # Show which profile is loaded
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

    st.markdown('<hr>', unsafe_allow_html=True)

    # Action row
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
    st.session_state["question"] = q


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
    pill = (
        'display:inline-block;padding:.22rem .65rem;margin:.15rem .2rem;'
        'background:var(--surface);border:1px solid var(--border);border-radius:20px;'
        'font-family:var(--mono);font-size:.62rem;color:var(--muted);white-space:nowrap'
    )
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

    # Question text area
    question_val = st.session_state.get("question", "")
    S.question = st.text_area(
        "Or type your own question",
        value=question_val,
        height=96,
        placeholder="e.g. Should I put extra cash towards debt or into savings?",
        key="in_question",
    )

    st.markdown('<hr>', unsafe_allow_html=True)

    # Action row
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
            S.reply      = None
            S.scenarios  = None
            S.tool_steps = []
            S.error      = None
            _go(3)

    _render_disclaimer()


# ─────────────────────────────────────────────────────────────────────────────
# STEP 3 — RESULTS
# ─────────────────────────────────────────────────────────────────────────────
def _render_scenario_cards(scenarios: list[dict]) -> None:
    highlighted = _pick_highlighted(scenarios)

    cards_html = '<div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(220px,1fr));gap:.7rem;margin:1.2rem 0 .8rem">'
    for i, s in enumerate(scenarios):
        cf     = s.get("cash_flow", 0)
        ef     = s.get("emergency_fund_months", 0)
        ps     = s.get("projected_savings", 0)
        ok     = s.get("feasible", False)
        is_best = (i == highlighted)

        border   = "var(--orange)" if is_best else "var(--border)"
        cf_color = "var(--green)" if cf >= 0 else "var(--orange)"
        badge_bg = "rgba(232,96,60,.12)" if not ok else ("rgba(212,168,75,.12)" if is_best else "rgba(91,184,122,.12)")
        badge_c  = "var(--orange)" if not ok else ("var(--gold)" if is_best else "var(--green)")
        badge_b  = "rgba(232,96,60,.28)" if not ok else ("rgba(212,168,75,.28)" if is_best else "rgba(91,184,122,.28)")
        badge_t  = "Infeasible" if not ok else ("Recommended ★" if is_best else "Feasible")

        cards_html += f"""
<div style="background:var(--surface);border:1px solid {border};border-radius:6px;overflow:hidden">
  <div style="padding:.5rem .8rem;background:var(--surface2);border-bottom:1px solid var(--border);
    font-family:var(--mono);font-size:.58rem;letter-spacing:.1em;text-transform:uppercase;
    color:{'var(--orange)' if is_best else 'var(--muted)'}">
    {s.get('label','—')}
  </div>
  <div style="padding:.85rem .9rem">
    <div style="margin-bottom:.65rem">
      <div style="font-family:var(--mono);font-size:.55rem;letter-spacing:.1em;text-transform:uppercase;color:var(--dim);margin-bottom:.18rem">Monthly surplus</div>
      <div style="font:600 1.15rem/1 var(--sans);color:{cf_color}">${cf:,.0f}</div>
      <span style="display:inline-block;margin-top:.3rem;font-family:var(--mono);font-size:.54rem;
        letter-spacing:.07em;text-transform:uppercase;padding:.15rem .45rem;border-radius:2px;
        background:{badge_bg};color:{badge_c};border:1px solid {badge_b}">{badge_t}</span>
    </div>
    <div style="margin-bottom:.65rem">
      <div style="font-family:var(--mono);font-size:.55rem;letter-spacing:.1em;text-transform:uppercase;color:var(--dim);margin-bottom:.18rem">Emergency fund</div>
      <div style="font:600 1.1rem/1 var(--sans);color:var(--text)">{ef:.1f} <span style="font-size:.78rem;color:var(--dim)">mo</span></div>
    </div>
    <div>
      <div style="font-family:var(--mono);font-size:.55rem;letter-spacing:.1em;text-transform:uppercase;color:var(--dim);margin-bottom:.18rem">Projected (12 mo)</div>
      <div style="font:600 1.1rem/1 var(--mono);color:var(--text)">${ps:,.0f}</div>
    </div>
  </div>
</div>"""
    cards_html += '</div>'
    st.markdown(cards_html, unsafe_allow_html=True)


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
        f'<div style="margin:1rem 0 .6rem">'
        f'<p style="font-family:var(--mono);font-size:.6rem;letter-spacing:.1em;'
        f'text-transform:uppercase;color:var(--dim);margin-bottom:.4rem">Tools used</p>'
        f'{chips}</div>',
        unsafe_allow_html=True,
    )


def _render_chart(scenarios: list[dict]) -> None:
    try:
        import pandas as pd
        import altair as alt
    except ImportError:
        return

    records = []
    for s in scenarios:
        lbl = s.get("label", "—")
        records += [
            {"Scenario": lbl, "Metric": "Monthly Surplus ($)",          "Value": s.get("cash_flow", 0)},
            {"Scenario": lbl, "Metric": "Emergency Fund (months)",      "Value": s.get("emergency_fund_months", 0)},
            {"Scenario": lbl, "Metric": "Projected Savings ($, 12 mo)", "Value": s.get("projected_savings", 0)},
        ]
    df = pd.DataFrame(records)

    chart = (
        alt.Chart(df)
        .mark_bar(cornerRadiusTopLeft=3, cornerRadiusTopRight=3)
        .encode(
            x=alt.X("Scenario:N", axis=alt.Axis(
                labelAngle=0, labelColor="#A6ACB4", tickColor="rgba(0,0,0,0)",
                domainColor="rgba(255,255,255,.08)", labelFontSize=10)),
            y=alt.Y("Value:Q", axis=alt.Axis(
                labelColor="#A6ACB4", gridColor="rgba(255,255,255,.06)",
                tickColor="rgba(0,0,0,0)", domainColor="rgba(0,0,0,0)", labelFontSize=10)),
            color=alt.Color("Scenario:N",
                scale=alt.Scale(range=["#E8603C", "#D4A84B", "#7EB8C9"]),
                legend=alt.Legend(labelColor="#ECE8E1", titleColor="#ECE8E1", labelFontSize=11)),
            facet=alt.Facet("Metric:N", columns=3,
                header=alt.Header(labelColor="#A6ACB4", labelFontSize=10, labelPadding=8)),
            tooltip=["Scenario:N", "Metric:N", alt.Tooltip("Value:Q", format=",.2f")],
        )
        .properties(width=190, height=150)
        .resolve_scale(y="independent")
        .configure_view(strokeOpacity=0, fill="#171B21")
        .configure(background="#0B0D10")
    )
    st.altair_chart(chart, use_container_width=True)


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
            f'border-bottom:1px solid var(--border);font-size:.82rem;">'
            f'<span style="color:var(--muted);font-family:var(--mono);font-size:.65rem;'
            f'letter-spacing:.04em">{label}</span>'
            f'<span style="color:var(--text);font-family:var(--mono);font-size:.65rem">{value}</span>'
            f'</div>'
            for label, value in rows
        )
        st.markdown(row_html, unsafe_allow_html=True)


def render_step3() -> None:
    _render_wordmark()
    _render_step_indicator(3)

    # ── Fetch results (cached in session_state) ───────────────────────────────
    if S.reply is None and S.error is None:
        with st.spinner("FinPath AI is analysing your scenario…"):
            try:
                profile_dict = {
                    "monthly_income":               S.income,
                    "monthly_expenses":             S.expenses,
                    "monthly_savings_contribution": S.savings_contrib,
                    "monthly_debt_payment":         S.debt_payment,
                    "cash_savings":                 S.savings,
                    "debt_balance":                 S.debt_bal,
                    "debt_rate":                    S.debt_rate / 100,
                    "savings_goal":                 S.goal,
                }
                reply, scenarios, new_thread_id = ask_agent(
                    S.question,
                    thread_id=S.thread_id,
                )
                S.reply     = reply
                S.scenarios = scenarios
                S.thread_id = new_thread_id
                if new_thread_id:
                    S.tool_steps = _extract_tool_steps(new_thread_id)
            except (RuntimeError, TimeoutError) as exc:
                S.error = str(exc)
            except Exception as exc:
                S.error = "An unexpected error occurred. Check that your Orchestrate environment is active."
                _log.debug("Agent call failed", exc_info=True)
        st.rerun()

    # ── Error state ───────────────────────────────────────────────────────────
    if S.error:
        st.markdown(
            '<h2 style="font:italic 400 1.7rem/1.1 var(--serif);margin:0 0 .25rem">'
            'Something went <span style="color:var(--orange)">wrong</span></h2>'
            '<p style="font-family:var(--mono);font-size:.65rem;letter-spacing:.06em;'
            'text-transform:uppercase;color:var(--muted);margin-bottom:1.2rem">Step 3 of 3</p>',
            unsafe_allow_html=True,
        )
        st.error(S.error)
        left, right = st.columns([1, 1])
        with left:
            if st.button("← Edit profile", key="err_profile"):
                S.error = None
                _go(1)
        with right:
            if st.button("← Ask another question", key="err_back"):
                S.error = None
                _go(2)
        _render_disclaimer()
        return

    # ── Heading ───────────────────────────────────────────────────────────────
    st.markdown(
        '<h2 style="font:italic 400 1.7rem/1.1 var(--serif);margin:0 0 .25rem">'
        'Your <span style="color:var(--orange)">results</span></h2>'
        '<p style="font-family:var(--mono);font-size:.65rem;letter-spacing:.06em;'
        'text-transform:uppercase;color:var(--muted);margin-bottom:1.2rem">'
        'Step 3 of 3 · Illustrative projections — not financial advice</p>',
        unsafe_allow_html=True,
    )

    # Question recap
    st.markdown(
        f'<div style="padding:.55rem .8rem;background:var(--surface);border:1px solid var(--border);'
        f'border-radius:4px;margin-bottom:1rem;">'
        f'<span style="font-family:var(--mono);font-size:.6rem;letter-spacing:.08em;'
        f'text-transform:uppercase;color:var(--dim)">Question: </span>'
        f'<span style="font-size:.88rem;color:var(--text)">{S.question}</span>'
        f'</div>',
        unsafe_allow_html=True,
    )

    # Scenario cards
    if S.scenarios:
        _render_scenario_cards(S.scenarios)
    else:
        st.info("No structured scenario data was returned. See the agent's explanation below.")

    # Tool chips
    _render_tool_chips(S.tool_steps)

    # Agent explanation in bordered container
    if S.reply:
        st.markdown(
            f'<div style="padding:1.1rem 1.2rem;background:var(--surface);'
            f'border:1px solid var(--border);border-radius:6px;'
            f'color:var(--text);font-size:.9rem;line-height:1.7;margin:.4rem 0 .8rem">'
            f'{S.reply}'
            f'</div>',
            unsafe_allow_html=True,
        )

    # Chart
    if S.scenarios:
        _render_chart(S.scenarios)

    # Assumptions expander
    _render_assumptions_expander()

    st.markdown('<hr>', unsafe_allow_html=True)

    # Action row
    left, right = st.columns([1, 1])
    with left:
        if st.button("← Edit profile", key="res_edit_profile"):
            S.reply      = None
            S.scenarios  = None
            S.tool_steps = []
            S.error      = None
            _go(1)
    with right:
        if st.button("Ask another question →", key="res_followup", type="primary", use_container_width=True):
            S.reply      = None
            S.scenarios  = None
            S.tool_steps = []
            S.error      = None
            S.question   = ""
            _go(2)

    _render_disclaimer()


# ─────────────────────────────────────────────────────────────────────────────
# ROUTER
# ─────────────────────────────────────────────────────────────────────────────
if   S.step == 1: render_step1()
elif S.step == 2: render_step2()
elif S.step == 3: render_step3()
