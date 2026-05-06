# D-igor-cognition-noise-2026-05-06
**title:** Fix Igor cognition noise — narrative visibility + TWM search quality
**date:** 2026-05-06
**status:** open
**spawned_tickets:** T-igor-narrative-turn-log, T-igor-twm-salience-gate, T-igor-attractor-first-traversal, T-igor-task-set-short-ttl

## Decision narrative
Diagnosed while investigating Igor's garbled response bug (Level0ExactRecall returning raw MSG| bus memories as responses). Root causes are broader than the symptom: (1) no per-turn visibility into what cognition actually retrieved and assembled — making quality assessment dependent on console intuition; (2) cortex.search pulls TWM observations into the candidate pool without a salience gate, so periodic snapshots (TASK_SET, heartbeat ticks) flood retrieval because they contain current session context and score highest by embedding similarity; (3) traversal starts from all 20 CP/ID roots at depth=3, producing 100+ parameter IN queries and 200-node candidate pools regardless of current focus; (4) TASK_SET observations accumulate session-long when they only need restart-window (5-10 min) TTL.

Biological model driving D2/D3: attention narrows the search space. Background associations should only surface if they beat the current attractor's activation level (D2). Traversal should start from the current focus, not all identity roots (D3 — supersedes D199 hot path).

Gating: D3 gated on D2; both D2 and D4 gated on D1 (narrative log is the verification instrument for all subsequent changes).

**Pre-approvals:** main.py HIGH inertia touch in T-igor-task-set-short-ttl approved inline (lines 3867-3878 only, TASK_SET push block, not turn loop core).
