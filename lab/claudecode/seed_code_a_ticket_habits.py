#!/usr/bin/env python3
"""
seed_code_a_ticket_habits.py — PROC_CODE_A_TICKET + PROC_RUN_TESTS habits.

Seeds:
  PROC_RUN_TESTS      — code_ref wrapper for ops:run_tests (zero-arg pytest runner)
  PROC_CODE_A_TICKET  — 8-step procedure habit triggered by [CODING SPRINT]

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
        "id": "PROC_RUN_TESTS",
        "narrative": (
            "Run the test suite. Calls run_tests() which executes pytest tests/ -x -q "
            "and returns the last 30 lines of output. Use to verify changes don't break "
            "anything before committing."
        ),
        "memory_type": "PROCEDURAL",
        "source": "user_seeded",
        "confidence": 1.0,
        "context_of_encoding": "T-thread-context-persistence coding cascade habits",
        "metadata": {
            "habit_type": "cognitive",
            "code_ref": "ops:run_tests",
            "inertia": 0.2,
            "why": (
                "Gives Igor a zero-arg run_tests tool dispatchable via MANAGEMENT_PHRASES. "
                "Part of PROC_CODE_A_TICKET procedure."
            ),
        },
    },
    {
        "id": "PROC_CODE_A_TICKET",
        "narrative": (
            "My procedure when I receive a [CODING SPRINT] prompt:\n"
            "1. Read the ticket description carefully. Identify: what file changes, what the fix does, what test verifies it.\n"
            "2. Call store_plan with ticket_id and a 2-3 sentence plan BEFORE touching any file.\n"
            "   Example: store_plan('T-deadend-ack-filter', 'Add post_response_filter() in main.py before channel post. Filter strips bare ack phrases. Test: unit test with mock response.')\n"
            "3. Use run_bash to grep for the relevant code: grep -n 'pattern' wild_igor/igor/main.py\n"
            "4. Use read_file to read the relevant section of the file.\n"
            "5. Write the fix. Use run_bash with a heredoc or direct edit tool.\n"
            "6. Call run_tests to verify nothing is broken.\n"
            "7. If tests pass: commit with a descriptive message.\n"
            "8. Call close_goal when done.\n"
            "Key rules: always store_plan first; always run_tests before commit; never skip close_goal."
        ),
        "memory_type": "PROCEDURAL",
        "source": "user_seeded",
        "confidence": 1.0,
        "context_of_encoding": "coding cascade — procedure for implementing tickets",
        "metadata": {
            "habit_type": "cognitive",
            "trigger": "[CODING SPRINT]",
            "inertia": 0.3,
            "why": (
                "Gives Igor a structured 8-step procedure when he receives a [CODING SPRINT] prompt. "
                "Without this he acks and goes quiet. With this the LLM has a concrete procedure to follow."
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
    print("PROC_CODE_A_TICKET habits seeded. Verify with:")
    print("  mcp__igor__memory_get PROC_RUN_TESTS")
    print("  mcp__igor__memory_get PROC_CODE_A_TICKET")
    print()
    print("Test via cc_send:")
    print('  "run tests"          → PROC_RUN_TESTS    → run_tests()')
    print('  "[CODING SPRINT] ..." → PROC_CODE_A_TICKET → 8-step procedure')


if __name__ == "__main__":
    seed(DB_URL)
