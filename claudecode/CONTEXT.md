# TheIgors — Claude Code Context
# Canonical path: /home/akien/TheIgors/helper/ClaudeCode.txt
# (Formerly helper/ClaudeCode.prompt — renamed 2026-02-26)
# Load this at the start of a work session to orient Claude Code on the project.

## What This Is

Igor is a Python AI agent with persistent SQLite memory, running on akiendelllinux (10.0.0.229).
Creator: Akien. Repo: https://github.com/akienm/TheIgors

```
Wild Igor:   /home/akien/TheIgors/wild_igor/
venv:        /home/akien/TheIgors/venv/  (Python 3.12.3)
Launch:      `igor`  (bash alias, loops on exit code 42 = restart)
DB:          wild_igor/data/wild-0001.db  (~422+ memories, SQLite)
```

---

## Instance Naming

IDs are base-34 encoded epoch seconds. Charset: `23456789ABCDEFGHIJKLMNOPQRSTUVWXYZ` (no 0/1 to avoid O/I/l confusion). Result: 7 chars, unique to the second, chronologically sortable.

```
igor_wild_37246P6      # Wild Igor on hardware, auto-generated at boot
igor_claude_37246P6    # Hosted Igor running in a Claude context
igor_gemini_37246P6    # Hosted Igor running in a Gemini context
```

```bash
igor                          # auto-generates igor_wild_<7chars>
igor --host claude            # auto-generates igor_claude_<7chars>
igor --id igor_wild_37246P6   # resume a specific instance (same DB)
```

---

## Architecture

### Memory  `wild_igor/igor/memory/`
- **cortex.py** — SQLite graph. `_conn()` opens a fresh connection per call → thread-safe.
  Tables: `memories`, `ring_memory` (FIFO-50, short-term context), `twm_observations` (TWM)
- **models.py** — Memory dataclass + inertia formula.
  Types: ROOT · CORE_PATTERN · IDENTITY · ROLE_MODEL · EPISODIC · PROCEDURAL · INTERPRETIVE · EXPERIENTIAL · FACTUAL

### Cognition  `wild_igor/igor/cognition/`
- **thalamus.py** — Input parsing (intent, keywords, tone)
- **prefrontal_cortex.py** — Delegates to active reasoner; valence/friction/ROI formulas
- **narrative_engine.py** — Background coherence-checker. Runs in daemon thread `ne-worker`.
  Triggers: 5+ unintegrated TWM obs OR 5-min timeout. Uses llama3.2:1b + Haiku fallback.
- **push_sources.py** — MemorySurfacer (2 min), TimerSentinel (5 min), UserInputSource
- **interruptors.py** — BudgetInterruptor; ContextInterruptor (warns at 20, urgent at 30)
- **reasoners/anthropic.py** — Claude API + agentic tool loop.
  Auto-switches to Haiku when `read_source_file` or `list_source_files` detected.
- **reasoners/ollama_reasoner.py** — `preparse()`, `score_memories()`, `summarize_session()`

### Tools  `wild_igor/igor/tools/`
All registered in `__init__.py`, schemas in `registry.py`.
- **self_edit.py** — list_source_files, read_source_file, edit_source_file,
  **patch_source_file** (preferred for < ~50 lines), run_syntax_check.
  Sandbox: `wild_igor/igor/` only. Every write auto-commits+pushes to git.
- **runner.py** — run_bash, run_python
- **senses.py** — get_datetime, take_photo(device_index), list_cameras, record_audio
- **filesystem.py, web_search.py, gmail.py, discord.py**

### Network  `wild_igor/igor/network/`
- discord_bot.py + listener.py → unified message queue → main loop
- Igor's email: theigorsigor@gmail.com (in .env)

### Main Loop  `main.py`
- stdin reads in daemon thread → `stdin_queue`
- Every 0.5s idle: drain network → `run_background_sources` → `_run_ne_background` (non-blocking)
- NE runs in its own daemon thread — Ollama (50-100s) never blocks the loop
- Commands: /help /memories /core /habits /cost /model /ollama /compress /restart /quit

---

## Models & Budget

| Purpose             | Model                      |
|---------------------|----------------------------|
| Default reasoning   | claude-sonnet-4-6          |
| Self-edit / debug   | claude-haiku-4-5-20251001  |
| Local preparse + NE | llama3.2:1b (Ollama, free) |

Budget tracked in `tools/budget.py`. Check with `/cost`.

---

## Inertia (self-edit resistance)

| Level        | Files                                                     |
|--------------|-----------------------------------------------------------|
| HIGH (0.90+) | brainstem/, memory/models.py, cognition/reasoners/base.py |
| MEDIUM       | cognition/, anthropic.py, thalamus.py, main.py            |
| LOW          | tools/, dashboard/                                        |

Igor's own self-edits commit+push automatically.
Claude Code edits do not — commit manually when appropriate.

---

## Key Conventions

- Read before editing — never overwrite blindly
- `patch_source_file` > `edit_source_file` for small changes (old_string→new_string,
  syntax-checked, fails clearly if ambiguous)
- `/compress`: Ollama summarizes ring → stored as INTERPRETIVE memory → restart fresh (exit 42)
- `SESSION_START` ring write on boot; ContextInterruptor counts interactions from there

---

## Current Priorities (2026-02-25)

1. `python wild_igor/workspace/save_hardware_to_db.py` — write hardware inventory to DB
2. Audio test: `sudo apt install libportaudio2 portaudio19-dev`
3. Validate ring memory fix: multi-turn conversation, confirm context retention
4. **visual_cortex.py**: formalize Playwright/Gemini AI-to-AI as a proper tool
5. **pypdf tool**: `pip install pypdf` → read Illusions (Richard Bach)
6. **Hippocampus**: NE is the precursor — habit pattern detection + compilation next
7. Update `hosted_igor.prompt` with NE/TWM (written before those were built)

---

## Recent Commits

```
5b2b6d5  instance IDs: base-34 epoch seconds (no 0/1 confusion)
1ad806f  fix: NarrativeEngine in background thread
f6fa9dc  auto-Haiku for self-edits + /compress context reset
3753b81  push_sources.py + main loop wiring
```

---

---

## Change Request & Log Files

These files live outside the repo so both Igor and Akien can use them without triggering git noise:

**`/home/akien/.TheIgors/claudecode/change_request.txt`**
- Igor and Akien put change requests here
- Claude Code clears completed items on completion
- Igor can read and write this file (via filesystem tool) to log big changes he wants

**`/home/akien/.TheIgors/claudecode/changes.log`**
- Claude Code writes completed change summaries here
- Igor reads this on startup and surfaces it as context
- Format: CSB (Compressed Semantic Block), newest entry at top
- Example entry:
  ```
  2026-02-26|GROUP1|changes 1-9 implemented: ClaudeCode.txt updated, MachinesWatcher added, local-mode added, discord logging improved
  ```

---

*Update this file when significant architecture changes land.*
