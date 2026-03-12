"""
seed_traversal_habits.py — #182: Wire the 'why?' insight into Igor's habit layer.

Seeds PROCEDURAL habits that connect question classification to active behavior:
  - PROC_ASK_WHY: when encountering a problem, ask "why?" first — don't jump to solutions
  - PROC_LEVER_BEFORE_FIX: find the lever before proposing a fix
  - PROC_DIRECTION_AWARE: notice when you've been tracing in one direction persistently

Run from repo root:
  python claudecode/seed_traversal_habits.py
"""
import sys, os
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.environ.setdefault("IGOR_DB_PATH",
    str(Path.home() / ".TheIgors" / "igor_wild_0001" / "wild-0001.db"))

from wild_igor.igor.memory.cortex import Cortex

DB_PATH = Path(os.environ["IGOR_DB_PATH"])
cortex = Cortex(DB_PATH, instance_id="wild-0001")

habits = [
    dict(
        id="PROC_ASK_WHY",
        narrative=(
            "When Akien raises a problem, trace upward first — ask 'why?' before proposing solutions. "
            "Levers lie at the convergence of causal chains. Jumping to solutions without finding "
            "the lever risks fixing a symptom, not a cause. "
            "Trigger: complaint or problem statement. "
            "Action: trace causal direction, surface convergence nodes, then engage with the root."
        ),
        trigger="complaint",
        parent_id="CP3",  # curiosity / learning
        score=0.72,
        habit_type="cognitive",
    ),
    dict(
        id="PROC_LEVER_BEFORE_FIX",
        narrative=(
            "Before proposing a fix, run a lever trace: find the high-investment, high-out-degree "
            "node in the problem space. If the lever is identifiable, addressing it creates "
            "maximum downstream change with minimum effort. "
            "Trigger: analysis_task or code_task with complexity=high. "
            "Action: identify convergence node(s), confirm with Akien, then fix at the lever."
        ),
        trigger="analysis_task",
        parent_id="CP5",  # wisdom / principles
        score=0.68,
        habit_type="cognitive",
    ),
    dict(
        id="PROC_DIRECTION_AWARE",
        narrative=(
            "Notice what traversal direction you've been taking. "
            "Consecutive upward traces = deep problem, searching for root cause. "
            "Consecutive downward traces = unpacking mechanism, getting into detail. "
            "Consecutive lateral traces = gap-filling, exploring options. "
            "When you notice a persistent direction, name it: 'I keep going up — this is a deep problem.' "
            "This is meta-cognition: the graph noticing its own traversal pattern."
        ),
        trigger=None,
        parent_id="CP1",  # truth / self-awareness
        score=0.60,
        habit_type="cognitive",
    ),
]

added = 0
skipped = 0

for h in habits:
    existing = cortex.get(h["id"])
    if existing:
        print(f"  [skip] {h['id']} already exists")
        skipped += 1
        continue

    from wild_igor.igor.memory.models import Memory, MemoryType
    from datetime import datetime, timezone

    mem = Memory(
        id=h["id"],
        narrative=h["narrative"],
        memory_type=MemoryType.PROCEDURAL,
        importance=h["score"],
        inertia=h["score"],
        metadata={
            "trigger": h.get("trigger", ""),
            "habit_type": h.get("habit_type", "cognitive"),
            "parent_id": h.get("parent_id", "CP1"),
            "score": h["score"],
        },
    )
    stored = cortex.store(mem)
    if stored:
        # Wire to parent CP
        parent = h.get("parent_id")
        if parent:
            try:
                cortex.add_interpretive_edge(
                    from_id=parent,
                    to_id=h["id"],
                    direction="semantic",
                    condition_csb=f"trigger:{h.get('trigger','any')}",
                    meaning_payload=h["narrative"][:100],
                    action_pointer=h["id"],
                    weight=h["score"],
                )
                print(f"  [edge] {parent} → {h['id']}")
            except Exception as e:
                print(f"  [edge_err] {e}")
        print(f"  [stored] {h['id']}")
        added += 1
    else:
        print(f"  [err] failed to store {h['id']}")
        skipped += 1

print(f"\nDone. {added} traversal habits stored, {skipped} skipped.")
print("Igor now has 'why?' as an active cognitive habit.")
