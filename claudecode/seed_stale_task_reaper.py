"""
seed_stale_task_reaper.py — Seed PROC_STALE_TASK_REAPER habit.

Creates a scheduled cognitive habit that fires run_stale_task_reaper()
every 45 minutes to auto-shelve stale TASK_SET memories.

Run once:
  IGOR_HOME_DB_URL=postgresql://igor:choose_a_password@127.0.0.1/igor_wild_0001 \
    python3 claudecode/seed_stale_task_reaper.py

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
    "id": "PROC_STALE_TASK_REAPER",
    "narrative": (
        "Stale task reaper: every 45 minutes, find TASK_SET memories older than 2 hours "
        "with no resolved status (done/closed/shelved/dismissed) and mark them shelved. "
        "Prevents the consolidation→NE→arc loop where an unresolved TASK_SET gets "
        "re-promoted indefinitely and fills the console with arc spam. "
        "Logs to ~/.TheIgors/logs/stale_task_reaper.log. "
        "T-stale-task-reaper."
    ),
    "memory_type": "PROCEDURAL",
    "source": "seed",
    "confidence": 1.0,
    "context_of_encoding": "T-stale-task-reaper seed 2026-03-29",
    "metadata": {
        "habit_type": "cognitive",
        "code_ref": "tools.stale_task_reaper:run_stale_task_reaper",
        "schedule_interval_sec": 2700,  # 45 minutes
        "why": (
            "TASK_SET memories with no status get re-promoted by consolidation every cycle. "
            "NE picks them up, arcs on them, habits fire, console fills with their content. "
            "Observed: 195min loop on T-book-learner-hash-lookup (2026-03-29). "
            "Reaper closes the loop automatically."
        ),
        "provenance": "T-stale-task-reaper",
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
