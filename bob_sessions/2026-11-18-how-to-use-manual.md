# Bob Session — FinPath "How to use" Manual
**Date:** 2026-11-18  
**Branch:** paridhi/how-to-use  
**Task:** Add a collapsible "How to use FinPath" manual section to Step 1 of the FinPath AI Streamlit app.

---

## Work completed

### Step 1 — Collapsible how-to manual
Added a `st.expander("📖 How to use FinPath", expanded=False)` block at the very top of `render_step1()`, immediately after the page heading and subtitle, before the "Load or save profile" section.

The expander is collapsed by default so it does not interrupt the normal flow for returning users, but is immediately visible and tappable for new users.

#### Content sections inside the expander

| Section | Content |
|---|---|
| **What is FinPath?** | Plain-English description of the tool — educational, not advice; turns numbers into insights via an AI assistant |
| **The 3 steps** | Numbered cards: 1 Pick a profile, 2 Ask a question, 3 See the numbers — each with a one-sentence explanation |
| **What each input means** | Two-column grid covering all eight profile fields: Monthly income, Monthly expenses, Savings (total), Saving per month, Debt balance, Monthly debt payment, Interest rate, Goals |
| **Uploading and saving a profile** | How to use the Save/Upload buttons; note that only FinPath JSON files are supported |
| **Common questions (Q&A)** | Four Q&As: "What if I don't know my numbers?", "Are these real recommendations?", "What does the health score mean?", "What is the emergency fund target?" |

#### Design decisions
- Uses Streamlit's native `st.expander` — consistent with the existing Income / Expenses / Savings expanders elsewhere on Step 1
- All styling uses existing CSS variables (`--sans`, `--mono`, `--surface2`, `--border`, `--orange`, `--dim`, `--muted`, `--text`, `--radius-sm`) so it matches the dark theme without adding new CSS
- `expanded=False` — collapsed by default, so Step 1 layout is unchanged for experienced users
- The "Educational tool · Not financial advice" disclaimer at the bottom of Step 1 (`_disclaimer()`) is **untouched and still visible**

### Files NOT changed
- `render_step0()` (landing page) — untouched
- All calculation / tool code (`tools/`) — untouched
- Agent / RAG code (`agent/`, `agents/`) — untouched
- Download report feature — untouched
- `data/profiles.json` — untouched
- Theme, CSS variables, global styles — untouched

---

## Validation

| Check | Result |
|---|---|
| `python -m py_compile app/main.py` | ✅ Syntax OK |
| `pytest tests/ --ignore=tests/smoke_test.py -q` | ✅ **217 passed** in 0.07s |
| `streamlit run app/main.py --server.port 8503` | ✅ HTTP 200, app running on :8503, no errors |

---

## Files changed
- `app/main.py` — added collapsible `st.expander("📖 How to use FinPath")` block (~75 lines) inside `render_step1()`, after the page heading and before the "Load or save profile" section. No other changes.

---

*No commits, no pushes, no PR created. Branch: paridhi/how-to-use.*
