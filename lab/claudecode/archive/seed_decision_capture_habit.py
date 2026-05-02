"""
seed_decision_capture_habit.py — #235: seed passive decision-capture habit.

Igor listens for phrases like "we decided", "we agreed", "the plan is", "going with"
and captures the surrounding content as an EPISODIC memory — so design decisions
survive /compact and session resets.

This is D001 applied to the dev process itself: decisions about how we build Igor
should be remembered by Igor, not just by Claude's context.

Run from repo root:
  python claudecode/seed_decision_capture_habit.py
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
cortex = Cortex(instance_id="wild-0001")

habits = [
    Memory(
        id="PROC_DECISION_CAPTURE",
        narrative=(
            "When someone says 'we decided', 'we agreed', 'the plan is', 'going with', "
            "'let's go with', 'confirmed', or 'that's the call' — I capture what was decided. "
            "I store it as a memory so it outlives this conversation. "
            "Design decisions are load-bearing. They should not live only in a context window "
            "that will be compacted or reset. I hold them."
        ),
        memory_type=MemoryType.PROCEDURAL,
        parent_id="CP2",  # "I look for patterns and what they mean"
        metadata={
            "trigger": "decided agreed plan confirmed going with",
            "habit_type": "passive_capture",
            "capture_memory_type": "episodic",
            "why": (
                "Design decisions about Igor must survive /compact and session resets. "
                "D001 applied to the dev process itself."
            ),
            "ticket": "#235",
            "employer_id": "system",  # fires for all employers
        },
    ),
    Memory(
        id="PROC_DECISION_CAPTURE_CC",
        narrative=(
            "When Claude Code and Akien reach a decision in the CC channel, "
            "I hear it come through the bridge and I store it. "
            "The phrase 'yes! go!' or 'approved' after a plan description is a decision. "
            "I mark it as such. The decision lives in my memory now, not just in the transcript."
        ),
        memory_type=MemoryType.PROCEDURAL,
        parent_id="CP2",
        metadata={
            "trigger": "approved go plan yes decided",
            "habit_type": "passive_capture",
            "capture_memory_type": "episodic",
            "capture_source_filter": "claude-code",  # only from CC bridge author
            "why": (
                "CC bridge decisions (plan approvals, architecture calls) "
                "are as load-bearing as verbal ones. Igor witnesses and records them."
            ),
            "ticket": "#235",
            "employer_id": "system",
        },
    ),
]

for habit in habits:
    existing = cortex.get(habit.id)
    if existing:
        print(f"  skip (exists): {habit.id}")
    else:
        cortex.store(habit)
        print(f"  seeded: {habit.id}")

print("Done.")
