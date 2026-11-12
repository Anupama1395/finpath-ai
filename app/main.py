"""
app/main.py
-----------
FinPath AI — Streamlit frontend (Concept 4: wizard flow).

Steps:
  1  Profile   — pick a sample or enter manually
  2  Question  — type the goal/question
  3  Results   — scenario cards, tool trace, chart, assumptions

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
# PAGE CONFIG
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="FinPath AI",
    page_icon="💰",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# ─────────────────────────────────────────────────────────────────────────────
# CSS — dark portfolio theme
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
/* ── fonts via Google Fonts (stylesheet link blocked; fallback stack used) ── */
:root{
  --night:   #07080c;
  --night-2: #0c0e14;
  --night-3: #131620;
  --ivory:   #f4f1ea;
  --dim:     rgba(244,241,234,.52);
  --dim-2:   rgba(244,241,234,.30);
  --hair:    rgba(244,241,234,.09);
  --red:     #e2492a;
  --gold:    #d9a441;
  --ice:     #8fb8c9;
  --green:   #5cb87a;
  --serif:   Georgia,"Times New Roman",serif;
  --sans:    -apple-system,"Segoe UI",system-ui,sans-serif;
  --mono:    "Courier New",Courier,monospace;
}

html, body, [class*="css"]{
  font-family: var(--sans) !important;
  -webkit-font-smoothing: antialiased;
}
.stApp{
  background: var(--night) !important;
  color: var(--ivory) !important;
}
header[data-testid="stHeader"], footer, #MainMenu{ display:none !important; }

/* centre the content column */
.block-container{
  max-width: 740px !important;
  padding-top: 2.4rem !important;
  padding-bottom: 3rem !important;
}

/* ── wordmark ── */
.fp-wordmark{
  font: italic 400 clamp(2rem,5vw,3.2rem)/.9 var(--serif);
  text-transform: uppercase;
  letter-spacing: -.02em;
  color: var(--ivory);
  margin: 0 0 .2rem;
}
.fp-wordmark em{ font-style:normal; color:var(--red); }
.fp-tagline{
  font-family: var(--mono);
  font-size: .68rem;
  letter-spacing: .12em;
  text-transform: uppercase;
  color: var(--dim-2);
  margin-bottom: 2rem;
}

/* ── step indicator ── */
.fp-steps{
  display: flex;
  align-items: center;
  gap: 0;
  margin-bottom: 2.2rem;
}
.fp-step{
  display: flex;
  align-items: center;
  gap: .45rem;
  font-family: var(--mono);
  font-size: .62rem;
  letter-spacing: .08em;
  text-transform: uppercase;
  color: var(--dim-2);
  white-space: nowrap;
}
.fp-step .dot{
  width: 22px; height: 22px;
  border-radius: 50%;
  border: 1px solid var(--hair);
  display: flex; align-items: center; justify-content: center;
  font-size: .7rem; flex-shrink: 0;
}
.fp-step.done .dot{ background:var(--red); border-color:var(--red); color:#fff; }
.fp-step.active .dot{ border-color:var(--ivory); color:var(--ivory); }
.fp-step.active{ color:var(--ivory); }
.fp-conn{ flex:1; height:1px; background:var(--hair); margin:0 .5rem; min-width:16px; }

/* ── step card ── */
.fp-card{
  background: var(--night-2);
  border: 1px solid var(--hair);
  border-radius: 8px;
  padding: 1.8rem 2rem;
}
.fp-card h2{
  font: italic 400 1.7rem/1.1 var(--serif);
  margin: 0 0 .35rem;
  color: var(--ivory);
}
.fp-card h2 em{ font-style:normal; color:var(--red); }
.fp-card .fp-card-sub{
  font-family: var(--mono);
  font-size: .62rem;
  letter-spacing: .08em;
  text-transform: uppercase;
  color: var(--dim-2);
  margin-bottom: 1.4rem;
}

/* ── profile chips ── */
.fp-profile-chips{
  display: flex;
  flex-wrap: wrap;
  gap: .5rem;
  margin-bottom: 1.2rem;
}
.fp-chip{
  font-family: var(--mono);
  font-size: .68rem;
  letter-spacing: .06em;
  padding: .38rem .85rem;
  border: 1px solid var(--hair);
  border-radius: 3px;
  background: var(--night-3);
  color: var(--dim);
  cursor: pointer;
  transition: border-color .18s, color .18s;
}
.fp-chip:hover{ border-color:var(--red); color:var(--ivory); }
.fp-chip.active{ border-color:var(--red); color:var(--ivory); background:rgba(226,73,42,.08); }

/* ── step actions bar ── */
.fp-actions{
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 1.6rem;
  padding-top: 1.2rem;
  border-top: 1px solid var(--hair);
}

/* ── ALL Streamlit buttons: dark base ── */
.stButton button{
  background: var(--night-3) !important;
  border: 1px solid var(--hair) !important;
  color: var(--ivory) !important;
  font-family: var(--mono) !important;
  font-size: .68rem !important;
  letter-spacing: .08em !important;
  text-transform: uppercase !important;
  border-radius: 3px !important;
  padding: .45rem 1.2rem !important;
  transition: background .18s, border-color .18s, color .18s !important;
}
.stButton button:hover{
  background: var(--night-2) !important;
  border-color: var(--dim-2) !important;
  color: var(--ivory) !important;
}
/* primary action button */
.btn-pri .stButton button,
.fp-card .stButton.btn-pri button{
  background: var(--red) !important;
  border-color: var(--red) !important;
  color: #fff !important;
}
.btn-pri .stButton button:hover,
.fp-card .stButton.btn-pri button:hover{
  background: #c73e23 !important;
  border-color: #c73e23 !important;
}
/* secondary action button */
.btn-sec .stButton button,
.fp-card .stButton.btn-sec button{
  background: transparent !important;
  border-color: var(--hair) !important;
  color: var(--dim) !important;
}
.btn-sec .stButton button:hover,
.fp-card .stButton.btn-sec button:hover{
  border-color: var(--ivory) !important;
  color: var(--ivory) !important;
}
/* selected profile chip: gold border + subtle tint */
.chip-active .stButton button{
  border-color: var(--gold) !important;
  color: var(--gold) !important;
  background: rgba(217,164,65,.10) !important;
}

/* ── inputs & labels inside card ── */
/* label text: raise contrast from dim-2 to dim */
.fp-card label,
.fp-card .stSlider label,
.fp-card .stNumberInput label,
.fp-card .stTextArea label{
  font-family: var(--mono) !important;
  font-size: .65rem !important;
  letter-spacing: .08em !important;
  text-transform: uppercase !important;
  color: var(--dim) !important;
}
/* number / text inputs: dark background, ivory text */
.fp-card [data-baseweb="base-input"],
.fp-card [data-baseweb="input"]{
  background: var(--night-3) !important;
  border-color: rgba(244,241,234,.18) !important;
}
.fp-card [data-baseweb="base-input"] input,
.fp-card [data-baseweb="input"] input{
  background: var(--night-3) !important;
  color: var(--ivory) !important;
  font-family: var(--mono) !important;
  caret-color: var(--red) !important;
}
/* textarea */
.fp-card textarea,
.fp-card .stTextArea textarea{
  background: var(--night-3) !important;
  color: var(--ivory) !important;
  border-color: rgba(244,241,234,.18) !important;
  font-family: var(--sans) !important;
}
/* number-input stepper arrows */
.fp-card [data-baseweb="base-input"] button{
  background: var(--night-3) !important;
  color: var(--dim) !important;
  border-color: rgba(244,241,234,.12) !important;
  font-size: .8rem !important;
  letter-spacing: normal !important;
  text-transform: none !important;
  padding: .2rem .5rem !important;
}
/* slider track & thumb accent */
.fp-card .stSlider [data-baseweb="slider"] [role="slider"]{
  background: var(--red) !important;
  border-color: var(--red) !important;
}

/* ── scenario result cards ── */
.fp-scenarios{
  display: grid;
  grid-template-columns: repeat(3,1fr);
  gap: .6rem;
  margin: 1.2rem 0 .6rem;
}
.fp-sc{
  background: var(--night-2);
  border: 1px solid var(--hair);
  border-radius: 6px;
  overflow: hidden;
}
.fp-sc.highlighted{
  border-color: var(--gold);
  box-shadow: 0 0 0 1px var(--gold);
}
.fp-sc-head{
  padding: .5rem .8rem;
  background: var(--night-3);
  border-bottom: 1px solid var(--hair);
  font-family: var(--mono);
  font-size: .58rem;
  letter-spacing: .1em;
  text-transform: uppercase;
  color: var(--dim-2);
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.fp-sc.highlighted .fp-sc-head{ color:var(--gold); }
.fp-sc-body{ padding: .85rem .9rem; }
.fp-sc-metric{ margin-bottom: .65rem; }
.fp-sc-metric:last-child{ margin-bottom:0; }
.fp-sc-metric .ml{
  font-family: var(--mono);
  font-size: .55rem;
  letter-spacing: .1em;
  text-transform: uppercase;
  color: var(--dim-2);
  margin-bottom: .18rem;
}
.fp-sc-metric .mv{
  font: 600 1.15rem/1 var(--sans);
  color: var(--ivory);
}
.fp-sc-metric .mv.pos{ color:var(--green); }
.fp-sc-metric .mv.neg{ color:var(--red); }
.fp-badge{
  display: inline-block;
  margin-top: .3rem;
  font-family: var(--mono);
  font-size: .54rem;
  letter-spacing: .07em;
  text-transform: uppercase;
  padding: .15rem .45rem;
  border-radius: 2px;
}
.fp-badge.ok{ background:rgba(92,184,122,.12); color:var(--green); border:1px solid rgba(92,184,122,.28); }
.fp-badge.bad{ background:rgba(226,73,42,.12); color:var(--red); border:1px solid rgba(226,73,42,.28); }
.fp-badge.best{ background:rgba(217,164,65,.12); color:var(--gold); border:1px solid rgba(217,164,65,.28); }

/* ── tool trace row ── */
.fp-trace{
  margin: 1rem 0;
  padding: .8rem 1rem;
  background: var(--night-2);
  border: 1px solid var(--hair);
  border-radius: 6px;
}
.fp-trace-title{
  font-family: var(--mono);
  font-size: .6rem;
  letter-spacing: .12em;
  text-transform: uppercase;
  color: var(--dim-2);
  margin-bottom: .7rem;
}
.fp-trace-steps{
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: .35rem;
}
.fp-trace-step{
  display: flex;
  align-items: center;
  gap: .3rem;
  font-family: var(--mono);
  font-size: .66rem;
  color: var(--ice);
  background: var(--night-3);
  border: 1px solid var(--hair);
  border-radius: 3px;
  padding: .28rem .6rem;
}
.fp-trace-step .tn{ color:var(--gold); }
.fp-trace-arrow{ color:var(--dim-2); font-size:.7rem; }

/* ── assumptions strip ── */
.fp-assumptions{
  padding: .65rem .9rem;
  font-family: var(--mono);
  font-size: .67rem;
  color: var(--dim-2);
  letter-spacing: .04em;
  display: flex;
  flex-wrap: wrap;
  gap: .3rem 1.4rem;
  border-top: 1px solid var(--hair);
  margin-top: .4rem;
}
.fp-assumptions b{ color:var(--gold); font-weight:500; }

/* ── agent explanation text ── */
.fp-explanation{
  color: var(--dim);
  font-size: .9rem;
  line-height: 1.65;
  margin: 1rem 0 .4rem;
}

/* ── markdown tables in explanation ── */
.stMarkdown table{
  width:100%; border-collapse:collapse; font-size:.85rem; margin:.6rem 0;
}
.stMarkdown th{
  background:var(--night-3); color:var(--dim);
  font-family:var(--mono); font-size:.62rem; letter-spacing:.08em; text-transform:uppercase;
  padding:.5rem .8rem; border:1px solid var(--hair);
}
.stMarkdown td{ padding:.5rem .8rem; border:1px solid var(--hair); color:var(--ivory); }
.stMarkdown tr:nth-child(even) td{ background:rgba(255,255,255,.02); }

/* ── disclaimer ── */
.fp-disclaimer{
  font-family: var(--mono);
  font-size: .65rem;
  letter-spacing: .05em;
  color: var(--dim-2);
  border-left: 2px solid var(--red);
  padding-left: .7rem;
  margin-top: 2rem;
}

/* ── start over link ── */
.fp-restart{
  font-family: var(--mono);
  font-size: .62rem;
  letter-spacing: .08em;
  text-transform: uppercase;
  color: var(--dim-2);
  cursor: pointer;
  text-decoration: none;
  border-bottom: 1px solid var(--hair);
  padding-bottom: 1px;
}

/* ── chart background ── */
.vega-embed{ background:transparent !important; }
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

# ─────────────────────────────────────────────────────────────────────────────
# SESSION STATE
# ─────────────────────────────────────────────────────────────────────────────
def _init_state() -> None:
    defaults = {
        "step": 1,                  # 1 | 2 | 3
        "profile": None,            # selected profile dict or None (manual)
        "income":    5000,
        "expenses":  3000,
        "savings":   6000,
        "debt_bal":  10000,
        "debt_rate": 6.0,
        "goal":      "",
        "question":  "",
        "reply":     None,          # agent reply text
        "scenarios": None,          # list[dict] | None
        "tool_steps": [],           # list[str] — tool names in call order
        "thread_id": None,
        "error":     None,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

_init_state()
S = st.session_state   # shorthand


# ─────────────────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────────────────
def _go(step: int) -> None:
    S.step = step
    st.rerun()


def _load_profile(p: dict) -> None:
    S.profile   = p
    S.income    = p["monthly_income"]
    S.expenses  = p["monthly_expenses"]
    S.savings   = p["cash_savings"]
    S.debt_bal  = p["debt_balance"]
    S.debt_rate = p["debt_rate"] * 100
    S.goal      = p["savings_goal"]


def _build_context() -> str:
    monthly_interest = round(S.debt_bal * (S.debt_rate / 100) / 12, 2)
    return (
        f"User profile:\n"
        f"- Monthly take-home income: ${S.income:,}\n"
        f"- Monthly essential expenses: ${S.expenses:,}\n"
        f"- Current cash savings: ${S.savings:,}\n"
        f"- Debt balance: ${S.debt_bal:,} at {S.debt_rate:.2f}% p.a. "
        f"(est. monthly interest: ${monthly_interest:,})\n"
        f"- Stated goal: {S.goal}\n\n"
        f"Question: {S.question}"
    )


def _extract_tool_steps(thread_id: str) -> list[str]:
    """Fetch the last assistant message's step_history and return tool names in order."""
    try:
        from ibm_watsonx_orchestrate.client.threads.threads_client import ThreadsClient
        from ibm_watsonx_orchestrate.client.utils import instantiate_client
        threads_client = instantiate_client(ThreadsClient)
        msgs_response  = threads_client.get_thread_messages(thread_id)
        messages = (
            msgs_response if isinstance(msgs_response, list)
            else msgs_response.get("data", []) if isinstance(msgs_response, dict)
            else []
        )
        for msg in reversed(messages):
            if isinstance(msg, dict) and msg.get("role") == "assistant":
                steps: list[str] = []
                for step in msg.get("step_history", []):
                    for detail in step.get("step_details", []):
                        if detail.get("type") == "tool_calls":
                            for tc in detail.get("tool_calls", []):
                                name = tc.get("name") or tc.get("function", {}).get("name", "")
                                if name:
                                    steps.append(name)
                return steps
    except Exception:
        _log.debug("Could not extract tool steps", exc_info=True)
    return []


def _pick_highlighted(scenarios: list[dict]) -> int:
    """Return the index of the scenario the agent most likely highlighted.

    Heuristic: the feasible scenario with the highest savings contribution
    that still has a non-negative cash_flow. Falls back to index 0.
    """
    feasible = [
        (i, s) for i, s in enumerate(scenarios) if s.get("feasible")
    ]
    if not feasible:
        return 0
    # highest savings_contribution among feasible
    best_i, _ = max(feasible, key=lambda x: x[1].get("savings_contribution", 0))
    return best_i


# ─────────────────────────────────────────────────────────────────────────────
# STEP INDICATOR
# ─────────────────────────────────────────────────────────────────────────────
STEP_LABELS = ["Profile", "Question", "Results"]

def _render_step_indicator(current: int) -> None:
    parts: list[str] = []
    for i, label in enumerate(STEP_LABELS, start=1):
        if i < current:
            cls = "done"
            dot = "✓"
        elif i == current:
            cls = "active"
            dot = str(i)
        else:
            cls = ""
            dot = str(i)
        parts.append(
            f'<div class="fp-step {cls}">'
            f'<div class="dot">{dot}</div>{label}</div>'
        )
        if i < len(STEP_LABELS):
            parts.append('<div class="fp-conn"></div>')
    st.markdown(
        f'<div class="fp-steps">{"".join(parts)}</div>',
        unsafe_allow_html=True,
    )


# ─────────────────────────────────────────────────────────────────────────────
# WORDMARK (shown on every step)
# ─────────────────────────────────────────────────────────────────────────────
def _render_wordmark() -> None:
    st.markdown(
        '<p class="fp-wordmark">Fin<em>Path</em> AI</p>'
        '<p class="fp-tagline">IBM SkillsBuild · Banking &amp; Financial Services · Track 2</p>',
        unsafe_allow_html=True,
    )


# ─────────────────────────────────────────────────────────────────────────────
# DISCLAIMER (shown on every step)
# ─────────────────────────────────────────────────────────────────────────────
def _render_disclaimer() -> None:
    st.markdown(
        '<p class="fp-disclaimer">Educational tool · Not financial advice · '
        'All projections are illustrative and based on the figures you supply.</p>',
        unsafe_allow_html=True,
    )


# ─────────────────────────────────────────────────────────────────────────────
# STEP 1 — PROFILE
# ─────────────────────────────────────────────────────────────────────────────
def render_step1() -> None:
    _render_wordmark()
    _render_step_indicator(1)

    st.markdown(
        '<div class="fp-card">'
        '<h2>Your <em>profile</em></h2>'
        '<p class="fp-card-sub">Step 1 of 3 · Select a sample or enter your own figures</p>',
        unsafe_allow_html=True,
    )

    # Profile chips — rendered as buttons in a horizontal row via columns.
    # Wrap each column in a div so .chip-active CSS can target the button inside.
    cols = st.columns(len(PROFILES) + 1)
    with cols[0]:
        manual_active = S.profile is None
        if manual_active:
            st.markdown('<div class="chip-active">', unsafe_allow_html=True)
        if st.button("Manual entry", key="chip_manual"):
            S.profile = None
            st.rerun()
        if manual_active:
            st.markdown('</div>', unsafe_allow_html=True)
    for idx, p in enumerate(PROFILES):
        with cols[idx + 1]:
            is_active = S.profile is not None and S.profile["id"] == p["id"]
            label = p['label'].split('—')[0].strip()
            if is_active:
                st.markdown('<div class="chip-active">', unsafe_allow_html=True)
            if st.button(label, key=f"chip_{p['id']}"):
                _load_profile(p)
                st.rerun()
            if is_active:
                st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("---")

    # Show which profile is loaded
    if S.profile:
        st.markdown(
            f'<p style="font-family:var(--mono);font-size:.65rem;letter-spacing:.06em;'
            f'color:var(--gold);margin-bottom:.8rem">'
            f'Loaded: {S.profile["label"]}</p>',
            unsafe_allow_html=True,
        )

    # Editable fields
    col_a, col_b = st.columns(2)
    with col_a:
        S.income   = st.number_input("Monthly income ($)",   min_value=0, step=100,  value=int(S.income),   key="in_income")
        S.savings  = st.number_input("Cash savings ($)",     min_value=0, step=500,  value=int(S.savings),  key="in_savings")
        S.debt_bal = st.number_input("Debt balance ($)",     min_value=0, step=1000, value=int(S.debt_bal), key="in_debt_bal")
    with col_b:
        S.expenses  = st.number_input("Monthly expenses ($)", min_value=0, step=100, value=int(S.expenses),  key="in_expenses")
        S.debt_rate = st.slider("Debt rate (%)", 0.0, 30.0, float(S.debt_rate), step=0.25, key="in_debt_rate")

    S.goal = st.text_area("Savings / investment goal", value=S.goal, height=76, key="in_goal")

    st.markdown('<div class="fp-actions">', unsafe_allow_html=True)
    _, right = st.columns([3, 1])
    with right:
        st.markdown('<div class="btn-pri">', unsafe_allow_html=True)
        if st.button("Next →", key="step1_next", use_container_width=True,
                     disabled=(S.income == 0 or S.expenses == 0)):
            _go(2)
        st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)  # close fp-card
    _render_disclaimer()


# ─────────────────────────────────────────────────────────────────────────────
# STEP 2 — QUESTION
# ─────────────────────────────────────────────────────────────────────────────
def render_step2() -> None:
    _render_wordmark()
    _render_step_indicator(2)

    st.markdown(
        '<div class="fp-card">'
        '<h2>Your <em>question</em></h2>'
        '<p class="fp-card-sub">Step 2 of 3 · Ask about your financial scenarios</p>',
        unsafe_allow_html=True,
    )

    # Profile summary strip
    st.markdown(
        f'<div style="display:flex;gap:1.5rem;flex-wrap:wrap;margin-bottom:1rem;'
        f'font-family:var(--mono);font-size:.65rem;color:var(--dim-2);">'
        f'<span>Income: <b style="color:var(--ivory)">${S.income:,}</b></span>'
        f'<span>Expenses: <b style="color:var(--ivory)">${S.expenses:,}</b></span>'
        f'<span>Savings: <b style="color:var(--ivory)">${S.savings:,}</b></span>'
        f'<span>Debt: <b style="color:var(--ivory)">${S.debt_bal:,}</b></span>'
        f'</div>',
        unsafe_allow_html=True,
    )

    suggestion = S.goal if S.goal else "Can I increase my monthly savings and still keep enough emergency cash?"
    S.question = st.text_area(
        "What do you want to know?",
        value=S.question or suggestion,
        height=100,
        key="in_question",
    )

    st.markdown('<div class="fp-actions">', unsafe_allow_html=True)
    left, right = st.columns([1, 1])
    with left:
        st.markdown('<div class="btn-sec">', unsafe_allow_html=True)
        if st.button("← Back", key="step2_back", use_container_width=True):
            _go(1)
        st.markdown('</div>', unsafe_allow_html=True)
    with right:
        st.markdown('<div class="btn-pri">', unsafe_allow_html=True)
        if st.button("Run scenarios →", key="step2_run", use_container_width=True,
                     disabled=not S.question.strip()):
            # Reset previous results
            S.reply     = None
            S.scenarios = None
            S.tool_steps = []
            S.error     = None
            _go(3)
        st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)  # close fp-card
    _render_disclaimer()


# ─────────────────────────────────────────────────────────────────────────────
# STEP 3 — RESULTS
# ─────────────────────────────────────────────────────────────────────────────
def _render_scenario_cards(scenarios: list[dict]) -> None:
    highlighted = _pick_highlighted(scenarios)

    cards_html = '<div class="fp-scenarios">'
    for i, s in enumerate(scenarios):
        cf  = s.get("cash_flow", 0)
        ef  = s.get("emergency_fund_months", 0)
        ps  = s.get("projected_savings", 0)
        ok  = s.get("feasible", False)
        is_best = (i == highlighted)

        sc_cls   = "fp-sc highlighted" if is_best else "fp-sc"
        cf_cls   = "mv pos" if cf >= 0 else "mv neg"
        bdg_cls  = "fp-badge best" if is_best and ok else ("fp-badge ok" if ok else "fp-badge bad")
        bdg_text = "Recommended" if is_best and ok else ("Feasible" if ok else "Infeasible")
        star     = ' <span style="color:var(--gold)">★</span>' if is_best else ""

        cards_html += f"""
<div class="{sc_cls}">
  <div class="fp-sc-head">{s.get('label','—')}{star}</div>
  <div class="fp-sc-body">
    <div class="fp-sc-metric">
      <div class="ml">Monthly surplus</div>
      <div class="{cf_cls}">${cf:,.0f}</div>
      <span class="{bdg_cls}">{bdg_text}</span>
    </div>
    <div class="fp-sc-metric">
      <div class="ml">Emergency fund</div>
      <div class="mv">{ef:.1f} <span style="font-size:.8rem;color:var(--dim-2)">mo</span></div>
    </div>
    <div class="fp-sc-metric">
      <div class="ml">Projected (12 mo)</div>
      <div class="mv">${ps:,.0f}</div>
    </div>
  </div>
</div>"""
    cards_html += '</div>'
    st.markdown(cards_html, unsafe_allow_html=True)


def _render_tool_trace(tool_steps: list[str]) -> None:
    if not tool_steps:
        return
    steps_html = ""
    for idx, name in enumerate(tool_steps):
        if idx > 0:
            steps_html += '<span class="fp-trace-arrow">›</span>'
        steps_html += (
            f'<div class="fp-trace-step">'
            f'<span style="color:var(--dim-2);font-size:.58rem">{idx+1}.</span>'
            f'<span class="tn">{name}()</span>'
            f'</div>'
        )
    st.markdown(
        f'<div class="fp-trace">'
        f'<div class="fp-trace-title">How FinPath worked this out</div>'
        f'<div class="fp-trace-steps">{steps_html}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )


def _render_chart(scenarios: list[dict]) -> None:
    import pandas as pd
    import altair as alt

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
                labelAngle=0, labelColor="#8fb8c9", tickColor="rgba(0,0,0,0)",
                domainColor="rgba(255,255,255,.1)", labelFontSize=10)),
            y=alt.Y("Value:Q", axis=alt.Axis(
                labelColor="#8fb8c9", gridColor="rgba(255,255,255,.06)",
                tickColor="rgba(0,0,0,0)", domainColor="rgba(0,0,0,0)", labelFontSize=10)),
            color=alt.Color("Scenario:N",
                scale=alt.Scale(range=["#e2492a", "#d9a441", "#8fb8c9"]),
                legend=alt.Legend(labelColor="#f4f1ea", titleColor="#f4f1ea", labelFontSize=11)),
            facet=alt.Facet("Metric:N", columns=3,
                header=alt.Header(labelColor="#8fb8c9", labelFontSize=10, labelPadding=8)),
            tooltip=["Scenario:N", "Metric:N", alt.Tooltip("Value:Q", format=",.2f")],
        )
        .properties(width=190, height=150)
        .resolve_scale(y="independent")
        .configure_view(strokeOpacity=0, fill="#0c0e14")
        .configure(background="#07080c")
    )
    st.altair_chart(chart, use_container_width=True)


def _render_assumptions(scenarios: list[dict]) -> None:
    s0 = scenarios[0]
    rate_pct = s0.get("assumed_annual_rate", 0.05) * 100
    months   = s0.get("assumed_months", 12)
    with st.expander("Assumptions"):
        st.markdown(
            f'<div class="fp-assumptions">'
            f'<span>Annual growth rate: <b>{rate_pct:.1f}% p.a.</b></span>'
            f'<span>Projection horizon: <b>{months} months</b></span>'
            f'<span>Monthly compound interest</span>'
            f'<span>3–6 mo emergency fund = conventional guideline, not a recommendation</span>'
            f'<span>Income / expenses as entered in Step 1</span>'
            f'</div>',
            unsafe_allow_html=True,
        )


def render_step3() -> None:
    _render_wordmark()
    _render_step_indicator(3)

    # ── If results not yet fetched, run the agent ─────────────────────────────
    if S.reply is None and S.error is None:
        with st.spinner("FinPath AI is running your scenarios…"):
            try:
                reply, scenarios, new_thread_id = ask_agent(
                    _build_context(),
                    thread_id=S.thread_id,
                )
                S.reply      = reply
                S.scenarios  = scenarios
                S.thread_id  = new_thread_id
                if new_thread_id:
                    S.tool_steps = _extract_tool_steps(new_thread_id)
            except (RuntimeError, TimeoutError) as exc:
                S.error = str(exc)
            except Exception as exc:
                S.error = "An unexpected error occurred. Check that your Orchestrate environment is active."
                _log.debug("Agent call failed", exc_info=True)
        st.rerun()   # rerun once results are stored to render cleanly

    # ── Error state ───────────────────────────────────────────────────────────
    if S.error:
        st.markdown(
            '<div class="fp-card">'
            '<h2>Something went <em>wrong</em></h2>'
            '<p class="fp-card-sub">Step 3 of 3</p>',
            unsafe_allow_html=True,
        )
        st.error(S.error)
        left, right = st.columns([1, 1])
        with left:
            if st.button("← Back to question", key="err_back"):
                S.error = None
                _go(2)
        with right:
            if st.button("↺ Start over", key="err_restart"):
                for k in list(st.session_state.keys()):
                    del st.session_state[k]
                st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
        _render_disclaimer()
        return

    # ── Results ───────────────────────────────────────────────────────────────
    st.markdown(
        '<div class="fp-card">'
        '<h2>Your <em>results</em></h2>'
        '<p class="fp-card-sub">Step 3 of 3 · Illustrative projections — not financial advice</p>',
        unsafe_allow_html=True,
    )

    # Question recap
    st.markdown(
        f'<div style="font-family:var(--mono);font-size:.66rem;color:var(--dim-2);'
        f'border-left:2px solid var(--hair);padding-left:.7rem;margin-bottom:1rem;">'
        f'<em style="color:var(--dim)">{S.question}</em></div>',
        unsafe_allow_html=True,
    )

    # Scenario cards
    if S.scenarios:
        _render_scenario_cards(S.scenarios)
    else:
        st.info("No structured scenario data was returned. See the agent's explanation below.")

    # Tool trace
    _render_tool_trace(S.tool_steps)

    # Agent explanation
    if S.reply:
        st.markdown(
            f'<div class="fp-explanation">{S.reply}</div>',
            unsafe_allow_html=True,
        )

    # Chart + assumptions
    if S.scenarios:
        _render_chart(S.scenarios)
        _render_assumptions(S.scenarios)

    # Action row
    st.markdown('<div class="fp-actions">', unsafe_allow_html=True)
    left, mid, right = st.columns([1, 1, 1])
    with left:
        if st.button("← Edit question", key="res_back"):
            S.reply     = None
            S.scenarios = None
            S.tool_steps = []
            S.error     = None
            _go(2)
    with mid:
        if st.button("↺ New profile", key="res_restart"):
            for k in list(st.session_state.keys()):
                del st.session_state[k]
            st.rerun()
    with right:
        if st.button("Ask follow-up →", key="res_followup"):
            S.reply     = None
            S.scenarios = None
            S.tool_steps = []
            S.error     = None
            S.question  = ""
            _go(2)
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)  # close fp-card
    _render_disclaimer()


# ─────────────────────────────────────────────────────────────────────────────
# ROUTER
# ─────────────────────────────────────────────────────────────────────────────
if   S.step == 1: render_step1()
elif S.step == 2: render_step2()
elif S.step == 3: render_step3()
