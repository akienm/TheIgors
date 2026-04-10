# TheIgors Audit Report — 2026-03-17

---

## PART 1: Runtime File Placement

### Misplaced Files (candidates for moving)

#### Source tree leakage — files that should never be in ~/TheIgors/

| Current path | Correct location | Written by | Risk |
|---|---|---|---|
| `/home/akien/TheIgors/igor.db` | `~/.TheIgors/` (already has one) | Unknown — empty file (0 bytes), likely an old accidental `touch` | LOW — empty, tracked in git, just clutter |
| `/home/akien/TheIgors/memory/igor.db` | `~/.TheIgors/Igor-wild-0001/` or deleted | Unknown origin, non-empty (64KB) | MEDIUM — DB in repo, gitignored by `*.db` but misleading |
| `/home/akien/TheIgors/memory/claude_budget.db` | `~/.TheIgors/Igor-wild-0001/` | budget.py | MEDIUM — DB in repo, gitignored by `*.db` |
| `/home/akien/TheIgors/6894.log` | `~/.TheIgors/logs/` | Likely a PID log from a process (6894 = process ID) | LOW — gitignored by `*.log`, stale (2026-03-10) |
| `/home/akien/TheIgors/wild_igor/koboldcpp_calls.log` | `~/.TheIgors/logs/` | KoboldCpp reasoner (now removed from source); log path was `os.path.join(__file__, "..", "..", "..", "koboldcpp_calls.log")` — hardcoded relative to source dir | LOW — gitignored, stale (last entry 2026-03-06), KoboldCpp reasoner no longer in codebase |
| `/home/akien/TheIgors/wild_igor/ollama_calls.log` | `~/.TheIgors/logs/` | `cognition/reasoners/ollama_reasoner.py` line 65: `_LOG_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "..", "ollama_calls.log")` — **hardcoded relative to `__file__`**, resolves to `wild_igor/` | MEDIUM — active bug: every Ollama call writes into source tree. Gitignored but dirty. Fix: use `paths().logs / "ollama_calls.log"` |
| `/home/akien/TheIgors/wild_igor/logs/discord.log` | `~/.TheIgors/logs/` | `network/discord_bot.py` or similar — writes to `wild_igor/logs/` which is inside source dir | LOW — gitignored, but the `wild_igor/logs/` directory itself is inside the source tree |
| `/home/akien/TheIgors/wild_igor/igor_memory.db` | `~/.TheIgors/Igor-wild-0001/` | Pre-PathManager artifact. Earlier code used a hardcoded relative path next to `wild_igor/`. Now orphaned (0 bytes active DB is at `Igor-wild-0001/wild-0001.db`) | LOW — gitignored, stale (2026-03-07), safe to remove |

#### JSON state files in source tree

| Current path | Status |
|---|---|
| `/home/akien/TheIgors/workspace/hamlet_akiendelllinux_gemma3_1b.json` | **Tracked in git** — benchmark result artifact, not config. Should be gitignored or moved to `~/.TheIgors/lab/benchmarks/results/` |
| `/home/akien/TheIgors/.claude.json` | **Tracked in git** — Claude Code project config (`{"dangerouslySkipPermissions": true}`). Reasonable to track, but exposes permission flag publicly. Low risk for a private repo. |
| `/home/akien/TheIgors/.claude/settings.local.json` | **Tracked in git** (1295 bytes). The filename says "local" — typically machine-specific settings should not be committed. Check if it contains any secrets or machine-specific paths. |
| `/home/akien/TheIgors/lab/benchmarks/results/bench_2026-03-09_13-14-42.json` | Benchmark output — fine in repo if intentional, but `benchmarks/results/` should probably be gitignored |

---

### Files Needing Decision (placement ambiguous per three-tier model)

The three-tier model (per CLAUDE.md) is:
- **machine-global**: `~/.TheIgors/local/` — machines.json, cluster config
- **database-global**: `~/.TheIgors/` root — word_graph.db, generation_graph.db, milieu_global.json, learn_queue.json, SOUL.md, cache/
- **instance-local**: `~/.TheIgors/Igor-wild-0001/` — wild-0001.db, .env, jobs/, logs/, warm_context, arbiter/

Items at `~/.TheIgors/` root that need placement decisions:

| File/Dir | Current | Question |
|---|---|---|
| `~/.TheIgors/learn_queue.json` (80KB, active) | runtime root | Database-global (shared across instances of same instance_id) OR instance-local? Currently at root per `paths().learn_queue`. Multiple instances would race on the same queue. Should probably be `paths().instance / "learn_queue.json"` for true multi-instance safety. |
| `~/.TheIgors/drain_learn_queue.pid` | runtime root | Same question — should be instance-local since drain runner is per-instance. |
| `~/.TheIgors/SOUL.md` | runtime root | `paths().soul` writes here. This is database-global (shared identity). But if multi-instance, two instances would overwrite each other. Intentional? |
| `~/.TheIgors/book_learner_progress/` | runtime root | Not in PathManager. Created by book_learner.py. Should this be `~/.TheIgors/local/book_learner_progress/` (machine-global shared) or instance-local? |
| `~/.TheIgors/cc_channel/` | runtime root | CC→Igor queue. Instance-local or machine-global? |
| `~/.TheIgors/logs/` | runtime root | Top-level logs vs `Igor-wild-0001/logs/` — two separate log dirs exist. `paths().logs` points to top-level. `Igor-wild-0001/logs/` also exists. Which is canonical? |
| `~/.TheIgors/training_corpus/` | runtime root | Word graph training data — machine-global makes sense (shared corpus). Not in PathManager; unclear if orphaned. |
| `~/.TheIgors/generation_graph.db` (82MB) | runtime root | `paths().word_graph("generation_graph")` correctly puts this here. But per three-tier: is the generation graph database-global or instance-local? If two Igor instances ran simultaneously they'd share it. |
| `~/.TheIgors/claude_bridge_history.json` | runtime root | Not in PathManager. Written by `claudecode/claude_bridge.py`. Should be in `~/.TheIgors/Igor-wild-0001/` or `cc_channel/`. |

---

### Corrupt / Bug-Artifact Files at Runtime Root

These files in `~/.TheIgors/` indicate active bugs:

| File | Problem | Likely cause |
|---|---|---|
| `<wild_igor.igor.memory.db_proxy.DatabaseProxy object at 0x738594f2c410>.db` (×4 files, 2026-03-16 15:16–15:19) | SQLite files named after Python object repr strings — `sqlite3.connect()` was called with `str(some_proxy_object)` as the path argument | Happened during D102/D092 DatabaseProxy debugging session. The files are 53KB (initialized but empty SQLite DBs). The bug is resolved (files are stale artifacts), but the 4 files remain and should be deleted. |
| `word_graph.db.db` (57KB, 2026-03-16 18:40) | Double `.db` extension — `paths().word_graph("word_graph.db")` appends `.db` to a name that already ends in `.db` | Likely caused by passing the Path `word_graph.db` to `WordGraph(name=path.stem, ...)` where `path.stem` = `"word_graph.db"` instead of `"word_graph"`. `Path("word_graph.db").stem == "word_graph"` is correct, but if someone passed the full filename as the `name` parameter directly, the `.db` appended twice. Stale artifact, safe to delete. |

---

### Stale Empty DBs at Runtime Root

| File | Size | Date | Status |
|---|---|---|---|
| `~/.TheIgors/cortex.db` | 0 bytes | 2026-03-05 | Pre-PathManager artifact. Stale, safe to delete. |
| `~/.TheIgors/igor.db` | 0 bytes | 2026-03-06 | Stale, safe to delete. |
| `~/.TheIgors/memory.db` | 0 bytes | 2026-03-05 | Stale, safe to delete. |
| `~/.TheIgors/wild-0001.db` | 0 bytes | 2026-03-11 | Stale — live DB is at `Igor-wild-0001/wild-0001.db`. Safe to delete. |
| `~/.TheIgors/igor_memory.db` | 49KB | 2026-03-07 | Pre-PathManager artifact. Inspect before deleting (may have early memories). |
| `~/.TheIgors/tmpokmnptpg.db` | 53KB | 2026-03-10 | Temp file — likely created during a test. Safe to delete. |
| `~/.TheIgors/igor_wild-0001/` | directory | 2026-03-09 | Hyphenated name vs underscore — **typo variant of `Igor-wild-0001`**. Contains stale `igor.db`, `milieu.json`, `response_habituation.json`. No code references this hyphenated path. Orphaned directory, safe to remove after inspection. |
| `~/.TheIgors/wild-0001/` | directory | 2026-03-17 (active!) | Another naming variant — contains active `consolidation_checkpoint.json`, `inbox/`, `outbox/`. This appears to be a second instance-dir that's being written to by some process. Source of confusion — paths.py uses `Igor-wild-0001` not `wild-0001`. |

---

### Misplaced Files at Home Root (~/)

| File/Dir | Status |
|---|---|
| `~/igor_notes_from_akien.md` | Pre-repo artifact (2026-02-25). Early design notes. Should be in `~/TheIgors/papers/history/_archive/` or deleted. Not in repo. |
| `~/igor_self_notes.md` | Pre-repo artifact (2026-02-24). Igor's own boot notes from before the runtime split. Should be in repo history or `~/.TheIgors/Igor-wild-0001/boot_notes.md`. Not in repo. |
| `~/chrome_igor_profile/` | Chrome profile for Igor — runtime artifact, correct to be at home root. OK. |
| `~/TheIgorsProject/` | Separate older directory (2026-03-04). Contains setup scripts. Looks like a precursor to the current repo. Could be archived. |

---

### Hardcoded Instance Names in Source

| File:Line | Hardcoded string | Problem |
|---|---|---|
| `tools/google_contacts.py:179,220` | `Path.home() / ".TheIgors" / "Igor-wild-0001" / "wild-0001.db"` | Bypasses PathManager entirely. If instance ID changes (e.g. `--id wild-0002`), this path will be wrong. Fix: use `paths().instance / "wild-0001.db"` |
| `tools/cluster_ssh.py:31` | `_DEFAULT_USER = "Igor-wild-0001"` | SSH username hardcoded. This is a system user not an instance ID, so it may be intentional. Still worth noting — if a different deployment uses a different username, this breaks. |
| `tools/cluster_ssh.py:203` | `igor_user = os.getenv("WINDOWS_USER_IGOR_USER", "Igor-wild-0001")` | Same as above — has an env override, so lower risk. |
| `tools/google_calendar.py:11` | Doc comment only: `~/.TheIgors/Igor-wild-0001/google_credentials.json` | Comment only, not code. Low priority. |
| `tools/ebook_reader.py:14` | Doc comment only: `~/.TheIgors/Igor-wild-0001/reading_state.json` | Comment only. The actual code uses PathManager. |
| `cognition/job_manager.py:10,90` | Doc comments only | Low priority. |
| `cognition/response_habituation.py:8` | Doc comment only | Low priority. |
| `main.py:904` | `"~/.TheIgors/Igor-wild-0001/ for backup files."` | Error message only — cosmetic issue. |
| `arbiter/queue.py:5` | Doc comment only | Low priority. |
| `cognition/pipeline_manager.py:21` | Doc comment only (notes the env override) | Low priority. |

**Active code violations (must fix):** `google_contacts.py` lines 179 and 220.

---

### Confirmed OK

- `~/.TheIgors/word_graph.db` (4GB) — correct per `paths().word_graph("word_graph")`.
- `~/.TheIgors/milieu_global.json` — correct per `paths().milieu`.
- `~/.TheIgors/SOUL.md` — correct per `paths().soul`.
- `~/.TheIgors/Igor-wild-0001/` directory and all contents — correct instance dir.
- `~/.TheIgors/local/` — correct machine-global dir.
- `~/.TheIgors/cache/` — correct per `paths().cache`.
- `~/.TheIgors/drain_learn_queue.pid` — at root per PathManager. Placement is debatable (see "needs decision") but consistent with current code.
- `~/TheIgors/igor` executable launcher at repo root — intentional, this is the entry point.
- `~/TheIgors/superclaude` and `superclaude.bat` — intentional launchers.

---

## PART 2: Repo Cleanliness

### Orphaned / One-Shot Scripts

All 37 `seed_*.py` scripts in `claudecode/` are one-shot DB population scripts. They are tracked in git and were presumably run once to populate the live DB. Most are safe to archive — they remain valuable as documentation of what was seeded and in case a DB needs to be rebuilt from scratch.

**Known broken / do-not-run (per CLAUDE.md):**

| Script | Status |
|---|---|
| `claudecode/seed_resource_gate_habits.py` | **Do not re-run.** PROC_RESOURCE_AWARENESS trigger contains "memory" — causes misfire on memory questions. Fixed in live DB only. |

**Migration scripts (one-shot, already run):**

| Script | Status |
|---|---|
| `claudecode/migrate_emb1.py` | G-EMB1 migration — move inline embeddings to `memory_embeddings` table. Already run (D102 commit landed). Safe to archive. Has "safe to re-run" annotation. |
| `claudecode/migrate_sqlite_to_postgres.py` | One-shot SQLite→Postgres migration. Has "One-shot" in header. Not yet run (Postgres migration is deferred). Keep until migration is executed. |

**Other one-shot / non-reusable scripts that could be archived:**

| Script | Likely status |
|---|---|
| `claudecode/consolidate_memories.py` | Memory consolidation runner — could be a utility or one-shot |
| `claudecode/eval_preparse.py` | Evaluation harness, likely one-shot testing tool |
| `claudecode/phrase_regression.py` | Regression test harness — likely one-shot |
| `claudecode/run_review_audit.sh` + `review_audit.md` | Audit artifacts — the `.md` is 2026-03-09, could be stale |
| `claudecode/launch_overnight_reading.py` | Launcher script — one-shot / operational |
| `claudecode/retrain_word_graph.py` | Retraining utility — operational tool, keep |
| `claudecode/push_restart.py` (34 lines) | Small operational utility — keep |

**Recommendation:** Create a `claudecode/archive/` subfolder and move all `seed_*.py` scripts there with a `README` noting they've been run and the live DB is the source of truth. Keep `migrate_sqlite_to_postgres.py` at top level until it's executed.

---

### Stale Docs

| Path | Status |
|---|---|
| `design_docs/subsystem_*.md` (6 files, last modified 2026-03-14) | **Superseded by `design_docs_for_igor/subsystem_*.dsb`** (last modified 2026-03-16). The `.dsb` versions are newer and are the format Igor reads. The `.md` files are the human-readable precursors. They may still serve as Akien-facing docs. Decision needed: keep for humans or delete as superseded. |
| `design_docs/DesignDecisions.md` (115 lines, 2026-03-14) | Self-describes as a summary pointing to `decisions_log.dsb`. Has value as a human entry point. Not superseded but the `.dsb` has the canonical content. |
| `design_docs/WorkingWithClaude.md` | Likely superseded by `thoughts/working_with_claude.md` (same topic). Check for overlap. |
| `thoughts/fixes_log.md` | Started 2026-03-11. Contains FIX-001 and FIX-002. These may have been resolved. Should be checked and either closed out or converted to GitHub issues. |
| `thoughts/reading_log.md` | Reading activity log — may have been superseded by the `reading_state.json` runtime file and ebook_reader system. |
| `history/_archive/*.csb.txt` | Early design conversations (Feb 2026). Permanently archived — OK as-is. |
| `history/*.csb.txt` | 5 files, research notes from March 2026. Active reference material for now. |
| `hosted_igor/hosted_igor.txt` | 1 text file describing hosted Igor concept. 2026-02-XX era. Likely an early concept doc. Low value. |

---

### Dead Code / Wrong-Location Files

| File | Status |
|---|---|
| `wild_igor/igor/cognition/multi_upstream.py` (3 lines) | **Shim only.** Re-exports from `multi_cloud.py`. The file comments say "Renamed to multi_cloud.py." This shim preserves old imports. Could be removed once all callers are confirmed to use `multi_cloud`. Check if anything still imports `multi_upstream` — if nothing does, remove. |
| `wild_igor/igor/tools/openrouter_reasoner.py` | **Tool, not a reasoner.** Despite the name, this is a registered tool (list_upstream_models, compare_upstream_costs) distinct from `cognition/reasoners/openrouter_reasoner.py`. It is imported via `tools/__init__.py` line 17. Not dead code, but the name collision with `cognition/reasoners/openrouter_reasoner.py` is confusing. Consider renaming to `tools/upstream_models.py`. |
| `wild_igor/igor/memory/scrub.py` (66 lines) | Small file. Check if it's imported anywhere. Purpose unclear from name alone. |
| `wild_igor/igor/cognition/prefrontal_cortex.py` (40 lines) | Very small for a module with this name. It re-exports from `judgments.py`. May be a thin shim layer or stub. |
| `wild_igor/igor/cognition/boredom.py` | Imported in `main.py` line 3075 (inside a conditional block). Live code. |
| `wild_igor/igor/cognition/observer.py` | Imported in `main.py` line 52. Live code. |
| `wild_igor/igor/cognition/relay.py` | Imported in `main.py` line 58. Live code. |
| `wild_igor/igor/cognition/judgments.py` | Imported via `prefrontal_cortex.py`. Live code. |
| `wild_igor/igor/tools/training.py` | Check if imported — could be a utility from the training corpus work |
| `wild_igor/igor/tools/want_tracker.py` | Referenced in MEMORY.md. Live code. |
| `wild_igor/igor/tools/watchlist.py` (70 lines) | Small. Check usage. |
| `wild_igor/igor/network/discord_bot.py` | Live — Discord integration |
| `wild_igor/igor/network/listener.py` | Live — network listener |
| `wild_igor/igor/dashboard/terminal.py` | Live — terminal dashboard |
| `benchmarks/benchmark.py` (large) | Benchmarking framework (#138). Not imported by Igor. A standalone tool. The `__pycache__` leaked here — should be gitignored. |
| `workspace/hamlet_test.py` | **Tracked in git** — test harness script. This is a development artifact that should be in `claudecode/` or gitignored, not in `workspace/`. |
| `workspace/hamlet_akiendelllinux_gemma3_1b.json` | **Tracked in git** — benchmark result. Should be gitignored or moved to `~/.TheIgors/lab/benchmarks/results/`. |
| `memory/sessions.md` | **Tracked in git** — active session log (17KB, updated 2026-03-17). This is runtime state (session history). It's in a `memory/` dir in the source repo alongside `igor.db` and `claude_budget.db`. Unclear why this is here rather than in `~/.TheIgors/Igor-wild-0001/` or just in `design_docs/`. |
| `change_request.txt` | **Tracked in git** — contains deferred GitHub gap tickets (G58, G59). This is a process artifact. The content belongs in GitHub issues or `design_docs/gap_analysis.md`, not as a tracked file at repo root. |
| `change_request_response.txt` | **Tracked in git** — contains `"# No active change request."` (28 bytes). This is a runtime state file that got committed. Should be gitignored. |

---

### __pycache__ / .pyc in Git

**The `__pycache__` directories and `.pyc` files are NOT tracked in git** — confirmed via `git ls-files`. The `.gitignore` rule `__pycache__/` and `*.pyc` are working. However, the directories exist on disk (12 of them outside venv):

```
/home/akien/TheIgors/lab/benchmarks/__pycache__
/home/akien/TheIgors/lab/claudecode/__pycache__
/home/akien/TheIgors/wild_igor/igor/cognition/__pycache__
/home/akien/TheIgors/wild_igor/igor/cognition/reasoners/__pycache__
/home/akien/TheIgors/wild_igor/igor/brainstem/__pycache__
/home/akien/TheIgors/wild_igor/igor/network/__pycache__
/home/akien/TheIgors/wild_igor/igor/dashboard/__pycache__
/home/akien/TheIgors/wild_igor/igor/web/__pycache__
/home/akien/TheIgors/wild_igor/igor/tools/__pycache__
/home/akien/TheIgors/wild_igor/igor/arbiter/__pycache__
/home/akien/TheIgors/wild_igor/igor/memory/__pycache__
/home/akien/TheIgors/wild_igor/igor/__pycache__
```

These are normal Python runtime artifacts — not a git problem, just disk clutter. The `.gitignore` is correctly excluding them.

**Note:** The `claudecode/__pycache__` directory contains `.pyc` files for `drain_learn_queue`, `eval_preparse`, and `seed_self_observation_habits` — these are from running those scripts directly. Normal behavior.

---

### .gitignore Gaps

Current `.gitignore` (12 lines):
```
venv/
wild_igor/.env
wild_igor/data/
wild_igor/workspace/
__pycache__/
*.pyc
*.db
*.bak
*.log
.env
.aider*
```

**Missing patterns that would prevent future accidents:**

| Missing pattern | Why needed |
|---|---|
| `*.pid` | `drain_learn_queue.pid` and similar PID files will never be in source |
| `*.lock` | `milieu_global.lock` and similar lock files |
| `warm_context*.json` | Instance state files |
| `change_request*.txt` | Already leaked into git; new pattern to prevent future recurrence |
| `workspace/` (at root level) | `workspace/hamlet_test.py` and `workspace/hamlet_akiendelllinux_gemma3_1b.json` are tracked — the workspace dir at repo root is not gitignored |
| `memory/*.db` | The `memory/` dir at repo root has `.db` files — `*.db` pattern should catch these, but `memory/sessions.md` (not a `.db`) is committed intentionally |
| `benchmarks/results/` | Benchmark output JSONs shouldn't be tracked |
| `.claude/settings.local.json` | Machine-specific Claude Code settings — shouldn't be committed |
| `benchmarks/__pycache__/` | Covered by `__pycache__/` but the subdirectory rule only applies if at root; may need `**/__pycache__/` |

**Patterns that DO work (confirmed by `git check-ignore`):**
- `*.db` correctly excludes `memory/igor.db`, `memory/claude_budget.db`, `igor.db`
- `*.log` correctly excludes `6894.log`

---

### Repo Root Clutter

Items at `~/TheIgors/` root that are unexpected or worth reviewing:

| Item | Status |
|---|---|
| `igor.db` (0 bytes, tracked) | Empty DB at repo root — stale artifact, should be gitignored (already is) and deleted |
| `6894.log` (134 bytes) | PID-numbered log file — stale artifact from 2026-03-10. Gitignored. Cleanup: delete |
| `change_request.txt` (tracked) | Should not be at repo root — move to `design_docs/` or close into GitHub issues |
| `change_request_response.txt` (tracked, 28 bytes) | Runtime state file committed — gitignore and delete |
| `memory/` directory | Runtime DBs and `sessions.md` at repo root — a `memory/` dir in a source repo that holds live DBs is confusing. Consider removing; `sessions.md` belongs in `design_docs/` or `~/.TheIgors/Igor-wild-0001/` |
| `workspace/` directory | Contains `hamlet_test.py` (tracked) and `hamlet_akiendelllinux_gemma3_1b.json` (tracked). Dev artifacts at repo root — gitignore and archive to `~/.TheIgors/lab/benchmarks/` |
| `superclaude.bat` (38 bytes) | Windows launcher stub — reasonable to have, low risk |
| `SYSTEM_PACKAGES.md` | System dependency list — fine at repo root |
| `docs/glossary.md` | Glossary — fine, but overlaps with `design_docs_for_igor/glossary.dsb`. One of these is redundant. |

---

## Summary

Top 10 things to address, prioritized by impact:

### Priority 1 — Active bugs / data integrity

1. **`ollama_reasoner.py` writes logs into source tree** (`wild_igor/ollama_calls.log`). Line 65 uses `os.path.join(__file__, "..", "..", "..", "ollama_calls.log")` — a relative path from `__file__` that resolves inside the repo. Fix: replace with `str(paths().logs / "ollama_calls.log")`. This is the same class of bug that the D108 PathManager cutover was meant to eliminate, but `ollama_reasoner.py` was missed.

2. **`google_contacts.py` hardcodes instance path** (lines 179, 220): `Path.home() / ".TheIgors" / "Igor-wild-0001" / "wild-0001.db"`. Bypasses PathManager. If Igor is ever run with `--id wild-0002` or `IGOR_INSTANCE_ID` override, contacts writes to the wrong DB. Fix: use `paths().instance / "wild-0001.db"`.

3. **`~/.TheIgors/wild-0001/` is receiving active writes** (consolidation_checkpoint dated 2026-03-17). This hyphenated-name directory is not the canonical instance dir (`Igor-wild-0001`). Something is writing to the wrong path. Investigate which process is creating `wild-0001/` as an instance dir — possibly the igor launcher with `--id wild-0001`.

### Priority 2 — Cleanup required (safe to do now)

4. **Delete 4 DatabaseProxy object-repr `.db` files** at `~/.TheIgors/`. Stale test artifacts from 2026-03-16 D102 debugging. Delete: `~/.TheIgors/<wild_igor.igor.memory.db_proxy.DatabaseProxy object at ...>.db` (×4). Also delete `word_graph.db.db`.

5. **Delete empty/stale DB files** at `~/.TheIgors/`: `cortex.db`, `igor.db`, `memory.db`, `wild-0001.db` (all 0 bytes). Also inspect `igor_memory.db` (49KB, 2026-03-07) before deleting — it may hold early memories from before the path split.

6. **Remove committed runtime artifacts from git**: `change_request.txt`, `change_request_response.txt`, `workspace/hamlet_test.py`, `workspace/hamlet_akiendelllinux_gemma3_1b.json`. Then gitignore the patterns.

### Priority 3 — .gitignore hardening

7. **Add missing `.gitignore` patterns**: `*.pid`, `*.lock`, `change_request*.txt`, `workspace/`, `benchmarks/results/`, `.claude/settings.local.json`. This prevents the same leakage from happening again.

### Priority 4 — Documentation consolidation

8. **Decide fate of `design_docs/subsystem_*.md` files**: These are the human-readable precursors to the `.dsb` files. The `.dsb` versions are newer (2026-03-16 vs 2026-03-14). If the `.md` files aren't being maintained in sync, they will mislead. Either: (a) delete and point humans to `.dsb`, (b) generate `.md` from `.dsb` as exports, or (c) accept that `.md` = stable human doc and `.dsb` = Igor-facing fast reference with different update cadences.

9. **Archive `seed_*.py` scripts** to `claudecode/archive/` with a note: "These were run once. The live DB is the source of truth. Re-run only if rebuilding the DB from scratch." Keep them in git for DB rebuild capability, just move them out of the top-level `claudecode/` to reduce noise. Mark `seed_resource_gate_habits.py` as `DO_NOT_RERUN_broken.py`.

### Priority 5 — Longer term

10. **Multi-instance safety for `learn_queue.json` and `drain_learn_queue.pid`**: Both are at `~/.TheIgors/` root (shared across all instances). If a second Igor instance is run, they will race on the same queue and PID file. PathManager should move these to `paths().instance / "learn_queue.json"` and `paths().instance / "drain_learn_queue.pid"`. The `wild-0001/` directory situation (item 3) suggests this multi-instance confusion is already causing real problems.
