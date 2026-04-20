#!/usr/bin/env python3
"""
migrate_decisions_to_palace.py — decisions_log.dsb + slug-style decisions → clan.memories.

T-decisions-into-palace-subtree. Shape per shape-lock:
- D### numbered decisions from lab/design_docs_for_igor/decisions_log.dsb
  become REFERENCE rows with metadata.kind='decision'.
- Slug-style decisions (e.g. D-palace-source-of-truth-2026-04-20) are
  synthesized from ticket.decision_id references so the backlink target
  exists in-graph.
- spawned_tickets backlink populated from tickets' decision_id values.
- Palace pointer at theigors/decisions/<id>.

Usage:
    python3 migrate_decisions_to_palace.py --dry-run
    python3 migrate_decisions_to_palace.py
"""

from __future__ import annotations

import argparse
import os
import re
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

import psycopg2
from psycopg2.extras import Json

DECISIONS_DSB = Path(
    os.path.expanduser("~/TheIgors/lab/design_docs_for_igor/decisions_log.dsb")
)

DECISIONS_ROOT_ID = "DECISIONS_ROOT"
DECISIONS_ROOT_PARENT = "PR_IGORS_PROJECT"
PALACE_DECISIONS_PATH = "theigors/decisions"
MIGRATION_SOURCE = "decision-migration-2026-04-20"

D_LINE_RE = re.compile(r"^(D[\w.-]+)\|")


def get_db_url() -> str:
    return os.environ.get(
        "IGOR_HOME_DB_URL",
        "postgresql://igor:choose_a_password@127.0.0.1/Igor-wild-0001",
    )


def ensure_decisions_root(cur, dry_run: bool) -> None:
    cur.execute("SELECT id FROM clan.memories WHERE id = %s", (DECISIONS_ROOT_ID,))
    if cur.fetchone():
        print(f"  {DECISIONS_ROOT_ID} exists")
    else:
        if dry_run:
            print(f"  would create {DECISIONS_ROOT_ID}")
        else:
            cur.execute(
                """
                INSERT INTO clan.memories
                  (id, narrative, memory_type, parent_id, metadata, timestamp,
                   source, scope, confidence)
                VALUES (%s, %s, 'REFERENCE', %s, %s, %s, %s, 'class', 1.0)
                """,
                (
                    DECISIONS_ROOT_ID,
                    "Decisions root — architectural decisions, numbered + slug.",
                    DECISIONS_ROOT_PARENT,
                    Json({"kind": "root", "child_kind": "decision"}),
                    datetime.now(timezone.utc).isoformat(),
                    MIGRATION_SOURCE,
                ),
            )
            print(f"  created {DECISIONS_ROOT_ID}")

    cur.execute(
        "SELECT path FROM clan.memory_palace WHERE path = %s",
        (PALACE_DECISIONS_PATH,),
    )
    if cur.fetchone():
        print(f"  palace {PALACE_DECISIONS_PATH} exists")
    else:
        if dry_run:
            print(f"  would create palace {PALACE_DECISIONS_PATH}")
        else:
            cur.execute(
                """
                INSERT INTO clan.memory_palace
                  (path, parent_path, title, content, pointers, updated_at, updated_by)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    PALACE_DECISIONS_PATH,
                    "theigors",
                    "Decisions — architectural choices",
                    (
                        "Decision rows under DECISIONS_ROOT. D### numbered from "
                        "decisions_log.dsb; slug-style (D-<topic>-<date>) synthesized "
                        "from ticket.decision_id backlinks. decisions_log.dsb is echo."
                    ),
                    Json([f"memories:{DECISIONS_ROOT_ID}"]),
                    datetime.now(timezone.utc).isoformat(),
                    "migrate_decisions_to_palace",
                ),
            )
            print(f"  created palace {PALACE_DECISIONS_PATH}")


def parse_dsb(path: Path) -> list[dict]:
    """Parse decisions_log.dsb → list of decision dicts."""
    out = []
    for raw in path.read_text().splitlines():
        line = raw.rstrip()
        if (
            not line
            or line.startswith("DOC|")
            or line.startswith("META|")
            or line.startswith("---")
        ):
            continue
        if not D_LINE_RE.match(line):
            continue
        parts = line.split("|", 3)
        if len(parts) < 4:
            continue
        did, topic, status, why = parts
        out.append(
            {
                "id": did,
                "topic": topic.strip(),
                "status": status.strip(),
                "why": why.strip(),
                "style": "numbered",
            }
        )
    return out


def fetch_slug_decisions_from_tickets(cur) -> dict[str, list[str]]:
    """Find ticket.decision_id values that are slug-style. Returns {decision_id: [ticket_ids]}."""
    cur.execute("""
        SELECT id, metadata->>'decision_id' as did
        FROM clan.memories
        WHERE parent_id='TICKETS_ROOT' AND metadata->>'decision_id' IS NOT NULL
        """)
    groups: dict[str, list[str]] = defaultdict(list)
    for row in cur.fetchall():
        tid, did = row
        groups[did].append(tid)
    return dict(groups)


def upsert_decision(
    cur, decision: dict, backlinks: list[str], dry_run: bool
) -> tuple[str, str]:
    did = decision["id"]
    palace_path = f"{PALACE_DECISIONS_PATH}/{did}"

    topic = decision.get("topic", did)
    status = decision.get("status", "")
    why = decision.get("why", "")
    narrative_parts = [f"{did} — {topic}."]
    if status:
        narrative_parts.append(f"Status: {status}.")
    if why:
        narrative_parts.append(why)
    narrative = " ".join(narrative_parts)

    metadata = {
        "kind": "decision",
        "decision_id": did,
        "topic": topic,
        "status": status,
        "why": why,
        "style": decision.get("style", "numbered"),
        "spawned_tickets": sorted(backlinks),
    }
    if decision.get("style") == "numbered":
        metadata["origin"] = "decisions_log.dsb"

    cur.execute("SELECT id FROM clan.memories WHERE id = %s", (did,))
    mem_exists = cur.fetchone() is not None
    cur.execute("SELECT path FROM clan.memory_palace WHERE path = %s", (palace_path,))
    palace_exists = cur.fetchone() is not None

    if dry_run:
        return (
            "would_update" if mem_exists else "would_insert",
            "would_update" if palace_exists else "would_insert",
        )

    now = datetime.now(timezone.utc).isoformat()

    if mem_exists:
        cur.execute(
            """
            UPDATE clan.memories
            SET narrative = %s, memory_type = 'REFERENCE', parent_id = %s,
                metadata = %s, source = %s, updated_at = %s, scope = 'class'
            WHERE id = %s
            """,
            (narrative, DECISIONS_ROOT_ID, Json(metadata), MIGRATION_SOURCE, now, did),
        )
        mem_action = "updated"
    else:
        cur.execute(
            """
            INSERT INTO clan.memories
              (id, narrative, memory_type, parent_id, metadata, timestamp,
               source, scope, confidence)
            VALUES (%s, %s, 'REFERENCE', %s, %s, %s, %s, 'class', 1.0)
            """,
            (did, narrative, DECISIONS_ROOT_ID, Json(metadata), now, MIGRATION_SOURCE),
        )
        mem_action = "inserted"

    palace_content = (
        f"Decision {did}: {topic}. Status: {status}. "
        f"Canonical row: clan.memories id={did}. "
        f"Spawned tickets: {len(backlinks)}."
    )
    palace_title = f"{did} — {topic}"[:300]

    if palace_exists:
        cur.execute(
            """
            UPDATE clan.memory_palace
            SET title = %s, content = %s, pointers = %s,
                updated_at = %s, updated_by = 'migrate_decisions_to_palace'
            WHERE path = %s
            """,
            (palace_title, palace_content, Json([f"memories:{did}"]), now, palace_path),
        )
        palace_action = "updated"
    else:
        cur.execute(
            """
            INSERT INTO clan.memory_palace
              (path, parent_path, title, content, pointers, updated_at, updated_by)
            VALUES (%s, %s, %s, %s, %s, %s, 'migrate_decisions_to_palace')
            """,
            (
                palace_path,
                PALACE_DECISIONS_PATH,
                palace_title,
                palace_content,
                Json([f"memories:{did}"]),
                now,
            ),
        )
        palace_action = "inserted"

    return (mem_action, palace_action)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args()

    if not DECISIONS_DSB.exists():
        print(f"Decisions file not found: {DECISIONS_DSB}", file=sys.stderr)
        return 1

    conn = psycopg2.connect(get_db_url())
    try:
        cur = conn.cursor()

        print("=== Roots ===")
        ensure_decisions_root(cur, args.dry_run)
        print()

        numbered = parse_dsb(DECISIONS_DSB)
        print(f"Numbered decisions from dsb: {len(numbered)}")

        slug_backlinks = fetch_slug_decisions_from_tickets(cur)
        slug_only = {
            k: v
            for k, v in slug_backlinks.items()
            if not k.startswith("D0")
            and not k.startswith("D1")
            and not k.startswith("D2")
            and not k.startswith("D3")
            and "-" in k
        }
        print(
            f"Slug-style decisions synthesized from ticket backlinks: {len(slug_only)}"
        )
        print()

        tallies = {"mem": {}, "palace": {}}

        numbered_ids = {d["id"] for d in numbered}
        print("=== Numbered decisions ===")
        for dec in numbered:
            backlinks = slug_backlinks.get(dec["id"], [])
            mem_action, palace_action = upsert_decision(
                cur, dec, backlinks, args.dry_run
            )
            tallies["mem"][mem_action] = tallies["mem"].get(mem_action, 0) + 1
            tallies["palace"][palace_action] = (
                tallies["palace"].get(palace_action, 0) + 1
            )
        print(f"  processed {len(numbered)} numbered decisions")
        print()

        print("=== Slug decisions ===")
        for did, ticket_ids in sorted(slug_only.items()):
            if did in numbered_ids:
                continue
            parts = did.split("-")
            topic = " ".join(parts[1:-3]) if len(parts) >= 4 else did
            synthetic = {
                "id": did,
                "topic": topic,
                "status": "active",
                "why": f"Synthesized from ticket backlinks ({len(ticket_ids)} tickets).",
                "style": "slug",
            }
            mem_action, palace_action = upsert_decision(
                cur, synthetic, ticket_ids, args.dry_run
            )
            tallies["mem"][mem_action] = tallies["mem"].get(mem_action, 0) + 1
            tallies["palace"][palace_action] = (
                tallies["palace"].get(palace_action, 0) + 1
            )
            print(
                f"  {did:50s} memory={mem_action} palace={palace_action} "
                f"tickets={len(ticket_ids)}"
            )
        print()

        print("=== Summary ===")
        print(f"Memory rows:   {dict(tallies['mem'])}")
        print(f"Palace nodes:  {dict(tallies['palace'])}")

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
