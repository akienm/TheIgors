# Igor — Overall Architecture

*Updated: 2026-03-20 | Authoritative machine-readable version: `design_docs_for_igor/architecture_root.dsb`*

---

## Source / Runtime Split

```
~/TheIgors/            ← source code (in git)
~/.TheIgors/           ← all runtime data (NOT in git)
  local/               ← machine-global (machines.json, word_graph.db, milieu_global.json)
  Igor-wild-0001/      ← this instance
    wild-0001.db       ← live SQLite DB (THE memory graph)
    .env               ← secrets and feature flags
    logs/              ← forensic logs (newest-at-top)
    warm_context.*.json← session context across restarts
```

---

## Per-Turn Pipeline

```
1. Backchannel check      — fast ack to user before processing
2. Preparse               — intent/complexity via gpt-4o-mini or Ollama
3. cortex.search()        — text keyword → cosine rerank (hybrid)
4. Winnow (optional)      — gpt-4o-mini trims retrieved memories to relevant set
5. expand_blob_memories() — appends full blob content for high-relevance memories
6. gateway.reason()       — tier cascade: habit → local → cloud
7. ring_push + episodic   — store response in ring and memory graph
8. web_server.send()      — deliver response to web UI
```

---

## Inference Tier Ladder

| Tier | Model | Trigger |
|------|-------|---------|
| t1 | Habit (no LLM) | Basal ganglia score ≥ threshold |
| t2 | Ollama qwen2.5:7b | Background / preparse |
| t3 | OR gpt-4o-mini | Interactive (cheap) |
| t3.5 | OR claude-haiku-4.5 | Interactive floor (D035: all interactive turns land here minimum) |
| t4 | OR claude-sonnet-4-6 | High complexity / NE ambiguity |
| t5 | Anthropic direct | Inhibited (`IGOR_TIER5_ENABLED=false`) |
| t6 | Arbiter alert | All inference exhausted |

**D035 rule**: All interactive turns use at minimum t3.5. t2/t3 are background-only.

---

## Subsystems

### Brainstem (HIGH inertia — never modify casually)
Genesis initialization. Core pattern verification at boot. Arithmetic Moral Model diagnostics. The irreducible foundation.

### Cortex (`memory/cortex.py`)
All database read/write — SQLite (default) or Postgres (`IGOR_HOME_DB_URL`). Owns DatabaseProxy (timing, metrics, reconnect). Hybrid search: text keyword Phase 1 → cosine rerank Phase 2 via nomic-embed-text. Also owns TWM, ring memory, interpretive edges, and the `tails` activation trail table.

### Thalamus (`cognition/thalamus.py`)
Intent classification (13 categories). Complexity assessment (low/medium/high → drives skip_to). Fast-path: greetings and commands detected in pure Python, no LLM call.

### Basal Ganglia (`cognition/basal_ganglia.py`)
Parallel habit scoring. Milieu-modulated threshold (0.30–0.70). Lateral inhibition (max scorer wins). Scores logged in ring for audit. PROC_HABIT_COMPILER fires at 0.95 confidence.

### Milieu (`cognition/milieu.py`)
3D affect vector: valence / arousal / dominance. Asymmetric EMA: fast rise (α=0.25), slow fall (α=0.05). Dominance baseline +0.3. Shared across instances via `~/.TheIgors/milieu_global.json`.

### Narrative Engine (`cognition/narrative_engine.py`)
Background daemon thread. ~60s cycle. Reads TWM sorted by urgency×salience. Synthesizes observations into LTM memories. Prospective prediction: predict_next on recent context, merge into search. Link reinforcement: correct predictions strengthened, wrong weakened.

### Word Graph (`cognition/word_graph.py`)
SQLite-backed two-tier: words + bigrams. Same weights for parsing (habit scoring) and generation (predict_next). Trained by book_learner and training_corpus. Cache: `~/.TheIgors/word_graph.db`.

### Backchannel (`cognition/backchannel.py`)
Three levels: nod / nod_think / full. Fires after thalamus+milieu, before BG/LLM. Routes to web session by thread_id. Gated by `IGOR_BACKCHANNEL`.

### Inference Gateway (`cognition/inference_gateway.py`)
Single entry point for all inference. DAG-based routing: `Node`/`Edge`/`PurposeConstraints` dataclasses define the routing graph. `gateway.call(purpose, prompt)` picks handler via edge weights and guards. `gateway.describe()` emits human-readable DAG. Built from env via `gateway.from_env()`.

### Cluster Router (`cognition/cluster_router.py`)
Probes all cluster machines. Tracks health, load, latency, active inferences. `route(call_type)` returns best available `(host, model)`. Drives the `_local_preferred` inference guard. Config: `~/.TheIgors/local/machines.json`.

### Tools (`tools/`)
Self-registering at module import. AI-agnostic: tools know nothing about which tier calls them. Hot-reloadable (LOW inertia). Reactive habit pattern: `code_ref + twm_ttl_seconds` in PROC metadata → tool auto-dispatch + short-TTL TWM result.

### Web (`web/server.py`)
Starlette + uvicorn. Port 8080. WebSocket fan-out. CC→Igor bridge: `POST /api/cc_send {"content":"..."}` injects as author "claude-code".

---

## Memory Graph Structure

```
ROOT
 └── CP1-CP6   (Core Patterns — inertia 0.90+; structural bedrock)
      └── ID1-ID14  (Identity memories)
           └── RM1-RM4  (Role Models)
                └── PROC, EPISODIC, FACTUAL, INTERPRETIVE, EXPERIENTIAL
```

**Inertia** is computed from graph position: `base(type) + 0.1·log1p(activation) + 0.05·len(children) + 0.02·depth`. It emerges from use, not manual assignment.

**TWM** (Transient Working Memory): push-only sandbox. Sources deposit; NE and reasoners pull. TTL cleans up. Urgency⊥salience: urgency×salience sorts NE queue.

**Ring Memory**: FIFO-50. Survives restarts. Injected into every API call for session continuity.

---

## Key Env Vars

| Var | Purpose |
|-----|---------|
| `IGOR_DB_PATH` | Path to live SQLite DB |
| `IGOR_HOME_DB_URL` | Postgres URL — enables PG mode (e.g. `postgresql://igor:pass@host/db`) |
| `OPENROUTER_API_KEY` | Primary cloud inference |
| `IGOR_SWARM_DB` | Postgres URL of swarm home — enables memory sync across boxes |
| `IGOR_SELF_EDIT_ENABLED` | Gates source file writes |
| `IGOR_TIER5_ENABLED` | Gates Anthropic direct spend (default false) |
| `IGOR_ARBITER_ENABLED` | Human-approval queue (default false) |
| `IGOR_BACKCHANNEL` | Enable backchannel acks |
| `IGOR_CONTEXT_WINNOW` | Enable context winnow pass |
| `IGOR_HOT_RELOAD` | Enable auto hot-reload after self-edit |
| `IGOR_MAX_TURNS` | Max agentic tool turns per call (default 8, .env=50) |
| `IGOR_SKIP_PREPARSE_ON_CONFIDENT` | Skip Ollama preparse on low/high complexity turns |
