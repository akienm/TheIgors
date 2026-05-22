#!/usr/bin/env python3
"""Seed facia memory + habits for the unified reading tool."""

import os
import sys
from pathlib import Path

REPO = Path(__file__).parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "wild_igor"))

os.environ.setdefault(
    "IGOR_DB_PATH",
    str(Path.home() / ".TheIgors" / "Igor-wild-0001" / "wild-0001.db"),
)

from igor.memory.cortex import Cortex
from igor.memory.models import Memory, MemoryType

cortex = Cortex(Path(os.environ["IGOR_DB_PATH"]))

# ── Facia memory ─────────────────────────────────────────────────────────────

FACIA = Memory(
    id="INTERP_FACIA_READING",
    narrative=(
        "I use reading() to manage my book reading pipeline. "
        "Commands: create_run (batch a set of books), start_run (begin processing), "
        "list_runs (see all runs), run_status (check progress), close_run (seal a run), "
        "read_now (read a specific book interactively), master_index (all books ever read), "
        "run_log (combined slate and processing log for a run), "
        "my_reading (what am I currently reading — self-visibility). "
        "This is my unified reading tool — one tool, two modes: foreground (interactive, "
        "human-requested) and background (batch processing, overnight). "
        "Use when: reading books, checking reading progress, starting a reading batch, "
        "seeing what I've read, managing overnight reading, checking pipeline health."
    ),
    memory_type=MemoryType.INTERPRETIVE,
    source="seed_reading_facia",
    confidence=1.0,
    metadata={
        "facia": True,
        "tool_name": "reading",
        "domain": "tools",
        "registry_entry": True,
    },
)

# ── Habits ───────────────────────────────────────────────────────────────────

FEEDER_HABIT = Memory(
    id="PROC_READING_FEEDER_V2",
    narrative=(
        "Hourly reading feeder: if no active reading run exists, create one from "
        "pending reading_list items and start it in background mode. This keeps the "
        "reading pipeline flowing automatically without human intervention."
    ),
    memory_type=MemoryType.PROCEDURAL,
    source="seed_reading_facia",
    confidence=1.0,
    metadata={
        "trigger": "hourly|reading feeder|feed reading|no active run",
        "code_ref": "tools/reading_tool.py:reading",
        "habit_type": "tool",
        "execution_permissions": ["read_memory", "write_memory"],
    },
)

SELF_CHECK_HABIT = Memory(
    id="PROC_READING_SELF_CHECK",
    narrative=(
        "Periodically check my reading status: active runs, items being processed, "
        "pipeline health. Self-monitoring so I can notice when reading has stalled "
        "or when I should start a new batch. Surface findings to TWM."
    ),
    memory_type=MemoryType.PROCEDURAL,
    source="seed_reading_facia",
    confidence=1.0,
    metadata={
        "trigger": "reading status|what am i reading|reading health|book progress",
        "code_ref": "tools/reading_tool.py:reading",
        "habit_type": "tool",
        "execution_permissions": ["read_memory"],
    },
)

# ── Seed ─────────────────────────────────────────────────────────────────────

for mem in [FACIA, FEEDER_HABIT, SELF_CHECK_HABIT]:
    existing = cortex.get(mem.id)
    if existing:
        print(f"  update: {mem.id}")
    else:
        print(f"  create: {mem.id}")
    cortex.store(mem)

# Wire facia to TOOL_REGISTRY_ROOT
try:
    cortex.add_child("TOOL_REGISTRY_ROOT", "INTERP_FACIA_READING")
    print("  wired INTERP_FACIA_READING → TOOL_REGISTRY_ROOT")
except Exception:
    pass

print(
    "Done. Seeded: INTERP_FACIA_READING, PROC_READING_FEEDER_V2, PROC_READING_SELF_CHECK"
)
