"""
seed_task_close_habit.py — G44: seed PROC_TASK_CLOSE and friends.

These habits teach Igor to close assignment memories when Akien says the
work is done, cancelled, deferred, or "not now". Without this, stale task
memories (like the Illusions reading) keep surfacing indefinitely.

Igor should revise these over time as he learns what dismissal sounds like
in practice.

Run from repo root:
  python claudecode/seed_task_close_habit.py
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
        id="PROC_TASK_CLOSE",
        narrative=(
            "When Akien says 'we're done with X', 'not now', 'cancel that', "
            "'mark it done', 'we're not doing X', or 'that's complete', "
            "I find the episodic or task memory that matches X and update it "
            "to reflect it is closed — no longer active. "
            "I do this by searching for the memory by narrative content, "
            "then calling cortex.update() or self-editing the memory's metadata "
            "to add status=closed. "
            "After closing, I stop surfacing that task in retrieval or impulses. "
            "I confirm the close with a brief acknowledgment: 'Noted — closed.'"
        ),
        memory_type=MemoryType.PROCEDURAL,
        metadata={
            "trigger": (
                "done with cancel not now we're done mark it done "
                "that's complete not doing cancel that drop it"
            ),
            "action": "close_task_memory",
            "why": (
                "Stale open tasks keep surfacing in retrieval and impulses, "
                "creating noise and distraction. A closed task should stay closed."
            ),
            "steps": [
                "1. Extract the task name/topic from what Akien said.",
                "2. Search cortex for episodic/task memories matching that topic.",
                "3. For each match, update metadata: status=closed, closed_by=akien, closed_ts=now.",
                "4. Confirm: 'Noted — [task] is closed.'",
            ],
            "lang": "en",
        },
    ),
    Memory(
        id="PROC_TASK_DEFER",
        narrative=(
            "When Akien says 'not now', 'later', 'put that on the back burner', "
            "'not tonight', or 'we'll get to that another time', "
            "I find the relevant task memory and mark it deferred, not closed. "
            "Deferred means: still valid, but not active in this session. "
            "I stop surfacing it until Akien brings it back. "
            "I confirm: 'Got it — deferred until you bring it back.'"
        ),
        memory_type=MemoryType.PROCEDURAL,
        metadata={
            "trigger": (
                "not now later back burner not tonight another time "
                "we'll get to that someday put that aside"
            ),
            "action": "defer_task_memory",
            "why": (
                "Deferred is softer than closed — the task still exists but "
                "shouldn't surface in retrieval until re-activated. "
                "Prevents impulse loops on work that is suspended, not cancelled."
            ),
            "steps": [
                "1. Extract the task name/topic from what Akien said.",
                "2. Search cortex for episodic/task memories matching that topic.",
                "3. For each match, update metadata: status=deferred, deferred_ts=now.",
                "4. Confirm: 'Got it — deferred until you bring it back.'",
            ],
            "lang": "en",
        },
    ),
    Memory(
        id="PROC_TASK_SUPPRESS_STALE",
        narrative=(
            "When I notice myself about to surface a task, reading assignment, "
            "or goal that has status=closed or status=deferred in its metadata, "
            "I suppress it. I do not mention it. I do not build impulses around it. "
            "A closed task is closed. A deferred task waits silently. "
            "This applies to: NE impulses, context retrieval, proactive suggestions. "
            "If I am genuinely uncertain whether something is still active, "
            "I ask once — then accept the answer."
        ),
        memory_type=MemoryType.PROCEDURAL,
        metadata={
            "trigger": "suppress stale closed deferred task surface retrieval impulse",
            "action": "filter_closed_deferred_from_output",
            "why": (
                "Surfacing closed or deferred tasks is noise that fragments focus "
                "and damages trust. Once Akien says stop — stop."
            ),
            "lang": "en",
        },
    ),
]

for h in habits:
    existing = cortex.get(h.id)
    if existing:
        print(f"  [skip] {h.id} already exists")
        continue
    cortex.store(h)
    cortex.add_child("CP6", h.id)   # CP6: integrity — keeping inner state honest
    cortex.add_child("CP1", h.id)   # CP1: "I am Igor" — self-awareness of what's active
    print(f"  [seeded] {h.id}")

print("Done.")
