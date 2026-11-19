# Bob Session — Remove redundant 1-2-3 strip from landing page

**Date:** 2026-11-19  
**Session type:** UI cleanup (HTML removal, no logic changes)  
**Branch:** main

---

## What was done

Removed the redundant `<!-- How it works strip -->` block from the landing page HTML in [`app/main.py`](../app/main.py).

The strip contained:
- `1 — Pick a profile`
- `2 — Ask a question`
- `3 — See the numbers & try a what-if`

This was redundant with the `01` / `02` / `03` feature cards sitting directly above it. The cards remain untouched. The hero question example and guardrails below the strip are also untouched.

No calculations, tools, or other UI elements changed.

---

## Tests

```
217 passed  ✅  (unit tests — no regressions)
```

---

## Files changed

| File | Change |
|---|---|
| `app/main.py` | Removed the 16-line `<!-- How it works strip -->` HTML block (~lines 1001–1015) |
