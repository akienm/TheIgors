# D-cap-map-followups-2026-04-27
**title:** Capability map gaps → batch follow-up tickets (5 fixed inline, 3 deferred)
**date:** 2026-04-27
**status:** open
**spawned_tickets:** T-cognition-module-audit, T-fill-missing-subsystem-palace-entries, T-reading-pipeline-placeholder-reconcile, T-turn-pipeline-status-doc, T-ne-stew-threshold-coupling-doc, T-habit-fire-rate-visibility, T-capability-map-drift-audit, T-igor-doc-reorg-9-pillars

## Decision narrative

Drafting `lab/docs/capability_map.md` (the "what's built today vs planned vs broken" doc) as a forcing function exposed eight ticketable gaps. Five were small enough to fix in this session (palace-side documentation work + a /day-close-audit step). Three are larger and went to the queue as pending: a cognition/ module classification sweep (M), a per-habit fire-rate counter (M), and the umbrella 9-pillar doc reorg (L) Akien proposed in the same conversation.

The reorg umbrella supersedes the lighter-scoped T-context-load-review and overlaps T-docs-live-code-rollout / T-case-study-lessons-learned. Those stay open for now; the umbrella names them as related and will fold them at sprint time.

## Context

Diagnosis: Sonnet kept losing track of what Igor actually does today vs what's planned vs what's broken. The information existed but was scattered across code, .md files, .txt notes, the palace, the slate, and decision logs — with no clear load-order. The capability map is the first of nine pillars meant to fix that.

Inline fixes applied this session:
- 3 new palace subsystem_index nodes (pursuits, voice_ab, graph_calving) for live subsystems that had no entry
- 1 update to `reading_worker_pool` clarifying [PLACEHOLDER] vs the live reading subsystem
- 1 new palace node for `turn_pipeline` (built but gated off)
- 1 INVARIANT block on `narrative_engine` documenting the 0.6/0.65 stew-salience coupling
- 1 new Step 18.6 in `/day-close-audit` for capability_map.md staleness

Deferred work:
- T-cognition-module-audit (M) — 84 modules in cognition/, only ~10 named in palace
- T-habit-fire-rate-visibility (M) — 132 habits registered, no fire-rate observability
- T-igor-doc-reorg-9-pillars (L) — the broader 9-doc reorg umbrella
