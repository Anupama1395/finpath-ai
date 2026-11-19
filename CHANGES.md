# FinPath AI: Change Log — Paridhi's changes

This file tracks changes I made in **IBM Bob IDE**: what changed, **why**, and how I checked it. Each change's session screenshot is in `bob_sessions/`.

**Why this file exists:** the submission requires (1) Bob session reports from *each* member in the repo, (2) a working prototype link, and (3) written problem/solution and technology statements. The code itself is in great shape (217 tests passing). These changes are polish, bug fixes, and the submission requirements.

| # | Change | Status | Bob screenshot |
|---|--------|--------|————————|
| 1 | Repo cleanup | ✅ done | `paridhi_01_cleanup.png` |
| 2 | Rate validation (percent vs. decimal bug) | ✅ done | `paridhi_02_rate-validation.png` |
| 3 | Architecture diagram (Mermaid) | ✅ done | `paridhi_03_architecture.png` |
| 4 | README: Built with Bob / Data sources / Responsible AI | 🔨 in progress | `paridhi_04_readme.png` |
| 5 | Deployable to Streamlit Cloud (secrets) | ✅ done | `paridhi_05_deploy.png` |
| 6 | Demo-mode fallback | ✅ done | `paridhi_05_deploy.png` |
| 7 | Step 1 & Step 3 UI fixes | ✅ done | `paridhi_06_ui-fixes.png` |
| 8 | Step 0 landing screen (aurora bg, typing tagline, GIF, cards, Get Started) | ✅ done | `paridhi_08_hero.png` |
| 9 | Landing screen polish: remove duplicate button, add ticker tape | ✅ done | `paridhi_08_hero.png` |
| 10 | Ticker tape: live values from session state, no hard-coded numbers | ✅ done | `paridhi_08_hero.png` |
| 11 | Landing screen: labels-only ticker, remove GIF, remove duplicate title | ✅ done | `paridhi_08_hero.png` |
| 12 | Landing layout fixes: full-width iframe, no empty black gap, card 02 title shortened to "See the numbers" | ✅ done | `paridhi_08_hero.png` |
| 13 | Landing screen: remove dashed wave/paths, add How-it-works strip, hero-question box, guardrails line, fill vertical space | ✅ done | `paridhi_09_remove-wave.png` |
| 14 | Fix Streamlit Cloud deploy crash: pin `ibm-watsonx-orchestrate==2.20.0`, add missing `ibm-cloud-sdk-core==3.28.2` to requirements.txt | ✅ done | — |
| 15 | Log full exception on agent connection failure (`logger.exception` instead of `logger.debug`) so Streamlit Cloud logs show real IAM/URL/agent errors | ✅ done | — |
| 16 | Sync `app/requirements.txt` with root: add `ibm-watsonx-orchestrate==2.20.0`, `ibm-cloud-sdk-core==3.28.2`, `python-dotenv`; align version floors for `streamlit`, `altair`, `pandas` — fixes Streamlit Cloud picking wrong file and crashing with `ModuleNotFoundError` | ✅ done | — |
| 17 | Steps 1–3 polish: help text on Step 1 inputs, upload label fixed, hero question chip on Step 2, plain-English takeaway + full goal summary on Step 3, width="stretch" cleanup, README live link | ✅ done | `paridhi_10_steps-polish.png` |
| 18 | Step 3 download report + rule-based suggestions: Download summary now returns a real markdown report (profile, health score, question, answer, what-if), 2–3 deterministic suggestions, no product recommendations | ✅ done | `paridhi_11_download-report.png` |
| 19 | "How to use FinPath" manual on Step 1: collapsible expander with what FinPath is, the 3 steps, what each input means, upload/save profile help, and 4 Q&As | ✅ done | `paridhi_12_how-to-use.png` |
| 20 | RAG knowledge base (`finpath_kb`), `finpath_kb_agent`, collaborator wiring in `finpath_agent.yaml`, and live Orchestrate import (PR #14) | ✅ done | `kartikeya_01_rag-plan.png` – `kartikeya_05_agent-integration.png` |
| 21 | RAG documentation updates in `README.md` and `docs/ARCHITECTURE.md` (folder layout, Mermaid diagram, tool table, import commands, delegation & citation rules) | ✅ done | `kartikeya_06_documentation.png`, `kartikeya_07_architecture.png`, `kartikeya_08_changes.png` |


Status key: ⏳ planned · 🔨 in progress · ✅ done · 🤝 discuss first

—

## 1. Repo cleanup

**What:** Removed tracked `__pycache__/` folders and `.coverage` from git, and deleted the stray `gitignore` file (no dot). The real `.gitignore` stays. Added `.coverage`, `*.pyc` and `.pytest_cache/` to `.gitignore`, and removed the duplicate `apikey.json` line.

**Why:** Judges score "completeness" partly on how clean the repo is. Compiled `.pyc` files and coverage data are machine-specific noise, and they cause merge conflicts every time one of us runs the tests. The stray `gitignore` file does nothing, because git only reads `.gitignore`.

**Checked by:** Bob session (`paridhi_01_cleanup.png`): 11 cached `.pyc` files + `.coverage` untracked, `.gitignore` updated, **193 tests passed**.

—

## 2. Rate validation: percent vs. decimal 🐛

**What:** Added a small `_validate_rates` helper to `tools/core/finance.py` and called it in all 8 functions that take a rate: `project_savings_growth`, `debt_payoff_months`, `debt_vs_invest`, `financial_health_check`, `goal_plan`, `debt_schedule`, `savings_schedule` and `multi_debt_plan` (each debt's `apr`). `compare_scenarios` is covered too, because it calls `project_savings_growth`. Any rate > 1 now raises `ValueError` with the message *"rates must be decimals, e.g. 0.20 for 20%"*. New file: `tests/test_rate_validation.py`.

**Why:** The tools expect decimals, but users (and the LLM) naturally say "20%". If the agent passes `20` instead of `0.20`, the math treats it as **2000%**. For example, `debt_payoff_months(5000, 20, 20)` reports about **$8,333/month of interest** on a $5,000 balance. With validation, the agent gets an error it can recover from (and retries with 0.20) instead of confidently explaining a nonsense number. This protects our main promise that "every number comes from a verified tool”.

**Checked by:** 24 new tests (rejects a percent-style rate, a boundary case, accepts a valid decimal). **217 passed** (all 193 original + 24 new). No formulas were changed: only `finance.py` and the new test file were touched.

—

## 3. Architecture diagram

**What:** Extended your existing `docs/ARCHITECTURE.md`. Everything you wrote stays as is (ASCII overview, design principles, data flow, auth). I added:
- a **Mermaid flowchart** (User → Streamlit UI → `api_client` → Orchestrate agent (ReAct) → tool wrappers → `tools/core/finance.py`)
- a **Tool reference** table with all 12 registered tools, their wrapper files, and what each one calculates
- a **Guardrails** section summarising the rules in `finpath_agent.yaml` (tool-only numbers, multi-turn old-vs-new comparison, stated assumptions and defaults, no product recommendations, mandatory disclaimer, `_verify_figures()` ±$0.51 cross-check)

**Why:** The presentation template needs an architecture slide, and the judges' "design" criterion rewards a clear system design. GitHub renders Mermaid natively, so the diagram is easy to read on the repo page and easy to screenshot for the video. The tool table and guardrails let judges see quickly what the agent can and can't do.

**Checked by:** Compared the tool names, defaults (5% growth, 12-month horizon, 7% invest rate), disclaimer text and `_verify_figures` tolerance with the actual code. Fixed curly quotes / `\n` line breaks that broke Bob's first Mermaid draft, and checked it renders on mermaid.live. The diff is **103 insertions, 0 deletions**, so none of your original content was removed.

—

## 4. README sections

**What:** Added three sections to `README.md`:
- **Built with IBM Bob:** how we used Bob during development, with a link to `bob_sessions/`
- **Data sources:** all 6 profiles in `data/profiles.json` are synthetic, with no real PII or client data
- **Responsible AI:** the agent never computes numbers, never recommends products, always adds the disclaimer, and shows which tools it used

**Why:** The program rules make Bob mandatory and forbid PII and confidential data. They also ask us to list our data sources. Putting this in the README means judges see it immediately.

—

## 5. Deployable to Streamlit Community Cloud ✅

**What (done in this PR, 2026-11-16, branch `paridhi/ui-fixes`):** `app/api_client.py` reads the Orchestrate URL and API key from `st.secrets` or environment variables when present, and falls back to the current local ADK config (`~/.wxo/`). The key is never logged or displayed. Added `.streamlit/secrets.toml.example` and a "Deploy" section in the README.

**Why:** A **working prototype link** is a required deliverable. Right now the app only runs on a machine where `orchestrate env activate` was run, so a hosted copy would fail on its first agent call.

**Checked by:** Bob session (`paridhi_05_deploy.png`).

—

## 6. Demo-mode fallback ✅

**What (done in this PR, 2026-11-16, branch `paridhi/ui-fixes`):** If the Orchestrate agent is unreachable (expired token, rate limit, outage), the app shows a clear "Demo mode: agent offline" banner in `app/main.py`, but still shows the health score and core tool results computed locally, with no stack trace.

**Why:** Judges might open the link at any time. A friendly fallback is much better than a stack trace, and it shows the deterministic tools work on their own.

**Checked by:** Bob session (`paridhi_05_deploy.png`).

—

## 7. Step 1 & Step 3 UI fixes ✅

**What (done 2026-11-16, branch `paridhi/ui-fixes`):**
- `data/profiles.json`: added `income_breakdown`, `expense_breakdown`, `savings_breakdown` to all 6 profiles, each summing exactly to the existing totals. Recent Graduate expenses $2,400 = housing $1,200 + food $500 + transport $300 + subs $100 + other $300.
- `app/main.py _load_profile()`: reads breakdown fields from the profile (with sum-check fallback to old behaviour if absent or mismatched). Seeds an "Emergency fund" goal with target = 3 × monthly_expenses, saved = cash_savings (Recent Graduate: $7,200 / $1,500).
- Goal summary changed from `st.text_input` → `st.text_area` (no more cut-off).
- File uploader label updated to "Upload a saved profile (.json, a few KB)”.
- Follow-up chips shortened to fit without truncation: "+$100/mo debt payment?", "Income down 10%?", "Invest vs pay debt?”.
- Chart title shortened to "Debt balance — 36 months" to prevent clipping.

**Health check unchanged:** Recent Graduate score=57, cash flow=+$350/mo, EF coverage=0.62 mo ✓

**Checked by:** 217 tests passed. Bob session (`paridhi_06_ui-fixes.png`).

—

## 8. Step 0 landing screen ✅

**What (done 2026-11-17, branch `paridhi/hero`):** Replaced the inline hero block with a full separate **Step 0** landing screen shown before the profile step. Changes:

- **`app/main.py`**: Added `render_step0()` using `streamlit.components.v1.components.html` to render a self-contained HTML page inside a tall iframe. Default `S.step` changed from `1` → `0`. Router extended with `if S.step == 0: render_step0()`. Hero block removed from `render_step1()`.
- **`assets/dot_path.gif`**: New 40-frame, 10.9 KB animated GIF (320×160 px) showing a glowing orange dot travelling along a winding sine-wave path, generated with Pillow. Embedded as a base64 data URI so it loads on Streamlit Cloud without static-file serving.

Landing screen features:
- **Dark navy background** (`#07090D`) with four radial-gradient aurora blobs (orange, teal, blue, gold)
- **SVG winding path** — dashed orange primary + teal secondary + blue accent, all decorative
- **Dark gradient overlay** so text stays readable against the aurora
- **FinPath AI** title (4.2 rem serif italic), "AI" in orange
- **Looping typing animation** — "Every dollar has a path. Find yours." types in, holds 1.8 s, deletes, loops; blinking orange cursor
- **Sub-line** in monospace muted text
- **Get Started →** CTA button (orange, large) — single button inside the iframe
- **Animated GIF** with label "Your dollars, finding their path”
- **3 rounded cards** — Ask a money question / See the numbers & trade-offs / Try a what-if
- **Disclaimer** footer
- Steps 1–3 unchanged — no background image, full readability preserved

No calculations, profile data, or Step 1/2/3 logic were touched. `tools/core/finance.py` unchanged.

**Checked by:** 217 tests passed. Bob session (`paridhi_07_hero.png`).

—

## 9. Landing screen polish ✅

**What (done 2026-11-17, branch `paridhi/hero`):** Two targeted fixes to the Step 0 landing screen:

1. **Removed duplicate Get Started button** — the previous implementation rendered a `st.button` below the `components.html` iframe as a fallback navigation trigger, which appeared as a second "GET STARTED →" floating below the landing panel. Removed the duplicate entirely. The in-iframe CTA now navigates by setting `?go=1` on the parent URL and dispatching a `popstate` event; Streamlit detects `st.query_params.get("go") == "1"` on rerun and calls `_go(1)`. Only one button remains.

2. **Ticker tape strip** — Added a `position:fixed; bottom:0` ticker at the bottom of the iframe, `2rem` tall with a subtle `rgba(7,9,13,.82)` background and a thin `rgba(232,96,60,.18)` top border. Ten illustrative items scroll at 38 s/cycle (slow, unobtrusive): **Savings · Emergency Fund · Debt · Goals · Cash Flow · Savings Rate · Debt-to-Income · Payoff · What-if** — values coloured teal (healthy), orange (attention), or gold (moderate). No real tickers, no stock prices, no red/green trading charts. The track is duplicated in HTML for a seamless CSS loop. Hovering pauses the animation.

No calculations, profile data, or Step 1/2/3 logic were touched. `tools/core/finance.py` unchanged.

**Checked by:** 217 tests passed. Bob session (`paridhi_07_hero.png`).

—

## 10. Ticker tape — live values from session state ✅

**What (done 2026-11-17, branch `paridhi/hero`):** Replaced all hard-coded ticker numbers with values computed dynamically from `S.*` (Streamlit session state) on every rerun.

- Added `_ticker_items()` helper (after `_headroom()` in `app/main.py`) — computes 7–8 items from live session state using the same logic as the health card: cash flow, savings, savings rate, debt-to-income, emergency fund coverage, EF target, debt balance, and debt payoff months (via `_debt_schedule`). Items are skipped if the underlying value is zero (e.g. no debt). Colours follow the same thresholds: teal = healthy, gold = moderate, orange = attention.
- Added `_ticker_html()` helper — renders one pass of items as HTML spans; called twice to build `ticker_inner` (duplicated track for seamless CSS loop).
- `render_step0()` calls `_ticker_items()` / `_ticker_html()` before building `html_page`, then injects `{ticker_inner}` into the f-string — server-side substitution, no JavaScript required.
- Changed ticker layout from `position:fixed;bottom:0` → `position:relative` with `body{display:flex;flex-direction:column}` and `.wrap{flex:1}`, so the ticker is a natural document footer visible at the bottom of the iframe. Iframe height bumped to `920`.

Default session state values shown (no profile selected on Step 0):
`Cash Flow +$1,500/mo · Savings +$200/mo · Savings Rate 4% · Debt-to-Income 6% · Emergency Fund 2.0 mo · EF Target $9,000 · Debt Balance $10,000 @ 6% · Debt Payoff 37 mo`

No calculations, profile data, or Step 1/2/3 logic were touched. `tools/core/finance.py` unchanged.

**Checked by:** 217 tests passed. Bob session (`paridhi_07_hero.png`).

—

## 11. Landing screen cleanup ✅

**What (done 2026-11-17, branch `paridhi/hero`):** Three targeted removals/simplifications — no logic, profile data, or Step 1–3 changes:

1. **Ticker labels only** — removed all numbers from the ticker. The six items now scroll as plain labels: `SAVINGS · DEBT · EMERGENCY FUND · GOALS · CASH FLOW · WHAT-IF`. No invented numbers, no session-state lookup needed. Removed `_ticker_items()` / `_ticker_html()` calls from `render_step0()`.

2. **GIF removed** — deleted the `<div class="gif-row">` block and `.gif-row` / `.gif-label` CSS. The dashed SVG path lines across the background serve the same visual purpose.

3. **Duplicate title removed** — deleted the `<div class="wm">` wordmark block (the italic `FINPATH` / `PATH` logo) and its CSS (`.wm`, `.wm-logo`, `.wm-sub`). "FinPath AI" as the `<h1>` is the single title. The IBM SkillsBuild sub-caption is kept as an inline `<p>` above the `<h1>`.

Also: outer Streamlit page background forced to `#07090D` to match the iframe so any residual gap is invisible; screenshot taken at viewport height 670 (exact content height) to confirm zero gap.

No calculations, profile data, or Step 1/2/3 logic were touched. `tools/core/finance.py` unchanged.

**Checked by:** 217 tests passed. Bob session (`paridhi_07_hero.png`).

—

## 12. Landing layout fixes ✅

**What (done 2026-11-17, branch `paridhi/hero`):** Two targeted layout fixes to the Step 0 landing screen, in a single change to `app/main.py`:

1. **Full-width, no empty gap** — the iframe previously had wide Streamlit margins (centered 860px block-container) and a large black empty area below the disclaimer before the ticker. Fixed by: (a) `.wrap` now uses `min-height:calc(100vh - 2rem)`, `display:flex`, `flex-direction:column` — the bottom block (cards + disclaimer) gets `margin-top:auto` so it always pins flush to the ticker with no dead space; (b) `.wrap` max-width widened to 980px with side padding 2.8rem for a full-bleed look; (c) ticker changed to `position:fixed; bottom:0` for a guaranteed bottom anchor regardless of content height; (d) vertical spacing redistributed across the top padding, h1 margin, tagline, sub-line, and CTA margin so all elements fit at a 1280×620 laptop viewport without scrolling. Cards kept `flex-wrap:nowrap` so they always stay side-by-side.

2. **Card 02 title** — shortened from `"See the numbers & trade-offs"` to `"See the numbers"`. The card body already says *"Every answer is backed by a verified calculation"*, so "trade-offs" was redundant and caused an awkward two-word wrap at narrow widths.

No calculations, profile data, or Step 1/2/3 logic were touched. `tools/core/finance.py` unchanged.

**Checked by:** 217 tests passed. Bob session (`paridhi_07_hero.png`).

—

## Not changed (on purpose)
- Agent instructions in `agents/finpath_agent.yaml`: your rules are solid
- Core math logic: only added validation, no formula changes
- `FinPath AI — Conversation Log.pdf`: should we move it to `docs/` or remove it? Your call.

## 13. Landing screen: remove wave, add content sections, fill vertical space ✅

**What (done 2026-11-17, branch `paridhi/remove-wave`):** Targeted changes to `app/main.py` `render_step0()` only — no logic, finance functions, profile data, or Step 1/2/3 changes:

1. **Removed SVG wave/path lines** — deleted the entire `<svg class="path-svg">` block (glow halo, dashed orange path, teal secondary, blue accent) and its `.path-svg` CSS rule. The paths were clipped at the viewport edges and looked broken. Dark navy `#07090D` background and aurora radial-gradient layer kept intact.

2. **Added three new sections under the cards:**
   - **How it works strip** — a three-cell horizontal bar: `1 — Pick a profile · 2 — Ask a question · 3 — See the numbers & try a what-if`
   - **Hero-question example box** — teal left-border callout: *"Can I invest $300 more a month and still keep three months of emergency cash?”*
   - **Guardrails line** — dim monospace text: *No real money · no real accounts · no product recommendations · Synthetic profiles only · Educational tool — not financial advice.*

3. **Vertical spacing** — wrap uses `height:calc(100vh - 2rem)` + `justify-content:space-between` with `padding-bottom:4rem` on the wrap so the two flex blocks (hero copy + bottom section) distribute the slack evenly (~117px above cards, ~98px below guardrails). Ticker stays `position:fixed; bottom:0` and is always visible at the bottom of the viewport. Iframe height set to `820px`. No page scrolling.

No calculations, profile data, or Step 1/2/3 logic were touched. `tools/core/finance.py` unchanged.

**Checked by:** 217 tests passed. Bob session (`paridhi_09_remove-wave.png`).

—

## 14. Fix Streamlit Cloud deploy crash ✅

**What (done 2026-11-17, branch `paridhi/fix-requirements`):** Two changes to `requirements.txt` only — no app logic, calculations, or landing touched:

1. **Pinned `ibm-watsonx-orchestrate==2.20.0`** — the entry existed but had no version, so Streamlit Cloud could resolve a different (incompatible) release. The version pin matches what works locally (confirmed via `pip show` in the project venv).

2. **Added `ibm-cloud-sdk-core==3.28.2`** — this package is imported directly in `app/api_client.py` line 98 (`from ibm_cloud_sdk_core.authenticators import IAMAuthenticator`) but was not listed in `requirements.txt` at all. Its absence caused the `ModuleNotFoundError` that crashed the cloud deploy. Version matches the venv.

No other missing imports were found: `streamlit`, `altair`, `pandas`, and `python-dotenv` were already listed and correct.

**Why:** Streamlit Community Cloud installs exactly what `requirements.txt` says. `ibm-cloud-sdk-core` is not a declared dependency of `ibm-watsonx-orchestrate`'s wheel on PyPI, so it was never pulled in transitively on the cloud even though it happened to be present locally.

**Checked by:** 217 tests passed (`pytest tests/ --ignore=tests/smoke_test.py`). No app logic, calculations, or landing changed.

—

## 15. Log full exception on agent connection failure ✅

**What (done 2026-11-17, branch `paridhi/fix-requirements`):** One-line change to [`app/api_client.py`](app/api_client.py) — no logic altered:

```python
# before
logger.debug("ADK call failed", exc_info=True)

# after
logger.exception("ADK call failed")
```

`logging.exception` logs at **ERROR** level and always attaches the current exception's full traceback. `logging.debug` with `exc_info=True` logs at DEBUG level, which Streamlit Cloud suppresses by default, so the real error (bad IAM key, wrong instance URL, agent not found, network timeout, etc.) was silently swallowed and never appeared in the cloud log viewer.

**Why:** When the deploy crashed, the only observable symptom was the generic `RuntimeError("Could not reach FinPath AI…")` bubble in the UI. The root cause — expired IAM token, mistyped `ORCHESTRATE_INSTANCE_URL`, agent name mismatch — was hidden in a DEBUG-level log that the cloud never surfaces. Switching to `logger.exception` makes the real failure visible immediately in the Streamlit Cloud "Logs" tab without any configuration change.

**Checked by:** 217 tests passed (`pytest tests/ --ignore=tests/smoke_test.py`). No other logic changed.

—

## 16. Sync `app/requirements.txt` with root ✅

**What (done 2026-11-17, branch `paridhi/fix-app-requirements`):** `app/requirements.txt` was a stale three-line stub that Streamlit Cloud preferred over the root `requirements.txt`. Replaced it with an exact copy of the root file — same packages, same version pins:

```
streamlit>=1.32.0
altair>=5.0.0
pandas>=2.0.0
ibm-watsonx-orchestrate==2.20.0
ibm-cloud-sdk-core==3.28.2
python-dotenv
```

**Why:** Streamlit Cloud's build log warned *"More than one requirements file detected. Used: /mount/src/finpath-ai/app/requirements.txt"* and chose `app/requirements.txt` over the root one. That file listed only `streamlit`, `altair`, and `pandas`, so `ibm-watsonx-orchestrate` and `ibm-cloud-sdk-core` were never installed, causing `ModuleNotFoundError: No module named 'ibm_watsonx_orchestrate'` on startup.

**Checked by:** 217 tests passed (`pytest tests/ --ignore=tests/smoke_test.py`). No app logic, calculations, or landing touched.

—

## 17. Steps 1–3 polish ✅

**What (done 2026-11-18, branch `paridhi/steps-polish`):**
- Step 1: plain-English `help=` text on every profile input; upload label changed to "Upload a saved FinPath AI profile (JSON)"
- Step 2: tappable hero chip — "Can I invest $300 more a month and still keep three months of emergency cash?" — fills the question box
- Step 3: "FinPath AI says" takeaway callout with the plain-English answer first; goal summary now shows every goal in full, no truncation
- Follow-up chips now show the full question text, not the short label
- Replaced all `use_container_width=True` with `width="stretch"`
- README: live prototype link added at the top — https://finpath-ai-copilot.streamlit.app/

**Why:** The demo video walks through Steps 1–3, so each step needs to be self-explanatory on screen, with no truncated text and no misleading labels.

**Checked by:** 217 tests passed. Bob session (`paridhi_10_steps-polish.png`). Verified on localhost with screenshots of Steps 1, 2, and 3.

## 18. Step 3 download report + rule-based suggestions ✅

**What (done 2026-11-18, branch `paridhi/download-report`):**
- Step 3 Download summary now returns a real markdown report: profile summary, goals, health score, question, agent answer with numbers, what-if tried, and suggestions
- 2–3 rule-based suggestions on Step 3, from deterministic rules/numbers only — no product recommendations, no named products
- Disclaimer kept: "Educational tool — not financial advice"

**Why:** Judges can download a complete record of the demo, and the suggestions show the deterministic tools working without the agent recommending products.

**Checked by:** 217 tests passed. Bob session (`paridhi_11_download-report.png`). Verified on localhost.

## 19. "How to use FinPath" manual ✅

**What (done 2026-11-18, branch `paridhi/how-to-use`):**
- Added a collapsible "📖 How to use FinPath" expander at the top of Step 1, collapsed by default
- Inside: what FinPath is, the 3 steps (Pick a profile, Ask a question, See the numbers), what each of the 8 profile inputs means, how to upload/save a profile (JSON only), and 4 Q&As — "What if I don't know my numbers?", "Are these real recommendations?", "What does the health score mean?", "What is the emergency fund target?"

**Why:** New users and judges can understand the app without guessing what to enter — the manual explains it in plain English, without changing the flow for returning users.

**Checked by:** 217 tests passed. Bob session (`paridhi_12_how-to-use.png`). Verified on localhost.

## 20. RAG knowledge base & `finpath_kb_agent` collaborator ✅

**What (done 2026-11-19, branch `kartikeya/rag`, merged in PR #14):**
- Added four cited, public-source personal finance explainers in `knowledge/` (`emergency_fund_guide.txt`, `compound_interest.txt`, `debt_payoff_strategies.txt`, `savings_rate.txt`) with no PII.
- Created `knowledge/finpath_kb.yaml` (`finpath_kb`) and `agents/finpath_kb_agent.yaml` (retrieval-only, `tools: []`, citation-backed, no calculations or product recommendations).
- Added `finpath_kb_agent` under `collaborators:` in `agents/finpath_agent.yaml` and added workflow rule `k.` to delegate conceptual "why" questions. No tool or math code was modified.
- Imported `finpath_kb` (4 docs, 27.5 KB, `built_in_index_status: ready`), `finpath_kb_agent`, and updated `finpath_agent` on the Tokyo watsonx Orchestrate instance.

**Why:** Enables cited, grounded answers to conceptual "why" questions (per `SPEC.md` §2a/§8) while keeping all calculations strictly deterministic on `finpath_agent`'s tools.

**Checked by:** 217 tests passed (`python -m pytest tests/ --ignore=tests/smoke_test.py -q`), `orchestrate knowledge-bases status --name finpath_kb` (`ready`), `orchestrate agents list` showing the collaborator wiring, and the Orchestrate chat test: "Why do I need an emergency fund?" handed off to `finpath_kb_agent`, retrieved from `emergency_fund_guide.txt` and returned a cited answer with the disclaimer. Live app (finpath-ai-copilot.streamlit.app) verified by Paridhi on 2026-11-20: the "why" answer displays. Bob sessions: `bob_sessions/kartikeya_01_rag-plan.png` through `bob_sessions/kartikeya_05_agent-integration.png`.

## 21. RAG documentation (`README.md` & `docs/ARCHITECTURE.md`) ✅

**What (done 2026-11-20, branch `kartikeya/rag-docs`):**
- Updated `README.md` repository structure and added a **Knowledge base (RAG)** section with the exact `orchestrate knowledge-bases import`, `status`, and `agents import` commands.
- Updated `docs/ARCHITECTURE.md` Mermaid diagram, tool reference table, and added a **Knowledge agent (RAG)** section documenting delegation triggers, citation format, and collaborator role boundaries.

**Why:** Documents the RAG architecture and exact reproducible Orchestrate import steps for teammates and judges.

**Checked by:** 217 tests passed (`python -m pytest tests/ --ignore=tests/smoke_test.py -q`). Bob sessions: `bob_sessions/kartikeya_06_documentation.png`, `bob_sessions/kartikeya_07_architecture.png`, `bob_sessions/kartikeya_08_changes.png`.
