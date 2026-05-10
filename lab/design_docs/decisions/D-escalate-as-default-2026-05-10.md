# D-escalate-as-default-2026-05-10
**title:** Escalate as Igor's default fallback; watch list + lever watcher for grand escalation
**date:** 2026-05-10
**status:** open
**spawned_tickets:** T-escalate-default-pattern, T-igor-watch-list, T-igor-lever-watcher

## Decision narrative
When habit inventory exhausts, Igor should escalate to channel (structured missing-info post) rather than confabulate or go mute — this is a cognition primitive symmetrical to human behaviour. When escalation itself can't reach a resolver, grand-escalate: park the problem on a persistent watch list with a structured lever description, then actively scan incoming information for conditions that would unblock it.

Three-tier fallback: (1) habits — normal operation; (2) escalate — post to channel what's missing; (3) grand escalation — add to watch list with watch_condition, monitor for lever.

Spawned from design conversation 2026-05-10 starting with: "humans often also go mute when their habits run out — they pick the best of bad choices to reply with rather than try for something new." The pe_chain description-gate kick-back (D-pe-chain-description-gate-2026-05-10) was the first instance of this pattern; this decision generalises it.
