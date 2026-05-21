# D-skill-telemetry-2026-05-20
**title:** Skill telemetry — per-skill forget-flags + improvement metrics
**date:** 2026-05-20
**status:** open
**spawned_tickets:** T-skill-telemetry-schema, T-skill-telemetry-contracts, T-skill-telemetry-logger, T-skill-telemetry-rollup, T-consequence-skill-telemetry

## Decision narrative
Add per-skill telemetry contracts (forget-flags + improvement metrics) so that CC behavioral drift is measurable and continuous skill improvement is data-driven rather than correction-dependent. Each skill gets a two-field spec defining what to log at execution time; a violation logger aggregates forget-flag trips; a monthly rollup surfaces the top recurring violations as reinforcement targets surfaced in context-load.

## Context
Emerged from Theory of Constraints discussion: the feedback loop is what lets you identify the constraint. Without execution telemetry, every skill looks equally broken or fine. Two specific problems: (1) CC forgets rules constantly and Akien manually re-states them — a violation log would surface which rules have the weakest retention; (2) there is no outcome metric per skill, so "is this skill improving?" is unanswerable. This decision builds the measurement instrument before the measurement-driven improvement work begins.

## Hypothesis
After these tickets ship, every skill execution emits a structured record, and the violation log surfaces recurring correction targets for the first time — replacing Akien's manual re-statements with a queryable signal.

## Measurement Signal
At least one skill emitting execution records within first week; violation counts per rule visible after 30 days; trend (improving/stable/degrading) per skill answerable from data.

## Goal Link
none: G-factory-factory not yet formally defined — candidate goal noted for separate /decided.

## Notes
- T-audit-feedback-build (filed same day) is complementary: audit-feedback is a static checker for whether skills HAVE feedback loops; telemetry is the runtime layer that CAPTURES the signal. Both needed.
- G-factory-factory ("build a system that can build any kind of factory") surfaced as new meta-goal; warrants its own /decided.
- Future /audit-expert expansion candidates noted: Schmidhuber, Shreya Shankar, Simon Willison, Boris Cherny lens.
