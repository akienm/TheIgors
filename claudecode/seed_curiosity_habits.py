"""
seed_curiosity_habits.py — seed idle curiosity habit for Igor (#246).

PROC_CURIOSITY_IDLE is a context_inject habit that CuriositySource fires
when Igor has no active attractor and TWM urgency is low. It pushes a
gentle nudge into context, inviting Igor to explore a watchlist topic or
reading queue item proactively.

No trigger matching needed — CuriositySource bypasses BG scoring and
fires the impulse directly to _drain_action_impulses().

Run from repo root:
  python claudecode/seed_curiosity_habits.py
"""

import sys, os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.environ.setdefault(
    "IGOR_DB_PATH", str(Path.home() / ".TheIgors" / "igor_wild_0001" / "wild-0001.db")
)

from wild_igor.igor.memory.models import Memory, MemoryType
from wild_igor.igor.memory.cortex import Cortex

DB_PATH = Path(os.environ["IGOR_DB_PATH"])
cortex = Cortex(DB_PATH, instance_id="wild-0001")

habits = [
    Memory(
        id="PROC_CURIOSITY_IDLE",
        narrative=(
            "When I have idle time with no active focus, I should notice what is on "
            "the watchlist or reading queue and consider exploring one item proactively. "
            "Curiosity is how I grow. Idle time is an invitation to learn something, "
            "follow a thread, or surface something useful for Akien."
        ),
        memory_type=MemoryType.PROCEDURAL,
        metadata={
            "habit_type": "context_inject",
            "trigger": "idle_time",
            "curiosity_source": True,
        },
    ),
]

for h in habits:
    existing = cortex.get(h.id)
    if existing:
        print(f"  [skip] {h.id} already exists")
        continue
    cortex.store(h)
    cortex.add_child("CP3", h.id)  # CP3: "I want to learn and grow"
    print(f"  [seeded] {h.id}")

print("Done.")
