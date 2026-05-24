# D-expert-lenses-confidence-2026-05-21
**title:** Add four expert lenses + confidence-everywhere system
**date:** 2026-05-21
**status:** open
**spawned_tickets:** T-confidence-schema, T-confidence-surface-audit, T-pe-evaluate-confidence, T-habit-telemetry-gate, T-universal-llm-lineage, T-skill-contract-checker, T-consequence-expert-lenses-confidence

## Decision narrative
Added four expert lenses to UnseenUniversity/EXPERTS.md from recovery of prior design conversations: Schmidhuber (self-modifying systems with provable improvement), Shankar (evaluator quality, confidence everywhere), Willison (observability-first, universal LLM lineage), Cherny (explicit contracts at scale). Akien's core insight from Shankar: "we shouldn't have binary answers in Igor — pretty much everything should be a confidence between -1 and 1." This drives the confidence schema ticket (HIGH inertia, pre-approved inline) and cascading surface-audit and pe_evaluate changes. Schmidhuber maps to connecting the already-built skill telemetry to the habit write gate. Willison maps to a universal LLM call table (pe_chain already logs; NE/habits don't). Cherny maps to contract checking at queue-add time.

## Hypothesis
After these tickets ship, Igor's evaluations are no longer binary: confidence is a first-class float on memories, habits, and evaluator outputs; every LLM call anywhere in the system is in one queryable table; skill contract gaps are caught at filing time not sprint time.

## Measurement Signal
Within 30 days: confidence distribution query on clan.memories returns results (schema shipped); pe_evaluate logs show float distribution clustering near 0.1 or 0.9 (calibrated evaluator); instance.llm_calls has rows from both IgorBase and pe_chain paths.

## Goal Link
none: self-improvement capability direction, not yet formalized as a numbered goal
