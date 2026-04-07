"""
seed_coding_sprint_habit.py — PROC_CODING_SPRINT habit (T-programming-engrams).

Seeds a cognitive habit that fires when Igor's TWM contains a GOAL_READY signal.
The habit calls run_coding_sprint() (ops.py), which reads ACTIVE_GOAL + goal memory
details and posts a structured coding prompt to the channel for LLM pickup.

D300: TWM is the inter-subsystem channel. goal_continuation step 3 writes
GOAL_READY to TWM → PROC_CODING_SPRINT fires reactively → run_coding_sprint()
posts prompt → LLM executes sprint.

Run once after deploying:
  IGOR_HOME_DB_URL=postgresql://igor:choose_a_password@127.0.0.1/Igor-wild-0001 \\
    python3 claudecode/seed_coding_sprint_habit.py

Safe to re-run — upserts on conflict.
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.environ.setdefault(
    "IGOR_DB_PATH",
    str(Path.home() / ".TheIgors" / "Igor-wild-0001" / "wild-0001.db"),
)
DB_URL = os.environ.get(
    "IGOR_HOME_DB_URL",
    "postgresql://igor:choose_a_password@127.0.0.1/Igor-wild-0001",
)
os.environ["IGOR_HOME_DB_URL"] = DB_URL

HABIT = {
    "id": "PROC_CODING_SPRINT",
    "narrative": (
        "When my TWM contains a GOAL_READY signal, I fire a coding sprint. "
        "I call run_coding_sprint(), which reads my current ACTIVE_GOAL and active "
        "GOAL memory details, then posts a structured coding prompt to the channel "
        "so the LLM can take over and implement the goal. After posting, the "
        "GOAL_READY signal is evicted from TWM — it has been consumed. "
        "This is the D300 reactive cascade: goal_continuation step 3 writes "
        "GOAL_READY → I fire → prompt posted → LLM sprints."
    ),
    "memory_type": "PROCEDURAL",
    "source": "seed",
    "confidence": 1.0,
    "context_of_encoding": "T-programming-engrams — seed_coding_sprint_habit 2026-04-01",
    "metadata": {
        "habit_type": "cognitive",
        "code_ref": "ops:run_coding_sprint",
        "twm_trigger": "GOAL_READY",
        "match_mode": "trigger_only",
        "proc_name": "PROC_CODING_SPRINT",
        "inertia": 0.3,
        "why": (
            "T-programming-engrams D300: wires GOAL_READY TWM signal to coding "
            "sprint execution. First step of the programming cascade: "
            "GOAL_ADOPTED → (goal_continuation 0-3) → GOAL_READY in TWM → "
            "PROC_CODING_SPRINT fires → implementation prompt posted → LLM sprints."
        ),
    },
}


def seed_pg(habit: dict) -> None:
    import psycopg2

    conn = psycopg2.connect(DB_URL)
    cur = conn.cursor()
    now = datetime.now().isoformat()
    cur.execute(
        """
        INSERT INTO memories
            (id, narrative, memory_type, source, confidence,
             context_of_encoding, timestamp, updated_at,
             metadata, portable, scope)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, 1, 'class')
        ON CONFLICT (id) DO UPDATE SET
            narrative  = EXCLUDED.narrative,
            metadata   = EXCLUDED.metadata,
            updated_at = EXCLUDED.updated_at
        """,
        (
            habit["id"],
            habit["narrative"],
            habit["memory_type"],
            habit.get("source", "seed"),
            habit.get("confidence", 1.0),
            habit.get(
                "context_of_encoding",
                "seed_coding_sprint_habit T-programming-engrams",
            ),
            now,
            now,
            json.dumps(habit["metadata"]),
        ),
    )
    conn.commit()
    cur.close()
    conn.close()
    print(f"  [upserted] {habit['id']}")


if __name__ == "__main__":
    seed_pg(HABIT)
    print("\nDone. Verify with:")
    print("  mcp__igor__memory_get PROC_CODING_SPRINT")
    print("\nTo test the cascade:")
    print("  1. Adopt a goal with a T-xxx ticket")
    print("  2. Let goal_continuation run steps 0-3")
    print("  3. Check TWM for GOAL_READY signal")
    print("  4. PROC_CODING_SPRINT should fire run_coding_sprint()")
