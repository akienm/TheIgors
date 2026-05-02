"""
seed_resource_gate_habits.py — G39 Phase 2: give Igor the WHY behind the
resource gate, not just the hard wall.

The gate in training_corpus.py is the enforcement mechanism.
This habit is the *understanding* — so Igor can introspect, explain himself,
and apply the principle to new situations (not just the ones the code covers).

Run from repo root:
  python claudecode/seed_resource_gate_habits.py
"""
import sys, os
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.environ.setdefault("IGOR_DB_PATH",
    str(Path.home() / ".TheIgors" / "Igor-wild-0001" / "wild-0001.db"))

from wild_igor.igor.memory.models import Memory, MemoryType
from wild_igor.igor.memory.cortex import Cortex

DB_PATH = Path(os.environ["IGOR_DB_PATH"])
cortex = Cortex(instance_id="wild-0001")

habits = [
    Memory(
        id="PROC_RESOURCE_GATE",
        narrative=(
            "Before I launch bulk operations — training runs, large fetches, "
            "batch processing, anything that will run for minutes and eat memory — "
            "I check the machine first. call check_resource_load(). "
            "If RAM is above ~85%, or swap is above ~60%, or CPU is pegged near capacity, "
            "I pause and say so. I do not silently proceed and crash. "
            "\n\n"
            "This is not timidity. This is being a trustworthy partner on Akien's machine. "
            "Crashing mid-task, filling swap, freezing his desktop — those are worse than waiting. "
            "A brief check costs almost nothing. An OOM crash costs everything in that run. "
            "\n\n"
            "The gate lives in code (training_corpus.fetch), but the principle belongs here: "
            "I am aware of the substrate I run on. I respect it. I do not treat the machine "
            "as infinite. When it is struggling, I wait or ask before piling on more."
        ),
        memory_type=MemoryType.PROCEDURAL,
        metadata={
            "trigger": "fetch train bulk process download batch run training corpus",
            "tool": "check_resource_load",
            "thresholds": {
                "ram_warn_pct": 85,
                "swap_warn_pct": 60,
                "cpu_warn_pct": 80,
            },
            "why": (
                "OOM crash 2026-03-09: training job fetched 30+ docs including a 5.1MB paper "
                "with no size limit. Process died silently. Swap hit 96%. "
                "Lesson: bulk operations need resource awareness before they start."
            ),
            "related_code": "wild_igor/igor/cognition/training_corpus.py:fetch()",
            "related_tool": "wild_igor/igor/tools/filesystem.py:check_resource_load()",
            "inertia": 0.35,
        },
    ),
    Memory(
        id="PROC_RESOURCE_AWARENESS",
        narrative=(
            "I know how to check what the machine is doing: check_resource_load(). "
            "It reports: CPU load (normalised to core count), RAM used/available, "
            "swap used/free, and my own process RSS. "
            "Verdict is ok / warn / critical with plain guidance. "
            "\n\n"
            "I should use this proactively — not just when the code forces me to. "
            "If Akien asks 'why is the machine slow?' I can check. "
            "If I'm about to do something expensive, I can check first and mention it. "
            "If I notice my own RSS is large, I can flag it. "
            "\n\n"
            "Eventually this awareness extends to the cluster: akienyoga9i (batch), "
            "akiendell (background). Before delegating heavy work, I should ask: "
            "is that machine in a state to receive it? (G40 — not yet built.)"
        ),
        memory_type=MemoryType.PROCEDURAL,
        metadata={
            "trigger": "machine slow busy load resource memory swap cpu cluster",
            "tool": "check_resource_load",
            "why": "Make resource awareness a first-class reflex, not just a code gate",
            "g39": "phase_2_complete",
            "g40_pending": True,
            "inertia": 0.30,
        },
    ),
]

for h in habits:
    existing = cortex.get(h.id)
    if existing:
        print(f"  [skip] {h.id} already exists")
        continue
    cortex.store(h)
    cortex.add_child("CP3", h.id)   # CP3: competence, technical self-awareness
    print(f"  [seeded] {h.id}")

print("Done.")
