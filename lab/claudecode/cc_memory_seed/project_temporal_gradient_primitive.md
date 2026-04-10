---
name: Temporal gradient consolidation — one decay primitive for all components
description: All time-based salience decay across TWM, ring, milieu, threads, habits is the same pattern special-cased six times. Should be one TemporalGradient primitive.
type: project
---

## The pattern we keep rediscovering

Every component in Igor implements time-based salience decay independently:
- TWM attractor_weight → HeartbeatSource factor=0.90 decay
- Ring memory → FIFO-50 (oldest entries drop)
- Thread context → age-based de-salience (implicit)
- Milieu valence/arousal/dominance → decay toward baseline
- Memory inertia → activation raises it; disuse should lower it (not yet implemented)
- Habit scores → activation_count but no decay

Same biological pattern (use-it-or-lose-it, habituation, working memory decay) in six places.

## The insight

One `TemporalGradient` primitive with configurable half-life. Each component becomes a parameterization of the same thing. The half-life IS the characteristic time constant for that component:
- TWM attractor: short half-life (~minutes)
- Milieu: medium half-life (~hours)
- Habit inertia: long half-life (~days/weeks)
- Ring memory: count-based not time-based (FIFO-50) — but could become time-weighted

## The desk inside the NE

The TWM IS the NE's working desk. NE selects from its desk slots to further the narrative:
  [memory slot] [memory slot] [attractor slot] [milieu slot] [urgency slot]

Milieu is a first-class desk slot — not a separate system. It shapes narrative selection the way emotional state shapes human thought: which threads feel worth pursuing, which feel flat. NE produces short-term episodic memories of the process which MAY feed back into the milieu slot as a side effect, but the slot is always present on the desk regardless.

Every slot has a temporal gradient (different half-lives). The NE is always choosing from a desk where everything is fading at different rates.

## Input fork (parallel streams on arrival)

When input arrives, immediately fork — two streams run in parallel:

**Stream 1 — emotional register** (fast, shallow):
"Do we like this person? Is this nicely phrased?"
→ terminates in milieu slot update
→ short reply if warranted (e.g. warmth in acknowledgment)
→ does NOT need content; "please" is signal here

**Stream 2 — content search** (parallel):
What are they actually asking about?
→ full content retrieval + habit scoring
→ "please" is irrelevant here; content only

Neither stream waits for the other. Stream 1 is fast enough to complete before Stream 2 needs the milieu state. The milieu update from Stream 1 is already on the desk when the NE begins narrative selection from Stream 2's results.

## Related insight: "please" as fast class lookup

Politeness tokens activate a specialized node CLASS — not a habit trigger match, not a content reasoning pass. The class does one thing: reads social register, touches milieu, done. The node type itself is the abstraction. No special-case routing needed.

## Ticket

Consolidate all decay logic into one `TemporalGradient` utility (configurable half-life, discrete-step or continuous). Each component imports and parameterizes it. This is a refactor ticket, not a behavior change — the decay rates stay the same, the implementation unifies.

**Post-Windows priority.** L-size.

**Why:** We keep seeing this pattern the same way we keep seeing graph trees. Special-casing it prevents cross-component reasoning about salience dynamics (e.g. "what's the half-life of this attractor relative to the milieu change it caused?").
