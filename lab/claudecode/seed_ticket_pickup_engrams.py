#!/usr/bin/env python3
"""
seed_ticket_pickup_engrams.py — T-retire-worker-foreman Phase A.

Seeds the biomimetic replacement for worker_foreman's konsole-spawn
pattern. Two engram nodes that, when wired to a boredom trigger, let
Igor pick up the next ticket himself and run pe_chain in-process —
no separate CC worker session, no polling daemon.

## Chain

  BOREDOM (ambient) → ENGRAM_TICKET_PICKUP_SCAN → ENGRAM_TICKET_PICKUP_ADOPT
                                                   → ENGRAM_CODE_INIT (existing)
                                                     → pe_chain runs

## What this script does (Phase A)

Creates two engram nodes in the memories table. Does NOT yet wire them
to a boredom trigger or retire any existing worker_foreman tools. That
flip is Phase B:

  1. Flip PROC_WORKER_FOREMAN (currently triggered by 'worker_done') or
     a new BOREDOM-triggered habit to point at ENGRAM_TICKET_PICKUP_SCAN
     instead of worker_foreman:launch_next_worker.
  2. Stop worker_daemon.sh (remove from startup).
  3. Once Phase B is stable, delete worker_foreman.py +
     worker_daemon.sh + the old PROC_* habits.

## Safe to run

Phase A is purely additive — Akien can run this multiple times. The
engrams won't fire on their own until a habit or trigger is explicitly
pointed at ENGRAM_TICKET_PICKUP_SCAN.

Restore command: python3 lab/claudecode/seed_ticket_pickup_engrams.py
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(_REPO))
sys.path.insert(0, str(_REPO / "wild_igor"))

DB_URL = os.environ.get(
    "IGOR_HOME_DB_URL",
    "postgresql://igor:choose_a_password@127.0.0.1/Igor-wild-0001",
)


# Payload cells follow the coding-engram pattern (see seed_coding_engrams.py):
#   ["MCPCALL", tool_name, basket_key_with_args, result_key_in_basket]
#   ["BRANCHIF", condition, target_node_id]
#
# Condition semantics: truthy values in the basket fire the branch. For the
# SCAN engram we want "pending > 0" — the MCPCALL stores
# "pending=N" as basket['scan_result'], and a Python expression check would
# normally evaluate pending>0. For simplicity here we use a literal True
# BRANCHIF and let the downstream ADOPT engram handle the "no pending"
# path by returning harmlessly. If you want crisper short-circuit later,
# swap the BRANCHIF condition to something like
#   ["BRANCHIF", "pending!=0", "ENGRAM_TICKET_PICKUP_ADOPT"]
# once node_executor supports basket-key comparisons in conditions.

PICKUP_CHAIN = [
    {
        "id": "ENGRAM_TICKET_PICKUP_SCAN",
        "narrative": (
            "When idle and wondering what to pick up next — 'pick up next "
            "ticket', 'pending work', 'what's next in the queue', 'start "
            "the queue', 'anything pending', 'what should I be working on' "
            "— I check the task queue for pending work. Deposits 'pending=N' "
            "into the basket and branches into ENGRAM_TICKET_PICKUP_ADOPT "
            "so I pick one up myself in-process. This is the biomimetic "
            "replacement for worker_foreman's konsole-spawn pattern: no "
            "separate CC worker session, no polling daemon — just engrams "
            "chaining under boredom or direct invocation."
        ),
        "tool_name": "queue_pending_count",
        "next_id": "ENGRAM_TICKET_PICKUP_ADOPT",
    },
    {
        "id": "ENGRAM_TICKET_PICKUP_ADOPT",
        "narrative": (
            "When a pickup scan has deposited pending>0 into the basket, "
            "I adopt the next-best pending ticket as an active goal using "
            "weighted_ticket_score and goal_adopt, then branch into "
            "ENGRAM_CODE_INIT so pe_chain runs in-process. No konsole "
            "spawn; I do the work myself. Triggered phrases: 'adopt next "
            "ticket', 'claim a ticket', 'pick up a ticket'."
        ),
        "tool_name": "adopt_next_ticket",
        "next_id": "ENGRAM_CODE_INIT",
    },
]


def seed(dry_run: bool = False):
    import psycopg2

    conn = psycopg2.connect(DB_URL)
    cur = conn.cursor()
    cur.execute("SET search_path TO instance, clan, infra, public")

    for step in PICKUP_CHAIN:
        payload_cells = [
            ["MCPCALL", step["tool_name"], "_basket_args", "_scan_result"],
            ["BRANCHIF", True, step["next_id"]],
        ]
        metadata = {
            "habit_type": "engram",
            "inertia": 0.3,
            "pickup_chain": True,
            "code_ref": f"tools.worker_foreman:{step['tool_name']}",
            "triggers": {"__entry__": "ticket pickup entry"},
            "retires": "worker_foreman.launch_next_worker",
            "ticket": "T-retire-worker-foreman",
        }
        payload = {"cells": payload_cells}

        if dry_run:
            print(f"  [dry-run] {step['id']} → {step['next_id']}")
            print(f"            payload: {json.dumps(payload_cells)}")
            continue

        cur.execute(
            """
            INSERT INTO memories (id, narrative, memory_type, parent_id, source, confidence,
                                  metadata, payload, scope)
            VALUES (%s, %s, 'PROCEDURAL', 'CP1', 'seed_ticket_pickup', 1.0, %s, %s, 'class')
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
        print(f"  Seeded {step['id']} → {step['next_id']}")

    if not dry_run:
        conn.commit()
    conn.close()


def main():
    import argparse

    p = argparse.ArgumentParser()
    p.add_argument("--dry-run", action="store_true", help="Show plan, don't write")
    args = p.parse_args()
    seed(dry_run=args.dry_run)
    print(
        "seed_ticket_pickup_engrams: Phase A complete. "
        "Chain is in the graph but not wired to any trigger. "
        "Phase B: point a BOREDOM habit at ENGRAM_TICKET_PICKUP_SCAN."
    )


if __name__ == "__main__":
    main()
