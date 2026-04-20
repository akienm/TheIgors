#!/usr/bin/env python3
"""
migrate_tickets_to_palace.py — one-shot: queue.json → clan.memories + memory_palace.

T-tickets-into-palace-subtree. Shape per lab/design_docs/palace_migration/shape_lock_2026-04-20.md:
- Each ticket becomes a FACTUAL memory row with metadata.kind='ticket', parent_id=TICKETS_ROOT
- Palace node at theigors/tickets/<id> points at the memories row (status-free, so state
  transitions don't churn palace diffs)
- TICKETS_ROOT created under PR_IGORS_PROJECT if absent
- Idempotent: re-running upserts rather than duplicating

Usage:
    python3 migrate_tickets_to_palace.py --dry-run    # print what would happen
    python3 migrate_tickets_to_palace.py              # live run
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import psycopg2
from psycopg2.extras import Json

QUEUE_PATH = Path(os.path.expanduser("~/.TheIgors/cc_channel/queue.json"))

TICKETS_ROOT_ID = "TICKETS_ROOT"
TICKETS_ROOT_PARENT = "PR_IGORS_PROJECT"
PALACE_TICKETS_PATH = "theigors/tickets"
MIGRATION_SOURCE = "ticket-migration-2026-04-20"


def get_db_url() -> str:
    return os.environ.get(
        "IGOR_HOME_DB_URL",
        "postgresql://igor:choose_a_password@127.0.0.1/Igor-wild-0001",
    )


def build_narrative(t: dict) -> str:
    """Narrative = title + description (both GIN-searchable)."""
    title = t.get("title", "").strip()
    desc = (t.get("description") or t.get("body") or "").strip()
    if desc:
        return f"{title}\n\n{desc}"
    return title


def build_metadata(t: dict) -> dict:
    """Preserve ALL ticket fields (not just canonical 15) into metadata.

    kind='ticket' is the discriminator. Everything else is as-is.
    """
    md = dict(t)
    md["kind"] = "ticket"
    return md


def ensure_tickets_root(cur, dry_run: bool) -> None:
    """Create TICKETS_ROOT memory row + theigors/tickets palace node if absent."""
    cur.execute("SELECT id FROM clan.memories WHERE id = %s", (TICKETS_ROOT_ID,))
    if cur.fetchone():
        print(f"  TICKETS_ROOT exists")
    else:
        if dry_run:
            print(f"  would create TICKETS_ROOT (parent={TICKETS_ROOT_PARENT})")
        else:
            cur.execute(
                """
                INSERT INTO clan.memories
                  (id, narrative, memory_type, parent_id, metadata, timestamp,
                   source, scope, confidence)
                VALUES (%s, %s, 'REFERENCE', %s, %s, %s, %s, 'class', 1.0)
                """,
                (
                    TICKETS_ROOT_ID,
                    "Tickets root — all cc_queue tickets live under this node.",
                    TICKETS_ROOT_PARENT,
                    Json({"kind": "root", "child_kind": "ticket"}),
                    datetime.now(timezone.utc).isoformat(),
                    MIGRATION_SOURCE,
                ),
            )
            print(f"  created TICKETS_ROOT")

    cur.execute(
        "SELECT path FROM clan.memory_palace WHERE path = %s",
        (PALACE_TICKETS_PATH,),
    )
    if cur.fetchone():
        print(f"  palace {PALACE_TICKETS_PATH} exists")
    else:
        if dry_run:
            print(f"  would create palace node {PALACE_TICKETS_PATH}")
        else:
            cur.execute(
                """
                INSERT INTO clan.memory_palace
                  (path, parent_path, title, content, pointers, updated_at, updated_by)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    PALACE_TICKETS_PATH,
                    "theigors",
                    "Tickets — cc_queue canonical storage",
                    (
                        "All tickets are FACTUAL memory rows with parent_id=TICKETS_ROOT. "
                        "Individual ticket palace nodes under this path are stable pointers — "
                        "mutable state (status/result/timestamps) lives only in clan.memories."
                    ),
                    Json([f"memories:{TICKETS_ROOT_ID}"]),
                    datetime.now(timezone.utc).isoformat(),
                    "migrate_tickets_to_palace",
                ),
            )
            print(f"  created palace node {PALACE_TICKETS_PATH}")


def upsert_ticket_memory(cur, t: dict, dry_run: bool) -> str:
    """Upsert one ticket → clan.memories. Returns action taken."""
    tid = t["id"]
    narrative = build_narrative(t)
    metadata = build_metadata(t)
    ts = (
        t.get("created_at")
        or t.get("created")
        or datetime.now(timezone.utc).isoformat()
    )

    cur.execute("SELECT id FROM clan.memories WHERE id = %s", (tid,))
    exists = cur.fetchone() is not None

    if dry_run:
        return "would_update" if exists else "would_insert"

    if exists:
        cur.execute(
            """
            UPDATE clan.memories
            SET narrative = %s,
                memory_type = 'FACTUAL',
                parent_id = %s,
                metadata = %s,
                source = %s,
                updated_at = %s,
                scope = 'class'
            WHERE id = %s
            """,
            (
                narrative,
                TICKETS_ROOT_ID,
                Json(metadata),
                MIGRATION_SOURCE,
                datetime.now(timezone.utc).isoformat(),
                tid,
            ),
        )
        return "updated"
    else:
        cur.execute(
            """
            INSERT INTO clan.memories
              (id, narrative, memory_type, parent_id, metadata, timestamp,
               source, scope, confidence)
            VALUES (%s, %s, 'FACTUAL', %s, %s, %s, %s, 'class', 1.0)
            """,
            (
                tid,
                narrative,
                TICKETS_ROOT_ID,
                Json(metadata),
                ts,
                MIGRATION_SOURCE,
            ),
        )
        return "inserted"


def upsert_ticket_palace(cur, t: dict, dry_run: bool) -> str:
    """Upsert one palace pointer node at theigors/tickets/<id>."""
    tid = t["id"]
    path = f"{PALACE_TICKETS_PATH}/{tid}"
    title = t.get("title") or tid
    size = t.get("size") or "?"
    tags = t.get("tags") or []
    decision = t.get("decision_id")
    content_parts = [f"Ticket `{tid}`. Size {size}."]
    if tags:
        content_parts.append(f"Tags: {', '.join(tags)}.")
    if decision:
        content_parts.append(f"Decision: {decision}.")
    content_parts.append(
        "Canonical row: `clan.memories` where id=<this ticket id>. "
        "Mutable state (status, result, timestamps) lives there, not here."
    )
    content = " ".join(content_parts)

    cur.execute("SELECT path FROM clan.memory_palace WHERE path = %s", (path,))
    exists = cur.fetchone() is not None

    if dry_run:
        return "would_update" if exists else "would_insert"

    if exists:
        cur.execute(
            """
            UPDATE clan.memory_palace
            SET title = %s,
                content = %s,
                pointers = %s,
                updated_at = %s,
                updated_by = 'migrate_tickets_to_palace'
            WHERE path = %s
            """,
            (
                title[:300],
                content,
                Json([f"memories:{tid}"]),
                datetime.now(timezone.utc).isoformat(),
                path,
            ),
        )
        return "updated"
    else:
        cur.execute(
            """
            INSERT INTO clan.memory_palace
              (path, parent_path, title, content, pointers, updated_at, updated_by)
            VALUES (%s, %s, %s, %s, %s, %s, 'migrate_tickets_to_palace')
            """,
            (
                path,
                PALACE_TICKETS_PATH,
                title[:300],
                content,
                Json([f"memories:{tid}"]),
                datetime.now(timezone.utc).isoformat(),
            ),
        )
        return "inserted"


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--limit", type=int, default=None, help="migrate at most N tickets")
    args = p.parse_args()

    if not QUEUE_PATH.exists():
        print(f"Queue file not found: {QUEUE_PATH}", file=sys.stderr)
        return 1

    with open(QUEUE_PATH) as f:
        tickets = json.load(f)

    if args.limit:
        tickets = tickets[: args.limit]

    print(f"Source: {QUEUE_PATH}")
    print(f"Tickets: {len(tickets)}")
    print(f"Mode: {'DRY RUN' if args.dry_run else 'LIVE'}")
    print()

    conn = psycopg2.connect(get_db_url())
    try:
        cur = conn.cursor()

        print("=== Roots ===")
        ensure_tickets_root(cur, args.dry_run)
        print()

        print("=== Tickets ===")
        actions = {"inserted": 0, "updated": 0, "would_insert": 0, "would_update": 0}
        palace_actions = {
            "inserted": 0,
            "updated": 0,
            "would_insert": 0,
            "would_update": 0,
        }

        for i, t in enumerate(tickets):
            if not t.get("id"):
                print(f"  skip (no id): index {i}")
                continue
            mem_action = upsert_ticket_memory(cur, t, args.dry_run)
            palace_action = upsert_ticket_palace(cur, t, args.dry_run)
            actions[mem_action] += 1
            palace_actions[palace_action] += 1

            if i < 5 or i == len(tickets) - 1:
                print(
                    f"  [{i + 1:4d}/{len(tickets)}] {t['id']:40s} "
                    f"memory={mem_action} palace={palace_action}"
                )

        print()
        print("=== Summary ===")
        print(f"Memory rows:   {dict(actions)}")
        print(f"Palace nodes:  {dict(palace_actions)}")

        if args.dry_run:
            conn.rollback()
            print("\n(dry run — rolled back)")
        else:
            conn.commit()
            print("\n(committed)")

    finally:
        conn.close()

    return 0


if __name__ == "__main__":
    sys.exit(main())
