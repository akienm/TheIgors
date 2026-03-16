# TheIgors — Claude Code Working Conventions

## What This Project Is
<!-- last-updated: 2026-03-13a -->
Igor is a Python AI agent with persistent SQLite memory, running on akiendelllinux.
- Repo: https://github.com/akienm/TheIgors
- Main agent code: `wild_igor/igor/`
- DB: `~/.TheIgors/igor_wild_0001/wild-0001.db` (runtime, not in repo)
- .env: `~/.TheIgors/igor_wild_0001/.env` (never committed)
- venv: `/home/akien/TheIgors/venv/` (Python 3.12)
- Launch: `igor` bash alias (loops on exit code 42 = restart); visible terminal: `DISPLAY=:0 konsole -e bash -c "igor" &` (add `; exec bash` to keep terminal open after crash)
- Source/runtime split: `~/TheIgors/` = source; `~/.TheIgors/` = all runtime data
- **Environment split (CRITICAL)**: Claude Code always runs with the REAL Anthropic key (`REAL_ANTHROPIC_API_KEY`). Igor's `.env` sets OR routing (`ANTHROPIC_BASE_URL=openrouter`, `ANTHROPIC_API_KEY=OR key`) — this does NOT affect Claude Code. `superclaude` and `cc.sh` handle the key swap. Never read Igor's `.env` and assume it reflects the Claude Code environment.

## Developer Conventions
<!-- last-updated: 2026-03-15c -->

### Before editing
- Read the file first. Never overwrite blindly.
- Check inertia level — HIGH files need strong justification.
- Check `design_docs/` for relevant architecture decisions.

### Workflow discipline
- Get plan approval before executing (full philosophy: `thoughts/working_with_claude.md`)
- Test against live systems, not mocks; forensic logging everywhere
- Two-session pattern: Designer Claude (architecture + conversation) + Worker Claude (execution); queue at `~/.TheIgors/cc_channel/queue.json`; Worker boot doc: `claudecode/WORKER_CONTEXT.md`

### Inertia levels (self-edit resistance)
<!-- last-updated: 2026-03-13a -->
| Level | Files | Convention |
|---|---|---|
| HIGH (0.90+) | `brainstem/`, `memory/models.py`, `cognition/reasoners/base.py` | Discuss with Akien; never edit casually |
| MEDIUM | `cognition/`, `memory/cortex.py`, `anthropic.py`, `main.py` | Discuss before editing |
| LOW | `tools/`, `dashboard/`, `thalamus.py`, `cognition/word_graph.py` | Freely improvable |

### Commit policy
<!-- last-updated: 2026-03-13a -->
- Claude Code edits do NOT auto-commit — commit manually at logical checkpoints.
- Igor's own self-edits DO auto-commit+push via `self_edit.py`.
- Never `--no-verify` or force-push main.

### Instance data location
<!-- last-updated: 2026-03-13a -->
All runtime instance data lives in `~/.TheIgors/igor_wild_0001/`:
- `jobs/` — background job state
- `arbiter/` — pending arbiter queue
- `warm_context.*.json` — session context
- `logs/` — forensic logs
- `inbox/`, `outbox/`, `workspace/` — instance working dirs

### Key env vars (in `~/.TheIgors/igor_wild_0001/.env`)
<!-- last-updated: 2026-03-13a -->
- `IGOR_DB_PATH` — path to live SQLite DB
- `OPENROUTER_API_KEY` — primary cloud inference
- `KOBOLDCPP_HOST` / `KOBOLDCPP_PORT` — local inference
- `IGOR_SELF_EDIT_ENABLED` — gates source file writes
- `IGOR_TIER5_ENABLED` — gates Anthropic direct spend (default false)
- `IGOR_ARBITER_ENABLED` — human-approval queue (default false — disabled)
- `IGOR_CALL_COST_WARN_USD` — per-call cost cap (default 2.00)
- `IGOR_MAX_TURNS` — max agentic tool turns per call (default 8)
- `IGOR_RESEARCH_MODE` — allow bulk external reads (default false)
- `OPENROUTER_CHEAP_MODEL` — tier.3 model (gpt-4o-mini)
- `OPENROUTER_DEFAULT_MODEL` — tier.3.5 model (haiku)
- `OPENROUTER_INTERACTIVE_MODEL` — tier.4 model (sonnet)

### Reference docs
<!-- last-updated: 2026-03-15c -->
- `design_docs/` — architecture, decisions log, ethical framework, mission
- `history/` — research notes, early design conversations, archives
- `claudecode/CONTEXT.md` — fuller onboarding context for new sessions
- `wild_igor/igor/memory/models.py` — Memory dataclass, MemoryType enum
- `wild_igor/igor/cognition/` — thalamus, NE, milieu, interruptors, job_manager
- `design_docs_for_igor/capabilities_index.dsb` — 118-tool inventory (check before asking "can Igor do X?")
- `design_docs_for_igor/decisions_log.dsb` — all architectural decisions D001-D076

### Key architecture (fast ref)
<!-- last-updated: 2026-03-15b -->
- **Word graph**: `cognition/word_graph.py` — SQLite-backed two-tier; words + bigram chunks; same weights for parsing (habit scoring) and generation (predict_next).
- **CC→Igor bridge**: `POST http://localhost:8080/api/cc_send` with `{"content": "..."}` — injects as author "claude-code"
- **Tier ladder**: tier.1 habit → tier.2 KoboldCpp → tier.3 OR cheap → tier.3.5 OR haiku → tier.4 OR sonnet → tier.5 Anthropic direct (inhibited) → tier.6 arbiter alert
- **Habit types**: threshold | action | workflow | delegation | reactive | response | question | context_inject | cognitive | tool | passive_capture
- **Intent gate (D074)**: threshold/workflow/delegation/reactive habits skip when parsed_intent is question-like

### End-of-session savestate (REQUIRED)
<!-- last-updated: 2026-03-15c -->
Run `/savestate`. It's not optional — skipping means the next session starts blind. Full checklist: `.claude/skills/savestate/SKILL.md`
Savestate now includes **Step 0: current hypothesis** — one sentence about what was in-flight and why.

### Compact Instructions
<!-- last-updated: 2026-03-13a -->
When `/compact` runs (manually or automatically), preserve:
- List of open gaps (Gxx) touched this session
- Files modified this session and what changed
- Current debugging hypothesis or in-progress task
- Any decisions made that haven't been saved to design_docs yet
- Next session priorities

### Do not
<!-- last-updated: 2026-03-13a -->
- Move or rename `brainstem/` contents without Akien review
- Store credentials in memory (use `.env` + CREDENTIAL_REF memory pattern — see #71)
- Delete `~/.TheIgors/igor_wild_0001/wild-0001.db` — that's the live DB
- Edit `.env` without noting what changed and why

## Known Broken / Do Not Touch
<!-- last-updated: 2026-03-15c -->
Items that are intentionally deferred or known broken. Do not flag these as bugs or attempt to fix without discussion.

- **`claudecode/seed_resource_gate_habits.py`**: PROC_RESOURCE_AWARENESS trigger contains "memory" — causes misfire on memory questions. Fixed in live DB only. Do not re-run seed script until trigger is updated. Track: gap_analysis.md.
- **`IGOR_TIER5_ENABLED=false`**: tier.5 (Anthropic direct) intentionally inhibited to prevent runaway spend. Re-enable only when 4090 arrives or explicit decision.
- **`IGOR_ARBITER_ENABLED=false`**: human-approval queue disabled. Re-enable when arbiter UI is built.
- **KoboldCpp**: currently not running; tier.2 falls through to tier.3 OR. Not broken, just idle.
