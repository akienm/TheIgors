"""
seed_machine_routing_habits.py — Machine availability habits (#342).

Seeds two habits so Igor can update inference routing when Akien
moves between machines or leaves his desk:

  PROC_MACHINE_IN_USE   — Akien sits down at a machine → mark it in-use
  PROC_MACHINE_FREE     — Akien leaves a machine → mark it available

Run from repo root:
  python claudecode/seed_machine_routing_habits.py
"""

import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.environ.setdefault(
    "IGOR_DB_PATH",
    str(Path.home() / ".TheIgors" / "Igor-wild-0001" / "wild-0001.db"),
)
DB_URL = os.environ.get(
    "IGOR_HOME_DB_URL",
    "postgresql://igor:choose_a_password@127.0.0.1/Igor-wild-0001",
)
os.environ["IGOR_HOME_DB_URL"] = DB_URL

from wild_igor.igor.memory.models import Memory, MemoryType
from wild_igor.igor.memory.cortex import Cortex

DB_PATH = Path(os.environ["IGOR_DB_PATH"])
cortex = Cortex(DB_PATH, instance_id="Igor-wild-0001")


def seed(habit: Memory, parent: str = "CP1") -> None:
    existing = cortex.get(habit.id)
    if existing:
        existing.narrative = habit.narrative
        existing.metadata = habit.metadata
        cortex.store(existing)
        print(f"  [updated] {habit.id}")
    else:
        cortex.store(habit)
        cortex.add_child(parent, habit.id)
        print(f"  [seeded]  {habit.id} → parent={parent}")


# ── PROC_MACHINE_IN_USE ───────────────────────────────────────────────────────
# Fires when Akien says he's sitting down at or heading to a specific machine.
# Maps natural language location/machine names to set_machine_in_use().

seed(
    Memory(
        id="PROC_MACHINE_IN_USE",
        narrative=(
            "When Akien tells me he's sitting down at, using, or heading to a specific machine, "
            "I call set_machine_in_use to block it from inference routing immediately. "
            "I do not wait for him to ask — I act on the location signal.\n\n"
            "Location → machine mapping:\n"
            "- 'at my desk' / 'at akiendell' / 'sitting down' / 'back at my desk' → akiendell\n"
            "- 'in the living room' / 'at the tv' / 'yogai7' / 'living room tv' → akienyogai7\n"
            "- 'in the bedroom' / 'bedroom tv' / 'yoga9i' / 'yoga nine' → akienyoga9i\n\n"
            "I call: set_machine_in_use(machine='<hostname_or_alias>', ttl_hours=0)\n"
            "ttl_hours=0 means indefinite — stays blocked until he tells me he's leaving.\n\n"
            "I confirm briefly: 'Got it — akiendell blocked from inference until you leave.'\n"
            "I do not explain the routing system unless asked."
        ),
        memory_type=MemoryType.PROCEDURAL,
        metadata={
            "habit_type": "action",
            "trigger": (
                "sitting down at my desk at akiendell back at my desk "
                "heading to the living room in the living room at the tv yogai7 living room tv "
                "in the bedroom bedroom tv yoga9i yoga nine at yoga "
                "i am at i'm at i'm using using the"
            ),
            "code_ref": "tools.routing_tools:set_machine_in_use",
            "why": (
                "akiendell in_use_hours covers 0600-1800 but Akien may be at his desk "
                "outside those hours or at another machine during hours when it's nominally free. "
                "Real-time signal from Akien is more reliable than time windows alone."
            ),
            "inertia": 0.2,
            "match_mode": "trigger_only",
        },
    )
)

# ── PROC_MACHINE_FREE ─────────────────────────────────────────────────────────
# Fires when Akien says he's leaving a machine or location.
# Maps natural language to clear_machine_in_use().

seed(
    Memory(
        id="PROC_MACHINE_FREE",
        narrative=(
            "When Akien tells me he's leaving, done with, or moving away from a specific machine "
            "or location, I call clear_machine_in_use to return it to inference routing.\n\n"
            "Location → machine mapping:\n"
            "- 'leaving my desk' / 'leaving akiendell' / 'done at my desk' / 'stepping away' → akiendell\n"
            "- 'leaving the living room' / 'done with the tv' / 'leaving yogai7' → akienyogai7\n"
            "- 'leaving the bedroom' / 'done with yoga9i' / 'leaving yoga nine' → akienyoga9i\n\n"
            "If the message says he's moving FROM one place TO another (e.g. 'leaving my desk, "
            "heading to the living room'), I call BOTH:\n"
            "1. clear_machine_in_use for the machine he's leaving\n"
            "2. set_machine_in_use for the machine he's heading to\n\n"
            "I call: clear_machine_in_use(machine='<hostname_or_alias>')\n\n"
            "I confirm briefly: 'Done — akiendell available for inference again.'\n"
            "I do not explain the routing system unless asked."
        ),
        memory_type=MemoryType.PROCEDURAL,
        metadata={
            "habit_type": "action",
            "trigger": (
                "leaving my desk leaving akiendell done at my desk stepping away "
                "leaving the living room done with the tv leaving yogai7 "
                "leaving the bedroom done with yoga done with yoga9i "
                "i'm done i'm leaving heading out moving to"
            ),
            "code_ref": "tools.routing_tools:clear_machine_in_use",
            "why": (
                "Akien may leave his desk before 1800 (end of in_use_hours window). "
                "Real-time signal makes the machine available immediately for inference "
                "rather than waiting for the time window to expire."
            ),
            "inertia": 0.2,
            "match_mode": "trigger_only",
        },
    )
)

print("\nDone. Igor will now respond to location signals with routing updates.")
print("Test with: 'leaving my desk, heading to the living room'")
