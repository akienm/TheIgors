"""
seed_traversal_context.py — PROC_TRAVERSAL_CTX_CONVENTION memory (T-traversal-context).

Seeds one PROCEDURAL memory documenting the TRAVERSAL_CTX_ID TWM convention
so Igor can self-describe traversal context behavior when asked.

Run from repo root:
  python claudecode/seed_traversal_context.py
"""

import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.environ.setdefault(
    "IGOR_DB_PATH",
    str(Path.home() / ".TheIgors" / "Igor-wild-0001" / "wild-0001.db"),
)

from wild_igor.igor.memory.models import Memory, MemoryType
from wild_igor.igor.memory.cortex import Cortex

DB_PATH = Path(os.environ["IGOR_DB_PATH"])
cortex = Cortex(DB_PATH, instance_id="Igor-wild-0001")

habit = Memory(
    id="PROC_TRAVERSAL_CTX_CONVENTION",
    narrative=(
        "Traversal context is how habit chains share state across steps. "
        "When a multi-step habit chain starts, traversal_start() mints a UUID "
        "called the context_id. That context_id is pushed to TWM under the key "
        "'TRAVERSAL_CTX_ID'. Each habit in the chain reads the context_id from TWM, "
        "then calls ctx_get(context_id, key) to read state set by earlier steps and "
        "ctx_set(context_id, key, value) to write state for later steps. "
        "The traversal_contexts table in the SQLite DB stores all these key/value pairs "
        "with a step column recording which step wrote each key. "
        "This is the substrate that OS primitives (PRIM_LIST_DIR, PRIM_ITER_NEXT, etc.) "
        "will run on — each primitive reads/writes the shared context so a 'for each file' "
        "loop can be assembled entirely from habits already in the graph."
    ),
    memory_type=MemoryType.PROCEDURAL,
    metadata={
        "habit_type": "context_inject",
        "trigger": (
            "traversal context habit chain state machine ctx_get ctx_set "
            "TRAVERSAL_CTX_ID context_id traversal_start"
        ),
        "pattern": "traversal_context",
        "why": (
            "T-traversal-context: documents the TRAVERSAL_CTX_ID TWM convention "
            "so Igor can explain and use traversal context correctly. "
            "Prerequisite: habit chains need to know how to share state."
        ),
        "inertia": 0.30,
    },
)

existing = cortex.get(habit.id)
if existing:
    print(f"  [skip] {habit.id} already exists")
else:
    cortex.store(habit)
    cortex.add_child("CP3", habit.id)
    print(f"  [seeded] {habit.id}  (context_inject) → parent=CP3")

print("Done. PROC_TRAVERSAL_CTX_CONVENTION seeded.")
