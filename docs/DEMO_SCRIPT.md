# FinPath AI — Demo Script (3 minutes)

## Setup (before recording)
1. `orchestrate env activate finpath --api-key "YOUR_KEY"`
2. `streamlit run app/main.py`
3. Open browser at `http://localhost:8501`
4. Open terminal side-by-side so viewers can see tool output logs

---

## Scene 1 — Profile & Health Card (45s)

**Say:** "FinPath AI is a financial copilot built on IBM watsonx Orchestrate. Let me show you how it works."

1. Click **"Recent Graduate"** — watch all fields update instantly (3200/2400/1500/200/8000/7%/250)
2. Point to the **health card** — "This score updates live using local math — no API call needed."
3. Point to the ring: "57 out of 100 — Needs attention."
4. Point to the priorities: "Top priority: Build a 1-month starter emergency fund. The score is calculated from 4 sub-scores — cash flow, emergency fund coverage, debt-to-income ratio, and savings rate."
5. Change income to 4000 — watch the score update in real time.
6. Change it back to 3200.

---

## Scene 2 — Goal Plan (20s)

1. Type `5000` in "Goal target ($)" and select "12 months"
2. Point to feasibility card: "At $200/month saving, this goal is **not feasible** — you need $316/month."
3. Change savings contrib to 350 — card turns green: "Feasible with $34/month to spare."

---

## Scene 3 — First Question (45s)

1. Click **"Next →"**
2. Click suggestion chip: **"How long to pay off my debt?"**
3. Click **"Ask FinPath →"**
4. Point to terminal: "Watch the terminal — you can see the exact profile being sent to the agent."
5. Reply arrives — point to tool chip: **⚙ debt_payoff_months**
6. Point to the answer: "36 months, $880.88 in total interest — every number came from the tool, not the model."

---

## Scene 4 — Follow-up (30s)

1. Click follow-up chip: **"What if I paid $100 more a month?"**
2. Reply arrives — point to comparison: "Same thread, same context — now 28 months instead of 36, saving $312 in interest."
3. Point to terminal: "Same thread ID — the agent remembers the previous answer."

---

## Scene 5 — What-if Sliders (20s)

1. Below the chat, drag the **"Extra debt payment"** slider to $200
2. Watch the debt payoff chart animate — "Debt-free 14 months sooner"
3. Drag **"Income change"** to −10% — savings chart drops

---

## Scene 6 — Multi-debt (20s)

1. Go back to Step 1 → open "Multiple debts" section
2. Show the editable table with 3 debts already filled
3. Click "Calculate" — avalanche vs snowball card appears
4. "Avalanche saves $340 more in interest over 24 months"

---

## Closing (10s)

**Say:** "FinPath AI uses IBM watsonx Orchestrate to chain 12 deterministic financial tools — the agent never computes a number itself, every figure is verified against tool output. All projections are illustrative — this is not financial advice."

---

## Key talking points for judges

- **IBM watsonx Orchestrate** — agent defined in YAML, tools imported with `orchestrate tools import`, thread continuity maintained server-side
- **Grounded outputs** — ReAct loop forces a tool call before every number; verified badge confirms no hallucination
- **Testable offline** — 148+ unit tests, zero ADK dependencies in `tools/core/finance.py`
- **Multi-turn** — same `thread_id` across follow-ups; agent explicitly compares old vs new numbers
