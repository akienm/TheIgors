# The Lab Map — ~/.TheIgors/ Directory Reference

*Updated: 2026-03-26*

This is the runtime tree for Igor. Everything under `~/TheIgors/` is **source**;
everything under `~/.TheIgors/` is **runtime data** that never gets committed.

---

## Top-Level Layout

```
~/.TheIgors/
├── igor_wild_0001/         # Primary instance (akiendelllinux)
├── local/                  # Machine-local shared data (multi-box)
├── akien/                  # Akien's personal files synced to instances
├── cc_channel/             # Claude Code ↔ Igor coordination substrate
├── milieu_global.json      # Shared milieu state (cross-instance)
├── milieu_global.lock      # Lock file for milieu writes
├── sudo_relay/             # Sudo relay socket + state
└── SOUL.md                 # Igor's ethical framework copy (runtime read)
```

---

## Instance Directory: `igor_wild_0001/`

```
igor_wild_0001/
├── .env                    # ALL secrets + config (never committed)
├── wild-0001.db            # Live PostgreSQL-backed DB (DO NOT DELETE)
├── claude_budget.db        # Per-session CC cost tracking (SQLite)
└── inbox/                  # Instance inbox (files dropped here = processed)
```

### `.env` — Key Variables

| Variable | Purpose |
|---|---|
| `IGOR_DB_PATH` | Path to live DB |
| `OPENROUTER_API_KEY` | Primary cloud inference (OR) |
| `OLLAMA_HOST` / `OLLAMA_LOCAL_MODEL` | Local inference (default: localhost:11434, llama3.2:1b) |
| `IGOR_SELF_EDIT_ENABLED` | Gates source file writes |
| `IGOR_TIER5_ENABLED` | Gates Anthropic direct spend (default: false) |
| `IGOR_ARBITER_ENABLED` | Human-approval queue (default: false) |
| `IGOR_CALL_COST_WARN_USD` | Per-call cost cap (default: 2.00) |
| `IGOR_MAX_TURNS` | Max agentic tool turns per call (default: 8) |
| `IGOR_WEB_PORT` | Dashboard + API port (default: 8080) |
| `OPENROUTER_CHEAP_MODEL` | tier.3 model (gpt-4o-mini) |
| `OPENROUTER_DEFAULT_MODEL` | tier.3.5 model (haiku) |
| `OPENROUTER_INTERACTIVE_MODEL` | tier.4 model (sonnet) |

---

## Logs Directory: `~/.TheIgors/logs/`

All logs rotate daily where date-stamped; others grow continuously (small).

| Log File | What It Contains |
|---|---|
| `interaction.YYYYMMDD.log` | Every turn: ts, tier, cost, IN:, OUT: — primary audit trail |
| `turn_trace.YYYYMMDD.log` | Full BG scoring detail per turn — habit match scores, tier escalation |
| `pipeline_trace.YYYYMMDD.log` | Thalamus parse detail per turn — intent, keywords, tone, tags |
| `inference_io.YYYYMMDD.log` | Raw inference calls: model, query_chars, response_chars |
| `cognition_metrics.log` | Background cognition events: NE runs, self-training, gap deposits |
| `errors.log` | All exceptions + tracebacks |
| `escalation.log` | Tier escalation events (why a turn went to cloud) |
| `tool_calls.log` | Every tool call Igor made: name, args, result snippet |
| `reasoning_calls.log` | Reasoner-level calls: which reasoner, elapsed, cost |
| `ollama_calls.log` | Ollama-specific calls: model, elapsed, token counts |
| `ne_runs.log` | Narrative Engine run results |
| `db_queries.log` | Slow DB queries (> threshold) |
| `metrics.log` | General metrics snapshots |
| `graph_cache_refresh.log` | Word graph cache refresh events |
| `review_audit.log` | Self-edit review audit trail |
| `cc_alerts.log` | Budget alerts + crash notices |
| `nudge_cron.log` | Cron nudge results |

### Quick Log Commands

```bash
# Last 50 interactions (most useful daily log)
tail -50 ~/.TheIgors/logs/interaction.$(date +%Y%m%d).log

# Recent errors
tail -30 ~/.TheIgors/logs/errors.log

# What tier did Igor use? (escalation story)
tail -30 ~/.TheIgors/logs/escalation.log

# Self-training activity
grep "output_training\|self_training" ~/.TheIgors/logs/cognition_metrics.log | tail -20

# Tool calls Igor made today
tail -30 ~/.TheIgors/logs/tool_calls.log

# Cost per turn today
grep "^\$(date +%Y-%m-%d)" ~/.TheIgors/logs/interaction.$(date +%Y%m%d).log | cut -d'|' -f6 | sort -n
```

---

## CC Channel: `~/.TheIgors/cc_channel/`

The coordination substrate between Claude Code sessions and Igor.

```
cc_channel/
├── messages.jsonl          # All channel messages (append-only)
├── slate.md                # Current active context / work slate
├── queue.json              # CC task queue (tickets)
├── queue.json.bak          # Queue backup (auto-generated)
├── current_session.txt     # Current Claude Code session ID
├── log.jsonl               # Session manager event log
└── slate_archive_*.md      # Archived slates
```

---

## Local Shared: `~/.TheIgors/local/`

Machine-local data not tied to a specific instance, shared across instances on this machine.

```
local/
├── ebooks/                 # Local ebook library
├── calibre_catalog.csv     # Calibre catalog export
├── cc_channel/             # Local CC channel (if separate from main)
├── claudecode/             # Local CC helper scripts
├── machines.json           # Multi-box machine registry
├── benchmarks/             # Performance benchmarks
├── cache/                  # General cache
├── sudo_relay/             # Sudo relay local socket
├── training_corpus/        # Reading/training text corpus
├── igor_id_rsa[.pub]       # Igor's SSH key (for cluster access)
├── tailscale.crt/.key      # Tailscale certificates
└── claude_bridge_history.json  # CC bridge conversation history
```

---

## Akien Personal: `~/.TheIgors/akien/`

Files Akien puts here get synced to Igor instances.

```
akien/
├── AkiensWorld/            # Personal writings, notes
├── onedrive/               # OneDrive mirror
├── inbox/                  # Drop files here for Igor to process
└── outbox/                 # Igor's output files for Akien
```

---

## Source Tree Cross-Reference

```
~/TheIgors/                 # Source root (committed to git)
├── wild_igor/igor/         # Agent source code
│   ├── brainstem/          # HIGH inertia: boot, supervisor, scheduler
│   ├── cognition/          # MEDIUM inertia: thalamus, NE, milieu, BG
│   ├── memory/             # HIGH inertia: models.py, cortex.py
│   ├── tools/              # LOW inertia: all registered tools
│   └── main.py             # MEDIUM inertia: main loop + commands
├── claudecode/             # CC scripts: seed_*.py, session_manager.py, etc.
├── design_docs/            # Human-readable architecture docs
├── design_docs_for_igor/   # Igor-readable DSB docs
├── tests/                  # Test suite (pytest)
└── venv/                   # Python 3.12 virtual environment
```
