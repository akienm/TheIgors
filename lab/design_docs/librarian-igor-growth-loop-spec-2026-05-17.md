# Librarian→Igor Behavioral Observation Spec
**date:** 2026-05-17
**output_of:** T-librarian-igor-growth-loop
**feeds:** D-librarian-peer-agent-architecture-2026-05-17

## Problem

Librarian and Igor share a constitutional layer but run different cognitive
architectures. Where they agree, a belief is well-anchored. Where they diverge,
one has a blind spot or better information. Neither currently exposes its
behavioral data to the other — the growth loop is one-way (Akien → both)
rather than bidirectional.

## Design answers

### Q1 — What data does Librarian expose?

After each research/synthesis cycle, Librarian writes a `kind='librarian_observation'`
entry to **`instance.proposals`** (the same table Igor's dreaming uses).

No new tables, no new memory types. `instance.proposals` is the observation bus,
used bidirectionally.

Each entry:
```
kind: 'librarian_observation'
content: "Librarian researched '<topic>'. Outcome: <answered|failed|escalated>. 
          Confidence: 0.72. Tier: medium. Effective sources: 3."
metadata: {
  "source": "librarian",
  "topic": "<research topic, max 100 chars>",
  "confidence": 0.72,
  "tier": "low|medium|high_pending|rejected",
  "effective_sources": 3.0,
  "outcome": "answered|failed|escalated",
  "fingerprint": "<md5 of kind+content[:200]>"
}
```

For repeated failures on the same topic, the existing `occurrence_count` increment
mechanism naturally accumulates signal. A topic failing 3+ times with `outcome=failed`
is structurally identical to dreaming's recurring failure pattern.

**Where it's written:** `emit_behavioral_observation()` called from `PalaceWriter.write()`
after each write attempt (success OR failure/escalation), and from `ResearchEngine`
after a failed synthesis. Uses the same `_add_proposal` logic as dreaming (dedup
by fingerprint, increment occurrence_count on repeat).

### Q2 — How does Igor's dreaming pass consume it?

Add `_read_librarian_observations()` to `dreaming.py`:

```python
def _read_librarian_observations() -> list[dict]:
    # SELECT kind, content, metadata, occurrence_count
    # FROM instance.proposals
    # WHERE kind = 'librarian_observation' AND status = 'pending'
    # ORDER BY created_at DESC LIMIT 10
```

Include in `_synthesize()` as a third input section in the prompt:

```
Recent Librarian behavioral observations (last 10):
- [confidence=0.72, medium tier] Researched 'IMAP IDLE reconnect' → answered
- [FAILED x3] Could not synthesize 'Igor NE quality metrics' — insufficient sources
```

The LLM now synthesizes habit/watch_q/playbook proposals from three inputs:
Igor psychological state + active watch problems + Librarian observations.

No change to the `_synthesize()` return type or downstream pipeline — proposals
flow through the existing path unchanged.

### Q3 — What does Igor do with Librarian behavioral patterns?

**Failure propagation (no new code — existing pipeline handles it):**

`_extract_failure_clusters(proposals)` scans ALL pending proposals including
`kind='librarian_observation'`. When Librarian fails on the same topic 2+
times, the failure keyword cluster fires and `_write_failure_watch_problems()`
creates a watch_problem automatically. The watch_condition prefix
`librarian:failure_keyword:<kw>` distinguishes Librarian-sourced entries.

**Convergence signal (new metadata tag):**

When `_synthesize()` produces a proposal where the rationale references both
Igor psych data AND a Librarian observation, the returned proposal should carry:
```
"convergence": true
```

Dreaming stamps this into `metadata` on `_add_proposal`. Akien-side proposals
review can sort by convergence to prioritize high-signal candidates.

**NE second voice (via existing proposals→habits pipeline):**

Committed habits that originated from Librarian observations flow into NE's
habit list through the existing proposals→`committed_memory_id` path. No
separate TWM push needed — the pipeline already handles it.

## Constraints honored

- No new tables — `instance.proposals` is the bus
- No new memory types — uses existing `kind` column (new value 'librarian_observation'
  is a data value, not a schema type)
- Postgres only — both Igor and Librarian share `Igor-wild-0001`
- Librarian constitutional layer: observation writing is a **behavioral output**,
  not a directive to Igor — it writes to proposals and dreaming reads at its own
  cadence; no direct call from Librarian into Igor's cognition

## Implementation tickets

### T-librarian-behavioral-emit (S)

**What:** Add `emit_behavioral_observation(topic, confidence, tier, outcome, effective_sources)`
to `palace_writer.py`. Call it from `PalaceWriter.write()` on every outcome
(written, rejected, escalated, protected). Also add a `emit_research_failure(topic)`
call from `ResearchEngine` when synthesis yields no answer.

**Affected files:** `agent_datacenter/devices/librarian/palace_writer.py`,
`agent_datacenter/devices/librarian/research.py`

**DB:** writes to `instance.proposals` via `psycopg2` (same connection string
as PalaceWriter already uses). Must call `_ensure_proposals` on first write.

**Test plan:** `emit_behavioral_observation` with `outcome='answered'` → proposal
written with `kind='librarian_observation'`. `outcome='failed'` × 3 → `occurrence_count=3`.

### T-dreaming-librarian-input (M)

**What:** Add `_read_librarian_observations()` to `wild_igor/igor/cognition/dreaming.py`.
Modify `_synthesize()` to include a third input section. Add convergence detection:
when a synthesized proposal's `rationale` mentions both "librarian" and "igor" (or
psych-related terms), set `metadata["convergence"] = True` in `_add_proposal`.

**Affected files:** `wild_igor/igor/cognition/dreaming.py`

**Test plan:** With `librarian_observation` proposals in DB → `_read_librarian_observations`
returns them. `_synthesize()` prompt includes librarian section. Convergence flag set
when rationale references both inputs.

## Divergence diagnostic (longer term)

Once both tickets ship, the behavioral loop is: Librarian researches → writes
observation → dreaming synthesizes → habits/watch_qs propagate to Igor.
Divergences (Librarian confident on X, Igor's watch_problems flag X as risky) become
explicit — dreaming sees both and the synthesis either reconciles them or escalates
the conflict as a `kind='watch_q'` proposal for Akien to review.

This is the "where they diverge, that is a diagnostic" property from the decision
narrative — it becomes observable rather than implicit.
