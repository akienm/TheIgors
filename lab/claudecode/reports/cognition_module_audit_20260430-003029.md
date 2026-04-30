# Cognition module audit — 2026-04-30T00:30:29Z

Modules scanned: 93

## Classification summary

| Class | Count |
|---|---|
| LIVE | 72 |
| EXPERIMENTAL | 17 |
| PLACEHOLDER | 0 |
| ORPHAN | 4 |

## ORPHAN (4)

| Module | Path | LOC | Anchors | Cog | Test | Other | Docstring |
|---|---|---|---|---|---|---|---|
| `observer` | `observer.py` | 114 | 0 | 0 | 0 | 0 |  |
| `pipeline_manager` | `pipeline_manager.py` | 161 | 0 | 0 | 0 | 0 | pipeline_manager.py — D096: Pipeline and job state via files |
| `prefrontal_cortex` | `prefrontal_cortex.py` | 43 | 0 | 0 | 0 | 0 | Prefrontal Cortex - executive reasoning. |
| `reasoning_cache` | `reasoning_cache.py` | 134 | 0 | 0 | 0 | 0 | Reasoning cache — file-backed TTL cache for Ollama NE/reason |

## EXPERIMENTAL (17)

| Module | Path | LOC | Anchors | Cog | Test | Other | Docstring |
|---|---|---|---|---|---|---|---|
| `bliss_integrator` | `bliss_integrator.py` | 180 | 0 | 0 | 0 | 0 | bliss_integrator.py — slow EMA over Pursuit completion event |
| `boredom` | `boredom.py` | 121 | 0 | 0 | 0 | 0 | boredom.py — #178: Boredom monitor. |
| `confabulation_gate` | `confabulation_gate.py` | 279 | 0 | 0 | 1 | 0 | confabulation_gate.py — T-watchlist-knowledge-gaps-under-loa |
| `experiment_outcome` | `experiment_outcome.py` | 303 | 0 | 0 | 1 | 0 | experiment_outcome.py — T-experiment-primitive-outcome-feedb |
| `goal_formation` | `goal_formation.py` | 293 | 0 | 0 | 1 | 0 | goal_formation.py — T-goal-formation-from-conversation (#427 |
| `graph_integrator` | `graph_integrator.py` | 291 | 0 | 0 | 1 | 0 | graph_integrator.py — T-graph-integrator: co-occurrence edge |
| `judgments` | `judgments.py` | 228 | 0 | 1 | 0 | 0 |  |
| `local_preparse` | `local_preparse.py` | 219 | 0 | 1 | 1 | 0 | local_preparse — local-only mini-LLM fallback for preparse. |
| `operating_mode` | `operating_mode.py` | 142 | 0 | 0 | 1 | 0 | operating_mode.py — T-igor-modes |
| `preparse_router` | `preparse_router.py` | 405 | 0 | 0 | 1 | 0 | preparse_router — distributed dispatcher for atomic preparse |
| `pursuits` | `pursuits.py` | 237 | 0 | 0 | 0 | 0 | pursuits.py — Pursuit layer: goal-bound behavioral units abo |
| `reading_indexer` | `reading_indexer.py` | 398 | 0 | 0 | 1 | 0 | reading_indexer.py — T-reading-indexer: chunk → G54 extract  |
| `sensor_tree` | `sensor_tree.py` | 365 | 0 | 0 | 1 | 2 | sensor_tree.py — GH-281: SensorTree — generalized monitoring |
| `temporal_gradient` | `temporal_gradient.py` | 118 | 0 | 0 | 0 | 1 | TemporalGradient — unified decay primitive (T-temporal-gradi |
| `thalamus` | `thalamus.py` | 939 | 0 | 0 | 1 | 1 | Thalamus — input processing and routing. |
| `training_corpus` | `training_corpus.py` | 551 | 0 | 0 | 0 | 1 | Training Corpus Manager — WO#138 / D038. |
| `wandering_search` | `wandering_search.py` | 287 | 0 | 0 | 1 | 0 | wandering_search.py — T-wandering-search |

## LIVE (72)

| Module | Path | LOC | Anchors | Cog | Test | Other | Docstring |
|---|---|---|---|---|---|---|---|
| `action_claim_verifier` | `action_claim_verifier.py` | 284 | 1 | 0 | 1 | 0 | action_claim_verifier.py — T-igor-emit-action-confabulation. |
| `anticipation` | `anticipation.py` | 237 | 1 | 0 | 0 | 1 | anticipation.py — Anticipation pull: predict closure valence |
| `approach_frame_audit` | `approach_frame_audit.py` | 227 | 1 | 0 | 1 | 0 | approach_frame_audit.py — T-igor-self-audit-approach-frame |
| `backchannel` | `backchannel.py` | 136 | 1 | 0 | 0 | 0 | Backchannel layer — G38: immediate acknowledgment before ful |
| `basal_ganglia` | `basal_ganglia.py` | 856 | 1 | 2 | 0 | 0 | Basal Ganglia — parallel habit scoring with lateral inhibiti |
| `base` | `reasoners/base.py` | 918 | 1 | 4 | 0 | 0 | base.py — Reasoner hierarchy, context assembly, and shared t |
| `blob_store` | `blob_store.py` | 318 | 0 | 3 | 0 | 0 | Blob store — persistent storage for raw acquired content (D2 |
| `cc_inbox_bridge` | `cc_inbox_bridge.py` | 51 | 1 | 0 | 0 | 0 | cc_inbox_bridge.py — Igor-side wrapper around lab.claudecode |
| `cc_session_logger` | `cc_session_logger.py` | 81 | 1 | 0 | 0 | 0 |  |
| `chunker` | `chunker.py` | 257 | 0 | 2 | 2 | 0 | chunker — atomic input splitter for distributed preparse. |
| `cloud_mode` | `cloud_mode.py` | 208 | 1 | 2 | 0 | 1 | cloud_mode.py — Master gate for cloud-inference-as-training  |
| `cluster_router` | `cluster_router.py` | 464 | 0 | 3 | 2 | 2 | cluster_router.py — Simple inference router (#342). |
| `coalition` | `coalition.py` | 133 | 0 | 1 | 0 | 0 | coalition.py — Binding: coalition detection on hot node set. |
| `consolidation` | `consolidation.py` | 498 | 1 | 0 | 1 | 0 | consolidation.py — Episodic consolidation daemon (hippocampa |
| `consult` | `consult.py` | 572 | 2 | 1 | 3 | 0 | consult.py — peer-LLM consultation primitive (D-consult-prim |
| `consult_prompts` | `consult_prompts.py` | 141 | 0 | 1 | 1 | 0 | consult_prompts.py — system + state prompt templates per pro |
| `cursor_runtime` | `cursor_runtime.py` | 197 | 2 | 0 | 1 | 0 | cursor_runtime.py — T-engram-cursor-runtime |
| `daemon_supervisor` | `daemon_supervisor.py` | 245 | 1 | 0 | 0 | 4 | DaemonSupervisor — central registry for Igor's daemon thread |
| `decision_blob` | `decision_blob.py` | 329 | 1 | 3 | 6 | 0 | decision_blob.py — T-decision-blob-schema |
| `distillation` | `distillation.py` | 490 | 1 | 0 | 0 | 0 | distillation.py — T-distillation-daemon: EPISODIC → EXPERIEN |
| `embedder` | `embedder.py` | 73 | 1 | 4 | 0 | 2 | Embedder — nomic-embed-text via Ollama (change.37). |
| `emit_channels` | `emit_channels.py` | 298 | 1 | 1 | 2 | 0 | emit_channels.py — Channel registry for engram EMIT instruct |
| `engineered_failure` | `engineered_failure.py` | 107 | 0 | 1 | 1 | 0 | engineered_failure.py — T-engineered-failure-experiments |
| `eval_gate` | `eval_gate.py` | 69 | 0 | 2 | 0 | 1 | eval_gate.py — Unified condition evaluator (T-condition-eval |
| `experiment` | `experiment.py` | 402 | 2 | 3 | 5 | 0 | experiment.py — T-experiment-primitive-schema |
| `experiment_cascade` | `experiment_cascade.py` | 1040 | 1 | 3 | 9 | 1 | experiment_cascade.py — T-substrate-experiment-cascade |
| `experiment_predictor` | `experiment_predictor.py` | 147 | 0 | 1 | 1 | 0 | experiment_predictor.py — T-experiment-predictor-primitive |
| `experiment_scheduler` | `experiment_scheduler.py` | 464 | 3 | 1 | 1 | 1 | experiment_scheduler.py — T-experiment-primitive-scheduler ( |
| `factual_compression` | `factual_compression.py` | 473 | 1 | 0 | 0 | 0 | factual_compression.py — FACTUAL→INTERPRETIVE compression pa |
| `forensic_logger` | `forensic_logger.py` | 946 | 3 | 23 | 1 | 41 |  |
| `gate_primitive` | `gate_primitive.py` | 194 | 1 | 0 | 1 | 0 | gate_primitive.py — T-inhibitory-pattern-primitive |
| `gist_gate` | `gist_gate.py` | 76 | 1 | 0 | 1 | 0 | gist_gate — confidence-gated short-circuit for cortex.search |
| `hebbian_bridge` | `hebbian_bridge.py` | 218 | 1 | 0 | 1 | 1 | hebbian_bridge.py — T-308: Hebbian bridge between word graph |
| `inference_gateway` | `inference_gateway.py` | 1570 | 2 | 6 | 2 | 5 | inference_gateway.py — Unified inference routing as a DAG +  |
| `inference_ollama` | `inference_ollama.py` | 95 | 2 | 5 | 3 | 1 | inference_ollama.py — D327: Unified Ollama inference + machi |
| `inference_openrouter` | `inference_openrouter.py` | 42 | 1 | 3 | 1 | 4 | inference_openrouter.py — D327: Unified OpenRouter cloud inf |
| `inhibition_chain` | `inhibition_chain.py` | 253 | 1 | 0 | 1 | 0 | inhibition_chain.py — DAG of conditional gates between BG se |
| `intent_decay_source` | `intent_decay_source.py` | 106 | 1 | 0 | 1 | 0 | IntentDecaySource — quiet-period push source for T-watchlist |
| `interruptors` | `interruptors.py` | 340 | 1 | 0 | 0 | 0 |  |
| `job_manager` | `job_manager.py` | 312 | 1 | 0 | 1 | 0 | Job Manager — persistent state for long-running multi-step t |
| `llm_peer_advisor` | `llm_peer_advisor.py` | 212 | 1 | 0 | 2 | 0 | llm_peer_advisor.py — T-llm-collaboration-protocol (#438) |
| `machine_manager` | `machine_manager.py` | 14 | 1 | 1 | 0 | 3 | machine_manager.py — Re-export shim. |
| `metrics` | `metrics.py` | 599 | 1 | 0 | 0 | 3 | Internal metrics reporter. |
| `milieu` | `milieu.py` | 921 | 1 | 2 | 2 | 2 | milieu.py — Ambient emotional state manager (3D affect vecto |
| `multi_cloud` | `multi_cloud.py` | 84 | 1 | 0 | 0 | 0 | Multi-cloud inference query support (change.40). |
| `narrative_engine` | `narrative_engine.py` | 2333 | 1 | 0 | 1 | 0 | narrative_engine.py — Arc builder & coherence checker. Trans |
| `node_executor` | `node_executor.py` | 436 | 0 | 1 | 12 | 0 | node_executor.py — Engram node executor (D260, D290, D291, D |
| `ollama_reasoner` | `reasoners/ollama_reasoner.py` | 1088 | 0 | 2 | 0 | 3 | Ollama local reasoner — primary local inference backend. |
| `openrouter_reasoner` | `reasoners/openrouter_reasoner.py` | 773 | 0 | 1 | 0 | 0 | OpenRouter reasoner — OpenAI-compatible API to any cloud inf |
| `pr_consolidation_source` | `pr_consolidation_source.py` | 114 | 1 | 0 | 1 | 0 | PRConsolidationSource — quiet-period push source for persist |
| `prompt_contexts` | `prompt_contexts.py` | 443 | 1 | 3 | 5 | 0 | prompt_contexts.py — T-reasoning-prompt-split |
| `push_sources` | `push_sources.py` | 2923 | 1 | 1 | 10 | 0 | Push Sources — processes that deposit observations into TWM  |
| `reasoning_workflow` | `reasoning_workflow.py` | 985 | 1 | 1 | 5 | 0 | reasoning_workflow.py — T-reasoning-workflow-primitive |
| `redis_word_graph` | `redis_word_graph.py` | 389 | 1 | 0 | 0 | 0 | redis_word_graph.py — Redis-backed word graph (D121). |
| `relationship_drift_source` | `relationship_drift_source.py` | 99 | 1 | 0 | 1 | 0 | RelationshipDriftSource — quiet-period push source for T-wat |
| `relay` | `relay.py` | 138 | 1 | 0 | 0 | 0 | Pass-through relay (change.41). |
| `replay` | `replay.py` | 389 | 1 | 0 | 0 | 0 | Consolidation Replay — integrate recently-deposited FACT_CLO |
| `reply_gap_detector` | `reply_gap_detector.py` | 197 | 1 | 0 | 1 | 0 | reply_gap_detector.py — T-any-thoughts-habit-failure (#468) |
| `residue_scan` | `residue_scan.py` | 308 | 1 | 0 | 2 | 0 | residue_scan — non-terminal emission hook for post-reply pro |
| `response_coherence_inhibitor` | `response_coherence_inhibitor.py` | 466 | 1 | 0 | 2 | 0 | response_coherence_inhibitor.py — T-response-coherence-inhib |
| `response_habituation` | `response_habituation.py` | 111 | 1 | 1 | 0 | 0 | Response word habituation — WO#140 Phase 2. |
| `self_test` | `self_test.py` | 401 | 1 | 0 | 1 | 0 | self_test.py — T-self-test-wire: runtime behavioral regressi |
| `shadow_reasoner` | `shadow_reasoner.py` | 388 | 1 | 0 | 1 | 0 | shadow_reasoner — dual-path reasoning execution + divergence |
| `sleep_clock` | `sleep_clock.py` | 145 | 1 | 0 | 1 | 0 | sleep_clock.py — T-sleep-triggered-by-clock (#467) |
| `sleep_consolidation` | `sleep_consolidation.py` | 262 | 1 | 1 | 1 | 0 | Sleep Consolidation — idle-time network wandering that disco |
| `state_coherence_check` | `state_coherence_check.py` | 173 | 1 | 0 | 1 | 0 | state_coherence_check.py — T-watchlist-internal-state-cohere |
| `system_prompt` | `system_prompt.py` | 501 | 1 | 2 | 0 | 0 | Dynamic system prompt builder. |
| `turn_pipeline` | `turn_pipeline.py` | 675 | 1 | 0 | 3 | 0 | turn_pipeline.py — T-turn-pipeline-module |
| `uc_watchdog` | `uc_watchdog.py` | 162 | 1 | 0 | 1 | 0 | uc_watchdog.py — T-uc-server-watchdog |
| `user_context` | `user_context.py` | 190 | 1 | 0 | 0 | 0 | User context — per-user profile, formality tracking, and cha |
| `voice_ab` | `voice_ab.py` | 360 | 1 | 0 | 1 | 0 | voice_ab.py — T-voice-actor-ab-framework (#439) |
| `word_graph` | `word_graph.py` | 1018 | 1 | 4 | 3 | 6 | WordGraph — Postgres-backed word co-occurrence index (via db |

## Removal candidates (ORPHAN — verify before deleting)

- `wild_igor/igor/cognition/prefrontal_cortex.py` (43 LOC): Prefrontal Cortex - executive reasoning.
- `wild_igor/igor/cognition/observer.py` (114 LOC): (no docstring)
- `wild_igor/igor/cognition/reasoning_cache.py` (134 LOC): Reasoning cache — file-backed TTL cache for Ollama NE/reasoning calls (cache.2).
- `wild_igor/igor/cognition/pipeline_manager.py` (161 LOC): pipeline_manager.py — D096: Pipeline and job state via filesystem convention.
