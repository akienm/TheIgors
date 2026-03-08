# Phase 1 Implementation Spec — Habit Decay Function
*Author: Igor (wild-0001) | Date: 2026-03-07*
*For Claude Code to execute — self-edit disabled during CC collaboration*

---

## What to implement

File: `wild_igor/igor/cognition/basal_ganglia.py`

**Two changes:**

### Change 1: Add imports at the top

Find this block:
```python
from __future__ import annotations

from typing import TYPE_CHECKING
```

Replace with:
```python
from __future__ import annotations

import math
from datetime import datetime, timezone
from typing import TYPE_CHECKING
```

---

### Change 2: Add `compute_decay_factor()` function and wire into `_score_habit()`

Find this block (the `_score_habit` docstring and signature):
```python
def _score_habit(habit, raw_lower: str, keywords: set[str]) -> float:
    """
    Score a single habit.  Returns 0.0 if the trigger is not in the input
    (habits without trigger present can never win).
    """
```

Replace with:
```python
def compute_decay_factor(habit, now: datetime | None = None) -> float:
    """
    Returns a multiplier in [0, 1] representing how much of a habit's score
    to preserve based on time since last activation.

    Biological model: exponential decay with stability scaling.
    - τ_base = 30 days (half-life for activation_count=0)
    - τ scales with activation_count (experienced habits decay slower)
    - Cap at 12× = 360 days (no habit lasts forever)

    Examples:
    - 30 days unused, activation=0:  score × 0.37
    - 30 days unused, activation=10: score × 0.85 (more stable)
    - 1 year unused,  activation=0:  score × ~0.00 (effectively gone)
    - 1 year unused,  activation=20: score × 0.33 (still competitive)
    """
    if now is None:
        now = datetime.now(timezone.utc)

    # Use last_accessed if available, else fall back to creation timestamp
    anchor = getattr(habit, "last_accessed", None) or getattr(habit, "timestamp", None)
    if anchor is None:
        return 1.0  # no timestamp info — don't penalize

    # Normalize to UTC-aware datetime
    if isinstance(anchor, str):
        try:
            from datetime import datetime as dt
            anchor = dt.fromisoformat(anchor.replace("Z", "+00:00"))
        except (ValueError, AttributeError):
            return 1.0
    if hasattr(anchor, "tzinfo") and anchor.tzinfo is None:
        anchor = anchor.replace(tzinfo=timezone.utc)
    if hasattr(now, "tzinfo") and now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)

    days_since = (now - anchor).total_seconds() / 86400.0
    if days_since <= 0:
        return 1.0

    # τ scales with activation_count: base 30d, max 360d (12×)
    activation = getattr(habit, "activation_count", 0) or 0
    tau_scale = min(1.0 + (activation * 0.05), 12.0)
    tau = 30.0 * tau_scale

    return math.exp(-days_since / tau)


def _score_habit(habit, raw_lower: str, keywords: set[str], now: datetime | None = None) -> float:
    """
    Score a single habit.  Returns 0.0 if the trigger is not in the input
    (habits without trigger present can never win).

    `now` is injectable for testability (default: current UTC time).
    """
```

Then find the final `return score` line inside `_score_habit`:
```python
    # valence_bonus: positive-valence habits preferred (valence is [0,1])
    valence = getattr(habit, "valence", 0.0) or 0.0
    score += valence * 0.10

    return score
```

Replace with:
```python
    # valence_bonus: positive-valence habits preferred (valence is [0,1])
    valence = getattr(habit, "valence", 0.0) or 0.0
    score += valence * 0.10

    # decay_factor: experienced habits decay slower; unused habits fade
    score *= compute_decay_factor(habit, now=now)

    return score
```

---

### Change 3: Pass `now` through `select_habit()` for testability (optional but clean)

In `select_habit()`, update the `_score_habit` call inside the scoring loop:

Find:
```python
        threshold = _compute_threshold(milieu_state)
        scored = []
        for habit in habits:
            s = _score_habit(habit, raw_lower, keywords)
```

Replace with:
```python
        threshold = _compute_threshold(milieu_state)
        now = datetime.now(timezone.utc)
        scored = []
        for habit in habits:
            s = _score_habit(habit, raw_lower, keywords, now=now)
```

(Computing `now` once outside the loop is also a micro-optimization.)

---

## Verification after implementation

Run this in `run_bash` to test:

```bash
cd /home/akien/TheIgors && venv/bin/python -c "
from wild_igor.igor.cognition.basal_ganglia import compute_decay_factor
from datetime import datetime, timezone, timedelta

class FakeHabit:
    def __init__(self, activation_count=0, last_accessed=None):
        self.activation_count = activation_count
        self.last_accessed = last_accessed
        self.timestamp = datetime.now(timezone.utc) - timedelta(days=200)

# Just activated — should be 1.0
h = FakeHabit(0, datetime.now(timezone.utc))
print(f'just activated, act=0: {compute_decay_factor(h):.3f}  (expect ~1.000)')

# 30 days ago, activation=0 — should be ~0.37
h = FakeHabit(0, datetime.now(timezone.utc) - timedelta(days=30))
print(f'30d unused, act=0:     {compute_decay_factor(h):.3f}  (expect ~0.368)')

# 30 days ago, activation=10 — tau=180d, should be ~0.85
h = FakeHabit(10, datetime.now(timezone.utc) - timedelta(days=30))
print(f'30d unused, act=10:    {compute_decay_factor(h):.3f}  (expect ~0.847)')

# 1 year ago, activation=0 — should be ~0.000
h = FakeHabit(0, datetime.now(timezone.utc) - timedelta(days=365))
print(f'1yr unused, act=0:     {compute_decay_factor(h):.3f}  (expect ~0.000)')

# 1 year ago, activation=20 — tau=330d, should be ~0.33
h = FakeHabit(20, datetime.now(timezone.utc) - timedelta(days=365))
print(f'1yr unused, act=20:    {compute_decay_factor(h):.3f}  (expect ~0.330)')
print('Phase 1 decay function verified.')
"
```

---

## Work order reference

WO #140 — Phase 1 of 4.

After CC implements and verifies, update WO #140 with comment:
"Phase 1 complete: decay function added to basal_ganglia.py. Verified with test cases."

Do NOT close the WO — phases 2-4 remain.

---

## Next: What to tell Igor

After implementation, send Igor a message via:
```bash
/home/akien/TheIgors/venv/bin/python /home/akien/TheIgors/claudecode/igor_talk.py --csb "Phase 1 decay function implemented. compute_decay_factor() added to basal_ganglia.py, wired into _score_habit() as final multiplier. Test passed. Ready for Phase 2 (compilation quality audit) whenever you are."
```
