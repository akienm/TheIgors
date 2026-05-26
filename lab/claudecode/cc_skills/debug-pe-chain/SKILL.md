---
name: debug-pe-chain
description: "DEPRECATED — use /diagnose igor instead. Realtime single-step of Igor's pe_chain pipeline."
model: sonnet
---

> **DEPRECATED 2026-05-25** — use `/diagnose igor` instead.
> `/diagnose` is the unified diagnostic entry point for any rack device.
> The pe_chain stepping logic is preserved in `/diagnose` Step 2 (igor-specific).

---

# /debug-pe-chain — Step Igor's pe_chain pipeline

DESIGNED:T-debug-pe-chain-skill. Motivation: post-analysis of pe_chain failures
requires assumptions about what happened between phases. Stepping exposes actual
HYPOTHESIZE output before IMPLEMENT runs, so bad proposals are caught before they
block the ticket.

## When to use

- BLOCKED(Igor):T-xxx with "HYPOTHESIZE produced an invalid old_string"
- BLOCKED(Igor):T-xxx with "hallucinated HIGH-inertia target"
- Any Igor ticket that exhausted retries — read the basket state at each phase

## Setup

```bash
cd ~/TheIgors && source venv/bin/activate
export IGOR_HOME_DB_URL=postgresql://igor:choose_a_password@127.0.0.1/Igor-wild-0001
```

## Phase sequence

pe_chain phases in order:
```
pe_entry_init → pe_claim → pe_read_ticket → pe_plan → pe_filter →
pe_situate → pe_observe → pe_hypothesize → pe_implement → pe_test →
pe_close_loop → _pe_commit → _pe_close
```

Each step takes a `basket` dict and returns it mutated. Run steps in Python,
inspect between each one.

## Stepping procedure

### 1. Initialize the basket

```python
from wild_igor.igor.tools.pe_chain import (
    pe_entry_init, pe_claim, pe_read_ticket, pe_plan, pe_filter,
    pe_situate, pe_observe, pe_hypothesize, pe_implement, pe_test,
    pe_close_loop, _pe_commit, _pe_close,
)

basket = pe_entry_init()
# basket["ticket_id"] is set from active GOAL; override if needed:
basket["ticket_id"] = "T-target-ticket"
print("ENTRY basket:", {k: v for k, v in basket.items() if k != "observe_results"})
```

**Pause.** Review `ticket_id`, `description`, `size`. Proceed?

### 2. Read ticket + plan

```python
basket = pe_read_ticket(basket)
print("TICKET:", basket.get("title"), "\nDESCRIPTION:", basket.get("description", "")[:500])
print("AFFECTED FILES declared:", basket.get("required_files", []))

basket = pe_plan(basket)
print("PLAN:\n", basket.get("plan_summary", "(none)"))
```

**Pause.** Does the plan look correct? Are the affected files right? If not, edit
`basket["plan_summary"]` or `basket["required_files"]` before continuing.

### 3. Filter + situate

```python
basket = pe_filter(basket)
print("FILTER result:", basket.get("filter_result", "ok"))

basket = pe_situate(basket)
print("FILES TO CHANGE:", basket.get("plan_files", []))
```

**Pause.** Verify `plan_files` — are these the right files? HIGH-inertia files
should only appear if the ticket explicitly names them.

### 4. Observe

```python
basket = pe_observe(basket)
# Don't print full observe_results (huge); print file list and line counts:
for fname, content in (basket.get("observe_results") or {}).items():
    print(f"  {fname}: {len(content.splitlines())} lines read")
```

**Pause.** Did it read the right files? Is the content current (not stale)?

### 5. HYPOTHESIZE — the critical step

```python
basket = pe_hypothesize(basket)
hypotheses = basket.get("hypotheses", [])
print(f"HYPOTHESIZE produced {len(hypotheses)} edit(s):")
for i, h in enumerate(hypotheses):
    print(f"\n[{i}] file: {h.get('file')}")
    print(f"  old_string ({len(h.get('old_string',''))} chars):\n{h.get('old_string','')[:300]}")
    print(f"  new_string ({len(h.get('new_string',''))} chars):\n{h.get('new_string','')[:300]}")
```

**PAUSE — this is the gate.** Review each hypothesis:
- Does `old_string` actually exist verbatim in the file? (`grep -c "exact string" file`)
- Is `file` actually in scope (listed in ticket's Affected files)?
- Is any HIGH-inertia file targeted that shouldn't be?

If a hypothesis is bad: fix `basket["hypotheses"][i]["old_string"]` / `["file"]`
directly, or discard (`basket["hypotheses"] = []`) and re-run `pe_hypothesize`.

### 6. Implement

```python
basket = pe_implement(basket)
print("IMPLEMENT result:", basket.get("implement_result"))
# Review the actual diff:
import subprocess
result = subprocess.run(["git", "diff"], capture_output=True, text=True)
print(result.stdout[:3000])
```

**Pause.** Does the diff look right? If not: `git checkout -- .` to rollback.

### 7. Test

```python
basket = pe_test(basket)
print("TEST result:", basket.get("test_result"), "exit:", basket.get("test_exit"))
```

If tests fail: fix the issue, then re-run `pe_test`. Don't proceed to close with
failing tests.

### 8. Close

```python
basket = _pe_commit(basket)
basket = _pe_close(basket)
print("DONE. Commit:", basket.get("commit_hash"))
```

## Escalation paths

| What you see | What to do |
|---|---|
| old_string not found in file | Fix basket["hypotheses"][i]["old_string"] → re-implement |
| HIGH-inertia file not in ticket | Delete from basket["hypotheses"] → re-implement |
| Tests fail | Fix code → re-test |
| Plan wrong | Edit basket["plan_summary"] → re-situate → re-observe |

## Hard rules

- Always pause after HYPOTHESIZE before calling pe_implement — that's the point.
- Never skip pe_test after pe_implement — a passing test is required to close.
- Log any missing log sites discovered during stepping (feedback to T-engram-logging-primitive).
- If the basket goes into an unknown state, run `_pe_escalate(basket, "debug-pe-chain: manual abort")` to block cleanly.
