# FinPath AI — Demo Script (~2:45)

## Setup (before recording)
1. `orchestrate env activate finpath --api-key "YOUR_KEY"`
2. `streamlit run app/main.py`
3. Open the live app at https://finpath-ai-copilot.streamlit.app/
4. Open terminal side-by-side so viewers can see tool output logs

---

## Cover (0:00 – 0:10)

**Say:** "FinPath AI is a personal finance copilot built on IBM watsonx Orchestrate. In the next two and a half minutes I'll show you a live session — real agent calls, real tool outputs, real numbers."

---

## Problem (0:10 – 0:30)

**Say:** "Most people get generic advice from chatbots that make up numbers. FinPath AI is different: every figure is produced by a deterministic financial tool — the agent never computes anything itself. The result is verifiable, grounded, and safe."

---

## User (0:30 – 0:50)

1. Click **"Recent Graduate"** — watch all fields update instantly (3200 / 2400 / 1500 / 200 / 8000 / 7% / 250)
2. Point to the **health card**: "57 out of 100 — Needs attention. This score updates live using local math — no API call."
3. Point to the priorities: "Top priority: build a 1-month starter emergency fund. The score is calculated from four sub-scores — cash flow, emergency fund coverage, debt-to-income ratio, and savings rate."

---

## Live Solution (0:50 – 2:20) — 90 seconds

### Debt payoff question (0:50 – 1:30)

1. Click **"Next →"**
2. Click suggestion chip: **"How long to pay off my debt?"**
3. Click **"Ask FinPath →"**
4. Point to terminal: "Watch the terminal — you can see the exact profile being sent to the agent."
5. Reply arrives — point to tool chip: **⚙ debt_payoff_months**
6. Point to the answer: "36 months, $880.88 in total interest — every number came from the tool, not the model."

### Follow-up what-if (1:30 – 1:55)

1. Click follow-up chip: **"What if I paid $100 more a month?"**
2. Reply arrives — point to comparison: "Same thread, same context — now 28 months instead of 36, saving $312 in interest."
3. Point to terminal: "Same thread ID — the agent remembers the previous answer."

### RAG knowledge question (2:00 – 2:20)

1. Type: **"Why should I prioritise an emergency fund before investing?"**
2. Click **"Ask FinPath →"**
3. Reply arrives — point to source citation: "For knowledge questions like this, the agent retrieves from our 4-doc knowledge base — emergency funds, compound interest, debt repayment, savings rate — and cites the source."
4. Point to citation line: "Source: emergency_fund_guide.txt — grounded in the document, not the model's training data."

---

## Architecture & Ethics (2:20 – 2:35)

**Say:** "Under the hood: a ReAct loop in IBM watsonx Orchestrate drives a finpath_agent that delegates every calculation to 12 deterministic tools. For conceptual questions, finpath_kb_agent retrieves from the finpath_kb knowledge base and returns a citation. The agent never invents a number — every figure is verified against tool output."

Point to the terminal one more time: "You can see the tool name and inputs in every exchange."

---

## Close (2:35 – 2:45)

**Say:** "FinPath AI — deterministic financial tools, grounded knowledge retrieval, and full auditability, all on IBM watsonx Orchestrate. All projections are illustrative — this is not financial advice."

---

## Key talking points for judges

- **IBM watsonx Orchestrate** — agent defined in YAML, tools imported with `orchestrate tools import`, thread continuity maintained server-side
- **Grounded outputs** — ReAct loop forces a tool call before every number; verified badge confirms no hallucination
- **RAG knowledge base** — `finpath_kb` (4 documents) + `finpath_kb_agent` collaborator; every answer cites the source document
- **Testable offline** — 217 unit tests, zero ADK dependencies in `tools/core/finance.py`
- **Multi-turn** — same `thread_id` across follow-ups; agent explicitly compares old vs new numbers
