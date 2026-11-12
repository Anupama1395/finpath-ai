# FinPath AI — Architecture

## System overview

```
┌─────────────────────────────────────────────────────────┐
│                    User (browser)                        │
└─────────────────────┬───────────────────────────────────┘
                      │ HTTP
┌─────────────────────▼───────────────────────────────────┐
│              Streamlit UI  (app/main.py)                 │
│                                                          │
│  Step 1: Profile  ──►  live health card (local math)    │
│  Step 2: Question ──►  suggestion chips                  │
│  Step 3: Results  ──►  multi-turn chat                   │
└─────────────────────┬───────────────────────────────────┘
                      │ ask_agent(message, profile)
┌─────────────────────▼───────────────────────────────────┐
│          api_client.py  (thin ADK wrapper)               │
│                                                          │
│  • Prepends full profile to every message                │
│  • Prints message to terminal (no secrets)               │
│  • Calls RunClient.create_run()                          │
│  • Waits for completion, extracts reply + tool names     │
└─────────────────────┬───────────────────────────────────┘
                      │ MCSP token (from ~/.wxo/)
┌─────────────────────▼───────────────────────────────────┐
│         IBM watsonx Orchestrate                          │
│                                                          │
│  Agent: finpath_agent (groq/openai/gpt-oss-120b)         │
│  Style: react_core (ReAct loop)                          │
│                                                          │
│  Rules:                                                  │
│  • Use a tool for EVERY number — never self-compute      │
│  • Quote tool summary fields verbatim                    │
│  • Multi-turn: compare new vs previous answer            │
│  • Close every reply: "not financial advice"             │
└─────────┬──────────────────────┬───────────────────────┘
          │ tool calls           │ tool results
┌─────────▼──────────┐  ┌───────▼──────────────────────┐
│  @tool wrappers     │  │  tools/core/finance.py        │
│  tools/*.py         │  │  (pure Python, stdlib only)   │
│                     │  │                               │
│  financial_health.. │  │  10 pure functions:           │
│  monthly_cash_flow  │  │  • monthly_cash_flow          │
│  project_savings..  │  │  • project_savings_growth     │
│  compare_scenarios  │  │  • compare_scenarios          │
│  emergency_fund_..  │  │  • emergency_fund_months      │
│  debt_payoff_months │  │  • emergency_fund_check       │
│  debt_vs_invest     │  │  • debt_payoff_months         │
│  stress_test        │  │  • debt_vs_invest             │
│  savings_headroom   │  │  • stress_test                │
│  emergency_fund_chk │  │  • savings_headroom           │
│  goal_plan          │  │  • financial_health_check     │
│  multi_debt_plan    │  │  • goal_plan          [NEW]   │
└─────────────────────┘  │  • debt_schedule      [NEW]   │
                         │  • savings_schedule   [NEW]   │
                         │  • multi_debt_plan    [NEW]   │
                         └───────────────────────────────┘
```

## Design principles

1. **Pure math in `tools/core/finance.py`** — zero ADK imports, stdlib only. Every function is unit-testable without credentials.

2. **Thin `@tool` wrappers** — no logic in `tools/*.py`. They only call `core.finance.*` and let the ADK handle schema generation.

3. **Agent never computes numbers** — every figure in the reply must come from a tool call. The agent YAML instructions enforce this explicitly.

4. **Profile in every message** — `api_client._build_message` prepends the full profile block to every single message, including follow-ups. The agent always has all inputs.

5. **Thread continuity** — `thread_id` is stored in `st.session_state` and passed on every follow-up call. Orchestrate maintains conversation context server-side.

6. **Local health card** — `financial_health_check` is called directly in `app/main.py` (no agent call) to render the live score card on Step 1. Fast, free, instant.

## Data flow for a typical question

```
User: "How long to pay off my debt?"
  │
  ▼
main.py: _send_message("How long to pay off my debt?")
  │
  ▼
api_client._build_message() prepends:
  "User profile: monthly_income=$3,200; debt_balance=$8,000;
   annual_debt_rate=7.00% (0.0700); monthly_debt_payment=$250; ..."
  │
  ▼
RunClient.create_run(full_message, agent_id, thread_id=None)
  │
  ▼
Orchestrate agent (ReAct loop):
  thinks → calls debt_payoff_months(balance=8000, rate=0.07, payment=250)
  tool returns: {months_to_payoff: 36, total_interest_paid: 880.88, summary: "..."}
  agent quotes summary → generates reply
  │
  ▼
api_client returns: {reply: "...", tools: ["debt_payoff_months"], thread_id: "abc123"}
  │
  ▼
main.py: appends to S.messages, renders with st.chat_message("assistant")
         shows tool chip: ⚙ debt_payoff_months
```

## Auth

The ADK (`orchestrate` CLI) stores a short-lived MCSP token in `~/.wxo/`. Refresh with:
```bash
orchestrate env activate finpath --api-key "YOUR_KEY"
```
No secrets are stored in `.env` for the UI path. The `.env` / `.env.example` are provided for reference only.
