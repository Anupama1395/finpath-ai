# FinPath AI — Enhanced Profile, Multi-Goal & User Persistence Plan

## Overview

Three connected improvements to `app/main.py` and `tools/core/finance.py`:

1. **Richer financial profile** — break down income sources, expense categories, and savings accounts so the agent has more precise inputs
2. **Multiple goals** — up to 5 named goals each with target, current saved, and deadline; individual feasibility cards
3. **Save/Load profile** — "Export profile" downloads a JSON file; "Import profile" uploads it back; no server, no database, works for the IBM demo

Architecture stays identical. All new data flows through `_build_profile_dict()` into the existing `ask_agent()` call. No new tools needed for 1 and 3. Goal plan already has `goal_plan()` — we call it once per goal.

---

## Sub-Task 1 — Richer Financial Profile

**Intent:** Replace the 4 flat number inputs with an expandable breakdown so users can enter salary + side income separately, housing vs other expenses, and label their savings accounts. The agent gets richer context; the health card reacts immediately.

**Expected Outcomes:**
- Income section shows: Salary, Side income / freelance, Other income — summed into `S.income`
- Expenses section shows: Housing/rent, Food & groceries, Transport, Subscriptions, Other — summed into `S.expenses`
- Savings section shows: Emergency fund balance, Investment balance, Other savings — summed into `S.savings`
- Existing `S.income`, `S.expenses`, `S.savings` session keys unchanged — just derived from sub-fields
- Health card and goal card still react in real time
- `_build_profile_dict()` gains breakdown fields so the agent can reference them by category

**Todo List:**
1. Add new session state keys in `_init_state()`:
   - Income breakdown: `inc_salary`, `inc_side`, `inc_other`
   - Expense breakdown: `exp_housing`, `exp_food`, `exp_transport`, `exp_subs`, `exp_other`
   - Savings breakdown: `sav_emergency`, `sav_invest`, `sav_other`
2. In `render_step1()`, replace the flat income/expenses/savings inputs with a `st.expander("Income breakdown")` and `st.expander("Expense breakdown")` and `st.expander("Savings accounts")` each showing sub-fields
3. After each expander, compute and display the total: `S.income = inc_salary + inc_side + inc_other` etc.
4. Update `_build_profile_dict()` to include the breakdown fields (prefixed `income_`, `expense_`, `savings_`)
5. Update `_load_profile()` to populate breakdown fields from the flat profile values (put everything into the primary field, zero the rest)
6. Update `_clear_profile()` to zero all breakdown fields

**Relevant Context:**
- `_init_state()` — lines ~171–201 in `app/main.py`
- `render_step1()` — lines ~462–525
- `_build_profile_dict()` — lines ~247–257
- `_load_profile()` — lines ~210–230
- Health card `_health_card()` reads `S.income`, `S.expenses`, `S.savings` — these stay unchanged

**Status:** `[ ] pending`

---

## Sub-Task 2 — Multiple Goals (up to 5)

**Intent:** Replace the single `goal_target` / `goal_months` pair with a list of up to 5 named goals. Each goal shows its own feasibility card. The agent receives all goals in `_build_profile_dict()` so it can prioritise and compare them.

**Expected Outcomes:**
- Session state has `goals: list[dict]` — each dict has `name`, `target`, `months`, `current_saved`
- Step 1 shows a goal list: each row has name input, target $, current saved $, months — plus "＋ Add goal" and "✕ Remove" controls
- Each goal shows a feasibility card (green ✓ / red ✗) using `goal_plan()` with the shared headroom divided across goals
- `_build_profile_dict()` includes `goals` list so agent sees all of them
- Existing single `goal` text field kept as "Goal summary" for the agent's natural language context

**Todo List:**
1. Replace `goal_target` and `goal_months` session keys with `goals: list[dict]` where each dict = `{name, target, current_saved, months}`; seed with one empty goal on init
2. Remove `in_goal_target` and `in_goal_months` widget keys from `_INPUT_KEYS`
3. In `render_step1()`, replace the two number inputs with a dynamic goal list:
   - Loop over `S.goals`, render 4 inputs per goal (name, target, current_saved, months) in a 4-column row
   - "＋ Add goal" button (disabled if 5 goals already)
   - "✕" remove button per goal (disabled if only 1 goal)
4. Replace `_goal_card()` with `_goal_cards()` that loops over `S.goals` and calls `goal_plan()` for each
5. Update `_build_profile_dict()` to include `goals` list and first goal's `name` as the `goal` string
6. Update `_load_profile()` to seed one goal from the profile's `savings_goal` text and zero target/months
7. Update `_clear_profile()` to reset to one empty goal

**Relevant Context:**
- `_goal_card()` function — calls `goal_plan()` from `tools/core/finance.py` (already imported as `_goal_plan`)
- `goal_plan()` signature: `(target_amount, months_to_goal, current_saved, monthly_headroom, annual_rate=0.0)`
- `_headroom()` helper already computes free cash — divide by number of goals as a simple allocation
- `_build_profile_dict()` — add `goals` key as a list of dicts

**Status:** `[ ] pending`

---

## Sub-Task 3 — Save / Load Profile (no server needed)

**Intent:** Let users export their full profile (including goals and debt table) as a JSON file, and re-import it on a future visit. No database, no login, no server — the file lives on the user's machine.

**Expected Outcomes:**
- "⬇ Save profile" button on Step 1 → downloads `finpath_profile_YYYY-MM-DD.json` containing all session fields
- "⬆ Load profile" file uploader on Step 1 → reads the JSON and calls `_load_profile_from_dict()` to populate all session state
- Saved file includes: all income/expense/savings breakdown fields, goals list, debt table, debt rate, savings contrib
- Loading a saved file is equivalent to selecting a sample profile — all widget keys updated immediately
- Invalid/corrupt files show an error message, don't crash

**Todo List:**
1. Write `_export_profile() -> str` — serialises all current session state fields to a JSON string (only financial fields, not chat history or thread_id)
2. Add `st.download_button("⬇ Save profile", data=json_str, file_name=..., mime="application/json")` at the bottom of the sample profiles section on Step 1
3. Add `st.file_uploader("⬆ Load a saved profile", type="json", key="profile_upload")` above the download button
4. Write `_load_profile_from_dict(d: dict)` — reads the exported JSON dict and populates all session keys and widget keys (same pattern as `_load_profile()`)
5. On file upload: parse JSON, call `_load_profile_from_dict()`, call `st.rerun()`
6. Wrap the parse in try/except — on failure show a styled error: "Could not read profile file — make sure it was saved by FinPath AI"

**Relevant Context:**
- `_load_profile()` pattern (lines ~210–230) — writes both `S.key` and `st.session_state["in_key"]`
- `_clear_profile()` — shows the full list of keys to reset
- `st.download_button` already used in Step 3 for conversation summary (same pattern)
- `st.file_uploader` — standard Streamlit component, returns a file-like object; read with `json.load()`
- No new dependencies needed

**Status:** `[ ] pending`

---

## Files Changed

| File | Changes |
|---|---|
| `app/main.py` | All UI changes — sub-tasks 1, 2, 3 |
| `app/main.py` `_build_profile_dict` | Add breakdown fields + goals list |
| No new tool files | `goal_plan()` already exists and imported |
| No agent YAML changes | Agent already receives `_build_profile_dict()` output |

---

## What stays the same

- `tools/core/finance.py` — no changes needed
- `app/api_client.py` — no changes needed
- `agents/finpath_agent.yaml` — agent already handles goals via `goal_plan` tool; the richer profile context in the message will be used automatically
- All 193 existing tests — no changes needed
- The 3-step wizard structure — only Step 1 changes
