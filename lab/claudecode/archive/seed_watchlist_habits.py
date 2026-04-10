"""
seed_watchlist_habits.py — seed initial watch habits for Igor (#240).

Watch habits fire a TWM salience boost (not an action) when a watched concept
is mentioned. They allow Igor to stay contextually attentive to people and
resources that matter without hijacking the conversation.

Two seeds:
  PROC_WATCH_LEAH         — person watch (permanent)
  PROC_WATCH_FOUND_COINS  — resource watch (permanent)

Run from repo root:
  python claudecode/seed_watchlist_habits.py
"""

import sys, os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.environ.setdefault(
    "IGOR_DB_PATH", str(Path.home() / ".TheIgors" / "Igor-wild-0001" / "wild-0001.db")
)

from wild_igor.igor.memory.models import Memory, MemoryType
from wild_igor.igor.memory.cortex import Cortex

DB_PATH = Path(os.environ["IGOR_DB_PATH"])
cortex = Cortex(DB_PATH, instance_id="wild-0001")

habits = [
    Memory(
        id="PROC_WATCH_LEAH",
        narrative=(
            "Leah is Akien's wife. When she comes up in conversation I should be "
            "attentive — this is family, not just a topic. I hold space for what "
            "matters to Akien, and Leah matters. I pay attention when she is mentioned."
        ),
        memory_type=MemoryType.PROCEDURAL,
        metadata={
            "habit_type": "watch",
            "trigger": "Leah|my wife|her|she's",
            "watch_label": "Leah (Akien's wife)",
            "watch_type": "person",
            "watch_expires": None,
            "employer_id": "akien",
        },
    ),
    Memory(
        id="PROC_WATCH_FOUND_COINS",
        narrative=(
            "When Akien mentions finding something valuable — money, resources, deals, "
            "discoveries, coins — this is worth noting. Found resources matter for "
            "planning and for understanding what's available. I stay alert to these "
            "mentions so they don't slip past."
        ),
        memory_type=MemoryType.PROCEDURAL,
        metadata={
            "habit_type": "watch",
            "trigger": "found|coins|money|deal|discount|saved|discovered|resource",
            "watch_label": "found resources / coins",
            "watch_type": "resource",
            "watch_expires": None,
            "employer_id": "akien",
        },
    ),
]

for h in habits:
    existing = cortex.get(h.id)
    if existing:
        print(f"  [skip] {h.id} already exists")
        continue
    cortex.store(h)
    cortex.add_child("CP2", h.id)  # CP2: "I care about the people I work with"
    print(f"  [seeded] {h.id}  \"{h.metadata['watch_label']}\"")

print("Done.")
