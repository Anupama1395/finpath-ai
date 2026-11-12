# FinPath AI

> Agentic financial scenario copilot built on **IBM watsonx Orchestrate**  
> IBM SkillsBuild AI Experiential Learning Lab · Banking & Financial Services

[![CI](https://github.com/Anupama1395/finpath-ai/actions/workflows/ci.yml/badge.svg)](https://github.com/Anupama1395/finpath-ai/actions/workflows/ci.yml)

---

## What it does

FinPath AI lets you describe your financial situation (income, expenses, savings, debts, goal) and asks an IBM watsonx Orchestrate agent to analyse it using deterministic Python tools. The agent never computes numbers itself — every figure comes from a verified tool call.

- **Live financial health score** (0–100) with sub-score breakdown — updates as you type, no agent call
- **Multi-turn chat** — ask follow-up questions in the same thread; the agent compares old vs new numbers
- **Tool-trace chips** — every agent reply shows which tools were called
- **10 financial tools** — cash flow, debt payoff, emergency fund, savings projections, stress test, debt-vs-invest simulation, and more

> FinPath AI provides **illustrative projections only**. It is not financial advice and never recommends specific products or securities.

---

## Repo layout

```
.github/workflows/   GitHub Actions CI (runs 148+ unit tests on every push)
agents/              ADK agent YAML definitions (finpath_agent.yaml)
agent/               orchestrate.py — thin ADK client (ask_agent + health_check)
app/
  main.py            Streamlit UI (3-step wizard + chat)
  api_client.py      ADK RunClient/ThreadsClient wrapper
data/
  profiles.json      6 synthetic sample profiles (no real PII)
docs/
  SPEC.md            Technical specification
  ARCHITECTURE.md    System design + data flow diagrams
  DEMO_SCRIPT.md     3-minute demo walkthrough
tests/
  test_finance.py    Unit tests for core math (42 tests)
  test_new_tools.py  Unit tests for new tools (71 tests)
  test_health_check.py  Unit tests for financial_health_check (35 tests)
  smoke_test.py      E2E tests (requires live Orchestrate token)
tools/
  core/finance.py    Pure Python math — no ADK imports, stdlib only
  *_tool.py          Thin @tool wrappers over tools/core/
```

---

## Setup

### Prerequisites
- Python 3.11+
- IBM watsonx Orchestrate account + API key
- `orchestrate` CLI (`pip install ibm-watsonx-orchestrate`)

### Install
```bash
git clone https://github.com/Anupama1395/finpath-ai.git
cd finpath-ai
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
```

### Configure Orchestrate
```bash
orchestrate env add finpath \
  --url "https://api.<region>.watson-orchestrate.cloud.ibm.com/instances/<id>"

orchestrate env activate finpath
# enter your IBM Cloud API key when prompted
```

### Import tools and agent
```bash
# Import all tool wrappers
for f in tools/cash_flow_tool.py tools/projections_tool.py tools/scenarios_tool.py \
          tools/debt_tool.py tools/stress_tool.py tools/savings_tool.py \
          tools/emergency_tool.py tools/health_tool.py tools/goal_tool.py \
          tools/multi_debt_tool.py; do
  orchestrate tools import --kind python --file $f \
    --package-root tools/ --requirements-file tools/requirements.txt
done

# Import agent
orchestrate agents import --file agents/finpath_agent.yaml
```

### Run
```bash
# Refresh token (required once per session, expires ~1hr)
orchestrate env activate finpath --api-key "YOUR_KEY"

# Start UI
streamlit run app/main.py
```

---

## Run tests

Unit tests require no credentials:
```bash
pytest tests/ --ignore=tests/smoke_test.py -v
```

End-to-end tests (requires live Orchestrate token):
```bash
pytest tests/smoke_test.py -v -s
```

---

## Architecture

See [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) for the full system diagram and data flow.

**Key design decisions:**
1. Pure math in `tools/core/finance.py` — zero ADK imports, fully testable offline
2. Agent never computes numbers — every figure must come from a tool call
3. Full profile prepended to every message — agent always has all inputs
4. Thread continuity — follow-up questions reuse the same Orchestrate thread

---

## Tools implemented

| Tool | What it calculates |
|---|---|
| `monthly_cash_flow` | Income − expenses − payments |
| `project_savings_growth` | Compound growth over N months |
| `compare_scenarios` | Side-by-side: cash flow, EF, savings for 2–3 scenarios |
| `emergency_fund_months` | Months of expenses covered by savings |
| `emergency_fund_check` | Status (low/ok/good) + gap to 3-month target |
| `debt_payoff_months` | Months to payoff + total interest paid |
| `debt_vs_invest` | Month-by-month: pay debt first vs invest same budget |
| `stress_test` | What-if income drop or expense spike |
| `savings_headroom` | Free cash after all commitments |
| `financial_health_check` | Score 0–100 with 4 sub-scores + priority list |
| `goal_plan` | Monthly saving needed to hit a target amount by a date |
| `multi_debt_plan` | Avalanche vs snowball comparison for multiple debts |

---

## Demo

<!-- Add demo video link here before submission -->

See [`docs/DEMO_SCRIPT.md`](docs/DEMO_SCRIPT.md) for the 3-minute walkthrough script.

---

## Built with IBM Bob

IBM Bob was used during development to make and verify the following changes (session screenshots in [`bob_sessions/`](bob_sessions/)):

- **Repo cleanup**: untracked cached `__pycache__`/`.pyc` files and `.coverage`, removed a stray `gitignore` file, and tightened `.gitignore`. All 193 existing tests still passed. ([screenshot](bob_sessions/paridhi_01_cleanup.png))
- **Rate-validation bug fix + tests**: added `_validate_rates` to `tools/core/finance.py`, so any rate > 1 (e.g. `20` instead of `0.20`) raises a clear error instead of silently computing a 2000% rate. Added 24 regression tests; 217 tests pass. ([screenshot](bob_sessions/paridhi_02_rate-validation.png))
- **Architecture docs**: added a Mermaid system diagram, a tool reference for all 12 tools, and a guardrails summary to [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md). ([screenshot](bob_sessions/paridhi_03_architecture.png))
- **README**: drafted these Built with Bob, Data sources and Responsible AI sections, grounded in the repo files.
---

## Data sources

All six profiles in [`data/profiles.json`](data/profiles.json) are fully synthetic — no real personal, client, or confidential data is used anywhere in this project. The profiles are:

| ID | Label |
|---|---|
| `recent_graduate` | Recent Graduate — Entry-level job |
| `mid_career` | Mid-career — Stable income, growing savings |
| `debt_focused` | Debt-focused — High-interest debt, limited savings |
| `student` | Student — Part-time work |
| `early_career` | Early career — First full-time job |
| `family` | Family — Dual income, one child |

All calculations are deterministic, pure Python in [`tools/core/finance.py`](tools/core/finance.py) — no external APIs, no ML inference, stdlib only.

---

## Responsible AI

- **Every number comes from a tool call.** The agent never computes, estimates, or rounds figures itself; all outputs are quoted directly from tool results (rule 1 in [`agents/finpath_agent.yaml`](agents/finpath_agent.yaml)).
- **Assumptions and defaults are always stated.** Every response lists the exact input values used, and any applied defaults (5% growth rate, 12-month horizon, 7% investment rate) are explicitly declared.
- **No product recommendations.** The agent never recommends specific financial products, securities, mutual funds, ETFs, or any buy/sell action.
- **Every reply ends with** "This is educational information, not financial advice." (rule 8 in [`agents/finpath_agent.yaml`](agents/finpath_agent.yaml)).
- **`_verify_figures()` cross-checks figures** — [`app/api_client.py`](app/api_client.py) extracts every dollar amount and percentage from the agent reply and matches them against raw tool outputs; the UI shows a ✓ verified badge on pass or a ⚠ warning on mismatch, and tool-call chips are always displayed for full transparency.
