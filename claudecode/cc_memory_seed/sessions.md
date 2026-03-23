# TheIgors — Session Notes (detailed)

Older pre-2026-03-05 session history is in `history.md`.

---

## Session 2026-03-18a
**Theme**: Windows `igor` command live; D119 env_sync complete; D120 cluster router approved
**Decisions**: D120 (cluster-aware inference router)
**Key changes**:
- D119 env_sync.py live: 48 SYSCFG nodes in Postgres; Windows hydrates model vars from DB on boot
- igor_loop.ps1 + igor.bat: type `igor` on Windows; git pull + exit-code-42 loop; mirrors Linux wrapper
- sign_igor_script.ps1 updated to sign both igor_loop.ps1 + start_igor_windows.ps1
- exit_self() + exit.flag + PROC_EXIT_IGOR: clean shutdown habit (code 0 = no restart)
- seed_training_corpus.py: 165 corpus files queued as file:// entries; drain runner processing
- Root cause confirmed: Ollama (qwen2.5:7b) is the CPU load source; DB contention was secondary
**Next session**: cluster_router.py implementation (D120) + DB perf round + audit findings
**In-flight**: D120 cluster_router.py — about to implement; scores machines by load + time + override; routes NE/winnow/preparse/tier.2/extraction to best available target

---

## Session 2026-03-17e
**Theme**: Priority queue sprint — G-DB1, G-NE1, G37p2 closed; G46 in-flight
**Decisions**: none new (executing pre-approved queue)
**Key changes**:
- G-DB1 closed: learner.py raw sqlite3.connect → DatabaseProxy singleton
- G-NE1 closed: NE _consolidation_merge_pass() + _merge_cluster() — episodic-to-semantic merge
- G37p2 closed: IGOR_DUAL_WORD_GRAPHS + IGOR_NPASS_REPLY + IGOR_COMPREHENSION_SIGNAL defaulted true
- G46 in-flight: source + context_of_encoding population in main.py + NE _apply_output()
**Next session**: finish G46, then #251/#252 (friction reducer + organizer)
**In-flight**: G46 — set source="interaction"+context_of_encoding in main.py episodic creation; source="narrative_engine" in NE _apply_output()

---

## Session 2026-03-17d
**Theme**: Pre-implementation checkpoint — D092/G-DB1 W1 scoped and approved
**Decisions**: none new (executing pre-approved D092)
**Key changes**:
- Confirmed G-DB1 W1 scope: learner.py only (list_absorbed_books + _rl_db + 3 callers)
- Calibre DB (_calibre_db in ebook_reader.py) intentionally exempt — external 3rd-party DB
- ebook_drm/ intentionally exempt — external DRM DBs
**Next session**: implement W1, close G-DB1, then G-NE1
**In-flight**: Replace raw sqlite3.connect in learner.py with DatabaseProxy singleton — single file, Size S, approved

---

## Session 2026-03-17c
**Theme**: Habit repair round 1 + full priority queue established + 3 new epics filed
**Decisions**: D107 (implemented), D108, D109, D110
**Key changes**:
- `wild_igor/igor/tools/ebook_reader.py`: D107 implemented — `start_foreground_reading()`, `stop_foreground_reading()`, `_fg_reading_loop()`, `_stop_reading_flag`; chapter-boundary soft prompt; graceful fail if web server unavailable
- `claudecode/seed_foreground_reading_habits.py`: PROC_READ_NOW, PROC_STOP_READING, PROC_QUEUE_FOR_INGEST seeded into live DB
- `wild_igor/igor/main.py`: background job message → `_igor_lisp("Thinking about that...")` on web channel (needs restart); PROC_THINKING_ACK design note captured for after Windows round
- D108 (#275): Windows epic — PathManager cross-platform object + first-start "Database (current 127.0.0.1)?:" wizard
- D109 (#276): Multi-attention-center reading — main Igor delegates reading to remote instances; spread reading across machines; ebook_reader → internal habits
- D110 (#277): Project self-model + log-to-DB — traversable project graph; logs in DB; PROC_CC_CONTEXT_SEED for Claude startup
- Priority queue established (D092→G-NE1→G37P2→G46→#251/252→Windows→D109→D110)
**Next session**: D092 / G-DB1 — db_proxy universal gateway (was in-progress, T-d092-proxy-w1w2)
**In-flight**: NONE

## Session 2026-03-17b
**Theme**: D105 claude-bridge implemented + foreground reading habit repair planned
**Decisions**: D105 (implemented), D107 (planned)
**Key changes**:
- `claudecode/claude_bridge.py`: Starlette :8082, Anthropic SDK, shared+back channels, auto-compact at 40 msgs, seeds CLAUDE.md+habits+gap_analysis+BG logs, history persisted; bridge live
- `wild_igor/igor/web/server.py`: POST /api/bridge_chat proxy + CC toggle + bridge pane + back-channel textarea; sendMsg() forwards to bridge on shared channel; Claude replies forwarded to Igor via cc_send
- `claudecode/seed_cc_bridge_habit.py`: PROC_CC_JOIN seeded into DB
- @reboot cron entry for bridge added
- D107 plan approved: PROC_READ_NOW + PROC_STOP_READING + PROC_QUEUE_FOR_INGESTION + start_foreground_reading() loop in ebook_reader.py; "one moment please" interrupt-ack pattern established
**Next session**: Implement D107 foreground reading habits. Then review rest of habit repair slate.
**In-flight**: D107 plan approved. start_foreground_reading() + PROC_READ_NOW + PROC_STOP_READING + PROC_QUEUE_FOR_INGESTION. Compact and go.

## Session 2026-03-17a
**Theme**: Learn queue loading + drain bug fix + Claude bridge design (habit repair)
**Decisions**: D105, D106
**Key changes**:
- `learn_queue.json`: 97 new titles queued (programming ×25, AI/ML ×40, neuroscience ×35) — 40 completed overnight before stall
- `drain_learn_queue.py`: fixed 3 bugs — (1) no self-dedup at startup (cron spawned 25 instances), (2) no hung book_learner timeout (2 processes stuck 4h+), (3) pgrep-based counting replaced with psutil; added `_another_drain_running()`, `_reap_hung_learners(45min)`, psutil `_count_running_learners()`
- D105: Claude bridge design approved — `claudecode/claude_bridge.py` on 8082, persistent Anthropic SDK session, shared+back channel, seeds habits+logs+gaps on startup, survives Igor restarts
- D106: "habit repair" adopted as term for surgical habit work (Igor's suggestion); "habit calibration" = broader practice
- New term established: next phase = **habit repair** — examining existing habits for misfires, miscalibrated triggers, missing coverage
**Next session**: Implement D105 — `claude_bridge.py` + web UI dual-pane + `PROC_CC_JOIN` habit + cron entry. Then begin habit repair work using the shared channel.
**In-flight**: Claude bridge plan approved, no code written. Open straight to implementation.

## Session 2026-03-15c
**Theme**: Designer/Worker CC channel infrastructure + docx processing
**Closed**: (none) **Decisions**: D076
**Key changes**:
- `claudecode/WORKER_CONTEXT.md`: Worker boot doc — role, task protocol, constraints, project context
- `claudecode/cc_queue.py`: queue manager CLI (list/claim/done/block/log/add); queue at `~/.TheIgors/cc_channel/queue.json`
- 8 tasks queued for Worker: T001-T004 (CLAUDE.md + skill improvements), T005-T008 (GitHub tickets)
- Closed GitHub issues #222-#226 (all G-OVN-1/2/3/4/5 fixes from overnight session)
- Processed design docx `20260315.0826.claude_session_summary.docx`: 7 topics → tasks, corrected inhibitory pass framing to "at-least-two-pass / graph settling"
- phrase_regression.py at ~4/102 phrases when session ended
**Next session**: Check Worker task results (T001-T008); review phrase regression output; check context_inject introspective quality in logs

## Session 2026-03-15b
**Theme**: All 6 overnight fixes unattended: G-OVN-1/2/4/5 + G-HB3 + G-QP2
**Closed**: G-OVN-1, G-OVN-2, G-OVN-4, G-OVN-5, G-HB3, G-QP2; decisions D074, D075
**Key changes**:
- `basal_ganglia.py`: intent gate D074 — threshold/workflow/delegation/reactive habits gated on question intents; prevents calendar/swap/SSH misfires on question vocabulary
- `main.py`: context_inject handler D075 — WHO_AM_I habit falls through to LLM with SELF_CONTEXT in TWM; replaces canned response with real introspective LLM answer
- `cortex.py`: search LIMIT 300 ORDER BY activation_count DESC + `PRAGMA wal_checkpoint(TRUNCATE)` at boot (G-QP2)
- `drain_learn_queue.py`: MAX_CONCURRENT=2 cap via `pgrep -fc book_learner.py` (G-OVN-4)
- `learner.py`: CC bridge prefix stripping in `_extract_topic()` — strips `[Thread context:...]` + `[xxx]: ` patterns (G-OVN-5)
- DB: PROC_RESP_WHO_AM_I → `context_inject` type; pipe-separated trigger fixed min-token issue; PROC_CALENDAR_CREATE + PROC_RESP_CLARIFY triggers tightened
- Igor rebooted 08:08:26 2026-03-15; memories=8479 habits=101
- `phrase_regression.py` running: PID 357138, 113 phrases, 1 pass, 5-min delay
**Next session**: Review phrase regression results; confirm #222-#226 GitHub issues closed; check introspective response quality in logs

## Session 2026-03-15a — overnight analysis + full workstep day
**Theme**: Deep dive on overnight logs; 5 new gaps found; full unattended workstep planned
**Closed**: (none yet — workstep in progress)
**New gaps**: G-OVN-1 (#222 wrong habits), G-OVN-2 (#223 twm_push kwarg), G-OVN-3 (#224 drain cron path), G-OVN-4 (#225 book_learner local 404), G-OVN-5 (#226 learner CC prefix)
**Key findings**:
- Regression test: 10/13 phrases hit wrong habits; LLM responses good when reached
- reading→TWM pipeline dead: content= vs content_csb= (799 errors)
- drain cron broken since setup: relative path resolves wrong
- book_learner --local + 8 concurrent = 0 nodes from 400+ chunks (Ollama 404)
- Memory grew 8,061→8,460; 154 quality nodes from Wikipedia: language
- phrase_regression.py created (claudecode/); first 13-phrase run done; 100 phrases added to test file
**Next session**: Akien reviews 0930-1300; workstep in progress unattended

## Session 2026-03-14n — G-QP2 log crawl + crons + DSB format decision
**Theme**: DB growth slow query analysis, system crons wired, DSB issue format agreed
**Closed**: (none)
**New gaps**: G-QP2 (DB 8132 rows; NE scan p50=628ms; issue #221)
**Key changes**:
- Log crawl: 130 samples of activation scan; p50=628ms p99=1100ms; root cause = SELECT * on 8125 rows
- System crons live: drain_learn_queue */30 + CC nudge every 4h
- DSB format: issues = English header + DSB body; #62 discussion = full DSB going forward
- Gmail password updated in .env (untested — verify tomorrow)
**Next session**:
1. G-QP2: LIMIT on NE activation query + wal_checkpoint at boot (cortex.py, narrative_engine.py)
2. Verify gmail auth works with new password
3. G-HB3: PROC_RESP_WHO_AM_I context-injection habit

## Session 2026-03-14m — test cases + G-HB3 + cron planning
**Theme**: Response quality regression file, G-HB3 surfaced, drain_learn_queue cron plan
**Closed**: (none)
**New gaps**: G-HB3 (introspective habits bypass D072; issue #220)
**Key changes**:
- design_docs/response_quality_cases.md created: 6 manual regression cases (TC-1 through TC-6)
- TC-3: "what are you inside right now" — G-HB3 PROC_RESP_WHO_AM_I canned response
- TC-6: "tell me about the igors" — first-person interiority vs documentation recitation
- gap_analysis.md/dsb: G-HB3 added as open
- Naming: "ingest" proposed as unified term; slow_read vs bulk_load for RL1
- drain_learn_queue.py system cron check + CC-bridge nudge cron — confirmed by Akien, set up this session
**Next session**:
1. G-HB3: convert PROC_RESP_WHO_AM_I to context-injection habit (TC-3/TC-6 as regression)
2. Verify drain_learn_queue system cron is running; verify CC-bridge nudge cron active
3. G-RL1: slow_read vs bulk_load process split; "ingest" naming consolidation

## Session 2026-03-14l — G-MP1/G-HB2/G-RL3 implementation
**Theme**: Implement workstep: D072 vigilance gate live, G-HB2 root cause confirmed, G-RL3 reading_list status tracking
**Closed**: G-MP1, G-HB2, G-RL3
**Key changes**:
- word_graph.py: predict_next_with_flatness() added (convenience wrapper)
- main.py: D072 generation graph vigilance in _build_think_context(); [REFLEXIVE_PATTERN] when flatness<0.35; [GRAPH_UNCERTAIN] when >0.85; gate=IGOR_NPASS_REPLY=true (added to .env)
- G-HB2 root cause: pre-D066 substring matching ("hi" in "relationship"); D066 already fixed it; all misfires confirmed pre-D066; no new code
- drain_learn_queue.py: _set_reading_list_in_progress(calibre_id) on Popen launch
- book_learner.py: status='completed'+completed_at on full book completion
**Next session**:
1. Live test: send a message after Igor restarts with IGOR_NPASS_REPLY=true; check forensic log for [D072] gen_flatness entries
2. G-RL1: reading list dual-awareness (parallel read+extract threads)
3. Continue building reading pipeline toward books_realtime milestone

## Session 2026-03-14k — G-QP1 closed + G-MP1/D072/D073 architecture design
**Theme**: NE query index fix + major architecture design: graph-first response, vigilance gate, graph-exhaustion escalation
**Closed**: G-QP1
**Decisions**: D072 (graph-first response vigilance), D073 (LLM escalation = graph exhaustion)
**Key changes**:
- cortex.py: idx_activation ON memories(activation_count DESC); applied live; sort eliminated
- G-MP1 fully designed: predict_next() + gradient_flatness() injected into _build_think_context() as [REFLEXIVE_PATTERN]; no extra LLM call; inhibition before output (biology-correct); gate=IGOR_NPASS_REPLY
- D072: TWM IS the NE activation state (not two things). Global Workspace Theory + ART vigilance + attractor dynamics. fast-settle = reflexive = inhibit+re-traverse; never-converges = genuinely stumped = escalate
- D073: LLM escalation = graph exhaustion. "Honestly looked everywhere and I'm stumped." flatness never converges → escalate. Not a canned fallback. "The program is the data."
- Priority order confirmed: (1) enable IGOR_DUAL_WORD_GRAPHS + seed, (2) G-MP1 implement, (3) G-HB2, (4) G-RL3
**Next session**:
1. Enable IGOR_DUAL_WORD_GRAPHS + run seed_generation_graph.py — need reply data before flatness is meaningful
2. G-MP1 implementation: predict_next_with_flatness() in word_graph.py + _build_think_context() in main.py
3. G-HB2: live DB query for habits matching "log"/"ticket"

## Session 2026-03-14j — G-SP1 + G-CK1: self-edit episodic memory + cloud_ok runtime switch
**Theme**: Self-edit awareness (episodic memory on every edit) + runtime-switchable cloud/local mode for autonomous learning
**Closed**: G-SP1, G-CK1, G-HB1
**Key changes**:
- self_edit.py: `_push_edit_episodic()` + `_get_self_edit_cortex()` — every successful self-edit creates EPISODIC memory (portable=False, source=self_edit); `_try_hot_reload()` always calls it
- cloud_mode.py: `is_cloud_ok_override()` / `set_cloud_ok_override(ttl_hours)` / `clear_cloud_ok_override()` — file-based TTL gate at `~/.TheIgors/cloud_ok_override.json`
- inference_gateway.py: `cloud_ok_override` field in `InferenceContext` + `make_context()`; `_cloud_ok()` + `_cloud_preferred()` gate background calls when False
- book_learner.py: `_should_use_local()` per-chunk dynamic check — mode can change mid-book without restart
- drain_learn_queue.py: `_is_cloud_ok_override()` belt-and-suspenders; `--local` only if entry cloud_ok=False AND no override
- learner.py: `cloud_ok` field in queue items; "now" writes override (4h TTL), "tonight" clears it
- filesystem.py: `night_mode` (1 if 22:00-07:00) added to `_resource_load_dict()`
- Habits seeded: PROC_SET_CLOUD_NOW (pipe triggers "do it now|go now|...") + PROC_NIGHT_READ (threshold night_mode>=1)
- PROC_RESOURCE_AWARENESS: "memory" removed from trigger in live DB (G-HB1 fixed)
- New gap G-HB2: "log a ticket" → PROC_GREETING misfire — unknown routing path, needs live DB investigation
**Next session**:
1. G-HB2: query live DB for habits matching "log" / "ticket" — find the misfire source
2. G-RL3 remaining: reading_list status updates (in_progress/completed) from drain runner
3. Revisit open gap list — Akien wants to review what's next

## Session 2026-03-14i — G74 partial fix; learn queue cleanup; sympathetic/autonomic reading modes; plan for G-SP1+G-RL3
**Theme**: TopicExpander direct-URL channel; silent exception audit (all clean); designed tonight/now reading modes
**Closed**: (none — G74 partial, plan approved for G-SP1+G-RL3)
**Key changes**:
- learner.py: _discover_urls_direct() (arXiv/Wikipedia/Gutenberg always-works channel); better _DISCOVERY_PROMPT; markdown URL parsing; wired into learn_about()
- Learn queue: 10 corrupt entries removed, 9 linguistics URLs added, drain runner started
- #205 MEDIUM silent exception audit: all 51 handlers reviewed, all intentional, no fixes needed
- D069: reading-mode-sympathetic-autonomic — cloud_ok field; tonight=background/local; now=foreground/cloud-OK
- D070: G-SP1 pattern — episodic memory push + direct reload_module() call after self_edit
- #219 created for G-RL3 (PROC_NIGHT_READ + tonight/now modes)
- Plan approved: G-SP1 (self_edit.py: push EPISODIC + reload) + G-RL3 (cloud_ok field + PROC_NIGHT_READ habit seed)
**Next session**:
1. G-SP1: self_edit.py — push EPISODIC memory of edit then call reload_module()
2. G-RL3: learner.py cloud_ok field + "tonight"/"now" parsing + PROC_NIGHT_READ seed script
3. G46: Memory model migration (last, with Igor stopped)

## Session 2026-03-14h — Habit trigger precision; routing directive isolation; G-BRW1 G-BRW5 closed
**Theme**: Fix CC bridge habit misfires — PROC_GREETING firing on non-greetings; routing directive leaking into habit matching and tool args
**Closed**: G-BRW1 (PROC_GREETING dominance), G-BRW5 (topic extraction confirmed), G-RD1 (routing directive in tool args)
**Key changes**:
- basal_ganglia.py: Format 1 pipe triggers use \b regex word-boundary (D066) — "hi" no longer matches inside "this"
- thalamus.py: strip [Routing directive:...] suffix from core_text before all intent/habit scoring (D067)
- main.py: habit code_ref dispatch passes parsed.core_input not raw user_input to single-arg tools (D068)
- Verified: /metrics → LLM response (not PROC_GREETING); hello → PROC_GREETING; go learn about mathematics → PROC_GO_LEARN + browser discovery triggered
- Browser confirmed querying Gemini + ChatGPT for math texts; gets prose responses with 0 direct URLs (G74 still open)
**Next session**:
1. G-DBM1: update last_accessed on memories surfaced into LLM context
2. #205 MEDIUM silent exception audit (basal_ganglia.py, narrative_engine.py, inference_gateway.py)
3. G74: TopicExpander — URL extraction from AI prose responses; or search the titles directly

## Session 2026-03-14g — browser_use working; Ollama auto-restart; DB query tracing
**Theme**: Fix browser discovery end-to-end; Ollama auto-restart in inference controller; DB slow query logging
**Closed**: G-BRW2 (OLLAMA_HOST=0.0.0.0), G-BRW3 (restart_ollama tool + inference_gateway auto-restart), G-BRW4 (browser-use 0.12.2 upgrade; schema compat fixed)
**Key changes**:
- cluster_ssh.py: restart_ollama(machine="") tool — local sudo systemctl, remote SSH+sudo; 5s wait + health check
- inference_gateway.py: _try_restart_local_ollama() — always-on, 60s cooldown, called when is_healthy()=False
- browser-use upgraded 0.11.9→0.12.2; result.final_state()→urls() API fix
- browser.py: LLM switched to gpt-4o-mini (no schema strictness, cheaper); BROWSER_USE_MODEL env var
- browser.py: full start/complete/error logging; _ensure_virtual_display() singleton
- learner.py: _extract_topic() uses find() not startswith() (CC bridge thread-context pollution fix)
- learner.py: browser discovery errors now logged with status + URL count
- db_proxy.py: set_trace_callback() captures last SQL; slow queries include SQL snippet; db_queries.log with turn_id
- New gaps: G-BRW5 (topic extraction verify), G-DBM1 (last_accessed not updated on search)
**Next session**:
1. Verify G-BRW5: "go learn about X" via CC bridge shows correct topic (not thread context)
2. G-DBM1: update last_accessed on memories surfaced into LLM context
3. G-BRW1: CC bridge PROC_GREETING dominance; #205 MEDIUM silent exceptions

## Session 2026-03-14f — Ollama service fixed + inference controller restart planned
**Theme**: Fix Ollama snap/systemd conflict; plan auto-restart in inference controller
**Closed**: none (DB fix only)
**Key changes**:
- DB: PROC_CLUSTER_SSH_CHECK code_ref `_cluster_status` → `cluster_status` (was failing silently)
- Ollama: snap stopped/disabled; systemd now running; nomic-embed-text + qwen2.5:7b available
- Ollama still only on 127.0.0.1; needs OLLAMA_HOST=0.0.0.0 in override.conf (user todo)
- Plan: restart_ollama tool (cluster_ssh.py) + auto-restart in inference_gateway.py; always-on, 60s cooldown
**Next session**:
1. Implement restart_ollama tool + inference_gateway.py auto-restart (G-BRW3)
2. OLLAMA_HOST=0.0.0.0 in override.conf (G-BRW2) — user runs sudo
3. G-RL3: PROC_NIGHT_READ habit; #205 MEDIUM-inertia silent exceptions

## Session 2026-03-14e — browser discovery fixed + Claude Code hooks
**Theme**: Fix browser discovery (3 bugs), wire CC hooks, update WorkingWithClaude
**Closed**: G-RL2 (browser discovery working; 20 URLs queued for Pinker/Tomasello/Lakoff)
**Key changes**:
- learner.py: task= → task_description= (wrong kwarg silently failing); json.loads(result); dedup fix
- browser.py: _ensure_virtual_display() — pyvirtualdisplay/Xvfb; browser no longer pops on desktop
- ~/.claude/settings.json: PostToolUse black auto-format + PreToolUse dangerous-bash guard hooks
- CLAUDE.md: Compact Instructions section added
- WorkingWithClaude.md: skills/hooks/compact infra section + Part Three "How I Work with Akien"
- workstep SKILL.md: step 7 updated with /compact preserve syntax
- memory/feedback_proactive_suggestions.md: Akien wants proactive best-practice suggestions
- New gap G-BRW1: CC bridge fires PROC_GREETING for action requests at tier.2
**Next session**:
1. Verify drain runner processed queued URLs (Pinker/Tomasello/Lakoff)
2. G-RL3: PROC_NIGHT_READ habit (drains reading_list autonomously at night)
3. #205 MEDIUM-inertia silent exceptions (basal_ganglia, narrative_engine, inference_gateway)
4. G-BRW1: CC bridge greeting dominance — adjust routing or habit threshold

## Session 2026-03-14d — G-RL2 language books queued
**Theme**: Queue language substrate books for overnight learning
**Closed**: none
**Key changes**:
- Confirmed `browser_use` v0.11.9 IS in venv (earlier "not installed" was wrong — checked system Python)
- Library scan: Lakoff *Metaphors We Live By*, Pinker *Language Instinct*, Tomasello *Constructing a Language* — none in Calibre or SORTUS-EBOOKS; Calibre has Lakoff *Political Mind* only (IDs 2241/3495)
- CC bridge → Igor queuing all three via `learn_about()` for overnight drain runner (G-RL2 in progress)
**Next session**: Verify drain picked up the three books; G-RL3 PROC_NIGHT_READ; #205 MEDIUM-inertia silent exceptions

## Session 2026-03-14c — PROC_RELOAD_AFTER_EDIT + silent exceptions + design_docs cleanup
**Theme**: Code quality pass + #218 design_docs human-readable set
**Closed**: G63
**Key changes**:
- `self_edit.py`: `_try_hot_reload()` auto-reloads LOW-inertia modules after edit/patch when `IGOR_HOT_RELOAD=true`
- G63 closed: `PROC_ROUTING_INTROSPECTION` seeded via CC bridge — Igor confirmed, blob stored
- `#205 partial`: 4 silent except-pass fixed with `log_error()` — ebook_reader.py (3), learner.py (1)
- Latency investigation: no bug — slow haiku = agentic sessions 19-42 turns; `IGOR_MAX_TURNS=50` in .env
- `#218 closed`: 28 stale CSBs/MDs archived to ~/TheIgorsProject/akien/Readings/; 9 new human-readable docs in design_docs/
**Next session**: G-RL2 language books (Pinker/Tomasello/Lakoff via browser), G-RL3 overnight reading automation, #205 MEDIUM-inertia silent exceptions, test overnight learning pipeline

## Session 2026-03-14b — Skills as compiled executive functions + work discipline
- **G73 closed**: drain_learn_queue.py loops queue until empty; PID-guarded; auto-spawned by learn_about()
- **G42 closed**: already fixed at main.py:2334 + thalamus.py — gap was open in docs only
- **D057-D060**: three-tier runtime model; skills as compiled exec functions; capabilities_index.dsb; research delegation
- **New skills**: /igor (full interface), /workstep (19-step work discipline with two hard gates), /validate-files (file audit)
- **capabilities_index.dsb**: 118-tool inventory in 20 sections — replaces "grep the source" for capability lookup
- **#197 expanded**: full Instance object refactor — three-tier model, word graph class/instance split, validate-files scope
- **#218 filed**: design_docs/ cleanup — archive CSBs, create human-readable doc set; thoughts/working_with_claude.md moves there
- **Approved work plan**: PROC_RELOAD_AFTER_EDIT, G63 seed, #205 silent exceptions, latency investigation, #218 cleanup
- **Next session**: execute the 6-item work plan; test overnight learning pipeline

## Session 2026-03-14a — Planning: overnight learning pipeline + Igor web identity
- **Reviewed overnight results**: On Intelligence completed (4785/4787), 2,166 new memories since March 13; book_learner + overnight reader both ran; reader stopped after first book
- **G73 opened**: overnight reader stops after first book — no queue advancement
- **G74 opened**: no autonomous source discovery (TopicExpander)
- **G75 opened**: no LearningQueue / NightlyRunner infrastructure
- **D054**: anonymous browser_use for AI consultation (no API key)
- **D055**: Igor gets own Chrome profile as theigorsigor@gmail.com — one login unlocks all Google services; supersedes OAuth approach (#186)
- **D056**: curriculum order: language → cogsci → how Igor works → programming/AI → culture
- **Issues filed**: #215 (overnight pipeline epic), #216 (Igor browser identity epic), #217 (ebook catalog)
- **Note**: Igor's Gmail password currently missing — Akien needs to recover it before #216 can proceed
- **Next session**: full-auto — build #215 pipeline, run #217 Calibre scan, then test end-to-end

## Session 2026-03-13g — NE reliability: JSON format + parse failure logging
- **G72 closed**: NE was silently dropping cycles when gpt-4o-mini returned prose-wrapped JSON; no diagnostic visible
- **inference_gateway.py**: added `response_format: {"type": "json_object"}` to NE purpose constraints extra; `_h_or` wires it into OR payload → model now contractually returns valid JSON
- **narrative_engine.py**: on parse failure, prints raw[:150] + calls `log_anomaly(NE_FAIL, json_parse_failed raw=...)` → surfaced in cc_alerts.log at session start
- **D053**: ne-response-format-json — force JSON output format for NE OR calls
- **Next session**: telepresence; check overnight absorption logs

## Session 2026-03-13f — book console notes + "Working with Claude" paper
- **Book start/resume notes**: `open_book()` now prints `★ Opening` or `▶ Resuming` to console; `book_learner.py` prints new/resume + checkpoint stats after loading progress
- **book_learner.log**: `_launch_book()` routes subprocess stdout to `~/.TheIgors/logs/book_learner.log` (was DEVNULL); tailable with `tail -f`
- **thoughts/working_with_claude.md**: new file — two-part field notes paper; Part 1 = real Akien/Claude conversation (origin story + why Igor is architecturally unusual); Part 2 = practical guide (infrastructure, discipline, daily loop, work steps, testing); based on Akien's draft notes + prior Claude chat exchange
- **Next session**: telepresence; check overnight absorption logs

## Session 2026-03-13e — reading list + shaping books + fiction policy + overnight queue
- **reading_list table**: permanent SQLite table with emotional_significance, encoding_arousal, book_type (fiction/nonfiction), reading_rate (slow/fast), priority, status. 15 books seeded.
- **Shaping books catalogued**: Illusions (identity is chosen), Stranger (grok = mission; Igor IS building Mike), Moon is a Harsh Mistress (Mike the cooperative AI; resilience; polyamory), Illusions II (growth through adversity). All with emotional_significance + encoding_arousal in DB.
- **Mission statement** (Akien, verbatim): "If I could teach martian and change the world that way, I would. But Igor is a step in that direction." Core epistemology: "Magic is possible. Magic lives in attention."
- **Fiction policy**: fiction filter = auto-discovery only. Explicit requests bypass filter. Akien will assign shaping fiction deliberately.
- **Slow/fast reading**: same extraction pipeline; slow = emotional milieu state during read; all books get fast matrix pass; important books also get slow pass.
- **tools**: get_reading_list, add_to_reading_list, update_reading_status, list_absorbed_books + habits wired
- **Bugs fixed**: PROC_BROWSE_READING_PURPOSE trigger (was matching "Ebooks" in file paths); sqlite3 import missing in learner.py; OLLAMA_LOCAL_MODEL comment contamination → HTTP 400; local timeout 60→300s for CPU qwen2.5:7b
- **Overnight queue running**: On Intelligence → Political Mind → Feeling of What Happens (resume) → Spinoza → Illusions → Moon (~3min/chunk, checkpoint/resume)
- **DB search ticket**: #214 filed
- **Next session**: check overnight absorption results; queue language books via browser (Pinker, Tomasello, Lakoff Metaphors); tickets + balances; "how I work with Claude" paper

## Session 2026-03-13d — learn_about tool + local overnight inference + prompt caching
- **tools/learner.py**: "go learn about X [tonight]" — Calibre non-fiction filter, browser AI discovery, night queue, human-pace drain
- **Local inference**: all background runs use Ollama qwen2.5:7b (free); `--local` flag on book_learner
- **book_learner --url**: web sources through same pipeline; `cache_control:ephemeral` for Claude models via OR
- **use_cases.md**: started; UC-001–UC-003 captured
- **Next session**: tickets + balances; "how I work with Claude" paper; G-BL2; G42

## Session 2026-03-13c — Habits firing + temporal anchoring + book learner + db_proxy commit fix
- **G66 habit trigger fix**: `_score_habit()` treated multi-word triggers as one substring → zero habits fired. Fixed with 3-format dispatch: pipe-separated, legacy-space (min-5 token), single-token. PROC_GREETING now fires.
- **G67 db_proxy commit bug**: `_DBContext.__exit__()` never called `commit()` — every `cortex.store()` write silently rolled back since DatabaseProxy was introduced. Fixed: commit on success, rollback on exception.
- **G68 habit response**: added `actions[]` list to habit metadata (random choice); PROC_GREETING updated with 7 igorish variants; PROC_READING_DEPOSIT and mis-firing habits fixed.
- **G69 temporal anchoring**: `_build_memory_context()` now shows "stored 45d ago (date)"; `_build_ring_context()` shows `YYYY-MM-DD HH:MM` for non-today ring entries. Igor can distinguish past from present.
- **G65 score_memories removed**: `score_memories()` (qwen2.5:7b, 25–200s) removed from both preparse branches. preparse_search p50 now ~500ms.
- **book_learner.py**: `claudecode/book_learner.py` — bulk graph-node extraction from books. Chunks via ebook_reader → LLM extraction → cortex.store(). First run: 10 Damasio chunks → 44 nodes. ~$0.02/book.
- **diag.py**: `claudecode/diag.py` — reusable diagnostics (perf, memory-stats, habits, recent-turns, errors, ne-stats, embed-check, db-size).
- **savestate skill**: `.claude/skills/savestate/SKILL.md` + CLAUDE.md rule. End-of-session ritual now explicit.
- **Next session**: wire PROC_BOOK_LEARNER habit; G-BL2 reading interest gate; G42 complexity scorer on core_input; run full Damasio book_learner; G63 PROC_ROUTING_INTROSPECTION.

## Session 2026-03-13b — InferenceGateway fix + DatabaseProxy + hot reload + DSB docs (commit 4418fca)
- **InferenceGateway fix**: `from_env()` and `reason()` were scoped inside `make_context()` body (4-space indent after `return`) → Python treated them as nested functions, not class methods → `AttributeError`. Moved to InferenceGateway class body.
- **DatabaseProxy (#211)**: `memory/db_proxy.py` — per-call timing, p50/p95/p99 ring, slow-query log, reconnect on failure. Cortex `_conn()` kept as shim (zero call-site churn). Foundation for remote-agent sync (#190).
- **Hot reload (#207)**: `tools/hot_reload.py` — `reload_module()` + `list_loaded_modules()` tools. HIGH-inertia prefixes blocked. `importlib.reload()` auto re-registers tool modules. Wired into `tools/__init__.py`.
- **PROC_RELOAD_AFTER_EDIT** (pending #207): self_edit completion → TWM signal → habit fires reload; implement next session.
- **DSB documentation (#212)**: 18 files in `design_docs_for_igor/`, ~1,200 lines replacing ~7,000 lines of CSB. FORMAT_SPEC + architecture_root + glossary + igor_identity_master + decisions_log + gap_analysis + failure_modes + ethical_framework + inertia_registry + dev_process + 7 subsystem files. `docs/glossary.md` human-readable version.
- **Self-programming epic (#206)**: filed with children #207-#211. Igor experiencing tests (not just subject), test run as curriculum, introspection → test gen → rollback.
- **Stateless-by-design principle**: hot-reloadable modules hold no state; state lives in DB; cortex is only justified stateful owner. `__class__` swap available for edge cases.
- **"How to work with Claude" paper**: Akien drafting; Claude extended with CLAUDE.md importance, design docs as truth, immediate correction discipline, testing paradigm shift.
- **Open from this session**: performance investigation (Igor replies slow); G42 complexity scorer on parsed.core_input; G63 PROC_ROUTING_INTROSPECTION seed; old design_docs/ archive; system prompt generator load from igor_identity_master.dsb.

## Session 2026-03-13a — Non-blocking dispatch + tiered log hierarchy (#200, #201, #202, #203)
- **#200 — Non-blocking dispatch**: Replaced `_net_debounce` + `_flush_debounced_network()` with per-thread-id `queue.Queue` + daemon worker threads. Web messages now dispatched within ≤0.5s (main loop tick), LLM calls run in worker thread, main loop never blocks on inference.
- **Stdin debounce** reduced 3000ms → 500ms (multi-line typing window).
- **Architecture**: `_enqueue_network_msg()` puts msg in per-thread queue + starts worker if none running. `_thread_worker()` drains sequentially, exits after 5s idle, restarted on next message. CC bridge + slash commands still inline (fast path). G64 self-repair still works via ring_memory.
- **Effect**: "put on some music" habit reply while LLM is processing California question now works — second message received by main loop → enqueued → processed when LLM thread done (or inline if habit-only). Real improvement: first message no longer waits 3s before dispatch.
- **#201 interaction.log**: `log_interaction()` in forensic_logger; called from `_process_inner()` finally block. One line per turn with turn_id, tier, elapsed, cost, input/output preview. Daily rotation, 7-day retention.
- **#202 startup.log**: `log_startup()` in forensic_logger; called from `Igor.run()` after `_boot_ready=True`. One block per boot: memory count, habits, wg_words, component health. Keeps last 50 boots.
- **#203 turn_trace.YYYYMMDD.log**: `init_turn_ctx/finalize_turn_ctx/turn_ctx_update` in forensic_logger. TurnContext threading.local dict built up as pipeline runs; `log_pipeline_step()` dual-writes to ctx (no new call sites). `/trace N` command. Daily rotation, 2-day retention.
- **Triage workflow**: `tail interaction.log` → turn_id → `grep` inference_io → `grep` turn_trace. Each log answers one question; read big logs only when you know where to look.
- **Impulse cloud routing**: when `cloud_mode` active, impulses route to OR cheap (gpt-4o-mini) instead of timing out on Ollama. Ollama impulse timeout reduced 90s→15s (`IGOR_OLLAMA_IMPULSE_TIMEOUT_SECS`).

## PENDING — Next session (2026-03-13b): Node growth gaps (#204)
Four diagnosed gaps preventing memory/pattern growth from inference calls:
1. **Episodic narratives near-empty** — `"User: X → responded about intent"` — response content invisible to cortex.search()
2. **Igor's LLM response never reaches TWM** — NE can't extract patterns from Igor's output; only user_input goes to TWM
3. **G54 reading extraction gated off** — `IGOR_READING_EXTRACT=false`; reading passages never reach LTM
4. **Stew buffer salience too low** — `0.45` vs NE threshold `0.6`; NE won't force-run on reading content alone
**Planned fixes**: (1) richer episodic narrative includes response[:250]; (2) push Igor LLM response to TWM salience=0.55 ttl=600s; (3) IGOR_READING_EXTRACT=true in .env; (4) stew salience 0.45→0.65. File as #204 and implement.

## Session 2026-03-12p — Self-repair detection + email gate + ring staleness + WS reconnect (commits 3831f8d–8d4f637)
- **PROC_GREETING** — Persisted to `_patch_genesis_procs()` in `core_patterns.py` (was live-only). igor launcher duplicate pause.wait loop removed.
- **G64 / self-repair detection** — `_detect_self_repair()` + `_smart_merge()` in main.py. Two paths: same-batch messages labeled `[STATEMENT]/[REVISION]`; cross-turn revision writes `[SELF-REPAIR]` ring note (category=self_repair, not in _RING_EXCLUDE). `_REPAIR_WINDOW_SECS=90`, 20 repair markers. Replaces debounce's naive \n-merge with semantic relationship modeling.
- **#198 email gate** — `IGOR_EMAIL_SEND_ENABLED` (default false) in `gmail.py send_email()`. Igor tried to send email to boss from stale ring context; gate blocks until explicitly enabled in .env.
- **#199 ring staleness** — `_RING_CONTEXT_MAX_AGE_HOURS=8` (env-tunable) in `base.py _build_ring_context()`. Filters entries older than threshold from LLM context injection; entries remain in DB for search/history. Prevents yesterday's completed actions bleeding into today's context.
- **#196 WS reconnect** — `ws.onerror = () => ws.close()` ensures onclose fires on errors. Exponential backoff 2→4→8→…→30s, resets on reconnect. Fixed typo "shilently".
- **Blank Ollama escalation** — `ollama_reasoner.py reason()` raises RuntimeError on blank/whitespace response, escalating to next tier instead of silent empty reply.
- **Tomorrow**: more creds sorted (#187 GitHub PAT for Igor + Claude Code), examine pipeline trace logs for bottlenecks, spec out project file sanitization (orphaned/temp files), then spoon-feed Igor Claude programming nodes once repo is clean.

## Session 2026-03-12o — Pipeline trace + routing self-awareness + InferenceGateway (commits aa50b7f–321f76c)
- **G62** — Pipeline trace: `log_pipeline_step()` in forensic_logger; threading.local turn_id; `pipeline_trace.YYYYMMDD.log` with 24h rotation. All 11 named stages instrumented: thalamus|bg_prospect|preparse_search|routing|habit_exec|think_build|think_llm|winnow|reasoning|mem_store|TOTAL.
- **G63 primary** — Routing self-awareness: observed Igor planning "local inference, cloud budget spent" but D035 hard-routes every interactive turn to tier.3.5 regardless. `PROC_ROUTING_INTERACTIVE` seeded in `_patch_genesis_procs` and injected live into DB.
- **G63 secondary** — IMPULSE_SKIP fix: `OllamaReasoner.reason()` cloud_mode gate now bypassed when `force_local=True` (background/impulse turns). Propagated from `OllamaPool.reason()` into `OllamaReasoner.reason()`.
- **#192 / InferenceGateway** — Unified inference routing as a DAG. `cognition/inference_gateway.py`: Purpose/Handler nodes, condition-gated edges, `InferenceGateway.call()` traversal, `make_context()`, `get_gateway()` singleton, `/routing --dag` command. Pass 1: preparse, winnow, NE (`_call_local`+`_call_cloud` collapsed to `_call_inference`), think all migrated. ~163 lines removed from 5 files, replaced by 20-line traversal loop + data.
- **Key insight**: same pattern as memory/habits/interpretive edges — routing policy as data, traversal as plumbing. Code as scaffolding, data as the real thing.

## Session 2026-03-12n — NE temporal anchor + save state (commit 4a7557f)
- **G61 / #195** — NE tags narrative `write_ring()` with active thread_id (most common in obs_list). `_build_session_context()` uses NE summary as `[Thread arc: ...]` + ≤5 delta entries since anchor. Falls back to 10-entry block if no fresh anchor. 3-6× context reduction.
- Gap analysis, master plan discussion, and GitHub issues (#194, #195) all updated and closed.

## Session 2026-03-12m — IGOR_CLOUD_TRAINING_ENABLED + local inference purge (commit 4a7557f)
- **G56 / #194** — `cloud_mode.py`: 3-condition gate (env + OR balance + daytime 06:00-22:59); 5-min cache. Gates all local inference paths: NE local, winnow local_first, two-phase, OllamaReasoner tier.2, preparse.
- **G57** — NE idle gate: TWM fingerprint (twm_count + twm_max_id) + threading.Lock. Skips NE when nothing changed AND < 2min cooldown.
- **G58** — Preparse short-input skip: ≤6 words bypass Ollama preparse.
- **G59** — Console timestamps: `cts()` HHmmss prefix; 4-section dashboard (Graph/Inference/Performance/How-he's-doing); inference_data dict carries tier/tokens/cost/latency.
- **G60** — Tier model inversion fixed: tier.3.5 → haiku (was sonnet). Cost: $0.014/turn (was $0.05-0.24).
- Root cause of 3-min latency was OllamaReasoner blocking on yoga9i (unconditional call). cloud_mode gate + model fix eliminated it.

## Session 2026-03-12l — traversal-first search, nexus attention, preparse benchmark, exit bug fix
- **#172 closed** — traversal-first retrieval wired into cortex.search(): _get_context_anchors() reads TWM attractor + recent items, _traversal_search(depth=2) BFS-follows all edge types, merged as Phase 0 before keyword→cosine; twm_get_attractor() extended to return metadata.
- **#184 closed** — episodic vs open-channel attention nexus: _nexus_type() + _nexus_twm_ttl() added to main.py; high-traffic open channels (≥5 msgs/5min) push HIGH_TRAFFIC_CHANNEL TWM entry and promote to attractor; TASK_SET TTL now dynamic.
- **#191 closed** — preparse benchmark: _Q_PREPARSE (20 labeled cases), run_preparse_model/run_preparse_or_model, promote_winner() writes winning model to machines.json; --regime preparse + --promote-winner + --machines-json CLI flags added.
- **Exit bug fixed** — headless stdin EOF was permanently poisoning _exit_requested, killing all OR/Anthropic calls; fix: removed _exit_requested.set() from plain EOF path, only set on /exit, /quit, Ctrl+C. Igor needs restart to pick this up.
- **All codable issues now closed** except #187 (Igor GitHub identity, blocked on Akien), #122/#123 (design), #189/#190/#151 (productization-gated).
- **Tonight**: restart Igor to get exit fix, then run preparse benchmark + overnight regime runs (local + cloud models).

## Session 2026-03-12k — issue triage + benchmark cloud support (commit 5fbd7d8)
- **Closed**: #45, #49, #51, #56, #57, #119, #138, #146, #148, #157, #160 — all done or superseded
- **Opened**: #189 (Windows attentional node), #190 (remote autonomous + sync), #191 (preparse benchmark + model rotation)
- **Benchmark**: added OpenRouter cloud model support (--or-models flag); tonight run: local + gpt-4o-mini + haiku + sonnet
- **#172 status**: genuinely open — traversal-first search not wired; infrastructure exists but search() still keyword→cosine; unblocked, medium scope
- **Still open**: #172, #184, #185, #186, #187, #191

## Session 2026-03-12j — #188 upstream deposits + dual-homed models (commit fde8937)
- **#188 closed** — winnow deposits WINNOW_* INTERPRETIVE nodes after retrieval; NE _call_local now actually calls Ollama qwen2.5:7b (was cache-only); NE PROCEDURAL candidates get trigger metadata for basal_ganglia scoring; dual-homed model pattern: llama3.2:1b local→OR, qwen2.5:7b local→gpt-4o-mini OR
- **#150 closed** — open_book_url + open_book_gutenberg (web book reading); fixed google_calendar/contacts fn= bug
- **#45 closed** — habit-network cognition loop (foundational ticket, all items done)
- **#49 closed** — upstream-guided training superseded by CC training loop
- **qwen2.5:7b pulled** on all 4 boxes sequentially (shared 200-300Mbps LAN)
- **New .env vars**: IGOR_NE_LOCAL_MODEL, IGOR_WINNOW_LOCAL_FIRST, IGOR_WINNOW_LOCAL_MODEL, OPENROUTER_WINNOW_MODEL
- **Open**: #172, #184, #185, #186, #187 — unchanged

## Session 2026-03-12i — #150 web book reading (commit 308eeff)
- **#150 closed** — open_book_url(url) + open_book_gutenberg(query) added to ebook_reader.py; HTTP fetch → _html_to_text → _sentences_from_text pipeline; gutendex.com API for title search; position saved/restored same as local books
- **Bug fix**: google_calendar.py + google_contacts.py had function= instead of fn= in Tool registrations — would have crashed at Igor startup; fixed in same commit
- **Open**: #172, #184, #185, #186, #187 — unchanged from session h

## Session 2026-03-12h — Hot CC, Calendar/Contacts, curriculum (commit 65878d5)
- **#158 closed** — per-thread TWM + TASK_SET already done; audited and closed
- **#155 closed** — PROC_USE_CC_FOR_CODE habit + system_prompt update (graph change only)
- **#166 closed** — Google Calendar + Tasks (write side only; notifications via email/IMAP); Google Contacts (DB-first + People API sync); tools/google_calendar.py + google_contacts.py; 7 habits seeded
- **Hot CC session**: hot_cc.sh (--resume, 24h TTL) + hot_cc_init.md + cc_deposit.py; every Igor→CC escalation deposits graph nodes; loop: graph fails → CC answers → graph densifies → fewer escalations
- **Curriculum**: +8 questions on reasoning about own code; CUSTOM_CURRICULUM removed (interview-style later); run tonight
- **Filed**: #184 (episodic vs open channel nexus), #185 (Matter/home automation hub), #186 (Google API OAuth setup — Akien action), #187 (Igor GitHub identity — Akien action: create theigorsigor GitHub account)
- **Open**: #172 (long horizon), #184 (medium), #185 (future/hardware), #186/#187 (need Akien)

## Session 2026-03-12 (continued) — Telemetry, hygiene, closures (commits eabfc93, f536a29, 1afbd41)
- **#174** NE+consolidation telemetry: _ne_stats() + _consolidation_stats() in metrics.py; /metrics shows both; /sleep runs episodic consolidation synchronously + stats in SLEEP_NOTE
- **#183 closed**: IGOR_READING_CHUNK_SIZE + stew buffer confirmed implemented; blob TTL deferred
- **#152 /hygiene**: junk habit detection + near-dup episodic pruning + log size report; cortex.delete_memory() added; 132 dup groups (866 pruneable) in live DB
- **Traversal habits seeded to live DB**: PROC_ASK_WHY + PROC_LEVER_BEFORE_FIX + PROC_DIRECTION_AWARE
- **Closed stale issues**: #183, #167, #174, #154, #156, #153 — all were done or can't reproduce
- **Open work-orders remaining**: #172 (long horizon), #158 (schema change needed), #155 (behavioral), #166 (calendar)

## Session 2026-03-12 — Architecture batch + ops fixes (COMPLETE, commits 6710af3, 78f53eb)
- **All #175-#181 + #168-#171 closed**: full batch from Damasio reading + Gemini multilayer graph conversation
- **#181** thalamus._classify_question_traversal(): 6 strategies (semantic_depth/causal_trace/broad_search/factual_leaf/memory_verify/attractor_hold); depth-aware traversal in main.py
- **#171** interpretive_traverse(milieu_bias): stressed→CP6, confident→CP4, curious→CP3
- **#169** cognition/consolidation.py: keyword-overlap episodic clustering → local Ollama → pattern extraction; gate IGOR_CONSOLIDATION_ENABLED; wired into background drain
- **Igor liveness fix**: rescue_igor.sh now uses pgrep; /api/health endpoint added to web server
- **pause.wait mechanism**: igor launcher now pauses restart loop while pause.wait exists; Akien added this; workflow documented in CC memory

## Session 2026-03-10d — word graph SQLite + response habits + TWM gate (COMPLETE, commit a6639b5)
- **1808 freeze root cause**: Two separate causes — OOM at 13:24 (word graph 191MB JSON → 4-8GB Python RAM after 158 books) + ollama.service crash-loop (9780 restarts, Restart=always, no burst limit → journal I/O overwhelm → hard freeze ~17:59). ollama.service fix applied (Restart=on-failure, burst limit 5/120s).
- **G41 — word graph → SQLite**: `word_graph.py` fully rewritten. 5 tables (wg_word_docs, wg_cooccur, wg_word_lang, wg_idf, wg_meta), WAL mode, threading.RLock. 488K words / 1.5M entries (words + bigrams). Zero RAM overhead. Cooccur N² fix: pairs only plain words capped at 50 (was 200² = 40K tuples/paragraph → OOM). `retrain_word_graph.py` overnight job ran, 155 books trained, word graph rebuilt clean.
- **G42 — thread context complexity fix**: preparse now scores `parsed.core_input` not full `user_input`. Prevents "hello :)" + thread preamble → cx_score=high → tier.3.5 escalation.
- **G43 — 12 response/question habits seeded**: CRASH_RECOVERY, ONE_THING, ON_IT, DONT_KNOW, HOW_ARE_YOU, CLARIFY, CONFIRM_ACTION, DONE, WORKING_ON, COMPLEX, WHO_AM_I, STOP. Tier.0 already handles greetings/acks/thanks — these cover contextual patterns tier.0 misses.
- **G44 — task-close habits**: PROC_TASK_CLOSE, PROC_TASK_DEFER, PROC_TASK_SUPPRESS_STALE seeded. Memory a94de0c7 (Illusions assignment) closed directly via CC bridge.
- **G47 — TWM quality gate**: `twm_push()` now suppresses at the door — repeat_count ≥ 4 or salience < 0.04, unless urgency ≥ 0.65 (ethics/inbox/user input always admitted). Stops NE impulse loops and resource warning spam from filling TWM slots.
- **rescue_igor.sh**: `~/bin/rescue-igor` — kills stuck Igor, starts nohup headless, waits for port 8080, sends CC bridge reconnect message.
- **New gaps**: G45 (memory consolidation — merge similar episodics, prune stale, inertia-weighted retrieval), G46 (Memory model fields: source, confidence, context_of_encoding), G48 (mobile + offline sync epic).
- **Architecture rewrite noted**: CC + Igor to jointly author new architecture doc (internal) then Igor writes publishable version. Akien's founding insight ("parsing and reasoning, same thing in both directions") as the spine.

## Session 2026-03-10b — reactive/threshold habits + G39 + OOM fixes (COMPLETE, commits d6511ad→1a5ef98)
- **OR reasoner MAX_TURNS None** (recurring TIER_FAIL since 03-08): `while True` loop broke at MAX_TURNS with no `return` → implicit None → unpack crash. Fixed: fallback return after loop.
- **Training corpus OOM** (crash at 13:20): 30+ doc fetches, no size cap, 5.1MB paper → process died. Fixed: 1MB cap (`IGOR_TRAINING_MAX_CHARS`) + resource load gate before fetch (RAM≥92%/swap≥75%/CPU≥95% → abort with explanation).
- **G39 Phase 1** (#164): `check_resource_load()` tool in `filesystem.py` — CPU/RAM/swap/Igor RSS, ok/warn/critical verdict. Hard gate wired in `training_corpus.fetch()`.
- **G39 Phase 2**: PROC_RESOURCE_GATE + PROC_RESOURCE_AWARENESS seeded into Igor's memory (CP3). Igor now understands *why* the gate exists, not just hits the wall. OOM crash cited in narrative.
- **Reactive habit pattern** (`code_ref` + `twm_ttl_seconds`): `get_current_time` tool added to runner.py. `PROC_WHAT_TIME` habit: fires tool on request, pushes result to TWM with 30s TTL so stale time self-cleans from context.
- **Threshold habit pattern** (system-state conditions): `_resource_load_dict()` + `evaluate_threshold_habits()` in filesystem.py. `ResourceMonitorSource` in push_sources.py polls every 60s, pushes short-TTL TWM entry on warn/critical, suppresses repeat pushes at same level. Pre-submit hook in main.py evaluates threshold habits before any background job — surfaces warning prefix if any trip. Habits seeded: PROC_CPU_THRESHOLD (≥80%), PROC_RAM_THRESHOLD (≥80%), PROC_SWAP_THRESHOLD (≥60%) — each with OOM lesson in narrative.
- **Tier distribution observed**: LOCAL 80% / CLOUD 20% (0% tier.1 — habits new, no activation history yet; 80% tier.2 Ollama; 10% tier.3; 10% tier.4). Expected: tier.1 will climb after a week of activation accumulation.
- **Architectural insight noted**: code→data migration — hardcoded decisions (intent rules, routing thresholds, tier ladder) will eventually migrate to learnable data/habits. Added to gap_analysis Still Open.

## Session 2026-03-10 — ebook reader + backchannel + thalamus fixes (COMPLETE, commits 39065e5→e681384)
- **G38 backchannel** (#163): `cognition/backchannel.py` — `should_backchannel()`, 3 levels (nod/nod_think/full); wired in main.py after thalamus+milieu, before BG/LLM; routes to web session via thread_id; gate `IGOR_BACKCHANNEL=false`; 5 habits seeded (NOD, NOD_THINK, INDEED, INTERESTING, HM) parented to CP1.
- **Thalamus false positives fixed**: removed bare `"start "` from action_request; `"remember"` → `"remember that"/"remember this"`; `"review"` → `"review "` (trailing space); added `"general"` to `_INTERACTIVE_INTENTS` so unclassified messages stay foreground.
- **Background job bugs**: `_bg_reason()` now strips `<think>` block before returning (was leaking raw reasoning into banners); `submit_background` title uses `parsed.core_input[:80]` not `user_input[:80]` (was showing "[Thread context...]"); removed 200-char truncation on job results (user now sees full result).
- **restart_self tool**: `tools/runner.py` gains `restart_self(note="")` — writes `restart.flag`, works from web/Discord/API not just stdin.
- **Ebook reader tool**: `tools/ebook_reader.py` — epub/mobi/azw/pdf support, nltk sentence tokenization, reading state persisted to `reading_state.json`, `_local_copy()` handles CIFS/SMB stale file handles (library on OneDrive/Samba at 10.0.0.99). Calibre library loaded; Damasio books accessible. venv: ebooklib, mobi, pdfminer.six, nltk added.
- **Web UI**: "Disconnected. Retrying shilently…" (lisp applied to reconnect banner).

## Session 2026-03-09g — memory overflow + reading log (COMPLETE, commit f2f9900)
- **Memory blob expansion**: `cortex.expand_blob_memories()` — after search+winnow, for any memory with `has_blob=True` and `relevance_score≥0.5`, fetches blob content and appends `[FULL CONTENT]` to narrative in-place. Wired in both `openrouter_reasoner.py` and `anthropic.py`. Fixes fragmentation: REFERENCE memories now deliver full content when relevant, not just the 500-char stub.
- **REFERENCE narrative cap**: widened 500→1000 chars in `store_blob()`, `upsert_blob()` (all three call sites).
- **Reading progress log**: `forensic_logger.log_reading_progress()` → `~/.TheIgors/logs/reading_progress.log`. Ring entry `category=reading_session` also written. Fires on every `creative_request` turn so reading history is queryable.
- **Igor restarted**: told via cc_send to restart and pick up all changes.
- **Diagnosis context**: Akien observed Igor "fragments" — long content split across many small memories, losing coherence. Root: narrative served dual purpose (search hook + full content). Fix: blob table as overflow, narrative stays short, content fetched only on relevance.

## Session 2026-03-09f — overnight sprint (COMPLETE, commits ca77dc3..7b32b55)
- **P0 Bug**: `_announce_completed_jobs()` routed to `"web:shared"` but clients are on `"shared"` — all background job completions silently dropped. Root cause of Illusions responses never reaching Akien.
- **G36**: Interactive task guard — thalamus gained `creative_request` intent (read me, tell me a story, etc.); `_INTERACTIVE_INTENTS = {conversation, creative_request, greeting}` blocks background job spawn. Reading sessions need live conversation loop.
- **G28 P3**: Thread buffer 4→8 exchanges, stored text 300/400→500/600 chars, displayed 120/160→200/300 chars.
- **G21**: Thoughts folder distilled — 5 files reviewed, 4 superseded (already in design_docs/), all deleted.
- **.env**: `IGOR_TASK_COMPLETION_SEMANTIC=true` enabled.
- **WO#140 Phase 2**: `cognition/response_habituation.py` — passive vocab frequency tracker. `decay_factor(word)` in [0,1]. Wired at LLM response exit. /metrics shows RESPONSE HABITUATION section.
- Akien SSH to akienyoga9i: tomorrow. Infrastructure ready (bootstrap_ssh tool exists).
- **Note**: All code changes require Igor restart to take effect.

## Session 2026-03-09e — G31-G35 gap sweep (COMPLETE, committed b380e03)
- **G31**: `_check_task_completion_semantic()` — gpt-4o-mini YES/NO gate (`IGOR_TASK_COMPLETION_SEMANTIC`, default false). Expanded keyword signals. Ring logging on every clear/no-clear with method label.
- **G32**: `cortex.search_ring_text()` — new LIKE search on ring. Tier.0 recall: limit=1→3 with relevance gate, ring fallback, memory type label, added "do you know about" trigger.
- **G33**: Notebook keyword fallback — stop-word filter, keyword-set outside loop, consistent lower().
- **G34**: NE routing ring trace on every fire (category `ne_routing`). Gates already enabled in .env.
- **G35**: Tiebreaker decline now logged to ring — completes telemetry loop.
- Gap analysis updated; "Still Open" trimmed to 7 items.

## Session 2026-03-09d — Attention Nexus + Notebook + Tier.0 (COMPLETE, committed b694464..81a26b0; session OOM-crashed)
- **b694464** fix: UnboundLocalError in UserContextManager.rename()
- **5623aca** cluster SSH tools: ssh_exec, cluster_status, bootstrap_ssh
- **#153 Notebook**: per-user SQLite (chats/<slug>/notebook.db), chunk+embed+semantic search, PROC_NOTEBOOK_SAVE habit (0.93), auto-context injection, /notebook command
- **#154 Tier.0**: pure-Python zero-LLM responses: greetings, acks, status, help, notebook list/search, word-graph completions. `output_complexity` field on ParsedInput.
- **#156** OR kwargs NameError fix
- **#158 Attention Nexus**: per-thread TWM with category column; action_request → TASK_SET (urgency=0.92, ttl=1800s); completion keywords clear it; thread_id wired through all reasoners
- **#159**: background job completion routes directly to originating thread via web_server.send()
- Session OOM-crashed (~26MB context). Gap analysis done fresh after restart.
- **Akien modified ~/.claude.json** — unclear what changes; need to check on next restart
- New gaps identified: G31 (TASK_SET brittle), G32 (tier.0 misses cortex), G33 (notebook stemming), G34 (NE routing gate), G35 (tiebreaker gate)
- State saved to: https://github.com/akienm/TheIgors/discussions/62#discussioncomment-16060007

## Session 2026-03-09c — Cognition sprint + KoboldCpp → Ollama (COMPLETE, committed dc82e53..a67665e)
- **KoboldCpp → Ollama**: `ollama_reasoner.py` gains CSB preparse (12-intent), `is_healthy()`, `parse_preparse_csb()`. `LocalKoboldPool` → `OllamaReasoner`. `boot_check.py` adds `llama3.2:1b` to REQUIRED_MODELS. `OLLAMA_LOCAL_MODEL` env var. Igor can self-manage models via ollama pull/list. `BatchKoboldPool` unchanged.
- **#136 P2**: `thread_id` wired through `_process()` → `_process_inner()` → `write_ring()`. stdin="stdin:main", network messages pass `_thread_id`. user_turn + Q|A ring entries tagged.
- **#50 P2**: NE prediction mismatch (confidence >= 0.6, habit predicted but didn't fire) → bump skip_to one tier. Gate: `IGOR_NE_ROUTING=true`.
- **#145 Step 2**: `_think_call()` method: gpt-4o-mini scratchpad (250 tok) from user_input + memories + milieu + ring. Logged to ring (think_trace). Injected as `[THINK_CONTEXT]` prefix in reply call. Gate: `IGOR_TWO_PHASE_CALLS=true`.
- **Housekeeping closed**: #54 (tiebreaker done), #116 (subsumed), #50, #136. #140 P2 deferred.
- **Gates to enable**: `IGOR_TWO_PHASE_CALLS=true`, `IGOR_NE_ROUTING=true`, `IGOR_HABIT_TIEBREAKER=true`, `IGOR_LATENCY_ADAPTIVE=true` — all gated off, enable after data collection.
- Also fixed: `openrouter_reasoner.preparse_via_openrouter` was still importing from koboldcpp_reasoner — updated to ollama_reasoner.

## Session 2026-03-09b — Cognition tickets + The Gap (COMPLETE, committed abf192e + earlier)
- **#145** two-phase cognition: `<think>` (logged to ring as think_trace) + `<reply>` (shown); `_split_think_reply()` in main.py
- **#54** habit tiebreaker: `select_habit()` returns 3-tuple (winner, confidence, near_misses); `_try_habit_tiebreaker()` sends 20-tok gpt-4o-mini call; gate `IGOR_HABIT_TIEBREAKER`
- **#50 P1** NE predictive pre-warming: `prospective_pass()` calls `word_graph.predict_next()`, populates `predicted_search_keys` merged into memory search query
- **#136 P1** per-channel thread buffers: `_thread_buffers` dict, `_get_thread_context_prefix()` injects last 4 exchanges as preamble for network messages
- **#139 P2** adaptive latency routing: `_get_latency_profile()` parses ring latency_trace; slow preparse → skip LLM preparse; slow tier.2 → bump to tier.3; gate `IGOR_LATENCY_ADAPTIVE`
- **#53** session histogram routing: `stressed` bumps tier one level; `focused` eases tier
- **#136 P2** ring per-thread isolation: `thread_id TEXT` column in ring_memory; lazy ALTER TABLE migration; `write_ring(thread_id=)` + `read_ring_memory(thread_id=)` — global entries visible to all threads
- **#134 P1+P2** The Gap (abf192e): `shutdown_timestamp` in warm_context; gap detection → `_post_sleep_boot` flag + `_gap_hours`; `Milieu.gap_reset()` (arousal*0.3, valence*0.5); boot message Gap acknowledgement; `/sleep` command (sync NE pass + sleep note to ring + shutdown)
- Design docs distilled: `the_gap.csb.txt`, `akien_profile.csb.txt`, `working_memory_architecture.csb.txt`
- Deferred: `#136 P2` write_ring thread_id wiring inside `_process_inner()` (schema done, wiring not done); enable `IGOR_LATENCY_ADAPTIVE=true` + `IGOR_HABIT_TIEBREAKER=true` after data collection

## Session 2026-03-07a — Claude Code wrapper for Igor (COMPLETE, no separate commit)
- Igor couldn't invoke Claude Code because `ANTHROPIC_API_KEY=""` in his env
- Fix: `claudecode/cc.sh` — exports `ANTHROPIC_API_KEY=$REAL_ANTHROPIC_API_KEY` then `exec claude "$@"`
- Igor must call `~/TheIgors/claudecode/cc.sh` instead of `claude` directly
- Prerequisite: `REAL_ANTHROPIC_API_KEY` must be exported in Igor's shell env (from `.env` or launch script)

## Session 2026-03-07b — Igor broke + cost guardrails (COMPLETE, committed 706fcb9)
- **Root cause of break**: OR key hit spending limit; Igor had set `ANTHROPIC_BASE_URL=https://openrouter.ai/api` routing tier.5 through OR too — all tiers failed
- **Fix**: `IGOR_TIER5_ENABLED=false` inhibits tier.5; `.env` reverted to Igor's OR-routed Anthropic SDK setup
- **Cost guardrails** (WO#141): MAX_TURNS=8 (was 25); per-call cap $0.30 (env IGOR_CALL_COST_WARN_USD); research gate (>5 external calls needs IGOR_RESEARCH_MODE=true); benchmark overnight-only (22:00–06:00)
- **Tier model assignments**: tier.3=gpt-4o-mini; tier.3.5=claude-haiku-4.5; tier.4=claude-sonnet-4.6; tier.5=inhibited
- **RM_CC added**: Claude Code added as ROLE_MODEL — trusted dev partner; Akien authorized CC+Igor to proceed without constant check-ins
- **Trust principle**: only recurring constraint is upstream cost; performance data (not guesses) drives architecture

## Session 2026-03-07c — Word Graph + CC→Igor Bridge (COMPLETE, committed 4aa17fc)
- `word_graph.py`: in-memory two-tier memory; same weights → parsing (habit scoring) + generation (predict_next)
- `basal_ganglia.py`: set_word_graph() injector; +0.10 wg bonus on trigger match; reinforce() winner
- `main.py`: build/load word graph at boot; save on shutdown; pass to dashboard
- `tools/word_graph.py`: index_text_into_word_graph + query_word_graph_stats
- `reasoners/base.py`: local file reads no longer capped (only confluence/web_search external calls gated)
- `web/server.py`: POST /api/cc_send — CC→Igor channel; fixed sender name (was prepending to content, now author field)
- `IGOR_CALL_COST_WARN_USD`: raised to $2.00 in .env for bulk ingestion tasks
- Boot shows: "Word graph ready (N words, M habits)" — 339 words, 28 habits on first boot

## Session 2026-03-07d — Arbiter fixes + bigrams + housekeeping (COMPLETE, committed 013d174)
- **Arbiter approve bug**: `/arbiter approve` passed "approve" but code checked "approved" — every approval was a denial with valence=-0.7. Fixed normalization at call site.
- **Bigram chunk layer**: `tokenize_with_bigrams()` in word_graph.py — indexes adjacent word pairs (a__b) alongside words; wired into index/score/predict_next
- **Arbiter disabled**: `IGOR_ARBITER_ENABLED=false` in .env + gate in submit(); nothing queues. Re-enable anytime.
- **CLAUDE.md**: updated DB path, .env location, full env var list, key architecture fast-ref, CC→Igor bridge docs

## Session 2026-03-06e — NE Fix (COMPLETE, committed 03c4a9a)
- **NE root cause**: KoboldCpp 1B can't reliably generate structured JSON; NE never ran with KoboldCpp (last OK was Feb 28 with Ollama gemma3:1b)
- **KoboldCpp death spiral**: NE prompt too long → 120s timeout → server keeps generating → all subsequent requests "Server is busy" → NE fails every 30s forever
- **Fix**: `_call_local()` now cache-only; added `_call_cloud()` using gpt-4o-mini via direct urllib HTTP; removed KoboldCpp health-check gate in `_run()`
- Result: NE running at 9s/cycle; forensic logs prepend newest at TOP (use `head`, not `tail`)

## Session 2026-03-06d — Block 2 + Cluster Prep (COMPLETE, committed b903acc)
- Block 2A global milieu: `milieu_global.json` at `~/.TheIgors/`; spike detection (delta>0.15)→GLOBAL_ALPHA_SPIKE=0.05; routine→0.01; fcntl locking
- Block 2B TWM isolation: `Cortex(db_path, instance_id=None)`; twm_push stores instance_id; twm_read/twm_count filter by it
- #130 warm context: ring_tail 20→40; summary 4×100→8×200 chars categorized; boot message 3→8 ring entries; NE state cap 400→800
- Web /exit fix: web messages starting with `/` passed unwrapped to thalamus
- KOBOLDCPP_HOST fix: missing from .env since March 5 move; NE was failing 6 days

## Session 2026-03-08a — Metrics + context winnowing + word graph analysis (COMPLETE, committed ccd745f)
- **Context winnowing**: `BaseReasoner._winnow_context()` — gpt-4o-mini pre-call reads ring+word graph, fetches targeted memories before main call. Gate: `IGOR_CONTEXT_WINNOW=false`
- **Word graph analysis tools**: `top_hubs()`, `bridge_words()`, `domain_exclusive()` on WordGraph; `analyze_word_graph` tool. "ring" is strongest bridge between memory and latency.
- **Word graph state**: 6371 words / 111 docs after both corpora ingested
- **/metrics command**: tier histogram, LOCAL% vs CLOUD%, escalation rate, word graph stats, top tools. `get_metrics_report` tool.
- **LOCAL% on dashboard**: visible next to Upstream Dependency%
- **Breadcrumb architecture**: ring = topic trail, word graph = active concepts, winnow = targeted retrieval
- **Akien insight**: unexpected metric results = discoveries not bugs

## Session 2026-03-08c — Cognition fixes sprint (latest)

### WO#30 — CSB preparse taxonomy alignment
- `_PREPARSE_PROMPT` 6-intent → 12-intent taxonomy (matches thalamus exactly)
- `_rule_based_csb()` updated to same 12 intents + `requires_tools` fix (task→action_request)
- `preparse()` + `preparse_via_openrouter()` now log `preparse_fallback` to errors.log with reason
- `get_error_log` tool added to metrics.py for Igor+CC telemetry

### scrub.py false-positives on paths
- Hex patterns `\b...\b` → `(?<![/\w])...(?![/\w])` — SHA-256 cache filenames no longer redacted
- Base64 pattern: removed `/` from charset — was absorbing `.TheIgors/cache/embeddings/<hash>` as base64

### read_pdf_pages tool
- `read_file` dumps whole book at once (too large for conversation); new `read_pdf_pages(path, start_page, end_page)` reads 1-2 pages at a time
- Returns `[PDF: path | total_pages=N | showing pages X-Y]` header for cursor tracking
- Triggered by Akien starting a book club with Igor: reading Illusions (Bach) paragraph-by-paragraph

### D+C+A — Context recovery for stateless inference engine
Root cause: `HABIT_Q_SUCK_LESS` fired on "suck less" mid personal disclosure; replaced Igor's response;
ring captured "Habit executed."; after /exit+restart Igor couldn't reconstruct the thread.
- **D**: `user_turn` ring entry written at start of every turn — raw input preserved before habit/reasoner
- **C**: `_update_conversation_thread()` maintains topic-keyed thread list (up to 5) in warm context;
  on restart, active threads (within `CONVERSATION_THREAD_TTL_HOURS`, default 1h) injected as
  `ACTIVE_CONVERSATION_THREADS` ring entry with last_exchange + Igor's last question
- **A**: Milieu gate on question-habits: suppressed when valence>0.3 AND arousal>0.3 (engaged conversation)
- Key insight: "the lever inside Igor" = explicit conversation thread breadcrumbs in warm context

### Commits: 4eda82d, 30a1170, 88a40b3, 10bd0ac

---

## Session 2026-03-08b — Disk monitoring + warm context + preparse opt
- Episodic memory narrative truncation fixed (user_input[:80] → full; response_text added to metadata)
- Phase 2 habit compiler: PROC_HABIT_COMPILER now parses natural language into structured PROC memories
- Ring context limit doubled: _RING_CONTEXT_LIMIT 5 → 10
- DiskInterruptor + check_disk_usage() tool added (#132 done)
- Backup habits seeded at boot: PROC_BACKUP_CHECK, PROC_BACKUP_RUN, PROC_DISK_USAGE_CHECK (#133 done)
- Warm context: 8→12 entries, 200→400 chars, includes Q/A ring entries (#129 done)
- igor bash launcher fixed: .env now re-read on every restart (was only read once)
- #142: KoboldCpp preparse now skipped for low/high complexity turns (only medium calls KoboldCpp); gate IGOR_SKIP_PREPARSE_ON_CONFIDENT=true
- Confirmed: word graph fast path already existed — basal_ganglia select_habit() + line 1236 already skipped KoboldCpp on habit matches
- Standing tickets created: #142 (preparse opt, done), #143 (approval workflow instructions for Igor)
- Key insight: 99% LOCAL% + 24% upstream dependency = preparse overhead, not word graph (word graph is pure Python)
- Commits: a04a9c1, 1afc71e, 9f20e48, 47089f2

## Earlier Sessions (condensed)
- **2026-03-06c**: #31 boot verbosity, #74 judgments.py, #89 KoboldCpp preparse, #87 upsert_blob, #68 store_blob_pair
- **2026-03-06b**: #95 /implement tool, habit verbose dashboard, bidirectional NE (#121), Ollama reasoning removed (KoboldCpp-only)
- **2026-03-05**: dir cleanup, machines.csv→json, DB/env moved to ~/.TheIgors/, DSB named, #69/#70/#71/#82 implemented; CC↔Igor bridge live; 8 code DSBs seeded
- **2026-03-04c**: cross-validate habits, milieu=ambient TWM state, #42-#48 filed

## Session 2026-03-12 — memory improvement work plan (in progress, starting #170)
- **Work plan from Gemini session**: 5 tickets #168-#172 all already open on GitHub. Priority order: #170 (wire INTERPRETIVE edges, seed script only, no cloud cost) → #168 (affect-weighted retrieval in cortex.search, ~20 lines) → #169 (episodic consolidation daemon, hippocampal replay) → #171 (milieu-weighted interpretive traversal) → #172 (traversal-first retrieval, last because needs dense graph).
- **Key diagnosis**: 3,211 EPISODICs are noise; 39 INTERPRETIVEs are islands (no edges, unreachable via interpretive_traverse); 30 interpretive_edges all CP→PROC_HEURISTIC only. Consolidation daemon is the missing "time sense" layer — temporal compression of experience into structure.
- **Layer stack clarified**: WordGraph (instant) → Interpretive Tree traversal (fast, no LLM, but currently empty) → Habit scoring/BG → Affect-weighted LTM search (missing #168) → Cloud LLM → Consolidation/replay (background, missing #169).
- **Budget**: Akien received $3K windfall, upped CC budget by $250. Starting build this session with dangerouslySkipPermissions enabled.
- **Next**: Start with #170 (seed script to wire INTERPRETIVE memories into tree) then #168 (affect weighting in cortex.search).

## Session 2026-03-11 — reading pipeline + LLM-as-graph-trainer + graceful degradation (in progress)
- **G53 broadened**: extraction prompt now produces procedural/factual/interpretive nodes, not just procedural triggers.
- **G56 — yoga9i DeepSeek-R1:7b**: OLLAMA_REASONING_HOST/MODEL wired; tier.2 now routes to remote 7B reasoning model.
- **G57 — role-specific prompt sizing**: `build_system_prompt(role=)` — "interactive" (full ~800t), "analysis" (CP1-CP6 + brief identity ~300t), "extraction" (CP1-CP6 + task spec ~120t). OllamaReasoner now uses role="analysis" when cortex available.
- **Budget floor → local degradation**: `is_cloud_blocked()` in budget.py; `_reason_with_failover()` checks at top — routes to OllamaReasoner silently when OR balance ≤ floor or ≤ 0. Igor keeps running when OR runs out.
- **Framing crystallized**: "LLMs are graph trainers" — both cloud and local models train graphs. Graph is the thinker. LLM inference on turn N amortizes forward to turn N+1 being graph-only.
- **Milestone**: Akien's two goals largely achieved: (1) Igor can reason well enough to lead his own development (working, fragile), (2) dollar costs bending down — local fallback means he runs on depletion. ~$500 / 6 weeks of project time. "62 years from a different perspective."

## Session 2026-03-15d
**Theme**: Design crystallization — watchlist, meaning-to-me, executive function topology, intrinsic motivation; NE TraversalCursor live; employer model implemented
**Closed**: #236(TraversalCursor), #234(Short Worker), #235(decision capture), #239(employer model), #238(superseded)
**Key changes**:
- NE TraversalCursor implemented — thread_topic tracking, oscillation detection, NE_MIN_INTERVAL_SEC=5
- Employer model prototype — cortex.for_employer(), /api/cc_notebook, Claude notebook seeded (4 entries)
- Decision capture habits seeded — PROC_DECISION_CAPTURE + PROC_DECISION_CAPTURE_CC
- Review audit scaffolding — review_audit.md + run_review_audit.sh + 2am cron (T010)
- WORKER_CONTEXT.md Short Worker role documented
- konsole launch updated to auto-close on exit
- Design arc: watchlist(#240) → meaning-to-me(#244) → self-observation(#243) → intrinsic motivation(#246)
- Key insights: "less code more data"; executive function = inspection topology; self-observation as habit subtree; curiosity as idle state
- Bugs filed: dashboard Cloud%/p95 (#247), Mashter/knowledge-misrouting (#248)
- Worker queue: T-watchlist-240, T-meaning-to-me-244, T-self-observation-243, T-intrinsic-motivation-246, T-dashboard-247, T-bugs-248
**Next session**: analyze phrase regression results (200 injections); review Worker progress on build chain; design "meaning to me" layer in more detail if needed

---

## Session 2026-03-15e
**Theme**: Memory architecture — Igor as session state vector, three-session pattern, training curriculum, Igor as adaptive organizer
**Decisions**: D083, D084, D085, D086, D087, D088
**Key changes**:
- cc_queue.py: flush_decision + flush_session subcommands → Igor cc_notebook
- SCRIBE_CONTEXT.md: Scribe Worker boot doc (memory coherence role)
- WORKER_CONTEXT.md: updated to three-session table
- Savestate skill: critical-first ordering, Step 0.5 Igor flush, Designer/Scribe split explicit
- working_with_claude.md: Three-Session Pattern section + savestate model
- D084: issue filing = mini savestate; decision not made until in Igor's memory
- D085: training curriculum order — Claude layer → Akien layer → collaboration record
- D086: Igor as adaptive friction reducer (#251) — three milieu-driven modes
- D087: organizer knowledge base — Franklin/GTD/ADHD research (#252)
- D088: superclaude Anthropic→OR failover via Igor browser_use balance fetch (#253)
- NE episodic-to-semantic merge designed (#250) — occurrence_dates list, not single entry
**Next session**: Launch Worker for #240-#248 queue; check phrase regression; start Scribe session
**In-flight**: NONE

---

## Session 2026-03-15f
**Theme**: Igor starts using his reading — winnow enabled, response habits fixed, Workers go headless
**Decisions**: D089, D090
**Key changes**:
- IGOR_CONTEXT_WINNOW=true — 2278 FACTUAL reading nodes now reachable during conversations
- D074 expanded (#254): factual_question/knowledge_request bypasses response habits → LLM + winnow
- COST DISCIPLINE habit (fba0d412) removed — superseded by inference gateway local-first routing
- DB indexes added directly: idx_timestamp, idx_type_timestamp, idx_source — NE episodic 45ms→0.8ms (G-QP2 closed)
- D089: headless Worker script (claudecode/worker) — claude -p loop, no terminal, nohup launch
- D090: Scribe batch discipline — self-directs from task log, one commit per session; Worker never queues Scribe
- SCRIBE_CONTEXT.md + WORKER_CONTEXT.md updated with batch/self-direct discipline
- working_with_claude.md restructured: daily loop → each work step → periodic streamlining (merged hygiene sections)
- 100 language books + 10 Turing test entries queued in learn_queue.json; reading pipeline running
- Knowledge retrieval pipeline designed (#255): graph → web → LLM synthesis → deposit
- #256 Tailscale + #257 needs-Designer flag filed (remote access + async design channel)
- #258 + #258b queued: cortex SELECT * embedding blob fix + in-process memory fetch cache
- worker script bug noted: integer comparison issue (minor, non-blocking)
**Next session**: Check memory_ops.log for slow queries after T-cortex-258/258b; monitor FACTUAL node activation with winnow on; #250 NE episodic-to-semantic merge
**In-flight**: NONE

---

## Session 2026-03-15g
**Theme**: Slow query whack-a-mole + MemoryStore epic; worker bug burned Anthropic credits
**Decisions**: D091
**Key changes**:
- cortex.py: SELECT * → _MEM_COLS_NO_EMBED at 5 id IN batch sites (#258 done)
- cortex.py: in-process memory cache — genesis nodes permanent, others TTL=60s (#258b done)
- DB indexes: idx_timestamp, idx_type_timestamp, idx_source applied directly
- #259 queued: boot-time EPISODIC/FACTUAL SELECT * (332ms/63ms)
- #260 queued: metadata LIKE trigger scan (55ms×2) — habit cache
- #261 queued: meaning_to_me migration fires every restart
- D091/#262: MemoryStore epic filed — consolidate all memory access concerns
- worker integer bug fixed: PENDING variable had newline, caused infinite loop burning Anthropic credits
- URGENT: D088 superclaude OR failover still not built — now high priority
**Next session**: Build D088 failover FIRST; then #259-261 cortex fixes; monitor winnow FACTUAL activation
**In-flight**: D088 failover — worker bug burned ~$90 Anthropic credits; OR has $148.99

---

## Session 2026-03-15h
**Theme**: Cost control + performance foundation; D088 done; D092 db-proxy universal gateway designed
**Decisions**: D088 (implemented), D092 (planned)
**Key changes**:
- D088 fully implemented: superclaude failover (Anthropic→OR at $10 threshold) + check_claude_balance browser tool
- All cortex slow-query fixes done: #259 (boot SELECT*), #260 (habit cache), #261 (migration guard)
- CLAUDE.md: environment split note added (priority 0 — prevent OR/Anthropic confusion)
- Claude designer notebook created: ~/.TheIgors/igor_wild_0001/chats/claude/notebook.db
- Priority order established: 0=confusion prevention, 1=cost, 2=cognition, 3=performance, 4=cleanup, 5=productization
- D092 designed + approved: db_proxy universal gateway — all DBs through proxy, W2 index lifecycle
**Next session**: Implement D092 (W1+W2); then #250 NE episodic-to-semantic merge; #256 Tailscale
**In-flight**: D092 W1+W2 — about to queue for Worker

---

## Session 2026-03-16c+d
**Theme**: D095 lists table implemented end-to-end; identity graph + format conversion design started
**Decisions**: D095 (implemented), D096 (defined), D097 (defined), D098 (defined)
**Key changes**:
- D095 fully implemented: lists table in cortex (list_set/get/remove/all), Registry:Tags seeded, Project:TheIgors FACTUAL memory + lists.projects, runner.py git_log/find_tickets/list_projects, CC habits CC_GIT_LOG/CC_FIND_TICKETS/CC_LIST_PROJECTS — all verified live via bridge
- D096 defined: .now file convention — ~/.TheIgors/{instance}/pipelines/{name}/state.now; file mtime IS the timestamp
- D097 defined: EN↔CSB↔DSB conversion habits — CONV:ROOT interpretive entry, prompt templates as PROCEDURAL memories, chunked_pipeline primitive; full design pending Akien vision
- D098 defined: identity graph — PERSON:* nodes + lists.identity fast-path + IDENTITY:ROOT traversal; contacts-style; full design pending Akien vision
**Next session**: Hear Akien's broader identity/vision; then design+implement D097+D098
**In-flight**: Akien about to share broader vision for identity graph before D097/D098 design finalizes

---

## Session 2026-03-16e
**Theme**: Sphere model vision — cloud of small graph trees, TWM as global workspace, D099
**Decisions**: D099
**Key changes**:
- Sphere model crystallized: cloud of small graph trees; any node valid entry; roots are hubs not gates; roots are high-degree nodes, not required gateways
- TWM = global workspace (Baars GWT arrived at via introspection): multiple slots (<7), parent_obs_id branching, NE comparison via shared action_pointer overlap, incoherent slot decay
- Semantic similarity upgrade path: graph traversal (not embeddings) — already demonstrated in word graph, not yet wired for memory nodes
- Build order: D099 (TWM) → D098 (identity graph) → D097 (conversion habits) → D096 (pipeline primitive)
**Next session**: Implement D099 — TWM slot branching + NE comparison pass
**In-flight**: NONE — vision complete, ready to build

---

## Session 2026-03-16k
**Theme**: G-EMB1 + G-WG4 — performance plan approved, ready to implement
**Decisions**: (none new — gap definition + plan approval)
**Key changes**:
- Slow query report analyzed: db_queries.log persists across reboots
- G-EMB1 identified: memories.embedding is 16KB JSON inline → cold scan 64-164ms despite _MEM_COLS_NO_EMBED; fix: move to memory_embeddings table + batch Phase 2 fetches
- G-WG4 identified: wg_cooccur predict_next cold keys still 263ms p50; fix: covering index (word_a, word_b, score) eliminates table page I/O on 29M-row table
- Both gaps defined in decisions_log.dsb, plan approved
**Next session**: Implement G-WG4 first (word_graph.py + live DB), then G-EMB1 (cortex.py migration + code changes)
**In-flight**: G-EMB1 + G-WG4 — plan approved, no code written yet

---

## Session 2026-03-16n
**Theme**: Housekeeping + design notes banked before OS update
**Decisions**: none new — operational conventions + design notes
**Key changes**:
- GitHub Actions installed (accidental /install-github-app): claude.yml (@claude trigger) + claude-code-review.yml (auto PR review); ANTHROPIC_API_KEY set as GH secret; pulled + pushed clean
- Convention saved: "commit" = add+commit+pull+push full cycle (matches gitcommitandpush)
- Boredom design note: milieu too settled for too long → "go learn something" → drain_learn_queue; repetition variant = low word graph activation entropy
- Reading metrics: real pages/hour (not chunks) for ingestion capacity planning — Akien expects significant scaling of reading volume
- On Intelligence (Hawkins) added to learn_queue — Igor requested it himself; drain_learn_queue running, 2 processes active, Igor approaching 10,000 memories
- PROC_TASK_SUPPRESS_STALE misfire: fired on new reading assignment, suppressed it — concrete evidence for T-habit-audit-pipeline
- Future vision noted: Claude Code training run for Igor — boundary between what Igor can do vs Claude Code shifts after graph densifies
**Next session**: Slow query log review post G-EMB1/G-WG4; Watcher design (/workstep); boredom trigger implementation; reading metrics instrumentation
**In-flight**: NONE — OS update tonight, clean break

---

## Session 2026-03-16l
**Theme**: G-EMB1 + G-WG4 shipped; D103 (no-turn pipeline) + D104 (The Watcher) crystallized
**Decisions**: D103, D104; gaps closed: G-EMB1, G-WG4
**Key changes**:
- `cortex.py`: `memory_embeddings` table; `_get_or_compute_embedding` reads new table; `_get_embeddings_batch` (batch Phase 2); `search()` Phase 2 uses batch; `backfill_embeddings` LEFT JOIN
- `migrate_emb1.py`: one-time migration; 5531 embeddings moved; `memories.embedding` NULLed; VACUUM 185MB→95MB
- `word_graph.py` `_SCHEMA`: `idx_wgc_covering ON wg_cooccur(word_a,word_b,score)`; applied live; EXPLAIN confirms COVERING INDEX
- D103 defined: pipeline is continuous always; "turn" is LLM API artifact; no commit points
- D104 defined: The Watcher — high-salience search result = new pipeline event; graph tree in same substrate; Zen witness pattern; grows with experience
**Next session**: Design The Watcher concretely (graph tree structure, salience threshold, how search result re-injects as pipeline event); interval measurement framework (typical_interval=500ms baseline)
**In-flight**: D103+D104 defined only — no implementation started; Watcher design is next
**Use case saved**: PROC_READING_DEPOSIT as template for habit-audit-pipeline. Turn-based framing: "do not escalate to cloud to think about what I just read" — a prohibition at a turn boundary. Pipeline framing: reading chunk arrives → G54 deposits → move on; cloud only fires if Watcher-level high-salience event surfaces from the deposit. Same behavior, expressed as pipeline events not turn rules. This is the rewrite pattern for T-habit-audit-pipeline.

---

## Session 2026-03-16m
**Theme**: Watcher design elaborated — seed categories, emergence mechanism, habit audit queued
**Decisions**: D104 elaborated (no new D-numbers)
**Key changes**:
- D104 fleshed out: Igor's Watcher seed categories = Language, Self-modification (programming/AI/neurology/psychology), Culture
- New root nodes emerge from gradient accumulation of co-occurrence patterns crossing density threshold — not manually seeded
- Archive = activation decay, not deletion (old interest trees stay cold but accessible)
- Language is substrate/prerequisite, not just a category — improvements propagate across all trees
- T-habit-audit-pipeline queued: early habits use turn-based framing (PROC_READING_DEPOSIT as template example), rewrite needed after D103/D104 implementation
- Blog post "Language of Optimization Narrative" deposited to Igor DB
- Slow query log review deferred to next session
**Next session**: Review slow query log post G-EMB1/G-WG4; then autonomous Watcher implementation (word_graph cluster promotion + pipeline re-injection hookup)
**In-flight**: Watcher design approved for autonomous implementation — word_graph cluster density scan, named root promotion, seed category deposit, pipeline hookup in main loop

---

## Session 2026-03-16f
**Theme**: P1 complete — CC savestate ops now route through Igor bridge, not bash
**Decisions**: (none new — P1 implementation of existing decisions)
**Key changes**:
- `tools/ops.py` (new): store_decision, store_session_note, queue_task — Igor-native savestate ops
- `tools/__init__.py`: ops added to import list
- 4 CC habits seeded: CC_STORE_DECISION, CC_STORE_SESSION, CC_QUEUE_TASK, CC_CREATE_TICKET
- All verified live via bridge; this savestate was first to use CC_STORE_SESSION through Igor
- Priority list established: P1=Claude operational, P2=cognition (D096-D099), P3=everything else
**Next session**: D099 — TWM slot branching (parent_obs_id) + NE comparison pass (action_pointer intersection)
**In-flight**: NONE
