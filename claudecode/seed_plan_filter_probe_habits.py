"""
seed_plan_filter_probe_habits.py — PROC_PLAN + PROC_FILTER + PROC_PROBE habits.

Seeds three cognitive habit memories (T-igor-plan-habit, T-igor-filter-habit,
T-igor-probe-habit). These are narrative PROCEDURAL memories — they give Igor's
LLM context about these steps when they appear in conversation or basket output.

The actual Python implementations live in pe_chain.py as pe_plan(), pe_filter(),
pe_probe() — wired into run_pe_entry_chain().

Run once after deploying pe_chain.py changes:
  IGOR_HOME_DB_URL=postgresql://igor:choose_a_password@127.0.0.1/Igor-wild-0001 \\
    python3 claudecode/seed_plan_filter_probe_habits.py

Safe to re-run — upserts on conflict.
"""

import json
import os
from datetime import datetime
from pathlib import Path

DB_URL = os.environ.get(
    "IGOR_HOME_DB_URL",
    "postgresql://igor:choose_a_password@127.0.0.1/Igor-wild-0001",
)

HABITS = [
    {
        "id": "PROC_PLAN",
        "narrative": (
            "Before touching any files, I generate an implementation plan for the ticket. "
            "I read the ticket description, then call tier.2 Ollama with a tight prompt: "
            "'given this description, what file(s) change and how? what test verifies it?' "
            "The result lands in basket[plan_summary] and basket[test_criterion]. "
            "I also call store_plan() to persist it across restarts. "
            "If tier.2 is unavailable, I use the ticket description as the plan_summary. "
            "This step runs after READ_TICKET and before FILTER in the pe_chain."
        ),
        "memory_type": "PROCEDURAL",
        "source": "seed",
        "confidence": 1.0,
        "context_of_encoding": "T-igor-plan-habit — seed_plan_filter_probe_habits 2026-04-03",
        "metadata": {
            "habit_type": "cognitive",
            "code_ref": "pe_chain:pe_plan",
            "chain_step": "PLAN",
            "chain_position": "after READ_TICKET, before FILTER",
            "proc_name": "PROC_PLAN",
            "inertia": 0.2,
            "why": (
                "T-igor-as-programmer: gives Igor a concrete plan before he starts "
                "grepping and editing. Without a plan, HYPOTHESIZE works blind. "
                "With a plan, tier.2 has a stated goal to aim at."
            ),
        },
    },
    {
        "id": "PROC_FILTER",
        "narrative": (
            "After I have a plan, I run a safety checklist before touching any files. "
            "I check three things: (1) is plan_summary present? (2) is test_criterion defined? "
            "(3) do plan_files include any HIGH inertia paths (brainstem/, models.py, reasoners/base.py)? "
            "If HIGH inertia files are in scope, I hard-fail and escalate — those require Akien. "
            "Missing plan or test criterion log as warnings but I proceed. "
            "Result lands in basket[filter_result]: 'PASS', 'WARN: reasons', or 'FAIL: reasons'. "
            "This step runs after PLAN and before SITUATE in the pe_chain."
        ),
        "memory_type": "PROCEDURAL",
        "source": "seed",
        "confidence": 1.0,
        "context_of_encoding": "T-igor-filter-habit — seed_plan_filter_probe_habits 2026-04-03",
        "metadata": {
            "habit_type": "cognitive",
            "code_ref": "pe_chain:pe_filter",
            "chain_step": "FILTER",
            "chain_position": "after PLAN, before SITUATE",
            "proc_name": "PROC_FILTER",
            "inertia": 0.2,
            "why": (
                "T-igor-as-programmer: prevents Igor from touching HIGH inertia files "
                "without escalation. Mirrors the /filter CC skill checklist. "
                "Gives early feedback before any LLM work or file reads."
            ),
        },
    },
    {
        "id": "PROC_PROBE",
        "narrative": (
            "After tests pass, I optionally run a behavioral probe before committing. "
            "I check if the ticket has a 'probe_criterion' field. "
            "If present, I send the criterion as a [probe] message via cc_send, wait 3 seconds, "
            "then read the last 3 Igor channel messages. "
            "If the criterion has an 'expect:' line, I check that Igor's response contains that string. "
            "On PASS or no expected pattern: I proceed to commit. "
            "On FAIL: I set escalate_reason and skip the commit. "
            "If probe_criterion is absent, I skip silently (SKIP: no probe_criterion). "
            "This step runs after TEST and before CLOSE_LOOP in the pe_chain."
        ),
        "memory_type": "PROCEDURAL",
        "source": "seed",
        "confidence": 1.0,
        "context_of_encoding": "T-igor-probe-habit — seed_plan_filter_probe_habits 2026-04-03",
        "metadata": {
            "habit_type": "cognitive",
            "code_ref": "pe_chain:pe_probe",
            "chain_step": "PROBE",
            "chain_position": "after TEST, before CLOSE_LOOP",
            "proc_name": "PROC_PROBE",
            "inertia": 0.2,
            "why": (
                "T-igor-as-programmer: allows tickets to specify a behavioral probe "
                "that verifies Igor's own response to a stimulus after the change. "
                "Mirrors the /probe CC skill. Most tickets skip this (no probe_criterion)."
            ),
        },
    },
]


def seed_pg(habits: list) -> None:
    import psycopg2

    conn = psycopg2.connect(DB_URL)
    cur = conn.cursor()
    now = datetime.now().isoformat()
    for habit in habits:
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
                habit["id"],
                habit["narrative"],
                habit["memory_type"],
                habit.get("source", "seed"),
                habit.get("confidence", 1.0),
                habit.get("context_of_encoding", "seed_plan_filter_probe_habits"),
                now,
                now,
                json.dumps(habit["metadata"]),
            ),
        )
        print(f"  [upserted] {habit['id']}")
    conn.commit()
    cur.close()
    conn.close()


if __name__ == "__main__":
    seed_pg(HABITS)
    print("\nDone. Verify with:")
    print("  mcp__igor__memory_get PROC_PLAN")
    print("  mcp__igor__memory_get PROC_FILTER")
    print("  mcp__igor__memory_get PROC_PROBE")
