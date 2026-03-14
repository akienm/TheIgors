# TheIgors — Claude Code Working Conventions

## What This Project Is
Igor is a Python AI agent with persistent SQLite memory, running on akiendelllinux.
- Repo: https://github.com/akienm/TheIgors
- Main agent code: `wild_igor/igor/`
- DB: `~/.TheIgors/igor_wild_0001/wild-0001.db` (runtime, not in repo)
- .env: `~/.TheIgors/igor_wild_0001/.env` (never committed)
- venv: `/home/akien/TheIgors/venv/` (Python 3.12)
- Launch: `igor` bash alias (loops on exit code 42 = restart)
- Source/runtime split: `~/TheIgors/` = source; `~/.TheIgors/` = all runtime data

## Developer Conventions

### Before editing
- Read the file first. Never overwrite blindly.
- Check inertia level — HIGH files need strong justification.
- Check `design_docs/` for relevant architecture decisions.

### Workflow discipline
- Get plan approval before executing (full philosophy: `thoughts/working_with_claude.md`)
- Test against live systems, not mocks; forensic logging everywhere

### Inertia levels (self-edit resistance)
| Level | Files | Convention |
|---|---|---|
| HIGH (0.90+) | `brainstem/`, `memory/models.py`, `cognition/reasoners/base.py` | Discuss with Akien; never edit casually |
| MEDIUM | `cognition/`, `memory/cortex.py`, `anthropic.py`, `main.py` | Discuss before editing |
| LOW | `tools/`, `dashboard/`, `thalamus.py`, `cognition/word_graph.py` | Freely improvable |

### Commit policy
- Claude Code edits do NOT auto-commit — commit manually at logical checkpoints.
- Igor's own self-edits DO auto-commit+push via `self_edit.py`.
- Never `--no-verify` or force-push main.

### Instance data location
All runtime instance data lives in `~/.TheIgors/igor_wild_0001/`:
- `jobs/` — background job state
- `arbiter/` — pending arbiter queue
- `warm_context.*.json` — session context
- `logs/` — forensic logs
- `inbox/`, `outbox/`, `workspace/` — instance working dirs

### Key env vars (in `~/.TheIgors/igor_wild_0001/.env`)
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
- `design_docs/` — architecture, decisions log, ethical framework, mission
- `history/` — research notes, early design conversations, archives
- `claudecode/CONTEXT.md` — fuller onboarding context for new sessions
- `wild_igor/igor/memory/models.py` — Memory dataclass, MemoryType enum
- `wild_igor/igor/cognition/` — thalamus, NE, milieu, interruptors, job_manager

### Key architecture (fast ref)
- **Word graph**: `cognition/word_graph.py` — in-memory two-tier memory; words + bigram chunks; same weights for parsing (habit scoring) and generation (predict_next). Cache: `~/.TheIgors/word_graph.json`.
- **CC→Igor bridge**: `POST http://localhost:8080/api/cc_send` with `{"content": "..."}` — injects as author "claude-code"
- **Tier ladder**: tier.1 habit → tier.2 KoboldCpp → tier.3 OR cheap → tier.3.5 OR haiku → tier.4 OR sonnet → tier.5 Anthropic direct (inhibited) → tier.6 arbiter alert

### End-of-session savestate (REQUIRED)
Run `/savestate`. It's not optional — skipping means the next session starts blind. Full checklist: `.claude/skills/savestate/SKILL.md`

### Do not
- Move or rename `brainstem/` contents without Akien review
- Store credentials in memory (use `.env` + CREDENTIAL_REF memory pattern — see #71)
- Delete `~/.TheIgors/igor_wild_0001/wild-0001.db` — that's the live DB
- Edit `.env` without noting what changed and why
