---
name: Search depth tiers + post-habit acknowledgment fork
description: Associative search depth controlled by TWM attractor weight; post-habit fork decouples action from response; self-query gates deeper processing
type: project
---

Three connected insights from 2026-03-17 habit repair session.

## 1. Search depth tiers

`cortex.search()` should have depth tiers controlled by TWM attractor weight:
- **Shallow (default)**: high-confidence, recent, non-stale memories only. Closed/deferred excluded.
- **Medium**: normal full search
- **Deep**: includes closed, deferred, low-confidence memories — only triggered when topic becomes primary attractor

Mechanism: memory metadata field `search_depth_required: "deep"` (or similar). cortex.search() checks this against the current search depth. Search depth = f(attractor_weight for this topic).

**Implication for PROC_TASK_SUPPRESS_STALE**: the passive_capture fix applied today is a temporary band-aid. The real fix is at the search layer — closed memories shouldn't be retrieved in the first place unless attractor_weight justifies a deep search. The habit was suppressing noise that shouldn't have been fetched.

## 2. Post-habit acknowledgment fork

When a habit completes an action, instead of:
- Leaking debug text as response (the bug)
- Going silent (current passive_capture fix)

There should be a fork AFTER the action: "should I ack this?" → brief reasoning pass → generates a natural acknowledgment ("Queued for ingestion." not "Habit executed. [...]"). Action and response are decoupled. The reasoning center generates the ack, not a canned template.

Example: PROC_QUEUE_FOR_INGEST executes the queue action, THEN triggers "I should acknowledge that request" → LLM generates natural response.

## 3. Post-action self-query

After the ack fork: "anything else I should ask myself about this?"
- Low salience → automatic no (no compute spent)
- Medium salience → brief check against watchlist/open questions
- High salience → triggers deeper search, potentially escalates tier

This is the same attractor threshold controlling reasoning depth that controls search depth. Same mechanism, two layers: search depth and reasoning depth both scale with attractor weight.

## Architecture connection

- TWM attractor_weight (G50) is the signal that already exists
- search_depth_required is a new memory metadata field
- Post-habit fork could be: action habits return a "should_ack" flag → main loop routes to LLM ack pass
- Self-query could be: a lightweight tier.3 call (cheap model) that decides yes/no on deeper processing

These three form one coherent design: **salience-gated depth** — both for retrieval and reasoning.

**Why:** Suppression habits at the output layer are the wrong abstraction. The right abstraction is salience controlling depth at the retrieval and reasoning layers. Low salience = shallow + no ack. High salience = deep + full reasoning.
