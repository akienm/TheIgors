"""
seed_memory_count_habit.py — Seed PROC_MEMORY_COUNT_SNAPSHOT nightly habit.

Runs run_memory_snapshot() every 12 hours; the tool self-gates to hour >= 22
and once-per-day, so it effectively fires once nightly.

Run once:
  IGOR_HOME_DB_URL=postgresql://igor:choose_a_password@127.0.0.1/igor_wild_0001 \
    python3 claudecode/seed_memory_count_habit.py

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
    "id": "PROC_MEMORY_COUNT_SNAPSHOT",
    "narrative": (
        "Every night after 22:00 I count my memories by type and log the totals to "
        "memory_count.log. This gives me a daily trend line — I can see if my memory "
        "base is growing (learning), stagnant, or shrinking (pruning). "
        "The habit self-gates: it skips if not yet 22:00, and skips if already run today. "
        "T-nightly-memory-count."
    ),
    "memory_type": "PROCEDURAL",
    "source": "seed",
    "confidence": 1.0,
    "context_of_encoding": "T-nightly-memory-count seed 2026-04-03",
    "metadata": {
        "habit_type": "cognitive",
        "code_ref": "tools.memory_snapshot:run_memory_snapshot",
        "schedule_interval_sec": 43200,  # poll every 12h; tool self-gates to 22:00+
        "why": (
            "Memory count trend is invisible without explicit logging. "
            "Dashboard shows live count but no history. "
            "Daily snapshot lets Igor detect anomalies (sudden drop = pruning bug, "
            "flat line = learning stalled)."
        ),
        "provenance": "T-nightly-memory-count",
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
    conn.close()
    print(f"Seeded {HABIT['id']}")


if __name__ == "__main__":
    seed(DB_URL)
