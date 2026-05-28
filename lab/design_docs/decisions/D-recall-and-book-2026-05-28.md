# D-recall-and-book-2026-05-28
**title:** recall-first tooling in skills + book chapters 3/4/5 updated for today's designs
**date:** 2026-05-28
**status:** open
**spawned_tickets:** T-recall-in-skills, T-book-ch3-recall, T-book-ch4-debug, T-book-ch5-launcher, T-consequence-recall-tools
**goal_link:** none: compiled inference — stored knowledge is the first lookup, not re-derived
**concept_links:** none

## Decision narrative
Two parts: (1) Update sprint-ticket, context-load, and sorted skill files to call recall(X) before bash/grep — recall-first is a mandatory step, bash is the fallback. (2) Update book chapters 3, 4, 5 to reflect today's design decisions: Chapter 3 adds recall-first lever; Chapter 4 adds /debug skill; Chapter 5 adds configurable frontend shim and launcher UX. Book goes to editor Monday 2026-06-01.

## Hypothesis
CC uses recall(X) before bash in the common case across sprint-ticket, context-load, sorted.

## Measurement Signal
Sprint-ticket execution logs show recall call before bash investigation commands.

## Goal Link
none: compiled inference — stored knowledge is the first lookup; book deadline Monday 2026-06-01

## Alternatives considered
- Suggest recall in skills but not mandate it (chose mandatory step — suggestions get skipped; gates don't)
- Book updates as separate decision (folded in — same S-sized skill/doc changes from same design session)
