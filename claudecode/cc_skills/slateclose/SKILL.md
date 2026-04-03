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

## Step 3 — Post slate summary to today's GitHub Discussion

If today's GitHub Discussion was already created (day-close creates it): add a comment to it.
If this is the only slate and no Discussion exists yet: create one now (same as day-close Step 10).

**Add comment to existing Discussion** (if you know the day's discussion number):
```bash
# Replace D_kwDORR89g84Axxx with today's discussion node ID
gh api graphql -f query='mutation {
  addDiscussionComment(input: {
    discussionId: "D_kwDORR89g84Axxx",
    body: "## Slate close YYYY-MM-DDx — <theme>\n\n**Done**: ...\n**Deferred**: ...\n**Carried**: ...\n**Next**: ..."
  }) { comment { id } }
}'
```

**Create new Discussion** (if none exists yet today):
```bash
# Repo: R_kgDORR89gw  Category General: DIC_kwDORR89g84C3wqk
gh api graphql -f query='mutation {
  createDiscussion(input: {
    repositoryId: "R_kgDORR89gw",
    categoryId: "DIC_kwDORR89g84C3wqk",
    title: "Day YYYY-MM-DD — <theme>",
    body: "## Done\n- ...\n\n## Deferred\n- ...\n\n## Next\n- ..."
  }) { discussion { number url } }
}'
```

#62 is the master plan — do not post slate summaries there.

---

## Step 4 — Optionally trigger day-close

If this is the last slate of the day: run `/day-close`.
If more slates are planned today: skip.

---

## Hard rules

- Never delete dated slate files — they're the record
- D304: each day's file is self-contained; no slate.md to clear
- Carried tickets stay in queue as in_progress — do not close them
