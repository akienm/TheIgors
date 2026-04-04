#!/usr/bin/env python3
"""
seed_git_auth_check_habit.py — T-gh-auth-check: PROC_GIT_AUTH_CHECK habit.

Seeds a cognitive habit that fires on git push intent and runs check_gh_auth()
to detect expired gh tokens before git push fails silently.

Safe to re-run — upserts on conflict.
"""

import json
import os
from datetime import datetime

import psycopg2

DB_URL = os.environ.get(
    "IGOR_HOME_DB_URL",
    "postgresql://igor:choose_a_password@127.0.0.1/igor_wild_0001",
)

HABITS = [
    {
        "id": "PROC_GIT_AUTH_CHECK",
        "narrative": (
            "Before pushing to git, I check whether the gh CLI auth token is valid. "
            "gh tokens expire silently — if expired, git push prompts for a password "
            "that always fails with 2FA enabled. I run check_gh_auth() to catch this "
            "before it causes a confusing failure mid-commit."
        ),
        "memory_type": "PROCEDURAL",
        "source": "user_seeded",
        "confidence": 1.0,
        "context_of_encoding": "T-gh-auth-check: pre-push auth gate",
        "metadata": {
            "habit_type": "cognitive",
            "code_ref": "git_auth_check:check_gh_auth",
            "trigger": "git push|push to git|push origin|commit and push|gh auth",
            "inertia": 0.2,
            "why": (
                "T-gh-auth-check: gh token expired mid-session 2026-04-04, "
                "git push prompted for password which always fails with 2FA. "
                "This habit catches the expiry before the push attempt."
            ),
        },
    }
]


def seed(db_url: str) -> None:
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
    print("PROC_GIT_AUTH_CHECK seeded. Verify with:")
    print("  mcp__igor__memory_get PROC_GIT_AUTH_CHECK")


if __name__ == "__main__":
    seed(DB_URL)
