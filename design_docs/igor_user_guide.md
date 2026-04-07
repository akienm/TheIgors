# Igor User Guide

*Updated: 2026-04-01*

The practical reference for running, talking to, and maintaining Igor.
For architecture, see `design_docs/ProjectOverview.md`.
For the lab directory map, see `design_docs/lab_map.md`.

---

## Getting Started

### Prerequisites

1. Clone the repo: `git clone https://github.com/akienm/TheIgors ~/TheIgors`
2. Create venv: `python3 -m venv ~/TheIgors/venv && pip install -r ~/TheIgors/wild_igor/requirements.txt`
3. Symlink launcher: `ln -s ~/TheIgors/igor ~/bin/igor`
4. Run `igor` — first-start wizard creates `~/.TheIgors/Igor-wild-0001/.env`
5. Edit `.env` to add `OPENROUTER_API_KEY` and `OLLAMA_HOST`
6. Run `igor` again — Igor starts

### Databases

Igor uses **PostgreSQL** (not SQLite). The DB is at `localhost/Igor-wild-0001`.
The DB is pre-created; Igor's migration system applies schema on first boot.

```bash
# Check DB is live
psql -U igor -d Igor-wild-0001 -c "SELECT count(*) FROM memories;"

# Never delete wild-0001.db — it's the live runtime DB
# Never use sqlite3 on Igor's data — always psql or psycopg2
```

---

## Launching Igor

```bash
igor                          # Start instance Igor-wild-0001 (default)
igor --id igor_wild_0002      # Start a different instance

# Keep terminal open after crash (KDE):
DISPLAY=:0 konsole -e bash -c "igor; exec bash" &

# Igor restarts automatically on exit code 42 (restart signal)
# Igor stays down on any other non-zero exit
```

### Pausing / Resuming

```bash
touch ~/TheIgors/pause.wait   # Igor loops idle (waits before next restart)
rm ~/TheIgors/pause.wait      # Resume
```

### Checking if Igor is Running

```bash
pgrep -f "igor\.main"         # Returns PIDs if running
curl -s http://localhost:8080/api/dashboard | python3 -m json.tool | head -20
```

---

## In-Session Commands

Type these directly into Igor's terminal prompt:

| Command | What It Does |
|---|---|
| `/help` | Show command list + current model/local state |
| `/memories` | Show recent memories (FIFO ring) |
| `/core` | Show core identity memories |
| `/habits` | List active habits (trigger + type) |
| `/metrics` | Show cognition metrics snapshot |
| `/cost` | Show session cost breakdown |
| `/model` | Show current model routing |
| `/local` | Toggle local mode (Ollama-only, no cloud) |
| `/routing` | Show escalation weaning analysis (G37) |
| `/cloud` | Force next turn to cloud |
| `/jobs` | List active background jobs |
| `/orders` | Show pending arbiter orders |
| `/relay` | Sudo relay status |
| `/implement` | Trigger agentic implementation mode |
| `/notebook` | Open notebook tool |
| `/sleep` | Pre-sleep ritual (summarize + compress) |
| `/compress` | Compress conversation context |
| `/arbiter` | Arbiter queue status |
| `/restart` | Restart Igor (re-reads .env) |
| `/quit` or `/exit` | Exit cleanly |

---

## Igor Tools (callable via cc_send or habit trigger)

These are registered tools Igor can invoke. Send via `cc_send` to trigger by name,
or they fire automatically when a matching habit is active.

### Goal / Task Management

| Tool | Args | What It Does |
|---|---|---|
| `goal_adopt` | `task: str` | Adopt a goal; stores as active GOAL memory at high salience |
| `goal_close` | `goal_id: str` | Close a goal by memory ID (sets goal_active=False) |
| `close_goal_by_ticket` | `ticket_id: str` | Close active GOAL whose source_message contains ticket_id |
| `goal_fail_active` | — | Mark the current active goal as failed |
| `goal_scan` | — | Report all active GOAL memories |
| `run_goal_continuation` | — | D274: drive mechanical steps on active GOAL (claim→show→grep→ready) |
| `adopt_top_queue_ticket` | — | D278: check queue.json, adopt top pending ticket as new goal |
| `read_queue_top` | — | Return top pending ticket from queue.json (no adoption) |
| `queue_task` | `task: str` | Add a task to the cc_queue |

### Memory / Knowledge

| Tool | Args | What It Does |
|---|---|---|
| `store_decision` | `text: str` | Store a design decision as INTERPRETIVE memory |
| `store_session_note` | `text: str` | Store a session note as EPISODIC memory |
| `flush_habit_cache` | — | Flush the BG habit score cache (after seeding new habits) |

### Monitoring / Diagnostics

| Tool | Args | What It Does |
|---|---|---|
| `get_escalation_stats` | — | D279: cloud escalation trend — this week vs last week, grouped by topic |

---

## Claude Code Skills (available in CC sessions)

Type `/skill-name` in a Claude Code session. All skills live in `~/.claude/skills/` (synced from `claudecode/cc_skills/`).

| Skill | What It Does |
|---|---|
| `/context-load` | Trail-based session startup — reads slate, blob tops, channel, starts session record |
| `/savestate` | End-of-session ritual — flush summary, record decisions, finalize session, commit |
| `/decided` | Record a design decision or work completion mid-session |
| `/sprint` | Worker session — reads ticket, implements, reports, exits |
| `/filter` | Pre-implementation plan verification checklist |
| `/audit` | Full subsystem audit against design docs |
| `/fixit` | Ticket + filter + implement loop |
| `/review` | Code review against Igor conventions |
| `/commit` | Structured git commit with session record |
| `/readigor` | Read Igor's recent channel output (supports machine arg: akiendell/yoga9i/yogai7) |
| `/probe` | Send a test message to Igor and observe response |
| `/slate` | Render/update the active work slate |
| `/slateclose` | Close completed slate items |
| `/day-close` | End-of-day ritual (gap analysis, subsystem DSBs, GitHub discussion, commit) |
| `/notethat` | Quick note to session record |
| `/validate-files` | Check file integrity / inertia before editing |
| `/igor` | Igor meta-skill (diagnose, inspect, send commands) |
| `/test-fix` | Run failing tests and iterate until green |

---

## Web Dashboard

Igor runs a web server at `http://localhost:8080` (or `IGOR_WEB_PORT` in .env).

```
http://localhost:8080/          # Chat interface
http://localhost:8080/api/dashboard  # JSON status: sessions, milieu, jobs
http://localhost:8080/api/cc_send    # POST {"content":"..."} — inject as claude-code
```

---

## Claude Code → Igor Bridge

From a Claude Code session, inject messages into Igor:

```bash
# Send a message to Igor
python3 ~/TheIgors/claudecode/channel.py send "CC: check your habits"

# Or via POST
curl -s -X POST http://localhost:8080/api/cc_send \
  -H "Content-Type: application/json" \
  -d '{"content": "CC: your message here"}'

# Read recent channel (all participants)
python3 ~/TheIgors/claudecode/channel.py read 20

# Read Igor's replies only (filter for author: igor)
python3 ~/TheIgors/claudecode/channel.py read 20 | grep -A3 '"author": "igor"'
```

---

## Logs

All logs live in `~/.TheIgors/logs/`. See `design_docs/lab_map.md` for the full log reference.

### Most Useful Logs

```bash
# What happened today (every turn: tier, cost, input, output)
tail -50 ~/.TheIgors/logs/interaction.$(date +%Y%m%d).log

# Why did Igor go to cloud? (escalation story)
tail -30 ~/.TheIgors/logs/escalation.log

# Recent errors
tail -30 ~/.TheIgors/logs/errors.log

# Self-training activity (did the training loops run?)
grep "output_training\|self_training" ~/.TheIgors/logs/cognition_metrics.log | tail -20

# What tools did Igor use?
tail -30 ~/.TheIgors/logs/tool_calls.log

# Full BG scoring for a specific turn (habit match detail)
grep "<turn_id>" ~/.TheIgors/logs/turn_trace.$(date +%Y%m%d).log
```

---

## Claude Code Tooling (`claudecode/`)

Operator scripts for seeding, maintenance, and session management.

### Session Management

```bash
DB=postgresql://igor:choose_a_password@127.0.0.1/Igor-wild-0001

# Start a session record
IGOR_HOME_DB_URL=$DB python3 ~/TheIgors/claudecode/session_manager.py start "2026-03-26a" "Theme: one line"

# Record a decision
IGOR_HOME_DB_URL=$DB python3 ~/TheIgors/claudecode/decision_manager.py add D123 "short-name" "status" "one-line description"

# Finalize session
IGOR_HOME_DB_URL=$DB python3 ~/TheIgors/claudecode/session_manager.py finalize "2026-03-26a" "Next: ..." "In-flight: ..."

# Flush summary to Igor memory
python3 ~/TheIgors/claudecode/cc_queue.py flush_session 2026-03-26a "theme: ...; next: ..."
```

### Task Queue

```bash
# Add a task (writes JSON to temp file, passes path)
cat > /tmp/task.json <<'EOF'
{"title": "Task title", "description": "What to do", "priority": 2}
EOF
python3 ~/TheIgors/claudecode/cc_queue.py add /tmp/task.json

# List tasks
python3 ~/TheIgors/claudecode/cc_queue.py list

# Mark done
python3 ~/TheIgors/claudecode/cc_queue.py done <task-id> "what was built"
```

### Seeding Habits (one-time scripts)

```bash
DB=postgresql://igor:choose_a_password@127.0.0.1/Igor-wild-0001

# Seed a specific habit (safe to re-run — all upsert on conflict)
IGOR_HOME_DB_URL=$DB python3 ~/TheIgors/claudecode/seed_self_training_habit.py
IGOR_HOME_DB_URL=$DB python3 ~/TheIgors/claudecode/seed_output_training_habit.py
IGOR_HOME_DB_URL=$DB python3 ~/TheIgors/claudecode/seed_routing_habits.py
# ... (see claudecode/ for full list of seed_*.py scripts)
```

### Reading / Training

```bash
# Queue a book for reading (from Calibre)
python3 ~/TheIgors/claudecode/book_learner.py --calibre-id <id> --title "Book Title"

# Drain the reading queue (runs book_learner in sequence)
python3 ~/TheIgors/claudecode/drain_learn_queue.py

# Launch overnight reading session
python3 ~/TheIgors/claudecode/launch_overnight_reading.py
```

### Diagnostics

```bash
# General diagnostics
python3 ~/TheIgors/claudecode/diag.py

# Eval preparse (test thalamus parsing on an input)
python3 ~/TheIgors/claudecode/eval_preparse.py "your test input"

# CC deposit (deposit a memory directly)
python3 ~/TheIgors/claudecode/cc_deposit.py
```

---

## Habit Inspection

```bash
# Via psql — list RESPONSE habits (tier.1 no-inference serving)
psql -U igor -d Igor-wild-0001 -c \
  "SELECT id, metadata->>'trigger', metadata->>'response_template' \
   FROM memories WHERE metadata->>'habit_type' = 'response' LIMIT 20;"

# Via psql — list cognitive habits (scheduled)
psql -U igor -d Igor-wild-0001 -c \
  "SELECT id, metadata->>'code_ref', metadata->>'schedule_interval_sec' \
   FROM memories WHERE metadata->>'habit_type' = 'cognitive';"

# Via MCP (from Claude Code) — preferred for queries
# mcp__igor__habit_list, mcp__igor__memory_search, mcp__igor__memory_get
```

---

## Environment Flags (`.env`)

These can be toggled without a code change — just edit `.env` and `/restart`:

| Flag | Default | Effect |
|---|---|---|
| `IGOR_SELF_EDIT_ENABLED` | false | Allow Igor to edit source files |
| `IGOR_TIER5_ENABLED` | false | Allow Anthropic-direct spend |
| `IGOR_ARBITER_ENABLED` | false | Enable human-approval queue |
| `IGOR_RESEARCH_MODE` | false | Allow bulk external reads |
| `IGOR_LATENCY_ADAPTIVE` | false | Adaptive latency tuning |
| `IGOR_SKIP_PREPARSE_ON_CONFIDENT` | false | Skip preparse on high-confidence turns |
| `IGOR_DUAL_WORD_GRAPHS` | false | Enable dual word graph (G37) |
| `IGOR_CALL_COST_WARN_USD` | 2.00 | Per-call cost cap |
| `IGOR_MAX_TURNS` | 8 | Max agentic tool turns |
| `IGOR_WEB_PORT` | 8080 | Dashboard + API port |

---

## Troubleshooting

### Igor won't start
1. Check venv: `source ~/TheIgors/venv/bin/activate && python -c "import igor"`
2. Check `.env` exists: `ls ~/.TheIgors/Igor-wild-0001/.env`
3. Check Postgres: `psql -U igor -d Igor-wild-0001 -c "SELECT 1;"`
4. Check Ollama: `curl http://localhost:11434/api/tags`
5. Check errors log: `tail -30 ~/.TheIgors/logs/errors.log`

### Igor is stuck / not responding
```bash
# Pause and restart cleanly
touch ~/TheIgors/pause.wait
pgrep -f "igor\.main" | xargs kill 2>/dev/null
rm ~/TheIgors/pause.wait
igor
```

### Port 8080 already in use
```bash
fuser -k 8080/tcp
```

### High cloud cost
- Check `/cost` in-session
- Check `~/.TheIgors/logs/escalation.log` for why turns escalated
- Set `IGOR_CALL_COST_WARN_USD=0.50` in `.env` and `/restart` to cap earlier

### DB is locked / slow
```bash
# Check slow queries
tail -30 ~/.TheIgors/logs/db_queries.log

# Check Postgres connections
psql -U igor -d Igor-wild-0001 -c "SELECT count(*) FROM pg_stat_activity WHERE datname='Igor-wild-0001';"
```

---

## Known Inhibited Features

These are intentionally off — do not re-enable without discussion:

| Feature | Flag | Reason |
|---|---|---|
| Anthropic-direct inference (tier.5) | `IGOR_TIER5_ENABLED=false` | Runaway spend prevention |
| Human-approval queue | `IGOR_ARBITER_ENABLED=false` | UI not built yet |
| `seed_resource_gate_habits.py` | Do not re-run | Trigger contains "memory" → misfire on memory questions |
