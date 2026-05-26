---
name: cognition-debug
description: "DEPRECATED — use /diagnose igor instead. Realtime cognition cycle stepping."
model: sonnet
---

> **DEPRECATED 2026-05-25** — use `/diagnose igor` instead.
> `/diagnose` is the unified diagnostic entry point for any rack device.
> For cognition-specific stepping, see `/diagnose igor` Step 2.

---

# /cognition-debug — DEPRECATED: use /diagnose igor

DESIGNED:T-cognition-debug-skill. Motivation: post-analysis of cognition issues
requires assumptions about what happened between phases; stepping exposes actual
state at each boundary.

## Phases of Igor's cognition cycle

```
Input → Thalamus (parse + intent) → TWM (context retrieval) →
Action selection (basal_ganglia) → NE cycle → Gateway (inference) →
Response → Memory deposit → Habit fire → TWM push
```

## Mode A — Replay (step through a recorded turn)

Use when diagnosing a past turn (routing incident, bad response, missing habit).

### 1. Find the turn

```bash
# List recent turns (shows turn_id, timestamp, input snippet)
python3 -c "
import os; os.environ['IGOR_HOME_DB_URL'] = 'postgresql://igor:choose_a_password@127.0.0.1/Igor-wild-0001'
from wild_igor.igor.cognition.forensic_logger import get_recent_turn_ids
for t in get_recent_turn_ids(limit=10): print(t)
"
```

Or via MCP (when transport is available):
```
mcp__igor__turn_trace_recent(limit=10)
```

### 2. Step through the turn trace

```bash
# Get the full trace for a specific turn_id
python3 -c "
import os; os.environ['IGOR_HOME_DB_URL'] = 'postgresql://igor:choose_a_password@127.0.0.1/Igor-wild-0001'
from wild_igor.igor.cognition.forensic_logger import get_turn_trace
trace = get_turn_trace('<turn_id>')
for step in trace:
    print(f'[{step[\"step\"]}] {step[\"elapsed_ms\"]}ms tier={step.get(\"tier\",\"-\")}')
    if step.get('detail'): print(f'  {step[\"detail\"][:200]}')
"
```

Or via MCP:
```
mcp__igor__traces_get(turn_id="<turn_id>")
```

**Pause after each phase.** Key questions:
- Thalamus: what intent was parsed? What complexity score?
- Gateway: was `is_user_turn=True`? Which tier was selected?
- Memory: which memories were retrieved? Were relevant ones missing?
- Habit fire: which habits matched? Which ones ran?

### 3. Check TWM state at time of turn

```bash
# What was in TWM when this turn fired?
python3 -c "
import os; os.environ['IGOR_HOME_DB_URL'] = 'postgresql://igor:choose_a_password@127.0.0.1/Igor-wild-0001'
from wild_igor.igor.cognition.inference_gateway import get_gateway
gw = get_gateway()
# hot_nodes shows current top salience — use traces_get for historical
"
```

Or via MCP:
```
mcp__igor__hot_nodes(limit=20)
mcp__igor__hot_attractors(limit=10)
mcp__igor__tail_heat(limit=20)
```

### 4. Check what the NE cycle did

```
mcp__igor__traces_recent(limit=5)    # recent NE traces
mcp__igor__wg_neighbors(node="<key concept>")  # word graph context
```

## Mode B — Realtime inspection (between live turns)

Use when Igor is running and you want to inspect state mid-session without
stopping him.

### Live TWM state

```
mcp__igor__twm_read(limit=30)
mcp__igor__hot_nodes(limit=20)
mcp__igor__hot_attractors(limit=10)
```

### Recent channel / what Igor's seeing

```
mcp__igor__channel_read(limit=10)
```

### Active habits

```
mcp__igor__habit_list()
```

### Tail heat (what's been firing)

```
mcp__igor__tail_heat(limit=30)
```

### Debug session flag (forces verbose mode in Igor)

When MCP transport is available:
```
mcp__igor__cognition_debug_claim(scope="session")   # DESIGNED:T-mcp-igor-cognition-debug-capability
```

Fallback (direct flag):
```bash
touch ~/.TheIgors/Igor-wild-0001/debug_session.flag
# ... inspect ...
rm ~/.TheIgors/Igor-wild-0001/debug_session.flag
```

## Common diagnoses

| Symptom | Where to look |
|---|---|
| Human turn went to local instead of cloud | `traces_get` → check `is_user_turn` in gateway entry log |
| Habit fired when it shouldn't | `habit_list` → check trigger condition + refractory state |
| Memory not retrieved | `hot_nodes` → check salience; cortex search with `twm_read` |
| Igor gave canned response instead of reasoning | `turn_trace_recent` → look for habit_fire before gateway call |
| TWM flooded with noise | `tail_heat` → identify high-volume push source |
| NE arc didn't complete | `traces_recent` → look for arc expiry or stuck state |

## Engram execution (requires DESIGNED:T-engram-logging-primitive)

When `T-engram-logging-primitive` is shipped, engram log lines will appear in
the turn trace alongside phase outputs. Until then, engram execution is a black
box — use `habit_list` to see which code_ref fired, then read the source.

## Hard rules

- Always start with `turn_trace_recent` to orient — don't probe blind.
- Realtime inspection is read-only — never modify TWM or channel state during inspection.
- Release the debug_session flag (or MCP release) when done — leaving it set suppresses Igor's crash-recovery CC spawning.
- Log any phase boundary that had no instrumentation → feedback to T-engram-logging-primitive.
