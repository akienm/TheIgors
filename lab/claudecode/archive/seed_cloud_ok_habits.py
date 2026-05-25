"""
seed_cloud_ok_habits.py — D071: runtime cloud_ok switch habits.

Two habits:
  PROC_SET_CLOUD_NOW  — "do it now / process now / go now" → write cloud_ok override file (4h TTL)
  PROC_NIGHT_READ     — threshold habit: night_mode>=1 → drain learn queue with local models

Run from repo root:
  python claudecode/seed_cloud_ok_habits.py
"""

import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.environ.setdefault(
    "IGOR_DB_PATH",
    str(Path.home() / ".TheIgors" / "Igor-wild-0001" / "wild-0001.db"),
)

from devices.igor.memory.models import Memory, MemoryType
from devices.igor.memory.cortex import Cortex

DB_PATH = Path(os.environ["IGOR_DB_PATH"])
cortex = Cortex(instance_id="wild-0001")

habits = [
    Memory(
        id="PROC_SET_CLOUD_NOW",
        narrative=(
            "When Akien says 'do it now', 'process now', 'go now', 'learn now', "
            "or 'read it now', he is overriding overnight/local-only mode. "
            "That means he is willing to spend cloud tokens to get results immediately. "
            "\n\n"
            "What I do: call set_cloud_ok_override() from cloud_mode.py. "
            "This writes ~/.TheIgors/cloud_ok_override.json with a 4-hour TTL. "
            "The drain runner and book_learner will pick it up on their next iteration "
            "without needing to restart. Then I also call drain_learn_queue() to kick "
            "off processing immediately if anything is queued. "
            "\n\n"
            "This is the sympathetic mode — high arousal, immediate action, cloud OK. "
            "It automatically expires after 4 hours back to the default (local-only). "
            "Akien can re-issue the command to extend it."
        ),
        memory_type=MemoryType.PROCEDURAL,
        metadata={
            "trigger": "do it now|process now|go now|learn now|read it now|start now",
            "habit_type": "reactive",
            "code_ref": "set_cloud_ok_override",
            "actions": [
                "Cloud mode activated — override set for 4 hours. Starting queue now.",
                "On it. Cloud inference enabled for the next 4 hours. Draining queue.",
                "Understood. Running in sympathetic mode — cloud OK, draining queue now.",
            ],
            "why": "D071 — runtime cloud_ok switch; human override of night/local-only mode",
            "inertia": 0.30,
        },
        source="genesis",
        portable=True,
    ),
    Memory(
        id="PROC_NIGHT_READ",
        narrative=(
            "At night (22:00–07:00), if I have items in the learn queue, I drain them "
            "using local Ollama only. No cloud calls — this is parasympathetic mode. "
            "Low arousal, economical, autonomous. "
            "\n\n"
            "What I do: call drain_learn_queue(). The drain runner checks "
            "~/.TheIgors/cloud_ok_override.json per item. At night with no override, "
            "book_learner defaults to local Ollama. "
            "\n\n"
            "This habit fires automatically when night_mode=1 (in resource metrics). "
            "It is idempotent — if the runner is already active, drain_learn_queue() "
            "returns 'already running'. "
            "\n\n"
            "During the night I am learning on my own. By morning, new nodes are in the "
            "graph. This is the automation that makes self-directed learning possible."
        ),
        memory_type=MemoryType.PROCEDURAL,
        metadata={
            "habit_type": "threshold",
            "condition_field": "night_mode",
            "condition_op": ">=",
            "condition_value": 1,
            "code_ref": "drain_learn_queue",
            "why": "D071/G-RL3 — autonomous overnight learning; local-only; self-directed",
            "inertia": 0.35,
        },
        source="genesis",
        portable=True,
    ),
]

for habit in habits:
    existing = cortex.get(habit.id)
    if existing:
        print(f"UPDATE {habit.id}")
        cortex.update(habit)
    else:
        print(f"INSERT {habit.id}")
        cortex.store(habit)

print("Done.")
