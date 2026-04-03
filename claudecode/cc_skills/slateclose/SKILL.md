---
name: slateclose
description: Closes the current work slate for TheIgors project. Reviews open tickets, notes what's done/deferred/carried, posts summary to GitHub discussion. D304: slates are daily dated files — no archive step needed. Use when Akien says /slateclose, "close the slate", "wrap up this slate", or "start a fresh slate".
model: haiku
---

# Slateclose — Close the Current Work Slate

Runs when a slate of work is complete or at a natural break point.
Not the same as day-close — a day can have multiple slates.
Not the same as savestate — session state is separate from slate state.

D304: Slates are daily dated files at `~/.TheIgors/claudecode/YYYYMMDD.slate.txt`.
Each file IS the archive. No copy/clear step needed — just render the final state.

---

## Step 1 — Review open tickets

```bash
python3 ~/TheIgors/claudecode/cc_queue.py list
```

Categorize each ticket:
- **Done this slate**: closed during this slate
- **Deferred**: not started, pushed to next slate
- **Carried**: in-progress or partially done, continues next slate

---

## Step 2 — Render final slate

Write the final done/active state to today's dated file:

```bash
DB=postgresql://igor:choose_a_password@127.0.0.1/igor_wild_0001
IGOR_HOME_DB_URL=$DB python3 ~/TheIgors/claudecode/slate_manager.py render
```

The dated file at `~/.TheIgors/claudecode/$(date +%Y%m%d).slate.txt` is the record.
No copying or clearing — tomorrow's `/context-load` reads tomorrow's file.

---

## Step 3 — Post slate summary to GitHub discussion #62

Compose a 3-5 bullet summary and post:

```bash
gh api graphql -f query='mutation {
  addDiscussionComment(input: {
    discussionId: "D_kwDORR89g84AkjSM",
    body: "## Slate close YYYY-MM-DDx — <theme>\n\n**Done**: ...\n**Deferred**: ...\n**Carried to next slate**: ...\n**Next slate focus**: ..."
  }) { comment { id } }
}'
```

---

## Step 4 — Optionally trigger day-close

If this is the last slate of the day: run `/day-close`.
If more slates are planned today: skip.

---

## Hard rules

- Never delete dated slate files — they're the record
- D304: each day's file is self-contained; no slate.md to clear
- Carried tickets stay in queue as in_progress — do not close them
