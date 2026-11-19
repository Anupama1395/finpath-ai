# Bob Session — Fix truncated follow-up suggestion chips (Step 3)

**Date:** 2026-11-19  
**Session type:** CSS fix (no logic, calculation, or tool changes)  
**Branch:** main

---

## Problem

Follow-up suggestion chips on Step 3 were clipping their text. Streamlit renders button labels inside inner `<p>` / `<span>` / `<div>` elements that can inherit or apply `overflow:hidden` and `text-overflow:ellipsis`, causing long question text to be truncated rather than wrapped.

The `.sug-btn` rule already had `white-space:normal!important` and `height:auto!important` on the `<button>` itself, but the inner child elements were still clipping.

---

## Fix

**File:** [`app/main.py`](../app/main.py) — global CSS block (~line 118)

Added `overflow:visible!important` to the existing `.sug-btn .stButton button` rule, and added a new child-element rule targeting `p`, `span`, and `div` inside the button:

```css
.sug-btn .stButton button{
  /* existing rules … */
  overflow:visible!important
}
.sug-btn .stButton button p,
.sug-btn .stButton button span,
.sug-btn .stButton button div{
  white-space:normal!important;
  overflow:visible!important;
  text-overflow:unset!important;
  display:inline!important
}
```

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
| `app/main.py` | Added `overflow:visible` to `.sug-btn` button rule; added child-element rule to prevent text clipping |
