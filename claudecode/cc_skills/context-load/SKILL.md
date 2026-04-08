# context-load — Trail-based startup context

Invoke when starting a session, picking up a ticket, or when you need to orient quickly.
Reads the slate, finds relevant blobs, reads their tops. Returns a focused briefing.
No Igor required. No Postgres required.

---

## Step 0 — Write debug session flag (D273)

Suppress Igor's crash auto-fixer while Claude Code is active:
```bash
touch ~/.TheIgors/Igor-wild-0001/debug_session.flag
```

This flag tells the `igor` startup script not to launch the auto-fixer if Igor crashes
during this session (Claude Code is already present to diagnose).

---

## Step 1 — Create today's slate if missing, then read it

D304: slates are daily files at `~/.TheIgors/claudecode/YYYYMMDD.slate.txt`.

If today's slate does not exist, create a fresh one (no done tickets carried forward):

```bash
SLATE=~/.TheIgors/claudecode/$(date +%Y%m%d).slate.txt
if [ ! -f "$SLATE" ]; then
  mkdir -p "$(dirname "$SLATE")"
  cat > "$SLATE" <<EOF
# Slate $(date +%Y-%m-%d)

## Active

## Done today
EOF
  echo "Created fresh slate: $SLATE"
fi
cat "$SLATE"
```

The slate tells you:
- Active tickets (what's open now)
- Done today (already closed this day)

Tools reference (static — not repeated in slates):
- Skills: /sprint /deep-audit /decided /commit /savestate /fixit /context-load /day-close /audit /probe /notethat /slateclose /readigor
- MCP: mcp__igor__memory_get(id) · mcp__igor__cc_send(text) · mcp__igor__channel_read(limit=N)
- DB: psql postgresql://igor:choose_a_password@127.0.0.1/Igor-wild-0001
- Design docs: ~/TheIgors/design_docs_for_igor/ or mcp__igor__memory_get('D304')
- Epics: Claude · Cognition · Training · Operations · Database · Swarm · Productization

---

## Step 2 — Read decisions hot window (last 10)

```bash
tail -10 ~/TheIgors/design_docs_for_igor/decisions_log.dsb | sed 's/|/ — /g; s/^ *//'
```

Recent decisions are appended at the BOTTOM. `tail -10` gives the 10 most recent decisions — the actual hot window. Skip the foundational D001-D030 block (already stable, derivable from CLAUDE.md).

D330 note: pipe-delimited DSB renders to prose via sed. Prose is 7% more token-efficient and produces better LLM responses than pipe-delimited format.

---

## Step 3 — Read recent channel (last 5)

```bash
python3 ~/TheIgors/claudecode/channel.py read 5
```

See what other sessions have posted recently. Who is working on what.

---

## Step 4 — Read session last-change (if session active)

```bash
DB=postgresql://igor:choose_a_password@127.0.0.1/Igor-wild-0001
IGOR_HOME_DB_URL=$DB python3 ~/TheIgors/claudecode/session_manager.py show 1
```

Scan the `key_changes` field only — skip the rest. One line tells you where the session left off.

---

## Step 4.5 — Stale ticket check

Flag in_progress tickets not mentioned in today's slate (DB vs slate drift):

```bash
SLATE=~/.TheIgors/claudecode/$(date +%Y%m%d).slate.txt
python3 ~/TheIgors/claudecode/cc_queue.py list 2>/dev/null | grep "🔵" | \
  sed 's/.*\[\(T-[^]]*\)\].*/\1/' | while read tid; do
    grep -q "$tid" "$SLATE" 2>/dev/null || echo "⚠ STALE: $tid is in_progress but not in today's slate"
  done
```

If any stale tickets appear: surface them in the briefing and decide whether to re-claim or reset to pending.

---

## Step 5 — Assemble briefing with token budget

**Token budget: 2000 tokens (~8000 characters). Stop reading when approaching this limit.**

D305 load tree (in order, stop when budget is reached):
1. Today's dated slate (active tickets + done + Tools block)
2. decisions_log.dsb top 30
3. channel last 5
4. session last-change

The Tools block in the slate already lists: skills, MCP tools, DB connection, design_docs pointer, epics.
Do NOT load MEMORY.md, sessions.md, or gap_analysis as primary context — they are too large.

**Token counting heuristic**: ~4 characters ≈ 1 token (for English prose). To estimate tokens:
```
(total_characters_read) / 4 = approximate_tokens
```

Output format:
```
CONTEXT LOAD — <timestamp>
Active: <ticket IDs>
Design thread: <one line from decisions top>
Channel: <recent activity or "quiet">
Do not touch: <files/areas in use by another session>
[Token count: ~NNN tokens]
Ready.
```

---

## ⛔ Step 6 — Start session record in DB (REQUIRED — do not skip)

Check if a session is already in progress (e.g. prior tab or crash recovery):
```bash
DB=postgresql://igor:choose_a_password@127.0.0.1/Igor-wild-0001
python3 ~/TheIgors/claudecode/session_manager.py current
IGOR_HOME_DB_URL=$DB python3 ~/TheIgors/claudecode/session_manager.py show 1
```
If a prior unfinalized session exists, surface it in the briefing: "previous session Xxx has partial record — last change: Y"

Determine the session ID: today's date + next letter (check `show 3` to see what's used).
**Start the session before doing any work:**
```bash
IGOR_HOME_DB_URL=$DB python3 ~/TheIgors/claudecode/session_manager.py start "YYYY-MM-DDx" "Theme: one line"
```
This creates a partial record AND writes `~/.TheIgors/cc_channel/current_session.txt`.
**Without this, /decided has nowhere to record changes.** Crash loses nothing — key changes accumulate via /decided without any ID argument.

---

## Hard rules

- **Token budget: 2000 tokens max (~8000 characters).** Stop adding context when cumulative character count approaches this limit.
- Never read more than 40 lines of any blob — if you need more, something is wrong with the blob
- Never load CLAUDE.md as your primary context — slate + blob tops replace it
- If slate is missing: fall back to MEMORY.md + decisions top + channel read
