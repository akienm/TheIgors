---
name: windows_epic
description: D108 — Cross-platform Igor: PathManager + first-start wizard + Windows round
type: project
---

D108 — Windows round epic. Ticket needed.

**Goal**: Igor runs on Windows (and Mac). All platforms connect as separate attention centers to same DB on akiendelllinux.

**Plan (Akien's words)**:
- Make code paths safe for Windows — a path manager of some kind, since disk organization differs
- Global PathManager system object replacing all path constants
- First-start wizard: "Database (current 127.0.0.1)?:" — enter akiendelllinux IP, away we go
- Pull latest repo on Windows, tell Claude to get it working

**Key work**:
1. PathManager class — wraps all ~/.TheIgors/, log, DB, runtime paths; platform-aware (Windows uses AppData or similar); replaces all hardcoded Path(home()) patterns
2. First-start wizard — on first boot, prompt for remote DB IP (default 127.0.0.1); write to instance config; NetworkDatabaseProxy uses it
3. Audit all path construction for Windows safety (forward slash, drive letters, symlinks)
4. venv / dependency check for Windows (ebooklib, uvicorn, etc.)

**Why:** Once running on all three platforms, they connect as separate attention centers on same DB. DB optimization becomes critical at that scale. akiendelllinux may wind up as main attention center + DB server, or a new dedicated DB server may spin up.

**How to apply:** When starting Windows round, begin with PathManager design before touching any other code. First-start wizard is the user-facing entry point.
