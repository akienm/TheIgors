"""
seed_worker_foreman.py — PROC_WORKER_FOREMAN habit.

Seeds one action habit that closes the worker orchestration loop:
when Igor receives "worker_done: <ticket>" from a completing sprint session,
this habit fires and launches the next pending ticket automatically.

Akien can also trigger it by saying "start the queue" or "launch next worker".

Run from repo root:
  python claudecode/seed_worker_foreman.py
"""

import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.environ.setdefault(
    "IGOR_DB_PATH",
    str(Path.home() / ".TheIgors" / "igor_wild_0001" / "wild-0001.db"),
)

DB_URL = os.environ.get(
    "IGOR_HOME_DB_URL",
    f"postgresql://igor:choose_a_password@127.0.0.1/igor_wild_0001",
)
if DB_URL:
    os.environ["IGOR_HOME_DB_URL"] = DB_URL

from wild_igor.igor.memory.models import Memory, MemoryType
from wild_igor.igor.memory.cortex import Cortex

DB_PATH = Path(os.environ["IGOR_DB_PATH"])
cortex = Cortex(DB_PATH, instance_id="igor_wild_0001")

habit = Memory(
    id="PROC_WORKER_FOREMAN",
    narrative=(
        "When a sprint worker signals completion — 'worker_done: <ticket>' — "
        "I check the task queue for the next pending ticket and launch a new worker. "
        "I also respond to Akien saying 'start the queue', 'launch next worker', "
        "'start working on tickets', or 'what's next in the queue'. "
        "I call launch_next_worker, which reads queue.json, skips any in_progress ticket "
        "(another worker is still running), finds the next pending by priority, and "
        "spawns a konsole worker session running /sprint <ticket-id>. "
        "If the queue is empty or all items are done/blocked, I report that and stop. "
        "This is the foreman loop: one ticket at a time, serially, until the queue clears."
    ),
    memory_type=MemoryType.PROCEDURAL,
    metadata={
        "habit_type": "reactive",
        "trigger": (
            "worker_done launch next worker "
            "start the queue start working on tickets what's next in the queue"
        ),
        "code_ref": "worker_foreman:launch_next_worker",
        "twm_ttl_seconds": 60,
        "why": (
            "Closes the orchestration loop: sprint worker signals done → "
            "foreman launches next ticket. Akien steps away; Igor drives the queue. "
            "Reactive: result surfaces to TWM and falls through to LLM — "
            "does not terminate the turn with a canned response."
        ),
        "inertia": 0.20,
    },
)

existing = cortex.get(habit.id)
if existing:
    # Update in place
    existing.narrative = habit.narrative
    existing.metadata = habit.metadata
    cortex.store(existing)
    print(f"  [updated] {habit.id}")
else:
    cortex.store(habit)
    cortex.add_child("CP1", habit.id)
    print(f"  [seeded] {habit.id} (action) → parent=CP1")

print("Done. PROC_WORKER_FOREMAN seeded.")
