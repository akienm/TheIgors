---
name: debug
description: Autonomous mixed-mode debugger. Parses freeform input (ticket ID, timestamp, pasted error), calls Scraps for deterministic extraction, runs Haiku/Sonnet analysis, returns a structured report. Report is the deliverable — CC reads a conclusion, not a transcript.
model: sonnet
---

# /debug — Autonomous debugger

Returns a structured report so CC diagnoses without interactive investigation.
Report-first: CC reads a conclusion, not a transcript.

## Input forms

- `/debug T-xxx` — ticket ID; looks up error from queue + logs
- `/debug 160401` — timestamp shorthand (HHMMSS → today's date)
- `/debug "pasted error text"` — raw console output or stack trace
- `/debug T-xxx "pasted text"` — ticket context + pasted error

## Flow

```
Input → pointer resolution → Scraps extraction → Haiku analysis
     → (confidence < 0.5 → Sonnet escalation) → structured report
```

## Steps

### 1. Pointer resolution (light inference)

Parse the input into a structured query:
```python
query = {
    "component": str,    # pe_chain | ne | test | schema | general
    "timestamp": str,    # ISO 8601 if derivable
    "window_min": int,   # default 5
    "ticket_id": str,    # if provided
    "text": str,         # pasted raw text, if any
}
```

Inference rules (no model call needed for these):
- `T-xxx` input → look up ticket in queue; read description + recent `FAILED` lines from ticket body; set component from ticket tags (Database→schema, Cognition→ne, else pe_chain or general)
- `HHMMSS` input → expand to `YYYY-MM-DDTHH:MM:SS` using today's date; set component=general unless context clarifies
- Pasted text → set `query["text"]` directly; component from error keywords (AssertionError→test, psycopg2→schema, NE stuck→ne, Edit/old_string→pe_chain)
- Mixed (ticket + text) → merge: ticket sets component/ticket_id, pasted text overrides `query["text"]`

### 2. Scraps extraction

Call the debug extractor in `devices/scraps/debug_extractor.py`:

```python
import sys
sys.path.insert(0, str(Path.home() / "dev/src/UnseenUniversity"))
from devices.scraps.debug_extractor import extract

result = extract(query)
# result keys: log_window, state_snapshot, stack_trace, error_type, raw_error
```

If Scraps unavailable (ImportError), fall back to parsing `query["text"]` directly with the same regex logic.

### 3. Haiku analysis

Spawn a Haiku subagent with the extracted data. Prompt:

```
You are a debugger. Given this extraction, produce:
1. HYPOTHESIS: one-sentence diagnosis
2. CONFIDENCE: float 0.0-1.0 (how certain you are)
3. CHECK: exact command to verify hypothesis
4. NEXT: recommended action

Error type: {error_type}
Raw error: {raw_error}
Stack trace: {stack_trace}
State snapshot: {state_snapshot}
Log window (last 10 lines):
{log_window[-10:]}

Respond in this exact format:
HYPOTHESIS: <text>
CONFIDENCE: <float>
CHECK: <command>
NEXT: <action>
```

Parse the Haiku response to extract the four fields.

### 4. Escalate to Sonnet if confidence < 0.5

When Haiku confidence < 0.5: spawn a Sonnet subagent with the same prompt
plus Haiku's hypothesis as additional context:

```
Haiku hypothesis (low confidence {haiku_confidence:.2f}): {haiku_hypothesis}
Your task: improve on this or provide an alternative.
```

Use Sonnet's HYPOTHESIS, CONFIDENCE, CHECK, NEXT in the final report.

### 5. Format and return report

```
DEBUG REPORT — {timestamp}
Component: {component}  Ticket: {ticket_id or "—"}  Phase: {error_type}

SUMMARY: {hypothesis}

WHERE:    {stack_trace[-1]["file"]}:{stack_trace[-1]["line"]}  fn={stack_trace[-1]["function"]}
WHAT:     {raw_error}

STATE:
{state_snapshot formatted as key: value lines}

LOG WINDOW ({log_window[0][:19] if log_window else "—"} → {log_window[-1][:19] if log_window else "—"}):
{chr(10).join("  " + l for l in log_window[-10:])}

HYPOTHESIS ({confidence:.2f}): {hypothesis}
  check: {check}

NEXT: {next_action}
```

When `stack_trace` is empty, omit the WHERE line.
When `state_snapshot` is empty, omit the STATE block.
When `log_window` is empty, show `LOG WINDOW: (none found)`.

## Hard rules

- Pointer resolution never calls a model — it's pure string parsing.
- Scraps extraction is always deterministic — no inference inside it.
- Report is always produced even when extraction returns empty — the "no log found" case is itself diagnostic.
- Escalate to Sonnet only when Haiku confidence < 0.5 — don't default to Sonnet.
- Report is the final output — CC reads it and acts, no follow-up investigation needed.
