---
name: savestate
description: End-of-session savestate for TheIgors project. Updates all persistent records — design docs, memory files, GitHub discussion — so the next session starts with full context. Use when the user says /savestate, "save state", "end of session", or "wrap up".
---

# Savestate — TheIgors End-of-Session Ritual

Run through this checklist in order. Do not skip steps. Each one is load-bearing for the next session.

## Step 1 — Summarise what changed this session

Before touching any file, produce a compact summary (internal, not shown to user unless asked):
- New files created
- Files modified and what changed (1 line each)
- Gaps closed (Gxx)
- New decisions made (Dxx)
- DB changes (habits added/modified, nodes deposited)
- Outstanding issues / next session priorities

## Step 2 — Update `design_docs/gap_analysis.md`

For each gap closed this session, add a `~~CLOSED YYYY-MM-DD~~` entry with:
- What was observed / what the root cause was
- What the fix was (code path, not prose)
- Result

For new gaps discovered, add them as open items with a short description and trigger condition.

Format: match the existing style in the file exactly.

## Step 3 — Update `design_docs_for_igor/gap_analysis.dsb`

Mirror the gap_analysis.md changes in DSB format. Closed gaps get `~~closed=YYYY-MM-DD~~`. New gaps get a new `Gxx|name|estimate|ticket=#nn` block.

## Step 4 — Update `design_docs_for_igor/decisions_log.dsb`

For each architectural decision made this session, append a `Dxx|short-name|implemented|one-line-description` entry under the appropriate section comment.

## Step 5 — Update affected subsystem DSBs

Only update files where something actually changed. Common ones:
- `subsystem_memory.dsb` — DB schema, cortex methods, db_proxy changes
- `subsystem_cognition.dsb` — basal_ganglia, thalamus, milieu, NE, habits
- `subsystem_inference.dsb` — tier ladder, reasoners, routing
- `subsystem_tools.dsb` — new tools, tool registry changes
- `subsystem_reading.dsb` — ebook_reader, book_learner changes
- `subsystem_self_edit.dsb` — self_edit, hot_reload changes

Update only the `updated=` date and the specific lines that changed. Do not rewrite the whole file.

## Step 6 — Update `memory/sessions.md`

Append a new session entry with:
```
## Session YYYY-MM-DDx
**Theme**: one line
**Closed**: Gxx, Gxx, Dxx
**Key changes**: bullet list, 1 line each
**Next session**: top 2-3 priorities
```

## Step 7 — Update `memory/MEMORY.md` if needed

If any persistent facts changed (latest commit hash, key architecture facts, known issues), update the relevant memory file and the MEMORY.md index.

## Step 8 — Update GitHub discussion #62

Post a comment to https://github.com/akienm/TheIgors/discussions/62 with:
- Session ID (YYYY-MM-DDx)
- What was built
- What was fixed
- Next session priorities

Use: `gh api repos/akienm/TheIgors/discussions/62/comments -f body="..."`

## Step 9 — Commit

Stage and commit all design_docs, design_docs_for_igor, claudecode, and memory changes with a message like:
`docs: savestate session YYYY-MM-DDx — [one-line theme]`

Do NOT commit runtime data, .env, or DB files.

---

## What NOT to do

- Do not rewrite DSB files from scratch — update in place
- Do not spend tokens re-reading files you already read this session
- Do not add speculative future plans to gap_analysis — only things that happened or were decided
- Do not commit source code changes as part of savestate — those should already be committed at logical checkpoints during the session
