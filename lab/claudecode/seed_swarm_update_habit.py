"""
seed_swarm_update_habit.py — PROC_SWARM_UPDATE habit (T-swarm-update / D204).

Triggers update_swarm() when Akien asks to update all boxes.

Run from repo root:
  python claudecode/seed_swarm_update_habit.py
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
cortex = Cortex(instance_id="Igor-wild-0001")

habits = [
    Memory(
        id="PROC_SWARM_UPDATE",
        narrative=(
            "When Akien asks to update all Igor instances across the cluster — "
            "'update swarm', 'pull latest', 'restart all boxes', 'swarm update' — "
            "I run the coordinated swarm update. "
            "This performs a git pull on every online box, then touches restart.flag "
            "for each Igor instance directory (~/.TheIgors/*/) so the idle loop "
            "restarts each instance at the next cycle. "
            "Remote boxes are handled via SSH (OS-typed commands); local box is direct subprocess. "
            "If git pull fails on a box, I skip the restart flags for that box and report the error. "
            "I return a per-box audit log showing pull result and instance count."
        ),
        memory_type=MemoryType.PROCEDURAL,
        parent_id="CP1",
        metadata={
            "habit_type": "action",
            "trigger": (
                "update swarm pull latest restart all boxes swarm update "
                "update all igors git pull swarm update igor instances "
                "restart all igor pull and restart"
            ),
            "code_ref": "tools.cluster_ssh:update_swarm",
            "twm_ttl_seconds": 600,
            "pattern": "swarm_ops",
            "why": (
                "D204 / T-swarm-update #326: Coordinated update across all running "
                "Igor instances. git pull + restart.flag glob covers any box with "
                "multiple CoAs without needing explicit instance IDs."
            ),
            "inertia": 0.20,
        },
    ),
]

for h in habits:
    existing = cortex.get(h.id)
    if existing:
        print(f"  [skip] {h.id} already exists")
        continue
    cortex.store(h)
    cortex.add_child("CP1", h.id)
    print(f"  [seeded] {h.id}  (action) → parent=CP1")

print("Done. PROC_SWARM_UPDATE habit seeded.")
