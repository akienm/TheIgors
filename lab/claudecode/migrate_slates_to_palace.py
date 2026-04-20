#!/usr/bin/env python3
"""
migrate_slates_to_palace.py — one-shot: slate.txt files → clan.memories + memory_palace.

T-slates-into-palace-subtree. Shape per lab/design_docs/palace_migration/shape_lock_2026-04-20.md:
- Each slate becomes a REFERENCE memory row with metadata.kind='slate',
  parent_id=SLATES_ROOT, metadata.date=YYYY-MM-DD, metadata.sections parsed
  best-effort from ## headers
- Palace node at theigors/slates/YYYYMMDD points at the memories row
- SLATES_ROOT created under PR_IGORS_PROJECT if absent
- Idempotent: re-running upserts rather than duplicating

Usage:
    python3 migrate_slates_to_palace.py --dry-run
    python3 migrate_slates_to_palace.py
"""

from __future__ import annotations

import argparse
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

import psycopg2
from psycopg2.extras import Json

SLATES_DIR = Path(os.path.expanduser("~/.TheIgors/claudecode"))
SLATE_FILE_RE = re.compile(r"^(\d{8})\.slate\.txt$")

SLATES_ROOT_ID = "SLATES_ROOT"
SLATES_ROOT_PARENT = "PR_IGORS_PROJECT"
PALACE_SLATES_PATH = "theigors/slates"
MIGRATION_SOURCE = "slate-migration-2026-04-20"


def get_db_url() -> str:
    return os.environ.get(
        "IGOR_HOME_DB_URL",
        "postgresql://igor:choose_a_password@127.0.0.1/Igor-wild-0001",
    )


def parse_sections(content: str) -> dict:
    """Split markdown into {section_name: [line, line, ...]} by ## headers."""
    sections: dict[str, list[str]] = {}
    current_name: str | None = None
    current_body: list[str] = []
    for line in content.splitlines():
        m = re.match(r"^##\s+(.+?)\s*$", line)
        if m:
            if current_name is not None:
                sections[current_name] = current_body
            current_name = m.group(1)
            current_body = []
        else:
            if current_name is not None:
                current_body.append(line)
    if current_name is not None:
        sections[current_name] = current_body
    return {k: [l for l in v if l.strip()] for k, v in sections.items()}


def ensure_slates_root(cur, dry_run: bool) -> None:
    cur.execute("SELECT id FROM clan.memories WHERE id = %s", (SLATES_ROOT_ID,))
    if cur.fetchone():
        print(f"  {SLATES_ROOT_ID} exists")
    else:
        if dry_run:
            print(f"  would create {SLATES_ROOT_ID}")
        else:
            cur.execute(
                """
                INSERT INTO clan.memories
                  (id, narrative, memory_type, parent_id, metadata, timestamp,
                   source, scope, confidence)
                VALUES (%s, %s, 'REFERENCE', %s, %s, %s, %s, 'class', 1.0)
                """,
                (
                    SLATES_ROOT_ID,
                    "Slates root — daily planning slates, one row per day.",
                    SLATES_ROOT_PARENT,
                    Json({"kind": "root", "child_kind": "slate"}),
                    datetime.now(timezone.utc).isoformat(),
                    MIGRATION_SOURCE,
                ),
            )
            print(f"  created {SLATES_ROOT_ID}")

    cur.execute(
        "SELECT path FROM clan.memory_palace WHERE path = %s", (PALACE_SLATES_PATH,)
    )
    if cur.fetchone():
        print(f"  palace {PALACE_SLATES_PATH} exists")
    else:
        if dry_run:
            print(f"  would create palace {PALACE_SLATES_PATH}")
        else:
            cur.execute(
                """
                INSERT INTO clan.memory_palace
                  (path, parent_path, title, content, pointers, updated_at, updated_by)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    PALACE_SLATES_PATH,
                    "theigors",
                    "Slates — daily planning",
                    (
                        "Daily slate rows under SLATES_ROOT in clan.memories. "
                        "Individual slate pointers at theigors/slates/YYYYMMDD. "
                        "Canonical content (full markdown + parsed sections) lives in memories; "
                        "text-file echo at ~/.TheIgors/claudecode/YYYYMMDD.slate.txt is hand-edited."
                    ),
                    Json([f"memories:{SLATES_ROOT_ID}"]),
                    datetime.now(timezone.utc).isoformat(),
                    "migrate_slates_to_palace",
                ),
            )
            print(f"  created palace {PALACE_SLATES_PATH}")


def upsert_slate(cur, path: Path, dry_run: bool) -> tuple[str, str]:
    """Upsert one slate file → clan.memories + palace pointer. Returns (mem_action, palace_action)."""
    m = SLATE_FILE_RE.match(path.name)
    if not m:
        return ("skipped", "skipped")
    yyyymmdd = m.group(1)
    date_iso = f"{yyyymmdd[:4]}-{yyyymmdd[4:6]}-{yyyymmdd[6:8]}"
    slate_id = f"SLATE-{yyyymmdd}"
    palace_path = f"{PALACE_SLATES_PATH}/{yyyymmdd}"

    content = path.read_text()
    sections = parse_sections(content)
    first_line = content.splitlines()[0] if content.splitlines() else ""
    title = first_line.lstrip("# ").strip() or f"Slate {date_iso}"

    metadata = {
        "kind": "slate",
        "date": date_iso,
        "sections": sections,
        "origin_path": str(path),
        "byte_size": len(content),
    }

    cur.execute("SELECT id FROM clan.memories WHERE id = %s", (slate_id,))
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
            (content, SLATES_ROOT_ID, Json(metadata), MIGRATION_SOURCE, now, slate_id),
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
            (
                slate_id,
                content,
                SLATES_ROOT_ID,
                Json(metadata),
                date_iso,
                MIGRATION_SOURCE,
            ),
        )
        mem_action = "inserted"

    palace_content = (
        f"Slate for {date_iso}. Canonical row: clan.memories id={slate_id}. "
        f"Sections: {', '.join(sections.keys()) or '(none)'}."
    )
    if palace_exists:
        cur.execute(
            """
            UPDATE clan.memory_palace
            SET title = %s, content = %s, pointers = %s,
                updated_at = %s, updated_by = 'migrate_slates_to_palace'
            WHERE path = %s
            """,
            (
                title[:300],
                palace_content,
                Json([f"memories:{slate_id}"]),
                now,
                palace_path,
            ),
        )
        palace_action = "updated"
    else:
        cur.execute(
            """
            INSERT INTO clan.memory_palace
              (path, parent_path, title, content, pointers, updated_at, updated_by)
            VALUES (%s, %s, %s, %s, %s, %s, 'migrate_slates_to_palace')
            """,
            (
                palace_path,
                PALACE_SLATES_PATH,
                title[:300],
                palace_content,
                Json([f"memories:{slate_id}"]),
                now,
            ),
        )
        palace_action = "inserted"

    return (mem_action, palace_action)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args()

    if not SLATES_DIR.exists():
        print(f"Slates dir not found: {SLATES_DIR}", file=sys.stderr)
        return 1

    slates = sorted(p for p in SLATES_DIR.iterdir() if SLATE_FILE_RE.match(p.name))
    print(f"Slates dir: {SLATES_DIR}")
    print(f"Slate files: {len(slates)}")
    print(f"Mode: {'DRY RUN' if args.dry_run else 'LIVE'}")
    print()

    conn = psycopg2.connect(get_db_url())
    try:
        cur = conn.cursor()
        print("=== Roots ===")
        ensure_slates_root(cur, args.dry_run)
        print()
        print("=== Slates ===")
        tallies = {
            "mem": {"inserted": 0, "updated": 0, "would_insert": 0, "would_update": 0},
            "palace": {
                "inserted": 0,
                "updated": 0,
                "would_insert": 0,
                "would_update": 0,
            },
        }
        for path in slates:
            mem_action, palace_action = upsert_slate(cur, path, args.dry_run)
            tallies["mem"][mem_action] = tallies["mem"].get(mem_action, 0) + 1
            tallies["palace"][palace_action] = (
                tallies["palace"].get(palace_action, 0) + 1
            )
            print(f"  {path.name:30s} memory={mem_action} palace={palace_action}")
        print()
        print("=== Summary ===")
        print(f"Memory rows:  {dict(tallies['mem'])}")
        print(f"Palace nodes: {dict(tallies['palace'])}")

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
