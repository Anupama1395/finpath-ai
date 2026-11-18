# Bob Session — FinPath Steps 1/2/3 Polish
**Date:** 2026-11-18  
**Branch:** paridhi/steps-polish  
**Task:** Polish Steps 1, 2, and 3 of the FinPath AI demo app for the demo video.

---

## Work completed

### Step 1 — Profile inputs
- Added `help=` tooltip text to every profile input widget (salary, side income, other income; housing, food, transport, subscriptions, other expenses; emergency fund, investments, other savings; savings contribution, goal text area, debt balance, monthly debt payment, debt interest rate). Each help string is a plain-English sentence explaining what the field means and what to enter.
- Fixed the file uploader label: changed from `"⬆ Upload a saved profile (.json, a few KB)"` (with the misleading "a few KB" and no mention of JSON type) to `"⬆ Upload a saved FinPath AI profile (JSON)"` with a proper `help=` tooltip and `label_visibility="visible"`.

### Step 1 — Expenses-to-Housing investigation
**Finding: data issue on old sessions, not a UI code bug.**  
All six sample profiles in `data/profiles.json` have full `expense_breakdown` dicts with correct Housing/Food/Transport/Subscriptions/Other splits. The `_load_profile()` function's guard (`if S.exp_housing + ... != expenses: S.exp_housing = expenses`) is a correct fallback for malformed or missing breakdowns. The "$2,400 in Housing" observed on Nov 16 was caused by the **default/manual state** (no profile selected) where the form was brand-new and the user had not entered individual expense line items — the total was written to `expenses` but the breakdown still showed the defaults. No UI-mapping bug was found; no fake fix was applied.

### Step 2 — Question page
- Added a tappable hero chip at the top of the suggestions area: `💡 Can I invest $300 more a month and still keep three months of emergency cash?` — clicking it fills the question box with that exact text.
- Changed follow-up chips (Step 3) to show the **full question text** (`question` variable) instead of the short `label` — `.sug-btn` CSS already has `white-space:normal` so text wraps without truncation.

### Step 3 — Results page
- Added a **hero takeaway callout**: the first non-heading line of the first assistant reply is extracted and displayed prominently above the chat history in an italic serif callout block labelled "FinPath AI says". This gives viewers the plain-English answer immediately, before all the numbers.
- **Goal summary**: expanded `_assumptions_expander()` to include every goal row in full (name, target, months, already saved) — no truncation, all goals visible.

### README
- Added `**Live prototype:** https://finpath-ai-copilot.streamlit.app/` on line 7, before the CI badge.

### Deprecation cleanup — `use_container_width`
Replaced all 12 occurrences of `use_container_width=True` with `width="stretch"` across:
- `st.button` (profile chips, Next button, Step 2 nav buttons, follow-up chips, New conversation)
- `st.download_button` (Save my profile, Download summary)
- `st.data_editor` (debt table)
- `st.altair_chart` (debt and savings charts in what-if explorer)

Zero occurrences of `use_container_width` remain in `app/main.py`.

---

## Validation

| Check | Result |
|---|---|
| `python -m py_compile app/main.py` | ✅ Syntax OK |
| `pytest tests/ --ignore=tests/smoke_test.py -q` | ✅ **217 passed** in 0.07s |
| `streamlit run app/main.py --server.port 8502` | ✅ HTTP 200, process listening on :8502, no errors/warnings |
| `grep use_container_width app/main.py` | ✅ No matches |

---

## Files changed
- `app/main.py` — Step 1 help text, upload label, hero chip, follow-up chips full text, hero takeaway, goals in assumptions expander, `width="stretch"` throughout
- `README.md` — live prototype link added at top

## Files NOT changed (per brief)
- `app/main.py` landing page (`render_step0`) — untouched
- All calculation/tool code (`tools/`)
- Agent/RAG code
- Theme/colours/CSS variables
- `data/profiles.json`

---

*No commits, no pushes, no PR created. Branch: paridhi/steps-polish.*
