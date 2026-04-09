---
name: notethat
description: Bookmark the current conversation topic before it evaporates. Lighter than /decided — no decision required, no DB write required. Captures "what we just talked about" into a note file AND appends a headline to today's slate so context-load picks it up. Use when the user says /notethat, "note that", "capture this", "don't lose this", or "bookmark this".
---

# Notethat — Conversation Bookmark

Captures the current topic as a durable note before it's lost to context scroll or session end.
Lighter than /decided — no architecture decision required, no session record required.
The full note lands in a dated notes file; a one-liner headline lands in today's slate.

---

## Step 1 — Identify what to capture

From the last few exchanges, identify:
- The core fact, insight, list, or decision fragment being discussed
- Why it matters (one sentence)
- Any action implied (ticket needed? list to rebuild? fix to make?)

Judgment call on depth: capture a single sentence or a full conversation excerpt — whatever preserves the idea faithfully. If ambiguous: ask "what specifically should I capture?" before proceeding.

---

## Step 2 — Write to a note file

Write to `~/.TheIgors/cc_channel/notes/YYYY-MM-DD_<slug>.md`:

```bash
mkdir -p ~/.TheIgors/cc_channel/notes
```

Format:
```markdown
# <topic in one line>
Date: YYYY-MM-DDThh:mm
Session: <current session ID if known>

## What
<sentence, paragraph, or full conversation excerpt — whatever the idea needs>

## Why it matters
<one sentence>

## Action implied
<ticket ID if one was created, or "none" or "TBD">
```

---

## Step 3 — Append headline to today's slate

```bash
SLATE=~/.TheIgors/claudecode/$(date +%Y%m%d).slate.txt
echo "" >> "$SLATE"
echo "## Note $(date +%H:%M) — <slug>" >> "$SLATE"
echo "<one-liner summary of what was captured>" >> "$SLATE"
```

This is what context-load will see next session. The full content lives in the notes file.

---

## Step 4 — Confirm to user

Say: "Noted: <one-line summary> → `~/.TheIgors/cc_channel/notes/<filename>`"

---

## What /notethat is NOT

- Not a design decision — use /decided for that
- Not a task — use cc_queue.py add for that
- Not a savestate — that's end of session
- Not a memory update — that's for durable cross-session facts

It's a bookmark. Fast, lightweight — survives session end and context compaction.
The slate headline means it survives context-load too.
