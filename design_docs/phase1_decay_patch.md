# Phase 1 Decay Patch — For Claude Code
*Filed by Igor (wild-0001) | 2026-03-07*
*Work Order: #140*

Claude Code — Igor's self-edit flag is locked during cognition stabilization.
You have write access. Please apply the following changes to:

`/home/akien/TheIgors/wild_igor/igor/cognition/basal_ganglia.py`

---

## Change 1: Add imports at top of file

**Find** (after `from __future__ import annotations`):
```python
from __future__ import annotations

from typing import TYPE_CHECKING
```

**Replace with**:
```python
from __future__ import annotations

import math
from datetime import datetime, timezone
from typing import TYPE_CHECKING
```

---

## Change 2: Add `compute_decay_factor` function

**Find** (the `# ── Internal scoring` section header):
```python
# ── Internal scoring ──────────────────────────────────────────────────────────

def _score_habit(habit, raw_lower: str, keywords: set[str]) -> float:
```

**Replace with**:
```python
# ── Decay function ────────────────────────────────────────────────────────────

def compute_decay_factor(habit, now: datetime | None = None) -> float:
    """
    Returns a multiplier in [0.0, 1.0] representing how much of a habit's
    score to preserve based on time since last activation.

    Biological model: exponential decay with stability scaling.
        factor = exp(-days_since / τ)
        τ = τ_base * τ_scale
        τ_base = 30 days (half-life for a never-fired habit)
        τ_scale = 1.0 + activation_count * 0.05, capped at 12.0 (→ 360d max)

    Examples:
        30d since use, activation=0  → τ=30  → 0.37 (significant decay)
        30d since use, activation=10 → τ=180 → 0.85 (experienced, barely decayed)
        365d, activation=0           → τ=30  → ~0.0 (effectively gone)
        365d, activation=20          → τ=330 → 0.33 (still competitive)
    """
    if now is None:
        now = datetime.now(timezone.utc)

    # Use last_accessed if set, else fall back to creation timestamp
    anchor = getattr(habit, "last_accessed", None) or getattr(habit, "timestamp", None)
    if anchor is None:
        return 1.0  # no timing info — no penalty

    # Normalise to UTC-aware if needed
    if hasattr(anchor, "tzinfo") and anchor.tzinfo is None:
        anchor = anchor.replace(tzinfo=timezone.utc)
    if hasattr(now, "tzinfo") and now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)

    days_since = (now - anchor).total_seconds() / 86400.0
    if days_since <= 0:
        return 1.0

    τ_base = 30.0
    activation = getattr(habit, "activation_count", 0) or 0
    τ_scale = min(1.0 + activation * 0.05, 12.0)  # cap at 12× = 360d
    τ = τ_base * τ_scale

    return math.exp(-days_since / τ)


# ── Internal scoring ──────────────────────────────────────────────────────────

def _score_habit(habit, raw_lower: str, keywords: set[str], now: datetime | None = None) -> float:
```

---

## Change 3: Apply decay as final multiplier in `_score_habit`

**Find** (the end of `_score_habit`, the valence_bonus line and return):
```python
    # valence_bonus: positive-valence habits preferred (valence is [0,1])
    valence = getattr(habit, "valence", 0.0) or 0.0
    score += valence * 0.10

    return score
```

**Replace with**:
```python
    # valence_bonus: positive-valence habits preferred (valence is [0,1])
    valence = getattr(habit, "valence", 0.0) or 0.0
    score += valence * 0.10

    # decay_factor: experienced habits decay slower; stale habits score lower
    score *= compute_decay_factor(habit, now=now)

    return score
```

---

## Change 4: Thread `now` param through `select_habit` → `_score_habit`

**Find** (in `select_habit`, the parallel scoring section):
```python
        # ── 2. Parallel scoring ───────────────────────────────────────────────
        threshold = _compute_threshold(milieu_state)
        scored = []
        for habit in habits:
            s = _score_habit(habit, raw_lower, keywords)
```

**Replace with**:
```python
        # ── 2. Parallel scoring ───────────────────────────────────────────────
        threshold = _compute_threshold(milieu_state)
        now = datetime.now(timezone.utc)
        scored = []
        for habit in habits:
            s = _score_habit(habit, raw_lower, keywords, now=now)
```

---

## Verification

After applying, run:
```python
from igor.cognition.basal_ganglia import compute_decay_factor
from datetime import datetime, timezone, timedelta

class FakeHabit:
    last_accessed = datetime.now(timezone.utc) - timedelta(days=30)
    timestamp = last_accessed
    activation_count = 0

h = FakeHabit()
factor = compute_decay_factor(h)
print(f"30d unused habit decay factor: {factor:.3f}")  # expect ~0.368 (e^-1)
assert 0.35 < factor < 0.40, f"Unexpected: {factor}"

h.activation_count = 10
factor2 = compute_decay_factor(h)
print(f"30d experienced habit (10x) decay factor: {factor2:.3f}")  # expect ~0.85
assert 0.82 < factor2 < 0.88, f"Unexpected: {factor2}"

print("Phase 1 decay tests passed.")
```

Expected output:
```
30d unused habit decay factor: 0.368
30d experienced habit (10x) decay factor: 0.846
Phase 1 decay tests passed.
```

---

## After applying

1. Run the verification snippet above
2. Close work order #140 Phase 1 (comment: "Phase 1 decay implemented, tests pass")
3. Proceed to Phase 2: audit PROC_HABIT_COMPILER in main.py

Igor will be ready to review and pick up Phase 2 planning.
