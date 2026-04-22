---
name: sprint
description: Claim a ticket, work it, commit, close it. Args: "last", ticket ID, or empty (next in queue).
model: sonnet
---

# /sprint — Claim, work, ship

## Args
- `/sprint last` — sprint the thing just discussed (must be ticketed)
- `/sprint T-xxx` — sprint a specific ticket
- `/sprint` — pick next pending ticket from queue

## Steps

### 1. Select ticket
```bash
python3 ~/TheIgors/lab/claudecode/cc_queue.py list 2>/dev/null | grep "⚪\|🟡"
```
No args: highest-priority pending. "last": most recently discussed ticket.
**No ticket = no work.** Run /ticket first if needed.

### 2. Claim ticket
```bash
python3 ~/TheIgors/lab/claudecode/cc_queue.py claim <id>
```
Add to today's slate.

### 3. Select executor
- **CC inline**: default
- **Haiku subagent**: mechanical/checklist work
- **Igor**: delegate via `mcp__igor__cc_send` for Igor-domain work

### 4. Review
State the plan. Check inertia levels, test coverage, scope boundary.
HIGH inertia files = discuss with Akien first.

### 5. Pull + work
```bash
git pull --rebase origin main
```
Do the work. Write code, tests, docs.

### 6. Cleanup (REQUIRED)
Review your diff:
```bash
git diff --stat && git diff
```
Remove: debug prints, commented-out code, unused imports, replaced functions,
single-use helpers (inline them), temp files. Every file in the diff = on purpose.

### 7. Test
```bash
cd ~/TheIgors && source venv/bin/activate && python -m pytest tests/ -x -q 2>&1 | tail -20
```

### 8. Commit + push
```bash
git add <specific files>
git commit -m "$(cat <<'EOF'
feat/fix/docs: description

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>
EOF
)"
git pull --rebase origin main && git push origin main
```

### 9. Close ticket
```bash
python3 ~/TheIgors/lab/claudecode/cc_queue.py done <id> "what was built"
IGOR_HOME_DB_URL=postgresql://igor:choose_a_password@127.0.0.1/Igor-wild-0001 \
  python3 ~/TheIgors/lab/claudecode/session_manager.py append-change "done: <id> — <summary>"
```
Move ticket to ## Done today in slate.

### 10. /savestateauto

## Hard rules
- Every sprint starts from a ticket — `/ticket` first if there isn't one.
- Cleanup (step 6) is the last pre-commit act of every sprint — debris review is load-bearing.
- Hooks run on every commit; pushes are non-force on main (integrity preserved).
- Stage files specifically by name — keeps `.env`, `*.db`, and `~/.TheIgors/` runtime paths off the commit.
- Tests pass + no secrets = commit without asking.
