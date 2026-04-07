"""
seed_self_training_habit.py — Seed PROC_SELF_TRAINING habit.

Creates a scheduled cognitive habit that fires run_self_training_pass()
every 30 minutes via SchedulerSource.

Run once after deploying self_trainer.py:
  IGOR_HOME_DB_URL=postgresql://igor:choose_a_password@127.0.0.1/Igor-wild-0001 \
    python3 claudecode/seed_self_training_habit.py

Safe to re-run — upserts on conflict.
"""

import json
import os
import sys
import uuid
from datetime import datetime

DB_URL = os.environ.get(
    "IGOR_HOME_DB_URL",
    "postgresql://igor:choose_a_password@127.0.0.1/Igor-wild-0001",
)

HABIT = {
    "id": "PROC_SELF_TRAINING",
    "narrative": (
        "Self-training loop: scan recent cloud inference turns, find matrix gaps "
        "(queries where coverage was thin), deposit LLM responses as FACTUAL memories. "
        "Runs every 30 minutes via SchedulerSource. "
        "Gap signal: no memory narrative contains the query tokens. "
        "Deposit: FACTUAL, source=self_training, confidence=0.7. "
        "Each cloud call that gets deposited may prevent the next identical call. "
        "T-self-training-loop."
    ),
    "memory_type": "PROCEDURAL",
    "source": "seed",
    "confidence": 1.0,
    "context_of_encoding": "T-self-training-loop seed 2026-03-26",
    "metadata": {
        "habit_type": "cognitive",
        "code_ref": "tools.self_trainer:run_self_training_pass",
        "schedule_interval_sec": 1800,  # 30 minutes
        "why": (
            "Every cloud call the matrix couldn't serve becomes a deposit. "
            "Progressive densification: graph answers more each cycle."
        ),
        "provenance": "T-self-training-loop",
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
            narrative = EXCLUDED.narrative,
            metadata  = EXCLUDED.metadata,
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
