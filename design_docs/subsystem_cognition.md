# Subsystem: Cognition

*Updated: 2026-03-20 | Machine-readable: `design_docs_for_igor/subsystem_cognition.dsb`*

Cognition is the processing layer between raw input and inference. It classifies intent, scores habits, modulates affect, and runs background consolidation — most of it without touching an LLM.

---

## Thalamus (`cognition/thalamus.py`)

**Intent classification.** 13 categories including `creative_request`, `question`, `command`, `greeting`, `status_check`, and more. Outputs a `ParsedInput` dataclass: `is_command`, `command`, `user_text`, `intent`, `complexity`, `preparse_result`, `core_input`.

**Complexity signal** (low/medium/high) drives `skip_to` — which tier to start from in the inference cascade. Complexity is scored on `core_input` only, not the full assembled input with thread context. This prevents a short message inflating to "high" just because it arrived with a long conversation history.

**Fast-path**: greetings and commands are detected in pure Python (<1ms) — no LLM preparse call.

---

## Basal Ganglia (`cognition/basal_ganglia.py`)

**Parallel habit scoring.** All loaded habits scored simultaneously. Winner-take-all above threshold.

Score formula:
```
trigger_score(1.0 if trigger matches)
+ keyword_bonus (≤ 0.15)
+ activation_bonus (≤ 0.15)
+ inertia_bonus (≤ 0.10)
+ valence_bonus (≤ 0.10)
```

**Milieu-modulated threshold**: base 0.50; high arousal → lowers threshold (more reactive); low dominance → raises threshold (more cautious). Clamped to [0.30, 0.70].

**Lateral inhibition**: max scorer wins. Tiebreak by activation count.

**Audit trail**: every habit execution logs a `score=` field in the ring. Low scores on a frequently-firing habit = trigger too broad.

**Trigger formats**: three supported: `pipe-separated|triggers`, `legacy space separated multi word trigger`, `single_token`.

**Habit response**: `metadata.action` (string) or `metadata.actions` (list → random choice) or fallback to narrative.

**Fork primitive** (`habit_type="fork"`): dispatches a list of `branch_habits` with a shared `traversal_context`. Context ID propagated via `args` dict — branches read/write a shared slot in the `lists` table. Used to parallelise habit chains over a shared workspace.

**Habit audit (D178)**: March 2026 audit archived 995 habits (991 zero-activation BL_*, 3 pipeline suppressors, 2 dead-trigger). 124 active habits remain. `PROC_DIRECTION_AWARE` wired as `context_inject/heartbeat_check`; `PROC_RESP_COMPLEX` changed to `context_inject`.

---

## Milieu (`cognition/milieu.py`)

**3D affect vector**: valence (positive/negative), arousal (activation level), dominance (agency/control).

**Update sources**: friction → arousal↑; friction inverse → dominance↑; ROI → dominance secondary signal.

**EMA asymmetry**: fast rise (α=0.25), slow fall (α=0.05). Dominance baseline +0.3 (Igor defaults to feeling capable).

**Consumers**: Basal Ganglia (threshold modulation), MilieuInterruptor (extremes → NE alert), MilieuSource (pushes VAD state to TWM every 60s).

**Persistence**: `~/.TheIgors/milieu_global.json` — shared across all instances on this machine.

---

## Narrative Engine (`cognition/narrative_engine.py`)

**Background daemon thread**. ~60s cycle. Yields to interactive turns (polls up to 10s before running).

**Reads**: TWM sorted by `urgency × salience` descending.

**Outputs**:
- Narrative synthesis → LTM promotion for observations with importance ≥ 0.7
- Action impulses deposited to TWM for the main loop to pick up

**Prospective prediction**: `predict_next()` on recent TWM context. Predicted topics merged into memory search for the next cycle.

**Link reinforcement**: correct prediction → +0.05 to predicted habit seed links. Wrong prediction → -0.10 to wrong + +0.05 to actual. This is the mechanistic learning loop.

**Model**: OR gpt-4o-mini (cloud_mode) or local NE model (Ollama). Response format: `json_object` (D053) — prevents prose-wrapping parse failures.

---

## Backchannel (`cognition/backchannel.py`)

Fast acknowledgment before the full response lands.

| Level | When |
|-------|------|
| `nod` | Immediate ack — Igor received the message |
| `nod_think` | Ack + thinking indicator |
| `full` | A full backchannel response (habit-driven) |

Fires after thalamus + milieu but before BG/LLM. Routes to web session via thread_id. Gate: `IGOR_BACKCHANNEL`.

Five habits seeded: NOD, NOD_THINK, INDEED, INTERESTING, HM.

---

## Word Graph (`cognition/word_graph.py`)

**Two-tier**: words + bigrams. **Same weights** for both parsing (habit scoring) and generation (predict_next). This is the architectural proof-of-concept: recognition and generation are the same operation in both directions.

**Storage**: SQLite at `~/.TheIgors/word_graph.db`. Migrated from JSON in 2026-03-10 after word graph grew to 191MB and caused OOM.

**Training**: `index_text_into_word_graph()` tool; `training_corpus.py` staged fetch→train→evict pipeline; `book_learner.py` trains per chunk during reading.

---

## Response Habituation (`cognition/response_habituation.py`)

Passive vocab frequency tracker. `decay_factor()` returns [0,1] — high frequency = high decay = Igor notices overused phrases and varies them. Persisted to `response_habituation.json`. Exposed in `/metrics`.

---

## Inference Gateway (`cognition/inference_gateway.py`)

Single call site for all LLM inference. DAG-based: `Node`/`Edge`/`PurposeConstraints` dataclasses define routing. `gateway.call(purpose, prompt)` picks the handler via edge weights and guards. `gateway.describe()` emits a human-readable DAG (exposed via `/routing --dag`). `gateway.from_env()` builds the DAG from environment — Ollama, OpenRouter, and Anthropic nodes wired by tier.

Guards: `_always` (unconditional) and `_local_preferred` (cluster has local capacity AND cloud_mode not active).

---

## Cluster Router (`cognition/cluster_router.py`)

Probes all cluster machines (config: `~/.TheIgors/local/machines.json`). Tracks health, load score, response latency, and active inferences per machine. `route(call_type)` returns the best available `(host, model)`. `has_local_capacity(call_type)` drives the `_local_preferred` guard. Override/clear methods for manual routing control. Status surfaced in `/metrics`.

---

## Traversal Context (`tools/traversal_context.py`)

Shared mutable scratch space for habit branches. `start_traversal(job_id)` mints a UUID context_id stored in the `lists` table. `ctx_get/ctx_set` read and write `(context_id, key)` slots. Fork habits mint the context_id and pass it to branches via `args` — branches coordinate without needing TWM.

---

## OS Primitives (`tools/os_primitives.py`)

Filesystem traversal ops wired to traversal_context. Designed for Igor to walk directories and process files via habit chains:

| Tool | What it does |
|------|-------------|
| `prim_list_dir()` | List `ctx[dir]` → write JSON list to `ctx[files]` |
| `prim_iter_next()` | Pop first item from `ctx[files]` → `ctx[current_file]` |
| `prim_iter_done()` | Check `ctx[files]` empty → `ctx[done]` |
| `prim_read_head()` | Read first N lines of `ctx[current_file]` → `ctx[content]` |
| `prim_type_detect()` | Detect file type → `ctx[file_type]` |
| `prim_file_meta()` | mtime + size → `ctx[file_mtime]`, `ctx[file_size]` |

---

## Temporal Gradient (`cognition/temporal_gradient.py`)

Single configurable decay primitive intended to replace 6 special-cased decay implementations (TWM decay, ring FIFO, milieu decay, thread age, habit inertia decay, NE cursor). File exists; full integration deferred post-experiment-7 (L-size).

---

## Decisions

D029, D030, D036, D037, D038, D044, D074, D075, D077, D177, D178
