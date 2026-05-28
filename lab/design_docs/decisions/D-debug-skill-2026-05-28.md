# D-debug-skill-2026-05-28
**title:** /debug autonomous mixed-mode debugger — pointer resolution → Scraps → Haiku/Sonnet → report
**date:** 2026-05-28
**status:** open
**spawned_tickets:** T-scraps-debug-extractor, T-debug-skill, T-consequence-debug-skill
**goal_link:** none: reduce CC inference overhead per debug cycle; make debugging systematic
**concept_links:** none

## Decision narrative
Implement /debug as an autonomous mixed-mode skill: freeform input (ticket ID, timestamp, pasted console text) → pointer resolution (light inference) → Scraps deterministic extraction (log window, state, test output) → Haiku classification + hypothesis → Sonnet escalation if needed → structured report. CC reads the report rather than investigating interactively. Report format: SUMMARY, WHERE, WHAT, STATE (type-specific), LOG WINDOW, HYPOTHESIS+confidence, NEXT step.

## Hypothesis
CC diagnoses most bugs from the structured report without running follow-up investigation commands.

## Measurement Signal
Run a known bug through /debug — report contains correct hypothesis and NEXT step without additional CC turns.

## Goal Link
none: reduce CC inference overhead per debug cycle; compiled inference applied to debugging

## Alternatives considered
- Interactive CC investigation (chose report-first — compiles the investigation into a reusable output)
- Haiku-only without escalation (chose escalation ladder — some bugs need Sonnet-level synthesis)
