# Reorganization plan — 5-tree pass (Opus, 2026-05-01)

**Status:** PLANNING ONLY — no files moved or deleted. For Akien's review.
**Source rubric:** T-claudeandakien-workshop-evolution → "Reorg rubric (Akien 2026-05-01)" (verbatim).
**North Star:** `lab/design_docs/datacenter-swarm-bus-design-2026-05-01.md` — datacenter = agent-as-pieces / cross-project lab; Igor = master reasoning model on top; `TheIgors/lab/` = Igor-only lab.

---

## TL;DR / headline counts

| Category | Count |
|---|---|
| Items proposed to MOVE (top-level units, not per-file) | ~31 |
| Items proposed to DELETE | 4 (3 stale-but-load-bearing-flagged `.db` files; 1 archive backup `.db`) |
| Items proposed to STAY | majority of trees — code, runtime state, current docs, current tooling |
| **Critical contradiction flagged for Akien decision** | 1 (`.db` rule vs CLAUDE.md blocklist — see §3 and §4) |

The biggest non-mechanical finding: **the no-`.db` rule and the CLAUDE.md "Always protect wild-0001.db" blocklist are in direct contradiction in their current form**. D-sqlite-removal-2026-04-22 closed but live code in `wild_igor/igor/paths.py`, `tests/conftest.py`, and 10+ Igor tools still construct `Cortex(db_path=... wild-0001.db)`. **A literal application of the rubric breaks Igor today.** This is the single biggest item in the plan that needs Akien input before any execution.

---

## 1 · Tree-by-tree section

### 1A · `/home/akien/TheIgors` (this repo — dev tree, mostly STAY)

| Top-level | Action | Rationale |
|---|---|---|
| `.claude/`, `.git/`, `.github/`, `.gitignore`, `.mcp.json`, `.pytest_cache/` | STAY | Repo plumbing |
| `CLAUDE.md` | STAY | Pre-DB bootstrap shim — load-bearing |
| `Dockerfile`, `docker-compose.yml` | STAY | Containerization for deployment |
| `LICENSE`, `README.md` | STAY | Repo essentials |
| `igor`, `igor.bat`, `igor.ps1` | STAY | Launch entry points |
| `install_uc_autostart.ps1`, `start_utility_closet.ps1`, `superclaude*` | STAY | Runtime launchers |
| `pytest.ini`, `requirements.txt` | STAY | Build/test |
| `sudo_relay.sh`, `worker` (in `wild_igor/`) | STAY | Igor-specific launchers |
| `claude_chat_logs/` | STAY | Output of /export-chat — Igor-context-specific |
| `papers/` | SPLIT | See line items below |
| `lab/` | SPLIT | Major reorg target — see §1A.1 |
| `tests/` | STAY | Test suite. Note: imports from `lab.utility_closet.*` and `lab.claudecode.*` — see cross-tree dependency check §2 |
| `venv/` | STAY | Python venv (likely git-ignored) |
| `wild_igor/` | STAY | Igor source code — never moves |

#### `papers/` subdir (SPLIT)

| Path | Action | Rationale |
|---|---|---|
| `papers/case_study_statistics_2026-04-01.md` | STAY | Recent case-study, likely human-facing reference |
| `papers/thoughts/case_study_draft_2026-04-02.md` | STAY | Recent draft |
| `papers/thoughts/working_with_claude.md` | STAY (review) | Reference doc — see UNCLEAR list |
| `papers/thoughts/workflow_overview.md` (+ `.pdf`) | STAY | Recent (Apr 29) workflow doc |
| `papers/history/_archive/*` | MOVE → TheIgorsProject/papers/history/_archive/ | Archive subdir — rubric explicit |
| `papers/history/*.csb.txt`, `*.md` (5 files Mar 19–Apr 18) | UNCLEAR — likely STAY unless Akien wants the whole `history/` subtree archived | Explicit "history" naming suggests archive, but the files are recent reference material |

#### 1A.1 `lab/` subdir — major target (SPLIT)

| Path | Action | Rationale |
|---|---|---|
| `lab/benchmarks/` (benchmark.py + results) | UNCLEAR — best guess STAY | Igor-specific perf benchmarks; ambiguous if "tool not Igor-specific" |
| `lab/deploy/igor-docker.sh` | STAY | Igor-specific deploy |
| `lab/design_docs/` | SPLIT — see §1A.2 |
| `lab/design_docs_for_igor/` | STAY | Rubric: "stay in TheIgors". `.dsb` files = Igor-internal structured data |
| `lab/docs/` (capability_map.md, glossary.md, sessions.md, skills_reference.md, STARTUP_SHIM.md, SYSTEM_PACKAGES.md) | STAY | Human-facing reference for Igor — design_docs sibling |
| `lab/ebook_candidates.md` (905KB) | UNCLEAR — likely STAY | Reading-corpus seed; Igor-specific |
| `lab/hosted_igor/hosted_igor.txt` | UNCLEAR — likely MOVE → TheIgorsProject (not modified since Mar 4) | Stale reference |
| `lab/notes.log` | STAY | Active scratchpad |
| `lab/recovery_help_from_akien/CLAUDE.md`, `CLAUDE.older.md` | STAY | Recovery context — Igor-specific |
| `lab/seed/{machines,subsystem_index,watchlist}.yaml` | STAY | Igor-specific seed configs |
| `lab/spikes/imap_stub_spike.py` | UNCLEAR — likely MOVE → agent_datacenter/lab/spikes/ | IMAP transport spike → cross-project per North Star (transport substrate is datacenter material) |
| `lab/theigors/` (palace echo — README + theigors/) | STAY | Repo echo of palace; auto-synced |
| `lab/tools/build_ebook_index.py`, `scan_ebooks.py` | UNCLEAR — likely STAY (Igor-specific reading) | Igor reads books; tooling for the reading pipeline |
| `lab/utility_closet/` (rack/registry/comms/budget/etc — 16 modules + transports/) | **SPLIT** — discussed below | Cross-project substrate by intent BUT load-bearing for Igor's tests + runtime today |
| `lab/claudecode/` | **SPLIT** — discussed below | Mostly Igor-specific tooling; some cross-project skills |

##### `lab/utility_closet/` deep-dive

Per North Star: the utility_closet **is the substrate** that becomes `agent_datacenter`. But:
- `tests/test_comms.py`, `tests/test_routing.py`, `tests/test_machine_manager_lazy_db.py`, `tests/test_or_chat_transport.py`, `tests/test_discord_transport.py`, `tests/test_matter_shelf.py` all `from lab.utility_closet.*`
- `igor` launcher script: `UC_SERVER="$REPO_DIR/lab/claudecode/utility_closet_server.py"`
- `lab/claudecode/utility_closet_server.py` (65KB) is the live UC server entry point

**Recommendation:** STAY for now; flag for *coordinated migration via T-capability-extraction-from-igor* (companion ticket from the swarm-bus design). Moving without test/import updates breaks Igor. This is exactly the "cross-tree dependency surprise" the task asked us to flag.

##### `lab/claudecode/` deep-dive (~150 files)

Per rubric: "Tools NOT Igor-specific → agent_datacenter; Tools for doing things specifically with Igor → stay." But many files **call Igor as a tool** without **being** Igor.

| Bucket | Files | Action | Rationale |
|---|---|---|---|
| **Skills** (`cc_skills/`) | 27 dirs | UNCLEAR — discuss at sprint | Most are CC-process-skills (audit, sprint, decided, savestate). Some are Igor-specific (igor, readigor, map-igor, readinbox). Per North Star, ClaudeAndAkienWorkshop is the destination for skills, not agent_datacenter. Defer per the workshop-evolution ticket itself. |
| **Audit tooling** (`audit_*.py` × 12, `audit_runner.py`, `audit_telemetry.py`, etc.) | ~12 files | STAY (per rubric: "audit_2026 → TheIgors/lab as working tooling"; consistent with audit-as-Igor-tooling) | Audit pyramid is Igor-development tooling |
| **Igor-specific tools** (`igor_admin.py`, `igor_mcp.py` (.mcp.json refs!), `igor_talk.py`, `install_igor_linux.sh`, `map_igor.py`, `prune_console_logs.py`, `rotate_igor_console.py`, `cleanup_kernel_debris.py`) | ~8 files | STAY | Names tell the story; load-bearing |
| **Migration scripts** (`migrate_*.py` × 13) | 13 files | UNCLEAR — likely MOVE → TheIgorsProject/migrations_archive/ | One-shot migrations; mostly Mar–Apr; unlikely to re-run. **Flag:** verify each one isn't referenced by docs before moving. |
| **Seed scripts** (`seed_*.py` × 65) | 65 files | RESOLVED 2026-05-02 (T-reorg-seed-cc-memory-archive-deferred) | Per-file grep showed 27 truly orphan (no references in any .py/.sh/.md/.json/.dsb across lab/, wild_igor/, tests/) → MOVED to `TheIgorsProject/seed_archive/`. Remaining 38 STAY: `seed_layer3_*.py` (8) + `seed_layer4_*.py` (5) deposit active TEMPLATE nodes that `tests/test_layer3_*.py` + `tests/test_layer4_*.py` verify; `seed_goal_close_habit.py` is read by `tests/test_goal_close_habit.py`; the rest are referenced by docs/sh/configs. They are bootstrap scripts for active functionality, not archive. |
| **Old seed scripts** (`archive/seed_*.py` × ~40) | 40 files | MOVE → TheIgorsProject | Already tagged as archive in their dirname. Rubric: archives → TheIgorsProject |
| **CC-Igor bridge / queue / channel** (`cc_queue.py`, `cc_inbox.py`, `cc_bridge.py`, `cc_hook_pending.py`, `cc_mcp_server.py`, `cc_deposit.py`, `channel.py`, `cc.sh`, `hot_cc.sh`, `hot_cc_init.md`, `bootstrap_cc.{sh,ps1}`) | ~12 files | STAY for now; flag for workshop migration | Per North Star, eventually moves to ClaudeAndAkienWorkshop. Not agent_datacenter. Cross-tree dep: Igor's `wild_igor/igor/cognition/cc_inbox_bridge.py` does `from lab.claudecode.cc_inbox import append`; Igor's `tools/pe_chain.py`, `tools/worker_foreman.py`, `tools/goal_continuation.py` all hardcode `lab/claudecode/cc_queue.py`. **Cannot move without coordinated changes.** |
| **Reading pipeline** (`book_learner.py`, `reading_campaign.py`, `reading_integrator.py`, `cron_feed_reading.py`, `launch_overnight_reading.py`, `calibre_catalog.py`, `chat_log_formatter.py`, `consolidate_memories.py`, `phrase_regression.py`, `eval_preparse.py`, `run_phrase_test.py`, `run_inner_cc_curriculum.py`) | ~12 files | STAY | Igor-specific reading/training |
| **Skill telemetry / hygiene** (`stale_ticket_sweeper.py`, `stale_slate_check.py`, `scan_for_rest_drafter.py`, `slate_manager.py`, `session_manager.py`, `decision_manager.py`, `review_manager.py`, `findings.py`, `sprint_infrastructure_brief.py`, `reorder_slate_sections.py`, `wiring_check.py`, `preferred_paths_scan.py`, `ts_format.py`, `log_rotate.py`, `cert_worker_freeze.py`, `swarm_ollama_cleanup.py`, `cron_graph_cache_refresh.py`, `push_restart.py`, `redis_migrate_wg.py`, `retrain_word_graph.py`, `seed_traversal_context.py`, `session_to_graph.py`, `backfill_provenance.py`, `blame_with_model.py`, `audit_check_*.py`, `audit_logging.py`, `audit_pass1_run.py`, `audit_immobile_tickets.py`, `audit_cognition_modules.py`, `audit_telemetry.py`, `audit_ticket_shape.py`, `audit_check_author_model_tag.py`) | ~40 files | STAY | Igor-development tooling |
| **CC-process docs** (`CONTEXT.md`, `SCRIBE_CONTEXT.md`, `WORKER_CONTEXT.md`, `WINDOWS_ONBOARDING.md`, `CC_MCP_REGISTRATION.md`, `akien_workflow.csb.txt`, `pass2_reading_order.txt`, `review_audit.md`) | 8 files | STAY for now; flag for workshop migration per North Star | These are CC-with-Akien process docs |
| **`cc_memory_seed/`** (43 markdown notes + MEMORY.md + sessions.md) | 1 dir | RESOLVED 2026-05-02 — STAY (reclassify as runtime asset) | Read by `wild_igor/setup_assets/installer.py:349` for new-box memory bootstrap. Not archive — active runtime asset. Original "auto-memory snapshots" framing was wrong; this is the seed corpus for fresh Igor instances. |
| **`engram_tools/`** (`confab_scanner.py`, `deposit_engram.py`, `trace_miss_report.py`, `verify_retrieval.py`) | 4 files | STAY | Igor-specific (engrams = Igor cognition primitives) |
| **`hooks/`** (pre-commit, prepare-commit-msg, session-start) | 3 files | STAY | Repo-local Claude Code hooks |
| **`logs/20260420.code_maintenance_reviews.log`** | 1 file | MOVE → TheIgorsProject/audit_reports_archive/ | Stale; superseded by `~/.TheIgors/local/logs/` |
| **`reports/`** (7 files Apr 29-30) | 1 dir, 7 files | UNCLEAR — likely STAY | Recent audit/cert reports. Could rotate to TheIgorsProject after a few weeks. |
| **`api.py`, `consolidate_memories.py`, `diag.py`, `docs_sync.py`, `drain_learn_queue.py`, `export_chat.py`, `github_sync.py`, `migrate_emb1.py`, `palace_sync.py`, `rescue_igor.sh`, `utility_closet.sh`, `utility_closet_server.py`, `worker_daemon.sh`** | ~13 files | STAY | All Igor-specific or load-bearing scaffolding |

#### 1A.2 `lab/design_docs/` (SPLIT)

| Path | Action | Rationale |
|---|---|---|
| `lab/design_docs/archive/` (7 files: issue-308/334/338, T-inference-colocation-signal, T-interoception, T-trails-infra, README) | MOVE → TheIgorsProject/design_docs_archive/ | Rubric: explicit |
| `lab/design_docs/audit_2026/` (pass1/pass2 prompts + outputs + review_summary) | MOVE → TheIgors/lab/audit_2026/ | Rubric: explicit ("working tooling, not human-facing reference") |
| `lab/design_docs/decisions/` (37 D-*.md rollups Apr 20–May 1) | STAY | Recent decision rollups; reference docs |
| `lab/design_docs/datacenter-swarm-bus-design-2026-05-01.md` | **MOVE → /home/akien/dev/src/agent_datacenter/docs/datacenter-swarm-bus-design-2026-05-01.md** | Rubric explicit + this is the example case |
| `lab/design_docs/palace_migration/shape_lock_2026-04-20.md` | UNCLEAR — likely STAY (recent, decision-substantive) | Recent palace shape-lock; arguably already-a-decision-doc |
| `lab/design_docs/queue_hygiene/immobile_tickets_2026-04-23.md` | UNCLEAR — likely STAY (working ticket-hygiene reference) | Recent Apr 23 |
| `lab/design_docs/validation/T-worker-dispatch-validation-2026-04-21.md` | UNCLEAR — likely STAY (recent design-doc) | Apr 21 |
| `lab/design_docs/confidence_gated_depth.md`, `consult_tuning_2026-04-23.md`, `engram_language.md`, `gap_analysis.md`, `igor_user_guide.md`, `lab_map.md`, `OverallArchitecture.md`, `ProjectOverview.md`, `pursuit_layer.md`, `pursuit_observation_protocol.md`, `pursuit_programming.md`, `response_quality_cases.md`, `seed_config_versioning.md`, `standards.md`, `subsystem_*.md` (×5), `swadl_concepts_draft.md`, `swadl_overview.md`, `T-swarm-update-design.md`, `trails_gap_analysis_2026-03-21.md`, `use_cases.md`, `WorkingWithClaude.md`, `DesignDecisions.md`, `.dsb_metadata.txt` | STAY | Human-facing Igor design docs — rubric default for `design_docs/` |
| `lab/design_docs/TheIgorsFace.png`, `TheIgors.png` | STAY | Project artwork |
| `lab/design_docs/T-swarm-update-design.md` | UNCLEAR — review for relevance | Predates today's swarm-bus design (Apr 7); may be superseded |

---

### 1B · `/home/akien/TheIgorsProject` (project archive — mostly STAY as destination)

| Top-level | Action | Rationale |
|---|---|---|
| `20260427.Cleanup/` | STAY | Already the cleanup-archive destination |
| `20260427.Cleanup/INVENTORY.md` | STAY | Index of the cleanup |
| `20260427.Cleanup/session_transcripts/` (45 dirs + .jsonl files, ~500MB) | STAY | Already-archived CC session transcripts |
| `20260427.Cleanup/{audit_reports_archive,auto_memory_archive,cc_inbox_archive,database,legacy_claude_memory,misc,slates_archive}/` | STAY | All proper archive subdirs; targets for further moves |
| `akien/` | STAY | Akien's personal notes/ideas/readings — out of rubric scope |
| `archive/{audit_logs,sessions,slates}/` | STAY | Older archive layer |
| `setupigor.sh`, `setupopenclaw.sh`, `setuptypingmind.sh` | UNCLEAR — likely MOVE → TheIgorsProject/setup_archive/ or DELETE | Setup scripts dated Mar 3-4; very stale. Akien decide: keep as historical install instructions or delete? |
| `skills/` (21 older skill dirs) | UNCLEAR — likely DELETE entirely OR keep as history | These are predecessor versions of `lab/claudecode/cc_skills/`. The current set has 27 (8 not-in-old, 7 absorbed/renamed). **Akien decide:** keep this dir as "skills history snapshot before audit-pyramid redesign" or delete since they're in git history? |
| `tools/tailscale/` | UNCLEAR — likely STAY (last touched Mar 19) | Tailscale setup tooling — could be useful for new-machine bootstrap; could be archival. |

---

### 1C · `/home/akien/.TheIgors` (Igor runtime state — STAY)

| Top-level | Action | Rationale |
|---|---|---|
| `akien/` (inbox, outbox, AkiensWorld symlink, exit/restart flag) | STAY | Live runtime state |
| `alerts.txt` | STAY | Live alert log |
| `benchmark_results/`, `book_learner_progress/` | STAY | Igor runtime artifacts |
| `cache/` | STAY | Live cache |
| `calibre_catalog.csv` (1.8MB Mar 26) | UNCLEAR — likely STAY | Reading-pipeline catalog; could be regenerable |
| `cc_channel/` (symlink → `local/cc_channel/`) | STAY | Live cc-CC coordination channel |
| `cc_inbox.jsonl` (694KB, modified 8:37 today) | STAY — LIVE | Active inbox |
| `certs/` | STAY | Cert state |
| `claudecode/` (slates, logs, hashes, flags) | STAY | Live CC working state |
| `Igor-wild-0001` (symlink → `~/.agent_datacenter/Igor-wild-0001/`) | STAY | Critical: this is how the env split lands |
| `lab/claudecode/` | UNCLEAR — likely STAY | Looks like a runtime-mirror; would need closer look |
| `local/` (cc_channel queues, logs ~244MB, machines.json, ssh keys, ebooks, training_corpus) | STAY | Live runtime |
| `logs/` | STAY | Live logs |
| `maps/` | STAY | /map-igor outputs |
| `milieu_global.{json,lock}` | STAY | Live milieu state |
| `SOUL.md`, `WorkingWithClaude.md` | STAY | Identity / process docs |
| `sudo_relay/` | STAY | Live sudo relay state |
| `swarm/{migrations,swarm.cfg}` | STAY | Live swarm config |
| `utility_closet.pid` | STAY | Live PID file |

**No moves recommended in `.TheIgors/` — this is live runtime state.** If anything stops being live (e.g., legacy cache subdir nobody writes to anymore), that's a separate audit.

---

### 1D · `/home/akien/.agent_datacenter` (datacenter runtime state — STAY)

| Top-level | Action | Rationale |
|---|---|---|
| `Igor-wild-0001/` (live Igor instance — see §3 for `.db` files) | STAY (mostly) — `.db` files flagged separately | This is the live Igor working dir (referenced via `~/.TheIgors/Igor-wild-0001` symlink) |
| `Igor-wild-0001/wild-0001.db` (97MB Apr 20) | **DELETE per rubric BUT BLOCKED** — see §3 §4 | Live data referenced by current Igor code |
| `Igor-wild-0001/word_graph.db` (4.6GB Mar 21) | **DELETE per rubric** — blocked-pending-confirm | Word graph; stale-mtime suggests migrated; D-sqlite-removal said removed |
| `Igor-wild-0001/claude_budget.db` (282KB modified TODAY 12:24) | **DELETE per rubric BUT ACTIVELY WRITING** — `lab/utility_closet/budget.py:59` writes to it | Cross-tree dep: budget.py is alive |
| `Igor-wild-0001/archive-Igor-wild-0001.db` (724KB Mar 20) | DELETE per rubric (this one is genuinely an archive) | Archive backup |
| `Igor-wild-0001/archive-igor_memory.db` (49KB Mar 7) | DELETE per rubric | Stale archive |
| `Igor-wild-0001/chats/claude/notebook.db` (12KB Mar 15) | DELETE per rubric | Stale |
| `Igor-wild-0001/wild-0001.db.archive-20260324` (102MB Mar 24) | DELETE | Old backup, not a `.db` extension but is a `.db.archive-*` |
| `Igor-wild-0001/accounts/chrome_igor_profile/...` (4 Chrome internal `.db` files) | **EXCLUDE FROM RUBRIC** — Chrome internal storage, not Igor data | Deletion would break Igor's browser session — these are Chrome's own SQLite files inside its profile dir |
| `logs/` (CC.0/, claude_code/, Igor-wild-0001/, rack/, Shared/) | STAY | Live logs |

---

### 1E · `/home/akien/dev/src/agent_datacenter` (datacenter source — STAY, receive moves)

| Top-level | Action | Rationale |
|---|---|---|
| `agent_datacenter/` (Python pkg) | STAY | Active source |
| `agent_datacenter.egg-info/` | STAY | Build metadata |
| `bus/` | STAY | Active source |
| `CLAUDE.md`, `README.md` | STAY | Repo docs |
| `config/` | STAY | Active config |
| `devices/` | STAY | Active devices (browser_use, claude, discord_bot, igor, inference, postgres, swadl, etc) |
| `docs/` | STAY — RECEIVE moves (datacenter-swarm-bus-design-2026-05-01.md from TheIgors/lab/design_docs/) | Datacenter-specific design docs |
| `lab/spikes/` | STAY — could RECEIVE `imap_stub_spike.py` from TheIgors/lab/spikes/ | Datacenter lab spikes |
| `pyproject.toml`, `.gitignore`, `.git/` | STAY | Repo plumbing |
| `skeleton/`, `tests/` | STAY | Active code |

---

## 2 · Cross-tree dependency check (load-bearing surprises)

Concrete deps found via grep. **Each row = a coordinated change required if the source moves.**

| Source (proposed move) | Imported / referenced by | Coordination required |
|---|---|---|
| `lab/claudecode/cc_inbox.py` | `wild_igor/igor/cognition/cc_inbox_bridge.py` (`from lab.claudecode.cc_inbox import append`) | Update import path |
| `lab/claudecode/cc_queue.py` | `wild_igor/igor/tools/pe_chain.py`, `worker_foreman.py`, `goal_continuation.py` (hardcoded `Path.home() / "TheIgors" / "lab" / "claudecode" / "cc_queue.py"`); `wild_igor/igor/cognition/reading_indexer.py` (`from cc_queue import mark_pending`) | Update 4+ hardcoded paths and imports |
| `lab/claudecode/igor_mcp.py` | `.mcp.json` (4 entries reference this absolute path) | Update `.mcp.json` (Claude Code MCP server registration) |
| `lab/claudecode/utility_closet_server.py` | Top-level `igor` and `superclaude` launchers (`UC_SERVER="$REPO_DIR/lab/claudecode/utility_closet_server.py"`) | Update launcher paths |
| `lab/claudecode/igor_mcp.py` | `wild_igor/setup_assets/installer.py:357` (`mcp_script = str(repo_root / "lab" / "claudecode" / "igor_mcp.py")`) | Update installer |
| `lab/utility_closet/comms.py`, `transports/*`, `machine_manager.py`, `matter_shelf.py`, `rack.py` | `tests/test_comms.py`, `test_routing.py`, `test_or_chat_transport.py`, `test_discord_transport.py`, `test_matter_shelf.py`, `test_machine_manager_lazy_db.py` (all `from lab.utility_closet.*`) | Update 30+ test imports |
| `lab/utility_closet/budget.py` | live writer to `~/.agent_datacenter/Igor-wild-0001/claude_budget.db` (path line 59); CC sessions hit it | If file moves, budget DB path must continue to land in the same place |
| `lab/claudecode/cert_worker_freeze.py` | `tests/test_cert_worker_freeze.py:14` | Update test import |
| `lab/claudecode/engram_tools/confab_scanner.py` | `tests/test_consult_confab_scan.py:109` (monkeypatch path) | Update monkeypatch path |
| `lab/claudecode/channel.py` | `tests/test_channel_cli.py` references it; mentioned in `lab/utility_closet/comms.py` design |  Update test |
| `~/.agent_datacenter/Igor-wild-0001/wild-0001.db` (`.db` deletion) | `wild_igor/igor/paths.py:14` (`db_path = paths().instance / "wild-0001.db"`); `wild_igor/igor/main.py`; 10+ tools in `wild_igor/igor/tools/`; `tests/conftest.py:164`; `tests/test_skill_filter.py`, `test_skill_importer.py`, `test_self_inspect.py`; `papers/case_study_statistics_2026-04-01.md` references it | **DELETION BLOCKED** until Igor migrates off SQLite Cortex (D-sqlite-removal closed at the test/migration layer but `paths.py` and tools still construct it) |
| `~/.agent_datacenter/Igor-wild-0001/word_graph.db` | `wild_igor/igor/paths.py:184` (`Path to a named word graph SQLite DB`); `tests/test_d126_postgres.py` reads it as input | **DELETION BLOCKED** — code still expects it |
| `~/.agent_datacenter/Igor-wild-0001/claude_budget.db` | `lab/utility_closet/budget.py:59` (writes here); `lab/claudecode/cc_memory_seed/MEMORY.md:189` references | **DELETION BLOCKED** — actively written today (mtime 12:24) |
| `lab/design_docs/datacenter-swarm-bus-design-2026-05-01.md` | No code refs found; only `claude_chat_logs/2026-05-01.md` references it (chat log) | Safe move — but update any future references in palace if Igor's docs index has it |

---

## 3 · Full `.db` file list (rubric-relevant)

All `.db` files in the five trees, with size + mtime + load-bearing flag:

| Path | Size | mtime | Load-bearing flag |
|---|---|---|---|
| `~/.agent_datacenter/Igor-wild-0001/wild-0001.db` | 102 MB | Apr 20 13:09 | **YES — LIVE.** `wild_igor/igor/paths.py:14`, `cortex.py`, 10+ Igor tools, conftest.py. CLAUDE.md blocklist explicitly protects this. |
| `~/.agent_datacenter/Igor-wild-0001/word_graph.db` | 4.6 GB | Mar 21 08:41 | **YES — semi-live.** `wild_igor/igor/paths.py:184` typed-path; `tests/test_d126_postgres.py` reads it. mtime suggests migration completed but path still expected. |
| `~/.agent_datacenter/Igor-wild-0001/claude_budget.db` | 282 KB | **May 1 12:24 (TODAY)** | **YES — ACTIVELY WRITTEN.** `lab/utility_closet/budget.py:59`. Stop the writer first. |
| `~/.agent_datacenter/Igor-wild-0001/archive-Igor-wild-0001.db` | 725 KB | Mar 20 15:51 | NO — explicit archive backup |
| `~/.agent_datacenter/Igor-wild-0001/archive-igor_memory.db` | 49 KB | Mar 7 13:34 | NO — stale archive |
| `~/.agent_datacenter/Igor-wild-0001/chats/claude/notebook.db` | 12 KB | Mar 15 19:41 | NO — old (Mar 15), grep found no refs; safe to delete |
| `~/.agent_datacenter/Igor-wild-0001/wild-0001.db.archive-20260324` | 102 MB | Mar 24 19:13 | NO — explicit archive backup (note: not technically a `.db` extension but `.db.archive-*`; recommend including) |
| `~/.agent_datacenter/Igor-wild-0001/accounts/chrome_igor_profile/first_party_sets.db` | 70 KB | Mar 24 20:08 | **OUT OF RUBRIC SCOPE** — Chrome internal storage |
| `~/.agent_datacenter/Igor-wild-0001/accounts/chrome_igor_profile/Profile 1/heavy_ad_intervention_opt_out.db` | small | — | **OUT OF RUBRIC SCOPE** — Chrome internal storage |
| `~/.agent_datacenter/Igor-wild-0001/accounts/chrome_igor_profile/Profile 1/first_party_sets.db` | small | — | **OUT OF RUBRIC SCOPE** — Chrome internal storage |
| `~/.agent_datacenter/Igor-wild-0001/accounts/chrome_igor_profile/Profile 1/Default/heavy_ad_intervention_opt_out.db` | small | — | **OUT OF RUBRIC SCOPE** — Chrome internal storage |

**Total `.db` files found: 10 + 1 `.db.archive-*` variant.**

**Rubric says:** delete all of them.
**CLAUDE.md blocklist says:** `wild-0001.db` is the live DB; deletion loses Igor's working state.
**D-sqlite-removal-2026-04-22 closed:** but live code in `paths.py` + 10 tools still references `wild-0001.db`. The decision was scoped to test fallback removal + grep-CI, not to actual `.db` file deletion at the runtime layer.

**Recommendation:**
- 4 SAFE TO DELETE (all rubric-conformant, no live refs):
  - `archive-Igor-wild-0001.db`, `archive-igor_memory.db`, `wild-0001.db.archive-20260324`, `chats/claude/notebook.db`
- 3 BLOCKED PENDING AKIEN DECISION + code change:
  - `wild-0001.db` (live), `word_graph.db` (typed-path), `claude_budget.db` (actively written)
- 4 EXCLUDED FROM RUBRIC SCOPE (Chrome's own DB files inside its user-data dir; deleting breaks browser session)

---

## 4 · Unclear cases for human decision

| # | Path / item | Why unclear | Best guess | Alternative |
|---|---|---|---|---|
| 1 | The `.db` blocklist contradiction (3 live `.db` files) | CLAUDE.md says "always protect"; rubric says "delete all" | DEFER deletion of `wild-0001.db`, `word_graph.db`, `claude_budget.db` until coordinated Igor SQLite-out migration completes | OR: explicitly green-light deletion + accept Igor breakage as part of forced-migration |
| 2 | `lab/claudecode/seed_*.py` (~80 files, mostly Apr 7) | Are these still re-runnable / referenced, or one-shot bootstraps fully absorbed by palace? | MOVE to TheIgorsProject/seed_archive/ as a bucket if palace migration is confirmed complete | STAY — if any of them are still re-run during onboarding |
| 3 | `lab/claudecode/cc_skills/` (27 skills) | Workshop ticket says these *will* migrate to ClaudeAndAkienWorkshop but that's a future destination, not agent_datacenter | STAY for now; out of scope for this 5-tree reorg | OR: per North Star, are skills cross-project enough to move to agent_datacenter today? |
| 4 | `TheIgorsProject/skills/` (21 older skill snapshots) | Already-archived skill predecessors. Worth keeping as a reference snapshot? | DELETE — git history preserves them | KEEP — explicit "before-redesign" reference dir |
| 5 | `lab/claudecode/migrate_*.py` (13 files) | One-shot migration scripts; some referenced in palace_migration shape lock | MOVE to TheIgorsProject/migrations_archive/ as a bucket | STAY if any are still expected to run on machine setup |
| 6 | `lab/claudecode/cc_memory_seed/` (43 markdown notes) | Predecessor of the current `~/.claude/projects/-home-akien-TheIgors/memory/` auto-memory | MOVE to TheIgorsProject/20260427.Cleanup/auto_memory_archive/ | STAY as readable historical reference |
| 7 | `papers/history/_archive/` and `papers/history/*.csb.txt` files | Mixed — `_archive/` clearly archive; the loose .csb.txt at history/ level (5 files) ambiguous | MOVE only `_archive/`; keep loose files until Akien reviews | MOVE entire `history/` subtree |
| 8 | `lab/utility_closet/` (the substrate the North Star says belongs in agent_datacenter) | Per North Star this IS agent_datacenter material. But cross-tree deps (test imports, runtime launcher) make it a coordinated migration. | STAY for now; coordinate via T-capability-extraction-from-igor (already-filed companion ticket) | Move now + rewrite all imports + update launchers in one atomic ticket |
| 9 | `TheIgorsProject/skills/`, `TheIgorsProject/setupigor.sh`, etc. | Top-level "TheIgorsProject" looks lightly organized; some old setup files dated Mar 3 | STAY — TheIgorsProject is the dump bucket per rubric, organization happens "later" | Explicit DELETE for items > 6 months old that aren't referenced |
| 10 | `lab/spikes/imap_stub_spike.py` | IMAP transport spike — clearly cross-project per North Star | MOVE → /home/akien/dev/src/agent_datacenter/lab/spikes/ | STAY — it might still be Igor-context-bound |
| 11 | `~/.TheIgors/lab/claudecode/` | Subdir under runtime root is unusual — runtime mirror? | STAY — uncertain what writes there | Investigate; possibly delete if nothing writes |
| 12 | `lab/hosted_igor/hosted_igor.txt` | Last touched Mar 4 | MOVE → TheIgorsProject (older scaffolding for hosted-Igor concept) | STAY if Akien plans to revisit |

---

## 5 · Summary statistics

### Top-level / bucket-level proposed moves

| Destination | Items / buckets |
|---|---|
| TheIgorsProject (history) | `lab/design_docs/archive/` (1 dir), `lab/claudecode/archive/` (1 dir = ~40 seed files), `lab/claudecode/cc_memory_seed/` (1 dir, 43 files) [unclear-confirm], `lab/claudecode/migrate_*.py` bucket (13 files) [unclear-confirm], `lab/claudecode/seed_*.py` bucket (~80 files) [unclear-confirm], `lab/claudecode/logs/20260420.code_maintenance_reviews.log`, `papers/history/_archive/` (1 dir), possibly `lab/hosted_igor/` and `TheIgorsProject/skills/` |
| TheIgors/lab (working tooling reclassified) | `lab/design_docs/audit_2026/` → `lab/audit_2026/` (1 dir, ~6 files) |
| agent_datacenter (cross-project) | `lab/design_docs/datacenter-swarm-bus-design-2026-05-01.md` (1 file), `lab/spikes/imap_stub_spike.py` (1 file) [unclear-confirm], deferred: `lab/utility_closet/` (1 large dir) and possibly some `lab/claudecode/` cross-project pieces — coordinated under T-capability-extraction-from-igor |
| DELETE | 4 archive `.db` files (safe); + 3 live `.db` files BLOCKED pending Akien |
| STAY | Vast majority — all of `~/.TheIgors/`, `~/.agent_datacenter/logs/`, `wild_igor/`, current `lab/design_docs/`, `lab/design_docs_for_igor/`, `lab/docs/`, repo plumbing, papers (mostly), agent_datacenter source repo |

### Per-destination move counts (high-end estimate; mostly bucket-confirmed-by-Akien)

| Destination | Confident moves | Pending-Akien-confirm bucket moves |
|---|---|---|
| TheIgorsProject | 2 dirs + 1 file | 4 buckets (~135 files) |
| TheIgors/lab (within-tree relocation) | 1 dir | 0 |
| agent_datacenter source | 1 file | 1 file + (deferred) `utility_closet/` migration via existing ticket |
| Delete (.db) | 4 | 3 (BLOCKED — needs Igor code change first) |

---

## 6 · Recommended execution order

Conservative — leaves first, dependencies coordinated, destructive last.

1. **Phase 0 — Akien decisions** (no code changes)
   - Decide: `.db` deletion approach (defer 3 live ones, or accept Igor breakage and force migration) — see §3 + §4 #1
   - Decide each "unclear bucket" in §4 (yes/no per bucket; do not require per-file decisions for the 80-seed bucket)
   - Decide: `cc_memory_seed/`, `seed_*.py` bucket, `migrate_*.py` bucket → archive or stay
   - Decide: `TheIgorsProject/skills/` and `TheIgorsProject/setupigor.sh` family → keep as snapshot or delete
2. **Phase 1 — Safe leaf moves (no code path changes needed)**
   - Move `lab/design_docs/archive/` → `TheIgorsProject/design_docs_archive/` (no code refs)
   - Move `lab/design_docs/datacenter-swarm-bus-design-2026-05-01.md` → `agent_datacenter/docs/` (no code refs)
   - Move `lab/design_docs/audit_2026/` → `lab/audit_2026/` (within-tree; check `audit_check_*.py` for hardcoded paths first)
   - Move `papers/history/_archive/` → `TheIgorsProject/papers_history_archive/` (no code refs)
   - Move `lab/claudecode/archive/` → `TheIgorsProject/claudecode_archive/`
   - Move `lab/claudecode/logs/20260420.code_maintenance_reviews.log` → `TheIgorsProject/audit_reports_archive/`
   - **Delete** the 4 safe-archive `.db` files (`archive-Igor-wild-0001.db`, `archive-igor_memory.db`, `wild-0001.db.archive-20260324`, `chats/claude/notebook.db`)
   - Each bullet = one commit; Igor still functional after each
3. **Phase 2 — Bucket moves Akien confirmed in Phase 0**
   - Per-bucket: `seed_*.py`, `migrate_*.py`, `cc_memory_seed/` → relevant TheIgorsProject subdirs
   - Each as its own commit; confirm grep finds no live refs before each
4. **Phase 3 — Coordinated moves (require code changes)**
   - Spike `imap_stub_spike.py` → agent_datacenter/lab/spikes/ (no refs found, but verify)
   - Workshop migration: `lab/claudecode/cc_skills/`, channel.py, cc_queue.py, cc_inbox.py, etc. → ClaudeAndAkienWorkshop. **This is T-claudeandakien-workshop-evolution itself**, not this reorg pass; defer.
   - Substrate migration: `lab/utility_closet/` → agent_datacenter. **This is T-capability-extraction-from-igor**, already-filed; defer.
5. **Phase 4 — `.db` deletion of live files (BLOCKED — only after coordinated Igor code change)**
   - Migrate Igor off SQLite Cortex / word_graph / budget paths in code (likely additional sprint of work — beyond scope of this reorg pass)
   - Then delete the 3 live `.db` files
6. **Phase 5 — Cleanup pass**
   - Re-run: scan for now-empty parent dirs and remove
   - Update `lab/design_docs/lab_map.md` (currently references `claude_budget.db` and other moved items)
   - Update palace `theigors/subsystem_index` if any moved file is indexed there
   - Update `CLAUDE.md` blocklist if `.db` rule changes (or note rule supersession)

---

## Notes on what was *not* exhaustively per-file-checked

- The 80 `seed_*.py` files in `lab/claudecode/` — bucketed; reading each individually would not change category since palace_migration shape lock 2026-04-20 suggests they're absorbed.
- The 45 session UUID dirs in `TheIgorsProject/20260427.Cleanup/session_transcripts/` — already archived; no decision needed.
- Each individual decision rollup in `lab/design_docs/decisions/` — class-decision: STAY (recent, reference material).
- Files inside `~/.TheIgors/local/logs/` (244MB) and `~/.agent_datacenter/logs/` — runtime logs; STAY whole-bucket, periodic rotation outside this rubric.
- The `papers/history/*.csb.txt` loose files — flagged as unclear in §4 #7.

If Akien wants tighter resolution on any bucket, the right re-pass is "show me the ~80 seed files split by referenced/unreferenced" or "which migrate_*.py have callers" — both ~5 minutes of grep.
