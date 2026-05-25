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
    str(Path.home() / ".TheIgors" / "Igor-wild-0001" / "wild-0001.db"),
)


from devices.igor.memory.models import Memory, MemoryType
from devices.igor.memory.cortex import Cortex

DB_PATH = Path(os.environ["IGOR_DB_PATH"])
cortex = Cortex(instance_id="Igor-wild-0001")

habit = Memory(
    id="PROC_WORKER_FOREMAN",
    narrative=(
        "When a sprint worker signals completion — 'worker_done: <ticket>' — "
        "or when BOREDOM_DETECTED / foreman_scan fires, I check the task queue "
        "for the next pending ticket and route by its `worker` metadata field "
        "(D-worker-mode-routing-2026-04-21). "
        "If worker='igor': I process in-process via the engram chain — cheap "
        "tier, Qwen-backed — by calling adopt_next_ticket, which adopts the "
        "ticket as an active goal and drives pe_chain.run_pe_chain. "
        "If worker='claude' (or the field is missing, which defaults to claude "
        "for safety): I launch a konsole CC session — reviewable, suited to "
        "HIGH-inertia or XL tickets — by calling launch_next_worker's "
        "konsole-spawn path. "
        "I also respond to Akien saying 'start the queue', 'launch next worker', "
        "'start working on tickets', or 'what's next in the queue'. "
        "The dispatch switch lives at the top of launch_next_worker: it peeks "
        "the next-best pending ticket's worker field and routes accordingly. "
        "If the queue is empty or all items are done/blocked, I report that "
        "and stop. One ticket at a time, serially, until the queue clears."
    ),
    memory_type=MemoryType.PROCEDURAL,
    metadata={
        "habit_type": "reactive",
        "trigger": "worker_done",
        "code_ref": "worker_foreman:launch_next_worker",
        "twm_ttl_seconds": 60,
        "why": (
            "Closes the orchestration loop and routes work to the right tier: "
            "cheap Igor-in-process for ordinary tickets, reviewable CC for "
            "HIGH-inertia / XL. Akien steps away; Igor drives the queue. "
            "Reactive: result surfaces to TWM and falls through to LLM — "
            "does not terminate the turn with a canned response."
        ),
        "inertia": 0.20,
        "decision_id": "D-worker-mode-routing-2026-04-21",
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
