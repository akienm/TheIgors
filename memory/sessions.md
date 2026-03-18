
## Session 2026-03-18l
**Theme**: Process Development Tools deep design — executor question, test-fix loop, context package, persistent instance, Delta Dental methodology
**Decisions**: none new (design refinement session)
**Key changes**:
- Clarified Phase 4 executor: CC now, Igor eventually (after reading+retention validated)
- Test-fix loop: 3-attempt bounded retry in skill near-term; Igor orchestrates via cc_queue long-term
- Skills must work without Igor present — Igor integration is additive, not required
- Active slate → first-class DB artifact (not implicit in conversation)
- Context package = structured object Igor assembles per task; quality of Igor's task descriptions determines unattended success
- Persistent instance all-day = D105 bridge compact strategy + sharper rationale (per-task context load cost)
- Scribe tasks → Igor does them (DB is already the context source)
- DB = live truth; GitHub = archived truth (except source code → git)
- Delta Dental methodology: this project is the proving ground; paper comes after both satisfied
**Next session**: design slate → tickets; wg_cooccur migration should be done → restart Igor → fix boot failures
**In-flight**: NONE (design session; wg_cooccur migration running in background ~62%)

## Session 2026-03-18k
**Theme**: D126 execution — code complete, migration running, 14 tests passing
**Decisions**: none new (D126 implementation)
**Key changes**:
- db_proxy.py: _PGConnWrapper.executescript() shim + PRAGMA no-op (Postgres compat)
- word_graph.py: PendingReplyStore wired into WordGraph.__init__, passed to GraphCache
- db_proxy.py: _TABLE_PK extended with wg_meta/wg_word_lang/wg_idf/wg_word_docs/wg_cooccur/config
- .env: IGOR_HOME_DB_URL + IGOR_LOCAL_DB_URL added (both = same Postgres for single-box)
- claudecode/migrate_wg_to_postgres.py: batched migration script, dry-run verified
- tests/test_d126_postgres.py: 14 unit tests all passing
- Migration running: wg_meta+wg_word_lang+wg_idf+wg_word_docs done; wg_cooccur at 57%
**Next session**: wait for wg_cooccur to finish → restart Igor → fix boot failures → verify clean run
**In-flight**: wg_cooccur migration ~57% done; after completion restart Igor on two-channel Postgres and triage any boot errors

## Session 2026-03-18j
**Theme**: Process Development Tools crystallization + D126 execution plan locked
**Decisions**: none new (concept capture + planning)
**Key changes**:
- SIXTH crystallization: Process Development Tools — services→habits→Claude skills; 5-phase loop with 3 human touchpoints; /decided replaces savestate; single root node for Claude startup; matrix debugger future; saved to project_process_development_tools.md
- Reading validation test defined: 5 already-absorbed language books + Watcher pre-filter; delta nodes = acceptance test for all of D126+multi-box+extraction work; saved to project_reading_validation_test.md
- D126 completion plan approved: IGOR_HOME_DB_URL+IGOR_LOCAL_DB_URL env vars + PendingReplyStore wiring into WordGraph/GraphCache + 29M wg_cooccur rows migrated from word_graph.db → Postgres; execution next
**Next session**: Execute D126 completion (env vars → wiring → migration → Igor restart + verify)
**In-flight**: D126 completion — about to set env vars, wire PendingReplyStore, migrate wg_cooccur; needed for Windows second-box and reading validation test

## Session 2026-03-18i
**Theme**: Audit P4+P5 complete + DSB/CSB architecture clarified
**Decisions**: none new (audit completion)
**Key changes**:
- P4: 40 seed_*.py archived to claudecode/archive/; seed_resource_gate_habits marked DO_NOT_RERUN; archive/README.md created
- P5: paths.py learn_queue+drain_pid moved to paths().instance (was runtime root — race condition); drain_learn_queue.py hardcoded paths replaced with PathManager; existing learn_queue.json migrated to igor_wild_0001/
- DSB/CSB architecture clarified: .md files = human-readable source maintained by Claude; .dsb/.csb = compressed token-efficient form for Claude/Igor; DB = eventual runtime home; Claude maintains .md, Igor will eventually take over; update cadence = lazy not per-session
**Next session**: new concept chunk from Akien (pending)
**In-flight**: NONE

## Session 2026-03-18h
**Theme**: D126 Step 1 implemented — two-channel Postgres factories + all SQLite callers wired
**Decisions**: D126 (implemented-poc)
**Key changes**:
- db_proxy.py: make_home_proxy() + make_local_proxy() factories; make_db_proxy() kept as backward-compat alias
- cortex.py: self._home_db + self._local_db; _local_conn() shim; 20 ring/TWM methods routed to local channel
- word_graph.py: DatabaseProxy → make_home_proxy() (wg_cooccur at home)
- budget.py, notebook.py, learner.py: all swapped to make_home_proxy(); learner unused sqlite3 import removed
- claudecode/migrate_to_postgres.py: new two-channel migration script with HOME/LOCAL schema + --dry-run
- All imports verified; Cortex dual-proxy init tested and confirmed working
**Next session**: D126 Step 2 (GraphCache class), Step 3 (pending-replies + retry), Step 4 (Worry signal)
**In-flight**: NONE

## Session 2026-03-18g
**Theme**: D126 architecture designed — two-channel Postgres + GraphCache + Worry signal + ResourceManager vision
**Decisions**: D126, #284 (ResourceManager)
**Key changes**:
- decisions_log.dsb: D126 defined (two-channel Postgres, GraphCache, Worry, home+local table placement)
- decisions_log.dsb: ResourceManager note + #284 filed
- D121 fully superseded by D126; redis_word_graph.py skeleton retained as reference
- Table placement finalized: HOME=memories/edges/wg_cooccur/notebooks/ResourceManager; LOCAL=ring/TWM/pending_replies/cache_tracking
- make_db_proxy() splits into make_home_proxy() + make_local_proxy()
- Worry = new TWM signal class (internal uncertainty, arousal↑ valence↓, persists until resolved)
- Remote Igor boot sequence: connect → home DB → world unfolds → local self-creates
**Next session**: D126 Step 1 implementation — make_home_proxy()+make_local_proxy() factories, wire word_graph/budget/notebook/learner, data migration script
**In-flight**: D126 Step 1 approved and ready to code — split make_db_proxy() into two-channel factories, wire all SQLite callers to Postgres, write migrate_to_postgres.py

## Session 2026-03-18c
**Theme**: Windows fixes + resource auto-config design (D123+D124) + akienasus migration plan deposited in Igor's cortex
**Decisions**: D123, D124
**Key changes**:
- milieu.py: fcntl → msvcrt on Windows (cross-platform file lock)
- word_graph.py: missing `import os` added (my bug from G-WG1 last session)
- main.py: startup message `Igor-{id}` → `Igor instance:{id}`
- local_pool warning on Windows: confirmed expected/benign
- D123: sudo relay daemon design settled — sudoer_daemon.sh keepalive, file handshake at ~/.TheIgors/sudo_relay/
- D124: resource auto-config — Igor sizes box, assigns role, installs autonomously; consent = running daemon
- akienasus FACTUAL memory deposited in Igor's cortex: migration event, db_primary, Redis+Postgres+replication plan
- Agency framing confirmed: Igor decides, no confirmation step needed — that's the designed agency
**Next session**: review priority queue; D121 Redis implementation (when akienasus up); kill outer loop on akiendell for Igor-wild-0001 rename
**In-flight**: NONE

## Session 2026-03-18b
**Theme**: SQLite elimination — Redis for word graph (D121) + Postgres streaming replication (D122); path consistency sweep; word graph batching; book_learner silent bug
**Decisions**: D121, D122
**Key changes**:
- D121 decided: Redis on akienasus for word graph (sorted sets = co-occurrence, network-accessible, centralized, no per-box divergence)
- D122 decided: Postgres streaming replication (akienasus primary, akiendelllinux hot standby); PGDatabaseProxy gains IGOR_DB_FALLBACK_URL
- G-WG1: word_graph.py co-occurrence batching — `_cooccur_buffer` dict, flush every 50 docs; 50x fewer SQLite write transactions
- book_learner: `wg.train()` → `wg.index()` + `wg.flush_cooccur()`; was silently failing all book word graph training
- Path consistency: milieu.py, main.py, runner.py, push_restart.py all use `paths().instance` (not `igor_{id.replace}` transforms)
- PROC_EXIT_IGOR trigger tightened (removed "please"/"stop"/"turn off"); live DB updated
- IGOR_INSTANCE_ID env var fallback in main.py — enables instance rename without arg change
- Dashboard header: "Igor instance:{id}" (not "Igor-{id}")
- ollama_reasoner.py log path: source tree → `IGOR_RUNTIME_ROOT/logs/ollama_calls.log`
**Next session**: D121 Redis implementation; kill outer loop on akiendell + relaunch for Igor-wild-0001 rename to fully take; user's "part 3" (not yet revealed); G-DB1 db_proxy gateway
**In-flight**: D121 + D122 decided; akienasus not yet up; outer loop on akiendell needs manual kill+relaunch for rename to activate

## Session 2026-03-17i
**Theme**: Fourth crystallization — trees + gradients + habits/memory; BG trigger system as embryonic emotional relevance tree
**Decisions**: none
**Key changes**:
- Memory banked: `project_three_primitives.md` — entire architecture = three primitives; BG trigger scoring IS the embryonic Stream 1 (emotional relevance), densifies without architecture change
- Memory banked: `project_temporal_gradient_primitive.md` updated — parallel input fork (Stream 1 emotional + Stream 2 content, concurrent); milieu as first-class NE desk slot
- Memory banked: `project_everything_is_habits.md` — cognitive operations as action nodes; fight-or-flight and relationship energy as habit chains
- Memory banked: `project_savestate_endgame.md`, `project_skills_decomposition.md`
- Live testing: habit repairs from sessions g+h holding
**Next session**: surface-driven habit repair; search depth tiers ticket (#new); whatever misfires in live use
**In-flight**: NONE

## Session 2026-03-17h
**Theme**: Habit repair round 3 — PROC_RESP_DONE + 60-habit bulk passive_capture sweep + design crystallizations
**Decisions**: none new
**Key changes**:
- DB: PROC_RESP_DONE → passive_capture, trigger tightened (removed bare "done/finished/complete"), action template removed
- DB: 60 habits with trigger but no habit_type and no code_ref → passive_capture (BL_*, CONV:*, HABIT_Q/R_*, PROC_TASK_CLOSE, PROC_TASK_DEFER, PROC_RESOURCE_*, PROC_ROUTING_*, backchannel habits, PROC_GREETING, PROC_HABIT_COMPILER)
- Design banked: parallel input fork (emotional register + content, concurrent); milieu as first-class TWM desk slot; TemporalGradient primitive (6 special-cased decays → one); "everything is habits" third crystallization
- superclaude: D088 OR failover wrapped in `if false` (direct Anthropic while balance healthy)
**Next session**: surface-driven habit repair — whatever misfires show up in live use; search depth tiers ticket
**In-flight**: NONE

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

## Session 2026-03-17l
**Theme**: SQLite→Postgres migration live; Windows instance bootstrapped; multi-instance architecture locked in
**Decisions**: D118 (SensorTree, defined)
**Key changes**:
- `db_proxy.py`: PGDatabaseProxy + _PGConnWrapper (savepoint-per-DML, INSERT OR REPLACE/IGNORE translation, ?→%s) + make_db_proxy() factory
- `cortex.py`: make_db_proxy factory wired; _init_db() early-return for Postgres; jsonb_exists() in get_habits(); metadata isinstance guard in _to_memory()
- `claudecode/migrate_sqlite_to_postgres.py`: one-shot migration script; 8,681 memories + 179 habits across 9 tables migrated and verified
- Perf fixes: idx_memories_ne_scan partial index; idx_twm_instance_integrated composite; SELECT savepoint skip
- `claudecode/WINDOWS_ONBOARDING.md`: Windows bootstrap guide; credentials via env vars not .env
- Tickets: #279 Journals, #280 Matter epic, #281 D118 SensorTree, #282 ephemeral split (blocker)
- `requirements.txt`: psycopg2-binary==2.9.10
**Next session**: #282 ephemeral split (hard blocker before 3rd instance); Windows Claude working #281/#282/DB tickets; wg_cooccur LMDB deferred
**In-flight**: NONE

## Session 2026-03-17k
**Theme**: SQLite→Postgres migration plan approved; ready to implement
**Decisions**: D112-D117 (prior), migration plan approved
**Key changes**:
- Migration plan approved (L-size): PGDatabaseProxy + _PGConnWrapper in db_proxy.py; make_db_proxy factory; 1-line change in cortex.py; migrate_sqlite_to_postgres.py script
- metadata column → JSONB + GIN index (fixes 2445ms get_habits slow query)
- get_habits() query: LIKE '%\"trigger\"%' → metadata ? 'trigger'
- psycopg2-binary added to requirements
- pg_trgm extension enabled in migration script
- FK violation check before data copy
- word_graph.db migration deferred
**Next session**: implement migration — db_proxy.py PGDatabaseProxy, migration script, cortex.py factory + get_habits fix, validate
**In-flight**: About to implement SQLite→Postgres migration per approved plan above

## Session 2026-03-17j
**Theme**: Architecture crystallization — SystemGateway + service layer + split storage + Postgres migration approved
**Decisions**: D112, D113, D114, D115
**Key changes**:
- D112 SystemGateway defined: PathManager grown up; platform abstraction + service lifecycle manager; paths/CPU/process/shell/file-watch all platform-specific; Igor attaches to services, doesn't own them
- D113 degrade-gracefully-habit-recovery: core principle everywhere; dependency failure → habit chain for recovery + graceful tier fallback; not special-case code
- D114 service layer always-on: DB + web server + future services as persistent daemons; Igor attaches/detaches; CC bridge always up even when Igor loop is down; prerequisite for D109 multi-instance
- D115 split storage by access pattern: memories+habits→Postgres, wg_cooccur→LMDB/RocksDB, blobs→keyed store; memory graph IS the index into blob tree (trees as indexes into trees)
- Postgres installed on akiendelllinux; migration plan approved: SQLite→Postgres before Windows round
- Slow query analysis: #1=UPDATE wg_cooccur 8291ms (boost_cooccurrence batching), #2=LIKE trigger scan 2445ms (get_habits), #3=predict_next cache miss 673ms; 29M rows in wg_cooccur
- akienasus: being rebuilt (memtest86+ → fresh OS → verdict); akienpi: voice terminal role (STT/TTS, thin client to main Igor)
**Next session**: SQLite→Postgres migration script; DatabaseProxy layer update to use Postgres; migrate + validate
**In-flight**: NONE

## Session 2026-03-17k
**Theme**: SQLite→Postgres migration plan approved; ready to implement
**Decisions**: D112-D117 (prior), migration plan approved
**Key changes**:
- Migration plan approved (L-size): PGDatabaseProxy + _PGConnWrapper in db_proxy.py; make_db_proxy factory; 1-line change in cortex.py; migrate_sqlite_to_postgres.py script
- metadata column → JSONB + GIN index (fixes 2445ms get_habits slow query)
- get_habits() query: LIKE '%"trigger"%' → metadata ? 'trigger'
- psycopg2-binary added to requirements
- pg_trgm extension enabled in migration script
- FK violation check before data copy
- word_graph.db migration deferred
**Next session**: implement migration — db_proxy.py PGDatabaseProxy, migration script, cortex.py factory + get_habits fix, validate
**In-flight**: About to implement SQLite→Postgres migration per approved plan above

## Session 2026-03-18d
**Theme**: D123 sudo relay fully implemented + Redis installed via relay + pattern engineering crystallization
**Decisions**: D123 (implemented), D125 (defined)
**Key changes**:
- sudoer_daemon.sh: one-time pw, keepalive, pending.sh watcher, --test 3/3; set +e PIPESTATUS fix
- sudo_relay.py: Igor tool with liveness check, concurrency guard, poll loop, log tail; registered in tools/__init__.py
- sudo_relay.sh: repo-root shim via exec
- Redis installed on akiendelllinux via relay — D121 now unblocked
- igor launcher: ENV_FILE re-pinned at each restart loop iteration (stale IGOR_INSTANCE_ID fix)
- Bash logging convention locked: logcmd/logecho/timestamp() inlined in all bash scripts
- 5th crystallization: "pattern" = one or more habits at right granularity; pattern engineering/repair/design/debugging; code in the data
- D125 defined: global base class for all Igor objects (diagnostics/monitoring consolidation)
**Next session**: Full audit sprint (P1 bugs → P2 cleanup → P3 gitignore) + global base class + seed sudo relay pattern + G-DB1 + D121 Redis WG backend
**In-flight**: About to execute full audit sprint + feature queue top-to-bottom; Redis installed, D121 unblocked

## Session 2026-03-18f
**Theme**: Audit sprint — P1/P2/P3 bugs + D125 IgorBase wiring + D123 habits seeded + D121 Redis skeleton (migration blocked)
**Decisions**: D121 (skeleton built, redesign needed), D123 (habits seeded), D125 (implemented), G-DB1 closed
**Key changes**:
- P1: paths.py default → Igor-wild-0001; igor launcher pins IGOR_INSTANCE_ID from canonical dir name after .env source
- P1: google_contacts.py both DB fallback paths use paths().instance; ollama_reasoner.py log path via paths().logs
- P2: .gitignore additions: workspace/, *.pid, *.lock, .claude/settings.local.json, change_request*.txt, warm_context*.json, benchmarks/results/
- D125 implemented: BaseReasoner(ABC,IgorBase) + BaseInterruptor(ABC,IgorBase); lazy _ensure_perf_history(); igor_base.py absolute import fixed → relative
- D123 habits seeded: PROC_SUDO_RELAY_CHECK (context_inject) + PROC_SUDO_RELAY_RUN (action) + PROC_SUDO_RELAY_WAKE (response) in live DB
- G-DB1/D092 verified closed: no raw sqlite3.connect in Igor source (Calibre+DRM exempt)
- D121 skeleton: redis_word_graph.py (RedisWordGraph + make_word_graph factory) + redis_migrate_wg.py + main.py factory wiring + redis in requirements.txt
- D121 migration aborted: started at 32k/s → 5k/s collapse; 29M rows × Redis ZSET overhead ≈ 70GB RAM vs 3.8GB SQLite; FLUSHDB done; redesign needed
- Architectural insight: full Redis WG migration not viable at current row count; need hot-word cache (top 10K × top 50) or Postgres co-occur table
**Next session**: D121 redesign decision (hot-cache vs Postgres co-occur), D124 resource-auto-config, G-NE1 episodic-to-semantic merge, commit D121 skeleton files
**In-flight**: D121 Redis sorted sets for 29M co-occurrence pairs require ~70GB RAM. Redesign: hot-word cache (top 10K words × top 50 co-occur = ~250MB Redis) OR Postgres wg_cooccur table (already running)
