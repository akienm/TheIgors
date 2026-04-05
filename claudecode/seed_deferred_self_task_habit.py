"""
seed_deferred_self_task_habit.py — T-igor-deferred-self-tasks

Seeds PROC_DEFERRED_SELF_TASK: a context_inject habit that fires when Igor
is building a diagnostic or planning response, and injects the DEFERRED_TASK
format into his context so he knows how to use it.

Run once to install. Safe to re-run (upsert).
"""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

os.environ.setdefault(
    "IGOR_HOME_DB_URL",
    "postgresql://igor:choose_a_password@127.0.0.1/igor_wild_0001",
)
os.environ.setdefault(
    "IGOR_DB_PATH",
    os.path.expanduser("~/.TheIgors/Igor-wild-0001/wild-0001.db"),
)

import psycopg2
from datetime import datetime

DB_URL = os.environ["IGOR_HOME_DB_URL"]

HABIT_ID = "PROC_DEFERRED_SELF_TASK"
HABIT_NARRATIVE = (
    "PROC_DEFERRED_SELF_TASK — context_inject habit: teaches Igor the "
    "DEFERRED_TASK format for emitting self-addressed forward-reaching tasks."
)
HABIT_TRIGGER = (
    "need more context|need to check|should look up|let me search|let me check|"
    "need to fetch|should fetch|deferred task|next turn"
)
HABIT_INJECT = """\
DEFERRED SELF-TASK FORMAT
You can emit self-addressed deferred tasks from within your reply to pre-load context
for your next turn. These are stripped from the visible reply and run as background jobs.
Their results appear in TWM before your next invocation.

Supported types:
  DEFERRED_TASK|memory_search|<query>   — search Cortex memories for <query>
  DEFERRED_TASK|twm_read|               — snapshot current TWM hot items
  DEFERRED_TASK|ring_read|<category>    — read ring memory (category optional)
  DEFERRED_TASK|tool_call|<name>|<json> — call a registered tool with args JSON
  DEFERRED_TASK|note|<text>             — inject a plain note into next context

Example — you realize you need recent reading list data before answering:
  I'll fetch the reading list for next turn.
  DEFERRED_TASK|tool_call|list_unvalidated_memories|{}

Rules:
- Emit at most 2-3 deferred tasks per turn — they run in background threads.
- Prefer memory_search or tool_call; avoid redundant twm_read (TWM is already in context).
- The result will appear as DEFERRED_RESULT|... in your next TWM context.
"""

METADATA = {
    "habit_type": "context_inject",
    "trigger": HABIT_TRIGGER,
    "inject_text": HABIT_INJECT,
    "priority": 5,
    "enabled": True,
    "source": "seed_deferred_self_task_habit.py",
    "seeded_at": datetime.now().isoformat(),
}

import json

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
            (HABIT_ID, HABIT_NARRATIVE, json.dumps(METADATA)),
        )
conn.close()
print(f"Seeded {HABIT_ID} — context_inject for DEFERRED_TASK format.")
