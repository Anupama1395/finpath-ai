# Bob Session — "How FinPath AI works" RAG line

**Date:** 2026-11-19  
**Session type:** UI copy update (single line, no logic changes)  
**Branch:** main

---

## What was done

Added one line to the `"ℹ️ How FinPath AI works"` expander in [`app/main.py`](../app/main.py) at line 1873:

> "For knowledge questions, the agent retrieves from our 4-doc knowledge base and cites the source."

Inserted between the ASCII flow diagram and the existing disclaimer sentence. No calculations, tools, or other UI elements were changed.

---

## Tests

```
217 passed  ✅  (unit tests — no regressions)
```

---

## Files changed

| File | Change |
|---|---|
| `app/main.py` | Added one RAG sentence to the "How FinPath AI works" expander (line 1873) |
