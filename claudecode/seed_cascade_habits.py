#!/usr/bin/env python3
"""
seed_cascade_habits.py — D302 direct-dispatch habits for coding cascade.

Seeds PROC_CLOSE_GOAL and PROC_TWM_READ_GOAL — code_ref wrappers needed by
the MANAGEMENT_PHRASES entries added to basal_ganglia.py (D302).

Safe to re-run — upserts on conflict.
"""

import json
import os
from datetime import datetime

DB_URL = os.environ.get(
    "IGOR_HOME_DB_URL",
    "postgresql://igor:choose_a_password@127.0.0.1/Igor-wild-0001",
)

HABITS = [
    {
        "id": "PROC_CLOSE_GOAL",
        "narrative": (
            "Close my active goal. Calls close_goal() to mark the most recent "
            "active GOAL memory as completed. Use when a ticket is done or when "
            "the goal needs to be released before adopting a new one."
        ),
        "memory_type": "PROCEDURAL",
        "source": "user_seeded",
        "confidence": 1.0,
        "context_of_encoding": "D302 cascade direct dispatch habits",
        "metadata": {
            "habit_type": "cognitive",
            "code_ref": "ops:close_goal",
            "inertia": 0.2,
            "why": (
                "D302: MANAGEMENT_PHRASES maps 'close goal' → PROC_CLOSE_GOAL. "
                "Without this habit, close_goal() has no code_ref wrapper and "
                "BG cannot dispatch it directly — LLM generates text instead."
            ),
        },
    },
    {
        "id": "PROC_TWM_READ_GOAL",
        "narrative": (
            "Read my current active goal from TWM. Calls prim_twm_read_active_goal() "
            "and returns the goal text currently held in working memory, or "
            "'No active goal set.' if none. Use to check what goal I'm pursuing."
        ),
        "memory_type": "PROCEDURAL",
        "source": "user_seeded",
        "confidence": 1.0,
        "context_of_encoding": "D302 cascade direct dispatch habits",
        "metadata": {
            "habit_type": "cognitive",
            "code_ref": "os_primitives:prim_twm_read_active_goal",
            "inertia": 0.1,
            "why": (
                "D302: MANAGEMENT_PHRASES maps 'read active goal' / 'what is my goal' "
                "→ PROC_TWM_READ_GOAL. Gives Igor reliable proprioception of his "
                "own current goal via direct code_ref dispatch, bypassing LLM."
            ),
        },
    },
]


def seed(db_url: str) -> None:
    import psycopg2

    conn = psycopg2.connect(db_url)
    cur = conn.cursor()
    now = datetime.now().isoformat()

    for habit in HABITS:
        cur.execute(
            """
            INSERT INTO memories
                (id, narrative, memory_type, source, confidence,
                 context_of_encoding, timestamp, updated_at,
                 metadata, portable, scope)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, 1, 'class')
            ON CONFLICT (id) DO UPDATE SET
                narrative          = EXCLUDED.narrative,
                metadata           = EXCLUDED.metadata,
                updated_at         = EXCLUDED.updated_at
            """,
            (
                habit["id"],
                habit["narrative"],
                habit["memory_type"],
                habit["source"],
                habit["confidence"],
                habit["context_of_encoding"],
                now,
                now,
                json.dumps(habit["metadata"]),
            ),
        )
        print(f"[upserted] {habit['id']}")

    conn.commit()
    cur.close()
    conn.close()
    print()
    print("D302 cascade habits seeded. Verify with:")
    print("  mcp__igor__memory_get PROC_CLOSE_GOAL")
    print("  mcp__igor__memory_get PROC_TWM_READ_GOAL")
    print()
    print("Test via cc_send:")
    print('  "close goal"         → PROC_CLOSE_GOAL  → close_goal()')
    print('  "read active goal"   → PROC_TWM_READ_GOAL → prim_twm_read_active_goal()')
    print('  "adopt top ticket"   → PROC_QUEUE_DRAIN  → adopt_top_queue_ticket()')
    print('  "goal continuation"  → PROC_GOAL_CONTINUATION → run_goal_continuation()')
    print('  "coding sprint"      → PROC_CODING_SPRINT → run_coding_sprint()')


if __name__ == "__main__":
    seed(DB_URL)
