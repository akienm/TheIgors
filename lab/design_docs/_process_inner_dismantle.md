# _process_inner dismantle plan

Deliverable for T-process-inner-dismantle.

`main.py._process_inner` runs from line 3531 to approximately line 6976 —
3445 lines. This document maps its natural phases, identifies seam lines and
data handoffs, and proposes a phased extraction sequence.

---

## Why this matters

- **Audit**: Static analysis tools hit method-size limits on `_process_inner`.
  The 3-pass audit cannot reason about code it cannot fully hold in context.
- **Self-observation**: Igor cannot reason about his own processing loop when
  the loop is a 3400-line monolith. Extraction is a prerequisite for
  T-igor-programs-himself.
- **Concurrency**: Concurrent settling (T-concurrent-ne-spawn) requires
  identifiable phase boundaries — you can't parallelize phases you can't name.

---

## Phase map

| Phase | Lines (approx) | LOC | Purpose |
|-------|---------------|-----|---------|
| 1 — Input Observation | 3531–3678 | ~150 | Turn instrumentation, raw input capture, relationship frame detection, repair detection, verbatim trace push to TWM |
| 2 — Thalamus Parsing | 3777–3874 | ~100 | Intent, complexity, routing directives, task detection, nexus traffic |
| 3 — Memory Retrieval & Traversal | 3998–4594 | ~600 | Keyword-based search, interpretive tree traversal, competitive forking |
| 4 — Preparse & Complexity Scoring | 4596–4725 | ~130 | Complexity estimate, tier routing decision, milieu/NE modulation |
| 5 — Job Routing Decision | 4743–4847 | ~100 | Background-vs-foreground choice; early return if backgrounded |
| 6 — Habit Selection & Dispatch | 4927–5710 | ~800 | Trigger match, gate checks, habit type dispatch (question/schema/code_ref/engram/fork/if_fork) |
| 7 — LLM Reasoning | 5710–6080 | ~370 | Tier.0 Python / TurnPipeline / Gateway; tool extraction & synthesis |
| 8 — Output Gating | 6089–6745 | ~650 | Task completion detection, identity gating, tool result verification, coherence check, action claim validation |
| 9 — Episodic Storage & Ring | 6258–6435 | ~180 | Episodic memory write, ring entry, word/generation graph index |
| 10 — Metrics & Telemetry | 6437–6579 | ~140 | Latency rings, friction, ROI, turn trace close, milieu update, dashboard flush |
| 11 — Turn Finalization | 6631–6845 | ~210 | Episode binding, relationship accretion, deferred task dispatch, TWM flush |

**Note**: Phases 8 and 9 overlap in line range (both touch 6258–6435). This is
an interleaving — not a seam-clean boundary. Phase 9 should be extracted after
Phase 8 gate logic is isolated.

---

## Data handoffs between phases

```
Input Observation ──── turn_id, episode_binder, frame_facia_id ────────►
Thalamus Parsing ────── parsed.intent, parsed.complexity, parsed.keywords ►
Memory Retrieval ──────────────────────────────── relevant[], interp ────►
Complexity Scoring ───────────────────── _skip_to (tier), _routing_reason ►
Job Routing ────────── _async_job_id (→ early return) OR tier continues ──►
Habit Dispatch ──────────────────── habit, response_text (or fall-through) ►
LLM Reasoning ──────────────── response_text, cost, used_api ────────────►
Output Gating ─────────────────────────────── cleaned response_text ──────►
Episodic Storage ─────────────────────── memory_id, links ───────────────►
Metrics ─────────────────────────────── turn trace closed ───────────────►
Turn Finalization ───────────────────── return response_text ────────────►
```

Phases are data-clean: each phase consumes the output of prior phases.
No circular references detected. This means extraction can proceed
phase-by-phase without cross-cutting refactors.

---

## Proposed module splits

| Module | Phases | Notes |
|--------|--------|-------|
| `cognition/input_observation.py` | Phase 1 | Relationship frame, repair detection, TWM push |
| `cognition/thalamus_phase.py` | Phase 2 | Already exists as `thalamus.py`; this is the *calling* wrapper |
| `cognition/memory_phase.py` | Phase 3 | search + interpretive_traverse + competitive forking |
| `cognition/routing_phase.py` | Phases 4–5 | Preparse, complexity scoring, tier decision, NE routing, background gate |
| `cognition/habit_dispatch.py` | Phase 6 | All habit type dispatchers; gate checks; coherence pre-gate |
| `cognition/reasoning_phase.py` | Phase 7 | Tier.0, TurnPipeline, Gateway, tool dispatch |
| `cognition/output_gates.py` | Phase 8 | Coherence, identity, action-claim, task completion |
| `cognition/consolidation_phase.py` | Phases 9–10 | Episodic store, ring, graphs, latency/friction/ROI telemetry |
| `tools/pr_accretion.py` | Phase 11 (partial) | Already exists; bind tighter — episode binding + accretion extracted here |

---

## Extraction sequence (phased, safest-first)

### Phase A — Telemetry (least entangled)
Extract Phase 10 (Metrics & Telemetry) first. It reads existing state and
writes to rings/dashboard but has no downstream consumers within
`_process_inner`. Zero functional risk; validates the extraction scaffolding.

### Phase B — Storage (downstream of everything)
Extract Phase 9 (Episodic Storage & Ring). It is a consumer of `response_text`
and `parsed` but produces nothing consumed within `_process_inner`. Low risk.

### Phase C — Input + Thalamus
Extract Phases 1–2 together. They are produced-only (no consumption within
`_process_inner` before line 3678). These two phases currently share the
`parsed` object as their primary output — extract together to avoid a split
return shape.

### Phase D — Routing (Phases 4–5)
Extract Complexity Scoring + Job Routing together. Both consume `relevant` and
emit `_skip_to` + `_async_job_id`. The early-return for backgrounded jobs
must be preserved as a return from the routing function (not a bare return
from `_process_inner`).

### Phase E — Memory Retrieval
Extract Phase 3. Largest single extraction (~600 LOC). Introduces a `MemoryPhaseResult`
datatype to carry `relevant[]`, `interp`, traversal traces. This is the riskiest
extraction because of the competitive forking logic — needs a matching test suite
first.

### Phase F — Output + Finalization
Extract Phases 8 + 11 together. Entangled: Phase 11 reads Phase 8 gate outputs.
Consider a single `cognition/output_phase.py` that runs gate + finalization.

### Phase G — Habit Dispatch + LLM Reasoning
Extract Phases 6–7 last. Most entangled with global state. Largest combined LOC.
Do after all other phases are stable and their interfaces are locked.

---

## Prerequisites before starting extraction

1. Full test coverage for `_process_inner` exit paths — currently sparse.
   The existing integration tests (pe_chain, habit execution) provide partial
   coverage but do not exercise all gate paths. At minimum: one test per
   phase boundary (correct data passed in → correct data out).
2. A `PhaseContext` dataclass or similar to pass turn-scoped state between
   extracted phases without relying on `_process_inner` local variables.
3. Agreement on whether phases are called as functions or as methods on a
   `TurnProcessor` object. Recommendation: functions first (easier to test);
   migrate to `TurnProcessor` if state sharing becomes unwieldy.

---

## Pass condition (per T-process-inner-dismantle)

This doc exists at `lab/design_docs/_process_inner_dismantle.md` and names:
- the proposed phases (11 phases named above) ✓
- their boundaries (line ranges and LOC) ✓
- the sequencing for extraction (Phases A → G above) ✓

Implementation begins under a separate ticket (not this one).
