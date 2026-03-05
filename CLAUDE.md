# TheIgors — Claude Code Working Conventions

## What This Project Is
Igor is a Python AI agent with persistent SQLite memory, running on akiendelllinux.
- Repo: https://github.com/akienm/TheIgors
- Main agent code: `wild_igor/igor/`
- DB: `wild_igor/data/wild-0001.db` (SQLite, ~1400+ memories)
- venv: `venv/` (Python 3.12)
- Launch: `igor` bash alias (loops on exit code 42 = restart)

## Developer Conventions

### Before editing
- Read the file first. Never overwrite blindly.
- Check inertia level — HIGH files need strong justification.
- Check `design_docs/` for relevant architecture decisions.

### Inertia levels (self-edit resistance)
| Level | Files | Convention |
|---|---|---|
| HIGH (0.90+) | `brainstem/`, `memory/models.py`, `cognition/reasoners/base.py` | Require arbiter approval; never edit casually |
| MEDIUM | `cognition/`, `memory/cortex.py`, `anthropic.py`, `main.py` | Discuss before editing |
| LOW | `tools/`, `dashboard/`, `thalamus.py` | Freely improvable |

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

### Key env vars (in `wild_igor/.env`)
- `IGOR_DB_PATH` — defaults to `memory/igor.db` relative to CWD (wild_igor/)
- `OPENROUTER_API_KEY` — primary cloud inference
- `KOBOLDCPP_HOST` / `KOBOLDCPP_PORT` — local inference
- `IGOR_SELF_EDIT_ENABLED` — gates source file writes

### Reference docs
- `design_docs/` — architecture, decisions log, ethical framework, mission
- `history/` — research notes, early design conversations, archives
- `claudecode/CONTEXT.md` — fuller onboarding context for new sessions
- `wild_igor/igor/memory/models.py` — Memory dataclass, MemoryType enum
- `wild_igor/igor/cognition/` — thalamus, NE, milieu, interruptors, job_manager

### Do not
- Move or rename `brainstem/` contents without Akien review
- Store credentials in memory (use `.env` + CREDENTIAL_REF memory pattern — see #71)
- Delete `wild_igor/data/wild-0001.db` — that's the live DB
- Delete `wild_igor/memory/claude_budget.db` — that's the spend history
