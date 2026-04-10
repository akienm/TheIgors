"""
seed_os_primitives.py — 6 OS primitive habits (T-os-primitives).

Each is an action habit whose code_ref points to a tool in os_primitives.py.
All have 0 required args — they read inputs from and write outputs to the
active traversal context.

Iteration pattern (compose these habits into a chain):
  1. Set ctx[dir] → call PRIM_LIST_DIR    → ctx[files] populated
  2. Loop:
       Call PRIM_ITER_DONE → ctx[done]
       If done=true: exit loop
       Call PRIM_ITER_NEXT → ctx[current_file]
       Call PRIM_TYPE_DETECT / PRIM_FILE_META / PRIM_READ_HEAD as needed

Run from repo root:
  python claudecode/seed_os_primitives.py
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
        id="PRIM_LIST_DIR",
        narrative=(
            "List the files in the directory stored in traversal context key 'dir'. "
            "Writes a JSON list of absolute file paths to context key 'files', sorted. "
            "Use this as the first step of any habit chain that iterates over files."
        ),
        memory_type=MemoryType.PROCEDURAL,
        metadata={
            "habit_type": "tool",
            "trigger": "",
            "code_ref": "tools/os_primitives.py:prim_list_dir",
            "pattern": "os_primitives",
            "why": "T-os-primitives: substrate for habit-chain file iteration loops. "
            "No trigger — called by schema step list only, never by BG scoring.",
            "inertia": 0.20,
        },
    ),
    Memory(
        id="PRIM_FILE_META",
        narrative=(
            "Get the modification time and size of the file at traversal context key "
            "'current_file'. Writes ISO timestamp to 'file_mtime' and byte count to "
            "'file_size'. Use after PRIM_ITER_NEXT when file metadata is needed."
        ),
        memory_type=MemoryType.PROCEDURAL,
        metadata={
            "habit_type": "tool",
            "trigger": "",
            "code_ref": "tools/os_primitives.py:prim_file_meta",
            "pattern": "os_primitives",
            "why": "T-os-primitives: reads mtime+size for the current iteration file. "
            "No trigger — schema step only.",
            "inertia": 0.20,
        },
    ),
    Memory(
        id="PRIM_READ_HEAD",
        narrative=(
            "Read the first N lines of the file at traversal context key 'current_file'. "
            "N comes from context key 'read_head_lines' (default 40). "
            "Writes the text to context key 'content'. "
            "This is how any habit chain reads file content without loading the whole file."
        ),
        memory_type=MemoryType.PROCEDURAL,
        metadata={
            "habit_type": "tool",
            "trigger": "",
            "code_ref": "tools/os_primitives.py:prim_read_head",
            "pattern": "os_primitives",
            "why": "T-os-primitives: safe head-read. No trigger — schema step only.",
            "inertia": 0.20,
        },
    ),
    Memory(
        id="PRIM_TYPE_DETECT",
        narrative=(
            "Detect the file type of the file at traversal context key 'current_file'. "
            "Uses extension mapping first, then magic-byte sniff for unknown types. "
            "Writes the type string (e.g. 'python', 'markdown', 'binary') to 'file_type'. "
            "Use before PRIM_READ_HEAD to decide whether reading makes sense."
        ),
        memory_type=MemoryType.PROCEDURAL,
        metadata={
            "habit_type": "tool",
            "trigger": "",
            "code_ref": "tools/os_primitives.py:prim_type_detect",
            "pattern": "os_primitives",
            "why": "T-os-primitives: guards PRIM_READ_HEAD from binary files. "
            "No trigger — schema step only.",
            "inertia": 0.20,
        },
    ),
    Memory(
        id="PRIM_ITER_NEXT",
        narrative=(
            "Advance the iteration: pop the first path from traversal context 'files' "
            "into 'current_file', and update 'files' with the remainder. "
            "Call this at the start of each loop body. "
            "Always check PRIM_ITER_DONE first to avoid calling on an empty list."
        ),
        memory_type=MemoryType.PROCEDURAL,
        metadata={
            "habit_type": "tool",
            "trigger": "",
            "code_ref": "tools/os_primitives.py:prim_iter_next",
            "pattern": "os_primitives",
            "why": "T-os-primitives: iteration cursor advance. No trigger — schema step only.",
            "inertia": 0.20,
        },
    ),
    Memory(
        id="PRIM_ITER_DONE",
        narrative=(
            "Check whether the file iteration is complete: reads 'files' from traversal "
            "context and writes 'done'='true' if the list is empty, 'false' otherwise. "
            "Call this before PRIM_ITER_NEXT on each loop iteration. "
            "When done=true, the habit chain should exit or move to its next phase."
        ),
        memory_type=MemoryType.PROCEDURAL,
        metadata={
            "habit_type": "tool",
            "trigger": "",
            "code_ref": "tools/os_primitives.py:prim_iter_done",
            "pattern": "os_primitives",
            "why": "T-os-primitives: loop guard. No trigger — schema step only.",
            "inertia": 0.20,
        },
    ),
    Memory(
        id="PRIM_TWM_READ",
        narrative=(
            "Read active (non-integrated) TWM observations and write a formatted summary "
            "to traversal context key 'twm_items' (salience|source|content per line, "
            "sorted by salience descending) and item count to 'twm_count'. "
            "Use as the tool step in any habit chain that needs to inspect current "
            "cognitive stew — stew readout, affect check, interoception patterns."
        ),
        memory_type=MemoryType.PROCEDURAL,
        metadata={
            "habit_type": "tool",
            "trigger": "",
            "code_ref": "tools/os_primitives.py:prim_twm_read",
            "pattern": "os_primitives",
            "why": (
                "T-wondering-catalog: substrate for PROC_STEW_READOUT and PROC_AFFECT_CHECK. "
                "No trigger — schema step only or called by reactive habits via code_ref."
            ),
            "inertia": 0.20,
        },
    ),
]

for h in habits:
    existing = cortex.get(h.id)
    if existing:
        existing.metadata = h.metadata
        existing.narrative = h.narrative
        cortex.store(existing)
        print(f"  [updated] {h.id}")
    else:
        cortex.store(h)
        cortex.add_child("CP1", h.id)
        print(f"  [seeded] {h.id}  (tool) → parent=CP1")

print("Done. 7 OS primitive habits seeded.")
