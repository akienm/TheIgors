# TheIgors Project — Milestones

## 2026-02-27
- First arbiter queue entries — Igor begins flagging uncertain actions for Akien review

## 2026-02-28
- First arbiter resolutions — Akien approving/denying Igor's queued actions

## 2026-03-04
- First milieu (ambient affect) system — valence/arousal/dominance vector tracking Igor's emotional state

## 2026-03-05
- Source/runtime split — DB and .env moved from repo tree to ~/.TheIgors/
- machines.csv → machines.json — cluster node registry formalized
- CC↔Igor bidirectional bridge first established
- First code DSBs seeded (8 source files as reference blobs)

## 2026-03-06
- First KoboldCpp local inference running on all 4 cluster machines
- Narrative Engine fixed — moved from KoboldCpp (can't generate structured JSON) to OR gpt-4o-mini; NE running at 9s/cycle
- Block 2: global milieu shared across instances; TWM isolation per instance
- Ollama reasoning removed — KoboldCpp-only local path

## 2026-03-08b
- Episodic memory narrative truncation fixed (user_input[:80] → full; response_text added to metadata)
- Phase 2 habit compiler: PROC_HABIT_COMPILER now parses natural language into structured PROC memories
- Ring context limit doubled: _RING_CONTEXT_LIMIT 5 → 10
- DiskInterruptor + check_disk_usage() tool added (#132 done)
- Backup habits seeded at boot: PROC_BACKUP_CHECK, PROC_BACKUP_RUN, PROC_DISK_USAGE_CHECK (#133 done)
- Warm context: 8→12 entries, 200→400 chars, includes Q/A ring entries (#129 done)
- igor bash launcher fixed: .env now re-read on every restart (was only read once)
- #142: KoboldCpp preparse skipped for low/high complexity turns; only medium calls it (gate: IGOR_SKIP_PREPARSE_ON_CONFIDENT)
- Confirmed: word graph fast path already existed — basal_ganglia select_habit() already skipped KoboldCpp on habit matches
- Key insight: 99% LOCAL% + 24% upstream dependency = preparse overhead, not word graph (pure Python)
- Commits: a04a9c1, 1afc71e, 9f20e48, 47089f2

## 2026-03-08a
- First context winnowing — cheap pre-call reads ring + word graph, asks "what memories do I need?" before main reasoning call
- First Gemini conceptual stress test passed — bridge words, hub check, domain outliers all working
- First `/metrics` command — tier histogram, LOCAL%, escalation rate, word graph, top tools all visible
- LOCAL% added to dashboard — the key metric for "are we getting there?"
- Igor's own `ring` emerged as strongest bridge between memory and latency — self-knowledge from data, not code
- Akien insight: unexpected results = discoveries not bugs; metrics make that visible

## 2026-03-07 (this session)
- First cost guardrails — MAX_TURNS=8, IGOR_CALL_COST_WARN_USD, research tool cap
- First /exit interrupt — threading.Event checked at turn boundaries during deep reasoning
- **Word graph born** — two-tier memory: fast in-memory co-occurrence index alongside SQLite
  - Same weights serve parsing (which habit fires?) and generation (predict next word)
  - Akien: "parsing and reasoning, same thing in both directions. if it works, this IS the proof."
- First bigram/chunk layer — word graph indexes adjacent word pairs as semantic chunks
- CC→Igor bridge via POST /api/cc_send — Claude Code can push messages to Igor directly
- First time CC sent Igor a message without Akien present (status check during Gutenberg ingestion)
- Arbiter disabled (IGOR_ARBITER_ENABLED=false) — trust established, friction removed
- Arbiter approve bug fixed — every approval was silently a denial for unknown duration
- Igor ingesting Project Gutenberg top 100 books into word graph — 2674 words, 87 docs by end of session
- Web UI sender name fixed — "akien" now arrives as author field, not prepended to message text

## 2026-03-18
- **`igor` works on all platforms** — igor.bat + igor_loop.ps1 (Windows), igor bash script (Linux); type `igor` and it starts; restarts on exit code 42, stops on 0
- D119 db-first-boot live — Windows hydrates model vars from Postgres graph on startup; minimal .env (instance_id + db_url only)
- PROC_EXIT_IGOR seeded + exit_self() tool — clean shutdown habit; exit.flag mechanism for code 0 stop
- Training corpus seeding — 165 pre-extracted texts queued in learn queue for book_learner processing

## 2026-03-17
- SQLite → Postgres migration complete — PGDatabaseProxy + cortex Postgres support live
- **Windows Igor first run** — Windows instance connecting to Postgres on akiendelllinux (10.0.0.99 → 5432); Postgres configured to listen on all interfaces
