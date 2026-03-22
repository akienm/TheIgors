"""
seed_schema_habit.py — PROC_SCAN_DIR habit (T-habit-schema).

Demo schema-defined habit: iterates files in ctx[dir], detects each file's type,
reports a summary. Executes entirely from its step list — no Python import needed.

Step list:
  1  prim_list_dir   → writes ctx[files] from ctx[dir]
  2  prim_iter_done  → writes ctx[done]='true'/'false'
  3  prim_branch     → if done=='true' goto 6, else goto 4
  4  prim_iter_next  → pops ctx[current_file], updates ctx[files]
  5  prim_type_detect → writes ctx[file_type] for ctx[current_file]
  (implicit goto back to step 2 via step number sequence... but we need explicit goto)
  ... actually we use prim_goto at step 5.5 to loop:
  5  prim_type_detect
  6  prim_goto goto=2       (loop back to done-check)
  7  prim_set key=result value="scan complete"

Corrected step numbering:
  1  prim_list_dir
  2  prim_iter_done
  3  prim_branch if done=='true' goto_true=7, goto_false=4
  4  prim_iter_next
  5  prim_type_detect
  6  prim_goto goto=2
  7  prim_set key=result value="scan complete"

Run from repo root:
  python claudecode/seed_schema_habit.py
"""

import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.environ.setdefault(
    "IGOR_DB_PATH",
    str(Path.home() / ".TheIgors" / "igor_wild_0001" / "wild-0001.db"),
)

from wild_igor.igor.memory.models import Memory, MemoryType
from wild_igor.igor.memory.cortex import Cortex

DB_PATH = Path(os.environ["IGOR_DB_PATH"])
cortex = Cortex(DB_PATH, instance_id="igor_wild_0001")

habits = [
    Memory(
        id="PROC_SCAN_DIR",
        narrative=(
            "When Akien asks me to scan a directory or list its file types — "
            "'scan dir', 'list file types', 'what files are in', 'scan files' — "
            "I run the PROC_SCAN_DIR schema habit, which iterates every file in "
            "the target directory and reports its detected type (python, markdown, "
            "json, binary, etc.). The dir is taken from ctx[dir] or user input."
        ),
        memory_type=MemoryType.PROCEDURAL,
        parent_id="CP1",
        metadata={
            "habit_type": "schema",
            "trigger": (
                "scan dir list file types what files scan files "
                "directory contents file inventory scan directory"
            ),
            "ctx_init": {"dir": "~/TheIgors/wild_igor/igor/tools"},
            "steps": [
                {"step": 1, "do": "prim_list_dir"},
                {"step": 2, "do": "prim_iter_done"},
                {
                    "step": 3,
                    "do": "prim_branch",
                    "if": {"key": "done", "op": "==", "value": "true"},
                    "goto_true": 7,
                    "goto_false": 4,
                },
                {"step": 4, "do": "prim_iter_next"},
                {"step": 5, "do": "prim_type_detect"},
                {"step": 6, "do": "prim_goto", "goto": 2},
                {
                    "step": 7,
                    "do": "prim_set",
                    "key": "result",
                    "value": "scan complete",
                },
            ],
            "pattern": "schema_ops",
            "why": (
                "T-habit-schema #330: First schema-defined habit demonstrating "
                "step-list execution with iteration loop (list→iter→detect→goto). "
                "Executes without any Python import — purely from step data."
            ),
            "inertia": 0.10,
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
    print(f"  [seeded] {h.id}  (schema) → parent=CP1")

print("Done. PROC_SCAN_DIR schema habit seeded.")
