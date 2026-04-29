# turn_pipeline — New conductor for cascade + workflow + voice (gated off)

**Path:** `theigors/subsystem_index/turn_pipeline`
**Updated:** 2026-04-27 by cap-map-followups

Conductor that strings cascade + reasoning_workflow + prompt_contexts + voice into one orchestrator. Single entry point TurnPipeline.run_turn(situation) returns a TurnResult with reply text and full path trace.

Status: BUILT BUT GATED OFF (IGOR_TURN_PIPELINE=false as of 2026-04-27).

The legacy path (direct reasoner.reason() calls in main.py with build_system_prompt() preamble) is still authoritative. This module is the migration target — see T-retire-legacy-direct-reasoner-path (pending) for the cutover plan.

Pipeline shape (per T-reasoning-voice-split #436, design 2026-04-15):
  situation → [1] CASCADE WALK (ExperimentCascade.attempt) → matched|escalate → [2] REASONING WORKFLOW (run_workflow with peer back-and-forth) → [3] DECISION BLOB (can_commit gate) → [4] VOICE CONTEXT → [5] VOICE PRODUCTION → TurnResult.

Primary file: wild_igor/igor/cognition/turn_pipeline.py — read its top-of-file docstring for the canonical explanation.

Also see: wild_igor/igor/cognition/reasoning_workflow.py, wild_igor/igor/cognition/voice_ab.py, wild_igor/igor/cognition/experiment_cascade.py.

CP grounding: CP1 (path_trace records known vs inferred), CP3 (per-step provenance), CP6 (reasoning never flows directly to voice without DecisionBlob gate).

Originating tickets: T-turn-pipeline-module, T-reasoning-voice-split (#436).
Cutover ticket: T-retire-legacy-direct-reasoner-path (pending, L).
