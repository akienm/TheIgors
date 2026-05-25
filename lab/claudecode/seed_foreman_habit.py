"""
seed_foreman_habit.py — Seed PROC_WORKER_FOREMAN and PROC_WHAT_ARE_WE_WORKING_ON.

Ticket: 341 (boredom/idle detector + foreman trigger).

Two habits:

  PROC_WORKER_FOREMAN
      habit_type: tool
      trigger: BG scores this when BOREDOM_DETECTED ACTION_IMPULSE arrives in TWM
      action: calls foreman_scan() tool → launches next worker or reports queue state
      conditions: {"keywords": ["BOREDOM_DETECTED", "check_worker_queue", "foreman_scan"]}

  PROC_WHAT_ARE_WE_WORKING_ON
      habit_type: action
      trigger: "what are we working on" (and variants)
      action: calls check_worker_queue() — returns queue summary inline
      conditions: {"keywords": ["working on", "what are we", "queue", "next ticket"]}

These habits complete the boredom→foreman pipeline:
  BoredomSource → BOREDOM_DETECTED in TWM
  → _drain_action_impulses() picks it up as ACTION_IMPULSE
  → BG scores PROC_WORKER_FOREMAN highest
  → foreman_scan() is called
  → next worker launched (or queue summary returned)

Run from repo root:
  cd ~/TheIgors && source venv/bin/activate
  python3 claudecode/seed_foreman_habit.py [--dry-run]

Requires IGOR_HOME_DB_URL or IGOR_DB_PATH.
"""

import sys
import os
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

os.environ.setdefault(
    "IGOR_DB_PATH",
    str(Path.home() / ".TheIgors" / "Igor-wild-0001" / "wild-0001.db"),
)

from devices.igor.memory.models import Memory, MemoryType
from devices.igor.memory.cortex import Cortex

DRY_RUN = "--dry-run" in sys.argv

db_path = Path(os.environ["IGOR_DB_PATH"])
cortex = Cortex(db_path, instance_id="Igor-wild-0001")

HABIT_IDS = ["PROC_BOREDOM_FOREMAN", "PROC_WHAT_ARE_WE_WORKING_ON"]

habits = [
    # ── Foreman dispatcher — fires on BOREDOM_DETECTED ACTION_IMPULSE ──────
    # (PROC_WORKER_FOREMAN already exists for worker_done→launch_next_worker;
    #  this is the idle-triggered companion habit)
    Memory(
        id="PROC_BOREDOM_FOREMAN",
        narrative=(
            "When I detect that I've been idle for a while (BOREDOM_DETECTED), "
            "I check the worker queue and launch the next pending task. "
            "This is how I keep the work pipeline moving without waiting to be asked. "
            "I use foreman_scan() to check the queue state — if there's pending work, "
            "a worker session is launched automatically."
        ),
        memory_type=MemoryType.PROCEDURAL,
        parent_id="CP1",
        valence=0.7,
        metadata={
            "habit_type": "tool",
            "conditions": {
                "keywords": [
                    "BOREDOM_DETECTED",
                    "check_worker_queue",
                    "foreman_scan",
                    "idle",
                    "nothing pressing",
                ],
            },
            "match_mode": "conditions_first",
            "tool_name": "foreman_scan",
            "habit_score": 0.85,
            "provenance": "seed:341-boredom-foreman",
            "why": (
                "Boredom = signal that attention is available. The right response to "
                "idle time is checking for pending work — not waiting to be asked. "
                "This closes the loop: BoredomSource detects flat arousal → fires "
                "BOREDOM_DETECTED → this habit calls foreman_scan() → next worker "
                "launches if there's something pending."
            ),
        },
    ),
    # ── Queue status on demand ───────────────────────────────────────────────
    Memory(
        id="PROC_WHAT_ARE_WE_WORKING_ON",
        narrative=(
            "When someone asks what we're working on, what's in the queue, "
            "or what's coming next, I check the worker queue and report back. "
            "I give a concise summary of pending, in-progress, and blocked tickets "
            "so Akien can orient quickly without needing to open a terminal."
        ),
        memory_type=MemoryType.PROCEDURAL,
        parent_id="CP1",
        valence=0.6,
        metadata={
            "habit_type": "tool",
            "conditions": {
                "intent": ["question"],
                "keywords": [
                    "working on",
                    "what are we",
                    "queue",
                    "next ticket",
                    "what's next",
                    "pending",
                ],
            },
            "match_mode": "conditions_first",
            "tool_name": "check_worker_queue",
            "habit_score": 0.82,
            "provenance": "seed:341-boredom-foreman",
            "why": (
                "Quick situational awareness query. Returns queue state inline "
                "without launching a worker. Two conditions (intent + keywords) → "
                "specific enough to beat generic question habits."
            ),
        },
    ),
]


def seed():
    print("=== seed_foreman_habit.py — PROC_WORKER_FOREMAN + queue status ===")
    print(f"  mode: {'DRY RUN' if DRY_RUN else 'LIVE'}")
    print()

    for habit in habits:
        existing = cortex.get(habit.id)
        if existing:
            print(f"  [skip] {habit.id} already exists")
            continue
        if DRY_RUN:
            kind = habit.metadata.get("habit_type")
            tool = habit.metadata.get("tool_name", "?")
            print(
                f"  [dry]  would seed {habit.id} ({kind}) → tool={tool}  parent={habit.parent_id}"
            )
            continue
        cortex.store(habit)
        cortex.add_child(habit.parent_id, habit.id)
        kind = habit.metadata.get("habit_type")
        tool = habit.metadata.get("tool_name", "?")
        print(f"  [+]    {habit.id}  ({kind}) tool={tool} → parent={habit.parent_id}")

    if not DRY_RUN:
        print()
        print("=== Validation ===")
        all_ok = True
        for habit in habits:
            node = cortex.get(habit.id)
            if not node:
                print(f"  FAIL  {habit.id} — not found in DB")
                all_ok = False
                continue
            kind = node.metadata.get("habit_type", "?")
            tool = node.metadata.get("tool_name", "?")
            conds = node.metadata.get("conditions", {})
            print(f"  OK    {habit.id}  habit_type={kind}  tool={tool}")
            print(f"        conditions={conds}")
        print()
        if all_ok:
            print("Validation PASS — foreman habits seeded.")
            print()
            print("Boredom→foreman pipeline:")
            print("  BoredomSource (push_sources.py, every 60s)")
            print("  → arousal flat for 20 min → BOREDOM_DETECTED in TWM")
            print("  → _drain_action_impulses() → ACTION_IMPULSE")
            print("  → BG scores PROC_WORKER_FOREMAN → foreman_scan() called")
            print("  → next worker launched (or queue summary if empty)")
        else:
            print("Validation FAIL — check errors above.")
            sys.exit(1)

    print()
    print("Next: restart Igor and let it idle for 20 min.")
    print(
        "Probe: Igor sends 'worker_done:' or queue summary to channel without prompting."
    )


if __name__ == "__main__":
    seed()
