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

## Step 1 — Read the slate

```bash
cat ~/.TheIgors/cc_channel/slate.md
```

The slate tells you:
- What's actively being worked (tickets)
- Which blobs are relevant and where they live
- One-paragraph current context

---

## Step 2 — Read blob tops

For each blob listed in the slate, read the top 40 lines only:

```bash
head -40 <blob-path>
```

Blobs are newest-first (prepend convention). The top is the hottest context.
Stop reading when you have enough. You rarely need the bottom.

Standard blobs (always read if no slate):
- `~/.claude/projects/-home-akien-TheIgors/memory/MEMORY.md` — project memory index
- `~/.TheIgors/cc_channel/messages.jsonl` — recent channel activity (last 10 lines)
- `~/TheIgors/design_docs_for_igor/decisions_log.dsb` — top 30 lines = recent decisions

---

## Step 3 — Read recent channel

```bash
python3 ~/TheIgors/claudecode/channel.py read 10
```

See what other sessions have posted recently. Who is working on what.

---

## Step 4 — Assemble briefing with token budget

**Token budget: 2000 tokens (~8000 characters). Stop reading when approaching this limit.**

Synthesize into 5-10 lines:
- Current active tickets
- Key design context (1-2 sentences per active area)
- What other sessions are doing (if any)
- What you should NOT touch (in-progress by another session)

**Token counting heuristic**: ~4 characters ≈ 1 token (for English prose). To estimate tokens:
```
(total_characters_read) / 4 = approximate_tokens
```

Stop reading blob tops when cumulative character count approaches 8000 (≈2000 tokens).
If you've read slate + 1-2 blob tops + channel, you're usually well within budget.

Output format:
```
CONTEXT LOAD — <timestamp>
Active: <ticket IDs>
Design thread: <one line>
Channel: <recent activity or "quiet">
Do not touch: <files/areas in use>
[Token count: ~NNN tokens]
Ready.
```

---

## ⛔ Step 5 — Start session record in DB (REQUIRED — do not skip)

Check if a session is already in progress (e.g. prior tab or crash recovery):
```bash
DB=postgresql://igor:choose_a_password@127.0.0.1/igor_wild_0001
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
