# D-tracking-system-redesign-2026-05-18
**title:** Add goals layer, hypothesis tracking, outcomes, evals, and auto-validation to the tracking system
**date:** 2026-05-18
**status:** open
**spawned_tickets:** T-goal-skill, T-audit-goal, T-goal-blocked, T-hypothesis-extract, T-audit-hypothesis, T-outcome-skill, T-weekly-retro, T-weekly-evals, T-questions-skill, T-auto-validate, T-challenge-step, T-workflow-skill, T-day-close-friday

## Decision narrative
The current tracking system (decisions → tickets) is strong on activity and weak on outcomes — 1089 done tickets with no measurement of whether they helped. Adding a goals layer above decisions, mandatory hypothesis extraction at /decided time, outcome measurement at decision close, weekly evals, and auto-validation for low-risk tickets closes the learning loop. The system will track whether decisions actually achieve their stated hypotheses, feeding back to goal KRs. Every audit step gets a "is there a better way?" challenge question. The /workflow skill makes the whole system navigable after any absence.

## Hypothesis
By making goals, hypotheses, and outcomes first-class tracked objects (not just implied in conversation), the system will produce measurable evidence of whether design decisions are working — and Akien's unvoiced hypotheses will survive compaction and accumulate into a track record.

## Measurement signal
/outcome verdicts accumulate on decisions; weekly-retro tracks confirmation rate; eval-run shows capability KR trends. Within 30 days: at least 3 /outcome verdicts recorded, weekly-retro running Fridays, eval-run producing weekly snapshots.
