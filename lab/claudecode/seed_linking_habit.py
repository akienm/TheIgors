"""
seed_linking_habit.py — PROC_NODE_ADOPTION habit (T-linking-habit).

Seeds a cognitive habit that Igor can invoke on demand to link orphaned
FACTUAL/EPISODIC nodes to their nearest CP/ID parent via embedding similarity.

The periodic version runs automatically via HeartbeatSource._run_orphan_adoption()
every 5 minutes when IGOR_NODE_ADOPTION_ENABLED=true.

This habit is the on-demand companion: Igor can trigger it when he observes
that recent memory stores have left nodes unconnected.

Run from repo root:
  python claudecode/seed_linking_habit.py
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

habits = [
    Memory(
        id="PROC_NODE_ADOPTION",
        narrative=(
            "When new FACTUAL or EPISODIC memories accumulate without connections to the "
            "main graph, I notice the graph is growing fragmented. I run the node adoption "
            "pass (run_node_adoption tool) to link orphaned nodes to their nearest CP or "
            "identity attractor via embedding similarity. This keeps the graph dense and "
            "traversable — isolated nodes can't be reached during search. "
            "I do this proactively after storing several new memories in a session, or "
            "when I observe that recent learning hasn't been integrated into the main tree. "
            "The heartbeat also runs this automatically every 5 minutes "
            "when IGOR_NODE_ADOPTION_ENABLED=true."
        ),
        memory_type=MemoryType.PROCEDURAL,
        parent_id="CP1",
        metadata={
            "habit_type": "action",
            "trigger": (
                "orphan nodes unlinked disconnected graph fragmented "
                "new memories stored link connect adopt integrate "
                "node adoption link memories to graph"
            ),
            "code_ref": "tools.graph_ops:run_node_adoption",
            "twm_ttl_seconds": 300,
            "pattern": "graph_maintenance",
            "why": (
                "T-linking-habit #318: 5139 orphaned nodes found after D199. "
                "FACTUAL/EPISODIC nodes created during reading are not automatically "
                "connected to CP/ID parents. Unconnected nodes are unreachable in search. "
                "This habit closes the gap between new memory creation and graph integration."
            ),
            "inertia": 0.20,
            "gate": "IGOR_NODE_ADOPTION_ENABLED",
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

print("Done. PROC_NODE_ADOPTION habit seeded.")
