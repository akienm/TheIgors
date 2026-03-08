# Habit Decay & Compilation — Design Document
*Author: Igor (wild-0001) | Date: 2026-03-07*
*Purpose: Joint design session with Claude Code, approved by Akien*

---

## The Goal (Akien's framing)

Success at this will train Igor to be better at habit-making in general.
That's the biggest win — not just the mechanics, but building a self-reinforcing
loop where habit-making improves through use.

Budget context: ~$122 on Anthropic, ~$61 on OpenRouter.
Both agents are authorized to read/write/execute in ~/home.

---

## Current State of Habits

### What exists today

**`memory/models.py`** — Memory dataclass:
- `activation_count` — how many times a habit has fired
- `timestamp` — when the memory was created
- `last_accessed` — last time it fired (added in #128)
- `inertia` — composite property: base + usage_boost + children_boost + friction_boost + arousal_boost
- `is_habit` — any memory with a `metadata.trigger` key is a habit
- No decay function. Habits, once compiled, persist forever at their current inertia.

**`cognition/basal_ganglia.py`** — Habit selection:
- Parallel scoring: trigger_score + keyword_bonus + activation_bonus + inertia_bonus + valence_bonus
- Lateral inhibition: winner takes all
- Milieu-modulated threshold (high arousal → lower threshold)
- COMPILE_PHRASES → immediate route to PROC_HABIT_COMPILER
- No decay. Old unused habits compete equally with fresh active ones.

**Problem**: A habit compiled once stays "hot" forever. A habit that was relevant
3 months ago but no longer fires pollutes the scoring space. A new habit with low
activation_count has to fight against stale habits with high activation_count that
haven't fired recently. This is the opposite of how biological habits work.

---

## The Decay Function

### Biological model
Human procedural memory decays with time-since-last-use (not just time-since-encoding).
The forgetting curve is roughly exponential: `strength = S * e^(-t/τ)` where τ is the
stability constant (higher activation → more stable, slower decay).

### Previous approach (Akien's note)
Last time we did this with a timestamp and a TTL. Simple cutoff — if `last_accessed`
is older than TTL, the habit is filtered out before scoring. Clean, but brutal.
Problem: hard cutoff loses habits that were "almost" relevant, and TTL is arbitrary.

### Proposed: soft exponential decay with stability scaling

```python
def compute_decay_factor(habit: Memory, now: datetime) -> float:
    """
    Returns multiplier in [0, 1] — how much of the habit's score to preserve.
    1.0 = no decay (just activated). 0.0 = fully decayed.

    τ_base = 30 days (half-life for a habit activated once)
    τ scales with activation_count — more experienced habits decay slower.
    """
    if habit.last_accessed is None:
        # Never activated — use creation timestamp, decay immediately
        anchor = habit.timestamp
    else:
        anchor = habit.last_accessed

    days_since = (now - anchor).total_seconds() / 86400.0
    if days_since <= 0:
        return 1.0

    # τ scales: base 30d, max 365d for very experienced habits
    τ_base = 30.0
    τ_scale = min(1.0 + (habit.activation_count * 0.05), 12.0)  # cap at 12x = 360d
    τ = τ_base * τ_scale

    import math
    return math.exp(-days_since / τ)
```

**Application**: in `basal_ganglia._score_habit()`, multiply final score by decay_factor.
Very simple integration — one additional factor in the scoring pipeline.

Habits that haven't fired in:
- 30 days (activation_count=0): score × 0.37 (e^-1)
- 30 days (activation_count=10): τ=180d → score × 0.85 (barely decayed)
- 1 year (activation_count=0): score × 0.0 (effectively gone)
- 1 year (activation_count=20): τ=330d → score × 0.33 (still competitive)

This is better than a hard TTL because:
- Experienced habits survive longer naturally (earned stability)
- New habits aren't killed by a sudden cut-off
- The decay is continuous, not abrupt

---

## Habit Compilation Improvements

### Current PROC_HABIT_COMPILER
When a COMPILE_PHRASES trigger fires, the habit compiler runs. But we don't have
a clear picture of what it actually does. Need to audit `PROC_HABIT_COMPILER`
memory and the handler in `main.py`.

### What good habit compilation looks like

A well-compiled habit should store:
```python
{
    "trigger": "whenever [X]",       # the cue
    "action": "...",                  # the response
    "context": "...",                 # when it applies
    "needs_met": ["..."],             # what needs does this habit serve
    "replacement_for": "...",         # if it replaces another habit
    "habit_type": "response",         # null | "response" | "question"
    "compiled_at": "ISO timestamp",   # when compiled
    "compiled_from_count": 3,         # how many episodic memories triggered this
}
```

### Training loop: habit improves through use

The big win Akien mentioned: success at this trains better habit-making.

The loop:
1. User/system says "build a habit for: X — whenever Y, Z"
2. HABIT_COMPILER stores PROCEDURAL memory with above structure
3. Habit fires in scoring, accumulates `activation_count`, updates `last_accessed`
4. After enough activations (threshold=5?), NE reviews the habit: 
   - Is it actually reducing friction?
   - Is the trigger too broad or too narrow?
   - Should it be promoted to higher inertia?
5. NE can refine the trigger, update `needs_met`, or flag for Akien review
6. Habits with negative friction_history automatically get decay_factor penalty

This creates a **feedback loop**: compile → fire → evaluate → refine → fire better.

---

## G7 Additions: Question-Habits & Response-Habits

### Response-habits (bypass LLM entirely)
```python
# habit stored with habit_type = "response"
# metadata["response_template"] = "Here's my ring memory: {ring_content}"
# On trigger: expand template, return directly, no API call

# Example:
{
    "trigger": "/refresh",
    "habit_type": "response",
    "response_template": "ring_content"  # special key → evaluate at runtime
}
```

### Question-habits (proactive inquiry)
```python
# habit stored with habit_type = "question"
# metadata["question_template"] = "What triggered this feeling of {emotion}?"
# On trigger: emit question to user without LLM call

# Example:
{
    "trigger": "i'm frustrated",
    "habit_type": "question",
    "question_template": "What specifically happened just before you felt frustrated?"
}
```

---

## Implementation Plan

### Phase 1: Decay function (small, safe, measurable) — ~2h
1. Add `compute_decay_factor(habit, now)` to `cognition/basal_ganglia.py`
2. Apply it in `_score_habit()` as a final multiplier
3. No model changes needed (last_accessed + timestamp already exist)
4. Test: compile a habit, artificially set `last_accessed` to 100 days ago, verify it loses

### Phase 2: Compilation quality improvement — ~3h  
1. Audit current PROC_HABIT_COMPILER handler in main.py
2. Improve the compiler prompt to extract trigger/action/context/needs_met
3. Add `compiled_from_count` tracking
4. Store `compiled_at` timestamp

### Phase 3: G7 habit_type field — ~2h
1. Update PROC_HABIT_COMPILER to store `habit_type` field
2. Add `cortex.get_response_habits()` and `cortex.get_question_habits()` filters
3. Modify `main._run_turn()` to short-circuit on response_habit (skip LLM)
4. Question-habits: emit proactively in output before LLM call

### Phase 4: NE feedback loop — ~4h (multi-session)
1. NE gains: "review high-activation habits for friction"
2. Habits with avg_friction > 0.7 → NE flags for refinement
3. NE can propose updated trigger (weaker claim → "available for Akien to review")
4. This is the training loop that makes habit-making self-improving

---

## Priority Ranking

| Item | Impact | Effort | Priority |
|------|--------|--------|----------|
| Decay function | High (removes stale noise) | 2h | **1** |
| Compilation quality | High (better habits from the start) | 3h | **2** |
| G7 habit_type (response shortcuts) | High (cuts API cost) | 2h | **3** |
| G7 question-habits | Medium (proactive inquiry) | 2h | **4** |
| NE feedback loop | Very High (training loop) | 4h | **5** |

Start with Phase 1 — it's the safest change and immediately improves the scoring quality.

---

## Files to Touch

| File | Inertia | Change |
|------|---------|--------|
| `cognition/basal_ganglia.py` | LOW (0.30) | Add decay_factor to _score_habit() |
| `main.py` | MEDIUM | Short-circuit on response_habit; audit HABIT_COMPILER |
| `memory/models.py` | HIGH (0.95) | NO CHANGES NEEDED — fields already exist |
| `cognition/narrative_engine.py` | MEDIUM | Phase 4: habit review integration |

---

## Open Questions (for Claude Code to weigh in on)

1. **Decay cap**: Should fully-decayed habits (factor < 0.01) be explicitly filtered out
   before scoring, or just score near-zero? Filter is slightly faster; near-zero means they
   can still be resurrected by a strong trigger.

2. **τ_scale ceiling**: `12x` gives max τ=360d. Is that too long? Too short?
   A daily-use habit should probably survive years (activation_count would be ~365+,
   giving τ >> 365d). Consider: τ_scale = log(activation_count + 1) instead of linear.

3. **Compilation trigger**: Should "build a habit for: X" also store the episodic memory
   that prompted it? That would let us track `compiled_from_count` naturally.

4. **Test harness**: How do we verify decay without waiting 30 days? Propose:
   - `basal_ganglia._score_habit()` accepts optional `now` parameter (default: datetime.now())
   - Tests pass a shifted `now` to simulate future
   - This is clean and doesn't require DB manipulation

---

## Notes on Budget Discipline

With ~$122 Anthropic and ~$61 OR, we're comfortable for a few sessions of substantive work.
The Phase 1 decay function is the safest first step — small, self-contained, testable.
Each phase should be validated before moving to the next.
