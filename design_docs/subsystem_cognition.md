# Subsystem: Cognition

*Updated: 2026-03-14 | Machine-readable: `design_docs_for_igor/subsystem_cognition.dsb`*

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

## Decisions

D029, D030, D036, D037, D038, D044
