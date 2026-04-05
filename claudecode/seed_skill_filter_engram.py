"""
seed_skill_filter_engram.py — T-skill-to-engram-filter

Seeds:
  1. SKILL_FILTER_ENTRY — PROCEDURAL Memory node (engram) that invokes run_filter
     via MCPCALL and emits the result to TWM. Igor's cursor can traverse this.

  2. PROC_INVOKE_FILTER — PROCEDURAL habit trigger: when Igor sees "filter the plan /
     is this ready / check the plan", invoke run_filter with the current input.

Run once. Safe to re-run (upsert on conflict).
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

os.environ.setdefault(
    "IGOR_HOME_DB_URL",
    "postgresql://igor:choose_a_password@127.0.0.1/igor_wild_0001",
)

import psycopg2

DB_URL = os.environ["IGOR_HOME_DB_URL"]


# ── 1. SKILL_FILTER_ENTRY engram node ─────────────────────────────────────────
#
# Payload cell "run_cell":
#   MCPCALL run_filter (args from basket["filter_args"]) → basket["filter_result"]
#   EMITIF True → emit result to TWM channel
#   EMITIF True → emit result to basket["output"] for caller inspection
#   ENDIF
#
# Basket contract:
#   INPUT:  basket["filter_args"]["plan_text"] = plan text to check
#   OUTPUT: basket["filter_result"] = FILTER RESULT string
#           basket["output"]        = same (convenience alias)

ENGRAM_ID = "SKILL_FILTER_ENTRY"
ENGRAM_NARRATIVE = (
    "SKILL_FILTER_ENTRY — engram node: run Filter plan-verification skill. "
    "MCPCALL run_filter with basket['filter_args'], emit result to TWM + basket['output']. "
    "Invoke with basket['filter_args'] = {'plan_text': '...'}."
)
ENGRAM_METADATA = {
    "memory_type": "PROCEDURAL",
    "skill_source": "~/.claude/skills/filter/SKILL.md",
    "skill_version": "2026-04-04",
    "triggers": {"__entry__": "run_cell"},
    "inertia": 0.3,
    "seeded_at": datetime.now().isoformat(),
}
ENGRAM_PAYLOAD = {
    "run_cell": [
        # Step 1: call run_filter with args from basket
        ["MCPCALL", "run_filter", "filter_args", "filter_result"],
        # Step 2: copy result to output alias
        ["EMITIF", True, "output", ["basket", "filter_result"], "basket"],
        # Step 3: push result to TWM so it's visible in Igor's next context
        ["EMITIF", True, "filter_result", ["basket", "filter_result"], "twm"],
        "ENDIF",
    ]
}


# ── 2. PROC_INVOKE_FILTER habit ───────────────────────────────────────────────

HABIT_ID = "PROC_INVOKE_FILTER"
HABIT_NARRATIVE = (
    "PROC_INVOKE_FILTER — when asked to filter a plan or check readiness, "
    "call run_filter tool with the plan text. Returns FILTER RESULT: PASS or FAIL."
)
HABIT_METADATA = {
    "habit_type": "tool",
    "trigger": (
        "filter the plan|filter this plan|is this ready|check the plan|"
        "/filter|verify the plan|run filter|plan ready"
    ),
    "code_ref": "skill_filter:run_filter",
    "priority": 8,
    "enabled": True,
    "source": "seed_skill_filter_engram.py",
    "seeded_at": datetime.now().isoformat(),
}


conn = psycopg2.connect(DB_URL)
with conn:
    with conn.cursor() as cur:
        # Upsert engram node
        cur.execute(
            """
            INSERT INTO memories (id, memory_type, narrative, metadata, payload, timestamp)
            VALUES (%s, 'PROCEDURAL', %s, %s::jsonb, %s::jsonb, NOW())
            ON CONFLICT (id) DO UPDATE
              SET narrative = EXCLUDED.narrative,
                  metadata  = EXCLUDED.metadata,
                  payload   = EXCLUDED.payload,
                  timestamp = NOW()
            """,
            (
                ENGRAM_ID,
                ENGRAM_NARRATIVE,
                json.dumps(ENGRAM_METADATA),
                json.dumps(ENGRAM_PAYLOAD),
            ),
        )
        print(f"Seeded {ENGRAM_ID}")

        # Upsert habit
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
