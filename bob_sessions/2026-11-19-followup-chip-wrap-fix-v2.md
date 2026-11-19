# Bob Session — Fix truncated follow-up chips (root cause: Streamlit DOM isolation)

**Date:** 2026-11-19  
**Session type:** CSS fix (no logic, calculation, or tool changes)  
**Branch:** main

---

## Root cause

The previous `.sug-btn .stButton button` fix had the right intent but the wrong DOM assumption. Streamlit renders each `st.button()` call inside its own isolated container (`stButton` > `stBaseButton`). When you do:

```python
st.markdown('<div class="sug-btn">', unsafe_allow_html=True)
st.button(...)
st.markdown('</div>', unsafe_allow_html=True)
```

The `<div class="sug-btn">` and the `st.button` output are **sibling nodes in the DOM** — not parent/child. So `.sug-btn .stButton button` never matches the actual button element, and `white-space:normal` was never applied.

Streamlit's internal stylesheet sets `white-space: nowrap` on button text, which is why the chips showed "WHAT IF I PAID $100 MORE A MO…".

---

## Fix

**File:** [`app/main.py`](../app/main.py) — global CSS block

Added direct `[data-testid="stBaseButton-secondary"]` rules (the actual DOM attribute Streamlit puts on secondary-kind `<button>` elements), targeting both the button itself and its inner text nodes:

```css
[data-testid="stBaseButton-secondary"] {
  white-space: normal !important;
  height: auto !important;
  overflow: visible !important;
}
[data-testid="stBaseButton-secondary"] p,
[data-testid="stBaseButton-secondary"] span,
[data-testid="stBaseButton-secondary"] div {
  white-space: normal !important;
  overflow: visible !important;
  text-overflow: unset !important;
}
```

The old `.sug-btn` rules were left in place (they still apply visual styling where they can).

---

## Tests

```
217 passed  ✅  (unit tests — no regressions)
```

---

## Files changed

| File | Change |
|---|---|
| `app/main.py` | Added `[data-testid="stBaseButton-secondary"]` wrap rules to global CSS |
