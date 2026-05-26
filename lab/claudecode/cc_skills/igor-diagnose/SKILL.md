> **DEPRECATED 2026-05-25** — use `/diagnose igor` instead.
> `/diagnose` is the unified diagnostic entry point for any rack device.
> The stuck-state diagnosis logic and the "no hypothesis before traces" invariant
> are preserved in `/diagnose` Steps 1-3.

---

# /igor-diagnose — DEPRECATED: use /diagnose igor

**Core invariant: No hypothesis before Step 3 (verbatim anomaly in hand).
Do not theorize from channel messages or TWM alone. Leaf logs are the truth.**

## When to use

- Igor is stuck (same NE arc repeating, NARRATIVE_GAP loop, ACTION_IMPULSE with no action)
- Igor produced output that seems incoherent or unrelated to the active goal
- pe_chain failed or is retrying without progress
- Something in the channel looks wrong and you want to understand the root cause

## Setup

```bash
export IGOR_HOME_DB_URL=postgresql://igor:choose_a_password@127.0.0.1/Igor-wild-0001
REPORT=~/.TheIgors/claudecode/igor_diagnose_report.md
```

---

## Step 1 — Anchor: find timestamp of last healthy action

Read the channel (last 20 messages) to find when Igor last produced a
substantive, non-stuck message. This is your anchor — everything from
here forward is the window to investigate.

```bash
python3 ${CC_WORKFLOW_TOOLS}/channel.py read 20
```

Record the anchor timestamp (the last healthy message before things diverged).
If the channel is clean, the incident may have been in a prior session —
check today's slate for the approximate time.

**Do NOT form a hypothesis yet.** You don't know the cause.

---

## Step 2 — Leaf log sweep: read the authoritative record

Read the specific subsystem logs FROM the anchor timestamp forward.
These are the leaf logs — they record what actually happened, not
what NE interpreted.

**Always-read list (start here):**
```bash
# Recent errors
tail -100 ~/.TheIgors/local/logs/errors.log 2>/dev/null | grep -A3 "ERROR\|CRITICAL" | head -60

# pe_chain activity
tail -100 ~/.TheIgors/local/logs/pe_chain.log 2>/dev/null | tail -60

# Goal / coding sprint ops
tail -50 ~/.TheIgors/local/logs/ops.log 2>/dev/null | tail -40

# Scope guard decisions
tail -30 ~/.TheIgors/local/logs/scope_guard.log 2>/dev/null | tail -20
```

**Read if pe_chain or goal-related:**
```bash
# Goal continuation
tail -50 ~/.TheIgors/logs/goal_continuation.log 2>/dev/null | tail -30

# NE run summary (only if stuck NE is the symptom — not the cause)
# This is an effects log, not a cause log — read last, not first
tail -20 ~/.TheIgors/local/logs/cognition.log 2>/dev/null | tail -20
```

**Read if memory or retrieval related:**
```bash
tail -30 ~/.TheIgors/local/logs/memory.log 2>/dev/null | tail -20
tail -30 ~/.TheIgors/local/logs/memory_ops.log 2>/dev/null | tail -20
```

**Read if inference / LLM call related:**
```bash
tail -30 ~/.TheIgors/local/logs/reasoning_calls.log 2>/dev/null | tail -20
```

---

## Step 3 — First anomaly: find the exact divergence point

**This step is mandatory. Do not proceed to Step 4 until you have the
verbatim log line where behavior diverged.**

The anomaly is the EARLIEST log line that shows something unexpected:
- An exception with traceback
- A SKIP/ABORT decision that shouldn't have happened
- A timeout or retry-exhaust
- A missing resource (key, file, DB row)
- An unexpected empty result

State it verbatim:
```
ANOMALY: [timestamp] [log file] [exact line]
```

If logs are ambiguous (not enough to identify the anomaly), **add logging
before guessing** — per standing instruction. Identify the function that
should have logged and add a self.log.info() or log.info() call at the
right point, then ask Igor to restart and reproduce.

---

## Step 4 — Categorize: which of the three failure modes is this?

### Case A: Code/logic bug
**Signs:** exception, wrong branch, incorrect condition, AttributeError,
KeyError, unexpected None
**Fix:** code change — identify the file:line and fix it (use /sprint if a
ticket warrants it, or fix inline for 1-3 line fixes)

### Case B: TWM/memory state corruption
**Signs:** GOAL_READY stuck in TWM without active goal, duplicate goals,
contradictory memories causing confused NE arc
**Diagnosis queries:**
```bash
IGOR_HOME_DB_URL=postgresql://igor:choose_a_password@127.0.0.1/Igor-wild-0001
# Check TWM observations
psql "$IGOR_HOME_DB_URL" -c \
  "SELECT id, content, expires_at FROM instance.twm_observations
   WHERE expires_at > NOW() OR expires_at IS NULL
   ORDER BY id DESC LIMIT 20"

# Check active goals
psql "$IGOR_HOME_DB_URL" -c \
  "SELECT id, narrative, metadata->>'status' FROM clan.memories
   WHERE memory_type='GOAL' AND metadata->>'status' NOT IN ('closed','completed')
   ORDER BY timestamp DESC LIMIT 10"
```
**Fix:** DB cleanup — expire the stuck TWM entries, close orphan goals,
or send a clarifying direction via channel

### Case C: External noise / false narrative loop
**Signs:** Igor responding to channel messages that aren't from Akien,
high-salience ACTION_IMPULSE based on test output or automated messages,
failover_tool or other infra noise triggering NE activity
**Fix:** clarifying direction (channel send) + optionally filter the source;
if the noise is from test pollution, file a bug ticket

---

## Step 5 — One targeted fix

Apply exactly what the logs point to. Nothing more.

| Case | Fix |
|------|-----|
| A — code bug | Edit the file, fix the line; /sprint if non-trivial |
| B — state corruption | psql cleanup or `cc_queue.py reset <ticket>` |
| C — external noise | Channel direction; optionally silence the source |

If pe_chain HYPOTHESIZE is the anomaly, escalate to **/debug-pe-chain**:
that skill steps phases manually and lets you inspect the basket at each
phase before committing to IMPLEMENT.

---

## Step 6 — Verify: watch for a successful action

**Silence is not verification.** Wait until Igor produces a substantive
output — a channel message, a pe_chain commit, a goal completion — that
matches what the active ticket or goal requires.

```bash
python3 ${CC_WORKFLOW_TOOLS}/channel.py read 5
```

If Igor goes quiet (no output in 5+ min with an active goal), re-read
the leaf logs — silence is another symptom, not a cure signal.

---

## Step 7 — Write diagnostic report entry

Always append to the persistent report so the incident is traceable:

```bash
REPORT=~/.TheIgors/claudecode/igor_diagnose_report.md
TS=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
TRIGGER="<what triggered the diagnosis>"
LEAF_CITATION="<file:line — the verbatim anomaly from Step 3>"
CATEGORY="A|B|C"
FIX_APPLIED="<one sentence>"
OUTCOME="<resolved|ongoing|escalated>"

cat >> "$REPORT" <<EOF

## $TS
- **Trigger:** $TRIGGER
- **Leaf log citation:** $LEAF_CITATION
- **Root cause category:** $CATEGORY
- **Fix applied:** $FIX_APPLIED
- **Outcome:** $OUTCOME
EOF
```

Over time this report becomes a pattern library. Frequency distribution
of A/B/C guides what to fix in the system.

---

## Hard rules

- Leaf logs FIRST, always — no diagnosis from channel or TWM alone.
- **No hypothesis before the verbatim anomaly is in hand (Step 3).**
- If logs are ambiguous → add logging, don't guess.
- Verify by watching Igor produce a successful action, not just silence.
- One fix at a time — the goal is root cause, not symptom suppression.

## Escalation

| Symptom | Escalate to |
|---------|-------------|
| pe_chain HYPOTHESIZE failure | /debug-pe-chain |
| Code change needed (non-trivial) | /sprint T-xxx |
| Persistent loop despite fix | Akien — the loop may be a design issue |

## Related

- **/debug-pe-chain** — step pe_chain phases manually; use when Step 3 points to HYPOTHESIZE
- **/readigor** — read recent Igor channel output (effects, not causes)
- **/context-load** — session startup; surfaces inbox notifications from Igor subsystems
