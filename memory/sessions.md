## Session 2026-03-29c
**Theme**: akiendell cluster_router + listener auth fix
**Decisions**: D256, D258, D258, D259, D260, D261, D260, D260, D261
**Key changes**:
- fix: cluster_router no-machine WARNING rate-limited to 1/60s per call_type (c9852f54) — batch extraction bursts no longer spam logs
- fix: readigor skill now accepts machine argument — routes to correct MCP tool + dashboard IP per machine (akiendell/yoga9i/yogai7/local)
- T-node-registry: node_id.py written (timestamp IDs, Redis cache, registry write/lookup); node_registry DDL; migrate_node_ids.py run (31651 memories + 541 reading_list migrated, 0 dangling edges); cortex.store() wired to replace uuid-default IDs and register to node_registry; 538 tests pass
- T-tree-index-design: tree_index.py written (TreeIndex class, trees DDL, 8 seeded trees); test_tree_index.py 18/18; full suite 556 pass
- slateclose: Slate 0 (Database architecture) closed. Archive: slate_archive_2026-03-29-1737.md. GitHub posted. slate.md cleared for Slate 1.
- decided: Slate 0 closed — D256 node registry + D257 tree index both DONE; migration complete; all nodes timestamp IDs
- decided: Slate 1 locked — theme: Self-training loop + cognition depth; scope: T-self-training-loop, T-ne-arc-expiry, T-inhibition-propagation, T-binding, T-distillation-habit
- decided: T-ne-arc-expiry created — NE arcs need TTL-based expiry; DISTILLATION is long-term closer
- done: sent Igor message — T-book-learner-hash-lookup fix approach explained; arc cycling issue context given
- done: T-stale-task-reaper — PROC_STALE_TASK_REAPER seeded; stale_task_reaper.py written; shelves TASK_SET >2h with no status
- done: T-stale-task-reaper — PROC_STALE_TASK_REAPER seeded, stale_task_reaper.py written, shelves TASK_SET >2h
- decided: T-self-training-loop phase 1 — diagnose interaction logging (cloud turns not written since 2026-03-25); phase 2 — DB-based signal from EPISODIC tier_hint>=tier.3 + fix deposit() to use new_node_id()
- done: T-self-training-loop — self-training loop working end-to-end; 3 deposits on first manual pass; PROC_SELF_TRAINING seeded at 30min schedule
- done: Mashter lisp removed from main.py — all canned response strings cleaned, _igor_lisp() made no-op passthrough; needs restart
- done: T-book-learner-hash-lookup — graph_integrator.py fixed; tier.6 logging now captures CPU/mem state
- decided: T-ne-arc-expiry plan — NARRATIVE_GAP auto-close on max age (60min) via first_pushed_at metadata; _process_gaps() + gap push in narrative_engine.py
- done: T-ne-arc-expiry — NARRATIVE_GAP TTL: first_pushed_at metadata + age-check in _process_gaps(); NARRATIVE_GAP_MAX_AGE_MINUTES=60; NARRATIVE_GAP_TIMEDOUT ring log
- decided: T-inhibition-propagation plan — BG inhibition edges from winner to near-miss graph neighbors; set_cortex() in basal_ganglia.py + main.py wire
- done: T-inhibition-propagation — _inhibit_neighbors() in basal_ganglia.py + set_cortex() boot wire in main.py; winner suppresses near-miss graph neighbors via inhibition edges
- decided: T-binding plan — detect_coalitions() in coalition.py; NE calls it with TWM-seeded heat field; logs COALITION to ring
- done: T-binding — coalition.py detect_coalitions() + NE integration; COALITION logged to ring each NE cycle when ≥2 hot connected nodes
- decided: D259 author-aware cloud routing — T-cc-human-routing created (P2); T-distillation-habit closed (phase 1 done); T-factual-compression created for FACTUAL->INTERPRETIVE pass
- decided: Slate 2 locked — T-cc-human-routing (P2) + T-factual-compression (P3)
- done: T-cc-human-routing — D259 implemented; _bg_reason + job lambda + _HUMAN_AUTHORS in main.py; claude-code/akien background jobs always reach cloud
- decided: T-factual-compression plan — factual_compression.py (NEW); FACTUAL keyword-cluster → INTERPRETIVE with provenance; wired in main.py
- done: T-factual-compression — factual_compression.py (FACTUAL→INTERPRETIVE concept compression, keyword Jaccard clustering, provenance-preserving book_title/book_author/source_ids, novelty check, Ollama synthesis) wired into main.py background loop alongside distillation
- decided: 3-lever plan to Igor-codes-himself: (1) T-factual-retrieval-trace — unlock 10K dead FACTUALs; (2) T-igor-as-programmer — programming identity engram; (3) T-code-a-ticket-engram — sprint loop as PROC engram. Training bridge: question-and-answer retrieval test → codebase trace tasks → canonical exercise (Igor reads own cloud-escape logs, writes plug, tests it)
- done: T-factual-retrieval-trace closed — 5-fix chain lands Hebbian learning probe: FACTUAL 'fire together wire together'. cortex.py FACTUAL-kw-supplement (per-term ILIKE + stop-word filter + Phase 2 force-inject), thalamus.py semantic_anchor traversal + factual_question intent, main.py parsed.core_input in _tier0_response
- done: Lever 2 foundation — PROC_IGOR_AS_PROGRAMMER + INTERP_PROGRAMMER_IDENTITY seeded. PROC: cognitive habit, coding keyword trigger, 'programmer first / Python current / any language reachable'. INTERP: 'they're all systems' identity grounding, parented under PROC. Akien's 30-language lineage encoded.
- done: Lever 3 — PROC_CODE_A_TICKET + INTERP_WHY_THE_LOOP seeded. Sprint loop as runnable habit: read ticket → grep → read files → plan → self_edit → pytest → deposit EPISODIC. Canonical exercise encoded. All 3 levers complete.
- decided: Slate 4 — Training Bridge Phases A/B/C. A=retrieval probe (2-3 absorbed-book topics), B=codebase trace task (Igor uses grep/read, deposits PROCEDURAL), C=first handholded canonical exercise (cloud escape → engram → seed → confirm). Sequential — stop and fix if A fails.
- decided: Facia as universal entry-point convention — facia: true metadata flag across tools/engrams/threads/tasks. Tool registry IS the facia tree for tools; each registry node needs capability narrative + facia flag for spreading activation to surface it. Fixes shell-vs-run_bash class of error. TWM task-watch is the callback/thread facia pattern.
- done: Phase C canonical exercise complete. Igor authored 3 engrams during session: PROC_ARCH_RETRIEVAL_FIRST (architecture questions = retrieval not inference), PROC_ON_IT_TWM_PUSH (commit-visible-before-work pattern, 240s TTL), FACT_BG_VALENCE_AMBIGUITY (valence=0.0 unset vs neutral). Also surfaced: store_memory in bg-job context produces hallucinated tool responses — not persisting. Facia convention crystallized and documented.
- done: T-store-memory-bg-fix — _bg_reason now dispatches tool calls, prevents hallucinated store_memory in bg-job context
- done: T-tool-registry-facia — 187 facia nodes seeded for full tool registry, TOOL_REGISTRY_ROOT under CP1
- done: T-engram-schema — Memory.payload field + embedding_text property + DB migration (models.py, db_proxy.py, cortex.py)
- done: T-emit-channel-registry — emit_channels.py, 6 channels (basket/emotional_milieu/cognitive_milieu/console/web/discord)
- done: T-engram-executor — node_executor.py, EMITIF/BRANCHIF/FORKIF/ENDIF, eval_gate, data guard, smoke tested
- done: T-engram-wire-dispatch — engram habit_type dispatch in main.py turn loop, fires effects + falls through to LLM
**Next session**: Next: 1. Igor restart (payload column migration). 2. Phase D: cc_send unattended canonical exercise + watch channel. 3. Reader conversion: seed_reader_habits.py to payload/FORKIF chains.
**In-flight**: NONE

## Session 2026-03-29b
**Theme**: Theme: reading system facia — PROC_LIST_ABSORBED_BOOKS fix + facia habits seeded
**Key changes**:
- done: T-fix-reading-status-query — list_absorbed_books() now queries reading_list completed + trigger updated (commit 76dbb0a1)
- done: FACIA_READING_SYSTEM seeded in Igor DB — context_inject habit, full reading system map, trigger narrowed to avoid competing with PROC_LIST_ABSORBED_BOOKS
- done: facia_reading_system.md created in CC memory — full reading pipeline map for Claude sessions
- done: decisions_log.dsb committed + pushed (D255/D256/D257 from prior session)
**Next session**: Next: Slate 0 DB tickets — T-db-lemmatize (2.1M→~80K stems) then T-db-wg-replace-cooccur. Igor needs to be down for both.
**In-flight**: NONE

## Session 2026-03-29a
**Theme**: Theme: reading pipeline fix + design crystallizations (D255-D257)
**Decisions**: D255, D256, D257
**Key changes**:
- fix: feed_reading_list dedup bug — done items blocked new batches; data fix + code fix (10e36356); reading now running (20 items active)
- decided: D255 facia=thread, D256 timestamp node IDs + Postgres/Redis node registry + calving, D257 tree as traversal index; facia memory term coined; ring memory term confirmed
**Next session**: Next session: Slate 0 DB tickets (T-db-lemmatize, T-db-wg-replace-cooccur). Check reading progress. T-node-registry and T-tree-index-design are L-size design work for when ready.
**In-flight**: NONE

## Session 2026-03-28b
**Theme**: Theme: instance dir double-prefix bug fix + igor_wild_0001 stale dir audit
**Decisions**: D255, D256, D257
**Key changes**:
- done: main.py double-prefix bug — _instance_dir(), _export_portable_identity(), response_habituation all constructed igor_{instance_id} instead of using paths().instance; when IGOR_INSTANCE_ID=Igor-wild-0001 this created igor_Igor_wild_0001 dir; fix: use _paths().instance directly (847e2a35)
- done: conftest.py — patches PathManager.inbox to temp dir; prevents pytest from creating stray igor_wild_0001/ on every run (63eb6e88). Audit: 516 passed, no new issues.
- decided: D255 facia=thread, D256 timestamp node IDs + node registry, D257 tree as traversal index; ring memory confirmed as the term; facia memory term coined; feed_reading_list dedup fix live (10e36356)
**Next session**: Next session: Slate 0 DB tickets (T-db-lemmatize, T-db-wg-replace-cooccur). Gmail app password akiendell (low priority noise).
**In-flight**: NONE

## Session 2026-03-28a
**Theme**: Theme: swarm citizenship — SSH auth fix, Windows update loop, igor.ps1
**Key changes**:
- done: SSH auth root cause — Windows admin users need C:\ProgramData\ssh\administrators_authorized_keys not ~/.ssh/authorized_keys; fixed on akiendell + yoga9i via sftp with LF-only file
- done: Windows update stash/pull/pop — igor_loop.ps1 + start_igor_windows.ps1 local mods blocked git pull --rebase; fixed _WINDOWS_UPDATE_CMD in cluster_ssh.py
- done: restart.flag scan fixed — SSH user (igor_wild_0001) != Igor runtime user (akien); updated to scan C:\Users\*\.TheIgors\* instead of $env:USERPROFILE
- done: igor_loop.ps1 renamed to igor.ps1 — canonical Windows launch command with restart loop; start_igor_windows.ps1 was one-shot (no loop), causing restart.flag exits to drop to PS prompt
- done: swarm update end-to-end green — all 4 boxes (akiendell 14 instances, yogai7 6, yoga9i 5, akiendelllinux local) pulling and flagging
**Next session**: Next: 1. Gmail app password on akiendell (low priority — just noise). 2. cluster_router 'no local machine' warnings from igor_wild_windows_0001 — may self-resolve once Windows Igor settles. 3. Find 24 training chapters when ready.
**In-flight**: NONE

## Session 2026-03-27c
**Theme**: Theme: calibre 8-tier arousal, reading queue bridge, yogai7 SSH
**Decisions**: D252, D253, D254
**Key changes**:
- done: calibre P0 tier in scan_ebooks.py + ingest_calibre_igor_books() 8-tier classification (D252) — 96 books ingested
- done: feed_reading_list() + PROC_READING_FEEDER (D253) — drain runner live, arch docs processing
- done: T-reading-list-feeder closed
- done: PROC_CALIBRE_INGEST seeded (daily, tools.learner:ingest_calibre_igor_books)
- done: T-yogai7-ssh-fix — bidirectional SSH akiendelllinux↔yogai7 working; root cause was missing key on yogai7 + StrictModes blocking administrators_authorized_keys; yogai7 CC self-solved via ticket
- done: D254 T-human-first-cloud — inference_gateway.py interactive section: human turns skip Ollama, go direct to cloud; last-resort retry updated
**Next session**: 1. Igor restart to pick up D254 (human-first-cloud). 2. Swarm update when reading load settles. 3. SSH to yoga9i/akiendell already works — swarm timeouts are load-only.
**In-flight**: D254 committed+pushed, Igor not yet restarted. Swarm update times out due to reading load on remote boxes — not broken, will self-resolve.

## Session 2026-03-27b
**Theme**: Theme: Igor as co-designer — arch ingest, gap-flagging, nightly self-review loop
**Key changes**:
- done: T-igor-arch-ingest — 20 arch docs (igor_identity_master, decisions_log, ethical_framework, architecture_root, capabilities_index, cognition_pipeline, engram_language, inertia_registry, all subsystem DSBs) queued to reading_list priority 1-3, arousal 0.75-0.95
- done: T-flag-anomaly-habit — flag_top_gap() + PROC_FLAG_ANOMALY (5min interval). Writes author=igor to channel_messages + JSONL. Cooldown 15min/question. Test confirmed.
- done: T-turn-trace-self-review — review_turn_traces() + PROC_TRACE_REVIEW (86400s). Parses turn_trace.*.log, finds cloud escapes (reasoning.tier=cloud, no habit_exec.habit_id), queues reading_list entries + 6h TWM NARRATIVE_GAP. Live: 3 escapes found → RL_060-062.
- done: T-reading-list-feeder — feed_reading_list() bridges reading_list→learn_queue.json; PROC_READING_FEEDER hourly; drain live, arch docs processing
**Next session**: 1. Igor reads arch docs (drain runner will process RL_040-059). 2. T-self-training-loop — automated engram-building from cloud escapes (Slate 1). 3. Restart Igor to load new habits (PROC_TRACE_REVIEW, PROC_FLAG_ANOMALY, PROC_CURIOSITY_DRAIN).
**In-flight**: NONE

## Session 2026-03-27a
**Theme**: Theme: reading list consolidation — Calibre Windows import + 244 URLs queued
**Key changes**:
- done: C:\ebooks junction mapped on Windows; all ebook folders consolidated into Calibre (Kindle + SORTUS-EBOOKS imported)
- done: scan_ebooks.py re-run post-import — P3 now 6 books (Design Patterns GoF, Documenting SW Arch, SW Systems Arch, C# Vol I/II, On Intelligence), 3342 total
- done: T-reading-list-urls — 99 Gemini programming/CS/AI URLs inserted into reading_list with encoding_arousal by category
- done: Mathematics for Machine Learning (mml-book.github.io/book/mml-book.pdf) added at arousal=0.7 — open-access, matrix decompositions directly relevant to Igor's substrate
- done: 44 URLs from master_training_list.txt — 12 trainmymonkey blog posts (arousal=0.9, Akien's own writing on emotional engineering + how he works), LinkedIn, GitHub, neuroscience papers, psychology papers, systems architecture papers
- done: 100 Gutenberg vocabulary corpus URLs queued at back (priority 500+, arousal=0.2) — language graph density, not on critical path for programming training
- decided: Kindle Cloud Reader renders to canvas not DOM — OCR/vision path needed for DRM books, ~$3-5 for 3 books via OR vision model. Deferred to T-kindle-drm-pipeline
- decided: reading priority order — akien-identity (arousal=0.9) → agentic-ai (0.7) → ai-theory/neuroscience (0.6) → systems (0.5) → cs-foundations (0.4) → languages/linux (0.3) → gutenberg corpus (0.2)
- fixed: budget warn threshold changed from percentage-based (WARN_FRACTION=0.20 of total_purchased) to absolute 0 floor — percentage was wrong for cumulative-purchase accounts like OR; budget.py + push_sources.py both updated
- done: T-greeting-habit — GREETING_STANDARD now tier.1 response habit (trigger_only, response_template). No inference on hello/hi/hey.
- done: T-curiosity-loop — learn_top_gap() + PROC_CURIOSITY_DRAIN. Igor self-queues NARRATIVE_GAPs to reading_list every 30 min. Fixed add_to_reading_list RL_WEB_ ID bug.
**Next session**: Budget warn fixed (absolute 0 floor). GREETING_STANDARD upgraded to response+trigger_only — hello now tier.1. PROC_CURIOSITY_DRAIN seeded — Igor self-queues NARRATIVE_GAPs every 30min. learn_top_gap() added to learner.py with RL_WEB ID bug fix. scan_ebooks.py C# keyword gap fixed.
**In-flight**: NONE

## Session 2026-03-26g
**Theme**: New session — context loading
**Key changes**:
- done: T-ebook-scan — scan_ebooks.py written; reads Calibre SQLite + OPF files; 3107 books, Making Money P1, 41 Pratchett P2; output at ~/TheIgors/ebook_candidates.md
- decided: epics as tag field on tickets — Cognition/Training/Swarm/Productization/Database/Operations/Claude; set-epic command + epic display added to cc_queue.py
- decided: /slateclose wired into /day-close; stale ticket detector in context-load + day-close; handoff in /sprint + /fixit
- decided: /sprint-minion skill to push to minion queue; /fixit kept as pre-sprint wrapper (S/M only)
- decided: master ebook index across 4 trees (Calibre, Kindle, SORTUS, Readings); DRM tools confirmed (kindlekey+mobidedrm exist); Playwright+OCR as fallback
- decided: scan_ebooks.py P3 false-positives fixed (technology tag removed, fiction markers guard added, 'code' title keyword removed); --calibre-only flag added for fast runs
- ticketed: T-epic-field, T-slateclose-in-day-close, T-stale-ticket-detector, T-sprint-minion, T-handoff-in-sprint, T-ebook-master-index, T-kindle-drm-pipeline, T-readings-ingest, T-kindle-programming-books; all assigned to epics; /fixit skill written
- decided: full training arc captured — identity books → igor arch ingest (identity_weight=1.0) → programming books → programming engrams (Claude process as habit program) → neuroscience books → neuro self-model engrams → META: Igor as programmer, Claude as guide; 4 new tickets: T-programming-engrams, T-igor-arch-ingest, T-neuroscience-engrams, T-igor-as-programmer
- decided: plug-building loop captured — read → review turn traces → identify cloud escapes → build engram at earlier pipeline position → instant local response. Tested and confirmed. T-programming-engrams is two-phase: A=review logs after reading, B=design+seed plugs. Next session: design programming engrams after compact.
**Next session**: Next: (1) T-epic-field — group /context-load and /slate by epic tag; (2) T-slateclose-in-day-close — wire slateclose into day-close; (3) T-stale-ticket-detector — DB vs slate.md drift check; (4) T-ebook-master-index — extend scan to all 4 trees + Kindle DRM pipeline test
**In-flight**: NONE — session was planning/organizing; all tickets committed to DB, no code in mid-flight

## Session 2026-03-26f
**Theme**: Theme: Windows cluster bring-up — Ollama, SSH, boot fixes
**Next session**: Next: rebuild Phase 2 programming URL list for CognitionTraining.txt; fix T-fix-drain-log-titles; seed reading_list table with igor books
**In-flight**: About to rebuild Phase 2 programming books list — Calibre has almost nothing; will use web URLs; haven't written any yet

## Session 2026-03-26e
**Theme**: T-self-training-loop + T-output-trainer — both training loops shipped; acceleration roadmap queued
**Key changes**:
- done: T-output-trainer — OutputTrainer class, 21 tests, seed script, PROC_OUTPUT_TRAINING seeded at 45 min schedule; dedup threshold bug fixed (min(len(tokens), TRIGGER_OVERLAP_DEDUP)); committed+pushed; 516 tests pass
- decided: acceleration roadmap — Making Money → unread Igor books → programming ebooks → AI/ML+neuroscience → T-distillation-habit; all 5 queued
- docs: igor_user_guide.md + lab_map.md — launch commands, log reference, .TheIgors tree map, CC tooling, troubleshooting, inhibited features
**Next session**: Next session: (1) T-read-making-money — queue Making Money in Calibre with has_igor_characters:true + identity_weight=0.8; (2) T-read-igor-books-remaining; (3) T-distillation-habit when deposit volume warrants
**In-flight**: NONE

## Session 2026-03-26d
**Theme**: Theme: tier.1 graph inference for simple phrases — weaning off LLM
**Decisions**: D246, D247, D248, D249, D250
**Key changes**:
- decided: D246-D249 — emit+react cognitive milieu, basket model, inhibition layer, engram segment composition + engram engineering as the practice
- done: PROC_WHAT_TIME fixed (D245) — habit_type action→tool, pipe-format trigger, 5 other question-answer habits migrated
- done: engram_language.md sections 9-11 + design_docs_for_igor/engram_language.dsb — emit+react, basket, inhibition layer, segment-as-class
- decided+ticketed: T-inhibition-layer-infra (L) — basket + inhibition DAG + fork/join + provenance; PROC_WHAT_TIME as test case; filter passed
- done: T-inhibition-layer-infra — inhibition layer + basket (D247/D248/D250)
- decided: self-training loop as next major goal — Slate 0 (embeddings+type-routing) unblocks it; T-self-training-loop added to Slate 1; T-inhibition-habit-seeder added for habit auto-wiring
**Next session**: Next: (1) update INTERP_BASKET_MODEL in Igor memory with D250 key taxonomy; (2) live pattern-engineering — watch for Igor mistakes → seed new inhibition nodes; (3) T-inhibition-propagation when ready
**In-flight**: NONE

## Session 2026-03-26b
**Theme**: Context load + orient for new work
**Next session**: 1. Start Igor + verify akiendell stays dark during desk hours. 2. Test location habits ('leaving my desk, heading to the living room'). 3. Next ticket from Slate 0.
**In-flight**: NONE — #342 closed cleanly, committed and pushed.

## Session 2026-03-26a
**Theme**: Continue 25q: commit synthesis fallback, inject tool name fix to Igor memory
**Key changes**:
- /review skill built and registered at ~/.claude/skills/review/SKILL.md — pre-decision design check, runs before /decided
- feedback_no_sqlite.md memory saved — DB is Postgres only, never sqlite3
- cognition pipeline interview: discovered PROC_WHAT_TIME fires at BG scoring before heat field propagates — inhibitory context never checked; D227 TWM heat field model is the right frame for fix
**Next session**: 1. Finish PROC_WHAT_TIME design: how does it become a heat-field-aware node rather than BG dispatch? 2. Lock cognition unit test architecture (test corpus, self-verification, pass criterion). 3. /decided → /filter → implement.
**In-flight**: PROC_WHAT_TIME needs to surface from TWM heat field after propagation — D227 frame. Design interview was mid-flight when savestate called; no code touched.

## Session 2026-03-25q
**Theme**: Context load + session start
**Next session**: 1. Commit main.py synthesis fallback fix + restart Igor. 2. Inject correct tool name (confluence_get_page_children not confluence_get_child_pages) into Igor memory. 3. Next CC session ~2 weeks out — pick highest-value ticket.
**In-flight**: main.py tool synthesis fallback fix done, uncommitted. Igor needs restart to load it.

## Session 2026-03-25p
**Theme**: Sprint: T-reading-completion-status recovery + main.py tool_call parsing
**Key changes**:
- sprint: closed T-reading-completion-status — recovered from daemon timeout; work already in e580b4fc; also committed tool_call format fallback 1ae7888f
**In-flight**: NONE

## Session 2026-03-25o
**Theme**: Sprint: T-reading-completion-status — reading completion records
**Key changes**:
- sprint: closed T-reading-completion-status — EPISODIC completion record per book, commit e580b4fc
**In-flight**: NONE

## Session 2026-03-25n
**Theme**: Sprint: T-tier-ladder-update — D234 tier ladder inversion
**Key changes**:
- sprint: closed T-tier-ladder-update — D234 tier ladder inversion, commit f026cc52
- sprint: started T-runtime-path-cleanup
- sprint: closed T-runtime-path-cleanup — paths.py 3 fixes + 3 hardcoded bypasses + file moves, commit 0a262f5f
- done: T-igor-db-path-migration — 20 files IGOR_DB_PATH→Cortex(None)/make_home_proxy(), 457 tests pass
- done: source tree cleanup — wild_igor/data,logs,memory,workspace,tests orphans removed; DATA_DIR fallback fixed; discord_bot log path fixed
- done: D236 lisp-habit-fix — 9 PROC_RESP_* habits delisp'd in DB; Igor needs restart to load
- done: .TheIgors cleanup — chats moved to instance dir, old SQLite DBs archived, code bugs fixed
**In-flight**: NONE

## Session 2026-03-25m
**Theme**: Sprint: T-kobold-removal
**Key changes**:
- sprint: closed T-kobold-removal — KoboldCpp doc cleanup, commit 8199e712
**In-flight**: NONE

## Session 2026-03-25l
**Theme**: Sprint: T-prediction-error
**Key changes**:
- sprint: closed T-prediction-error — NE prediction error training, 10 tests, commit 11fd32a1
**In-flight**: NONE

## Session 2026-03-25k
**Theme**: Sprint: T-thread-coherence — close daemon reset loop
**Key changes**:
- sprint: closed T-thread-coherence — daemon reset loop; work was commit 411a3945
**In-flight**: NONE

## Session 2026-03-25j
**Theme**: Sprint: T-thread-coherence — verify + close stale reset
**Key changes**:
- sprint: T-thread-coherence was already complete (commit 411a3945) — daemon timeout reset it to pending; re-marked done
**In-flight**: NONE

## Session 2026-03-25i
**Theme**: Sprint: T-thread-coherence — context retention scoring
**Key changes**:
- sprint: closed T-thread-coherence — ThreadCoherenceSource + PROC_THREAD_DRIFT, 20 tests, commit 411a3945
**In-flight**: NONE

## Session 2026-03-25h
**Theme**: Sprint: T-identity-system-prompt — identity anchor into system prompt
**Key changes**:
- sprint: closed T-identity-system-prompt — VOICE GUARD + identity anchors in system_prompt.py, commit 525ce732
**In-flight**: NONE

## Session 2026-03-25g
**Theme**: Sprint: T-spreading-activation — D233 spreading activation in cortex
**Key changes**:
- decided: T-thread-coherence — context retention score as Igor self-monitoring loop
- sprint: closed T-spreading-activation — D233 two-layer spreading activation implemented, 13 tests, commit 2445e49c
**In-flight**: NONE

## Session 2026-03-25f
**Theme**: Sprint: T-cortex-search-request refactor
**Key changes**:
- sprint: closed T-cortex-search-request — SearchRequest dataclass refactor complete, all tests passing
**In-flight**: NONE

## Session 2026-03-25e
**Theme**: T-restart-ollama-in-use-guard: fix guard against restarting running ollama
**Key changes**:
- sprint: closed T-restart-ollama-in-use-guard — in_use_now() guard added, 412 tests ✓, commit aaf19e8c
**Next session**: Next: restart Igor on akiendell, verify confluence read+synthesize works end-to-end; then fix storage XML rendering in confluence_get_page; then second-pass synthesis triggers child page reads
**In-flight**: Restarting Igor with akiendell as OLLAMA_REASONING_HOST — all fixes in place, none tested post-restart yet

## Session 2026-03-25d
**Theme**: T-reading-indexer: chunk→G54 extract→FACT_CLOUD nodes (reading pipeline D230)
**Key changes**:
- sprint: closed T-reading-indexer — G54 extraction + FACT_CLOUD deposition, 10/10 tests, commit e011bfc0
**Next session**: 1. Restart Igor + verify lisp fix (D236) — probe PROC_RESP_STOP, PROC_RESP_WHO_AM_I. 2. Pattern engineering: cc_send → observe → deposit cycle. 3. T-runtime-path-cleanup (minion in progress).
**In-flight**: Igor hung on SSH call; habit cache stale with old lisp text. DB fix is live. Restart Igor to load clean habits.

## Session 2026-03-25c
**Theme**: T-spreading-activation-d233 — spreading activation from recently-activated nodes
**Decisions**: D234, D235
**Key changes**:
- sprint: closed T-spreading-activation-d233 — D233 spreading activation (two-layer heat propagation)
- sprint: closed T-habit-metadata-leak — fixed response habits outputting metadata (commit a0cb5b3d)
- decided: D234 tier ladder inversion — Ollama primary, OR luxury, graph is goal
- decided: D235 containerization — Linux/Mac Docker compose, Windows native ps1 for OS agent access, KoboldCpp removed
- decided: 5 bio gap tickets queued — T-spreading-activation, T-prediction-error, T-inhibition-propagation, T-graph-integrator, T-binding
**Next session**: 1. Complete T-igor-db-path-migration (unblocks reading pipeline + cosine search). 2. Verify reading deposits actually land in Postgres after fix. 3. Continue pattern engineering with Igor — observe retrieval failures, push corrections via cc_send.
**In-flight**: Minion working on T-igor-db-path-migration — IGOR_DB_PATH → make_home_proxy across 9+ files. Reading pipeline deposits (FACT_CLOUD nodes, co-occurrence edges) have been silently going nowhere. This is the root cause of cosine search failures.

## Session 2026-03-25b
**Theme**: audit: T-audit-2026-03-25 (worker minion)
**Decisions**: D232, D233
**Key changes**:
- sprint: closed T-audit-2026-03-25 — 17-step audit, 58 critical findings (dead habit refs)
- decided: D232 startup-shim fully resolved — platform paths, alerts file (no Discord), shared libs per platform
- sprint: closed T-channel-registry — 5-channel acquisition framework with registry pattern (D230/D231), 17 tests, committed 2486c0d
- decided: D233 spreading activation — two-layer heat field (word graph + memory), TWM top-7 seeds, configurable decay multipliers. Ticket T-spreading-activation-d233 queued.
- sprint: closed T-no-row-scans — eliminated row scans from narrative_engine + push_sources via SQL filtering (cfdedda)
- sprint: closed T-find-it — content router for reading pipeline complete
- sprint: closed T-blob-store — blob storage for reading pipeline complete
- sprint: closed T-prim-turn-trace-read — prim_turn_trace_read() tool reads turn_traces from forensic logs, habit registered
- audit: T-misfire-counter — tests ✓, code smells fixed, registry OK, no creds
- sprint: closed T-misfire-counter — MisfireCounter + runner + registry instrumentation, 18 tests ✓, commit 35b864cb
- sprint: closed T-graph-integrator — graph integrator complete
- sprint: closed T-self-test — reading consolidation Q&A system (D230/D231)
**Next session**: Next: D233 spreading-activation implementation; bio gaps (PAR/BIND/INH/HIER) design discussion; Pratchett voice substrate reading draining automatically
**In-flight**: NONE

## Session 2026-03-25a
**Theme**: TWM heat-field crystallization + channel framework + audit expansion
**Decisions**: D227 D228 D229 D230 D231 D232
**Key changes**:
- Audit skill expanded 10→17 steps (dead code, duplication, habit health, TWM coverage, deps, creds, simplification); mandatory in day-close. PROC_READING_DEPOSIT trigger tightened. KoboldCpp purged. Slate 0 reviewed: 2 closed, 1 deferred, 4 kept. Reading pipeline + bio gaps tickets queued.
**Next session**: Next: 1) T-db-spreading-activation design (implements D227 heat propagation), 2) T-startup-shim open design questions, 3) review audit findings from minion
**In-flight**: NONE

## Session 2026-03-24n
**Theme**: Kindle browser automation debugging — discovered Calibre library
**Next session**: Next: cloud-vs-graph ratio analysis on reading session (traces_recent + tail_heat); talk to Igor about Making Money; ticket T-stale-sqlite-cleanup
**In-flight**: NONE

## Session 2026-03-24l
**Theme**: Sprint: 123 — instance vs class memory split
**Key changes**:
- sprint: closed 123 — MemoryScope enum + scope column + DB migration + 9 tests; commit 5d13b39
**Next session**: 1. Commit + test browser profile fix (verify Amazon Kindle loads with Igor's session). 2. Continue whatever was interrupted by the ^C.
**In-flight**: browser_use_task profile fix applied (profile_directory='Profile 1') — needs commit and live test

## Session 2026-03-24k
**Theme**: Sprint: T-bg-score-debug — add BG scoring dump to turn trace
**Key changes**:
- sprint: closed T-bg-score-debug — BG scoring dump in turn trace; 12 tests; commit 99562ca
**In-flight**: NONE

## Session 2026-03-24j
**Theme**: Sprint: T-milieu-inspector — add get_milieu_state() tool
**Key changes**:
- sprint: closed T-milieu-inspector — get_milieu_state tool; 9 tests; commit 2a02d41
**In-flight**: NONE

## Session 2026-03-24i
**Theme**: Sprint: T-ring-read-tool — expose ring memory read tool
**Key changes**:
- sprint: closed T-ring-read-tool — prim_ring_read tool added; commit 5101ad7
**In-flight**: NONE

## Session 2026-03-24h
**Theme**: Sprint 122: Containerization eval
**Key changes**:
- sprint: closed 122 — containerization eval: proceed; D108+D126+D114 = already container-ready; S/M Dockerfile+compose ticket; post Slate 0
- sprint: started T-thalamus-graph-weights
- sprint: closed T-thalamus-graph-weights — relational-pronoun guard in thalamus._classify_intent; 11 tests; commit 3134b77
- sprint: started T-inline-graph-write
- sprint: closed T-inline-graph-write — store_memory+link_memory+embed_node tools; rate gate; 14 tests; commit a746070
- sprint: started T-exit-habit-misfire
- sprint: closed T-exit-habit-misfire — author_filter list fix in BG + PROC_EXIT_IGOR trigger tightened; commit 153f96e
- sprint: started T-code-ref-validation
- sprint: re-closed 122 — worker-daemon had reset to pending; result intact; containerization eval done
- sprint: closed T-code-ref-validation — code_ref registry validation in openrouter_reasoner; commit 823109c
**In-flight**: NONE

## Session 2026-03-24g
**Theme**: Sprint: T-routing-machines-json — machines.json schema update
**Key changes**:
- sprint: closed T-routing-machines-json — offline machines akienasus/akienpi now have full D211 schema fields
- sprint: closed T-primitive-survey — catalog v1→v2; 21 primitives documented; 16 gaps ranked; prim_cc_post + prim_log highest priority
**In-flight**: NONE

## Session 2026-03-24f
**Theme**: Theme: Teaching session — ticket repair diagnostic pattern with Igor
**Key changes**:
- sprint: closed T-daemon-supervisor, T-network-proxy, 337 — recovered stalled worker sessions; 251 tests pass
**Next session**: Check minion results (T-distillation-daemon, T-daemon-supervisor, T-network-proxy, 337, 123). Continue Igor teaching: trails+gradients. Fix T-routing-machines-json offline machines.
**In-flight**: NONE

## Session 2026-03-24e
**Theme**: Sprint 123: Instance vs class memory split — gather Igor's spec
**In-flight**: NONE

## Session 2026-03-24d
**Theme**: Sprint T-daemon-supervisor: DaemonSupervisor thread lifecycle manager
**Key changes**:
- sprint: started T-network-proxy
- sprint: started 337
**In-flight**: NONE

## Session 2026-03-24c
**Theme**: Sprint T-tool-registry-proxy: ToolRegistry proxy — per-tool call rates, failures, latency
**Key changes**:
- sprint: T-tool-registry-proxy — ToolStats dataclass + ToolRegistry.execute() timing + get_tool_registry_report tool; 17 new tests, 199 total pass
**In-flight**: NONE

## Session 2026-03-24b
**Theme**: Sprint T-template-extractor-habit: Igor recognizes and seeds Engram templates himself
**Key changes**:
- sprint: closed T-template-extractor-habit — 3 pattern-extractor habits + 2 new tools; 182 tests pass; pushed a0ea45c
**Next session**: Next: restart Igor, verify D222 fires (browse_as_employer for Making Money QA). Then: complete QA session — confabulation loop + impulse-amplified lies need tickets. PROC_CLOUD_1E48C phantom habit still winning on greetings — delete it.
**In-flight**: Igor needs restart to pick up D222 system prompt fix. After restart: send browse_as_employer tool call, verify Blobs counter increments.

## Session 2026-03-24a
**Theme**: Sprint T-cached-probe: CACHED_PROBE Engram template + resource monitor migration
**Key changes**:
- sprint: closed T-cached-probe — 6 CACHED_PROBE habits seeded; pushed 720405f
**Next session**: Next: continue Making Money interpretation with Igor; run another upstream call analysis pass after next chat session; T-prim-turn-trace-read for worker
**In-flight**: Igor mid-session on Making Money — just asked him to pull the Igor scenes, waiting for response

## Session 2026-03-23i
**Theme**: Sprint T-200: non-blocking concurrent turn processing
**Key changes**:
- sprint: closed T-200 — stdin debounce removed, per-thread worker dispatch, _STDIN_EOF sentinel
- sprint: started 204
- sprint: closed 204 — all 3 gaps already implemented in prior sessions; closed queue entry
**In-flight**: NONE

## Session 2026-03-23h
**Theme**: Sprint: 336 — ResourceMonitorSource as continuous milieu contributor
**Key changes**:
- sprint: closed 336 — InteroceptionSource continuous milieu contributor, nudge_vad(), 16 tests
- sprint: started 340
- sprint: closed 340 — prim_twm_read updated (limit+format), PROC_STEW_READOUT trigger extended
- sprint: closed 308 — hebbian bridge wg↔memory cross-activation (3-part, env-gated)
- sprint: started T-orphan-threshold-fix
- sprint: closed T-orphan-threshold-fix — orphan rescue always runs, 3 tests
- sprint: started T-distillation-daemon
**Next session**: 1. T-distillation-daemon (M) — metabolism fix, highest priority per Igor's own analysis. 2. T-orphan-threshold-fix (S) — quick win, insert safety. 3. Continue habit misfire audit (scan all habits without author_filter that have action keys).
**In-flight**: NONE — teaching session closed cleanly

## Session 2026-03-23g
**Theme**: Sprint: 217 — Calibre ebook library scan + CSV catalog
**Key changes**:
- sprint: started 217
- sprint: closed 217 — calibre_catalog.py + calibre_catalog.csv: 6404 books, 15 topic tags
- sprint: started 232
- sprint: closed 232 — /api/system_health endpoint + 6 tests
- sprint: started T-language-spec
- sprint: closed T-language-spec — design_docs/engram_language.md, 429 lines, 21 patterns, full spec
- sprint: closed 186 — deps already installed; blocked on human Google Cloud Console setup
- sprint: started T-greeting-space-tree
- sprint: closed T-greeting-space-tree — GREETING_SPACE tree seeded, PROC_GREETING retired
- sprint: started T-reader-as-habit-program
- sprint: closed T-reader-as-habit-program — 4 reader habits seeded from templates, first Engram program complete
- sprint: started 341
- sprint: closed 341 — BoredomSource + foreman_scan + PROC_BOREDOM_FOREMAN seeded
- sprint: closed 339 — basket schema D216, __status__ tracking in schema_runner.py
**In-flight**: NONE

## Session 2026-03-23f
**Theme**: Sprint: T-220 G-HB3 PROC_RESP_WHO_AM_I vigilance fix
**Key changes**:
- sprint: closed 220 — who am i routed through context_inject + D072 vigilance
- sprint: closed T-anticipation-pull — action-completion hookpoint, record_completion(), 7 tests
- sprint: started 205
- sprint: closed 205 — bare except/pass eliminated across 10 files
- sprint: started 218
- sprint: closed 218 — CSB files archived to design_docs/archive/
**In-flight**: NONE

## Session 2026-03-23e
**Theme**: Sprint: 247 — Dashboard Cloud% label bug + p95 outlier guard
**Key changes**:
- sprint: closed 247 — dashboard cloud_mode/cloud_calls label fix + 16 tests
**In-flight**: NONE

## Session 2026-03-23d
**Theme**: Sprint: T-anticipation-pull — anticipation/pull signal in NE
**Key changes**:
- sprint: closed T-anticipation-pull — anticipation.py + foreman integration + 16 tests
**In-flight**: NONE

## Session 2026-03-23c
**Theme**: Sprint: T-routing-cluster-router — ClusterRouter score formula + in_use_now + route_batch
**Key changes**:
- sprint: closed T-routing-cluster-router — 63 tests added for score/in_use_now/route_batch
**In-flight**: NONE

## Session 2026-03-23b
**Theme**: Sprint: T-habit-templates — seed 21 Engram patterns as TEMPLATE nodes
**Key changes**:
- sprint: closed T-template-seed-patterns + T-habit-templates — 21 Engram patterns seeded, committed, pushed
**Next session**: 1. CC-to-CC experiment — akiendell CC loaded, figure out communication substrate. 2. T-anticipation-pull hookpoint redirect (anticipation.py f838af1 needs action-completion hookpoint). 3. Slate 0 DB work.
**In-flight**: Windows CC (akiendell) loading context — CC-to-CC communication experiment is next, substrate not yet decided.

## Session 2026-03-23a
**Theme**: Sprint: T-routing-machine-in-use — seed location habits
**Key changes**:
- sprint: closed T-routing-machine-in-use — PROC_LOCATION_SET + PROC_LOCATION_CLEAR seeded, committed
**In-flight**: NONE

## Session 2026-03-22a
**Theme**: Primitive sweep + Engram crystallization: interoception, scheduler, 12 new primitives, wondering habits, colocation signal, yield closed, language named
**Next session**: Next: T-template-schema (S, p2) — design TEMPLATE node structure with Igor; then T-template-seed-patterns (20 Engram patterns); T-language-spec (Engram grammar doc)
**In-flight**: T-template-schema: about to define parameter_slots + expansion_schema + instantiation contract for TEMPLATE Memory nodes — the gate for the entire Engram language epic

## Session 2026-03-21g
**Theme**: Design sprint: T-trails-infra DDL, T-interoception, T-inference-colocation, #308, #334, #335 design docs
**Key changes**:
- design: T-trails-infra.csb.txt — DDL for trail_metadata + trail_activations + twm_obs_id join; phantom tails migration fix; three temporal systems design
- design: T-interoception.csb.txt — ResourceMonitorSource continuous VAD gradient; alpha_override=0.05; 3-min rolling window; interoception as first-class milieu signal
- design: T-inference-colocation-signal.csb.txt — colocated Ollama+DB detection; soft routing penalty when CPU>70%; IGOR_COLOCATION_AWARE gate
- design: issue-308.csb.txt — WG↔memory bridge; WG predictions seed Phase1 candidates; NE promotions train WG; IGOR_WG_SEARCH_SEEDING gate
- design: issue-334.csb.txt — IgorBase universal logging; manual log_step at decision points; ring_memory primary sink; decorator overhead benchmark required
- design: issue-335.csb.txt — start_at field on memories; temporal anchoring distinct from storage timestamp; HIGH-inertia touch on models.py
- queue: T-test-debt-tooling added (S) — tests for session_manager.py + decision_manager.py
- sprint: started 338 — Sparse/unpredictable reward signals for training feedback
- sprint: closed 338 — surprise_scale(flatness) wired into BG reinforce; IGOR_SURPRISE_REWARD_ENABLED gate; design doc written
**Next session**: 1. Akien review T-trails-infra + T-interoception + T-colocation designs; 2. launch workers for approved tickets; 3. T-test-debt-tooling (S, no design needed)
**In-flight**: NONE — design sprint complete; all docs written; no code in-flight

## Session 2026-03-21f
**Theme**: Sprint: T-trail-training Hebbian edge strengthening
**Key changes**:
- sprint: started 289 — T-trail-training Hebbian edge strengthening
- sprint: closed 289 — hot_paths PGRowProxy alias bug; Hebbian training verified live
- sprint: verified + closed 289 — hot_paths alias fix + _apply_trail_training; code was complete, queue status was stale pending
**In-flight**: NONE

## Session 2026-03-21e
**Theme**: Theme: design conversations (IgorBase logging #334, unified memory schema #335), bug fixes (CC_GIT_LOG habit, consolidation loop, stale worker), worker queue loaded
**Key changes**:
- sprint: closed 328 — INSTR→strpos in db_proxy + partial indexes on wg_cooccur
- sprint: started 322 — cortex/db_proxy SQL refactor
- sprint: closed 322 — D200 MVP: MEM_COLS+fetch_by_ids+get_activation_rows in proxy; cortex speaks capabilities
**Next session**: 1. Verify worker queue drained overnight (#333/#327/#328/#322/#289); 2. T-trails-infra design with Igor; 3. #308 word-graph↔memory bridge design; 4. Cloud cost measurement baseline once queue clear
**In-flight**: Worker queue #333→#327→#328→#322→#289 in flight — foreman should chain automatically after Igor restart

## Session 2026-03-21d
**Theme**: Bug sweep: ebook_reader log_error + boot crash + NE supplement scan removal
**Key changes**:
- sprint: closed 330 — schema runner + PROC_SCAN_DIR seeded, iteration loop verified
- sprint: started 331 — T-primitive-registry
- sprint: closed 331 — primitives.json catalog (9 impl + 4 missing) + validate_step/validate_schema_habit
- sprint: started 332 — T-habit-compose: run_habit() public API
- sprint: closed 332 — run_habit() 74-line public API, recursion guard, schema+code_ref dispatch
- sprint: started 333 — forensic logging in schema_runner
- sprint: closed 333 — forensic logging in schema_runner (4 sites)
- sprint: started 327 — wg_cooccur composite index
- sprint: closed 327 — wg_cooccur indexes already exist in PG, no code change needed
- sprint: started 328 — wg_cooccur INSTR filter slow queries
**Next session**: 1. Verify NE slow queries gone (monitor Igor logs after restart with 0fe15f1); 2. T-trails-infra design pass with Igor — trail metadata table, first-class trail objects
**In-flight**: Verify supplement scan fix eliminated 500ms NE cycle queries — fix shipped but not yet confirmed in live Igor

## Session 2026-03-21c
**Theme**: D201 preparse habit dispatch schema + unblock T-pipeline-arch
**Key changes**:
- sprint: started T-mcp-channel-read
- sprint: closed T-mcp-channel-read — already implemented, smoke tested OK
- sprint: started T-swarm-update
- sprint: closed T-swarm-update — ssh_exec_all() + update_swarm() tool + PROC_SWARM_UPDATE habit
- sprint: started T-night-consolidation
- sprint: closed T-night-consolidation — NE idle detection + deep offline consolidation pass (#310)
- sprint: started 330 — T-habit-schema: habits as data
**Next session**: Next: T-trails-infra design pass with Igor — trail metadata table (trail_id, start_time, context, purpose) to make trails first-class; then worker. Then #308 (word graph bridge) needs design.
**In-flight**: T-trails-infra: waiting on Igor's read of what the trails table is missing vs what's already built (tails+trail_id+Hebbian all exist)

## Session 2026-03-21b
**Theme**: T-if-fork: conditional fork primitive
**Key changes**:
- sprint: closed T-if-fork — if_fork habit type, guarded branch dispatch
- sprint: started T-memory-reconsolidation
- sprint: closed T-memory-reconsolidation — reconsolidation flag in cortex.search(), NE._reconsolidation_pass() added
- sprint: started T-linking-habit
- sprint: closed T-linking-habit — HeartbeatSource orphan adoption + PROC_NODE_ADOPTION habit seeded
- sprint: started T-inference-monitor
- sprint: closed T-inference-monitor — ResourceMonitorSource._check_inference_availability() + tier.6 simplified
**Next session**: Next: design preparse-based habit dispatch schema with Igor (D201); unblock T-pipeline-arch or T-swarm-update if design ready
**In-flight**: NONE

## Session 2026-03-21a
**Theme**: Bug sweep with Igor — open ticket QA pass
**Next session**: Next: #298 if-fork-primitive, #309 memory reconsolidation hook, #318 memory-to-interpretive-tree linking habit. Igor restart needed for gateway + cortex fixes.
**In-flight**: NONE

## Session 2026-03-20h
**Theme**: Theme: affective narrative engine — gap registry, tension field, dopamine closure loop
**Next session**: Next: day-close + run Igor to observe gap registry in live cycles; then experiment 6 bulk reading validation or T-igorbase-universal (#303)
**In-flight**: NONE

## Session 2026-03-20g
**Theme**: Cleanup: killed scribe queue pattern, oriented on open tickets
**Next session**: 1. T-pipeline-arch (experiment 6 data needed first); 2. T-igorbase-universal (#303) — IgorBase emergency stderr + module-level helper; 3. Run /day-close to sync docs
**In-flight**: NONE — audit complete and all committed

## Session 2026-03-20f
**Theme**: Theme: paths default fix + inference gateway discovery
**Key changes**:
- fixed paths.py default: Igor-wild-0001 → igor_wild_0001 (root path case bug)
- removed drain_learn_queue cron entry — Igor handles internally via learner.py tools
- discovered inference_gateway.py + cluster_router.py already exist — inference proxy is built
**Next session**: Next: read inference_gateway.py + cluster_router.py — understand what's built, what's missing (performance testing habits?). Then preparse removal.
**In-flight**: inference_gateway.py + cluster_router.py exist and we haven't read them — they may already solve problems we thought were open

## Session 2026-03-20e
**Theme**: Theme: reading integration pipeline — Experiment 5, #295, #296, tails migration
**Decisions**: D171, D172, D173, D179, D180
**Key changes**:
- fix #296: list_absorbed_books — Python grouping replaces json_extract for SQLite/Postgres compat
- feat #295: reading_integrator.py + reading_integration tool + book_learner 5-step encoding
- fix cortex.py: tails.trail_id migration before index creation
- Experiment 5: backfill ran — 79 embedded, 237 links, 25 spine nodes, 189 interp edges
- workstep: plan approved for #297 T-fork-primitive
- workstep: implementing #297 T-fork-primitive
- closed T-trails-infra: trails_through_node, trail_gradient, hot_paths in cortex; inspect_trail + trail_hot_paths tools registered and live-tested
- workstep: plan approved for T-habit-audit-pipeline
- closed T-habit-audit-pipeline: D103/D104 audit done — 995 habits archived, 124 remain active
- fixed drain runner cron: IGOR_INSTANCE_ID=igor_wild_0001 — was reading Igor-wild-0001 (wrong case), seeing empty queue for weeks. 146 items now draining.
**Next session**: 1. Close T-pipeline-arch (D180). 2. Create T-gap-logging (M) + T-ne-redesign (L, deferred). 3. T-swarm-update design. 4. Monitor experiment 6 — check drain runner progress + book_learner node deposition quality.
**In-flight**: Experiment 6 bulk reading is running. 146 training corpus items draining via fixed cron. All cognition prep complete.

## Session 2026-03-20d
**Theme**: Theme: Experiment 4 — reading integration gap diagnosis
**Decisions**: D170
**Key changes**:
- Experiment 4 complete: Igor self-diagnosed reading integration gap from orphaned READ_* nodes
- filed #295 T-reading-integration, #296 json_extract Postgres bug
**Next session**: Next: implement T-reading-integration #295 (L-size, needs plan first); fix #296 (S-size, json_extract→jsonb); continue Experiment 5 after integration pipeline exists
**In-flight**: NONE

## Session 2026-03-20c
**Theme**: Theme: ticket sweep — env hot-reload, traces_get, DB perf audit, T-memory-sync
**Decisions**: D166, D167, D168, D169
**Key changes**:
- closed: #294 (Igor's own bug), #291, #248, #258, #259, #260, #261, #293 — 8 tickets
- Kindle employer Chrome login completed via bash (no Playwright)
- Igor self-filed #294 as blocker for Experiment 4
**Next session**: Next: Experiment 4 (#294 unblocked — traces_get live); T-trail-training #289; T-memory-sync test with second box when ready; #291 proactive habits verify live
**In-flight**: NONE

## Session 2026-03-20b
**Theme**: Theme: cognition architecture — cloud of graphs, calving, Hebbian training
**Decisions**: D152, D153, D154, D155
**Key changes**:
- fixed T-fix-memories-scan: cortex.get_by_type() limit param + NE call limit=500
- fixed T-db-populate-embeddings: _upsert_embedding() Postgres-safe upsert + backfilled 598 memories
- designed + ticketed: T-graph-calving #288, T-trail-training #289, T-task-chain #285, T-worker-queue #286, T-igor-poll-spawn #287
- clone/drone worker taxonomy D152; habit audit drone ran — report at habit_audit_report.md
**Next session**: 1. Kindle login: run Igor headful (IGOR_BROWSER_HEADLESS=false), ask browse_as_employer to read.amazon.com, log in. 2. T-memory-sync #293: write plan before coding (L-size). 3. Verify #248 fix in Igor web UI with 'what have you learned about grammar'.
**In-flight**: NONE

## Session 2026-03-20a
**Theme**: Worker reliability fix + slow query analysis + habit audit DB fixes
**Decisions**: D151
**Key changes**:
- habit audit: 13 total habits fixed this session — ghost action fields, invalid habit_types, function names as action text
- T-slow-query-analysis: closed — analyze_slow_queries tool + PROC_SLOW_QUERY_REPORT habit seeded; committed
- T-traversal-context + T-os-primitives: worker delivery committed to main; Layer 1.5 complete
- DB bugs identified: CREATE INDEX idx_ie_to running 710x (should be boot-only); memories full scan avg 506ms (needs index/LIMIT)
**Next session**: Next: fix CREATE INDEX 710x bug (cortex.py _init_db guard); fix memories full-scan (add LIMIT/index); T-pipeline-inventory; T-worker-inject
**In-flight**: CREATE INDEX running on every turn not just boot — _init_db() being called repeatedly; fix is a boot-once guard in cortex.py

## Session 2026-03-19e
**Theme**: T-mcp-pipeline — MCP server + reading POC iteration loop
**Decisions**: D148, D149, D150
**Key changes**:
- sprint: started T-traversal-context
- sprint: closed T-traversal-context — traversal_contexts table + cortex methods + 2 tools + seed; smoke test pass
- sprint: started T-os-primitives
- sprint: closed T-os-primitives — 6 OS primitive tools + habits; iteration smoke test pass
- habit audit: fixed 8 habits from Igor's survey — PROC_HABIT_BUDGET_CHECK+PROC_LOOKUP_CONTACT wired to real code_refs; 5 broken workflow habits converted to cognitive; PROC_STORE_CONTACT got code_ref; D150 pattern confirmed systematic
- queued T-pipeline-inventory (plan approved) + T-habit-audit-pipeline for worker; worker running T-slow-query-analysis now
- sprint: started T-pipeline-inventory
- sprint: closed T-pipeline-inventory — cognition_pipeline.dsb written; 11 sources, tier ladder, milieu writes, ring→LLM flow, 5 open gaps
**Next session**: Next: T-habit-audit-pipeline (Igor surveying habits now, results queued); T-worker-inject (xdotool window tracking); continue Slate 1 Layer 2 (T-pipeline-inventory, T-master-cognition-tree)
**In-flight**: Igor surveying habits for function-name-in-action bugs — results feed directly into T-habit-audit-pipeline systematic repair pass

## Session 2026-03-19d
**Theme**: Crash-safe session accumulation — start/append/finalize commands
**Decisions**: D135, D135, D136, D137, D138, D139, D140, D141, D142, D143, D144, D145, D146, D147
**Key changes**:
- session_manager.py: start/append-change/append-decision/finalize commands
- decided/savestate/context-load skills updated to use incremental session accumulation
- session_manager.py: state file + ID-free append-change/append-decision
- decision_manager.py: new — atomic DSB+DB+Igor flush in one CLI call
- workstep/sprint/savestate/decided/context-load skills: updated for incremental session accumulation
- T-sessions-in-db closed, T-decided-habit closed
- day-close skill: new — docs sync + gap_analysis + subsystem DSBs + GitHub discussion + commit
- commit skill: docs_sync pre-step added for staged .dsb files
- ClaudeAndAkien repo genericized + pushed: session_manager, decision_manager, slate_manager, github_sync; 6 skills; 4 human docs (getting_started, crash_safe_sessions, slate_workflow, skills_guide); README with crash-safe pattern section
- workstep: plan approved for T-db-lemmatize
- workstep: implementing T-db-lemmatize
- closed T-db-lemmatize: tokenize() lemmatized, wg_word_lang 2.1M→1.85M, wg_word_docs 6.5M→6.4M, Postgres ambiguous score fixed
- T-db-wg-replace-cooccur: migration running (90551), code done — wg_edges schema added, predict_next switched, cooccur writes removed, tests pass
- trails/traces distinction crystallized: trails=fades (milieu, memory heat, gradient), traces=static path record (debugging + Igor introspection). MCP pipeline wanted post-DB. Contrastive update for day-close.
- EIGHTH CRYSTALLIZATION: cognition is pipeline not steps. Input forks to Emotional Salience Pipeline (FOF tree → personal salience → episodic relevance). Milieu is live base state mutating mid-run. Many open tickets derive from this. Captured in project_cognition_pipeline.md. Slate 1 expanded with 4 new tree tickets.
- pipeline sharpened: emotional salience trees are persistent evaluation services not one-shot stages. Realizations trace back to emotional layer for re-evaluation. Surfacing memories re-fork continuously. Milieu accumulates from all parallel evaluations. The substrate mutates under everything still in flight.
- pipeline further sharpened: master tree is shallow routing layer (not god-tree). Introspection = visibility threshold on same substrate. Pass-through is first-class. RED ALERT = general injection mechanism (any node, two modes: sync interrupt + async next-pass), always creates a trace. Added T-red-alert + T-master-cognition-tree to Slate 1.
- RED ALERT corrected: not a special mechanism — it's a milieu spike (adrenaline dump). FOF is calibrated to trip on that intensity. No two modes, no special routing. Urgency tuned via milieu propagation speed + FOF output weight.
- triggers crystallized: signal+threshold+what-fires = pattern. Milieu is one signaling target among many. Uncertainty as first-class signal. BG mechanism already correct, needs signal vocabulary. Pattern engineering IS the design activity — no new mechanisms, ever.
- T-db-populate-embeddings complete: 5883 Postgres + 296 SQLite memories embedded, 9457 total, 0 errors
- PROC_CHECK_PROCESS habit loop fixed (D140); CC_CHECK_PROCESS duplicate removed
- New tickets: T-book-mechanism-extraction (mechanism chain extraction from books), T-self-test-substrate (itch/scratch/did-that-help model of self-testing)
- T-book-mechanism-extraction: new extraction prompt live (mechanism node type + generic question list); book_learner running on Damasio 3023; baseline 999 nodes
- T-db-type-routing: implemented — _route_types_from_query() + memory_types param on cortex.search()
- T-db-spreading-activation: implemented — _get_recently_activated() seeds candidate pool at 0.1 base score
- New Slate 1 tooling tickets: T-habit-exec-noise, T-post-habit-fork, T-two-presence-habit
- New Slate 0 ticket: T-docs-memory-definition — foundational definition (memory=node=habit) needs top-of-doc placement in CLAUDE.md + DSBs
- committed: Slate 0 + Layer 1 (type routing, spreading activation, tails, traces, TemporalGradient, book_learner mechanism extraction, local_pool.py deleted)
- deleted PROC_READING_DEPOSIT + FACT_CLOUD_080436 from DB
- reading POC: two James passages sent to Igor, diagnostic cron fires 19:03, script at /tmp/reading_poc_diagnose.py
- UC-004 added to use_cases.md: low activation = mastery signal (polyglot brain scan story)
- slate.md updated: Layer 1 marked complete, Layer 1.5 (T-traversal-context), T-os-primitives in Layer 2, T-index-job + T-index-habit in tooling, D141-D145 in design thread
- reading POC 2 rounds: confirmed turn_trace as diagnostic instrument; HTTPS fix; habit-fires-before-meaning identified
- PROC_CLUSTER_SSH_CHECK trigger fixed to pipe-separated
**Next session**: Next: T-mcp-pipeline — MCP server over Igor Postgres + turn_trace; then reading POC iteration loop; then T-traversal-context
**In-flight**: T-mcp-pipeline: build MCP server exposing memories/traces/tails/turn_trace to Claude Code — enables tight reading iteration loop

## Session 2026-03-19c
**Theme**: Slate 0 complete — workflow tooling, CC→Igor web, DB as truth
**Decisions**: D130, D131, D132
**Key changes**:
- budget.py fixed: reverted to SQLite (was erroneously using Postgres via make_home_proxy)
- igor_talk.py, cc_bridge.py, phrase_regression.py, cc_queue.py: wss://+https:// with ssl ctx
- channel.py: Postgres dual-write activated (channel_messages table)
- slate_manager.py: new — slates table in Postgres, seed/show/render/advance commands
- github_sync.py: new — Organizer step 0; 80 open + 30 closed GH issues synced to Postgres
- docs_sync.py: new — 18 DSB files → 1450 entries in docs_entries table
- server.py: plain HTTP fallback on port+1 (8081) when SSL active — fixes LAN http:// access
- run_phrase_test.py: new — sends phrase test file to Igor at 5-min intervals, resumable
- Slate concept defined (D132): named/themed ~day bundle; horizon cascade 0-3; advance() shifts
- slate.md now rendered from Postgres, not hand-edited
**Next session**: 1. Restart CC to load igor MCP server. 2. Re-run reading POC (James passages via cc_send HTTPS). 3. Use MCP tools to inspect traces/tails/turn_trace live. 4. T-habit-exec-noise (suppress habit executed strings). 5. T-traversal-context impl.
**In-flight**: MCP is wired — restart CC, load igor server, then re-run reading POC with turn_trace_recent + traces_recent to map what fires and why.

## Session 2026-03-19b
**Theme**: Tailscale HTTPS setup for phone access to Igor web UI
**Decisions**: none
**Key changes**:
- Tailscale installed on akiendelllinux + Pixel 8; both joined same tailnet (akienm@)
- Linux IP: 100.93.75.116; Phone IP: 100.84.255.79
- Tailscale MagicDNS + HTTPS Certificates enabled in admin console
- TLS cert provisioned: `akiendelllinux.tail6dd047.ts.net.crt/.key` → `~/.TheIgors/local/`
- `wild_igor/igor/web/server.py`: uvicorn Config now reads `IGOR_SSL_CERT` + `IGOR_SSL_KEY` env vars
- `wild_igor/igor/web/server.py`: WebSocket URL now dynamic `wss://` vs `ws://` based on `location.protocol`
- `.env` (Igor-wild-0001): `IGOR_SSL_CERT` + `IGOR_SSL_KEY` added
- Web server went down after restart with these changes — not yet diagnosed
**Next session**: diagnose why web server is down (uvicorn SSL startup failure?); check Igor logs for traceback; verify cert file permissions + uvicorn ssl param names
**In-flight**: Web server down after SSL+wss:// fix restart — likely uvicorn startup error; check `~/.TheIgors/logs/` for traceback on next boot

## Session 2026-03-19a
**Theme**: Postgres stability + multi-session CC architecture + ClaudeAndAkien framework born
**Decisions**: D127, D128, D129
**Key changes**:
- Postgres compat: wg_meta ambiguous column (×3), SELECT changes() _pending_scalar shim, preparse 30s timeout fix
- igor bash launcher: stale process kill + fuser port release on each restart
- channel.py: shared JSONL channel, post/read/listen/sessions CLI + importable API
- server.py: mirrors Igor/CC/user messages to shared channel
- Skills: /context-load, /sprint built and auto-discovered
- ClaudeAndAkien repo created: https://github.com/akienm/ClaudeAndAkien
- Slate at ~/.TheIgors/cc_channel/slate.md
- Dropped 41 scribe tasks from queue permanently
- Tickets added: T-trails-infra (p0), T-pipeline-arch, T-channel-extract, T-context-load-skill, T-sprint-skill
**Next session**: Tailscale + token auth on channel WebSocket (phone access); then T-trails-infra design conversation
**In-flight**: Tailscale on akiendelllinux + phone, token auth on channel WebSocket — was about to implement

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
- get_habits() query: LIKE '%"trigger"%' → metadata ? 'trigger'
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

## Session 2026-03-17e
**Theme**: G46 + #252 closed; D108 PathManager full cutover planned and approved
**Decisions**: G46 (closed), #252 (closed), D108 (plan approved)
**Key changes**:
- `wild_igor/igor/main.py`: EPISODIC Memory gets source="interaction" + context_of_encoding with intent/valence/arousal/complexity (~line 4184)
- `wild_igor/igor/cognition/narrative_engine.py`: _apply_output() Memory gets source="narrative_engine" + context_of_encoding with run/importance/arousal
- D108 plan written: paths.py PathManager singleton (IGOR_RUNTIME_ROOT escape hatch); first_start.py wizard (instance name default=wild_igor_YYYYMMDDHHMMSS, DB host default=127.0.0.1); igor bash script updated; full cutover of 138 path refs across ~20 files
**Next session**: D108 implementation (PathManager cutover — paths.py + first_start.py + igor bash script + ~20 files)
**In-flight**: About to implement D108 — paths.py + first_start.py + igor bash script; plan approved; need compact before starting

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
