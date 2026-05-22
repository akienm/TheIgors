"""
seed_skill_commit_engram.py — T-skill-engram-sprint

Seeds PROC_INVOKE_COMMIT habit: routes /commit or commit-related requests
to the SKILL_COMMIT_ENTRY engram node (already seeded by import_all_skills).

Run once. Safe to re-run (upsert on conflict).
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


import psycopg2

DB_URL = os.environ["IGOR_HOME_DB_URL"]


HABIT_ID = "PROC_INVOKE_COMMIT"
HABIT_NARRATIVE = (
    "PROC_INVOKE_COMMIT — when asked to commit, push, or ship code changes, "
    "invoke the commit skill engram. Runs tests, audits staged changes, "
    "stages files, commits, pulls, and pushes. Full cycle."
)
HABIT_METADATA = {
    "habit_type": "cognitive",
    "trigger": (
        "/commit|commit and push|commit this|push the changes|ship it|"
        "commit changes|git commit|push to main|commit to git"
    ),
    "code_ref": "pe_chain:run_engram_cursor",
    "engram_entry": "SKILL_COMMIT_ENTRY",
    "conversation_eligible": True,
    "priority": 8,
    "enabled": True,
    "source": "seed_skill_commit_engram.py",
    "seeded_at": datetime.now().isoformat(),
}


conn = psycopg2.connect(DB_URL)
with conn:
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO memories (id, memory_type, narrative, metadata, timestamp)
            VALUES (%s, 'PROCEDURAL', %s, %s::jsonb, NOW())
            ON CONFLICT (id) DO UPDATE
              SET narrative = EXCLUDED.narrative,
                  metadata  = EXCLUDED.metadata,
                  timestamp = NOW()
            """,
            (HABIT_ID, HABIT_NARRATIVE, json.dumps(HABIT_METADATA)),
        )
        print(f"Seeded {HABIT_ID}")

conn.close()
print("Done.")
