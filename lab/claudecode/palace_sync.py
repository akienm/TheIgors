#!/usr/bin/env python3
"""
palace_sync.py — Echo memory_palace DB → lab/theigors/ directory tree.

T-palace-repo-sync: Syncs the memory palace from Postgres to a mirrored
directory tree in the repo. Each palace node becomes a markdown file at
its path. Committed to repo for version history and human readability.

Runs idempotently. Writes only when content has changed so git diffs
stay meaningful. Removes repo files that no longer exist in the palace.

Usage:
    IGOR_HOME_DB_URL=postgresql://... python3 lab/claudecode/palace_sync.py
    IGOR_HOME_DB_URL=postgresql://... python3 lab/claudecode/palace_sync.py --dry-run
"""

import json
import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
PALACE_DIR = REPO_ROOT / "lab" / "theigors"


def node_to_markdown(
    path: str, title: str, content: str, pointers, updated_at: str, updated_by: str
) -> str:
    """Render a palace node as a markdown file."""
    lines = [
        f"# {title}",
        "",
        f"**Path:** `{path}`",
        f"**Updated:** {updated_at} by {updated_by}",
        "",
    ]
    if content:
        lines.append(content)
        lines.append("")

    if pointers:
        if isinstance(pointers, str):
            pointers = json.loads(pointers)
        if pointers:
            lines.append("## Pointers")
            lines.append("")
            for p in pointers:
                if isinstance(p, dict):
                    ptype = p.get("type", "ref")
                    pref = p.get("ref", "")
                    lines.append(f"- **{ptype}:** `{pref}`")
                else:
                    lines.append(f"- `{p}`")
            lines.append("")

    return "\n".join(lines)


def main():
    dry_run = "--dry-run" in sys.argv

    db_url = os.environ.get("IGOR_HOME_DB_URL")
    if not db_url:
        print("ERROR: IGOR_HOME_DB_URL not set", file=sys.stderr)
        sys.exit(1)

    import psycopg2

    conn = psycopg2.connect(db_url)
    cur = conn.cursor()

    cur.execute(
        "SELECT path, title, content, pointers, updated_at, updated_by "
        "FROM memory_palace ORDER BY path"
    )
    rows = cur.fetchall()
    conn.close()

    if not rows:
        print("Palace is empty — nothing to sync.")
        return

    # Track which files we write so we can delete orphans
    written_files = set()

    # Also generate an index file
    index_lines = [
        "# Memory Palace",
        "",
        "Auto-synced from `memory_palace` table. Do not edit by hand — "
        "changes will be overwritten on next sync.",
        "",
        "## Tree",
        "",
    ]

    for row in rows:
        path, title, content, pointers, updated_at, updated_by = row

        # Map path → file: theigors/rules/coding → lab/theigors/rules/coding.md
        file_path = PALACE_DIR / f"{path}.md"

        markdown = node_to_markdown(
            path, title, content, pointers, updated_at, updated_by
        )

        if dry_run:
            print(f"Would write: {file_path.relative_to(REPO_ROOT)}")
        else:
            file_path.parent.mkdir(parents=True, exist_ok=True)
            # Only write if content changed (preserve git diffs)
            if file_path.exists() and file_path.read_text() == markdown:
                pass
            else:
                file_path.write_text(markdown)

        written_files.add(file_path)

        # Index entry
        depth = path.count("/")
        indent = "  " * depth
        name = path.rsplit("/", 1)[-1]
        relative = file_path.relative_to(PALACE_DIR)
        index_lines.append(f"{indent}- [{name}/ — {title}]({relative})")

    index_lines.append("")

    # Write index
    index_path = PALACE_DIR / "README.md"
    index_content = "\n".join(index_lines)
    if dry_run:
        print(f"Would write: {index_path.relative_to(REPO_ROOT)}")
    else:
        PALACE_DIR.mkdir(parents=True, exist_ok=True)
        if not index_path.exists() or index_path.read_text() != index_content:
            index_path.write_text(index_content)
    written_files.add(index_path)

    # Remove orphan files (present in repo but not in palace)
    if PALACE_DIR.exists():
        for existing in PALACE_DIR.rglob("*.md"):
            if existing not in written_files:
                if dry_run:
                    print(f"Would delete: {existing.relative_to(REPO_ROOT)}")
                else:
                    existing.unlink()

        # Clean up empty dirs
        if not dry_run:
            for d in sorted(PALACE_DIR.rglob("*"), key=lambda p: -len(str(p))):
                if d.is_dir() and not any(d.iterdir()):
                    d.rmdir()

    print(f"Synced {len(rows)} palace nodes → {PALACE_DIR.relative_to(REPO_ROOT)}/")


if __name__ == "__main__":
    main()
