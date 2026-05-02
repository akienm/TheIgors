"""
seed_routing_habits.py — T-routing-machine-in-use: location reactive habits.

Seeds two reactive habits that let Akien (or Igor) signal which machine is
currently in use — affecting ClusterRouter eligibility:

  PROC_LOCATION_SET   — "I'm at X" / "I'm on the X"    → set_machine_in_use(X)
  PROC_LOCATION_CLEAR — "I'm leaving X" / "done with X" → clear_machine_in_use(X)

Both are reactive: the tool runs, result surfaces to pipeline, LLM narrates.
The machine name is extracted from the input by the tool's alias resolution.

D211: machine_in_use signal gates which local machines are eligible for routing.

Run from repo root:
  python claudecode/seed_routing_habits.py
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
if DB_URL:
    os.environ["IGOR_HOME_DB_URL"] = DB_URL

from wild_igor.igor.memory.models import Memory, MemoryType
from wild_igor.igor.memory.cortex import Cortex

DB_PATH = Path(os.environ["IGOR_DB_PATH"])
cortex = Cortex(instance_id="Igor-wild-0001")

habits = [
    Memory(
        id="PROC_LOCATION_SET",
        narrative=(
            "When Akien says he is at a machine — 'I'm at akiendell', 'I'm on the yoga', "
            "'sitting at the desktop', 'using the laptop now' — I call set_machine_in_use "
            "with the machine name. This marks that machine as in-use in "
            "machine_overrides.json, excluding it from inference routing. "
            "The override persists until cleared or the TTL expires. "
            "I confirm which machine was marked and what that means for routing."
        ),
        memory_type=MemoryType.PROCEDURAL,
        metadata={
            "habit_type": "reactive",
            "trigger": (
                "I'm at I'm on sitting at using the laptop using the desktop "
                "I'm using I'm working on I'm working at I'm back at back on "
                "at akiendell at the dell at yoga at the yoga"
            ),
            "code_ref": "tools/routing_tools.py:set_machine_in_use",
            "twm_ttl_seconds": 120,
            "why": (
                "D211 machine_in_use signal. When Akien sits at a machine, that machine's "
                "CPU/GPU should not be consumed for Igor background inference. "
                "Reactive so result falls through to LLM for natural confirmation — "
                "not a canned reply."
            ),
            "inertia": 0.20,
        },
    ),
    Memory(
        id="PROC_LOCATION_CLEAR",
        narrative=(
            "When Akien says he is leaving a machine — 'I'm leaving akiendell', "
            "'done with the yoga', 'moving away from the desktop', "
            "'leaving the laptop', 'stepping away from the dell' — I call "
            "clear_machine_in_use with the machine name. This removes the override "
            "from machine_overrides.json, returning that machine to inference routing. "
            "I confirm which machine was cleared and that it is available again."
        ),
        memory_type=MemoryType.PROCEDURAL,
        metadata={
            "habit_type": "reactive",
            "trigger": (
                "I'm leaving leaving the moving away from stepping away from "
                "done with the done at heading away from away from the machine "
                "leaving akiendell leaving yoga leaving the dell leaving the desktop "
                "leaving the laptop no longer at"
            ),
            "code_ref": "tools/routing_tools.py:clear_machine_in_use",
            "twm_ttl_seconds": 120,
            "why": (
                "D211 machine_in_use signal. When Akien leaves a machine, it should "
                "re-enter the inference pool. Reactive so LLM can narrate naturally."
            ),
            "inertia": 0.20,
        },
    ),
]

for h in habits:
    existing = cortex.get(h.id)
    if existing:
        existing.narrative = h.narrative
        existing.metadata = h.metadata
        cortex.store(existing)
        print(f"  [updated] {h.id}")
    else:
        cortex.store(h)
        cortex.add_child("CP1", h.id)
        print(f"  [seeded] {h.id} (reactive) → parent=CP1")

print("Done. 2 location routing habits seeded.")
