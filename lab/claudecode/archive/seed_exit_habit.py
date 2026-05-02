"""
seed_exit_habit.py — PROC_EXIT_IGOR: clean shutdown habit.

Triggers Igor to write exit.flag (code 0) when asked to stop/exit/shutdown.
The bash/PS wrapper does NOT restart on exit code 0.

Run from repo root:
  python claudecode/seed_exit_habit.py
"""

import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "wild_igor"))

# Allow override via IGOR_DB_URL (Postgres) or IGOR_DB_PATH (SQLite)
os.environ.setdefault(
    "IGOR_DB_PATH", str(Path.home() / ".TheIgors" / "Igor-wild-0001" / "wild-0001.db")
)

from igor.memory.models import Memory, MemoryType
from igor.memory.cortex import Cortex

DB_PATH = Path(os.environ["IGOR_DB_PATH"])
cortex = Cortex(instance_id="wild-0001")

habit = Memory(
    id="PROC_EXIT_IGOR",
    narrative=(
        "When Akien says 'exit igor', 'shutdown igor', 'shut yourself down', "
        "'halt', 'stop yourself', 'quit igor', or 'exit cleanly', I call exit_self() "
        "to write the exit flag. The main loop picks it up and exits with code 0 — "
        "the wrapper does not restart. I confirm: 'Shutting down cleanly.'"
    ),
    memory_type=MemoryType.PROCEDURAL,
    metadata={
        "trigger": (
            "exit igor shutdown igor shut yourself down halt "
            "stop yourself exit cleanly quit igor terminate igor"
        ),
        "habit_type": "action",
        "code_ref": "tools.runner.exit_self",
        "action": "exit_self",
        "why": (
            "Igor needs a clean way to stop that doesn't trigger a restart. "
            "exit.flag + code 0 = stop. restart.flag + code 42 = restart. "
            "The bash/PS loop wrappers only restart on code 42."
        ),
        "lang": "en",
    },
)

existing = cortex.get("PROC_EXIT_IGOR")
if existing:
    print("PROC_EXIT_IGOR already exists — updating.")
    habit.timestamp = existing.timestamp
    habit.activation_count = existing.activation_count

cortex.store(habit)
verify = cortex.get("PROC_EXIT_IGOR")
if verify:
    print(f"OK: PROC_EXIT_IGOR seeded ({verify.memory_type.value})")
    print(f"  trigger: {verify.metadata.get('trigger', '')[:80]}")
else:
    print("ERROR: failed to retrieve after store")
