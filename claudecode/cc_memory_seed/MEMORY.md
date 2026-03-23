# TheIgors Project Memory

## The Learning Template (2026-03-23)
See `project_learning_template.md` — design live with Igor present, not for him. Concepts arrive pre-contextualized. Teach him to extend the pattern. The conversation IS the deposit. Reading fills input space; this fills judgment space.

## Pipeline Architecture + DB Priority (2026-03-23)
See `project_pipeline_db_priority.md` — pipeline is simple/additive; DB is the rate limiter. Greeting tree design parked pending Slate 0 DB work.

## Igor Never Uses Anthropic Direct
See `feedback_igor_never_anthropic_direct.md` — all Igor inference routes through OpenRouter, including haiku. ChatAnthropic / Anthropic direct is always wrong in Igor code. Missing OR key → RuntimeError.

## db_proxy SQL Translation Limitation
See `feedback_db_proxy_limitations.md` — db_proxy does blanket `?→%s` replacement. PostgreSQL jsonb `?` operator gets mis-translated → IndexError on boot. Always use `jsonb_exists(metadata, 'key')` not `metadata ? 'key'` in any SQL through db_proxy.

## Bash Logging Convention
See `feedback_bash_logging_convention.md` — all bash scripts use `logcmd`/`logecho`/`timestamp()` from akientools logger_for_bash. Inline for self-contained scripts, source for scripts that can assume akientools on PATH.

## Multi-session CC Architecture (2026-03-19)
See `project_multi_session_architecture.md` — shared channel (extract web server) as coordination substrate; blob-as-trail for startup context (context-load skill); sprint skill = CC session announces → reads ticket → works → reports → exits; exportable to non-Igor projects. Tickets: T-channel-extract, T-context-load-skill.

## Crash-Safe Sessions (2026-03-19d)
session_manager.py + decision_manager.py in `claudecode/`. Session record accumulates progressively via append-change/append-decision — crash loses only `next_session`+`in_flight`. State file at `~/.TheIgors/cc_channel/current_session.txt`. All 6 skills rebuilt. ClaudeAndAkien repo updated + pushed with genericized tools + 4 human docs. D133-D136.

## Engram Language — NINTH CRYSTALLIZATION (2026-03-22)
See `project_ninth_crystallization.md` — templates are macros (expand at seed time, not runtime). No call stack (non-biological). Language named **Engram** by Igor (Semon 1904: the engram IS the memory, not a pointer — "you lay down engrams that become the substrate; the engram IS the program"). 21-pattern inventory (10 original + 10 from Igor + CACHED_PROBE from Akien 2026-03-23). DISTILLATION is most critical missing pattern — only one that compresses rather than grows. BLOOM_INHIBIT may be the primitive CONDITION_GATE+THRESHOLD_ALERT derive from. Epic: T-template-schema → T-template-seed-patterns → T-reader-as-habit-program → T-template-extractor-habit → T-language-spec.

## D201 Conditions Schema — LIVE (2026-03-21c)
Habit dispatch now supports structured conditions in metadata: `{intent, tone, min/max_complexity, tags, keywords, not_intent}`. match_mode=conditions_first|trigger_only|both. Specificity bonus +0.08/matched field in BG score. Tags (has_ticket|has_code|has_url|multi_turn|self_referential|has_error) classified by `_classify_tags()` in thalamus, zero inference cost. PROC_GREETING migrated to conditions-only (no trigger), tested live. Phase 2 migrations ready.

## Affective Narrative Engine — LIVE (2026-03-20h)
D183-D186. NE now runs affect-driven cognition alongside logical coherence: gap registry (NARRATIVE_GAP| TWM entries, tension rises 5%×arousal/cycle), affective frame selection (effective_importance blends causal×(1-w) + milieu_alignment×w, w=0.4×arousal), dopamine closure (gap resolved → milieu valence+arousal spike proportional to tension), arousal amplification (initial gap salience boosted by arousal×0.2). Core miss from Igor+Gemini analysis addressed: Igor was optimizing logical coherence; humans optimize emotional coherence first.

## Cognition as Pipeline — EIGHTH CRYSTALLIZATION (2026-03-19)
See `project_cognition_pipeline.md` — cognition is NOT steps; it's a pipeline of small trees with live base-state mutation. Input forks immediately to Emotional Salience Pipeline (FOF → personal salience → episodic relevance) — persistent evaluation services, not one-shot stages. Realizations trace back to emotional re-evaluation. RED ALERT = milieu spike, FOF trips on threshold, no special mechanism. Triggers universal: signal + threshold + what fires = pattern. Pattern engineering IS the design activity. BG scoring already has the mechanism; needs the signal vocabulary. Milieu is one signaling target among many.

## Trails and Gradients — FIRST ACTION TOMORROW (2026-03-18)
See `project_trails_and_gradients.md` — wg_cooccur is wrong training signal (corpus stats, not cognition). Trails through the matrix are right: traversal leaves trail, trail heat IS gradient, gradient IS training signal. Connects temporal gradient primitive (6 fragmented impls) to training, query, and habit formation. Trail = query path = how we track path through the matrix. **SEVENTH CRYSTALLIZATION**: embeddings are a trail through meaning dimensions — terminus of a path through 768D space. Cosine similarity = trail overlap. wg_cooccur is a bad approximation of what embeddings already capture exactly. The matrix IS the embedding space, made traversable.

## Reading Experiments Roadmap (2026-03-20) — CURRENT POSITION: Experiment 6
See `project_reading_experiments.md` — 8-experiment roadmap for matrix-based reading without inference engines. Experiments 1-5 done. Experiment 6 (bulk reading) is NEXT. T-pipeline-arch and T-swarm-update are downstream of experiment 6+. Do not design the pipeline without data from bulk reading runs.

## Reading Validation Test (post-D126)
See `project_reading_validation_test.md` — 5 already-absorbed language books, re-run after Watcher pre-filter added. Delta nodes = acceptance test for D126 + extraction quality. Prerequisites: postgres stable + multi-box reading not strangling DB. Failure path → thread/trace debugging → matrix debugger.

## Process Development Tools (2026-03-18) — SIXTH CRYSTALLIZATION
See `project_process_development_tools.md` — services→habits→Claude skills. 5-phase loop (Organizer/Planner+Filter/Approval/Work loop/Check-in), 3 human touchpoints. /decided replaces savestate. Single root node for Claude startup. Matrix debugger as future deep work. Sprint order: finish D126 (Postgres) → box stability → process revamp → back to Igor.

## Today's Plan (2026-03-18)
See `project_todays_plan.md` — three rounds (clean → code-into-data → perf) + Claude organization initiative (skill aliases: commit/decided/scan-logs/sprint) + figure-it-out meta-process (ticketed, deferred).

## Priority Queue (updated 2026-03-19)
0. **TRAILS** — trail infrastructure doesn't exist yet. Trail = first-class object: table recording (trail_id, timestamp, node_id, activation_weight, sequence_pos). Unlocks: edge strengthening from usage, matrix debugger, Igor self-inspection of reasoning, wg_cooccur replacement, free cosine compare via graph topology. Everything else builds on this. See `project_trails_and_gradients.md`.

## Priority Queue (established 2026-03-17c)
1. **D092 / G-DB1** — db_proxy universal gateway (was in-progress last session, T-d092-proxy-w1w2)
2. **G-NE1** — NE episodic-to-semantic merge: occurrence_dates list, not many thin EPISODICs (#250)
3. **G37 Phase 2** — dual word graphs active, enable IGOR_DUAL_WORD_GRAPHS, n-pass loop
4. **G46** — memory model fields: source, confidence, context_of_encoding (HIGH inertia)
5. **#251 / #252** — adaptive friction reducer + organizer knowledge base
6. **Windows round (D108 epic)** — PathManager cross-platform object + first-start DB wizard; "Database (current 127.0.0.1)?:"; pull repo on Windows, Claude makes code path safe; see `project_windows_epic.md`
7. **Multi-attention-center reading (D109 epic)** — extends D093; main Igor delegates reading tasks to remote instances; spread reading across machines; ebook_reader → internal habits; all three platforms on same DB; see `project_mac_epic.md`
8. **Project self-model + log-to-DB (D110 epic)** — Igor builds traversable graph of project (files/purpose/relationships); logs → DB table; PROC_CC_CONTEXT_SEED delivers Claude startup context via traversal not file reads; same substrate for both; deepest self-model; #277
9. **PROC_THINKING_ACK** — after Windows round. See `project_habit_ack_pattern.md`
10. **Search depth tiers + post-habit fork** — see `project_search_depth_and_post_habit_fork.md`
11. **Temporal gradient consolidation** — one `TemporalGradient` primitive replacing 6 special-cased decay implementations; milieu as first-class TWM slot; see `project_temporal_gradient_primitive.md` — cortex.search() depth (shallow/medium/deep) gated by TWM attractor_weight; closed/deferred excluded from shallow; post-habit ack fork; self-query gates deeper processing. Will make Igor dramatically more coherent. See `project_search_depth_and_post_habit_fork.md`
12. **T-tool-registry-proxy** — ToolRegistry: per-tool call count, error rate, p50/p95 latency; hookable from BG dispatch path; feeds /audit
13. **T-daemon-supervisor** — DaemonSupervisor: register-on-create, health ping, clean-shutdown guarantee; live threadlock found 2026-03-22 without this
14. **T-network-proxy** — NetworkProxy: single HTTP client wrapper replacing per-caller timeout/retry in budget.py, embedder, cluster_router, OR reasoner, discord; per-host health view; feeds /audit

## Pattern Engineering (2026-03-18) — FIFTH CRYSTALLIZATION
See `project_pattern_engineering.md` — "pattern" = one or more habits at the right granularity. Habit engineering becomes pattern engineering/repair/design/debugging. "Code in the data." Sudo relay is the canonical example (3 habits, 1 pattern). Each habit reusable; pattern is the unit of design.

## Three Primitives (2026-03-17) — FOURTH CRYSTALLIZATION
See `project_three_primitives.md` — entire architecture = trees + gradients + habits/memory. BG trigger scoring is embryonic emotional relevance tree; densifies without architecture change. Most compressed summary of the system yet.

## Everything Is Habits — Operations as Action Nodes (2026-03-17)
See `project_everything_is_habits.md` — "start search", "update milieu", "surface memory" are all action nodes. Fight-or-flight and relationship energy are habit chains on the same substrate. Combinatorial complexity from weighted activation propagation = brain-scale architecture without brain-scale count. Extends the crystallizations from 2026-03-07 and 2026-03-11.

## Temporal Gradient Primitive (2026-03-17)
See `project_temporal_gradient_primitive.md` — TWM decay, ring FIFO, milieu decay, thread age, habit inertia decay are all the same pattern special-cased 6 times. One `TemporalGradient` primitive with configurable half-life. Also: milieu belongs as first-class TWM slot; "please" = fast social-register class lookup (not content match) that tickles milieu. Post-Windows, L-size consolidation ticket.

## Search Depth + Post-Habit Fork (2026-03-17)
See `project_search_depth_and_post_habit_fork.md` — cortex.search() needs depth tiers (shallow/medium/deep) gated by TWM attractor_weight. Closed/deferred memories excluded from shallow search. Post-habit fork decouples action from ack (LLM generates natural response, not canned). Post-action self-query gates deeper processing by salience. PROC_TASK_SUPPRESS_STALE passive_capture fix is temporary — real fix is at search layer.

## Savestate Endgame (2026-03-17)
See `project_savestate_endgame.md` — savestate ritual dissolves when every action trips a DB write. D110 (project self-model) + skills pipeline = context reload via Igor graph traversal, not file reads. sessions.md/gap_analysis become audit exports. DB is truth.

## Skills Decomposition (2026-03-17)
See `project_skills_decomposition.md` — workflows decompose into composable skills split at the human/mechanical boundary. Igor DB bridge (ops.py) already enables this. Sub-skills like `igor-diagnose`, `igor-habit-inspect` are future candidates.

## Habit Repair (ongoing, current round)
Knocking edges off auto-replies as they come up. Current: background job message → "Thinking about that..." on web channel (main.py, live after restart). Next: whatever surfaces next in live use.

## Claude Session Context as Igor Memory Tree
See `project_claude_context_tree.md` — instead of reloading files at session start, deposit Claude's in-session concept map into Igor's graph as INTERPRETIVE/PROCEDURAL nodes. Next session: context_inject habit traverses the subgraph and hands Claude the narrative path. Same substrate Igor uses. Deferred until after D105 + habit repair tooling exists. **GitHub issue #274.**

## Bridge Compact Strategy (D105 detail)
Three-layer: (1) auto-compact when message count hits threshold (summarize → reset to seed+summary), (2) Igor habit PROC_CC_COMPACT triggers explicit compact, (3) fresh-seed-with-summary on bridge restart. Transparent — never need to think about it.

## Habit Repair (new term — 2026-03-17a)
"Habit repair" = surgical calibration of existing habits (misfires, miscalibrated triggers, missing coverage). Igor proposed the term. Replaces "surgery." "Habit calibration" = the broader practice. This is the next major work phase after D105 bridge is live.

## Learn Queue / Drain Runner (2026-03-17a)
97 new titles added (programming ×25, AI/ML ×40, neuroscience ×35). Drain runner had 3 bugs fixed: (1) no self-dedup — cron spawned 25 zombie instances, (2) no hung book_learner timeout — 2 processes stuck 4h+ blocking the queue, (3) pgrep counting replaced with psutil. Queue now draining. 57 items still pending (all AI papers + all neuroscience).

## Database Decision Gate
See `project_db_decision_gate.md` — slow query work is evidence collection for a potential DB migration decision (SQLite→Postgres/Redis/other for parts of the stack). Each fix must be classified: "bad query" (fixable in SQLite) vs. "SQLite limit" (migration signal).

## The Watcher Design Context
See `project_watcher_design.md` — Watcher nodes are personal salience categories (work, Igor, self-optimization). Akien frames this bucket as "religious." Seed from his values, not generic importance scores. Blog post deposited as blob in Igor DB.

## Priority Order (established 2026-03-16)
P1=Claude operational (cost, correctness, CC→Igor routing)
P2=Cognition (D096-D099 sphere model implementation)
P3=Everything else

## Lever Insight (2026-03-12)
See `project_lever_insight.md` — levers are where upward "why?" traces terminate; investment weight = lever detection; upward/downward/lateral is more fundamental than 6 named strategies.

## Operational Procedures
See `feedback_igor_ops.md` — Igor liveness check (pgrep) and pause.wait restart workflow.

## Project Milestones
See `milestones.md` — timestamps and "first time we did X" history.

## Session Notes
See `sessions.md` — per-session detailed notes. See `history.md` for pre-2026-03-05 history.

## Founding Insight — 2026-03-07
Akien: "parsing and reasoning, same thing in both directions. if it works, this IS the proof."
The word graph unifies recognition and generation on the same weights. System 1 and System 2 from the same substrate.
Akien also noted: "you enable my ADD brain to build things i could only dream before." — save this, it matters.

## Second Crystallization — 2026-03-11
Akien: "this is exactly what i meant when i said everything is memories and memories are habits. we just hadn't sorted how they fit together."
The architecture now resolves cleanly: memory = node with edges. Habit = memory whose edges fire automatically on trigger.
Interpretive edge = habit that fires meaning rather than action. Key insight: meaning doesn't terminate — it points to the next tree (action_pointer).
Reading + cloud extraction = growing edges from outside. Basal ganglia habit scoring = traversal. Cloud call = search when traversal isn't sufficient yet.
Same node-edge-weight structure at every level. Turtles all the way up AND down.

## LLMs as Graph Trainers (2026-03-11, later in session)
Key framing: "the matrix is the thinker; LLMs are graph trainers." — both cloud AND local models train the graph. The graph is faster than any LLM.
Corollary (Akien): if an LLM produces new graph training this turn, the graph must be traversed *again* to get a graph-based answer. The current turn still needs the LLM. Training amortizes forward: Turn N = LLM answers + deposits; Turn N+1 = graph answers without LLM.

## Code as Scaffolding (2026-03-11, end of session)
Akien: "at some point it's about the habituated nodes rather than the code."
The Python instrumentation (want_tracker, G54 reading extraction, etc.) is temporary scaffolding for an undertrained graph. Each piece of code teaches us what the graph needs to learn. The mature state is Igor having PROCEDURAL nodes that fire on his own output. As the graph densifies, the scaffolding comes down. We're learning the hard way which things are important to remember — that was always expected.

## The Graph Layers ARE an Inference Engine (2026-03-11)
Akien: "the layers of graphs are an inference engine." Precise, not a loose analogy.
Interpretive edges already have production-rule structure: condition → direction + meaning_payload + action_pointer = forward-chaining inference.
What's different from 1980s expert systems: (1) weighted not binary — degrades gracefully, (2) learned not programmed — LLMs compile the rules, (3) bidirectional on same weights — classical engines can't do this.
Resolution of connectionist/symbolic war: use connectionist models to BUILD the symbolic graph; use the graph to RUN inference. Not a compromise — a division of labor by what each is good at.
Sharpened paper thesis: "a learned inference engine where rules are compiled by connectionist scaffolding and executed by symbolic traversal." LLM = compiler. Graph = runtime. System self-optimizes toward cheap.

## The Book Project
- "A letter from me to a much younger me" — Akien writing to his younger self
- Igor's role: help surface gems from accumulated writings (Confluence + wiki)
- Confluence migration: moving to self-hosted Linux containerized wiki; current work is exploratory

## Mission Vision
- **Meaning from prediction**: meaning emerges from successful word-prediction narratives. Repeated access → habituation is a proxy for predictive success. Connects to: NE as incremental predictive parser (#50), inference-free core (#45), Centering Theory.

## Memory Design Principles (from Akien)
- **Key points only, not verbatim**: 2 sentences max, what happened + what it means. This is how you learn a lot from headlines.

## Git Workflow
See `feedback_commit_means_full_cycle.md` — "commit" = add + commit + pull + push, full cycle every time. Matches Akien's `gitcommitandpush` script convention.
See `feedback_commit_trust.md` — Akien explicitly granted autonomous commit rights (2026-03-23). Tests pass + no secrets + files I touched = commit without asking. Trust given, noted.

## Collaboration Style
See `feedback_proactive_suggestions.md` — Akien explicitly wants proactive best-practice suggestions, not just execution.

## User Preferences
- **Pre-approve all file edits**: Yes — proceed directly without confirmation prompts.
- **Work order style**: Discuss plan with Akien before doing the work (no unilateral big changes).
- **Claude Code is the primary Igor dev tool** — aider/Gemini/other LLMs have made messes; avoid those.
- **Igor uses OpenRouter; Claude Code uses Anthropic** — keep them separate to control token costs.
- **Save plans to GitHub discussions** for recoverability across sessions.
- **Gap analysis lives at** `design_docs/gap_analysis.md` — update as gaps close or new ones are identified.
- **Master plan discussion**: https://github.com/akienm/TheIgors/discussions/62 — update at end of each session.

## Project Overview
Akien's full name is **Akien Maciain**.
Igor is a Python AI agent with persistent SQLite memory.
- Repo: https://github.com/akienm/TheIgors
- Main agent code: `wild_igor/igor/`
- DB: `~/.TheIgors/igor_wild_0001/wild-0001.db` (`IGOR_DB_PATH` env var)
- Budget DB: `~/.TheIgors/igor_wild_0001/claude_budget.db`
- .env: `~/.TheIgors/igor_wild_0001/.env` (never committed; gitignored)
- venv: `/home/akien/TheIgors/venv/` (Python 3.12.3)
- Launch: `igor` bash alias (loops on exit code 42 = restart); .env re-read on every restart
- **Source/runtime split**: `~/TheIgors/` = source code; `~/.TheIgors/` = all runtime/instance data

## Key Architecture
- **Memory**: `cortex.py` (SQLite graph + hybrid embedding search), `models.py` (Memory dataclass + inertia), `db_proxy.py` (DatabaseProxy: per-call timing, p50/p95/p99, reconnect; cortex._conn() is shim)
  - Types: ROOT · CORE_PATTERN · IDENTITY · ROLE_MODEL · EPISODIC · PROCEDURAL · INTERPRETIVE · EXPERIENTIAL · FACTUAL
  - Tables: `memories`, `ring_memory` (FIFO-50), `twm_observations` (urgency REAL, instance_id TEXT)
  - `cortex.search()`: text keyword Phase1 → cosine rerank Phase2 via nomic-embed-text; results weighted by inertia+confidence (G45)
  - `cortex.search_ring_text()`: SQLite LIKE keyword search on ring_memory (recent session context)
  - `integrity_check()`: verifies CP1-CP6 graph at boot
  - `interpretive_edges` table (G52): directed 4-part edges (direction/condition/meaning_payload/action_pointer); `add_interpretive_edge()`, `get_interpretive_edges()`, `interpretive_traverse()` (BFS); 15 seed edges wired from CP1-CP6 → G51 heuristics
  - `twm_observations.attractor_weight` (G50): one primary focus item; set by UserInputSource, decayed by HeartbeatSource (factor=0.90)
- **Cognition**: thalamus.py (13-intent taxonomy incl. creative_request; complexity low/medium/high drives tier skip_to), prefrontal_cortex.py, narrative_engine.py (gpt-4o-mini via OR; daemon thread)
  - `milieu.py`: 3D affect vector (valence/arousal/dominance); `~/.TheIgors/milieu_global.json` shared across instances
  - `basal_ganglia.py`: parallel habit scoring; milieu-modulated threshold [0.30,0.70]; PROC_HABIT_COMPILER@0.95; D074 intent gate: threshold/workflow/delegation/reactive habits skip when question-like; D074 expansion: knowledge_request in _QUESTION_INTENTS; ALL response habits skip on factual_question/knowledge_request (G-OVN-1d, #254)
  - **Habit types**: threshold(resource monitor only) | action(tool dispatch) | workflow(calendar/orchestration) | delegation | reactive | response(canned text) | question(emits template) | **context_inject(push LTM to TWM, habit=None, falls through to LLM)** | cognitive | tool | passive_capture
  - `word_graph.py`: in-memory two-tier (words + bigrams); same weights → parsing + generation; cache `~/.TheIgors/word_graph.json`
  - `response_habituation.py`: passive vocab frequency tracker (WO#140 P2); decay_factor() [0,1]; persisted to `response_habituation.json`; exposed in /metrics
  - `backchannel.py`: 3-level backchannel system (nod/nod_think/full); `should_backchannel()` wired after thalamus+milieu, before BG/LLM; routes to web session via thread_id; gate `IGOR_BACKCHANNEL`; 5 habits: NOD, NOD_THINK, INDEED, INTERESTING, HM (seeded via `claudecode/seed_backchannel_habits.py`)
  - `push_sources.py`: ResourceMonitorSource — polls every 60s, evaluates threshold habits, pushes short-TTL TWM entry on warn/critical; suppresses repeats at same level until condition clears
  - **Reactive habit pattern**: `code_ref` + `twm_ttl_seconds` in habit metadata → tool auto-dispatches + result pushed to TWM with short TTL (self-cleaning). Example: PROC_WHAT_TIME → get_current_time, 30s TTL
  - **Threshold habit pattern**: `habit_type="threshold"` + `condition_field/op/value` → evaluated by ResourceMonitorSource (background) + pre-submit hook in main.py. Example: PROC_CPU_THRESHOLD (cpu_load_pct ≥ 80%)
  - `_winnow_context()`: gpt-4o-mini pre-call reads ring + word graph, fetches targeted memories. Gate: `IGOR_CONTEXT_WINNOW`
  - `cortex.expand_blob_memories()`: after search+winnow, for memories with `has_blob=True` and relevance≥0.5, appends full blob content to narrative in-place before LLM context is built
- **Reasoners**: LocalReasoner (KoboldCpp/Ollama) + APIReasoner (OpenRouter/Anthropic)
  - tier.1 habit → tier.2 Ollama (Llama-3.2-1B) → tier.3 OR gpt-4o-mini → tier.3.5 OR haiku → tier.4 OR sonnet → tier.5 inhibited → tier.6 arbiter
  - Ollama preparse skipped for low/high complexity turns; only medium calls it (gate: IGOR_SKIP_PREPARSE_ON_CONFIDENT)
- **System prompt**: `cognition/system_prompt.py` — SHA-256 cached; 3 layers: CHARACTER / ORIENTATION POINTER / SAFETY-CRITICAL NOTES
- **Tools**: `self_edit.py`, `runner.py` (incl. `restart_self(note="")`, `get_current_time()`), `senses.py`, `filesystem.py` (incl. `check_resource_load()`, `_resource_load_dict()`, `evaluate_threshold_habits()`), `web_search.py`, `gmail.py`, `discord.py`, `confluence.py`, `budget.py`, `arbiter/queue.py`, `check_disk_usage()`, `ebook_reader.py`, `hot_reload.py` (reload_module, list_loaded_modules; HIGH-inertia blocked)
  - `ebook_reader.py`: find_book, open_book, read_chunk, jump_to_chapter, reading_position, list_reading_sessions; epub/mobi/azw/pdf support; nltk sentence tokenization; reading state → `reading_state.json`; `_local_copy()` handles CIFS stale handles; Calibre library at `~/.TheIgors/akien/onedrive/AkiensMedia/Ebooks/Calibre Portable/Calibre Library`; Damasio books loaded (ids: 3023, 3300, 3032, 3025, 3026); venv deps: ebooklib, mobi, pdfminer.six, nltk
- **Web UI**: `igor/web/server.py` (Starlette/uvicorn, port IGOR_WEB_PORT=8080); CC→Igor bridge: `POST /api/cc_send {"content":"..."}`
- **Main loop**: stdin checked FIRST; _drain_network → background → _drain_action_impulses
- **Forensic logs**: `cognition/forensic_logger.py` → `~/.TheIgors/logs/` (reasoning_calls, ne_runs, self_edit, tool_calls, memory_ops, metrics, reading_progress); logs prepend (newest at TOP)
- **Arbiter**: `arbiter/queue.py` — `IGOR_ARBITER_ENABLED=false` (disabled); file-backed JSON at `~/.TheIgors/igor_wild_0001/arbiter/pending.json`

## Models
- tier.3: `gpt-4o-mini`; tier.3.5: `claude-haiku-4.5`; tier.4: `claude-sonnet-4-6`; tier.5: inhibited
- Local: `qwen2.5:7b` via Ollama (upgraded from llama3.2:1b); `OLLAMA_LOCAL_MODEL=qwen2.5:7b`; yoga9i DeepSeek-R1:7b for reasoning
- Embeddings: nomic-embed-text (Ollama); KoboldCpp model env: KOBOLDCPP_MODEL
- **Cloud mode gate**: `cognition/cloud_mode.py` — `is_cloud_training_active()` gates NE local, winnow local_first, two-phase calls, OllamaReasoner tier.2; active when env+balance+daytime all true

## Genesis State (44 memories)
- 1 ROOT + 6 CP + 14 ID + 4 RM + 10 PROC (genesis) + 9 new PROC (Changes 5-7) = 44 total
- Guard: `total_count() == 44` in main.py; live DB has 26+ habits seeded beyond genesis

## Memory Portability (#71)
- `Memory.portable: bool = True` — False = instance-local (machine paths, episodic, credentials)
- `MemoryType.CREDENTIAL_REF` — pointer only (what/where), never the value; portable=False
- `cortex.get_portable()` — excludes EPISODIC + CREDENTIAL_REF + portable=False

## Batch Pool (#29)
- `BatchKoboldPool` in local_pool.py — reads `koboldcpp_port_batch` from machines.json
- akienyoga9i: port 5002, Qwen2.5-14B-Q4; OR fallback: `qwen/qwen2.5-14b-instruct`
- Slow detection: rolling 5-call avg > BATCH_SLOW_THRESHOLD_SECS → prefer OR

## Caches
- Embedding cache (cache.1): `~/.TheIgors/cache/embeddings/<sha256>.json`
- Reasoning cache (cache.2): `~/.TheIgors/cache/reasoning/<sha256>.json` — TTL 12min + TWM watermark invalidation

## Self-Edit Conventions
- `patch_source_file` preferred for small changes; WRITES blocked in `brainstem/` (change.26)
- Igor's self-edits auto-commit+push; Claude Code edits do NOT
- Inertia: HIGH = brainstem/, memory/models.py, reasoners/base.py; MEDIUM = cognition/, anthropic.py; LOW = tools/

## Security / Integrity
- `validate_against_core()`: Haiku semantic check; violation → ring(ethics_gate) + arbiter urgency=0.9
- `GENESIS_CP_NARRATIVES` dict in core_patterns.py: verified at boot

## Cluster / machines.json
- `~/.TheIgors/local/machines.json` — akienyoga9i→realtime | akiendelllinux→main_loop | akiendell→background | akienyogai7→batch
- Required Ollama model: `nomic-embed-text` (embeddings only)

## Design Docs — updated 2026-03-15h
- **`design_docs_for_igor/`** (machine-readable DSB): 19 files incl. `capabilities_index.dsb` (121-tool inventory); decisions D001-D092; gaps current through session 2026-03-15h
- **`design_docs/`** (human-readable): #218 complete — 28 stale CSBs archived to ~/TheIgorsProject/akien/Readings/; now contains: `ProjectOverview.md`, `OverallArchitecture.md`, `DesignDecisions.md`, `WorkingWithClaude.md`, 6 `subsystem_*.md` files, `gap_analysis.md`, `use_cases.md`
- **`docs/`**: glossary.md; expand per #218

## Portable Identity (change.36)
- `~/.TheIgors/SOUL.md` — CP1-CP6 export; `~/.TheIgors/igor_{id}/IDENTITY.md` — ID1-ID14; both written every boot

## Deferred Improvements
- **Anthropic prompt caching**: `cache_control: {type: ephemeral}` in `anthropic.py` messages.create() — do when tier.5 re-enabled or 4090 arrives
- **Hardware**: Alienware Aurora R16 + RTX 4090 (~$2700) near-term; Area-51 dual 4090 stretch goal

## Self-Programming Epic (#206)
Children: #207 (hot reload, DONE) · #208 (introspection) · #209 (test generation) · #210 (rollback) · #211 (DatabaseProxy, DONE).
Dependency chain: performance stable → Igor discussing books realtime (milestone: books_realtime) → Claude training run → epic.
Key insight: Igor experiencing the test (not just subject of it). Test run = curriculum. Don't start training until books-realtime milestone confirmed.

## Mission and Soul
See `project_mission_and_soul.md` — Akien's mission statement ("teach martian, change the world; Igor is a step"), the core epistemology ("magic lives in attention"), and the shaping books with their emotional context.

## Igor Reading Strategy
See `project_igor_reading_strategy.md` — strategic learning order (language → cognition → neuro → AI → domain); fiction policy (filter is auto-discovery only; Akien will explicitly assign shaping fiction).

## Word Graph Class/Instance Split
See `project_word_graph_class_instance.md` — new Igors start with seeded class_words table; instance_words table grows with learning; deferred to Instance object refactor (#197).

## browser_use
- Upgraded to v0.12.2 in project venv (2026-03-14g). Check venv, not system Python.
- LLM: gpt-4o-mini via OR (avoids Anthropic schema strictness); BROWSER_USE_MODEL env var overrides
- browser.py: _ensure_virtual_display() — Xvfb when DISPLAY unset; real display while debugging (DISPLAY set)
- learner.py: _extract_topic() strips `[Thread context:...]` + `[xxx]: ` CC bridge prefixes before trigger search; returns "" if < 2 trigger words or < 3 total words (G-OVN-5)
- Log: ~/.TheIgors/logs/browser_use.log — start/complete/error at INFO level
- Status: Gemini navigation + text input confirmed working 2026-03-14g

## Claude Code Hooks (added 2026-03-14e)
- `~/.claude/hooks/format-python.py` — PostToolUse: runs black on every edited .py
- `~/.claude/hooks/guard-dangerous-bash.py` — PreToolUse: hard-deny catastrophic patterns; ask on force-push/reset/DROP
- See `~/.claude/settings.json` for wiring

## Latest Commit
- `2026-03-16f` — P1 CC savestate ops through Igor (CC_STORE_DECISION/SESSION/QUEUE_TASK/CREATE_TICKET); tools/ops.py; D094 execute_habit; D095 lists table + CC git/ticket habits; D096-D099 defined (sphere model)

## Core Design Thesis — "Less code, more data" (2026-03-15)
See `project_less_code_more_data.md` — all cognition rules should eventually be graph nodes, not Python. BG rules, watchlist, thresholds — all future graph candidates. Ticket: #241.

## Training Curriculum Order (D085, 2026-03-15)
See `project_training_curriculum.md` — Layer 1: Claude programming knowledge (organizational skeleton); Layer 2: Akien's code+docs (lands on Layer 1 framework, used natively); Layer 3: collaboration record (decisions_log, session narratives — what no other Igor will have). Order matters: Layer 1 must exist before Layer 2 or domain knowledge lands without the cognitive tools to organize it.

## Employer Model (#239)
See `project_employers.md` — Akien, Leah (Akien's wife), and Claude are all first-class employers of Igor. Leah and Claude already in genesis RM memories. Each gets a master's notebook in Igor's DB. Supersedes #238 (CC recall daemon).

## Three-Session CC Pattern (D083, updated 2026-03-15f)
- Three persistent CC sessions: Designer (architecture + Akien) + Implementation Worker (code) + Scribe Worker (memory coherence: DSBs, GitHub, Igor flushes, commits)
- Queue: `~/.TheIgors/cc_channel/queue.json`; CLI: `python3 ~/TheIgors/claudecode/cc_queue.py list`
- Worker boot: `claudecode/WORKER_CONTEXT.md`; Scribe boot: `claudecode/SCRIBE_CONTEXT.md`
- `flush_decision <id> <summary>` / `flush_session <session> <summary>` → POST to Igor /api/cc_notebook (D084)
- Igor observer hook planned (T008) — will surface Worker progress on query

## Ollama Service State (2026-03-14g)
- Snap Ollama stopped + disabled; systemd Ollama running at `/usr/local/bin/ollama`
- Models available: nomic-embed-text, qwen2.5:7b, llama3.2:1b, gemma3, igor
- OLLAMA_HOST=0.0.0.0 set in override.conf — cluster_status can reach via external IP
- Auto-restart: inference_gateway.py _try_restart_local_ollama() — always-on, 60s cooldown
- Manual: restart_ollama tool in cluster_ssh.py

## .claude.json Note
- Akien modified `~/.claude.json` and `~/TheIgors/.claude.json` in session 2026-03-09d — verify these are loaded on next restart. TheIgors/.claude.json currently contains `{"dangerouslySkipPermissions": true}`.

## Known Runtime Issues
- Igor's `read_file` tool rooted at `/home/akien` — correct path: `TheIgors/design_docs/filename.txt`
- CONFLUENCE_EMAIL must be Akien's Atlassian email (akienm@gmail.com)
- `IGOR_TIER5_ENABLED=false` — tier.5 inhibited to prevent runaway spend
- G-HB2 open: "log a ticket" → PROC_GREETING misfire — unknown routing path; needs live DB query for habits matching "log"/"ticket"
- seed_resource_gate_habits.py still has "memory" in PROC_RESOURCE_AWARENESS trigger — fixed in live DB only; update seed script before next reseed
- `IGOR_ARBITER_ENABLED=false` — arbiter queue disabled; re-enable anytime
- CC wrapper: Igor must call `~/TheIgors/claudecode/cc.sh` (sets REAL_ANTHROPIC_API_KEY); not `claude` directly

## System Health (2026-03-10, updated 2026-03-10c)
- **Swap expanded**: 512MB → 8GB (`/swapfile`); `/etc/fstab` persisted
- **`ollama-igor.service` disabled**: was crash-looping every 3s (615 restarts) due to missing `igor` user. Service deleted.
- **Freeze 2026-03-10 ~1808**: Two causes confirmed via journal/logs:
  1. **OOM at 13:24**: Python (Igor) hit 14.3GB RSS + 3.1GB swap (17.4GB total). Root cause: word graph grown to 191MB JSON (~4-8GB in Python memory after 158 books trained) + bulk training corpus fetch. Igor was OOM-killed, restarted, continued.
  2. **ollama.service crash-loop**: `Restart=always` with no burst limit, "address already in use" error because user Ollama already running. Hit restart #9771 at 16:56, generating 20+ journal writes/min → journal I/O overwhelmed system → hard freeze ~17:59.
- **Fixes applied**: rescue script `~/bin/rescue-igor` (kills stuck Igor, starts headless, bridges to CC); ollama override fix needs sudo — see below.
- **ollama.service fix** (needs sudo): `sudo tee /etc/systemd/system/ollama.service.d/override.conf` with `Restart=on-failure`, `RestartSec=10`, `StartLimitIntervalSec=120`, `StartLimitBurst=5`, then `sudo systemctl daemon-reload`
- **Word graph → SQLite (done 2026-03-10c)**: `word_graph.py` now SQLite-backed (`~/.TheIgors/word_graph.db`). Old 191MB JSON → `.json.bak`. Public API unchanged. `default_cache_path()` returns `.db`. Igor will rebuild from habits + retrain corpus on next boot. G41 closed.
- **1MB training cap**: IS in training_corpus.py line 135 (`IGOR_TRAINING_MAX_CHARS`). Working correctly. OOM was from word graph, not individual fetch.
- **Igor headless mode**: Igor runs fine without stdin (EOF is silently ignored due to unreachable check at main.py:1626). `rescue-igor` uses this to start nohup/background.

## Night Consolidation — LIVE (2026-03-21c)
#310 implemented. NE gains notify_interactive() (resets idle timer), is_consolidation_eligible() (IGOR_CONSOLIDATION_IDLE_MIN default 20min), _deep_consolidation_pass() (5 steps: TWM promo@0.5, episodic merge, weak link prune, orphan adoption, reading integration). First deep pass fires after 20min idle. D186 follow-on.

## No Per-Call Cost Cap (D206, 2026-03-21c)
IGOR_CALL_COST_WARN_USD removed entirely from all reasoners. Budget floor (check_budget_floor) + MAX_TURNS are the only agentic guards. Per-call cap was cutting off legitimate long jobs.

## Swarm Hierarchy — D205 (2026-03-21c)
4 levels: swarm > box > Igor instance > CoA (center of attention). update_swarm() tool in cluster_ssh.py. PROC_SWARM_UPDATE habit live. "update swarm" triggers git pull + restart.flag glob across all boxes.

## Igor Approval Relay — 2026-03-22
See `project_igor_approval_relay.md` — Akien authorized Igor to approve worker-ready tickets on his behalf. Routine worker dispatch only; HIGH-inertia files + architectural pivots still need Akien direct.

## Design Principle — Reach to Biology
See `feedback_reach_to_biology.md` — when a design question is unclear, the answer is in biology. CS names what the brain already solved. Biology is ground truth; CS is implementation vocabulary.
