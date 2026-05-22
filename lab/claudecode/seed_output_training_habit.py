"""
seed_output_training_habit.py — Seed PROC_OUTPUT_TRAINING habit.

Creates a scheduled cognitive habit that fires run_output_training_pass()
every 45 minutes via SchedulerSource (offset from self_trainer's 30 min
to avoid simultaneous DB load).

Run once after deploying output_trainer.py:
  IGOR_HOME_DB_URL=postgresql://igor:choose_a_password@127.0.0.1/Igor-wild-0001 \
    python3 claudecode/seed_output_training_habit.py

Safe to re-run — upserts on conflict.
"""

import json
import os
from datetime import datetime

DB_URL = os.environ["IGOR_HOME_DB_URL"]

HABIT = {
    "id": "PROC_OUTPUT_TRAINING",
    "narrative": (
        "Output training loop: scan recent short-input cloud turns, extract trigger "
        "keywords, seed RESPONSE habits where no similar trigger already exists. "
        "Runs every 45 minutes via SchedulerSource. "
        "Each seeded RESPONSE habit fires at tier.1 (no inference) for future matching queries. "
        "Complement to PROC_SELF_TRAINING (knowledge) — this trains output patterns. "
        "T-output-trainer."
    ),
    "memory_type": "PROCEDURAL",
    "source": "seed",
    "confidence": 1.0,
    "context_of_encoding": "T-output-trainer seed 2026-03-26",
    "metadata": {
        "habit_type": "cognitive",
        "code_ref": "tools.output_trainer:run_output_training_pass",
        "schedule_interval_sec": 2700,  # 45 minutes (offset from self_trainer's 30 min)
        "why": (
            "Cloud reply round-trips are the most expensive operation. "
            "Each RESPONSE habit seeded removes one round-trip permanently."
        ),
        "provenance": "T-output-trainer",
        "inertia": 0.3,
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
