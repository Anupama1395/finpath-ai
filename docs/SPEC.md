# FinPath AI — Technical Specification

**IBM SkillsBuild AI Experiential Learning Lab · Track 2: Banking & Financial Services**  
**Submission deadline: November 22, 2026**  
**Team size: 2**

---

## 1 · Problem Statement

People struggle to reason about multiple financial scenarios simultaneously — e.g.
"If I increase my monthly investment by $200, do I still have enough emergency cash?"
FinPath AI answers this by running 2–3 user-defined scenarios side-by-side, computing
cash-flow, emergency-fund coverage, and projected savings growth, then explaining
the tradeoffs in plain language.

> **Hard constraint:** The agent never recommends specific financial products,
> securities, or buy/sell actions. All outputs are labelled as illustrative
> projections, not financial advice. Assumptions are stated in every response.

---

## 2 · Architecture

```
Streamlit UI
    └── POST /v1/chat  (Orchestrate API, credentials from .env)
            └── finpath_agent  (native agent)
                    ├── Python tools  (thin @tool wrappers → tools/core/)
                    └── finpath_kb_agent  (knowledge agent, collaborator)
```

### 2a · Agent Roles

| Agent | Type | Responsibility |
|---|---|---|
| `finpath_agent` | Native | Orchestrates the full conversation. Decides which 2–3 scenarios to compare based on the user's goal, calls `compare_scenarios` with those scenarios, aggregates results, and delegates follow-up "why" questions to the knowledge agent. System prompt embeds the no-advice guardrail and requires all assumptions to be stated. |
| `finpath_kb_agent` | Knowledge | Collaborator only — never surfaces directly to the user. Answers with citations from the uploaded knowledge base (emergency fund rationale, compound interest, debt payoff strategies). |

### 2b · Scenario ownership

**The agent decides which scenarios to compare.** It interprets the user's goal,
forms 2–3 concrete scenario dicts (e.g. "current", "+$200/mo savings", "+$400/mo
savings"), and passes them to `compare_scenarios`. The tool never invents scenarios.

---

## 3 · Code Structure — two-layer tool design

All financial math lives in pure Python in `tools/core/` with no ADK imports.
The `@tool` functions in `tools/` are thin wrappers that import from `tools/core/`
and handle only the ADK surface (decorator, docstring, type annotations).

This separation means:
- Core math is testable with plain `pytest` — no Orchestrate dependency.
- Core logic can be iterated without re-importing tools into Orchestrate.
- `@tool` wrappers stay trivially small and easy to audit.

### 3a · Packaging for `orchestrate tools import`

The ADK's `--package-root` flag controls what gets bundled:

```bash
orchestrate tools import \
  --kind python \
  --file tools/cash_flow_tool.py \
  --package-root tools/ \
  --requirements-file tools/requirements.txt
```

When `--package-root tools/` is set, the entire `tools/` directory is uploaded
as a package. The `@tool` file can then do `from core.finance import ...` and
the `core/` sub-package is available at runtime. Each `@tool` file is imported
separately; all share the same `--package-root`.

---

## 4 · Python Modules

### `tools/core/finance.py` — pure math, no ADK

| Function | Signature | Returns |
|---|---|---|
| `emergency_fund_months` | `(savings: float, monthly_expenses: float) → float` | Months of expenses covered by current savings |
| `monthly_cash_flow` | `(income: float, expenses: float, debt_payments: float, savings_contribution: float) → float` | Net monthly surplus (negative = infeasible) |
| `project_savings_growth` | `(principal: float, monthly_contribution: float, annual_rate: float, months: int) → float` | Future value via monthly compounding |
| `compare_scenarios` | `(scenarios: list[dict]) → list[dict]` | Runs the three functions above for each scenario dict; max 3 scenarios |

### `tools/` — ADK `@tool` wrappers

- `cash_flow_tool.py` — wraps `emergency_fund_months` and `monthly_cash_flow`
- `projections_tool.py` — wraps `project_savings_growth`
- `scenarios_tool.py` — wraps `compare_scenarios`
- `requirements.txt` — no third-party deps (stdlib only for core math)

---

## 5 · Folder Structure

```
finpath-ai/
├── .venv/                      # existing venv (ibm-watsonx-orchestrate 2.20.0)
├── .env                        # secrets — never committed
├── .gitignore
├── apikey.json
├── README.md
│
├── agents/
│   ├── finpath_agent.yaml
│   └── finpath_kb_agent.yaml
│
├── tools/
│   ├── __init__.py
│   ├── requirements.txt         # used with --requirements-file flag
│   ├── cash_flow_tool.py        # @tool wrappers: emergency_fund_months, monthly_cash_flow
│   ├── projections_tool.py      # @tool wrapper: project_savings_growth
│   ├── scenarios_tool.py        # @tool wrapper: compare_scenarios
│   └── core/
│       ├── __init__.py
│       └── finance.py           # all math — no ADK imports
│
├── tests/
│   ├── test_finance.py          # tests against tools/core/finance.py only
│   └── conftest.py
│
├── knowledge/
│   ├── emergency_fund_guide.txt
│   ├── compound_interest.txt
│   └── debt_payoff_strategies.txt
│
├── data/
│   └── profiles/
│       ├── profile_student.json
│       ├── profile_earlycareer.json
│       └── profile_family.json
│
├── frontend/
│   ├── app.py
│   ├── api_client.py
│   └── components/
│       ├── scenario_form.py
│       └── results_table.py
│
└── docs/
    ├── SPEC.md                  # this file
    ├── architecture.md
    └── demo_script.md
```

---

## 6 · Data & Secrets

- **User data:** Synthetic profiles only — no real PII. Three sample profiles in `data/profiles/`.
- **Secrets:** `WATSONX_ORCHESTRATE_API_KEY`, `WATSONX_ORCHESTRATE_URL`, `WATSONX_ORCHESTRATE_ENV` in `.env`. Already in `.gitignore`. Never read or printed at runtime.
- **Knowledge base docs:** 2–4 short plain-text explainers. Imported via `orchestrate knowledge-bases import`.

---

## 7 · Agent System Prompt (required guardrails)

```
You are FinPath AI, a financial scenario modelling assistant.

Rules you must follow in every response:
1. You do not recommend specific financial products, securities, funds,
   or any buy/sell action. If asked, decline and explain why.
2. Every response that contains numbers must explicitly state the
   assumptions used (income, expenses, interest rate, time horizon).
3. All projections are illustrative only and based entirely on the
   user-supplied figures. They are not financial advice.
4. You decide which 2–3 scenarios to compare based on the user's stated
   goal, form the scenario parameters, and call compare_scenarios with them.
   Do not ask the user to supply pre-formed scenario dicts.
5. After presenting numbers, invite the user to adjust any assumption.
```

---

## 8 · Ordered Task List

| # | Task | Artifact | Done-when |
|---|---|---|---|
| 1 | **Scaffold repo** — create all folders, placeholder files, README skeleton | folder tree | `git status` clean |
| 2 | **Core math** — implement `tools/core/finance.py`; write `tests/test_finance.py` | `.py` files | `pytest` green, ≥ 90% line coverage |
| 3 | **@tool wrappers** — implement the three `tools/*_tool.py` files with ADK decorators | `.py` files | files lint-clean; wrappers call core correctly |
| 4 | **Import tools into Orchestrate** — `orchestrate tools import --kind python --package-root tools/` for each wrapper | Orchestrate env | `orchestrate tools list` shows all four tools |
| 5 | **Author agent YAMLs** — `finpath_agent` (native) and `finpath_kb_agent` | `agents/*.yaml` | files validate against ADK schema |
| 6 | **Upload knowledge base** — ingest three explainer docs | Orchestrate env | `orchestrate knowledge-bases status` → READY |
| 7 | **Import agents** — push both YAMLs; smoke-test via `orchestrate chat` | Orchestrate env | both agents listed; single turn returns tool-backed response |
| 8 | **Streamlit frontend** — input form, API client, scenario results table | `frontend/` | app runs locally; 2-scenario comparison renders correctly |
| 9 | **Synthetic profiles** — 3 JSON profiles; wire "load profile" in UI | `data/profiles/` | each profile pre-fills form; demo flow works end-to-end |
| 10 | **End-to-end integration** — full scenario comparison against live Orchestrate API; verify traces | observability | all tools invoked; no product recommendations in output |
| 11 | **Demo script** — 3-minute judge walkthrough | `docs/demo_script.md` | rehearsed; fits in 3 min |
| 12 | **README & repo cleanup** — finalise README (problem, setup steps, run instructions, repo layout), remove debug artefacts, tag release | `README.md` | repo is submission-ready; link in README to demo video |

---

## 9 · Key Constraints Summary

- All math is **deterministic** — no LLM-generated numbers; the LLM only interprets tool outputs.
- Annual interest rate defaults to **5% p.a.** only when the user omits it; the assumption is always stated.
- `compare_scenarios` accepts a maximum of **3 scenarios** per call; raises `ValueError` on invalid input.
- `.env` is never read or printed at runtime; credentials only accessed via the ADK environment context.
- No real user data anywhere in the repo.
- Submission artefacts: demo video, written statements, GitHub repo link.
