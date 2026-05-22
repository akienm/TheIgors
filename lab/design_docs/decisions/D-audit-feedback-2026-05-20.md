# D-audit-feedback-2026-05-20
**title:** Add /audit-feedback skill to enforce feedback-loop completeness in all skills
**date:** 2026-05-20
**status:** open
**spawned_tickets:** T-audit-feedback-build, T-audit-ticket-integrate-feedback, T-consequence-audit-feedback

## Decision narrative
Every skill must be designed with its feedback loop in mind: does it verify its own output, surface failures, feed the outcome back into context, and preserve what was learned? The principle "I'm only as good as my feedback loop" — stated during Windows porting work — implies a structural audit. We create /audit-feedback as a new audit skill (parallel to /audit-ticket, /audit-design, /audit-hypothesis) that checks these five properties on any skill directory, and wire it into /audit-ticket so skill-touching tickets get feedback-loop review at filing time.

## Hypothesis
Skills that are explicitly required to pass a feedback-loop audit will surface failures visibly, preserve learning across sessions, and compound quality over time rather than silently degrading.

## Measurement Signal
After /audit-feedback is wired into /audit-ticket: spot-check 5 existing skills against the audit. Count AMEND results. Each AMEND that leads to a skill edit (run script or SKILL.md update) is a learning-preservation event — if we see >0 such events in the first week, the audit is doing useful work.

## Goal Link
none: /audit-feedback is a meta-quality mechanism for the skill layer, not tied to a specific G-xxx product goal.
