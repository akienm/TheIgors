#!/usr/bin/env python3
"""
seed_pe_entry_nodes.py — PROC_PE_CHAIN habit (T-pe-entry-nodes).

Seeds the PROC_PE_CHAIN code_ref habit that dispatches to run_pe_chain()
in tools/pe_chain.py. This is the entry point for the PROC_CODE_A_TICKET
execution chain — replaces OR agentic loop with Igor-native basket steps.

Current chain: ENTRY → CLAIM → READ_TICKET
Future chain:  + SITUATE → OBSERVE → HYPOTHESIZE → IMPLEMENT → TEST → CLOSE

Usage:
    cd ~/TheIgors && source venv/bin/activate
    IGOR_HOME_DB_URL=postgresql://igor:choose_a_password@127.0.0.1/igor_wild_0001 \\
        python claudecode/seed_pe_entry_nodes.py

Verify:
    Igor: memory_get("PROC_PE_CHAIN")
    Igor: run_pe_chain()

Safe to re-run — upserts on conflict.
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

DB_URL = os.environ.get(
    "IGOR_HOME_DB_URL",
    "postgresql://igor:choose_a_password@127.0.0.1/igor_wild_0001",
)

HABIT_ID = "PROC_PE_CHAIN"

HABIT_NODE = {
    "id": HABIT_ID,
    "narrative": (
        "PROC_CODE_A_TICKET execution chain — native basket step runner. "
        "Reads active GOAL → extracts ticket_id → claims ticket → loads description. "
        "Basket: {ticket_id, ticket_description, plan_files, attempt_count, expected}. "
        "Chain: ENTRY → CLAIM → READ_TICKET (SITUATE/OBSERVE/HYPOTHESIZE/IMPLEMENT/TEST/CLOSE coming). "
        "Replaces OR agentic loop with Igor-native Python steps. "
        "Call when a coding sprint begins and ticket is active."
    ),
    "memory_type": "PROCEDURAL",
    "source": "user_seeded",
    "confidence": 1.0,
    "context_of_encoding": (
        "T-pe-entry-nodes: first executable step of T-programming-engrams chain. "
        "Basket = shared Python dict; forks share parent (T-basket-fork-sharing). "
        "2026-04-02 session."
    ),
    "metadata": {
        "habit_type": "cognitive",
        "code_ref": "pe_chain:run_pe_chain",
        "trigger": "run pe chain begin coding sprint pe_chain",
        "tags": [
            "coding_sprint",
            "pe_chain",
            "basket",
            "proc_code_a_ticket",
            "layer4",
        ],
        "inertia": 0.3,
        "why": (
            "T-programming-engrams: replace OR agentic loop with Igor-native execution. "
            "Each step is a Python function that reads/writes a basket dict. "
            "The chain grows as pe-* tickets land. "
            "Basket contract: tpl-layer4-code-a-ticket-basket."
        ),
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
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, 1, 'instance')
        ON CONFLICT (id) DO UPDATE SET
            narrative          = EXCLUDED.narrative,
            metadata           = EXCLUDED.metadata,
            updated_at         = EXCLUDED.updated_at
        """,
        (
            HABIT_NODE["id"],
            HABIT_NODE["narrative"],
            HABIT_NODE["memory_type"],
            HABIT_NODE["source"],
            HABIT_NODE["confidence"],
            HABIT_NODE["context_of_encoding"],
            now,
            now,
            json.dumps(HABIT_NODE["metadata"]),
        ),
    )

    conn.commit()
    cur.close()
    conn.close()
    print(f"Seeded habit: {HABIT_ID}")
    print()
    print("Verify with:")
    print(f"  Igor: memory_get('{HABIT_ID}')")
    print("  Igor: run_pe_chain()")


if __name__ == "__main__":
    seed(DB_URL)
