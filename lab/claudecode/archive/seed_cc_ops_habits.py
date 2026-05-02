"""
seed_cc_ops_habits.py — CC direct-execution operational habits (D094).

Three habits callable via POST /api/execute_habit that let Claude Code
delegate common ops to Igor instead of running bash directly:

  CC_CHECK_PROCESS — check if a named process is running (pgrep)
  CC_RUN_BASH      — run a bash command and return output
  CC_RUN_PYTHON    — run a Python snippet and return output

Uses CC_ prefix to avoid colliding with genesis PROC_RUN_BASH / PROC_RUN_PYTHON.
All three are multi-arg tools; execute_habit's explicit args dict handles
dispatch cleanly (no 0/1-arg limitation).

Run from repo root:
  python claudecode/seed_cc_ops_habits.py
"""

import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.environ.setdefault(
    "IGOR_DB_PATH", str(Path.home() / ".TheIgors" / "Igor-wild-0001" / "wild-0001.db")
)

from wild_igor.igor.memory.models import Memory, MemoryType
from wild_igor.igor.memory.cortex import Cortex

DB_PATH = Path(os.environ["IGOR_DB_PATH"])
cortex = Cortex(instance_id="wild-0001")

habits = [
    # CC_CHECK_PROCESS
    Memory(
        id="CC_CHECK_PROCESS",
        narrative=(
            "Claude Code can ask me to check whether any named process is running. "
            "I use pgrep to search by name pattern and return the running status, "
            "PID list, and matching process lines, so CC can verify Igor, Ollama, "
            "KoboldCpp, or any background job is alive without running bash directly."
        ),
        memory_type=MemoryType.PROCEDURAL,
        metadata={
            "trigger": "is igor running is process running check process pgrep",
            "habit_type": "action",
            "code_ref": "tools.runner:check_process",
            "why": "D094 CC direct habit execution; replaces pgrep bash calls",
            "inertia": 0.25,
        },
    ),
    # CC_RUN_BASH — CC-facing; genesis PROC_RUN_BASH narrative stays untouched
    Memory(
        id="CC_RUN_BASH",
        narrative=(
            "Claude Code can delegate shell commands to me via this habit. "
            "The command runs in my workspace directory with a configurable timeout "
            "and all output is captured and returned. Every call lands in the "
            "cc_session log so we have a forensic record of what was run and when."
        ),
        memory_type=MemoryType.PROCEDURAL,
        metadata={
            "trigger": "cc delegate run bash command shell execute",
            "habit_type": "action",
            "code_ref": "tools.runner:run_bash",
            "why": "D094 CC direct habit execution; forensic-logged shell delegation",
            "inertia": 0.25,
        },
    ),
    # CC_RUN_PYTHON — CC-facing; genesis PROC_RUN_PYTHON narrative stays untouched
    Memory(
        id="CC_RUN_PYTHON",
        narrative=(
            "Claude Code can delegate Python snippets to me via this habit. "
            "The code runs in my workspace directory using my interpreter and all "
            "output is captured and returned. Every call lands in the cc_session log."
        ),
        memory_type=MemoryType.PROCEDURAL,
        metadata={
            "trigger": "cc delegate run python code snippet execute python",
            "habit_type": "action",
            "code_ref": "tools.runner:run_python",
            "why": "D094 CC direct habit execution; forensic-logged python delegation",
            "inertia": 0.25,
        },
    ),
]

for mem in habits:
    existing = cortex.get(mem.id)
    if existing:
        cortex.store(mem)
        print(f"  updated  {mem.id}")
    else:
        cortex.store(mem)
        print(f"  seeded   {mem.id}")

print(f"\nDone. {len(habits)} CC ops habits seeded.")
