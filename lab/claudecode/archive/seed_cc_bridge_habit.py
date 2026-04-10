"""
seed_cc_bridge_habit.py — PROC_CC_JOIN habit (D105).

Seeds one habit: PROC_CC_JOIN
  Trigger: "cc join the chat"
  Action: checks port 8082; if bridge is not running, advises how to start it;
          announces bridge status to the chat.

Run from repo root:
  python claudecode/seed_cc_bridge_habit.py
"""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.environ.setdefault(
    "IGOR_DB_PATH",
    str(Path.home() / ".TheIgors" / "Igor-wild-0001" / "wild-0001.db"),
)

from wild_igor.igor.memory.models import Memory, MemoryType
from wild_igor.igor.memory.cortex import Cortex

DB_PATH = Path(os.environ["IGOR_DB_PATH"])
cortex = Cortex(DB_PATH, instance_id="wild-0001")

habits = [
    Memory(
        id="PROC_CC_JOIN",
        narrative=(
            "When Akien asks Claude Code to join the chat, I check whether the "
            "Claude bridge service is running on port 8082. "
            "If it is running, I announce that Claude is available in the web UI bridge pane "
            "and remind Akien to click the CC toggle button to open it. "
            "If port 8082 is not responding, I explain that the bridge is not running "
            "and tell Akien to start it with: "
            "python ~/TheIgors/lab/claudecode/claude_bridge.py "
            "or check the @reboot cron entry. "
            "I always respond clearly so Akien knows exactly how to connect to Claude."
        ),
        memory_type=MemoryType.PROCEDURAL,
        metadata={
            "trigger": "cc join the chat claude join claude bridge start cc toggle",
            "habit_type": "action",
            "code_ref": "tools.runner:check_process",
            "action": (
                "import socket; s=socket.socket(); r=s.connect_ex(('localhost',8082)); s.close(); "
                "print('Claude bridge is UP on port 8082 — click CC in the web UI to open the pane.' "
                "if r==0 else "
                "'Claude bridge is NOT running. Start it: python ~/TheIgors/lab/claudecode/claude_bridge.py')"
            ),
            "why": "D105 claude-bridge; lets Akien invoke bridge status by voice",
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

print(f"\nDone. {len(habits)} CC bridge habit(s) seeded.")
