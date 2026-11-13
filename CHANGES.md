# FinPath AI: Change Log (Paridhi → Anupama)

Hi Anupama! 👋 This file tracks every change I'm making on branch **`paridhi/bob-docs`**: what changed, **why**, and how I checked it. Each change was made in **IBM Bob IDE**, and its session screenshot is in `bob_sessions/`. Please review the draft PR and leave comments on anything you'd like done differently. Nothing touches your agent logic without us agreeing first.

**Why this branch exists:** the submission requires (1) Bob session reports from *each* member in the repo, (2) a working prototype link, and (3) written problem/solution and technology statements. The code itself is in great shape (193 tests passing, 99% coverage on `tools/core`). These changes are polish, one bug fix, and the submission requirements.

| # | Change | Status | Bob screenshot |
|---|--------|--------|----------------|
| 1 | Repo cleanup | ✅ done | `paridhi_01_cleanup.png` |
| 2 | Rate validation (percent vs. decimal bug) | ✅ done | `paridhi_02_rate-validation.png` |
| 3 | Architecture diagram (Mermaid) | ✅ done | `paridhi_03_architecture.png` |
| 4 | README: Built with Bob / Data sources / Responsible AI | 🔨 in progress | `paridhi_04_readme.png` |
| 5 | Deployable to Streamlit Cloud (secrets) | 🤝 needs your OK | `*_05_deploy.png` |
| 6 | Demo-mode fallback | 🤝 needs your OK | `*_06_demo-mode.png` |

Status key: ⏳ planned · 🔨 in progress · ✅ done · 🤝 discuss first

---

## 1. Repo cleanup

**What:** Removed tracked `__pycache__/` folders and `.coverage` from git, and deleted the stray `gitignore` file (no dot). The real `.gitignore` stays. Added `.coverage`, `*.pyc` and `.pytest_cache/` to `.gitignore`, and removed the duplicate `apikey.json` line.

**Why:** Judges score "completeness" partly on how clean the repo is. Compiled `.pyc` files and coverage data are machine-specific noise, and they cause merge conflicts every time one of us runs the tests. The stray `gitignore` file does nothing, because git only reads `.gitignore`.

**Checked by:** Bob session (`paridhi_01_cleanup.png`): 11 cached `.pyc` files + `.coverage` untracked, `.gitignore` updated, **193 tests passed**.

---

## 2. Rate validation: percent vs. decimal 🐛

**What:** Added a small `_validate_rates` helper to `tools/core/finance.py` and called it in all 8 functions that take a rate: `project_savings_growth`, `debt_payoff_months`, `debt_vs_invest`, `financial_health_check`, `goal_plan`, `debt_schedule`, `savings_schedule` and `multi_debt_plan` (each debt's `apr`). `compare_scenarios` is covered too, because it calls `project_savings_growth`. Any rate > 1 now raises `ValueError` with the message *"rates must be decimals, e.g. 0.20 for 20%"*. New file: `tests/test_rate_validation.py`.

**Why:** The tools expect decimals, but users (and the LLM) naturally say "20%". If the agent passes `20` instead of `0.20`, the math treats it as **2000%**. For example, `debt_payoff_months(5000, 20, 20)` reports about **$8,333/month of interest** on a $5,000 balance. With validation, the agent gets an error it can recover from (and retries with 0.20) instead of confidently explaining a nonsense number. This protects our main promise that "every number comes from a verified tool".

**Checked by:** 24 new tests (rejects a percent-style rate, a boundary case, accepts a valid decimal). **217 passed** (all 193 original + 24 new). No formulas were changed: only `finance.py` and the new test file were touched.

---

## 3. Architecture diagram

**What:** Extended your existing `docs/ARCHITECTURE.md`. Everything you wrote stays as is (ASCII overview, design principles, data flow, auth). I added:
- a **Mermaid flowchart** (User → Streamlit UI → `api_client` → Orchestrate agent (ReAct) → tool wrappers → `tools/core/finance.py`)
- a **Tool reference** table with all 12 registered tools, their wrapper files, and what each one calculates
- a **Guardrails** section summarising the rules in `finpath_agent.yaml` (tool-only numbers, multi-turn old-vs-new comparison, stated assumptions and defaults, no product recommendations, mandatory disclaimer, `_verify_figures()` ±$0.51 cross-check)

**Why:** The presentation template needs an architecture slide, and the judges' "design" criterion rewards a clear system design. GitHub renders Mermaid natively, so the diagram is easy to read on the repo page and easy to screenshot for the video. The tool table and guardrails let judges see quickly what the agent can and can't do.

**Checked by:** Compared the tool names, defaults (5% growth, 12-month horizon, 7% invest rate), disclaimer text and `_verify_figures` tolerance with the actual code. Fixed curly quotes / `\n` line breaks that broke Bob's first Mermaid draft, and checked it renders on mermaid.live. The diff is **103 insertions, 0 deletions**, so none of your original content was removed.

---

## 4. README sections

**What:** Added three sections to `README.md`:
- **Built with IBM Bob:** how we used Bob during development, with a link to `bob_sessions/`
- **Data sources:** all 6 profiles in `data/profiles.json` are synthetic, with no real PII or client data
- **Responsible AI:** the agent never computes numbers, never recommends products, always adds the disclaimer, and shows which tools it used

**Why:** The program rules make Bob mandatory and forbid PII and confidential data. They also ask us to list our data sources. Putting this in the README means judges see it immediately.

---

## 5. Deployable to Streamlit Community Cloud 🤝

**What (proposed):** `app/api_client.py` reads the Orchestrate URL and API key from `st.secrets` or environment variables when present, and falls back to the current local ADK config (`~/.wxo/`). The key is never logged or displayed. I'd also add `.streamlit/secrets.toml.example` and a "Deploy" section in the README.

**Why:** A **working prototype link** is a required deliverable. Right now the app only runs on a machine where `orchestrate env activate` was run, so a hosted copy would fail on its first agent call.

**Question for you:** you know the ADK client best. Do you want to do this one, or should I try it in Bob and you review?

---

## 6. Demo-mode fallback 🤝

**What (proposed):** If the Orchestrate agent is unreachable (expired token, rate limit, outage), the app still shows the health score and core tool results computed locally, with a clear "Demo mode: agent offline" banner.

**Why:** Judges might open the link at any time. A friendly fallback is much better than a stack trace, and it shows the deterministic tools work on their own.

---

## Not changed (on purpose)
- Agent instructions in `agents/finpath_agent.yaml`: your rules are solid
- Core math logic: only added validation, no formula changes
- `FinPath AI — Conversation Log.pdf`: should we move it to `docs/` or remove it? Your call.
