---
name: sprint-minion
description: Push a ticket to the worker daemon queue and signal it to start. Use when Akien says /sprint-minion <id>, "push to daemon", or "let the daemon handle it".
---

# sprint-minion — Push Ticket to Worker Daemon

Marks a ticket as pending with worker=cc, ensures the daemon is running, and posts to channel.
The daemon polls every 20 seconds and will pick it up automatically.

Arguments: `/sprint-minion <ticket-id>`

---

## Step 1 — Validate ticket

Read the ticket:
```bash
python3 ~/TheIgors/lab/claudecode/cc_queue.py show <ticket-id>
```

If ticket doesn't exist: stop with error.
If ticket is already `in_progress`: warn — daemon may be working it already. Ask before resetting.
If ticket is `done`: stop — nothing to push.

---

## Step 2 — Reset to pending (if not already pending)

If ticket is `in_progress` and user confirmed reset:
```bash
python3 ~/TheIgors/lab/claudecode/cc_queue.py reset <ticket-id>
```

If ticket is already `pending`: skip this step.

---

## Step 3 — Ensure daemon is running

```bash
python3 ~/TheIgors/lab/claudecode/cc_queue.py worker-launch
```

This is idempotent — if the daemon is already running it does nothing harmful.
Note the output (daemon PID or "already running").

---

## Step 4 — Post to channel

```bash
python3 ~/TheIgors/lab/claudecode/channel.py post "sprint-minion: pushed <ticket-id> to worker queue — daemon will pick up within 20s" --as cc
```

---

## Step 5 — Report

Tell Akien:
- Ticket ID and title
- Daemon status (launched / already running)
- Estimated pickup: within 20 seconds

The daemon will:
1. Claim the ticket
2. Run `claude /sprint <ticket-id>` in a background konsole
3. Post progress to channel
4. Close the ticket when done

To monitor: run `/readigor` or `python3 ~/TheIgors/lab/claudecode/channel.py read 10`

---

## Hard rules

- Never push a ticket that is already `in_progress` without explicit confirmation
- Never push L-size tickets without plan approval — they need Akien review first
- Daemon handles commit + close loop — root Claude should NOT also sprint the same ticket
