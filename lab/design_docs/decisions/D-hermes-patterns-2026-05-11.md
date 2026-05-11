# D-hermes-patterns-2026-05-11
**title:** Steal Hermes "do-learn-improve" patterns — palace FTS, pe_chain skill-gen, depth-over-breadth rule
**date:** 2026-05-11
**status:** open
**spawned_tickets:** T-palace-fts-index, T-pe-chain-skill-gen, T-depth-over-breadth-rule

## Decision narrative
Hermes Agent overtook OpenClaw as OpenRouter's #1 agent by implementing a "do, learn, improve" loop with procedurally generated skill files rather than optimizing for 50+ platform integrations — validating depth over breadth as a design principle. We implement three analogues: (1) Postgres FTS index on adc.palace for session-content search (mirrors Hermes's SQLite FTS5 layer), (2) mandatory post-task skill synthesis in pe_chain for M/L/XL tickets writing PLAYBOOK palace nodes under theigors/skills/ (mirrors Hermes's auto-generated skill files), and (3) a theigors/rules/design-principles palace node formalizing the depth-over-breadth principle so it doesn't get relitigated. PLAYBOOK memory type already shipped (T-igor-playbook-memory-type done 2026-05-10).
