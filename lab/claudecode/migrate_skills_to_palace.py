#!/usr/bin/env python3
"""
migrate_skills_to_palace.py — active skills → clan.memories + memory_palace + cc_skills sync.

T-skills-into-palace-subtree. Shape per lab/design_docs/palace_migration/shape_lock_2026-04-20.md
plus acceptance addition requiring cc_skills to stay fully-populated as a git-resident
bootstrap set.

- Active copy (~/.claude/skills/<name>/SKILL.md) is canonical input.
- Migrates each active skill to a PROCEDURAL row under SKILLS_ROOT with
  metadata.habit_type='skill', frontmatter fields in metadata.
- Palace pointer at theigors/skills/<name>.
- Syncs active → cc_skills so lab/claudecode/cc_skills/<name>/SKILL.md is
  a byte-identical copy (ensures fresh-box bootstrap has current skill set).

Usage:
    python3 migrate_skills_to_palace.py --dry-run
    python3 migrate_skills_to_palace.py
"""

from __future__ import annotations

import argparse
import os
import re
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

import psycopg2
from psycopg2.extras import Json

ACTIVE_SKILLS_DIR = Path(os.path.expanduser("~/.claude/skills"))
CC_SKILLS_DIR = Path(os.path.expanduser("~/TheIgors/lab/claudecode/cc_skills"))

SKILLS_ROOT_ID = "SKILLS_ROOT"
SKILLS_ROOT_PARENT = "PR_IGORS_PROJECT"
PALACE_SKILLS_PATH = "theigors/skills"
MIGRATION_SOURCE = "skill-migration-2026-04-20"


def get_db_url() -> str:
    return os.environ.get(
        "IGOR_HOME_DB_URL",
        "postgresql://igor:choose_a_password@127.0.0.1/Igor-wild-0001",
    )


def parse_frontmatter(text: str) -> tuple[dict, str]:
    """Split YAML frontmatter (---...---) from body. Returns (fm_dict, body)."""
    if not text.startswith("---\n"):
        return ({}, text)
    end = text.find("\n---\n", 4)
    if end < 0:
        return ({}, text)
    fm_raw = text[4:end]
    body = text[end + 5 :]
    fm = {}
    for line in fm_raw.splitlines():
        if not line.strip() or line.startswith("#"):
            continue
        m = re.match(r"^(\w+):\s*(.*)$", line)
        if m:
            fm[m.group(1)] = m.group(2).strip()
    return (fm, body)


def ensure_skills_root(cur, dry_run: bool) -> None:
    cur.execute("SELECT id FROM clan.memories WHERE id = %s", (SKILLS_ROOT_ID,))
    if cur.fetchone():
        print(f"  {SKILLS_ROOT_ID} exists")
    else:
        if dry_run:
            print(f"  would create {SKILLS_ROOT_ID}")
        else:
            cur.execute(
                """
                INSERT INTO clan.memories
                  (id, narrative, memory_type, parent_id, metadata, timestamp,
                   source, scope, confidence)
                VALUES (%s, %s, 'PROCEDURAL', %s, %s, %s, %s, 'class', 1.0)
                """,
                (
                    SKILLS_ROOT_ID,
                    "Skills root — CC slash-commands stored as PROCEDURAL memories.",
                    SKILLS_ROOT_PARENT,
                    Json(
                        {"kind": "root", "child_kind": "skill", "habit_type": "skill"}
                    ),
                    datetime.now(timezone.utc).isoformat(),
                    MIGRATION_SOURCE,
                ),
            )
            print(f"  created {SKILLS_ROOT_ID}")

    cur.execute(
        "SELECT path FROM clan.memory_palace WHERE path = %s", (PALACE_SKILLS_PATH,)
    )
    if cur.fetchone():
        print(f"  palace {PALACE_SKILLS_PATH} exists")
    else:
        if dry_run:
            print(f"  would create palace {PALACE_SKILLS_PATH}")
        else:
            cur.execute(
                """
                INSERT INTO clan.memory_palace
                  (path, parent_path, title, content, pointers, updated_at, updated_by)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    PALACE_SKILLS_PATH,
                    "theigors",
                    "Skills — CC slash-commands",
                    (
                        "Skill memory rows under SKILLS_ROOT. Active copy at "
                        "~/.claude/skills/<name>/SKILL.md is canonical input; "
                        "cc_skills/ mirror is bootstrap set for fresh boxes."
                    ),
                    Json([f"memories:{SKILLS_ROOT_ID}"]),
                    datetime.now(timezone.utc).isoformat(),
                    "migrate_skills_to_palace",
                ),
            )
            print(f"  created palace {PALACE_SKILLS_PATH}")


def upsert_skill(cur, skill_dir: Path, dry_run: bool) -> tuple[str, str, str]:
    """Upsert one skill. Returns (mem_action, palace_action, cc_skills_action)."""
    name = skill_dir.name
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.exists():
        return ("skipped", "skipped", "skipped")

    text = skill_md.read_text()
    fm, body = parse_frontmatter(text)
    skill_id = f"SKILL-{name}"
    palace_path = f"{PALACE_SKILLS_PATH}/{name}"

    description = fm.get("description", "")
    narrative = f"Skill /{name}. {description}"

    metadata = {
        "kind": "skill",
        "habit_type": "skill",
        "name": name,
        "description": description,
        "model": fm.get("model"),
        "model_exception": fm.get("model_exception"),
        "origin_path": str(skill_md),
        "byte_size": len(text),
    }

    cur.execute("SELECT id FROM clan.memories WHERE id = %s", (skill_id,))
    mem_exists = cur.fetchone() is not None
    cur.execute("SELECT path FROM clan.memory_palace WHERE path = %s", (palace_path,))
    palace_exists = cur.fetchone() is not None

    target_cc_skill = CC_SKILLS_DIR / name / "SKILL.md"
    current_cc_content = (
        target_cc_skill.read_text() if target_cc_skill.exists() else None
    )
    if current_cc_content == text:
        cc_action = "match"
    elif current_cc_content is None:
        cc_action = "would_create" if dry_run else "created"
    else:
        cc_action = "would_sync" if dry_run else "synced"

    if dry_run:
        return (
            "would_update" if mem_exists else "would_insert",
            "would_update" if palace_exists else "would_insert",
            cc_action,
        )

    now = datetime.now(timezone.utc).isoformat()

    if mem_exists:
        cur.execute(
            """
            UPDATE clan.memories
            SET narrative = %s, memory_type = 'PROCEDURAL', parent_id = %s,
                metadata = %s, payload = %s, source = %s, updated_at = %s, scope = 'class'
            WHERE id = %s
            """,
            (
                narrative,
                SKILLS_ROOT_ID,
                Json(metadata),
                text,
                MIGRATION_SOURCE,
                now,
                skill_id,
            ),
        )
        mem_action = "updated"
    else:
        cur.execute(
            """
            INSERT INTO clan.memories
              (id, narrative, memory_type, parent_id, metadata, payload, timestamp,
               source, scope, confidence)
            VALUES (%s, %s, 'PROCEDURAL', %s, %s, %s, %s, %s, 'class', 1.0)
            """,
            (
                skill_id,
                narrative,
                SKILLS_ROOT_ID,
                Json(metadata),
                text,
                now,
                MIGRATION_SOURCE,
            ),
        )
        mem_action = "inserted"

    palace_content = (
        f"Skill /{name}. Canonical row: clan.memories id={skill_id}. "
        f"Active file: {skill_md}. Description: {description[:200]}"
    )
    if palace_exists:
        cur.execute(
            """
            UPDATE clan.memory_palace
            SET title = %s, content = %s, pointers = %s,
                updated_at = %s, updated_by = 'migrate_skills_to_palace'
            WHERE path = %s
            """,
            (
                f"/{name}",
                palace_content,
                Json([f"memories:{skill_id}"]),
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
            VALUES (%s, %s, %s, %s, %s, %s, 'migrate_skills_to_palace')
            """,
            (
                palace_path,
                PALACE_SKILLS_PATH,
                f"/{name}",
                palace_content,
                Json([f"memories:{skill_id}"]),
                now,
            ),
        )
        palace_action = "inserted"

    if cc_action in ("created", "synced"):
        target_cc_skill.parent.mkdir(parents=True, exist_ok=True)
        target_cc_skill.write_text(text)

    return (mem_action, palace_action, cc_action)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args()

    if not ACTIVE_SKILLS_DIR.exists():
        print(f"Active skills dir missing: {ACTIVE_SKILLS_DIR}", file=sys.stderr)
        return 1

    skills = sorted(d for d in ACTIVE_SKILLS_DIR.iterdir() if d.is_dir())
    print(f"Active skills dir: {ACTIVE_SKILLS_DIR}")
    print(f"cc_skills dir:     {CC_SKILLS_DIR}")
    print(f"Skills: {len(skills)}")
    print(f"Mode: {'DRY RUN' if args.dry_run else 'LIVE'}")
    print()

    conn = psycopg2.connect(get_db_url())
    try:
        cur = conn.cursor()
        print("=== Roots ===")
        ensure_skills_root(cur, args.dry_run)
        print()
        print("=== Skills ===")
        tallies = {"mem": {}, "palace": {}, "cc_skills": {}}
        for d in skills:
            mem_action, palace_action, cc_action = upsert_skill(cur, d, args.dry_run)
            tallies["mem"][mem_action] = tallies["mem"].get(mem_action, 0) + 1
            tallies["palace"][palace_action] = (
                tallies["palace"].get(palace_action, 0) + 1
            )
            tallies["cc_skills"][cc_action] = tallies["cc_skills"].get(cc_action, 0) + 1
            print(
                f"  {d.name:25s} memory={mem_action:14s} "
                f"palace={palace_action:14s} cc_skills={cc_action}"
            )
        print()
        print("=== Summary ===")
        print(f"Memory rows:       {dict(tallies['mem'])}")
        print(f"Palace nodes:      {dict(tallies['palace'])}")
        print(f"cc_skills sync:    {dict(tallies['cc_skills'])}")

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
