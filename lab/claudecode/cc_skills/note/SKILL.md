---
name: note
description: Log a milestone, insight, or decision to notes.log. Replaces /decided for non-ticket items.
---

# /note — Log a notable event

Append to `~/TheIgors/lab/notes.log`:
```
<ISO datetime> | <note text> | <related tickets if any>
```

Example:
```bash
echo "$(date -Iseconds) | Haiku extracts 15 nodes vs gpt-4o-mini's 10 — Haiku is the reading model | T-reading-benchmark" >> ~/TheIgors/lab/notes.log
```

Also append to session key_changes:
```bash
DB=postgresql://igor:choose_a_password@127.0.0.1/Igor-wild-0001
IGOR_HOME_DB_URL=$DB python3 ~/TheIgors/lab/claudecode/session_manager.py append-change "note: <summary>"
```

That's it. No DSB writes, no decision pipeline. Just a timestamped log line.
