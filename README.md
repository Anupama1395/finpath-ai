# FinPath AI

Agentic financial scenario copilot built on IBM watsonx Orchestrate.

**IBM SkillsBuild AI Experiential Learning Lab · Track 2: Banking & Financial Services**

## Problem

People struggle to reason about multiple financial scenarios at once.
FinPath AI lets a user supply their income, expenses, savings, debts, and a goal,
then compares 2–3 scenarios side-by-side — showing cash flow, emergency-fund
coverage, and projected savings growth — with plain-language tradeoff explanations.

> FinPath AI provides **illustrative projections only**. It is not financial advice
> and never recommends specific products or securities.

## Repo layout

```
agents/          ADK agent YAML definitions
data/profiles/   Synthetic user profiles (no real PII)
docs/            SPEC.md, demo_script.md, architecture.md
frontend/        Streamlit UI
knowledge/       Plain-text docs ingested into the knowledge base
tests/           pytest test suite (tests tools/core/ only)
tools/
  core/          Pure Python math — no ADK imports
  *_tool.py      Thin @tool wrappers over tools/core/
```

## Setup

```bash
python -m venv venv && source venv/bin/activate
pip install ibm-watsonx-orchestrate   # already present in ./venv
cp .env.example .env                  # fill in your credentials
```

## Run tests

```bash
pytest tests/ -v --tb=short
```

## Run the UI

```bash
streamlit run frontend/app.py
```

## Demo video

<!-- link added at submission -->
