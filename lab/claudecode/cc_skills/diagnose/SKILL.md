---
name: diagnose
description: Unified device diagnostics — surfaces recent trace, categorizes issue (code bug/state corruption/external noise), suggests one fix. Works for any rack device.
model: sonnet
---

# /diagnose — Rack device diagnostics

Single entry point for diagnosing any rack device. Usage:
```
/diagnose igor          # diagnose Igor device (default)
/diagnose queue         # diagnose the queue rack device
/diagnose librarian     # diagnose Librarian
/diagnose <device_id>   # any device that inherits DiagnosticBase
```

Replaces /debug-pe-chain, /igor-diagnose, and /cognition-debug — those skills
are deprecated and redirect here.

---

## Step 1 — Collect device traces

```python
# Preferred: query DiagnosticBase.last_traces() via MCP if device is running
# mcp__datacenter__<device>_traces(n=20)   # when the tool exists

# Fallback: read trace files directly
import json, pathlib, os
device = "<device_id>"
log_root = pathlib.Path(os.environ.get("DATACENTER_LOGS", "datacenter_logs"))
trace_dir = log_root / device / "trace"
records = []
for f in sorted(trace_dir.glob("*.jsonl"), reverse=True)[:3]:
    for line in f.read_text().splitlines():
        try:
            records.append(json.loads(line))
        except Exception:
            pass
records.sort(key=lambda r: r.get("ts",""), reverse=True)
for r in records[:20]:
    print(r.get("ts","")[:19], r.get("event",""), r.get("data",""))
```

Also pull recent JSON logs if traces are sparse:
```bash
ls -lt datacenter_logs/<device>/log/json/ | head -20
# Read the 3 most recent files for context
```

**If debug_mode is not enabled, suggest enabling it:**
```python
# In a Python shell or via MCP tool:
device_instance.debug_mode = True   # traces will also appear in live loguru output
```

---

## Step 2 — Igor-specific: pe_chain basket state

When `device == "igor"`, also inspect pe_chain basket state. Reuse the
stepping logic from the former /debug-pe-chain skill:

```python
from devices.igor.tools.pe_chain import pe_entry_init
basket = pe_entry_init()
print("Active ticket:", basket.get("ticket_id"))
print("Last phase:", basket.get("last_phase"))
print("Error:", basket.get("error"))
```

Check channel for stuck patterns:
```bash
python3 ${CC_WORKFLOW_TOOLS}/channel.py read 20
```

Look for:
- Same NE arc repeating → stuck state (Step 3 category B)
- HYPOTHESIZE old_string not found → Step 3 category A (code bug)
- DB/network errors → Step 3 category C (external noise)

---

## Step 3 — Categorize + suggest one fix

Classify the issue into one of four categories and suggest the most targeted fix:

| Category | Signal | Typical fix |
|---|---|---|
| **A — Code bug** | Exception/assertion in trace, old_string mismatch, import error | Read the file at the failing line; fix the bug; re-run |
| **B — State corruption** | Unexpected values in basket/TWM/NE, ticket stuck in_progress | `cc_queue.py reset --timeout <id>`; restart Igor if TWM is corrupt |
| **C — External noise** | DB connection error, network timeout, missing env var | Check Postgres is up; check `.env`; check network |
| **D — Unknown** | No clear signal in traces | Enable debug_mode; re-run the failing operation; re-diagnose with more trace data |

Always end with one concrete action:
```
CATEGORY: <A/B/C/D>
DIAGNOSIS: <one sentence>
NEXT ACTION: <specific command or step>
```

---

## Hard rules

- Never hypothesize before Step 1 (traces in hand). Channel messages alone are not enough.
- When traces are empty: enable debug_mode, reproduce the failure, then re-diagnose.
- The fix is always singular — if you see multiple issues, pick the one blocking progress first.
