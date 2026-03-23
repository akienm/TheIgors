---
name: decided
description: Post-discussion record for TheIgors. "These points are decided." Records design decisions to DB/DSB, runs plan check if work was planned, updates tickets. Use when Akien says /decided, "that's decided", "we've decided", or at the end of any planning discussion.
---

# Decided — Post-Discussion Record

Fires when a discussion concludes. "These points are decided."
The action taken depends on what type of conclusion was reached.

---

## Step 1 — What was decided?

Identify the type(s) of conclusion:
- **Design decision** (Dxxx): architectural choice made → go to Step 2
- **Work plan**: tasks agreed, ready to implement → go to Step 3
- **Work complete**: unit of work finished → go to Step 4
- **Multiple**: do all that apply

---

## Step 2 — Record design decisions

For each Dxxx decided:

```bash
DB=postgresql://igor:choose_a_password@127.0.0.1/igor_wild_0001
IGOR_HOME_DB_URL=$DB python3 ~/TheIgors/claudecode/decision_manager.py add Dxxx "short-name" "status" "one-line description"
IGOR_HOME_DB_URL=$DB python3 ~/TheIgors/claudecode/session_manager.py append-decision Dxxx
```

This atomically: updates decisions_log.dsb header + appends line, upserts to docs_entries, flushes to Igor memory.

---

## Step 3 — If work was planned: run plan check

Run `/filter` on the plan before any tickets are created or work starts:

```
/filter
```

Fix any blocking issues. If Akien explicitly overrides a filter failure: note it and proceed.

Then update tickets:

```bash
# Add new tickets
python3 ~/TheIgors/claudecode/cc_queue.py add "title" "description" --priority N

# Update existing tickets
python3 ~/TheIgors/claudecode/cc_queue.py update <ticket-id> "updated description"
```

Accumulate in session record:
```bash
DB=postgresql://igor:choose_a_password@127.0.0.1/igor_wild_0001
IGOR_HOME_DB_URL=$DB python3 ~/TheIgors/claudecode/session_manager.py append-change "decided: <what was planned>"
```

---

## Step 4 — If work was completed: record key change

```bash
DB=postgresql://igor:choose_a_password@127.0.0.1/igor_wild_0001
python3 ~/TheIgors/claudecode/cc_queue.py done <task-id> "what was built + test status"
IGOR_HOME_DB_URL=$DB python3 ~/TheIgors/claudecode/session_manager.py append-change "done: <what was built>"
```

---

## Step 5 — Savestate if session is winding down

If this was a major planning session or the session is ending: run `/savestate`.
Otherwise skip — savestate runs at natural session end.

---

## What /decided is NOT

- Not a commit — commit separately with `/commit`
- Not a day-close — that's separate
- Not a savestate on its own — only triggers savestate when session is winding down
