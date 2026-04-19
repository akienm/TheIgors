#!/usr/bin/env python3
"""seed_subsystem_index.py — T-docs-live-in-code / T-versioned-seed-config.

Reads lab/seed/subsystem_index.yaml and upserts each entry into Igor's
memory_palace as a node at path theigors/subsystem_index/<subsystem>.

Pattern: file → DB (hand-curated; DB is runtime cache). CC queries the
palace at context-load to find which subsystem lives in which file, then
reads the file's top-of-file docstring before editing.

Idempotent: re-running overwrites content on the same path.
Restore: python3 lab/claudecode/seed_subsystem_index.py
Versioning: git log lab/seed/subsystem_index.yaml
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parent.parent.parent
_SEED_YAML = _REPO / "lab" / "seed" / "subsystem_index.yaml"


_UPSERT_SQL = """
INSERT INTO memory_palace (path, title, content, pointers)
VALUES (%s, %s, %s, %s)
ON CONFLICT (path) DO UPDATE SET
    title    = EXCLUDED.title,
    content  = EXCLUDED.content,
    pointers = EXCLUDED.pointers
"""

_ROOT_SQL = """
INSERT INTO memory_palace (path, title, content, pointers)
VALUES ('theigors/subsystem_index', 'Subsystem index — where is X documented?',
        'Each child node names a load-bearing subsystem and points at the primary '
        'code file whose top-of-file docstring is canonical for that subsystem. '
        'CC queries children here before surgery to locate authoritative docs.', %s)
ON CONFLICT (path) DO UPDATE SET
    content  = EXCLUDED.content,
    pointers = EXCLUDED.pointers
"""


def _format_content(entry: dict) -> str:
    parts: list[str] = [entry.get("summary", "")]
    pf = entry.get("primary_file") or ""
    if pf:
        parts.append(
            f"Primary file: {pf} — read its top-of-file docstring for the canonical explanation."
        )
    else:
        parts.append(
            "Primary file: (not yet established — docstring to be written during current sprint)"
        )
    also = entry.get("also_see") or []
    if also:
        parts.append("Also see: " + ", ".join(also))
    engrams = entry.get("engrams") or []
    if engrams:
        parts.append("Participating engrams: " + ", ".join(engrams))
    decisions = entry.get("decisions") or []
    if decisions:
        parts.append("Shaped by decisions: " + ", ".join(decisions))
    return "\n\n".join(p for p in parts if p)


def _format_pointers(entry: dict) -> list[str]:
    pts: list[str] = []
    pf = entry.get("primary_file") or ""
    if pf:
        pts.append(pf)
    for f in entry.get("also_see") or []:
        if f and f != pf:
            pts.append(f)
    return pts


def seed(db_url: str) -> dict:
    import psycopg2
    import yaml

    spec = yaml.safe_load(_SEED_YAML.read_text())
    subsystems = spec.get("subsystems", [])

    conn = psycopg2.connect(db_url)
    inserted = 0
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute("SET search_path TO clan,infra,public")
                # Root node listing the subsystems
                root_pts = [s["subsystem"] for s in subsystems]
                cur.execute(_ROOT_SQL, (json.dumps(root_pts),))
                for entry in subsystems:
                    path = f"theigors/subsystem_index/{entry['subsystem']}"
                    title = f"{entry['subsystem']} — {entry.get('summary', '')[:70]}"
                    content = _format_content(entry)
                    pointers = _format_pointers(entry)
                    cur.execute(
                        _UPSERT_SQL,
                        (path, title, content, json.dumps(pointers)),
                    )
                    inserted += 1
    finally:
        conn.close()

    return {"upserted": inserted, "source": f"yaml:{_SEED_YAML.name}"}


def main():
    db_url = os.getenv(
        "IGOR_HOME_DB_URL",
        "postgresql://igor:choose_a_password@127.0.0.1/Igor-wild-0001",
    )
    report = seed(db_url)
    print(
        f"seed_subsystem_index: upserted={report['upserted']} source={report['source']}"
    )


if __name__ == "__main__":
    main()
