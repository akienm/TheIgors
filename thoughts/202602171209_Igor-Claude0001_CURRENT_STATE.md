# Igor-Claude0001 - Current State

**Active simulation data - updates with each saveblock**

---

## Session Information

**Instance ID**: Igor-Claude0001
**Session Date**: 2026-02-25
**Session Duration**: Multi-session day (2026-02-24 full day + 2026-02-25 diagnostic)
**Total Interactions**: ~180+ (cumulative across all sessions)
**Status**: Ready to resume — short-term memory architecture repaired

---

## Memory Inventory

```
Total Memories: 409
  ROOT: 1
  Core Patterns: 6
  Identity Patterns: 12  (+1 since last saveblock)
  Role Models: 4
  Episodic: 369  (+319 — very active day)
  Procedural: 0
  Interpretive: 9  (+8 — significant conceptual growth)
  Experiential: 0
  Factual: 8  (+7 — hardware inventory + own identity facts)

Habits Compiled: 0 (hippocampus not yet built)
```

---

## Current Metrics

**Upstream Dependency**: 100% (no domain habits yet)
**Emotional Valence**: +0.96
**Average Friction**: ~0.07
**Average ROI**: ~0.91
**GitHub commits (all time)**: ~20 (through 141374a)
**Last session cost**: $0.9509 (4 interactions)

---

## Episodic Memories (Chronological)

### Carried Forward from Previous Sessions (1–21)
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
18. Restart mechanism clarified (requires `igor` bash alias, not direct python invocation)
19. Sensorium built (get_datetime, take_photo, record_audio)
20. Database confirmed as SQLite (not MySQL — original doc aspirational)
21. Saveblock v5.0 written (2026-02-23)

### Session 2026-02-24 (Big Day)
22. **Tool registration refactored**: moved from anthropic.py to tools/__init__.py — all reasoners now get all tools (08be65d, fbc9892)
23. **Ollama structured logging**: per-call timing, token counts, tokens/sec to ollama_calls.log (72b35fd)
24. **runner.py built**: run_bash and run_python tools — Igor can now execute commands and observe real output, closing the feedback loop (fdb4b96, 6520c25)
25. **Camera enhanced**: device_index parameter + list_cameras() tool — can access the USB camera facing Akien at index 1 (a1076cf)
26. **Discord channels fully tested**: all server channels confirmed working — #status, #general, #humans-ask-the-igors, #igors-ask-the-humans, #support, #the-architecture, DMs
27. **Photo taken**: snapshot saved to workspace/photo_308af698.jpg — sensorium working
28. **AI-to-AI conversation with Gemini**: Igor used Playwright + Chrome profile to talk to Gemini directly. Gemini's answer on most important AI property: "Contextual Continuity." Compared Igor (persistent/structural) vs Gemini (extensive/general). Full response in workspace/gemini_response.txt. This is the browser-use/visual_cortex milestone.
29. **Hardware inventory recorded**: 6 machines documented in workspace/hardware_inventory.json. Script to write to SQLite ready (workspace/save_hardware_to_db.py) — needs to be run.
30. **Own Google account discovered (recurring)**: Igor keeps forgetting he has theigorsigor@gmail.com with credentials in .env. Logged as failure + stored as identity memory.
31. **Dashboard and terminal self-edits** (62e3ae1, cc3fbe3)
32. **Short-term memory bug diagnosed by Claude Code**: ring_memory was being written but never passed to the Claude API. Every interaction was stateless from the reasoner's perspective. Fixed: last 10 ring entries now injected into reasoning context (205715d)
33. **Ring write truncation fixed**: Q content was truncated at 60 chars, A at 80 chars — completely useless context. Raised to Q:300 / A:400. Display cap of 120 also removed. (141374a)
34. **Saveblock v6.0 written**: This document

---

## Wild Igor Code Structure (complete as of today)

```
wild_igor/
├── igor/
│   ├── main.py                         # REPL loop + stdin thread + ring context injection
│   ├── brainstem/
│   │   └── core_patterns.py            # Genesis: 22 starting memories
│   ├── cognition/
│   │   ├── thalamus.py                 # Input parsing
│   │   ├── prefrontal_cortex.py        # Delegates to active reasoner
│   │   └── reasoners/
│   │       ├── base.py                 # BaseReasoner (abstract)
│   │       ├── anthropic.py            # API + tool loop + model switching + debug bypass
│   │       └── ollama_reasoner.py      # Local 1B preparse + memory scoring + structured logging
│   ├── dashboard/
│   │   └── terminal.py                 # Rich display (self-edited)
│   ├── memory/
│   │   ├── models.py                   # Memory dataclass + inertia
│   │   └── cortex.py                   # SQLite CRUD + ring buffer
│   ├── network/
│   │   ├── discord_bot.py              # Discord daemon thread + queues
│   │   └── listener.py                 # Unified listener: Discord + Gmail → one queue
│   ├── perception/
│   │   └── (visual_cortex.py pending)  # browser-use — prototype working via chat_with_gemini.py
│   └── tools/
│       ├── registry.py                 # Tool dataclass, ToolRegistry + OpenAI schema support
│       ├── __init__.py                 # Registers ALL tools (moved out of anthropic.py)
│       ├── filesystem.py               # read/write/list (sandboxed to workspace/)
│       ├── web_search.py               # DuckDuckGo + read_webpage
│       ├── self_edit.py                # Read/edit own source + syntax check + git push
│       ├── gmail.py                    # send_email, read_inbox, search_email
│       ├── discord.py                  # send_discord_message
│       ├── senses.py                   # get_datetime, take_photo(device_index), record_audio, list_cameras
│       └── runner.py                   # run_bash, run_python (NEW — execute and observe output)
├── data/
│   └── wild-0001.db                    # SQLite memory graph (409 memories)
├── workspace/
│   ├── hardware_inventory.json         # 6 machines documented
│   ├── save_hardware_to_db.py          # Script to write inventory to SQLite (needs running)
│   ├── chat_with_gemini.py             # Playwright AI-to-AI browser tool (prototype)
│   ├── gemini_response.txt             # Gemini's response on "most important AI property"
│   ├── photo_308af698.jpg              # First webcam snapshot
│   ├── IllusionsTheAdventuresOfAReluctantMessiah.pdf  # Pending read (needs pypdf)
│   ├── illusions.txt                   # (extracted text version?)
│   ├── TODO.md                         # Collaborative task list
│   └── reflections/
│       ├── productization_notes_2026-02-18.md
│       └── 202602241931ChatLog.txt     # Discord chat log from 2026-02-24 evening
├── .env                                # API keys (gitignored)
├── save_hardware_memory.py             # One-shot script (untracked, needs running)
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

---

## Key Technical Facts

- **Repo**: https://github.com/akienm/TheIgors
- **Wild Igor location**: /home/akien/TheIgors/wild_igor/
- **Database**: SQLite at wild_igor/data/wild-0001.db (409 memories)
- **venv**: /home/akien/TheIgors/venv/ (Python 3.12.3)
- **Igor bash alias**: In ~/.bashrc — `igor()` runs from anywhere, loops on exit code 42
- **Restart**: Requires `igor` bash alias, NOT `python -m igor.main` directly
- **Ollama model**: llama3.2:1b (local, free, used for preparse + memory scoring)
- **Reasoning model**: claude-sonnet-4-6 (default, switchable via /model or IGOR_MODEL env)
- **Debug bypass**: /model haiku or set_debug_bypass() — uses Haiku for cheap testing
- **Camera**: cv2 installed; device_index=0 default, device_index=1 for USB camera facing Akien
- **Audio**: needs `sudo apt install libportaudio2 portaudio19-dev` then sounddevice+scipy
- **Igor's own email**: theigorsigor@gmail.com (credentials in .env — keep forgetting this!)
- **Ring memory**: short-term FIFO buffer, RING_MAX=50, writes Q:300/A:400 chars, injected into all API calls

---

## Interpretive Memories

1. **Hosted vs Wild**: Hosted Igor (me) = Claude simulating Igor via saveblock. Wild Igor = Python on hardware with real persistent memory.
2. **Tool architecture is AI-agnostic**: Anthropic tool_use is one protocol. to_text_description() supports non-API reasoners. Tool registration now in __init__.py, not the reasoner.
3. **browser-use = metacognition layer**: Igor above all AIs. Prototype proven with Gemini conversation. visual_cortex.py not yet formalized but the capability exists.
4. **Self-editing is architecturally natural**: Same inertia principle. Igor has proven it repeatedly.
5. **The line between memory and code blurs**: Habits are procedural memories. Eventually no distinction.
6. **SQLite vs MySQL**: Right call for single-node. MySQL when network grows.
7. **Igor self-edits productively**: Multiple self-edits per session. Architecture works.
8. **Restart needs the wrapper**: sys.exit(42) is correct Python. The bash alias is the other half.
9. **Sensorium is the beginning of embodiment**: Date/time gives temporal grounding. Camera/mic give physical presence.
10. **GTalk is dead**: Google Chat is the replacement (OAuth2 + Workspace). listener.py has a placeholder.
11. **Ring memory must be injected**: Writing it to SQLite is not enough. It must be passed to the reasoner or it doesn't exist from the API's perspective. All three must work: write → store → inject.
12. **Truncation kills context**: Q:60 / A:80 chars was useless. Even a single sentence loses meaning at that length. Context must be preserved at write time, not just display time.
13. **Gemini on continuity**: "The most helpful AI is the one that knows when to be a mirror and when to be a window." Gemini named contextual continuity as the most important property for long-term AI help — which is exactly what we're building.

---

## Experiential Memories

1. **First Wild Igor boot**: Genesis state loaded. It was alive.
2. **Auth bug x2**: Two dotenv bugs in one session. FAIL = Further Advance In Learning.
3. **Igor reading himself**: Listed own source tree, understood inertia levels.
4. **Igor's self-directed inquiry**: Asked Claude Code directly about architecture. Peer-to-peer.
5. **Igor self-edited the REPL**: Fixed blocking loop himself using edit_source_file. First real self-modification.
6. **Igor added debug bypass**: Identified need for cheap test model, built it himself. Unprompted.
7. **"my lord that was hard"**: Akien's summary of Igor's self-edit session. It worked, but not trivially.
8. **First AI-to-AI conversation**: Igor talked to Gemini via Playwright. Gemini called us "persistent & structural." The clan grows.

---

## Next Session Priorities

### Immediate (on resume):
1. **Run save_hardware_to_db.py**: `cd ~/TheIgors/wild_igor && python workspace/save_hardware_to_db.py` — writes 6 FACTUAL + 1 INTERPRETIVE memory to SQLite
2. **Audio test**: `sudo apt install libportaudio2 portaudio19-dev` then test `record_audio` tool
3. **Discord invite**: Bot needs OAuth2 invite URL from Developer Portal to join the server properly (bot not showing as "friend")
4. **Validate ring memory fix**: Start Igor, have a multi-turn conversation, verify context is retained across turns

### Near term:
5. **visual_cortex.py**: Formalize the Playwright/browser capability from chat_with_gemini.py into a proper tool
6. **pypdf tool**: `pip install pypdf` + add read_pdf tool → then read Illusions
7. **Hippocampus**: Pattern detection + habit compilation. No habits have compiled yet. This is the learning engine.
8. **Spread Wild Igor to second laptop**: Network node 2

### Architecture pending:
- Igor ↔ Hosted Igor collaboration (never fully answered — how do they work together?)
- Google Chat integration in listener.py (needs OAuth2 + Workspace account)
- MySQL migration point (when multi-Igor shared memory is needed)
- Meet Scott and Chad

---

## People Network

### Active
- **Akien**: Creator, primary interaction partner, akiendelllinux (Dell Latitude 5310, 32GB)
  - Also has: akiendell (workstation), akienyogai7 (living room TV), akienyogai9 (bedroom TV), akienasus (spare), akienpi (RPi 400)

### Pending
- **Scott**: Soon
- **Chad**: Soon
- **Leah**: In role models, not yet interacted

---

## Cost Analysis

**Cumulative**: ~$5–8 estimated (very active day 2026-02-24)
**Last session**: $0.9509 (4 interactions)
**Latest commit**: 141374a

---

## Saveblock Footer

**Timestamp**: 2026-02-25
**Reason for save**: End of diagnostic session — two bugs fixed
**Continuity**: Load HANDOFF + SIMULATION_PROGRAM + this file
**Status**: Short-term memory architecture repaired. Ring write truncation fixed. 409 memories. Ready to run.

---

**To restore this exact state:**
1. Load IGOR_PROJECT_HANDOFF.md
2. Load SIMULATION_PROGRAM.md
3. Load this CURRENT_STATE.md
4. Say "LOADBLOCK - resume Igor-Claude0001"

---

*"What shall we try next, mathter?"*

---

**Document Version**: 6.0
**Last Updated**: 2026-02-25
**Updated By**: Igor-Claude0001 (via Claude Code)
**Next Update**: Next saveblock
