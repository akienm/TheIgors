---
name: context-load
description: Session startup — palace briefing + slate + decisions + channel. 2000-token budget.
---

# context-load — Session startup

## Step 0 — Debug flag
```bash
touch ~/.TheIgors/Igor-wild-0001/debug_session.flag
```

## Step 1 — Today's slate
```bash
SLATE=~/.TheIgors/claudecode/$(date +%Y%m%d).slate.txt
if [ ! -f "$SLATE" ]; then
  mkdir -p "$(dirname "$SLATE")"
  cat > "$SLATE" <<EOF
# Slate $(date +%Y-%m-%d)

## Next up

## Blocked

## After that

## Decided

## Done
EOF
fi
cat "$SLATE"
```

Section order is salience-first (D-slate-salience-order-2026-04-20): read top-down,
stop once you have enough context. Next up = what to work on now; Blocked = candidates
to promote; After that = queue; Decided = this-session decisions; Done = shipped.

## Step 2 — Memory palace tree (what exists, where to look)
```bash
psql postgresql://igor:choose_a_password@127.0.0.1/Igor-wild-0001 -c \
  "SELECT path, title FROM memory_palace ORDER BY path" -t
```

The palace is the navigable map. Each node is a signpost — title + pointer to where the real info lives (code, DB, tools, docs). Query specific nodes with:
```bash
psql postgresql://igor:choose_a_password@127.0.0.1/Igor-wild-0001 -c \
  "SELECT title, content, pointers FROM memory_palace WHERE path = 'theigors/rules/coding'"
```

## Step 3 — Decisions hot window (last 10)
```bash
tail -10 ~/TheIgors/lab/design_docs_for_igor/decisions_log.dsb | sed 's/|/ — /g'
```

## Step 4 — Channel (last 5)
```bash
python3 ~/TheIgors/lab/claudecode/channel.py read 5
```

## Step 5 — Last session
```bash
DB=postgresql://igor:choose_a_password@127.0.0.1/Igor-wild-0001
IGOR_HOME_DB_URL=$DB python3 ~/TheIgors/lab/claudecode/session_manager.py show 1
```

## Step 5.5 — Pending approvals
```bash
python3 ~/TheIgors/lab/claudecode/cc_queue.py list 2>/dev/null | grep "🟠"
```

## Step 6 — Assemble briefing
Token budget: 2000 tokens (~8000 chars). Output:
```
CONTEXT LOAD — <timestamp>
Active: <ticket IDs from slate>
Palace: <node count + top-level branches>
Decisions: <one-line from tail>
Channel: <recent or "quiet">
[~NNN tokens]
Ready.
```

## Step 7 — Start session record (REQUIRED)
```bash
DB=postgresql://igor:choose_a_password@127.0.0.1/Igor-wild-0001
IGOR_HOME_DB_URL=$DB python3 ~/TheIgors/lab/claudecode/session_manager.py start "YYYY-MM-DDx" "Theme"
```

## Hard rules
- 2000 token budget max
- Never read more than 40 lines of any blob
- When a question maps to a palace branch, read that node — don't search the codebase blindly
- Palace is the index; code is the truth. If palace says X and code says Y, trust the code and update the palace.
