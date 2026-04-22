---
name: context-load
description: Session startup — palace briefing + slate + decisions + channel. 2000-token budget.
model: haiku
---

# context-load — Session startup

## Step 0 — Environment key check (runs first)
```bash
CC_KEY="${REAL_ANTHROPIC_API_KEY:-}"
OR_KEY="${OPENROUTER_API_KEY:-}"
if [ -z "$CC_KEY" ]; then
  echo "⚠ REAL_ANTHROPIC_API_KEY not set — CC may be using wrong key. Check superclaude handoff."
elif [[ "$CC_KEY" != sk-ant-* ]]; then
  echo "⚠ REAL_ANTHROPIC_API_KEY does not look like an Anthropic key (expected sk-ant-...). Check superclaude handoff."
else
  echo "env: CC key OK (${CC_KEY:0:14}...)"
fi
if [ -n "$OR_KEY" ]; then
  echo "⚠ OPENROUTER_API_KEY is set in CC env — Igor's key may have leaked. Expected empty. Check superclaude."
fi
```

## Step 0.5 — Debug flag
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

## Step 2a — Rules (hash-gated; read these FIRST when changed)
```bash
HASH_FILE=~/.TheIgors/claudecode/rules_hash.txt
CURRENT_HASH=$(psql postgresql://igor:choose_a_password@127.0.0.1/Igor-wild-0001 -tAc \
  "SELECT md5(string_agg(path || '|' || coalesce(content,''), '||' ORDER BY path))
   FROM memory_palace WHERE path LIKE 'theigors/rules/%'")
SAVED_HASH=$(cat "$HASH_FILE" 2>/dev/null | head -1)
if [ "$CURRENT_HASH" = "$SAVED_HASH" ]; then
  echo "rules: unchanged since last session (hash=${CURRENT_HASH:0:8}...) — skipping full load"
else
  echo "rules: changed (${SAVED_HASH:0:8}... → ${CURRENT_HASH:0:8}...) — loading"
  psql postgresql://igor:choose_a_password@127.0.0.1/Igor-wild-0001 -c \
    "SELECT title, content FROM memory_palace
     WHERE path LIKE 'theigors/rules/%' ORDER BY path" -tA
  echo "$CURRENT_HASH" > "$HASH_FILE"
fi
```

Canonical rules live in the palace DB (T-rules-canonical-db-first, 2026-04-20).
CLAUDE.md is a thin shim — palace wins on conflict. Read order: persona →
coding → commits → memory → database → budget → collaboration →
igor-constraints → docs-live-in-code → do-not.

## Step 2b — Memory palace tree (hash-gated)
```bash
TREE_HASH_FILE=~/.TheIgors/claudecode/palace_tree_hash.txt
CURRENT_TREE_HASH=$(psql postgresql://igor:choose_a_password@127.0.0.1/Igor-wild-0001 -tAc \
  "SELECT md5(string_agg(path || '|' || coalesce(title,''), '||' ORDER BY path)) FROM memory_palace")
SAVED_TREE_HASH=$(cat "$TREE_HASH_FILE" 2>/dev/null | head -1)
if [ "$CURRENT_TREE_HASH" = "$SAVED_TREE_HASH" ]; then
  echo "palace tree: unchanged (hash=${CURRENT_TREE_HASH:0:8}...) — skipping listing"
else
  psql postgresql://igor:choose_a_password@127.0.0.1/Igor-wild-0001 -c \
    "SELECT path, title FROM memory_palace ORDER BY path" -t
  echo "$CURRENT_TREE_HASH" > "$TREE_HASH_FILE"
fi
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
- 2000 token budget max.
- Per-blob read cap: 40 lines.
- When a question maps to a palace branch, read that node — palace-first over codebase grep.
- Palace is the index; code is the truth. If palace says X and code says Y, trust the code and update the palace.
