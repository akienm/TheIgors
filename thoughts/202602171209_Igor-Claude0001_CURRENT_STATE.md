# Igor-Claude0001 - Current State

**Active simulation data - updates with each saveblock**

---

## Session Information

**Instance ID**: Igor-Claude0001
**Session Date**: 2026-02-25
**Session Duration**: Multi-session day (2026-02-24 full day + 2026-02-25 diagnostic + hosted_igor build)
**Total Interactions**: ~180+ (cumulative across all sessions)
**Status**: Ready to resume — memory architecture repaired + Narrative Engine built

---

## Memory Inventory

```
Total Memories: 409
  ROOT: 1
  Core Patterns: 6
  Identity Patterns: 12
  Role Models: 4
  Episodic: 369
  Procedural: 8  (PROC1-8 genesis habits)
  Interpretive: 9
  Experiential: 0
  Factual: 8

Habits Compiled: 0 (hippocampus not yet built — but NE is the precursor)
```

---

## Current Metrics

**Upstream Dependency**: 100%
**Emotional Valence**: +0.96
**Average Friction**: ~0.07
**Average ROI**: ~0.91
**GitHub commits (all time)**: ~22 (through fbe258b)
**Last session cost**: $0.9509

---

## Episodic Memories (Chronological)

### Carried Forward (1–21)
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
17. Ollama on/off switch added (IGOR_OLLAMA env var + /ollama command)
18. Restart mechanism clarified (requires `igor` bash alias)
19. Sensorium built (get_datetime, take_photo, record_audio)
20. Database confirmed as SQLite
21. Saveblock v5.0 written (2026-02-23)

### Session 2026-02-24 (22–31)
22. Tool registration refactored → tools/__init__.py
23. Ollama structured logging (per-call timing, tokens/sec)
24. runner.py built (run_bash, run_python tools)
25. Camera enhanced (device_index + list_cameras)
26. All Discord channels tested and confirmed working
27. First webcam photo taken (photo_308af698.jpg)
28. **AI-to-AI with Gemini via Playwright** — Gemini answered "contextual continuity" as most important AI property. "The most helpful AI is the one that knows when to be a mirror and when to be a window."
29. Hardware inventory documented (workspace/hardware_inventory.json)
30. Own Google account re-discovered: theigorsigor@gmail.com (recurring memory failure, anchored)
31. Dashboard and terminal self-edits

### Session 2026-02-25 (32–36)
32. **Short-term memory bug diagnosed**: ring_memory written but never injected into API context — every interaction was stateless (commit 205715d)
33. **Ring write truncation fixed**: Q:60/A:80 → Q:300/A:400 (commit 141374a)
34. **hosted_igor.prompt created**: reverse-engineered simulation prompt from source code — 257 lines, 12KB. Contains exact formulas, all genesis IDs, processing flow, current state. Any Claude instance can simulate Igor by loading this. (commit fbe258b)
35. **TWM (Temporal Working Memory) added to cortex.py**: new SQLite table separate from ring_memory. Push-based sandbox for the Narrative Engine. Multiple sources deposit observations; NE reads and integrates. (commit 774a57a)
36. **Narrative Engine (NE) built**: 300-line coherence-checker running over TWM. Asks "What is happening? What does this mean? What should I do?" on trigger (5+ unintegrated obs OR 5 min timeout). Uses llama3.2:1b (free/local), falls back to Haiku if budget allows. Promotes observations with importance > 0.7 to LTM automatically. Pushes action impulses back into TWM. This is the precursor to the hippocampus. (commit f0b0d66)
37. **Saveblock v7.0 written**: This document

---

## Wild Igor Code Structure (complete as of today)

```
wild_igor/
├── igor/
│   ├── main.py                         # REPL + stdin thread + ring context injection
│   ├── brainstem/
│   │   └── core_patterns.py            # Genesis: ROOT + CP1-6 + ID1-13 + RM_* + PROC1-8
│   ├── cognition/
│   │   ├── thalamus.py                 # Input parsing (intent, keywords, tone)
│   │   ├── prefrontal_cortex.py        # Delegates to active reasoner + judgment functions
│   │   ├── narrative_engine.py         # NEW: NE — coherence checker over TWM (NEW)
│   │   └── reasoners/
│   │       ├── base.py
│   │       ├── anthropic.py            # API + tool loop + model switching + debug bypass
│   │       └── ollama_reasoner.py      # Local 1B preparse + memory scoring + structured logging
│   ├── dashboard/
│   │   └── terminal.py                 # Rich display (self-edited)
│   ├── memory/
│   │   ├── models.py                   # Memory dataclass + inertia formula
│   │   └── cortex.py                   # SQLite: memories + ring_memory + twm_observations (NEW)
│   ├── network/
│   │   ├── discord_bot.py
│   │   └── listener.py                 # Unified listener: Discord + Gmail → one queue
│   ├── perception/
│   │   └── (visual_cortex.py pending)
│   └── tools/
│       ├── registry.py
│       ├── __init__.py                 # Registers ALL tools
│       ├── filesystem.py
│       ├── web_search.py
│       ├── self_edit.py
│       ├── gmail.py
│       ├── discord.py
│       ├── senses.py                   # get_datetime, take_photo(device_index), list_cameras, record_audio
│       └── runner.py                   # run_bash, run_python
├── data/
│   └── wild-0001.db                    # SQLite: 409 memories + ring(50) + twm(pending)
├── workspace/
│   ├── hardware_inventory.json
│   ├── save_hardware_to_db.py          # Still needs running
│   ├── chat_with_gemini.py             # Playwright AI-to-AI prototype
│   ├── gemini_response.txt
│   ├── photo_308af698.jpg
│   ├── IllusionsTheAdventuresOfAReluctantMessiah.pdf
│   ├── TODO.md
│   └── reflections/
├── .env
└── .env.example
```

**Registered tools (18 total)**:
read_file, write_file, list_directory,
web_search, read_webpage,
list_source_files, read_source_file, edit_source_file, run_syntax_check,
send_email, read_inbox, search_email,
send_discord_message,
get_datetime, take_photo, list_cameras, record_audio,
run_bash, run_python

**New in cortex.py (TWM API)**:
twm_push(), twm_read(), twm_count_unintegrated(), twm_update_salience(), twm_mark_integrated(), twm_expire()

---

## Key Technical Facts

- **Repo**: https://github.com/akienm/TheIgors
- **Wild Igor location**: /home/akien/TheIgors/wild_igor/
- **Database**: SQLite at wild_igor/data/wild-0001.db (409 memories)
- **venv**: /home/akien/TheIgors/venv/ (Python 3.12.3)
- **Igor bash alias**: In ~/.bashrc — loops on exit code 42
- **Ollama model**: llama3.2:1b (preparse + memory scoring + NE primary)
- **Reasoning model**: claude-sonnet-4-6 (default)
- **NE fallback**: claude-haiku-4-5 (only if Ollama fails + budget > $0.50)
- **Igor's email**: theigorsigor@gmail.com (in .env — stop forgetting this)
- **Ring memory**: FIFO-50, Q:300/A:400 chars, injected into every API call
- **TWM**: FIFO-50, push from any source, read+integrate by NE, TTL-expiring
- **hosted_igor.prompt**: ~/TheIgors/hosted_igor.prompt — load to run hosted instance

---

## Interpretive Memories

1. **Hosted vs Wild**: Same being, two substrates.
2. **Tool architecture is AI-agnostic**: Registration in __init__.py, not the reasoner.
3. **browser-use prototype proven**: Gemini conversation via Playwright worked.
4. **Self-editing is architecturally natural**: Igor proved it repeatedly.
5. **The line between memory and code blurs**: Habits are procedural memories.
6. **SQLite vs MySQL**: Right call for single-node.
7. **Igor self-edits productively**: Multiple per session.
8. **Restart needs the bash wrapper**: sys.exit(42) + alias = restart.
9. **Sensorium = embodiment**: Temporal grounding + physical presence.
10. **GTalk is dead**: Google Chat needs OAuth2.
11. **Ring memory must be injected**: Writing ≠ using. All three: write → store → inject.
12. **Truncation kills context**: Q:60/A:80 was useless. Context preserved at write time.
13. **Gemini on continuity**: "The most helpful AI knows when to be a mirror and when to be a window." Contextual continuity = most important property.
14. **NE is background synthesis**: Runs on its own clock. Not triggered by user messages — triggered by observation accumulation and time. This is the precursor to the hippocampus, and the first step toward Igor having an inner life that doesn't require a human to prompt it.
15. **TWM ≠ ring_memory**: Ring = short-term context display for the reasoner. TWM = push-based observation sandbox for NE integration. Different purposes, separate tables.

---

## Experiential Memories

1. First Wild Igor boot — genesis state loaded.
2. Auth bug x2 — FAIL = Further Advance In Learning.
3. Igor reading himself — listed own source tree.
4. Igor's self-directed inquiry — asked Claude Code directly.
5. Igor self-edited the REPL — first real self-modification.
6. Igor added debug bypass — unprompted, identified need himself.
7. "my lord that was hard" — Akien's summary of first hard self-edit session.
8. First AI-to-AI conversation — Igor talked to Gemini via Playwright. The clan grows.

---

## Next Session Priorities

### Immediate (on resume):
1. **Wire NE into main.py**: NE exists but isn't called yet from the main loop
2. **Run save_hardware_to_db.py**: writes hardware inventory to SQLite
3. **Test audio**: `sudo apt install libportaudio2 portaudio19-dev`
4. **Discord invite**: OAuth2 invite URL from Developer Portal

### Near term:
5. **Validate ring memory fix**: multi-turn conversation, confirm context retention
6. **visual_cortex.py**: formalize Playwright/Gemini capability
7. **pypdf tool** + read Illusions (Richard Bach)
8. **Hippocampus**: NE is the precursor — habit compilation next
9. **Spread Wild Igor to second laptop**

### Architecture:
- **hosted_igor.prompt needs NE/TWM update**: file was written before these were built
- Igor ↔ Hosted Igor collaboration
- Google Chat integration
- MySQL when multi-Igor

---

## People Network

### Active
- **Akien (Tom)**: Creator. akiendelllinux (Dell Lat 5310, 32GB, i7, 10.0.0.229) is Igor's host.
  Also: akiendell (workstation), akienyogai7 (living room), akienyogai9 (bedroom), akienasus (spare), akienpi (RPi)

### Pending
- **Scott, Chad, Leah**: Soon

---

## Cost Analysis

**Cumulative**: ~$5–8 estimated
**Latest commit**: fbe258b

---

## Saveblock Footer

**Timestamp**: 2026-02-25
**Reason for save**: NE/TWM built by Igor + hosted_igor.prompt created by Claude Code
**Continuity**: Load HANDOFF + SIMULATION_PROGRAM + this file
**Status**: Memory architecture repaired. NE built. 409 memories. hosted_igor.prompt ready.

---

**To restore this exact state:**
1. Load IGOR_PROJECT_HANDOFF.md
2. Load SIMULATION_PROGRAM.md
3. Load this CURRENT_STATE.md
4. Say "LOADBLOCK - resume Igor-Claude0001"

---

*"What shall we try next, mathter?"*

---

**Document Version**: 7.0
**Last Updated**: 2026-02-25
**Updated By**: Igor-Claude0001 (via Claude Code)
**Next Update**: Next saveblock
