#!/usr/bin/env python3
"""
seed_coding_engrams.py — T-igor-as-programmer

Seed engram nodes for the coding dev cycle, mirroring pe_chain.py's
decomposition. Each pe_ function becomes its own engram node wired
as a BRANCHIF chain.

Usage:
    IGOR_HOME_DB_URL=postgresql://... python3 lab/claudecode/seed_coding_engrams.py [--dry-run]
"""

import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

DB_URL = os.environ.get("IGOR_HOME_DB_URL", "")
if not DB_URL:
    print("IGOR_HOME_DB_URL not set")
    sys.exit(1)


# The coding chain: each step with its pe_ function and description
CODING_CHAIN = [
    {
        "id": "ENGRAM_CODE_INIT",
        "narrative": "Initialize coding sprint: load ticket, set up basket with ticket_id, description, and initial state.",
        "code_ref": "tools.pe_chain:pe_entry_init",
    },
    {
        "id": "ENGRAM_CODE_CLAIM",
        "narrative": "Claim the ticket in cc_queue so other workers don't pick it up.",
        "code_ref": "tools.pe_chain:pe_claim",
    },
    {
        "id": "ENGRAM_CODE_READ",
        "narrative": "Read the ticket description and extract requirements, affected files, and test criteria.",
        "code_ref": "tools.pe_chain:pe_read_ticket",
    },
    {
        "id": "ENGRAM_CODE_PLAN",
        "narrative": "Plan the implementation: call LLM with ticket description to produce a plan_summary and test_criterion.",
        "code_ref": "tools.pe_chain:pe_plan",
    },
    {
        "id": "ENGRAM_CODE_FILTER",
        "narrative": "Verify plan readiness: check plan_summary present, test_criterion defined, scope guard against large diffs.",
        "code_ref": "tools.pe_chain:pe_filter",
    },
    {
        "id": "ENGRAM_CODE_SITUATE",
        "narrative": "Situate in codebase: grep for relevant patterns, read key files, build file_context in basket.",
        "code_ref": "tools.pe_chain:pe_situate",
    },
    {
        "id": "ENGRAM_CODE_OBSERVE",
        "narrative": "Observe current state: run tests before changes to establish baseline. Record pre-existing failures.",
        "code_ref": "tools.pe_chain:pe_observe",
    },
    {
        "id": "ENGRAM_CODE_HYPOTHESIZE",
        "narrative": "Hypothesize the fix: call LLM with plan + file_context to generate specific code changes.",
        "code_ref": "tools.pe_chain:pe_hypothesize",
    },
    {
        "id": "ENGRAM_CODE_IMPLEMENT",
        "narrative": "Implement the changes: apply the hypothesized code changes to the actual files.",
        "code_ref": "tools.pe_chain:pe_implement",
    },
    {
        "id": "ENGRAM_CODE_TEST",
        "narrative": "Test the changes: run the test suite to verify the implementation works.",
        "code_ref": "tools.pe_chain:pe_test",
    },
    {
        "id": "ENGRAM_CODE_PROBE",
        "narrative": "Probe for issues: review the diff, check for unintended side effects, verify scope.",
        "code_ref": "tools.pe_chain:pe_probe",
    },
    {
        "id": "ENGRAM_CODE_CLOSE",
        "narrative": "Close the loop: commit, mark ticket done, deposit results as memory.",
        "code_ref": "tools.pe_chain:pe_close_loop",
    },
]


def seed(dry_run: bool = False):
    import psycopg2

    conn = psycopg2.connect(DB_URL)
    cur = conn.cursor()
    cur.execute("SET search_path TO instance, clan, infra, public")

    # Create chain: each node branches to the next via BRANCHIF payload
    for i, step in enumerate(CODING_CHAIN):
        next_id = CODING_CHAIN[i + 1]["id"] if i + 1 < len(CODING_CHAIN) else None

        # Build payload with BRANCHIF to next step (if not last)
        payload_cells = []
        # MCPCALL to execute the pe_ function
        payload_cells.append(
            ["MCPCALL", step["code_ref"].split(":")[-1], "_basket_args", "_step_result"]
        )
        if next_id:
            # Branch to next step unconditionally
            payload_cells.append(["BRANCHIF", True, next_id])

        metadata = {
            "code_ref": step["code_ref"],
            "habit_type": "engram",
            "inertia": 0.3,
            "coding_chain": True,
            "chain_position": i,
            "chain_length": len(CODING_CHAIN),
            "triggers": {"__entry__": "coding sprint entry"},
        }

        payload = {"cells": payload_cells}

        if dry_run:
            print(f"  [{i}] {step['id']} → {next_id or 'END'}")
            print(f"      code_ref: {step['code_ref']}")
            print(f"      payload: {json.dumps(payload_cells)}")
            continue

        # Upsert: ON CONFLICT update narrative + metadata + payload
        cur.execute(
            """
            INSERT INTO memories (id, narrative, memory_type, parent_id, source, confidence,
                                  metadata, payload, scope)
            VALUES (%s, %s, 'PROCEDURAL', 'CP1', 'seed', 1.0, %s, %s, 'class')
            ON CONFLICT (id) DO UPDATE SET
                narrative = EXCLUDED.narrative,
                metadata = EXCLUDED.metadata,
                payload = EXCLUDED.payload
            """,
            (
                step["id"],
                step["narrative"],
                json.dumps(metadata),
                json.dumps(payload),
            ),
        )
        print(f"  Seeded {step['id']} → {next_id or 'END'}")

    # Update PROC_CODE_A_TICKET to point to the chain entry
    if not dry_run:
        cur.execute(
            """
            UPDATE memories SET metadata = jsonb_set(
                jsonb_set(metadata, '{engram_entry}', '"ENGRAM_CODE_INIT"'),
                '{chain_note}', '"Coding dev cycle decomposed into engram chain. Entry: ENGRAM_CODE_INIT"'
            )
            WHERE id = 'PROC_CODE_A_TICKET'
            """,
        )
        print("  Updated PROC_CODE_A_TICKET with engram_entry pointer")

    if dry_run:
        print(f"\nDRY RUN — {len(CODING_CHAIN)} nodes would be seeded")
        conn.rollback()
    else:
        conn.commit()
        print(f"\nSeeded {len(CODING_CHAIN)} coding engram nodes")

    cur.close()
    conn.close()


if __name__ == "__main__":
    dry = "--dry-run" in sys.argv
    seed(dry_run=dry)
