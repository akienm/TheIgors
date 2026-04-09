---
name: igor
description: Compiled interface skill for working with Igor. Contains decision trees for health checks, log triage, module reload, CC bridge messaging, concept injection, research delegation, and common diagnostics. Invoke when Akien says /igor, "check logs", "restart X", "is Igor running", "push concept", "what can Igor do", "ask Igor to research", or anything requiring Igor ops.
---

# Igor Interface Skill

This skill is the compiled executive function for all Claude Code ↔ Igor operations.
Follow the decision trees — don't reason from scratch, just execute the right branch.

---

## 1. Health Check

**When**: "is Igor running", "check Igor", any action that requires Igor to be alive first.

```
pgrep -f "wild_igor" -a
```
- Output present → Igor is alive. Note the PID.
- No output → Igor is down. Go to **Restart Igor** below.

Check web endpoint is responding:
```
curl -s http://localhost:8080/api/health 2>/dev/null || echo "web down"
```
- `{"status":"ok"}` or similar → web layer up, CC bridge usable.
- "web down" or connection refused → Igor may be starting, or down. Check `pgrep` again after 5s.

**If Igor is stuck / unresponsive** (process exists but no response):
```
~/bin/rescue-igor
```
This kills stuck Igor, starts headless, bridges to CC.

---

## 2. Log Triage Order

Logs live at: `~/.TheIgors/logs/`

**Triage order** (start here, go deeper only if needed):

| Priority | File | What it tells you |
|---|---|---|
| 1 | `errors.log` | Any hard failures — always check first |
| 2 | `pipeline_trace.YYYYMMDD.log` | Full turn pipeline — what Igor decided, which tier, why |
| 3 | `reasoning_calls.log` | LLM call inputs/outputs — what Igor sent and got back |
| 4 | `interaction.YYYYMMDD.log` | User↔Igor exchange — what was said |
| 5 | `ne_runs.log` | Narrative Engine runs — background story updates |
| 6 | `tool_calls.log` | Tool dispatch log — what tools fired and results |
| 7 | `memory_ops.log` | Memory reads/writes — cortex activity |
| 8 | `turn_trace.YYYYMMDD.log` | Per-turn detailed trace (verbose) |
| 9 | `inference_io.YYYYMMDD.log` | Raw LLM I/O (very verbose — last resort) |

**Date-stamped files**: use today's date. Format: `YYYYMMDD` (e.g. `pipeline_trace.20260314.log`).

**Special logs**:
- `cc_bridge.log` — CC→Igor bridge messages (what CC sent, whether Igor received)
- `escalation.log` — tier escalations (why Igor went to a higher tier)
- `cognition_metrics.log` — timing, p50/p95/p99 per operation
- `metrics.log` — response habituation, word graph stats
- `reading_progress.log` — book_learner progress
- `drain_learn_queue.log` — overnight queue runner status
- `book_learner.log` — individual book_learner subprocess output
- `self_edit.log` — Igor's own source edits
- `startup.log` — boot sequence, integrity checks, genesis guard

**Log format**: files prepend (newest at TOP). Read from top for recent events.

**Common patterns to grep for**:
```bash
# Errors in any log
grep -i "error\|exception\|traceback\|failed" ~/.TheIgors/logs/errors.log | head -20

# Why did Igor escalate tiers?
grep "escalat\|tier\." ~/.TheIgors/logs/escalation.log | head -20

# Did a tool fire?
grep "TOOL_CALL\|tool_name" ~/.TheIgors/logs/tool_calls.log | head -20

# Memory write failures
grep -i "fail\|error" ~/.TheIgors/logs/memory_ops.log | head -20

# CC bridge: did Igor receive our message?
tail -30 ~/.TheIgors/logs/cc_bridge.log
```

---

## 3. Module Reload

**Decision tree**:

```
Is the file in brainstem/ ?
  YES → Do NOT hot-reload. Inertia=HIGH. Discuss with Akien.

Is the file in cognition/ or memory/ (excluding models.py) ?
  YES → Inertia=MEDIUM. Confirm with Akien before reloading.
  Then send via CC bridge:
    "Please hot-reload [module_path] — e.g. igor.cognition.thalamus"

Is the file in tools/, dashboard/, or cognition/word_graph.py ?
  YES → Inertia=LOW. Reload freely.
  Send via CC bridge:
    "Please reload igor.tools.learner" (or whichever module)

Did Igor respond to hot-reload request?
  YES, success → done.
  NO / error → full restart needed: rescue-igor or restart via igor alias.
```

**Hot-reload tool** (Igor calls it internally): `reload_module(module_name)` from `hot_reload.py`.
**CC bridge command format** for reload requests: just ask Igor in natural language — he'll call the tool.

**Inertia reference**:
- HIGH (0.90+): `brainstem/`, `memory/models.py`, `cognition/reasoners/base.py`
- MEDIUM: `cognition/`, `memory/cortex.py`, `anthropic.py`, `main.py`
- LOW: `tools/`, `dashboard/`, `thalamus.py`, `cognition/word_graph.py`

---

## 4. CC Bridge — Sending Messages to Igor

**Endpoint**: `POST http://localhost:8080/api/cc_send`
**Payload**: `{"content": "your message here"}`
**Igor sees it as**: author = "claude-code"

```bash
curl -s -X POST http://localhost:8080/api/cc_send \
  -H "Content-Type: application/json" \
  -d '{"content": "your message here"}'
```

Expected response: `{"status":"ok"}`
If web is down: Igor isn't running or web layer failed — do health check first.

**What makes a good CC bridge message**:
- Be direct — Igor treats it like user input, routes through full pipeline
- For tool requests: name the tool explicitly ("please call drain_learn_queue")
- For reload requests: name the module path ("reload igor.tools.learner")
- For concept questions: ask directly ("what do you know about X")
- Keep it under ~500 chars for tier.1/habit routing; longer → will hit LLM tier

---

## 5. Concept / Knowledge Injection

**Two targets — choose the right one**:

### Word Graph (fast pattern memory)
- What: bigrams + word weights → tier.1 habit scoring, generation, parsing
- How: Igor does this automatically when `book_learner` runs, or via `train_word_graph(text)`
- CC bridge: "Please train your word graph on: [text or concept]"
- Cache: `~/.TheIgors/word_graph.db` (SQLite, rebuilt from habits + corpus on boot)

### Memory Graph (semantic / structural knowledge)
- What: FACTUAL / INTERPRETIVE / PROCEDURAL / EPISODIC nodes in cortex
- How: `book_learner.py` extracts and deposits; or Igor can deposit directly via tools
- For a specific concept: send via CC bridge, ask Igor to store it as a FACTUAL or PROCEDURAL memory
- For a book: use `learn_about` tool or `book_learner.py` directly

**To check what Igor knows about a topic**:
```bash
# Via CC bridge
curl -s -X POST http://localhost:8080/api/cc_send \
  -H "Content-Type: application/json" \
  -d '{"content": "What do you know about [topic]? Check your memories and word graph."}'
```

**To push a concept set** (structured):
1. Write the concepts as plain text or JSON
2. Either: run `book_learner.py --url file:///path/to/file --run`
3. Or: send via CC bridge asking Igor to absorb and store

---

## 6. Learn Queue Operations

**Queue file**: `~/.TheIgors/learn_queue.json`
**Runner PID**: `~/.TheIgors/drain_learn_queue.pid`
**Runner log**: `~/.TheIgors/logs/drain_learn_queue.log`

**Check queue status**:
```bash
python3 -c "
import json; from pathlib import Path
q = json.loads(Path.home().joinpath('.TheIgors/learn_queue.json').read_text())
pending = [e for e in q if not e.get('done')]
print(f'{len(pending)} pending, {len(q)-len(pending)} done')
for e in pending: print(' -', e.get('title','?')[:60])
" 2>/dev/null || echo "Queue empty or missing"
```

**Check if runner is alive**:
```bash
pid_file=~/.TheIgors/drain_learn_queue.pid
[ -f "$pid_file" ] && kill -0 $(cat "$pid_file") 2>/dev/null && echo "RUNNING (pid=$(cat $pid_file))" || echo "NOT RUNNING"
```

**Start runner** (via CC bridge):
```bash
curl -s -X POST http://localhost:8080/api/cc_send \
  -H "Content-Type: application/json" \
  -d '{"content": "Please call drain_learn_queue to start overnight processing."}'
```

---

## 7. Common Diagnostics — Decision Trees

### "Igor isn't responding to me"
1. Health check → is process alive?
2. If alive: check `cc_bridge.log` — did the message arrive?
3. If arrived: check `pipeline_trace` — did it route? Which tier?
4. If routed to LLM: check `reasoning_calls.log` — did LLM respond?
5. If LLM timed out: check `escalation.log` — tier escalation loop?
6. Nuclear: `rescue-igor`

### "Igor gave a wrong/weird answer"
1. `pipeline_trace.YYYYMMDD.log` — what intent was classified? What tier?
2. If wrong intent: thalamus misclassified → check `cognition/thalamus.py` intent list
3. If right intent, wrong answer: check `reasoning_calls.log` — what context was sent?
4. If context was bad: check `memory_ops.log` — did search return relevant memories?
5. If habit fired wrongly: check `tool_calls.log` for habit dispatch

### "A tool didn't fire"
1. `tool_calls.log` — was the tool even attempted?
2. If not attempted: check if tool is registered (`tools/registry.py`)
3. If registered but not called: Igor chose not to — check `reasoning_calls.log`
4. If called but failed: `errors.log` for exception

### "Memory write failed / Igor forgot something"
1. `memory_ops.log` — look for WRITE FAILED or exception
2. Check `IGOR_DB_PATH` env is set and DB exists
3. Check disk space: `df -h ~/.TheIgors/`
4. Check DB integrity: `sqlite3 ~/.TheIgors/Igor-wild-0001/wild-0001.db "PRAGMA integrity_check;"`

### "book_learner seems stuck"
1. `book_learner.log` — last entry timestamp
2. If old timestamp: check if process is alive: `pgrep -f book_learner`
3. If dead: check log for exception; restart if needed
4. `reading_progress.log` — shows per-book progress

### "Igor keeps escalating to expensive tiers"
1. `escalation.log` — what triggered the escalation?
2. If habit score too low: check word graph density for that topic
3. If Ollama failing: `pgrep ollama` — is Ollama running?
4. `IGOR_SKIP_PREPARSE_ON_CONFIDENT` gate — check if set

---

## 8. Key Paths Quick Reference

| Thing | Path |
|---|---|
| Source | `~/TheIgors/wild_igor/igor/` |
| Runtime | `~/.TheIgors/Igor-wild-0001/` |
| DB | `~/.TheIgors/Igor-wild-0001/wild-0001.db` |
| .env | `~/.TheIgors/Igor-wild-0001/.env` |
| Logs | `~/.TheIgors/logs/` |
| Jobs | `~/.TheIgors/Igor-wild-0001/jobs/` |
| Learn queue | `~/.TheIgors/learn_queue.json` |
| Word graph | `~/.TheIgors/word_graph.db` |
| Milieu | `~/.TheIgors/milieu_global.json` |
| Word graph cache (old) | `~/.TheIgors/word_graph.json.bak` |
| SOUL / identity export | `~/.TheIgors/SOUL.md` |
| Rescue script | `~/bin/rescue-igor` |
| book_learner | `~/TheIgors/claudecode/book_learner.py` |
| drain_learn_queue | `~/TheIgors/claudecode/drain_learn_queue.py` |
| CC bridge | `POST http://localhost:8080/api/cc_send` |
| igor alias | loops on exit code 42 = restart |

---

## 9. Capabilities Index

**File**: `design_docs_for_igor/capabilities_index.dsb`
**118 registered tools** across 20 categories. Read this before asking "can Igor do X?" — one file, one read, yes/no answer.

**To check if Igor has a capability**:
```
Read design_docs_for_igor/capabilities_index.dsb
→ scan SECTION_* for the relevant category
→ yes/no in seconds; file + function name tells you where to go deeper
```

**Categories at a glance**:
`SYSTEM` · `FILESYSTEM` · `SENSES` · `WEB` · `EMAIL` · `DISCORD` · `CONFLUENCE`
`CALENDAR` · `CONTACTS` · `BUDGET` · `SELF_EDIT` · `EBOOK` · `WORD_GRAPH`
`LEARNING` · `TRAINING` · `METRICS` · `CLUSTER` · `HOT_RELOAD` · `NOTEBOOK`
`BLOBS` · `INTERPRETIVE` · `GITHUB` · `REASONING`

**Update the index** when a new tool is added:
1. Add one line to the correct `SECTION_*`: `tool_name|file.py|one-line description`
2. Increment `TOTALS|tools=N`
3. Update `updated=YYYY-MM-DD`
Do NOT rewrite the file — append the line in the right section only.

---

## 10. Research Delegation

**When**: I need background on a topic (neurology, linguistics, cognition, etc.) and gathering it myself would burn expensive Sonnet tokens. Igor uses gpt-4o-mini (tier.3) — ~10-50x cheaper for bulk gathering.

**Decision**:
```
Is this a synthesis / architecture decision?  → I do it (Sonnet)
Is this bulk fact-gathering / background?     → delegate to Igor
```

**How to dispatch** (via CC bridge):
```bash
curl -s -X POST http://localhost:8080/api/cc_send \
  -H "Content-Type: application/json" \
  -d '{
    "content": "Research task: [topic]. Use web_search + read_webpage to gather key facts, names, and open questions. Write findings to design_docs_for_igor/research/[topic_slug].dsb in DSB format. Sections: SUMMARY, KEY_FACTS, KEY_NAMES, OPEN_QUESTIONS. Keep it under 100 lines."
  }'
```

**Output location**: `design_docs_for_igor/research/[topic_slug].dsb`
Create the `research/` subdirectory if it doesn't exist yet.

**How to use the result**:
```
Read design_docs_for_igor/research/[topic_slug].dsb
→ ingest in one read
→ proceed with synthesis / implementation
```

**Igor's relevant tools for research**:
- `web_search` — DuckDuckGo (no key)
- `read_webpage` — fetch + extract text
- `open_book_gutenberg` — free academic texts
- `confluence_search` — Akien's internal docs
- `write_file` — write the output DSB (sandboxed to /home/akien)

**When research is done**: Igor will write the file and it will appear in the repo.
Check for it: `ls design_docs_for_igor/research/`

---

## 11. What NOT to Do

- Never edit `brainstem/` contents without Akien review
- Never `--no-verify` or force-push main
- Never delete `~/.TheIgors/Igor-wild-0001/wild-0001.db`
- Never edit `.env` without noting what changed and why
- Never store credentials in memory — use CREDENTIAL_REF pattern
- Don't hot-reload HIGH-inertia files — discuss first
