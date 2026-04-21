# T-worker-dispatch-validation — outcome report (2026-04-21)

**Status:** BLOCKED on T-validation-adopt-goal-kwarg.
**Chain walked cleanly:** no.
**Closure posted:** no (chain never reached CLOSE_LOOP).
**Model observed doing the work:** n/a (dispatch crashed before any reasoning call).

## Seeded artifacts

- **Probe ticket:** `T-igor-validation-probe`
  - title: "Probe: create /tmp/igor_validation_probe.txt with 'hello' then remove it"
  - `worker=igor`, `priority=0.01`, `test_marker=true`
  - size=S, tags=[Validation, TestOnly]
  - Status after the run: gated (reason: "seed for T-worker-dispatch-validation rerun —
    wake after T-validation-adopt-goal-kwarg fix lands; test_marker=true so audit skips it")
  - Queue position at dispatch time: top (lowest score per weighted_ticket_score; only
    competing tickets at priority 0.4 and 0.6 were worker=claude).

## Dispatch invocation

```bash
IGOR_HOME_DB_URL=postgresql://igor:choose_a_password@127.0.0.1/Igor-wild-0001 \
  /home/akien/TheIgors/venv/bin/python -c "
from igor.tools.worker_foreman import adopt_next_ticket
print(adopt_next_ticket())
"
```

Output:

```
[ERROR] adopt_next_ticket: goal_adopt() got an unexpected keyword argument 'source_message'
```

## Failure site

`wild_igor/igor/tools/worker_foreman.py:293–296` calls:

```python
adopt_result = _goal_adopt(
    f"work ticket {ticket_id}: {pick.get('title','')}",
    source_message=f"[engram pickup] {ticket_id}",
)
```

`ops.goal_adopt()` (wild_igor/igor/tools/ops.py:174) signature:

```python
def goal_adopt(
    task_description: str,
    goal_id: str | None = None,
    origin_thread_id: str | None = None,
    origin_turn_id: str | None = None,
    origin_question: str | None = None,
    awaiting_reply: bool = False,
    pr_facia_id: str | None = None,
    parent_goal_facia_id: str | None = None,
) -> str:
```

No `source_message` parameter. (`source_message` IS a metadata key the function
sets internally from `task_description`: ops.py:217 stores
`"source_message": task_short` into the GOAL memory's metadata. That's
probably what the caller intended to piggy-back on, but the kwarg never
existed on the function signature.)

The bug raises TypeError before `adopt_next_ticket` even makes its first
DB mutation — the probe ticket was left untouched at status=pending, and no
reasoning call was logged.

## Child bug filed

**`T-validation-adopt-goal-kwarg`** — XS/Bug
- worker=claude, priority=0.02, decision_id=D-worker-mode-routing-2026-04-21
- Fix: drop the kwarg (simplest — `goal_adopt` already stores the task
  description as `source_message` in goal metadata automatically) OR route
  the provenance through `origin_question` if the engram-pickup breadcrumb
  is worth preserving.

T-worker-dispatch-validation was gated on this ticket and then blocked
with a detailed reason pointing to it.

## Baseline observations (infrastructure health, captured during setup)

Even though the dispatch crashed, the surrounding infrastructure is
verified alive and cost-auditable:

- **Ollama:** reachable at `http://localhost:11434` and `http://10.0.0.71:11434`
  (swarm host). `qwen2.5:7b` is loaded.
- **Igor running:** PID 1871694 (`python -m igor.main --id Igor-wild-0001`).
  Logs under `~/.TheIgors/local/logs/` are live as of today.
- **pe_chain → Qwen routing works end-to-end already:** the most recent
  `reasoning_calls.log` entry before this run was
  ```
  2026-04-21T11:07:16|reasoning|ollama|qwen2.5:7b|tier=tier.2|in=0|out=0
    |ctx=492|rsp=220|cost=$0.00000|elapsed=106664ms|turns=1
    |via=pe_chain/ollama@http://10.0.0.71:11434|resp=pe_chain step
  ```
  That row alone confirms three of the four prerequisites end-to-end:
    - `via=pe_chain/...` → T-engram-mcpcall-register-pe-steps is firing
    - `tier=tier.2` + `ollama|qwen2.5:7b` → T-verify-pe-chain-qwen-tier is correct
    - `cost=$0.00000` → cost-auditability story holds (local inference, no cloud spend)
  The fourth prerequisite (T-engram-trigger-cell-name-mismatch) is implicit
  in the chain running at all via cell-keyed triggers.
- **Cluster router intermittently logs `ROUTE_FAIL` for `10.0.0.1:11434`
  (unhealthy host), but calls successfully fall through to `10.0.0.71`.**
  Not a blocker, not related to this ticket.

## What the four prerequisites delivered

- c1409e0c T-engram-trigger-cell-name-mismatch — verified implicitly
  (chain starts under cell-keyed triggers).
- 5410ea6f T-engram-mcpcall-register-pe-steps — verified
  (`via=pe_chain/...` in reasoning_calls).
- fa8f6f95 T-verify-pe-chain-qwen-tier — verified
  (`tier=tier.2|ollama|qwen2.5:7b`).
- 11b1a586 T-worker-dispatch-routing — **not verified end-to-end.** Adding
  the worker field + routing switch works; the switch picks the `igor`
  branch correctly (the crash happens inside that branch, not in the
  decision to take it). But the `igor` branch's adopt_next_ticket has the
  kwarg bug — so the "cheap, in-process via Qwen" promise of the worker
  split cannot currently be demonstrated.

## What an operator should do next

1. Ship **T-validation-adopt-goal-kwarg** (one-line fix most likely).
2. Ungate **T-igor-validation-probe** and **T-worker-dispatch-validation**.
3. Re-run this validation against the unchanged probe — everything else
   is already primed.
