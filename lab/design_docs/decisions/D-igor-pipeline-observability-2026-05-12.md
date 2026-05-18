# D-igor-pipeline-observability-2026-05-12
**title:** Wire IgorBase through Igor's coding pipeline and add flight-recorder logging
**date:** 2026-05-12
**status:** open
**spawned_tickets:** T-igorbase-llm-io-log, T-pe-chain-igorbase, T-pe-chain-flight-recorder, T-coa-flight-recorder, T-goal-continuation-igorbase

## Decision narrative
Build observable, diagnosable Igor coding pipeline by extending IgorBase with log_llm_io()/log_state_snapshot() methods, refactoring pe_chain.py from standalone functions into PeChain(IgorBase), adding flight-recorder log calls to PeChain (LLM I/O at every tier.2 call, state snapshot at escalation/implement), adding TWM pre-NE logging to COA, and refactoring goal_continuation.py into GoalContinuation(IgorBase) with untruncated bash output logging. Migrate forensic_logger references to self.log as each file is touched.

forensic_logger.py was an ad-hoc logging module that grew alongside the pipeline but is not the base class logger. The base class pattern (IgorBase → AgentBase, with self.log, time_it(), dump()) is the canonical mechanism established by T-d125-igorbase-drift and T-logging-class-inheritance-fixups. pe_chain and goal_continuation were missed by those tickets.

Alternative considered: ad-hoc Python logging per function (rejected — no time_it(), dump(), or consistent routing; continues the inconsistency those earlier tickets were meant to end).

## Dependency chain
T-igorbase-llm-io-log (S, CC) → unblocks → T-pe-chain-flight-recorder, T-coa-flight-recorder
T-pe-chain-igorbase (L, CC) → unblocks → T-pe-chain-flight-recorder
T-goal-continuation-igorbase (S, CC) → no deps
