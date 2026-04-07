#!/usr/bin/env python3
"""
seed_pe_basket_contract.py — PROC_CODE_A_TICKET basket contract (T-pe-basket).

Layer 4 schema node. Defines the shared Python dict (basket) that all
PROC_CODE_A_TICKET engram nodes read from and emit into.

Basket semantics (T-basket-fork-sharing design):
  - The basket is a plain Python dict, alive in memory for one engram run.
  - Forks share the parent basket (concurrent read). Child processes emit
    results back into the shared basket. No copy-on-fork.
  - Isolation (when needed): create a new scoped basket and EMIT a keyed
    subset into it — not serialization, just projection.
  - JSON serialization only at async fork boundaries (when a new process
    needs to reconstruct basket state).

Basket contract:

  Key                     Type            Written by          Read by
  ──────────────────────────────────────────────────────────────────────
  ticket_id               str             ENTRY (from TWM)    CLAIM, READ_TICKET
  ticket_description      str             READ_TICKET         SITUATE, HYPOTHESIZE
  plan_files              list[str]       SITUATE             OBSERVE
  line_range              dict            OBSERVE pass-1      OBSERVE pass-2
                          {file, start,   (grep result)
                           end}
  actual                  str             OBSERVE pass-2      HYPOTHESIZE
                                          (file section)
  expected                str             constant            OBSERVE (optional —
                          "tests pass,                        used as baseline for
                           requirements                       delta computation)
                           met"
  hypothesis              dict            HYPOTHESIZE         IMPLEMENT
                          {file,
                           old_string,
                           new_string}
  test_result             str             TEST                BRANCHIF
                          "pass" |
                          "fail: <msg>"
  attempt_count           int             ENTRY (=0)          BRANCHIF, REPLAN
                                          REPLAN (increment)

Usage:
    cd ~/TheIgors && source venv/bin/activate
    IGOR_HOME_DB_URL=postgresql://igor:choose_a_password@127.0.0.1/Igor-wild-0001 \\
        python claudecode/seed_pe_basket_contract.py

Verify:
    Igor: memory_get("tpl-layer4-code-a-ticket-basket")

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
    "postgresql://igor:choose_a_password@127.0.0.1/Igor-wild-0001",
)

TEMPLATE_ID = "tpl-layer4-code-a-ticket-basket"

# ── Basket contract schema ────────────────────────────────────────────────────

BASKET_SCHEMA = {
    "ticket_id": {
        "type": "str",
        "written_by": "ENTRY",
        "source": "TWM active_goal metadata",
        "read_by": ["CLAIM", "READ_TICKET"],
    },
    "ticket_description": {
        "type": "str",
        "written_by": "READ_TICKET",
        "source": "cc_queue ticket details",
        "read_by": ["SITUATE", "HYPOTHESIZE"],
    },
    "plan_files": {
        "type": "list[str]",
        "written_by": "SITUATE",
        "source": "tier.2 call: which files does this ticket touch?",
        "read_by": ["OBSERVE"],
    },
    "line_range": {
        "type": "dict — {file: str, start: int, end: int}",
        "written_by": "OBSERVE pass-1 (grep)",
        "source": "grep_for result — where in the file is the relevant section",
        "read_by": ["OBSERVE pass-2 (read_file)"],
    },
    "actual": {
        "type": "str",
        "written_by": "OBSERVE pass-2 (read_file with offset)",
        "source": "file section identified by line_range — small context, high signal",
        "read_by": ["HYPOTHESIZE"],
    },
    "expected": {
        "type": "str",
        "written_by": "ENTRY (constant)",
        "value": "tests pass, ticket requirements met",
        "read_by": ["OBSERVE (optional baseline for delta)"],
    },
    "hypothesis": {
        "type": "dict — {file: str, old_string: str, new_string: str}",
        "written_by": "HYPOTHESIZE",
        "source": "tier.2 call: given description+actual, what is the exact edit?",
        "read_by": ["IMPLEMENT"],
        "note": "Single edit per call in v1. Expand to list[dict] in later iteration.",
    },
    "test_result": {
        "type": "str — 'pass' | 'fail: <details>'",
        "written_by": "TEST",
        "source": "run_tests() output",
        "read_by": ["BRANCHIF"],
    },
    "attempt_count": {
        "type": "int",
        "written_by": "ENTRY (=0), REPLAN (increment)",
        "source": "loop guard — escalate after 3 failed attempts",
        "read_by": ["BRANCHIF"],
    },
}

TEMPLATE_NODE = {
    "id": TEMPLATE_ID,
    "narrative": (
        "PROC_CODE_A_TICKET basket contract — Layer 4 schema node (T-pe-basket). "
        "Defines the shared Python dict that all coding-sprint engram nodes read "
        "from and emit into. Keys: ticket_id, ticket_description, plan_files, "
        "line_range, actual, expected, hypothesis, test_result, attempt_count. "
        "Basket is shared across forks (concurrent read + emit-back). "
        "No copy-on-fork. Serialization only at async fork boundaries."
    ),
    "memory_type": "PROCEDURAL",
    "source": "user_seeded",
    "confidence": 1.0,
    "context_of_encoding": (
        "T-pe-basket: Layer 4 basket contract for PROC_CODE_A_TICKET coding sprint engram. "
        "Design: 2026-04-02 session. Basket = shared Python dict; forks share parent; "
        "T-basket-fork-sharing captures the full semantics."
    ),
    "metadata": {
        "template": True,
        "schema_node": True,  # pure contract — not executable
        "schema_version": 1,
        "layer": 4,
        "pattern_name": "PROC_CODE_A_TICKET",
        "basket_schema": BASKET_SCHEMA,
        "node_sequence": [
            "ENTRY",
            "CLAIM",
            "READ_TICKET",
            "SITUATE",
            "OBSERVE",  # two-pass: grep → read_file(offset)
            "HYPOTHESIZE",
            "IMPLEMENT",
            "TEST",
            "BRANCHIF",  # pass → COMMIT → CLOSE; fail → REPLAN or ESCALATE
            "REPLAN",  # loops back to OBSERVE on attempt < 3
            "COMMIT",
            "CLOSE",
            "ESCALATE",
        ],
        "llm_calls": ["SITUATE", "HYPOTHESIZE", "REPLAN"],
        "pure_tool_nodes": [
            "ENTRY",
            "CLAIM",
            "READ_TICKET",
            "OBSERVE",
            "IMPLEMENT",
            "TEST",
            "COMMIT",
            "CLOSE",
            "ESCALATE",
        ],
        "tags": [
            "layer4",
            "coding_sprint",
            "basket_contract",
            "proc_code_a_ticket",
            "schema",
        ],
        "inertia": 0.3,
        "why": (
            "The basket contract is the first thing to define before seeding any nodes — "
            "all pe-* nodes reference it. Keeps the shared state schema explicit and "
            "queryable by Igor. Basket is a plain Python dict (not JSON schema) because "
            "the basket lives in memory during execution; the schema node is just the "
            "human/Igor-readable contract, not a runtime enforcer."
        ),
    },
}


# ── Seed function ─────────────────────────────────────────────────────────────


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
            narrative          = EXCLUDED.narrative,
            metadata           = EXCLUDED.metadata,
            updated_at         = EXCLUDED.updated_at
        """,
        (
            TEMPLATE_NODE["id"],
            TEMPLATE_NODE["narrative"],
            TEMPLATE_NODE["memory_type"],
            TEMPLATE_NODE["source"],
            TEMPLATE_NODE["confidence"],
            TEMPLATE_NODE["context_of_encoding"],
            now,
            now,
            json.dumps(TEMPLATE_NODE["metadata"]),
        ),
    )

    conn.commit()
    cur.close()
    conn.close()
    print(f"Seeded schema node: {TEMPLATE_ID}")
    print()
    print("Verify with:")
    print(f"  Igor: memory_get('{TEMPLATE_ID}')")


if __name__ == "__main__":
    seed(DB_URL)
