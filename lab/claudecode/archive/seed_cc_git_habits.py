"""
seed_cc_git_habits.py — D095: CC git log, find tickets, list projects habits.

Three habits callable via POST /api/execute_habit:

  CC_GIT_LOG       — last N commits for a project (default: Project:TheIgors)
  CC_FIND_TICKETS  — gh issue list for a project
  CC_LIST_PROJECTS — list all registered projects from lists.projects

Run from repo root:
    python3 ~/TheIgors/lab/claudecode/seed_cc_git_habits.py
"""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
os.environ.setdefault(
    "IGOR_DB_PATH", str(Path.home() / ".TheIgors" / "Igor-wild-0001" / "wild-0001.db")
)

from wild_igor.igor.memory.models import Memory, MemoryType
from wild_igor.igor.memory.cortex import Cortex

DB_PATH = Path(os.environ["IGOR_DB_PATH"])
cortex = Cortex(DB_PATH, instance_id="wild-0001")

habits = [
    Memory(
        id="CC_GIT_LOG",
        narrative=(
            "Claude Code can ask me to show the recent git log for any registered project. "
            "I look up the project path from my memory graph using the project_id, then run "
            "git log and return the last N commits. Default project is Project:TheIgors. "
            "Saves CC from hardcoding repo paths."
        ),
        memory_type=MemoryType.PROCEDURAL,
        metadata={
            "trigger": "git log recent commits project history",
            "habit_type": "action",
            "code_ref": "tools.runner:git_log",
            "default_args": {"project_id": "Project:TheIgors", "n": 20},
            "why": "D095 project-aware CC ops — git log via project memory lookup",
            "inertia": 0.25,
        },
    ),
    Memory(
        id="CC_FIND_TICKETS",
        narrative=(
            "Claude Code can ask me to find GitHub issues for any registered project. "
            "I look up the project path from my memory graph and run gh issue list, "
            "optionally filtering by state (open/closed/all) and a search query. "
            "Default project is Project:TheIgors, default state is open."
        ),
        memory_type=MemoryType.PROCEDURAL,
        metadata={
            "trigger": "find tickets github issues list issues open tickets",
            "habit_type": "action",
            "code_ref": "tools.runner:find_tickets",
            "default_args": {"project_id": "Project:TheIgors", "state": "open"},
            "why": "D095 project-aware CC ops — gh issue list via project memory lookup",
            "inertia": 0.25,
        },
    ),
    Memory(
        id="CC_LIST_PROJECTS",
        narrative=(
            "Claude Code can ask me to list all projects I know about. "
            "I read lists.projects and return each registered project's ID, path, "
            "and GitHub repo. This is how CC discovers what project_ids exist "
            "before calling CC_GIT_LOG or CC_FIND_TICKETS."
        ),
        memory_type=MemoryType.PROCEDURAL,
        metadata={
            "trigger": "list projects what projects do you know registered projects",
            "habit_type": "action",
            "code_ref": "tools.runner:list_projects",
            "why": "D095 project discovery — enumerate lists.projects",
            "inertia": 0.25,
        },
    ),
]

for habit in habits:
    cortex.store(habit)
    print(f"stored habit: {habit.id}")

print("\nverifying:")
for habit in habits:
    mem = cortex.get(habit.id)
    print(f"  {mem.id:22s}  code_ref={mem.metadata['code_ref']}")
