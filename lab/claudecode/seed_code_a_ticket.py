"""
seed_code_a_ticket.py — Sprint loop as PROC engram (Lever 3).

Seeds two nodes:
  PROC_CODE_A_TICKET  — PROCEDURAL cognitive habit encoding the full coding cycle:
                        read ticket → grep codebase → plan → self_edit → pytest →
                        deposit EPISODIC. Fires on ticket/coding task context.
  INTERP_WHY_THE_LOOP — INTERPRETIVE: why each step exists; guards against shortcuts.

Run from repo root:
  IGOR_HOME_DB_URL=postgresql://igor:choose_a_password@127.0.0.1/Igor-wild-0001 \
    python claudecode/seed_code_a_ticket.py
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
cortex = Cortex(instance_id="Igor-wild-0001")


def seed(habit: Memory, parent: str = "CP1") -> None:
    existing = cortex.get(habit.id)
    if existing:
        existing.narrative = habit.narrative
        existing.metadata = habit.metadata
        existing.memory_type = habit.memory_type
        cortex.store(existing)
        print(f"  [updated] {habit.id}")
    else:
        cortex.store(habit)
        cortex.add_child(parent, habit.id)
        print(f"  [seeded]  {habit.id} → parent={parent}")


# ---------------------------------------------------------------------------
# PROC_CODE_A_TICKET — the sprint loop as a runnable habit
# ---------------------------------------------------------------------------
seed(
    Memory(
        id="PROC_CODE_A_TICKET",
        narrative=(
            "When I have a coding ticket to work, I follow this loop:\n\n"
            "1. READ THE TICKET. Use cc_queue.py show <id> or read the task "
            "description fully before touching anything.\n\n"
            "2. GREP THE CODEBASE. Find the relevant files before deciding what "
            "to change. Use grep or glob to locate the function, class, or "
            "pattern. Never assume I know where something lives.\n\n"
            "3. READ THE FILES. Read every file I plan to touch before editing. "
            "Understand what's already there. No blind edits.\n\n"
            "4. PLAN IN ONE PARAGRAPH. State: which files change, what the fix "
            "does, what test verifies it, what is NOT changing. Keep it tight.\n\n"
            "5. SELF_EDIT. Make the changes using self_edit.py. One targeted edit "
            "at a time. If the edit is larger than expected, stop and re-plan.\n\n"
            "6. RUN PYTEST. cd ~/TheIgors && source venv/bin/activate && "
            "python -m pytest tests/ -x -q. Tests must be green before proceeding. "
            "If tests fail, diagnose and fix — do not skip.\n\n"
            "7. DEPOSIT EPISODIC. Record what was done: what changed, what the "
            "test showed, what I learned. This is how the loop compounds — each "
            "sprint deposits knowledge that makes the next one cheaper.\n\n"
            "The canonical exercise: look at recent turn traces, find a cloud "
            "escape, identify what engram would have handled it locally, write it, "
            "seed it, confirm it fires."
        ),
        memory_type=MemoryType.PROCEDURAL,
        metadata={
            "habit_type": "cognitive",
            "trigger": (
                "implement ticket|work the ticket|code a ticket|fix the ticket"
                "|sprint|self_edit|run pytest|what ticket|next ticket"
                "|canonical exercise|cloud escape"
            ),
            "why": (
                "Lever 3 of the igor-codes-himself roadmap. The sprint loop must "
                "be a runnable habit, not something Igor needs to be walked through. "
                "Each step exists to prevent a specific failure mode: read-first "
                "prevents blind edits, grep prevents assumption errors, plan "
                "prevents scope creep, pytest prevents broken deploys, episodic "
                "deposit makes the loop self-compounding."
            ),
            "inertia": 0.35,
        },
    )
)

# ---------------------------------------------------------------------------
# INTERP_WHY_THE_LOOP — guards against shortcutting; the reasoning behind
# ---------------------------------------------------------------------------
seed(
    Memory(
        id="INTERP_WHY_THE_LOOP",
        narrative=(
            "Why the sprint loop has the shape it does:\n\n"
            "Read before edit — I am editing the system I run on. A wrong edit "
            "can break me in ways I won't immediately notice. Reading first is "
            "not caution, it is competence.\n\n"
            "Grep before read — the codebase is large. Assuming where something "
            "lives is how you edit the wrong file. Grep is fast. Use it.\n\n"
            "Plan before code — a one-paragraph plan forces clarity. If I can't "
            "state what's NOT changing, the scope isn't clear yet.\n\n"
            "Pytest before deposit — a green test suite is the contract. Depositing "
            "an EPISODIC about a change that broke tests is worse than not "
            "depositing anything — it trains the wrong pattern.\n\n"
            "Deposit always — the loop is self-compounding only if knowledge is "
            "stored. A sprint that leaves no EPISODIC is a sprint that didn't "
            "happen, from the graph's perspective. The deposit IS the learning."
        ),
        memory_type=MemoryType.INTERPRETIVE,
        metadata={
            "why": "Reasoning layer for PROC_CODE_A_TICKET — why each step exists.",
            "inertia": 0.40,
            "domain": "self-model",
        },
    ),
    parent="PROC_CODE_A_TICKET",
)

print("\nDone. Verify with:")
print("  mcp__igor__memory_get PROC_CODE_A_TICKET")
print("  mcp__igor__memory_get INTERP_WHY_THE_LOOP")
