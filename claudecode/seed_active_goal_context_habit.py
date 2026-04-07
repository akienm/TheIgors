#!/usr/bin/env python3
"""
seed_active_goal_context_habit.py — T-thread-context-persistence.

Seeds PROC_ACTIVE_GOAL_CONTEXT_REFRESH — a scheduler habit that reads the
active goal's stored implementation plan from traversal_contexts every 2 minutes
and surfaces it to TWM so BG scoring sees it as context on every turn.

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
        "id": "PROC_ACTIVE_GOAL_CONTEXT_REFRESH",
        "narrative": (
            "Every 2 minutes, read my active goal's stored implementation plan from "
            "traversal_contexts and surface it to TWM. This ensures my plan is always "
            "visible to BG scoring and the LLM even after restarts. When I have an active "
            "goal, this keeps the plan in my working memory continuously."
        ),
        "memory_type": "PROCEDURAL",
        "source": "user_seeded",
        "confidence": 1.0,
        "context_of_encoding": "T-thread-context-persistence — seed_active_goal_context_habit 2026-04-02",
        "metadata": {
            "habit_type": "cognitive",
            "code_ref": "ops:read_active_goal_plan",
            "schedule_interval_sec": 120,
            "why": (
                "T-thread-context-persistence: active goal plan must surface to TWM every 2 min "
                "so BG sees it as context on every turn. Same pattern as PROC_GOAL_CONTINUATION "
                "scheduler habit."
            ),
            "inertia": 0.2,
        },
    }
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
    print("T-thread-context-persistence habit seeded. Verify with:")
    print("  mcp__igor__memory_get PROC_ACTIVE_GOAL_CONTEXT_REFRESH")
    print()
    print("Test via cc_send:")
    print(
        "  \"store_plan T-foo 'Read X, add Y, test Z'\"  → store_plan() → traversal_contexts upsert"
    )
    print(
        "  After 2 min: PROC_ACTIVE_GOAL_CONTEXT_REFRESH fires → read_active_goal_plan()"
    )


if __name__ == "__main__":
    seed(DB_URL)
