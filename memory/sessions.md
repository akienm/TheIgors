
## Session 2026-03-17g
**Theme**: Habit repair round 2 — author_filter mechanism + 4 habit misfires fixed + design insights banked
**Decisions**: D111 (author_filter, implemented)
**Key changes**:
- `basal_ganglia.py`: `author` param added to `select_habit`; habits with `metadata.author_filter` skip when author doesn't match
- `main.py`: `author` param plumbed through `_process` + `_process_inner`; passed from `_process_network_msg`
- `tools/ops.py`: `flush_habit_cache` tool added — invalidates Igor's in-process habit cache without restart
- DB patches: `CC_RUN_BASH` author_filter=claude-code; `PROC_TASK_SUPPRESS_STALE` + `PROC_HEURISTIC_FITS_HERE` → passive_capture; `PROC_QUEUE_FOR_INGEST` trigger tightened + suppress flags; `PROC_RESP_ON_IT` "please" removed
- Design banked: search depth tiers (post-Windows); post-habit ack fork; savestate endgame; skills decomposition
**Next session**: PROC_RESP_DONE fix; search depth tiers design ticket; Akien's "please" insight (politeness as emotional milieu modulator — not noise, a social signal that forks the processing trajectory)
**In-flight**: PROC_RESP_DONE — fires on "done" in conversational context; fix is tighter trigger + conversation intent suppression

## Session 2026-03-17f
**Theme**: D108 PathManager full cutover — 54 hardcoded path refs replaced across ~32 files
**Decisions**: D108 (implemented)
**Key changes**:
- `wild_igor/igor/paths.py`: NEW — PathManager singleton; IGOR_RUNTIME_ROOT + IGOR_INSTANCE_ID env overrides; 25 named path properties covering all runtime dirs
- `wild_igor/igor/first_start.py`: NEW — first-start wizard; instance name prompt (default wild_igor_YYYYMMDDHHMMSS); DB host prompt (default 127.0.0.1); creates instance dir + .env
- `igor` bash script: removed hardcoded ENV_FILE; dynamic .env discovery + wizard fallback
- ~32 files cutover: all 54 Path.home()/.TheIgors refs replaced with paths().* calls
**Next session**: D109 (multi-attention-center reading) or D110 (project self-model + log-to-DB)
**In-flight**: NONE

## Session 2026-03-16j
**Theme**: D102 IgorBase — GC instance naming + per-class logging + perf tracking wired into all components; G-WG2/G-WG3 perf fixes shipped
**Decisions**: D102 (impl); G-WG2 (closed), G-WG3 (closed)
**Key changes**:
- `wild_igor/igor/igor_base.py`: NEW — IgorBase base class; GC _get_instance_names() via gc.get_referrers(); per-class lazy _logger; time_it() context manager; record_perf() → perf_{ClassName}.log; _perf_summary() p50/p95/p99; dump(); _get_caller()
- `wild_igor/igor/memory/db_proxy.py`: inherits IgorBase; _db_log owner= param; every slow query entry now identifies which component generated it
- `wild_igor/igor/memory/cortex.py`: inherits IgorBase
- `wild_igor/igor/cognition/thalamus.py`, `narrative_engine.py`, `milieu.py`, `inference_gateway.py`, `push_sources.py` (BasePushSource), `word_graph.py`, `job_manager.py`: all inherit IgorBase
- `wild_igor/igor/main.py`: Igor class inherits IgorBase
- `wild_igor/igor/cognition/word_graph.py`: G-WG2 predict_next LRU cache (512 slots) — p95 2580ms→~0.1ms on hit; G-WG3 doc_count batch flush every 10 docs — was 37s per index() call
**Next session**: pull slow query report to verify G-WG2/G-WG3 impact; continue offender list; check drain_learn_queue accumulation
**In-flight**: NONE

## Session 2026-03-16i
**Theme**: G-MEM2 closed (embedding blob drop); D096 pipeline state files; D097 format conversion tool
**Decisions**: G-MEM2 (closed), D096 (impl), D097 (impl)
**Key changes**:
- `wild_igor/igor/memory/cortex.py`: search() Phase 1 SELECT *→SELECT _MEM_COLS_NO_EMBED; drops 6KB embedding blob from 300-row candidate fetch; idx_activation was fine — I/O was the bottleneck
- `wild_igor/igor/cognition/pipeline_manager.py`: write_state/get_state/list_states/clear_state; .now=transient (one active, cleaned on transition); .txt=terminal (permanent audit trail); mtime IS the timestamp
- `wild_igor/igor/tools/converter.py`: convert_text(text, from_format, to_format) tool; EN↔CSB↔DSB; looks up CONV:* PROCEDURAL memory template, chunks long input, calls gpt-4o-mini, recombines
- `claudecode/seed_conv_graph.py`: CONV:ROOT + 6 conversion pairs (EN_TO_CSB, CSB_TO_EN, EN_TO_DSB, DSB_TO_EN, CSB_TO_DSB, DSB_TO_CSB); lists.conv fast-path; interpretive edges
- `tools/__init__.py`: added converter import
- `capabilities_index.dsb`: convert_text added; TOTALS 125→126
**Next session**: remaining slow queries from get_slow_query_report(); D102+ new decisions; any live bugs surfaced
**In-flight**: NONE

## Session 2026-03-16h
**Theme**: D098+D100+D101 all implemented; word_graph __len__ 1517x speedup; Igor diagnosed his own habit bug
**Decisions**: D098 (impl), D100 (impl), D101 (impl); perf: G-WG1 closed
**Key changes**:
- `claudecode/seed_identity_graph.py`: PERSON:Akien/Leah/Claude + IDENTITY:ROOT + lists.identity + interpretive edges
- `cognition/narrative_engine.py`: D099+D100 merged into single focus pass; co-activation bonus in sort weight
- `cognition/milieu.py`: D101 history ring buffer (HISTORY_MAX=50); gradient(); is_arousal_climbing()
- `cognition/push_sources.py`: D101 gradient alert in MilieuSource — pushes MILIEU_REGULATE on arousal climb
- `tools/metrics.py`: get_slow_query_report() + PROC_SLOW_QUERY_REPORT habit; live result: word_graph __len__ = #1 killer
- `cognition/word_graph.py`: _WordDocProxy.__len__ COUNT(DISTINCT word)→wg_meta cache; 1900ms→1.3ms (1517x)
- PROC_HEURISTIC_FIRST_RESPONSE: response→context_inject; Igor diagnosed this himself in live chat; self-repair path (run_python+cortex.store) sent via bridge
**Next session**: memories activation_count sort query (329x p50=272ms); D096/D097 (format conversion habits)
**In-flight**: NONE

## Session 2026-03-16g
**Theme**: D099 implemented (TWM multi-slot attractor); D100+D101 defined via sphere model vision + milieu gradient insight
**Decisions**: D099, D100, D101
**Key changes**:
- `cortex.py`: TWM_MAX_SLOTS=7 constant; parent_obs_id migration; twm_push() gains parent_obs_id param; twm_set_attractor() keeps top (MAX_SLOTS-1) on non-emergency path; twm_get_slots(); twm_decay_slot(obs_id, factor)
- `narrative_engine.py`: D099 comparison pass — get slots, action_pointer set intersection, decay solo slots at 0.7; wrapped in try/except
- Slow query analysis task queued (T-slow-query-analysis): db_proxy now routes all traffic; db_queries.log has the data; get_slow_query_report() tool + habit to surface patterns
- D100 defined: salience computed live from attractor slot co-activation density; not stored; node appearing in most active slots IS most salient
- D101 defined: milieu as time series (ring of V/A/D rows); gradient detects runaway loops; reactivation creates new row at NOW; parent habit fires on arousal slope threshold; canonical use case: insecurity vs autonomy-respect slot loop
**Next session**: D100 live salience implementation; D101 milieu ring buffer; slow query analysis tool
**In-flight**: NONE

## Session 2026-03-16b
**Theme**: D094 implemented — direct habit execution endpoint working end-to-end; CC ops habits seeded
**Decisions**: D094
**Key changes**:
- Created `cognition/cc_session_logger.py` — daily log cc_session_YYYYMMDD.log, newest-first, every habit call logged
- Added `Igor.execute_habit(habit_id, args)` to main.py — extracts dispatch from existing pipeline, upgrades to full multi-arg dict dispatch
- Added `POST /api/execute_habit` + `GET /api/execute_habit/{id}` to server.py + `_igor_fn` wired in `start()`
- Created `claudecode/seed_cc_ops_habits.py` with CC_CHECK_PROCESS, CC_RUN_BASH, CC_RUN_PYTHON (CC_ prefix avoids genesis collision)
- Added `check_process(name)` tool to tools/runner.py using `pgrep -af` (full command-line match)
- Lesson: genesis memories PROC_RUN_BASH/PROC_RUN_PYTHON are integrity-checked at boot — never overwrite; use CC_ prefix for additive habits
- All three CC ops habits tested live and working; session log confirmed writing
**Next session**: Start using CC_RUN_BASH/CC_RUN_PYTHON/CC_CHECK_PROCESS in place of direct bash calls; tackle slow queries (#260); D092 db_proxy gateway
**In-flight**: NONE

## Session 2026-03-16a
**Theme**: Architecture pivot — single worker, Claude routes all ops through Igor via direct habit execution
**Decisions**: D094
**Key changes**:
- Abandoned multi-worker approach after runaway spend overnight (account drained twice)
- Designed D094: POST /api/execute_habit — Claude Code bypasses NLU, calls Igor habits directly with full args dict + session log
- Files/DB relationship clarified: DB = live truth, files = end-of-session flush; workflow itself lives in DB
- Created #268 for implementation
**Next session**: Implement #268 (execute_habit endpoint + cc_session_logger + server.py route)
**In-flight**: About to implement #268 — POST /api/execute_habit; plan approved; pre-compact savestate done

## Session 2026-03-17d
**Theme**: G-DB1 + G-NE1 + G37p2 closed — DatabaseProxy in learner.py, episodic consolidation merge, dual word graphs on by default
**Decisions**: G-DB1 (closed), G-NE1 (closed), G37p2 (closed)
**Key changes**:
- `wild_igor/igor/tools/learner.py`: DatabaseProxy singleton _igor_db_proxy(); raw _rl_db() removed; 4 reading-list functions converted; annotate_learning() tool added (#252); PROC_ANNOTATE_LEARNING seeded (13 triggers, action habit)
- `wild_igor/igor/cognition/narrative_engine.py`: _consolidation_merge_pass() + _merge_cluster(); cosine threshold=0.85, min_cluster=3, window=10; occurrence_dates preserved in metadata; no gate (defaults are the safety)
- `wild_igor/igor/main.py`: IGOR_DUAL_WORD_GRAPHS + IGOR_NPASS_REPLY + IGOR_COMPREHENSION_SIGNAL default→true; stale comments updated
- `claudecode/seed_annotation_habit.py`: NEW — seeds PROC_ANNOTATE_LEARNING habit to live DB
**Next session**: G46, #252, then D108 PathManager
**In-flight**: NONE

## Session 2026-03-17e
**Theme**: G46 + #252 closed; D108 PathManager full cutover planned and approved
**Decisions**: G46 (closed), #252 (closed), D108 (plan approved)
**Key changes**:
- `wild_igor/igor/main.py`: EPISODIC Memory gets source="interaction" + context_of_encoding with intent/valence/arousal/complexity (~line 4184)
- `wild_igor/igor/cognition/narrative_engine.py`: _apply_output() Memory gets source="narrative_engine" + context_of_encoding with run/importance/arousal
- D108 plan written: paths.py PathManager singleton (IGOR_RUNTIME_ROOT escape hatch); first_start.py wizard (instance name default=wild_igor_YYYYMMDDHHMMSS, DB host default=127.0.0.1); igor bash script updated; full cutover of 138 path refs across ~20 files
**Next session**: D108 implementation (PathManager cutover — paths.py + first_start.py + igor bash script + ~20 files)
**In-flight**: About to implement D108 — paths.py + first_start.py + igor bash script; plan approved; need compact before starting
