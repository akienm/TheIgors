"""
seed_skill_sprint_engram.py — T-skill-engram-sprint

Seeds PROC_INVOKE_SPRINT habit: routes /sprint or sprint-related requests
to the SKILL_SPRINT_ENTRY engram node (already seeded by import_all_skills).

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


HABIT_ID = "PROC_INVOKE_SPRINT"
HABIT_NARRATIVE = (
    "PROC_INVOKE_SPRINT — when asked to sprint on a ticket, run a coding sprint, "
    "or work a task, invoke the sprint skill engram. Claims a ticket from the queue, "
    "loads context, works the ticket, and reports back."
)
HABIT_METADATA = {
    "habit_type": "cognitive",
    "trigger": (
        "/sprint|sprint on|start sprint|work a ticket|pick up a ticket|"
        "work the next ticket|sprint this|coding sprint|run sprint"
    ),
    "code_ref": "pe_chain:run_engram_cursor",
    "engram_entry": "SKILL_SPRINT_ENTRY",
    "conversation_eligible": True,
    "priority": 8,
    "enabled": True,
    "source": "seed_skill_sprint_engram.py",
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
