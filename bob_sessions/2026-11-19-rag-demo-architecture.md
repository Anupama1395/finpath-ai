# Bob Session — RAG Demo Script & Architecture Update

**Date:** 2026-11-19  
**Session type:** Documentation update (no code changes)  
**Branch:** main

---

## What was done

### 1. `docs/DEMO_SCRIPT.md` — replaced with ~2:45 script

The old 3-minute, 6-scene script was replaced with a tighter structured script matching the Google Doc "Demo Script":

| Segment | Timestamp | Content |
|---|---|---|
| Cover | 0:00–0:10 | Intro line — live session framing |
| Problem | 0:10–0:30 | "Chatbots make up numbers" — deterministic tools contrast |
| User | 0:30–0:50 | Recent Graduate preset, health card walk-through |
| Live Solution | 0:50–2:20 | 90 sec: debt payoff → follow-up → **RAG knowledge question** |
| Architecture & Ethics | 2:20–2:35 | ReAct loop + RAG collaborator + verified output |
| Close | 2:35–2:45 | Sign-off + disclaimer |

**New RAG line at 2:00–2:20:**
> "For knowledge questions like this, the agent retrieves from our 4-doc knowledge base — emergency funds, compound interest, debt repayment, savings rate — and cites the source."

Key talking points updated: 148+ → **217 unit tests**, added RAG knowledge base bullet.

---

### 2. `docs/ARCHITECTURE.md` — mermaid diagram updated

Added a `RAG / Knowledge Base` subgraph between `WXO` (finpath_agent) and the tool wrappers:

```
WXO  -->|"knowledge questions"|  KBA  (finpath_kb_agent)
                                   ↑
                               KB  (finpath_kb — 4 docs)
                           vector retrieval
```

- `KB` node: `finpath_kb` / `knowledge/finpath_kb.yaml` / 4 documents listed
- `KBA` node: `finpath_kb_agent` / `agents/finpath_kb_agent.yaml`
- Removed the loose `KBAgent` node that was previously dangling in the diagram
- Edge `WXO --> KBA` replaces `WXO -.->|"why / conceptual"| KBAgent`

---

## Tests

```
217 passed  (unit tests, --ignore=tests/smoke_test.py)
15 pre-existing smoke failures  (require live agent credentials — unchanged)
```

No regressions introduced. No tools, calculations, or app code were modified.

---

## Files changed

| File | Change |
|---|---|
| `docs/DEMO_SCRIPT.md` | Full replacement — new ~2:45 structured script |
| `docs/ARCHITECTURE.md` | Mermaid diagram: added RAG subgraph (finpath_kb + finpath_kb_agent) |
