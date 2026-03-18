#!/usr/bin/env python3
"""
seed_implement_workflow.py — Seed PROC_IMPLEMENT_WORKFLOW memory (#95).

Seeds Igor with the implementation workflow pattern so he knows the steps
when /implement #N is invoked.

Run once. Safe to re-run.
Usage: python claudecode/seed_implement_workflow.py
"""
import sys
from pathlib import Path

REPO = Path(__file__).parent.parent
sys.path.insert(0, str(REPO))

import os
env_path = Path.home() / ".TheIgors" / "igor_wild_0001" / ".env"
if env_path.exists():
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, _, v = line.partition("=")
            os.environ.setdefault(k.strip(), v.strip())

from wild_igor.igor.memory.cortex import Cortex
from wild_igor.igor.memory.models import Memory, MemoryType

DB_PATH = Path(os.environ.get(
    "IGOR_DB_PATH",
    Path.home() / ".TheIgors" / "igor_wild_0001" / "wild-0001.db"
))

cortex = Cortex(DB_PATH)

MEMORIES = [
    Memory(
        id="PROC_IMPLEMENT_WORKFLOW",
        narrative=(
            "When /implement #N is invoked: (1) read the ticket carefully, "
            "(2) state a concise plan — which files, what changes, (3) ask Akien to confirm, "
            "(4) on confirmation use patch_source_file for each change, "
            "(5) run run_syntax_check on every modified file, "
            "(6) call close_work_order with a resolution summary, "
            "(7) report completion. Never skip the confirmation step."
        ),
        memory_type=MemoryType.PROCEDURAL,
        activation_count=0,
        valence=0.8,
        metadata={
            "trigger": "implement",
            "habit_type": "workflow",
            "action": "get_work_order|patch_source_file|run_syntax_check|close_work_order",
            "parent_cp": "CP4",
            "github_issue": "95",
            "inertia": "0.5",
        },
    ),
    Memory(
        id="FACTUAL_IMPLEMENT_TOOLS",
        narrative=(
            "Tools available for self-implementation: get_work_order(N) fetches ticket details; "
            "patch_source_file(path, old, new, reason) edits source files; "
            "run_syntax_check(path) validates Python syntax; "
            "close_work_order(N, resolution) marks the GitHub issue done. "
            "All live in wild_igor/igor/tools/. Never edit brainstem/ without arbiter approval."
        ),
        memory_type=MemoryType.FACTUAL,
        activation_count=0,
        valence=0.6,
        metadata={
            "tags": ["self_edit", "tools", "implementation", "github"],
            "github_issue": "95",
            "inertia": "0.45",
        },
    ),
]

for m in MEMORIES:
    cortex.store(m)
    print(f"  seeded {m.id}")

print(f"Done. {len(MEMORIES)} memories seeded.")
