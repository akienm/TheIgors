---
name: fixit
description: Quick-fix loop for TheIgors. Ticket → Filter → Sprint → Slate. Use when Akien says /fixit, "fix this", or "quick fix for X".
model: haiku
model_exception: Step 3 (/sprint) runs under Sonnet — implementation requires full reasoning capability.
---

# fixit — Triage → Ticket → Filter → Sprint

Primary job: ensure everything is ticketed. Filter and sprint follow for S/M
items that are ready to work now. L items get ticketed and queued — they need
plan approval separately.

Use when: Akien has one or more things to fix, ideas to queue, or descriptions
of gaps. Can be a single bug or a list of improvements. /fixit makes sure
nothing falls through without a ticket.

Arguments:
  /fixit <description>           — ticket one item, then work it
  /fixit <ticket-id>             — pick up existing ticket, work it
  /fixit <item1> / <item2> / … — ticket multiple items, work S/M ones in order

---

## Step 1 — Ticket everything

For each item (description or ticket ID) in the argument list:

If it's an existing ticket ID, read it:
```bash
python3 ~/TheIgors/claudecode/cc_queue.py show <ticket-id>
```

If it's a description with no ticket, create one:
```bash
python3 ~/TheIgors/claudecode/cc_queue.py add "<title>" "<one-line description>" --priority 2
```

Add each ticket to today's slate:
```bash
DB=postgresql://igor:choose_a_password@127.0.0.1/Igor-wild-0001
IGOR_HOME_DB_URL=$DB python3 ~/TheIgors/claudecode/slate_manager.py add-ticket 0 "<ticket-id>" "<title>"
```

After all tickets are created, print a summary table:
| # | Ticket ID | Title | Size |
|---|-----------|-------|------|

Classify size (S/M/L) based on scope. If unsure, default to M.

---

## Step 2 — Separate S/M from L

- **S/M tickets**: proceed to Step 3 for each, in order
- **L tickets**: stop here. Flag them: "L ticket <id> queued — needs plan approval before sprint."

If ALL tickets are L, end here. Slate is updated; that's enough.

---

## Step 3 — Plan + Filter + Sprint (S/M only, one at a time)

For each S/M ticket:

**3a. State the plan** (one paragraph):
- What file(s) change (with inertia level)
- What the fix does
- What test verifies it
- What is NOT changing (scope boundary)

**3b. Run /filter** on the plan. Fix any blocking issues. Non-blocking notes: proceed and annotate.

**3b.5 Write handoff note to slate** (before sprint starts):
```bash
SLATE=~/.TheIgors/claudecode/$(date +%Y%m%d).slate.txt
echo "" >> "$SLATE"
echo "## In-flight $(date +%H:%M) — <ticket-id>" >> "$SLATE"
echo "claimed: <ticket-id> — <title>" >> "$SLATE"
echo "status: fixit — entering sprint" >> "$SLATE"
```
This survives auto-compact and budget-exhaustion. Sprint Step 8 replaces it with the done summary.

**3c. Run /sprint <ticket-id>**

Sprint handles: implement → test-fix → probe → record → close ticket → render slate.

---

## Step 4 — Confirm slate

After all S/M tickets are worked, render the slate:
```bash
DB=postgresql://igor:choose_a_password@127.0.0.1/Igor-wild-0001
IGOR_HOME_DB_URL=$DB python3 ~/TheIgors/claudecode/slate_manager.py render
```

Print the P1/P2 section so Akien can see what landed and what's queued.

---

## Hard rules

- Always ticket before working — the ticket is truth, not the conversation
- Always add to slate before working — the slate is truth
- L tickets get ticketed and stopped — never sprint an L without plan approval
- If scope expands mid-sprint, stop, ticket the new scope, return to Step 1
