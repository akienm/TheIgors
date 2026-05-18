# D-igor-cognition-research-improvements-2026-05-17
**title:** Research-driven Igor cognition improvements across 5 cognitive-architecture domains
**date:** 2026-05-17
**status:** open
**spawned_tickets:** T-igor-ne-impasse-handler, T-igor-stuck-triggers-dreaming, T-igor-twm-salience-competition, T-igor-twm-age-decay, T-igor-pec-confidence-gate, T-igor-failure-accumulator, T-igor-ne-grader-to-action, T-igor-dreaming-schema-extraction, T-igor-dreaming-outputs-actionable

## Decision narrative
Librarian queried 5 cognitive-architecture research topics (stuck-state recovery, attention competition, metacognition, spreading activation, memory consolidation) and the results were analyzed to produce 9 improvement tickets for Igor's cognition pipeline. 2 proposed tickets were removed as already-shipped (T-igor-activate-primitive + T-igor-recursive-edge-traversal: interpretive_edges table and cortex.spreading_activation() exist). Alternative considered: ad-hoc per-symptom fixes — chose research-grounded batch to address root causes. All tickets target Igor's wild_igor codebase, MEDIUM inertia (cognition/, cortex.py, pe_chain, dreaming), executor=Igor. No HIGH-inertia files touched.

## Ticket priority tiers
- Immediate (fix 12h stuck loop): T-igor-ne-impasse-handler, T-igor-stuck-triggers-dreaming
- High (quality+reliability): T-igor-pec-confidence-gate, T-igor-twm-salience-competition, T-igor-ne-grader-to-action
- Medium (path to 1.5c): T-igor-failure-accumulator, T-igor-twm-age-decay, T-igor-dreaming-outputs-actionable
- Strategic (path to 1.5d): T-igor-dreaming-schema-extraction
