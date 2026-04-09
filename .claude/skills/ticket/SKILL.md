---
name: ticket
description: Quick-capture a ticket to the cc_queue without context switching. Use when the user says /ticket, "add a ticket", "quick ticket", or "queue this idea". Arguments are the ticket description.
---

# ticket — Quick Capture to Queue

One command captures an idea as a pending ticket. No scope discussion needed now — that happens next time we look at the queue.

---

## Step 1 — Parse the description

Arguments are the ticket description (everything after `/ticket`).

If no arguments: ask "What's the ticket description?" (one prompt only).

From the description, infer:
- A short title (≤ 60 chars)
- A longer description (the original text, with any obvious context added)
- Size guess: S / M / L / ? (default `?` if unclear)
- Priority: 1-5 (default 3)
- Tags: infer from content — Cognition, Training, Operations, Claude, Swarm, Database, Productization

---

## Step 2 — Generate a ticket ID

Format: `T-<kebab-slug>` from the title (lowercase, hyphens, max 5 words).
Example: "add webhook retry logic" → `T-webhook-retry`

Check for collision:
```bash
python3 ~/TheIgors/claudecode/cc_queue.py list 2>/dev/null | grep "<proposed-id>"
```
If collision: append `-2`, `-3`, etc.

---

## Step 3 — Add to queue

```bash
python3 ~/TheIgors/claudecode/cc_queue.py add \
  --id "<id>" \
  --title "<title>" \
  --description "<full description> — deferred: scope/priority TBD" \
  --size "<S|M|L|?>" \
  --priority <1-5> \
  --tags "<tag1>,<tag2>"
```

---

## Step 4 — Post to channel

```bash
python3 ~/TheIgors/claudecode/channel.py post "queued <id>: <title>" --as tab
```

---

## Step 5 — Confirm to user

Reply with one line: `Queued <id>: <title>` and the inferred size/priority.
Do NOT start discussing scope or implementation — this is quick-capture only.

---

## Hard rules

- Never claim the ticket immediately after adding it
- Never expand into a sprint — this is capture only
- If the description is ambiguous: add it as-is with a "deferred: needs clarification" note
- Always post to channel so other sessions see new items
