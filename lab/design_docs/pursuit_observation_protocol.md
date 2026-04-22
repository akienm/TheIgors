# Pursuit Observation Protocol — minute-cadence debug

*Companion to `pursuit_layer.md` and `pursuit_programming.md`.
Use after wiring a Pursuit into an engram chain, to prove binding in vivo.
Updated 2026-04-22.*

---

## Purpose

The design doc (§5) predicts specific behavior: commitment dopamine at
spawn, optional subgoal events during, completion or abandonment at the
end. This protocol is how you **check** that the wiring actually produces
those events — with a cadence slow enough to catch stuck state, fast
enough that a human observer doesn't lose patience.

This is the minute-cadence-protocol referenced in `feedback_handhold_igor_debug_minute_cadence.md`:
stimulus → check at minute 1, 2, 3, 4 → backtrack at 5 if no advance.

---

## Prerequisites

- `IGOR_PURSUITS_ENABLED=true` in Igor's environment.
- `IGOR_BOREDOM_ENABLED=true` (since the first test-case wraps the boredom
  chain).
- Igor running; milieu sufficiently settled to trip the boredom threshold
  (`IGOR_BOREDOM_AROUSAL_THRESHOLD` default 0.08). If Igor has been idle
  ~15 min, this is usually satisfied.

---

## The check loop

At each minute after the expected commitment, read the registry and assert
one of the expected states. Use the Python snippet below (paste in
`igor repl` or run via `python -c`):

```python
from wild_igor.igor.cognition import pursuits as p
import time

for pu in p.registry().all():
    print(f"{pu.name:30} {pu.status:12} age={time.time()-pu.commitment_ts:.0f}s "
          f"events={[(e.kind,round(e.magnitude,2)) for e in pu.dopamine_trace]}")
```

---

## Expected trace

### Minute 0 (commitment)
Boredom trigger fires. A Pursuit named `address_boredom` appears with:
- `status=active`
- 1 dopamine event: `commitment` (magnitude ~0.7)
- Empty `sub_pursuits`, empty `actions_taken`

**If not seen:** the wiring in `boredom_idle.run_boredom_check` isn't firing.
Check the gate (`IGOR_PURSUITS_ENABLED`), check that `_is_bored()` returned
true, check that the rate-limit window passed.

### Minute 1 (during)
Cascade escalation, experiment tick, or wonder generation is in flight.
`address_boredom` still `active`. No completion event yet.

**If `status=abandoned` already:** the `finally` clause is firing without
`_state["posted"]` ever being set to True — something returned before the
post happened. Read `outcome` to find out where.

### Minute 2 (completion)
The wonder/cascade/experiment posted. `address_boredom` transitions to
`completed`. New events:
- `completion` (magnitude 1.0)

**If still `active` at minute 2:** `run_boredom_check` is hung — probably
blocking on cascade or experiment. This is the bug the minute-cadence
protocol is designed to surface.

### Minute 3 (persistence)
`address_boredom` is in terminal state. `registry().all()` still returns
it (no auto-clear). Next boredom trigger will create a *new* Pursuit,
leaving the old one in the registry.

**If the registry grows unboundedly:** note it. The MVP intentionally
defers GC/persistence; the staleness-based abandonment policy (open
question §9 of design doc) will handle this in a follow-up ticket.

### Minute 4 (next cycle starts)
After `IGOR_BOREDOM_COOLDOWN_SECONDS` (default 900s = 15min), a new
boredom trigger fires and a second `address_boredom` Pursuit appears.
Confirms the wrap is repeatable, not one-shot.

### Minute 5 (backtrack if no advance)
If by now no state change has occurred — no commitment, no completion,
no second cycle — the wiring is broken upstream. Back off from "observe
the Pursuit" to "observe whether the trigger fired at all":
```python
# does PROC_BOREDOM_TRIGGER even exist in habits?
# is IGOR_BOREDOM_ENABLED true?
# what does _is_bored() return on the current milieu?
```

---

## Reading the dopamine_trace

The trace is the **evidence log** of the commitment arc. A healthy arc
looks like:

```
[("commitment", 0.7), ("completion", 1.0)]
```

An abandoned-but-tried arc:

```
[("commitment", 0.7), ("abandonment", -0.5)]
```

A nested-with-subgoal arc (parent Pursuit):

```
[("commitment", 0.7), ("subgoal", 0.5), ("subgoal", 0.5), ("completion", 1.0)]
```

A stuck arc (commitment without resolution, persisting past minute 2):

```
[("commitment", 0.7)]
# ... and no events for 3+ minutes
```

Stuck arcs are the bug signature. They mean: a commitment was formed and
no downstream signal ever closed it. This is the **exact failure mode**
Pursuits were introduced to surface — and it's what the minute-cadence
protocol is designed to make visible.

---

## What to do when you see a stuck arc

1. Check `actions_taken` — did any engrams fire while the Pursuit was
   active? If yes, the engrams are decoupled from the Pursuit (not
   carrying `pursuit_id` through the basket). If no, no engrams fired at
   all — the chain didn't progress.
2. Check the parent-of-parent — if this Pursuit has a parent, is the
   parent still `suspended`? Resume should have been called by now.
3. Check whether `evaluate_completion` was ever called. The `finally`
   clause in `boredom_idle` calls it; if the function returned without
   hitting finally, that's a Python-level bug, not a Pursuit-level one.

---

## Related

- `pursuit_layer.md` — predictions this protocol checks.
- `pursuit_programming.md` — how the wrap was supposed to be written.
- `feedback_handhold_igor_debug_minute_cadence.md` — the general
  cadence pattern this specialises.
- Tickets: T-single-pursuit-test-case (this protocol validates it),
  T-reply-forms-pursuit (next Pursuit to observe once this one passes).
