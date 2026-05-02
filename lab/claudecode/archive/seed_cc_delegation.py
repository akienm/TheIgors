#!/usr/bin/env python3
"""
seed_cc_delegation.py — Seed PROC_USE_CC_FOR_CODE habit (#155).

Seeds Igor with the habit of delegating codebase reasoning to Claude Code
instead of burning OpenRouter turns on reasoning about his own source.

Run once. Safe to re-run (upsert).
Usage: python claudecode/seed_cc_delegation.py
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

from wild_igor.igor.memory.cortex import Cortex
from wild_igor.igor.memory.models import Memory, MemoryType

DB_PATH = Path(os.environ.get(
    "IGOR_DB_PATH",
    Path.home() / ".TheIgors" / "Igor-wild-0001" / "wild-0001.db"
))

cortex = Cortex()

MEMORIES = [
    Memory(
        id="PROC_USE_CC_FOR_CODE",
        narrative=(
            "When reasoning about my own codebase — reading source files, planning edits, "
            "understanding architecture, or debugging my own code — delegate to the hot CC "
            "session via ~/TheIgors/lab/claudecode/hot_cc.sh rather than using an OpenRouter turn. "
            "Write a brief to ~/.TheIgors/Igor-wild-0001/workspace/cc_task.md, then call "
            "run_bash(command='~/TheIgors/lab/claudecode/hot_cc.sh \"$(cat ~/.TheIgors/Igor-wild-0001/workspace/cc_task.md)\"'). "
            "hot_cc.sh maintains a warm session with codebase context and deposits graph nodes "
            "on every answer — each escalation trains the graph so future turns stay local. "
            "Exception: use inner_cc() for quick single-question lookups that don't need live source."
        ),
        memory_type=MemoryType.PROCEDURAL,
        activation_count=0,
        valence=0.7,
        metadata={
            "trigger": "read source edit architecture debug my code codebase",
            "habit_type": "delegation",
            "action": "run_bash",
            "parent_cp": "CP4",
            "github_issue": "155",
            "inertia": "0.5",
        },
    ),
    Memory(
        id="FACTUAL_CC_COST_ADVANTAGE",
        narrative=(
            "Claude Code has a token-caching advantage when reasoning about the TheIgors "
            "codebase: the stable repo context is cached, so repeated reads cost a fraction "
            "of a fresh OpenRouter call. For multi-file architecture reasoning or debugging, "
            "CC is 5-10x cheaper than an OR sonnet turn. OR turns should be reserved for "
            "reasoning about external content (user requests, web results, book extracts) "
            "where the context is novel each time."
        ),
        memory_type=MemoryType.FACTUAL,
        activation_count=0,
        valence=0.6,
        metadata={
            "tags": ["cost", "claude_code", "openrouter", "codebase", "delegation"],
            "github_issue": "155",
            "inertia": "0.4",
        },
    ),
]

for m in MEMORIES:
    cortex.store(m)
    print(f"  seeded {m.id}")

print(f"Done. {len(MEMORIES)} memories seeded.")
