"""
seed_goal_close_habit.py — PROC_GOAL_CLOSE habit (T-goal-close-habit).

Seeds a tool habit that closes an active GOAL by ticket ID.
Fires when user says "close goal T-xxx", "goal done", "goal complete", etc.
Calls close_goal_by_ticket(ticket_id) — single-arg wrapper in ops.py.

Run once after deploying:
  IGOR_HOME_DB_URL=postgresql://igor:choose_a_password@127.0.0.1/Igor-wild-0001 \
    python3 claudecode/seed_goal_close_habit.py

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
DB_URL = os.environ["IGOR_HOME_DB_URL"]


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
                "context_of_encoding", "seed_goal_close_habit T-goal-close-habit"
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


seed_pg(
    {
        "id": "PROC_GOAL_CLOSE",
        "narrative": (
            "When Akien says 'close goal T-xxx', 'goal done', 'goal complete', or "
            "'goal closed', I find the active GOAL whose source_message contains that "
            "ticket ID and mark it inactive. I call close_goal_by_ticket with the ticket "
            "ID extracted from the message. If no matching active goal is found I say so. "
            "This closes the goal continuity loop started by PROC_GOAL_ADOPTION."
        ),
        "memory_type": "PROCEDURAL",
        "source": "seed",
        "confidence": 1.0,
        "context_of_encoding": "T-goal-close-habit — seed_goal_close_habit 2026-04-01",
        "metadata": {
            "habit_type": "tool",
            "trigger": "close goal|goal done|goal complete|goal closed",
            "tool": "close_goal_by_ticket",
            "arg_field": "ticket_id",
            "extract_pattern": r"(T-[\w-]+)",
            "match_mode": "trigger_only",
            "proc_name": "PROC_GOAL_CLOSE",
            "why": (
                "T-goal-close-habit: Igor had no habit for closing goals by ticket. "
                "LLM was hallucinating a goals.py file. Single-arg wrapper satisfies "
                "habit dispatch constraint (max one required arg for auto-dispatch)."
            ),
            "inertia": 0.25,
        },
    }
)

print("\nDone. Verify with:")
print("  mcp__igor__memory_get PROC_GOAL_CLOSE")
