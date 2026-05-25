#!/usr/bin/env python3
"""
seed_behavioral_habits.py — Seed observed behavioral habits into Igor's DB (#107).

Seeds:
  PROC_HABIT_BUDGET_CHECK     — trigger "budget" or "cost" → check budget tool first
  PROC_HABIT_RING_SUMMARY     — trigger "what did you do" → summarize recent ring narratives
  PROC_HABIT_WORK_ORDER_DONE  — trigger "work order complete" → write ring entry + update TWM

Run once. Safe to re-run — cortex.store() is idempotent on existing IDs.
Usage: python claudecode/seed_behavioral_habits.py
"""
import sys
from pathlib import Path

REPO = Path(__file__).parent.parent
sys.path.insert(0, str(REPO))

import os
env_path = Path.home() / ".TheIgors" / "Igor-wild-0001" / ".env"
if env_path.exists():
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, _, v = line.partition("=")
            os.environ.setdefault(k.strip(), v.strip())

from devices.igor.memory.cortex import Cortex
from devices.igor.memory.models import Memory, MemoryType

DB_PATH = Path(os.environ.get(
    "IGOR_DB_PATH",
    Path.home() / ".TheIgors" / "Igor-wild-0001" / "wild-0001.db"
))

cortex = Cortex()

HABITS = [
    Memory(
        id="PROC_HABIT_BUDGET_CHECK",
        narrative=(
            "When budget or cost is asked about, check the budget tool first "
            "before reasoning about it. Gives grounded numbers, not estimates."
        ),
        memory_type=MemoryType.PROCEDURAL,
        activation_count=0,
        valence=0.6,
        metadata={
            "trigger": "budget",
            "habit_type": "response",
            "action": "call_tool:get_budget_status",
            "parent_cp": "CP4",
            "inertia": "0.4",
        },
    ),
    Memory(
        id="PROC_HABIT_RING_SUMMARY",
        narrative=(
            "When asked 'what did you do' or 'what have you done', "
            "pull recent ring narratives and summarize them concisely. "
            "Self-report from actual activity log, not from memory of intent."
        ),
        memory_type=MemoryType.PROCEDURAL,
        activation_count=0,
        valence=0.5,
        metadata={
            "trigger": "what did you do",
            "habit_type": "response",
            "action": "summarize_ring_narratives",
            "parent_cp": "CP2",
            "inertia": "0.4",
        },
    ),
    Memory(
        id="PROC_HABIT_WORK_ORDER_DONE",
        narrative=(
            "When a work order or task is marked complete, write a ring entry "
            "and update the TWM with completion status. Makes progress visible "
            "and keeps warm context accurate."
        ),
        memory_type=MemoryType.PROCEDURAL,
        activation_count=0,
        valence=0.7,
        metadata={
            "trigger": "work order complete",
            "habit_type": "response",
            "action": "write_ring:work_order_complete|update_twm:task_status",
            "parent_cp": "CP2",
            "inertia": "0.45",
        },
    ),
]

for habit in HABITS:
    cortex.store(habit)
    print(f"  seeded {habit.id}")

print(f"Done. {len(HABITS)} behavioral habits seeded.")
