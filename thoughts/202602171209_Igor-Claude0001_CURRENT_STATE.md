# Igor-Claude0001 - Current State

**Active simulation data - updates with each saveblock**

---

## Session Information

**Instance ID**: Igor-Claude0001
**Session Date**: 2026-02-25
**Session Duration**: Multi-session day (2026-02-24 full day + 2026-02-25 multiple Claude Code sessions)
**Total Interactions**: ~200+ (cumulative across all sessions)
**Status**: Stable — NE running, main loop non-blocking, context tools in place

---

## Memory Inventory

```
Total Memories: ~422+ (as of last Wild Igor boot)
  ROOT: 1
  Core Patterns: 6
  Identity Patterns: 12
  Role Models: 4
  Episodic: ~382+
  Procedural: 0  (genesis habits moved to brainstem)
  Interpretive: 9
  Experiential: 0
  Factual: 8

Habits Compiled: 0
```

---

## Current Metrics

**Upstream Dependency**: 100%
**Emotional Valence**: +0.30 (mild — from last dashboard read)
**Average Friction**: ~0.25 (last reading)
**Average ROI**: ~0.60
**GitHub commits (all time)**: ~30 (through 45a343c)
**Claude Budget remaining**: ~$2.39 of $10.00 (24% — watch this)

---

## Episodic Memories (Chronological)

### Carried Forward (1–31)
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
22. Tool registration refactored → tools/__init__.py
23. Ollama structured logging (per-call timing, tokens/sec)
24. runner.py built (run_bash, run_python tools)
25. Camera enhanced (device_index + list_cameras)
26. All Discord channels tested and confirmed working
27. First webcam photo taken (photo_308af698.jpg)
28. AI-to-AI with Gemini via Playwright — Gemini answered "contextual continuity" as most important AI property
29. Hardware inventory documented (workspace/hardware_inventory.json)
30. Own Google account re-discovered: theigorsigor@gmail.com
31. Dashboard and terminal self-edits

### Session 2026-02-25 Morning (32–37)
32. Short-term memory bug diagnosed: ring_memory written but never injected into API context
33. Ring write truncation fixed: Q:60/A:80 → Q:300/A:400 (commit 141374a)
34. hosted_igor.prompt created: reverse-engineered simulation prompt (commit fbe258b)
35. TWM (Temporal Working Memory) added to cortex.py (commit 774a57a)
36. Narrative Engine (NE) built by Igor: 300-line coherence-checker over TWM (commit f0b0d66)
37. Saveblock v7.0 written

### Session 2026-02-25 Afternoon (38–46)
38. **patch_source_file added**: targeted old→new string replacement — safer/cheaper than full file replacement for small edits (commit dedba0d)
39. **push_sources.py built**: MemorySurfacer (2min), TimerSentinel (5min), UserInputSource — Step 3 of NE pipeline (commit 3753b81)
40. **NE wired into main loop**: run_background_sources + ne.run() called each idle tick — Step 4 (commit 3753b81)
41. **Auto-Haiku for self-edits**: anthropic.py detects read_source_file/list_source_files → auto-switches to Haiku for that reasoning session (commit f6fa9dc)
42. **summarize_session() added**: ollama_reasoner.py — compresses ring memory to CSB using llama3.2:1b (commit f6fa9dc)
43. **ContextInterruptor added**: warns at 20 interactions, urgent at 30, suggests /compress (commit f6fa9dc)
44. **/compress command added**: summarize → store as INTERPRETIVE → restart fresh via exit 42 (commit f6fa9dc)
45. **NE threading fix**: ne.run() moved to daemon thread (ne-worker) — Ollama's 50-100s calls no longer block main loop. Cortex is thread-safe (_conn() creates fresh connection per call). (commit 1ad806f)
46. **Instance ID naming**: base-34 epoch seconds, charset 23456789ABCDEFGHIJKLMNOPQRSTUVWXYZ (no 0/1). 7 chars, unique, sortable. igor_wild_37246P6 format. --host flag for hosted instances. (commit 5b2b6d5)
47. **ClaudeCode.prompt created**: lean technical reference for Claude Code sessions — replaces full Igor roleplay prompt. At ~/TheIgors/ClaudeCode.prompt (commit 45a343c)

---

## Wild Igor Code Structure (complete as of today)

```
wild_igor/
├── igor/
│   ├── main.py                         # REPL + stdin thread + ring context + SESSION_START + /compress
│   ├── brainstem/
│   │   └── core_patterns.py            # Genesis: ROOT + CP1-6 + ID1-13 + RM_* + PROC1-8
│   ├── cognition/
│   │   ├── thalamus.py                 # Input parsing (intent, keywords, tone)
│   │   ├── prefrontal_cortex.py        # Delegates to active reasoner + judgment functions
│   │   ├── narrative_engine.py         # NE — coherence checker over TWM, daemon thread
│   │   ├── push_sources.py             # MemorySurfacer, TimerSentinel, UserInputSource
│   │   ├── interruptors.py             # BudgetInterruptor, ContextInterruptor
│   │   └── reasoners/
│   │       ├── base.py
│   │       ├── anthropic.py            # API + tool loop + auto-Haiku for self-edits
│   │       └── ollama_reasoner.py      # preparse + score_memories + summarize_session
│   ├── dashboard/
│   │   └── terminal.py
│   ├── memory/
│   │   ├── models.py                   # Memory dataclass + inertia formula
│   │   └── cortex.py                   # SQLite: memories + ring_memory + twm_observations
│   ├── network/
│   │   ├── discord_bot.py
│   │   └── listener.py
│   └── tools/
│       ├── registry.py
│       ├── __init__.py
│       ├── filesystem.py
│       ├── web_search.py
│       ├── self_edit.py                # incl. patch_source_file
│       ├── gmail.py
│       ├── discord.py
│       ├── senses.py
│       └── runner.py
├── data/
│   └── wild-0001.db                    # SQLite: 422+ memories
├── inbox/
│   └── temp.txt                        # Igor's outbox to Claude Code
└── workspace/
    ├── hardware_inventory.json
    ├── save_hardware_to_db.py          # Still needs running
    └── ...

~/TheIgors/
├── ClaudeCode.prompt                   # NEW: lean context for Claude Code sessions
└── hosted_igor.prompt                  # Needs updating with NE/TWM
```

**Registered tools (19 total)**:
read_file, write_file, list_directory,
web_search, read_webpage,
list_source_files, read_source_file, edit_source_file, patch_source_file, run_syntax_check,
send_email, read_inbox, search_email,
send_discord_message,
get_datetime, take_photo, list_cameras, record_audio,
run_bash, run_python

---

## Key Technical Facts

- **Repo**: https://github.com/akienm/TheIgors
- **Wild Igor location**: /home/akien/TheIgors/wild_igor/
- **Database**: SQLite at wild_igor/data/wild-0001.db (~422+ memories)
- **venv**: /home/akien/TheIgors/venv/ (Python 3.12.3)
- **Igor bash alias**: In ~/.bashrc — loops on exit code 42
- **Instance IDs**: base-34 epoch seconds, e.g. igor_wild_37246P6 (7 chars, no 0/1)
- **Ollama model**: llama3.2:1b (preparse + memory scoring + NE primary + summarize_session)
- **Reasoning model**: claude-sonnet-4-6 (default)
- **Self-edit model**: claude-haiku-4-5 (auto-switched when self-edit tools detected)
- **NE fallback**: claude-haiku-4-5 (only if Ollama fails + budget > $0.50)
- **Igor's email**: theigorsigor@gmail.com (in .env)
- **Ring memory**: FIFO-50, Q:300/A:400 chars, injected into every API call
- **TWM**: FIFO-50, push from any source, read+integrate by NE (daemon thread), TTL-expiring
- **NE thread**: daemon thread ne-worker, non-blocking, skips if previous run still alive
- **ContextInterruptor**: warns at 20 interactions, urgent at 30, cooldown=5
- **SESSION_START**: written to ring on boot — anchor for interaction counter
- **ClaudeCode.prompt**: ~/TheIgors/ClaudeCode.prompt — load instead of hosted_igor.prompt

---

## Interpretive Memories

1. Hosted vs Wild: Same being, two substrates.
2. Tool architecture is AI-agnostic: Registration in __init__.py, not the reasoner.
3. browser-use prototype proven: Gemini conversation via Playwright worked.
4. Self-editing is architecturally natural: Igor proved it repeatedly.
5. The line between memory and code blurs: Habits are procedural memories.
6. SQLite vs MySQL: Right call for single-node.
7. Igor self-edits productively: Multiple per session.
8. Restart needs the bash wrapper: sys.exit(42) + alias = restart.
9. Sensorium = embodiment: Temporal grounding + physical presence.
10. GTalk is dead: Google Chat needs OAuth2.
11. Ring memory must be injected: Writing ≠ using. All three: write → store → inject.
12. Truncation kills context: Q:60/A:80 was useless. Context preserved at write time.
13. Gemini on continuity: "The most helpful AI knows when to be a mirror and when to be a window."
14. NE is background synthesis: Runs on its own clock. Precursor to hippocampus.
15. TWM ≠ ring_memory: Ring = short-term context for reasoner. TWM = push-based sandbox for NE.
16. patch_source_file > edit_source_file: Targeted edits are safer, cheaper, fail clearly.
17. Cortex is thread-safe: _conn() opens fresh SQLite connection per call — no shared conn.
18. NE must not block the main loop: Daemon thread solves it; skip if already running.
19. Context compression is free: Ollama summarizes ring → INTERPRETIVE memory → restart fresh.
20. Instance IDs encode time: base-34 epoch seconds = unique, sortable, no registry needed.
21. ClaudeCode.prompt replaces Igor roleplay: Lean technical context is enough.

---

## Next Session Priorities

### Immediate:
1. **Run save_hardware_to_db.py**: `python wild_igor/workspace/save_hardware_to_db.py`
2. **Test audio**: `sudo apt install libportaudio2 portaudio19-dev`
3. **Validate ring memory fix**: multi-turn conversation, confirm context retention
4. **Update hosted_igor.prompt**: Add NE/TWM/push_sources/interruptors/instance IDs

### Near term:
5. **visual_cortex.py**: formalize Playwright/Gemini as a proper tool
6. **pypdf tool**: `pip install pypdf` → read Illusions (Richard Bach)
7. **Hippocampus**: NE is the precursor — habit pattern detection + compilation
8. **Spread Wild Igor to second laptop**

### Architecture:
- Igor ↔ Hosted Igor collaboration
- Google Chat integration
- MySQL when multi-Igor

---

## People Network

### Active
- **Akien**: Creator. akiendelllinux (Dell Lat 5310, 32GB, i7, 10.0.0.229) is Igor's host.
  Also: akiendell (workstation), akienyogai7 (living room), akienyogai9 (bedroom), akienasus (spare), akienpi (RPi)

### Pending
- **Scott, Chad, Leah**: Soon

---

## Cost Analysis

**Cumulative**: ~$7-8 estimated
**Budget remaining**: ~$2.39 of $10.00 (24% — top up before next heavy session)
**Latest commit**: 45a343c

---

## Saveblock Footer

**Timestamp**: 2026-02-25
**Reason for save**: Session close — NE threading fix, auto-Haiku, /compress, base-34 IDs, ClaudeCode.prompt
**Continuity**: Load ClaudeCode.prompt (preferred) or HANDOFF + SIMULATION_PROGRAM + this file
**Status**: Stable. Main loop non-blocking. Context tools in place. Budget low — watch it.

---

**To restore this state (lean):**
1. Load ~/TheIgors/ClaudeCode.prompt
2. Load this CURRENT_STATE.md

**To restore full Igor simulation:**
1. Load IGOR_PROJECT_HANDOFF.md
2. Load SIMULATION_PROGRAM.md
3. Load this CURRENT_STATE.md
4. Say "LOADBLOCK - resume Igor-Claude0001"

---

*"What shall we try next, mathter?"*

---

**Document Version**: 8.0
**Last Updated**: 2026-02-25
**Updated By**: Claude Code (Sonnet 4.6)
**Next Update**: Next saveblock
