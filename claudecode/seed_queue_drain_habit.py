"""
seed_queue_drain_habit.py — PROC_QUEUE_DRAIN habit (T-goal-queue-consumer).

Seeds a scheduled cognitive habit that fires adopt_top_queue_ticket()
every 30 minutes. If no goal is active and a pending ticket exists,
Igor adopts it autonomously.

Run once after deploying:
  IGOR_HOME_DB_URL=postgresql://igor:choose_a_password@127.0.0.1/igor_wild_0001 \
    python3 claudecode/seed_queue_drain_habit.py

Safe to re-run — upserts on conflict.
"""

import json
import os
from datetime import datetime

DB_URL = os.environ.get(
    "IGOR_HOME_DB_URL",
    "postgresql://igor:choose_a_password@127.0.0.1/igor_wild_0001",
)

HABIT = {
    "id": "PROC_QUEUE_DRAIN",
    "narrative": (
        "Queue drain: every 30 minutes during idle time, check the cc_channel work queue "
        "for pending tickets assigned to 'claude'. If no goal is currently active, adopt "
        "the top-priority pending ticket as an active GOAL so Igor can work it autonomously. "
        "No-ops silently when a goal is already active or the queue is empty. "
        "Calls adopt_top_queue_ticket() — a zero-arg tool that handles the active-goal "
        "check, queue read, priority sort, and goal_adopt in one step. "
        "T-goal-queue-consumer."
    ),
    "memory_type": "PROCEDURAL",
    "source": "seed",
    "confidence": 1.0,
    "context_of_encoding": "T-goal-queue-consumer seed 2026-04-01",
    "metadata": {
        "habit_type": "cognitive",
        "code_ref": "ops:adopt_top_queue_ticket",
        "schedule_interval_sec": 1800,  # 30 minutes
        "why": (
            "Igor had no mechanism to act on queued tickets during idle time. "
            "Tickets sat in queue.json indefinitely. PROC_QUEUE_DRAIN closes the loop: "
            "idle Igor picks the top pending ticket and adopts it as a goal, enabling "
            "autonomous work without Akien needing to manually trigger each ticket. "
            "Active-goal guard prevents re-adoption while work is in progress."
        ),
        "provenance": "T-goal-queue-consumer",
        "inertia": 0.2,
    },
}


def seed(db_url: str) -> None:
    import psycopg2

    conn = psycopg2.connect(db_url)
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
            HABIT["id"],
            HABIT["narrative"],
            HABIT["memory_type"],
            HABIT["source"],
            HABIT["confidence"],
            HABIT["context_of_encoding"],
            now,
            now,
            json.dumps(HABIT["metadata"]),
        ),
    )
    conn.commit()
    cur.close()
    conn.close()
    print(
        f"Seeded {HABIT['id']} — schedule_interval_sec={HABIT['metadata']['schedule_interval_sec']}"
    )


if __name__ == "__main__":
    seed(DB_URL)
