# TheIgors — Developer Standards

*The authoritative reference for code written in this codebase. Both Claude and Igor should
read this before writing a new module or modifying an existing one. When in doubt, this
document wins over personal preference.*

*Future state: this document will be loaded as a DSB memory node so Igor can traverse it
directly rather than Claude reading it at session start.*

---

## 1. Forensic Logging

### Philosophy

Logging in TheIgors is built for fastest human digestion, not just capture. Every log entry
should answer: *what happened, when, and why does it matter?* If you're writing a log line
that you wouldn't want to read at 2am during an incident, write it differently.

### The forensic_logger API

All logging goes through `wild_igor.igor.cognition.forensic_logger`. Never use `print()` for
observable output in production paths. Use `logging.getLogger(__name__)` for module-level
debug noise; use `forensic_logger` for anything that crosses a boundary or changes state.

```python
from ..cognition.forensic_logger import log_error, log_tool_call, log_memory_op

# Tool call — log at both entry and exit for elapsed time
import time
t0 = time.monotonic()
result = do_the_thing()
log_tool_call(
    tool_name="my_tool",
    args_summary=f"param={param[:60]}",
    result_summary=str(result)[:80],
    success=True,
    elapsed_ms=int((time.monotonic() - t0) * 1000),
)

# Error — always log before returning/raising
log_error(
    kind="MY_TOOL_FAIL",       # SCREAMING_SNAKE, descriptive category
    detail=f"step failed: {e}",
    source="tools/my_tool",    # file:function or subsystem name
)

# Memory operation — when storing or retrieving
log_memory_op(
    operation="store",         # store | search | retrieve | update
    memory_type="INTERPRETIVE",
    narrative_snippet=narrative[:80],
    inertia=0.75,
    why="training pass deposit",
)
```

### What MUST be logged

| Event | Logger call | Log file |
|---|---|---|
| Tool called (entry + exit) | `log_tool_call()` | `tool_calls.log` |
| Tool failure | `log_error(kind="TOOL_FAIL")` | `errors.log` |
| Tier selection | `log_tier_selection()` | `reasoning_calls.log` |
| Cloud inference (each call) | `log_reasoning_call()` | `reasoning_calls.log` |
| Memory store/search | `log_memory_op()` | (internal) |
| Any escalation or fallback | `log_error(kind="TIER_FAIL"\|"IMPULSE_SKIP")` | `errors.log` |
| Interface crossing | `log_error` or `log_tool_call` as appropriate | varies |
| State change (milieu, TWM, habit fire) | `log_tool_call` or forensic inline | `tool_calls.log` |

### Log file conventions

- All logs live in `~/.TheIgors/logs/` — never write logs into `~/TheIgors/` (source tree)
- Newest-first prepend via `_prepend()` — do not append; prepend means the top is always current
- Rotate when file exceeds 10MB (flag for `/audit` to catch)
- Dated logs (turn_trace, pipeline_trace, inference_io) rotate daily: `name.YYYYMMDD.log`
- One log file per concern — do not multiplex unrelated events into the same file

### Timing instrumentation

Use `get_timer` from `logging_setup.py` (or `self.log.get_timer()` from any IgorBase subclass)
to emit structured elapsed-time log lines without building your own t0/elapsed boilerplate:

```python
# Module-level tool (not a class)
from ..logging_setup import get_timer
timer = get_timer(log, "pe_chain.hypothesize", ticket=ticket_id)
result = call_llm(prompt)
timer.stop(tokens=len(result), model=model_id)
# → logs: name=pe_chain.hypothesize started=20260406... elapsed=3.142 ticket=T-foo tokens=412 model=...

# IgorBase subclass
timer = self.log.get_timer("read_ticket", ticket=ticket_id)
desc = read_ticket(ticket_id)
timer.stop(desc_len=len(desc))
```

`timer.stop()` returns elapsed seconds if you need it for further logic. The structured format
(space-separated `key=value` pairs) is machine-parseable and grep-friendly.

### bash scripts

Bash scripts use `logcmd`/`logecho`/`timestamp()` from akientools `logger_for_bash`:

```bash
# Self-contained scripts — inline the logger
logecho() { echo "[$(date '+%Y-%m-%dT%H:%M:%S')] $*" | tee -a "$LOG_FILE"; }
logcmd()  { logecho "RUN: $*"; "$@" 2>&1 | tee -a "$LOG_FILE"; }

# Scripts that can assume akientools on PATH
source logger_for_bash.sh
```

---

## 2. Module Structure

### New tool file template

Every file in `tools/` follows this shape:

```python
"""
module_name.py — One-line purpose (D-number if applicable).

Longer description of what this module does and why it exists.
Key design decisions or constraints go here.
"""

import logging
import os
# stdlib imports first, alphabetical

from .registry import Tool, registry
# local imports second

_LOG = logging.getLogger(__name__)

# ── Module-level constants ─────────────────────────────────────────────────────
# Document what each constant does and why its default is what it is


# ── Implementation functions ──────────────────────────────────────────────────

def _private_helper() -> str:
    """Private helpers prefixed with _."""
    ...


def public_tool_function(param: str = "", **_) -> str:
    """
    One-line summary.

    Longer description if needed.
    The **_ catch-all is mandatory — habit dispatch passes extra keys.

    param: what it means
    Returns: what the string contains
    """
    try:
        result = _private_helper()
        return result
    except Exception as e:
        from ..cognition.forensic_logger import log_error
        log_error(kind="MY_TOOL_FAIL", detail=str(e), source="tools/module_name")
        return f"[module_name ERROR] {e}"


# ── Registration ──────────────────────────────────────────────────────────────

registry.register(
    Tool(
        name="public_tool_function",
        description=(
            "One sentence: what this does for Igor. "
            "Second sentence: when to use it. "
            "Third sentence: what it returns."
        ),
        parameters={
            "type": "object",
            "properties": {
                "param": {
                    "type": "string",
                    "description": "What this parameter means. No example values with hardcoded IDs.",
                },
            },
            "required": [],
        },
        fn=public_tool_function,
    )
)
```

### Key conventions

- **`**_` in every tool function signature** — habit dispatch sends extra keys; without it you get TypeError
- **Registration at the bottom** — implementation first, registration last; makes the file readable top-to-bottom
- **Description strings must be useful to the LLM** — Igor reads these to decide which tool to call. "Does X" is worse than "Call this when you need X; returns Y"
- **No example values with hardcoded model IDs or instance names in description strings** — the LLM will use them verbatim and they go stale (this burned us with `anthropic/claude-haiku-4-5-20251001`)
- **Import `forensic_logger` lazily inside functions** — avoids circular imports at module load

### Adding a new tool: checklist

1. Write the function in `tools/your_module.py`
2. Register it with `registry.register(Tool(...))`
3. Add `your_module` to `tools/__init__.py` imports
4. Add `log_tool_call()` at the exit point
5. Add `log_error()` in every except block
6. Write a test in `tests/test_your_module.py`
7. If the tool needs a habit to fire it: write a `seed_your_module.py` and run it

---

## 3. Error Handling

### Rules

**No silent failures.** Every `except` block must do at least one of:
- Call `log_error()` from forensic_logger
- Call `logging.getLogger(__name__).error()` with the exception
- Re-raise with context added

**No bare `except:`** — always `except Exception as e:` at minimum. Catch specific exceptions
where you know them; fall back to `Exception` only as a final catch-all.

**No swallowed None returns.** If a function catches an exception and returns None, the caller
has no idea something failed. Return an error string or raise — never silently None.

```python
# Wrong
try:
    result = risky_call()
except Exception:
    pass  # ← never do this

# Wrong
try:
    result = risky_call()
except Exception as e:
    return None  # ← caller can't tell this from "no result"

# Right
try:
    result = risky_call()
except Exception as e:
    log_error(kind="RISKY_FAIL", detail=str(e), source="tools/my_module")
    return f"[my_module ERROR] {e}"
```

**Non-fatal vs. fatal.** Most tool errors are non-fatal — log and return an error string so
Igor can surface it. Only raise when the caller genuinely cannot continue (e.g. missing DB
connection at startup). Background threads must never raise unhandled — they kill the thread
silently.

---

## 4. Database Access

### Postgres only

The database is PostgreSQL at `postgresql://igor:choose_a_password@127.0.0.1/igor_wild_0001`.
Never use `sqlite3`. Never hardcode the URL — always read from env:

```python
db_url = os.environ.get(
    "IGOR_HOME_DB_URL",
    "postgresql://igor:choose_a_password@127.0.0.1/igor_wild_0001",
)
```

### JSONB queries

The `db_proxy` does blanket `?`→`%s` replacement. PostgreSQL's JSONB `?` operator gets
mis-translated → IndexError. Always use `jsonb_exists()` instead:

```python
# Wrong — breaks through db_proxy
WHERE metadata ? 'trigger'

# Right — always
WHERE jsonb_exists(metadata, 'trigger')
```

### Metadata serialization

Always use `json.dumps()` for metadata dicts. Python's `str()` produces `True`/`False`/`None`
(Python syntax) not `true`/`false`/`null` (JSON). Postgres rejects the Python form:

```python
# Wrong
metadata=str(my_dict)           # produces {'key': True} — invalid JSON
metadata=str(my_dict).replace("'", '"')  # brittle, misses True/False/None

# Right
metadata=json.dumps(my_dict)    # always
```

### ON CONFLICT — qualify table name

When updating `activation_count` in a conflict clause, qualify the column:

```python
# Wrong — ambiguous reference
ON CONFLICT (id) DO UPDATE SET activation_count = activation_count + 1

# Right
ON CONFLICT (id) DO UPDATE SET activation_count = memories.activation_count + 1
```

### node_registry

Only timestamp-format node IDs (YYYYMMDDHHMMSSuuuuuu) should be registered in
`node_registry`. Named fixture IDs (e.g. `PROC_TRAINING_PASS`, `INTERP_FACIA_*`) are stored
in `memories` only — registering them fails because `parse_node_id()` returns no `created_at`.

---

## 5. Testing

### Live systems, not mocks

Tests run against a real Postgres instance and real file paths. Mocked tests verify the mock,
not the behavior. If a test requires a live DB and one isn't available, skip with `pytest.mark.skip`
and a reason — do not mock the DB.

```python
import pytest
import os

pytestmark = pytest.mark.skipif(
    not os.getenv("IGOR_HOME_DB_URL"),
    reason="requires live Postgres"
)
```

### Test file naming

One test file per module: `tests/test_<module_name>.py`. If the module is in a subdirectory,
mirror it: `tests/tools/test_my_tool.py`.

### What to test

- **Happy path**: does the function return the right shape/content?
- **Error path**: does a bad input return an error string, not raise?
- **Integration**: does the tool write to the DB and is the row readable back?
- **Not**: implementation internals, private helpers, mocked external services

### Running tests

```bash
cd ~/TheIgors && source venv/bin/activate && python -m pytest tests/ -x -q
```

All 567 tests must pass before any commit. Never `--no-verify` a failing test suite.

---

## 6. Inertia Levels

Inertia is self-edit resistance — how carefully a change must be considered before making it.

| Level | Files | Requirement | Examples of "discuss before editing" |
|---|---|---|---|
| **HIGH** | `brainstem/`, `memory/models.py`, `cognition/reasoners/base.py` | Akien sign-off required; never casually edit | Adding a field to Memory dataclass, changing CP node structure, modifying base reasoner interface |
| **MEDIUM** | `cognition/`, `memory/cortex.py`, `anthropic.py`, `main.py` | Discuss with Akien before editing | Adding a thalamus gate, changing cortex.search() signature, modifying milieu mutation logic |
| **LOW** | `tools/`, `dashboard/`, `thalamus.py`, `cognition/word_graph.py`, `claudecode/`, `design_docs/` | Freely improvable; read file first | Adding a new tool, fixing a tool bug, updating docs, adding a dashboard endpoint |

### Practical meaning

**HIGH** — if you're about to edit a HIGH file and you haven't had an explicit conversation
about why, stop. The architecture depends on these files being stable. A wrong change here
can corrupt the memory graph or break all inference routing.

**MEDIUM** — read the relevant design doc first. Post a one-line plan to the channel before
making the change. These files have many callers; a signature change ripples.

**LOW** — read the file before editing (always). Make the change. Tests pass → commit.
No special process required, but don't cross into MEDIUM files as "just one more thing."

### Inertia and self-editing

When Igor self-edits, the inertia level gates whether he can proceed autonomously:
- LOW: Igor can self-edit directly via `patch_source_file`
- MEDIUM: Igor posts a plan and waits for approval (or escalates to Claude Code)
- HIGH: Igor escalates to Claude Code regardless; never self-edits

---

## 7. OpenRouter Model IDs

OpenRouter model IDs use a different format than Anthropic direct:

| Provider | Format | Example |
|---|---|---|
| OpenRouter | `provider/model-name` with dots | `anthropic/claude-haiku-4.5` |
| Anthropic direct | `model-name-with-date` | `claude-haiku-4-5-20251001` |

Never hardcode a specific model ID in a parameter description string — the LLM will use it
verbatim and model names change. Store model IDs in env vars with sensible defaults:

```python
_HAIKU_MODEL = os.getenv("INNER_CC_HAIKU_MODEL", "anthropic/claude-haiku-4.5")
```

When an OR call returns HTTP 400 "not a valid model ID", check OR's `/models` endpoint for
the current name. Ticket `T-or-model-auto-update` will automate this.

---

*Last updated: 2026-03-31. Maintained by Akien + Claude. Future: DSB at `design_docs_for_igor/standards.dsb`.*
