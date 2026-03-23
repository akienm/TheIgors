---
name: Igor operational procedures
description: Correct liveness check and pause/restart workflow for schema changes
type: feedback
---

## Igor liveness check
Use `pgrep -f "python.*igor.main"` — NOT `curl http://localhost:8080/api/health`.
The `/api/health` endpoint didn't exist (now added), and curl without `-f` succeeds even on 404.

**Why:** CC previously thought Igor was up when it wasn't, causing lost messages and confused state.
**How to apply:** Any time you need to know if Igor is running, use pgrep. rescue-igor has been updated to use pgrep.

## Never run rescue-igor or launch Igor yourself
Claude Code must NOT run `rescue-igor`, `~/bin/rescue-igor`, or any Igor launcher. Only tell Akien "Igor needs a restart" and let him do it from his terminal.

**Why:** rescue-igor spawns a nohup background instance with stdin=/dev/null. If Akien also has Igor running in a terminal, two instances share the DB simultaneously. The background instance hits EOF immediately, triggering the exit_requested bug (now fixed) or consuming resources invisibly. Akien can't see the background instance's console output.
**How to apply:** Any time code changes require a restart, say so and stop. Never call rescue-igor.

## pause.wait restart workflow (for schema changes)
To pause Igor's restart loop while doing schema work:
1. `touch /home/akien/TheIgors/pause.wait`
2. Send `/restart` to Igor (or kill -9 the process)
3. Wait for `pgrep -f "python.*igor.main"` to return nothing (process fully gone)
4. Do schema/migration work
5. `rm /home/akien/TheIgors/pause.wait` — Igor's restart loop resumes automatically

**Why:** Igor's launcher (`~/TheIgors/igor`) has a wait loop that sleeps 1s/iter while pause.wait exists, and removes it on fresh start. Akien added this 2026-03-12.
**How to apply:** Any time you need to stop Igor for DB schema changes, migrations, or destructive file edits.
