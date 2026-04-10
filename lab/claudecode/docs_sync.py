#!/usr/bin/env python3
"""
docs_sync.py — Mirror DSB/CSB design docs into Postgres docs_entries table.

Files remain canonical for editing. DB enables SQL queries for token-efficient
context load — e.g. "last 10 decisions" without reading the whole file.

Usage:
    python3 claudecode/docs_sync.py sync       — parse all DSB files → DB
    python3 claudecode/docs_sync.py query decisions [N]  — last N decisions
    python3 claudecode/docs_sync.py query gaps           — open gaps
    python3 claudecode/docs_sync.py query tools [filter] — tool index
    python3 claudecode/docs_sync.py list                 — show sources + counts

Ref: D130, D131, T-docs-tree-in-db
"""

import hashlib
import os
import re
import sys
from datetime import datetime
from pathlib import Path

DSB_DIR = Path.home() / "TheIgors" / "design_docs_for_igor"
DB_URL = os.getenv("IGOR_HOME_DB_URL") or os.getenv("IGOR_DB_URL")

# Files to sync (ordered by priority for context load)
DSB_FILES = [
    "decisions_log.dsb",
    "gap_analysis.dsb",
    "capabilities_index.dsb",
    "glossary.dsb",
    "inertia_registry.dsb",
    "architecture_root.dsb",
    "ethical_framework.dsb",
    "dev_process.dsb",
    "failure_modes.dsb",
    "igor_identity_master.dsb",
    "subsystem_cluster.dsb",
    "subsystem_cognition.dsb",
    "subsystem_inference.dsb",
    "subsystem_memory.dsb",
    "subsystem_reading.dsb",
    "subsystem_self_edit.dsb",
    "subsystem_tools.dsb",
    "subsystem_web_network.dsb",
]

# Patterns for entry_key + entry_type detection
_DECISION = re.compile(r"^(D\d+)\|")
_GAP = re.compile(r"^(G[-\w]+)\|")
_TOOL = re.compile(r"^  (\w[\w_./]+)\|")  # indented tool entries
_SECTION = re.compile(r"^(SECTION_\w+)\|?")
_META = re.compile(r"^(META)\|")
_DOC = re.compile(r"^(DOC)\|")
_COMMENT = re.compile(r"^//")


def _classify(line: str, source: str) -> tuple[str, str]:
    """Return (entry_key, entry_type) for a DSB line."""
    if _COMMENT.match(line) or not line.strip():
        return None, None
    if _DOC.match(line):
        return "DOC", "header"
    if _META.match(line):
        return line.split("|")[1] if "|" in line else "META", "meta"
    if _SECTION.match(line):
        return line.split("|")[0].strip(), "section"
    if source == "decisions_log":
        m = _DECISION.match(line)
        if m:
            return m.group(1), "decision"
    if source == "gap_analysis":
        m = _GAP.match(line)
        if m:
            return m.group(1), "gap"
    if source == "capabilities_index":
        m = _TOOL.match(line)
        if m:
            return m.group(1), "tool"
    # Generic: use first field as key
    parts = line.split("|")
    key = parts[0].strip()
    return (key if key else None), "entry"


def _parse_dsb(path: Path) -> list[dict]:
    """Parse a DSB file into a list of entry dicts."""
    source = path.stem  # filename without extension
    now = datetime.now().strftime("%Y-%m-%dT%H:%M")
    entries = []
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return []

    for line in text.splitlines():
        line = line.rstrip()
        if not line or _COMMENT.match(line):
            continue
        key, etype = _classify(line, source)
        if key is None:
            continue
        entries.append(
            {
                "source": source,
                "entry_key": key,
                "entry_type": etype,
                "content": line,
                "content_hash": hashlib.md5(line.encode()).hexdigest(),
                "synced_at": now,
            }
        )
    return entries


def _conn():
    import psycopg2
    import psycopg2.extras

    return psycopg2.connect(DB_URL, cursor_factory=psycopg2.extras.RealDictCursor)


def _upsert_entries(entries: list[dict]) -> int:
    if not entries:
        return 0
    now = datetime.now().isoformat()
    with _conn() as conn:
        with conn.cursor() as c:
            for e in entries:
                c.execute(
                    """
                    INSERT INTO docs_entries
                        (source, entry_key, entry_type, content, content_hash, synced_at, last_modified)
                    VALUES
                        (%(source)s, %(entry_key)s, %(entry_type)s, %(content)s,
                         %(content_hash)s, %(synced_at)s, %(now)s)
                    ON CONFLICT (source, entry_key) DO UPDATE SET
                        entry_type    = EXCLUDED.entry_type,
                        content       = EXCLUDED.content,
                        content_hash  = EXCLUDED.content_hash,
                        synced_at     = EXCLUDED.synced_at,
                        last_modified = CASE
                            WHEN docs_entries.content_hash IS DISTINCT FROM EXCLUDED.content_hash
                            THEN EXCLUDED.last_modified
                            ELSE docs_entries.last_modified
                        END
                """,
                    {**e, "now": now},
                )
        conn.commit()
    return len(entries)


# ── Commands ──────────────────────────────────────────────────────────────────


def cmd_sync():
    total = 0
    for fname in DSB_FILES:
        path = DSB_DIR / fname
        if not path.exists():
            print(f"  skip (not found): {fname}")
            continue
        entries = _parse_dsb(path)
        n = _upsert_entries(entries)
        print(f"  {fname}: {n} entries")
        total += n
    print(f"\nSync complete — {total} total entries in DB")


def cmd_query(args: list[str]):
    kind = args[0] if args else "decisions"
    limit = int(args[1]) if len(args) > 1 and args[1].isdigit() else 20

    with _conn() as conn:
        with conn.cursor() as c:
            if kind == "decisions":
                c.execute(
                    """
                    SELECT content FROM docs_entries
                    WHERE source='decisions_log' AND entry_type='decision'
                    ORDER BY entry_key DESC LIMIT %s
                """,
                    (limit,),
                )
                rows = c.fetchall()
                print(f"Last {limit} decisions (newest first):")
                for r in rows:
                    print(f"  {r['content']}")

            elif kind == "gaps":
                filter_str = (
                    args[1] if len(args) > 1 and not args[1].isdigit() else None
                )
                q = "SELECT entry_key, content FROM docs_entries WHERE source='gap_analysis' AND entry_type='gap'"
                if filter_str:
                    q += f" AND content ILIKE '%{filter_str}%'"
                q += " ORDER BY entry_key"
                c.execute(q)
                rows = c.fetchall()
                for r in rows:
                    print(f"  {r['content']}")
                print(f"\n{len(rows)} gaps")

            elif kind == "tools":
                filter_str = (
                    args[1] if len(args) > 1 and not args[1].isdigit() else None
                )
                q = "SELECT entry_key, content FROM docs_entries WHERE source='capabilities_index' AND entry_type='tool'"
                if filter_str:
                    q += f" AND content ILIKE '%{filter_str}%'"
                q += " ORDER BY entry_key"
                c.execute(q)
                rows = c.fetchall()
                for r in rows:
                    print(f"  {r['content'].strip()}")
                print(f"\n{len(rows)} tools matched")

            elif kind == "changed-since":
                # changed-since <ISO-datetime> — entries modified after that time
                since = args[1] if len(args) > 1 else "1970-01-01"
                c.execute(
                    """
                    SELECT source, entry_key, entry_type, content, last_modified
                    FROM docs_entries
                    WHERE last_modified > %s
                    ORDER BY last_modified DESC
                    LIMIT %s
                """,
                    (since, limit),
                )
                rows = c.fetchall()
                for r in rows:
                    ts = r["last_modified"] or "?"
                    if hasattr(ts, "isoformat"):
                        ts = ts.isoformat()
                    print(
                        f"  [{ts}] {r['source']}:{r['entry_key']} {r['content'][:80]}"
                    )
                print(f"\n{len(rows)} entries changed since {since}")

            else:
                # Generic source query
                c.execute(
                    """
                    SELECT entry_key, entry_type, content FROM docs_entries
                    WHERE source=%s ORDER BY id LIMIT %s
                """,
                    (kind, limit),
                )
                rows = c.fetchall()
                for r in rows:
                    print(f"  [{r['entry_type']}] {r['content']}")
                print(f"\n{len(rows)} entries from {kind}")


def cmd_list():
    with _conn() as conn:
        with conn.cursor() as c:
            c.execute("""
                SELECT source, entry_type, COUNT(*) as n
                FROM docs_entries
                GROUP BY source, entry_type
                ORDER BY source, entry_type
            """)
            rows = c.fetchall()
    current_source = None
    for r in rows:
        if r["source"] != current_source:
            current_source = r["source"]
            print(f"\n{current_source}")
        print(f"  {r['entry_type']:12s} {r['n']}")


# ── Entry point ───────────────────────────────────────────────────────────────


def main():
    if not DB_URL:
        print("ERROR: IGOR_HOME_DB_URL not set", file=sys.stderr)
        sys.exit(1)

    cmd = sys.argv[1] if len(sys.argv) > 1 else "sync"

    if cmd == "sync":
        cmd_sync()
    elif cmd == "query":
        cmd_query(sys.argv[2:])
    elif cmd == "list":
        cmd_list()
    else:
        print(f"Unknown command: {cmd}  (sync|query|list)")
        sys.exit(2)


if __name__ == "__main__":
    main()
