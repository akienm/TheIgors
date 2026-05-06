# D-datacenter-agent-infra-2026-05-05
**title:** agent_datacenter gets its own Postgres DB + shared coding subagent pattern
**date:** 2026-05-05
**status:** open
**spawned_tickets:** T-adc-db-provision, T-adc-db-proxy-wire, T-cc-minion-palace-rule, T-coding-subagent-igor-path

## Decision narrative
agent_datacenter gets its own Postgres database (`agent-datacenter-0001`) within the same Postgres instance as Igor (one process, multiple databases), with a separate `datacenter` role and credentials. This gives clean identity separation — Igor's credentials cannot touch datacenter tables. Same memory schema shape as Igor's palace. No Igor dependency for any datacenter operation.

Separately: the CC minion pattern (worktree-isolated Agent for mechanical code edits) is formalized as the standard path. Igor-coding is last — all other tickets close before touching Igor cognition. The Igor→coding-subagent invocation mechanism is deferred to T-coding-subagent-igor-path.
