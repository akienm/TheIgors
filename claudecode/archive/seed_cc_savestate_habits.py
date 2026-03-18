"""
seed_cc_savestate_habits.py — P1: CC savestate operations through Igor.

Four habits so CC routes through the bridge instead of bash subprocesses:

  CC_STORE_DECISION   — store design decision as FACTUAL memory
  CC_STORE_SESSION    — append session summary to ring memory
  CC_QUEUE_TASK       — add task to cc_channel queue
  CC_CREATE_TICKET    — create GitHub issue (wraps existing create_work_order)

Run from repo root:
    python3 ~/TheIgors/claudecode/seed_cc_savestate_habits.py
"""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
os.environ.setdefault(
    "IGOR_DB_PATH", str(Path.home() / ".TheIgors" / "igor_wild_0001" / "wild-0001.db")
)

from wild_igor.igor.memory.models import Memory, MemoryType
from wild_igor.igor.memory.cortex import Cortex

DB_PATH = Path(os.environ["IGOR_DB_PATH"])
cortex = Cortex(DB_PATH, instance_id="wild-0001")

habits = [
    Memory(
        id="CC_STORE_DECISION",
        narrative=(
            "Claude Code can ask me to store a design decision directly into my memory. "
            "I create a FACTUAL memory with the decision ID, summary, and status. "
            "This replaces cc_queue.py flush_decision — the decision goes into my graph "
            "natively, not through a bash subprocess."
        ),
        memory_type=MemoryType.PROCEDURAL,
        metadata={
            "trigger": "store decision flush decision save design decision",
            "habit_type": "action",
            "code_ref": "tools.ops:store_decision",
            "why": "P1 — CC routes through Igor not bash; decisions land in memory graph",
            "inertia": 0.25,
        },
    ),
    Memory(
        id="CC_STORE_SESSION",
        narrative=(
            "Claude Code can ask me to record a session summary in my ring memory. "
            "I write the session ID and summary as a ring entry with category=session_summary. "
            "This replaces cc_queue.py flush_session — the session note lives in my "
            "short-term memory where I can read it on the next turn."
        ),
        memory_type=MemoryType.PROCEDURAL,
        metadata={
            "trigger": "store session flush session save session summary",
            "habit_type": "action",
            "code_ref": "tools.ops:store_session_note",
            "why": "P1 — CC routes through Igor not bash; session notes land in ring memory",
            "inertia": 0.25,
        },
    ),
    Memory(
        id="CC_QUEUE_TASK",
        narrative=(
            "Claude Code can ask me to add a task to the CC channel queue. "
            "I write the task JSON to ~/.TheIgors/cc_channel/queue.json, "
            "skipping duplicates by ID. This replaces cc_queue.py add — "
            "task queuing goes through me, not a bash subprocess."
        ),
        memory_type=MemoryType.PROCEDURAL,
        metadata={
            "trigger": "queue task add task cc queue worker task",
            "habit_type": "action",
            "code_ref": "tools.ops:queue_task",
            "why": "P1 — CC routes through Igor not bash; task queuing is an Igor operation",
            "inertia": 0.25,
        },
    ),
    Memory(
        id="CC_CREATE_TICKET",
        narrative=(
            "Claude Code can ask me to create a GitHub issue. "
            "I call create_work_order with title, description, and optional labels. "
            "Returns the issue number and URL. This replaces gh CLI bash calls — "
            "ticket creation goes through me."
        ),
        memory_type=MemoryType.PROCEDURAL,
        metadata={
            "trigger": "create ticket create issue github issue new ticket work order",
            "habit_type": "action",
            "code_ref": "tools.github:create_work_order",
            "why": "P1 — CC routes through Igor not bash; Igor owns GitHub operations",
            "inertia": 0.25,
        },
    ),
]

for habit in habits:
    cortex.store(habit)
    print(f"stored: {habit.id}")

print("\nverifying:")
for habit in habits:
    mem = cortex.get(habit.id)
    print(f"  {mem.id:22s}  code_ref={mem.metadata['code_ref']}")
