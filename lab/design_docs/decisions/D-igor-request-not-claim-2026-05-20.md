# D-igor-request-not-claim-2026-05-20
**title:** Igor requests tickets via cmd_next --max-difficulty, never claims directly
**date:** 2026-05-20
**status:** open
**spawned_tickets:** T-adopt-next-uses-cmd-next, T-legacy-direct-claim-error, T-decided-always-verify, T-consequence-difficulty-tiers, T-consequence-igor-request-not-claim

## Decision narrative
Replace Igor's direct queue browse (adopt_next_ticket picks any sprint ticket regardless of ownership or difficulty) with a request model: Igor calls `cmd_next --max-difficulty=1` and receives the next Apprentice-tier ticket he qualifies for, or None. Three difficulty-tier tickets filed under D-target-difficulty-tiers-2026-05-19 add the filtering mechanism to cmd_next but do not update adopt_next_ticket — that gap is the root cause of Igor repeatedly claiming test fixtures and bare tickets. This decision fills that gap and adds a LegacyDirectClaimError stub so remaining old code paths surface in logs immediately rather than silently misfiring.

Alternative considered: worker=igor filter alone in adopt_next_ticket (doesn't generalize to capability routing). Chose cmd_next delegation because it unifies the external worker-daemon path and Igor's internal path through one canonical mechanism.

## Hypothesis
Igor never directly claims a specific ticket ID; adopt_next_ticket returns None when no eligible tickets exist rather than picking up whatever happens to be in the queue.

## Measurement Signal
No more `[pe_chain] ✗ T-test-ticket` or equivalent bare-ticket failures in the channel. LegacyDirectClaimError log lines (if any) identify remaining old code paths. Igor's NE cycles resume normal results (not stuck in empty-queue loop from failed claims).

## Goal Link
none: prerequisite for Igor self-programming — until Igor picks up work correctly, every sprint creates cleanup overhead that blocks self-improvement cycles.

## Retroactive finding
D-target-difficulty-tiers-2026-05-19 had the same end-state hypothesis but no verification ticket, because all tickets were S-size and /decided skips consequence tickets for all-S batches. This is a skills gap: T-decided-always-verify fixes the skip condition so behavioral hypotheses always get a verification gate regardless of ticket size.
