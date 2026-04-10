# sprint — Pick up a ticket, work it, report back

Invoke at the start of a focused work session. Loads context, claims a ticket,
works it, posts result to channel and queue. One ticket per sprint.

Arguments (optional):
  /sprint <ticket-id>    — work a specific ticket
  /sprint                — pick the next pending ticket by priority

---

## Step 0 — Pre-load deferred tools

The `Skill` tool is deferred — call ToolSearch first to load its schema, otherwise the first skill invocation fails with "Invalid tool parameters":

```
ToolSearch: select:Skill,Bash,Read,Edit,Grep,Glob
```

Do this before anything else. It is instant and silent.

---

## Step 1 — Load context

Run `/context-load` first. Get the briefing. Confirm session record is started in DB.

---

## Step 2 — Claim ticket

If ticket ID given: read it from queue.
If no ID: find next pending by priority:
```bash
python3 ~/TheIgors/lab/claudecode/cc_queue.py list
```

Mark ticket as in_progress:
```bash
python3 ~/TheIgors/lab/claudecode/cc_queue.py claim <ticket-id>
```

Post to channel:
```bash
python3 ~/TheIgors/lab/claudecode/channel.py post "claimed <ticket-id>: <title>" --as <tab>
```

Record in session:
```bash
DB=postgresql://igor:choose_a_password@127.0.0.1/Igor-wild-0001
IGOR_HOME_DB_URL=$DB python3 ~/TheIgors/lab/claudecode/session_manager.py append-change "sprint: started <ticket-id>"
```

---

## Step 2.5 — Write handoff note to slate

Write in-flight state immediately after claiming — before any code is written.
This survives auto-compact and budget-exhaustion session ends.

```bash
SLATE=~/.TheIgors/lab/claudecode/$(date +%Y%m%d).slate.txt
echo "" >> "$SLATE"
echo "## In-flight $(date +%H:%M) — <ticket-id>" >> "$SLATE"
echo "claimed: <ticket-id> — <title>" >> "$SLATE"
echo "status: implementation not started" >> "$SLATE"
```

Update this note as work progresses (after IMPLEMENT, after TEST). The last written state
is what context-load will see if the session dies. A clean close in Step 8 will replace it
with the done summary.

---

## Step 3 — Implement

Read every file before editing. Key gates:
- S/M size: implement directly after reading relevant files
- L size:
  - **Run /filter on the plan first.** If filter FAILS with blocking issues, stop and report before posting to channel or writing any code.
  - Log filter result to `~/.TheIgors/logs/worker_daemon.log`: `[filter] <ticket-id> result=PASS|FAIL ts=<timestamp>`
  - If `$WORKER_TICKET` env var is set (minion mode): post plan + filter result to channel then **proceed immediately** — the ticket being queued is the approval. Do NOT wait for user input.
  - If interactive (foreground) session: post plan + filter result to channel, wait for Akien approval before coding
- Forensic logging for non-trivial changes

Post progress updates to channel:
```bash
python3 ~/TheIgors/lab/claudecode/channel.py post "progress: <what just happened>" --as <tab>
```

---

## Step 4 — Test-fix

Run tests and fix any failures:
```
/test-fix
```

Do not proceed to probe until tests are green.

After tests pass, kill any lingering pytest zombie processes:
```bash
pkill -f "python.*pytest" 2>/dev/null; pkill -f "pytest.*tests/" 2>/dev/null; true
```

---

## Step 5 — Probe (if defined for this ticket)

Check if the ticket has a probe criterion:
```bash
python3 ~/TheIgors/lab/claudecode/cc_queue.py show <ticket-id> | grep -i "probe:"
```

If a `probe:` criterion exists: run `/probe <criterion>`.
If no criterion: skip this step.

---

## Step 6 — Audit

Run a quick audit scan on changed files:
```
/audit
```

Fix small findings now. Ticket anything bigger.

---

## Step 7 — Commit

**If running as minion** (`$WORKER_TICKET` env var is set): skip `/commit` entirely.
Minions do not commit. Commit is a human checkpoint — root session handles it.
Just proceed to Step 8.

**If running as root session** (interactive, no `$WORKER_TICKET`):
```
/commit
```

Stage only the files changed for this ticket. Never `git add -A`.

---

## Step 8 — Complete

Mark done and write result:
```bash
python3 ~/TheIgors/lab/claudecode/cc_queue.py done <ticket-id> "<one paragraph summary>"
```

Record in session:
```bash
DB=postgresql://igor:choose_a_password@127.0.0.1/Igor-wild-0001
IGOR_HOME_DB_URL=$DB python3 ~/TheIgors/lab/claudecode/session_manager.py append-change "sprint: closed <ticket-id> — <one line>"
```

Post completion to channel:
```bash
python3 ~/TheIgors/lab/claudecode/channel.py post "done: <ticket-id> — <one line summary>" --as <tab>
```

Update slate if this ticket was listed there:
```bash
IGOR_HOME_DB_URL=$DB python3 ~/TheIgors/lab/claudecode/slate_manager.py close-ticket <ticket-id>
IGOR_HOME_DB_URL=$DB python3 ~/TheIgors/lab/claudecode/slate_manager.py render
```

Run `/decided` to record any design decisions made during this sprint.

---

## Step 9 — Surface next + loop

```bash
python3 ~/TheIgors/lab/claudecode/cc_queue.py list
```

Post next ticket to channel. Then either:
- Start another sprint (if context is fresh and next ticket is related)
- End session with `/savestate` (if this is root Claude, not a minion)

The worker daemon picks up the next ticket automatically if running in a daemon konsole.

If this is a minion session (launched by worker_daemon.sh), write the done flag:
```bash
echo "<ticket-id>" > ~/.TheIgors/cc_channel/sprint_done.flag
```

The daemon watches for this flag and kills the Claude session, then loops to the next ticket.

---

## Hard rules

- One ticket per sprint — no scope creep
- L-size tickets: plan approval required before any code
- Never claim a ticket already marked in_progress by another session
- Always post to channel at start, on progress, and on completion
- Tests must pass before probe; probe must pass before commit
- Root Claude: run /savestate at end. Minion: exit cleanly, daemon loops.
