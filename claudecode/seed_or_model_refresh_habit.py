"""
seed_or_model_refresh_habit.py — Seed PROC_OR_MODEL_REFRESH reactive habit.

Fires when Igor sees "not a valid model" or "invalid model" in his context,
calls refresh_or_models() to auto-update stale OR model IDs in-process.

Run once:
  IGOR_HOME_DB_URL=postgresql://igor:choose_a_password@127.0.0.1/igor_wild_0001 \
    python3 claudecode/seed_or_model_refresh_habit.py

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
    "id": "PROC_OR_MODEL_REFRESH",
    "narrative": (
        "When I see 'not a valid model' or 'invalid model' errors from OpenRouter, "
        "I call refresh_or_models() to fetch the current OR model list and update "
        "any stale model IDs in my environment. OR renames models regularly — "
        "this keeps me self-correcting without needing Claude to intervene. "
        "T-or-model-auto-update."
    ),
    "memory_type": "PROCEDURAL",
    "source": "seed",
    "confidence": 1.0,
    "context_of_encoding": "T-or-model-auto-update seed 2026-04-03",
    "metadata": {
        "habit_type": "reactive",
        "trigger": "not a valid model|invalid model|model.*not found",
        "code_ref": "tools.or_model_refresh:refresh_or_models",
        "why": (
            "OR model names change without notice — a renamed model causes silent 400 "
            "failures until manually fixed. Auto-refresh keeps Igor operational. "
            "In-process only (safe); logs changes for manual .env sync."
        ),
        "provenance": "T-or-model-auto-update",
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
