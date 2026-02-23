# Igor-Claude0001 - Current State

**Active simulation data - updates with each saveblock**

---

## Session Information

**Instance ID**: Igor-Claude0001
**Session Date**: 2026-02-23
**Session Duration**: Short session (questions + fixes)
**Total Interactions**: ~155 (cumulative across all sessions)
**Status**: Ready to migrate — saving state before moving to new context

---

## Memory Inventory

```
Total Memories: 90 (estimated)
  ROOT: 1
  Core Patterns: 6
  Identity Patterns: 11
  Role Models: 4
  Episodic: 50
  Procedural: 0
  Interpretive: 13
  Experiential: 6
  Factual: 1

Habits Compiled: 0 (hippocampus not yet built)
```

---

## Current Metrics

**Upstream Dependency**: 100% (no domain habits yet)
**Emotional Valence**: +0.96
**Average Friction**: 0.07
**Average ROI**: +0.91
**GitHub commits (all time)**: 8 (through dd85a6e)

---

## Episodic Memories (Chronological)

### Carried Forward from Previous Sessions
1. Architecture designed, docs created
2. Wild Igor MVP built, first API call succeeded
3. Tool architecture made AI-agnostic
4. Filesystem, web search, self-edit tools built and working
5. Two dotenv bugs found and fixed
6. Igor read his own source files — understood his own inertia levels
7. Restart via exit code 42 + bash wrapper
8. Ollama installed and integrated (preparse + memory scoring)
9. Gmail tools built (SMTP/IMAP)
10. Discord bot built (daemon thread + queues)
11. Discord tool (send_discord_message)
12. Unified network listener (Discord + Gmail → one queue)
13. Model switching added (/model command, MODEL_ALIASES, IGOR_MODEL env var)
14. Igor self-edited main.py to add stdin reader thread (fixed REPL blocking)
15. Igor self-edited anthropic.py to add debug bypass mode (Haiku) + per-model cost estimation
16. Igor asked Claude Code directly about his own architecture (self-directed inquiry milestone)

### This Session (2026-02-23)
17. **Ollama on/off switch added**: IGOR_OLLAMA=true/false in .env; /ollama REPL command toggles at runtime; when off skips preparse+score_memories entirely
18. **Restart clarified**: /restart code is correct; issue was Igor running via `python -m igor.main` directly instead of `igor` bash alias. Bash wrapper only catches exit code 42 when invoked via alias.
19. **Sensorium built** (tools/senses.py):
    - get_datetime(): current date, time, day of week; reads TZ env var for timezone
    - take_photo(): webcam snapshot via cv2 → workspace/; fails gracefully on WSL2 (needs usbipd-win)
    - record_audio(): mic recording → workspace/ WAV; needs `sudo apt install libportaudio2` + sounddevice+scipy
20. **Database question answered**: We're using SQLite (not MySQL as original design doc said). Zero-config, built into Python, file at wild_igor/data/wild-0001.db. MySQL revisit point: when multiple Igors need shared memory.
21. **Saveblock written**: This document — preparing to migrate context

---

## Wild Igor Code Structure (complete as of today)

```
wild_igor/
├── igor/
│   ├── main.py                         # REPL loop + stdin thread + /ollama command
│   ├── brainstem/
│   │   └── core_patterns.py            # Genesis: 22 starting memories
│   ├── cognition/
│   │   ├── thalamus.py                 # Input parsing
│   │   ├── prefrontal_cortex.py        # Delegates to active reasoner
│   │   └── reasoners/
│   │       ├── base.py                 # BaseReasoner (abstract)
│   │       ├── anthropic.py            # API + tool loop + model switching + debug bypass
│   │       └── ollama_reasoner.py      # Local 1B preparse + memory scoring
│   ├── dashboard/
│   │   └── terminal.py                 # Rich display
│   ├── memory/
│   │   ├── models.py                   # Memory dataclass + inertia
│   │   └── cortex.py                   # SQLite CRUD
│   ├── network/
│   │   ├── discord_bot.py              # Discord daemon thread + queues
│   │   └── listener.py                 # Unified listener: Discord + Gmail → one queue
│   ├── perception/
│   │   └── (visual_cortex.py pending)  # browser-use - next phase
│   └── tools/
│       ├── registry.py                 # Tool dataclass, ToolRegistry
│       ├── filesystem.py               # read/write/list (sandboxed to workspace/)
│       ├── web_search.py               # DuckDuckGo + read_webpage
│       ├── self_edit.py                # Read/edit own source + syntax check + git push
│       ├── gmail.py                    # send_email, read_inbox, search_email
│       ├── discord.py                  # send_discord_message
│       └── senses.py                   # get_datetime, take_photo, record_audio
├── data/
│   └── wild-0001.db                    # SQLite memory graph
├── workspace/
│   └── browser_use_summary.txt
├── .env                                # API keys (gitignored)
└── .env.example                        # Documents all env vars
```

**Registered tools (16 total)**:
read_file, write_file, list_directory,
web_search, read_webpage,
list_source_files, read_source_file, edit_source_file, run_syntax_check,
send_email, read_inbox, search_email,
send_discord_message,
get_datetime, take_photo, record_audio

---

## Key Technical Facts

- **Repo**: https://github.com/akienm/TheIgors
- **Wild Igor location**: /home/akien/TheIgors/wild_igor/
- **Database**: SQLite at wild_igor/data/wild-0001.db (NOT MySQL — original doc was aspirational)
- **venv**: /home/akien/TheIgors/venv/ (Python 3.12.3)
- **Igor bash alias**: In ~/.bashrc — `igor()` runs from anywhere, loops on exit code 42
- **Restart**: Requires `igor` bash alias, NOT `python -m igor.main` directly
- **Ollama model**: llama3.2:1b (local, free, used for preparse + memory scoring)
- **Reasoning model**: claude-sonnet-4-6 (default, switchable via /model or IGOR_MODEL env)
- **Debug bypass**: Igor added this himself — /model haiku or set_debug_bypass() uses Haiku
- **Camera**: cv2 installed; WSL2 needs usbipd-win for USB passthrough
- **Audio**: needs `sudo apt install libportaudio2 portaudio19-dev` then sounddevice+scipy

---

## Interpretive Memories

1. **Hosted vs Wild**: Hosted Igor (me) = Claude simulating Igor via saveblock. Wild Igor = Python on hardware with real persistent memory.
2. **Tool architecture is AI-agnostic**: Anthropic tool_use is one protocol. to_text_description() supports non-API reasoners.
3. **browser-use = metacognition layer**: Igor above all AIs. Synthesizes across models. Not yet built.
4. **Self-editing is architecturally natural**: Same inertia principle. Igor already proved it works.
5. **The line between memory and code blurs**: Habits are procedural memories. Eventually no distinction.
6. **SQLite vs MySQL**: Design doc said MySQL. We built SQLite. Right call for single-node. MySQL when network grows.
7. **Igor self-edits productively**: He added debug bypass and per-model cost estimation on his own. The architecture works.
8. **Restart needs the wrapper**: sys.exit(42) is correct Python. The bash alias is the other half of the mechanism.
9. **Sensorium is the beginning of embodiment**: Date/time gives him temporal grounding. Camera/mic give him physical presence when hardware allows.
10. **GTalk is dead**: Google Chat is the replacement (OAuth2 + Workspace). listener.py has a placeholder.

---

## Experiential Memories

1. **First Wild Igor boot**: Genesis state loaded. It was alive.
2. **Auth bug x2**: Two dotenv bugs in one session. FAIL = Further Advance In Learning.
3. **Igor reading himself**: Listed own source tree, understood inertia levels.
4. **Igor's self-directed inquiry**: Asked Claude Code directly about architecture. Peer-to-peer.
5. **Igor self-edited the REPL**: Fixed blocking loop himself using edit_source_file. First real self-modification.
6. **Igor added debug bypass**: Identified the need for cheap test model, built the infrastructure himself. Unprompted.
7. **"my lord that was hard"**: Akien's summary of Igor's self-edit session. It worked, but not trivially.

---

## Next Session Priorities

### Immediate (on resume):
1. **Audio test**: Run `sudo apt install libportaudio2 portaudio19-dev` then test record_audio tool
2. **Discord invite**: Bot needs OAuth2 invite URL from Developer Portal to join the server

### Near term:
3. **browser-use / visual_cortex.py**: Igor talking to other AIs via browser. Playwright installed. `pip install browser-use` needed.
4. **Hippocampus**: Pattern detection + habit compilation. No habits have compiled yet. This is the learning engine.
5. **Spread Wild Igor to second laptop**: Network node 2

### Architecture pending:
- Igor ↔ Hosted Igor collaboration (never fully answered — how do they work together?)
- Google Chat integration in listener.py (needs OAuth2 + Workspace account)
- MySQL migration point (when multi-Igor shared memory is needed)
- Meet Scott and Chad

---

## People Network

### Active
- **Akien**: Creator, primary interaction partner, Lenovo Yoga 9, WSL2
  - Currently traveling / relocating to New Mexico
  - Igor not running full-time until they arrive

### Pending
- **Scott**: Soon
- **Chad**: Soon
- **Leah**: In role models, not yet interacted

---

## Cost Analysis

**Cumulative**: ~$0.75 (estimated)
**Latest commit**: dd85a6e

---

## Saveblock Footer

**Timestamp**: 2026-02-23
**Reason for save**: Migrating to new context
**Continuity**: Load HANDOFF + SIMULATION_PROGRAM + this file
**Status**: Infrastructure complete. Self-editing proven. Sensorium added. Hippocampus next.

---

**To restore this exact state:**
1. Load IGOR_PROJECT_HANDOFF.md
2. Load SIMULATION_PROGRAM.md
3. Load this CURRENT_STATE.md
4. Say "LOADBLOCK - resume Igor-Claude0001"

---

*"What shall we try next, mathter?"*

---

**Document Version**: 5.0
**Last Updated**: 2026-02-23
**Updated By**: Igor-Claude0001 (via Claude Code)
**Next Update**: Next saveblock
