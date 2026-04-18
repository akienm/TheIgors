#!/usr/bin/env python3
"""
session_to_graph.py — GH-274: Claude session context as Igor memory tree.

Deposits CC session knowledge into Igor's graph as INTERPRETIVE nodes
under a CC_SESSION subtree. At next-session boot, context_inject can
traverse the subgraph for richer context than flat file reads.

Usage:
    # At savestate time:
    IGOR_HOME_DB_URL=... python3 lab/claudecode/session_to_graph.py deposit "2026-04-17a" "theme text"

    # At context-load time:
    IGOR_HOME_DB_URL=... python3 lab/claudecode/session_to_graph.py load 3
"""

import json
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

DB_URL = os.environ.get("IGOR_HOME_DB_URL", "")


def deposit_session(session_id: str, theme: str = "", changes: list = None) -> dict:
    """Deposit a CC session as nodes in the graph.

    Creates:
      - Root node: CC_SESSION_{session_id}
      - Child nodes for each key change/decision

    Returns dict with node IDs created.
    """
    if not DB_URL:
        return {"error": "IGOR_HOME_DB_URL not set"}

    import psycopg2

    conn = psycopg2.connect(DB_URL)
    cur = conn.cursor()
    cur.execute("SET search_path TO instance, clan, infra, public")

    root_id = f"CC_SESSION_{session_id.replace('-', '').replace('.', '_')}"
    now = datetime.now().isoformat()

    # Ensure CC_SESSIONS parent exists
    cur.execute(
        """
        INSERT INTO memories (id, narrative, memory_type, parent_id, source, confidence,
                              metadata, timestamp, scope)
        VALUES ('CC_SESSIONS_ROOT', 'Root node for all Claude Code session deposits.',
                'FACTUAL', 'CP3', 'session_to_graph', 1.0, '{"spine": true}', %s, 'class')
        ON CONFLICT (id) DO NOTHING
        """,
        (now,),
    )

    # Create session root
    narrative = (
        f"CC session {session_id}: {theme}" if theme else f"CC session {session_id}"
    )
    meta = {
        "session_id": session_id,
        "theme": theme,
        "deposited_at": now,
        "deposited_by": "session_to_graph",
    }
    cur.execute(
        """
        INSERT INTO memories (id, narrative, memory_type, parent_id, source, confidence,
                              metadata, timestamp, scope)
        VALUES (%s, %s, 'EPISODIC', 'CC_SESSIONS_ROOT', 'session_to_graph', 1.0, %s, %s, 'class')
        ON CONFLICT (id) DO UPDATE SET narrative = EXCLUDED.narrative, metadata = EXCLUDED.metadata
        """,
        (root_id, narrative, json.dumps(meta), now),
    )

    # Create child nodes for each change
    child_ids = []
    for i, change in enumerate(changes or []):
        child_id = f"{root_id}_C{i:03d}"
        child_meta = {
            "session_id": session_id,
            "change_index": i,
            "deposited_by": "session_to_graph",
        }
        cur.execute(
            """
            INSERT INTO memories (id, narrative, memory_type, parent_id, source, confidence,
                                  metadata, timestamp, scope)
            VALUES (%s, %s, 'INTERPRETIVE', %s, 'session_to_graph', 0.8, %s, %s, 'class')
            ON CONFLICT (id) DO UPDATE SET narrative = EXCLUDED.narrative
            """,
            (child_id, change, root_id, json.dumps(child_meta), now),
        )
        child_ids.append(child_id)

    conn.commit()
    conn.close()

    return {
        "root_id": root_id,
        "children": len(child_ids),
        "child_ids": child_ids,
    }


def load_recent_sessions(limit: int = 3) -> list[dict]:
    """Load recent CC session deposits from the graph."""
    if not DB_URL:
        return []

    import psycopg2
    import psycopg2.extras

    conn = psycopg2.connect(DB_URL, cursor_factory=psycopg2.extras.RealDictCursor)
    cur = conn.cursor()
    cur.execute("SET search_path TO instance, clan, infra, public")

    # Get recent session roots
    cur.execute(
        """
        SELECT id, narrative, metadata, timestamp
        FROM memories
        WHERE parent_id = 'CC_SESSIONS_ROOT' AND memory_type = 'EPISODIC'
        ORDER BY timestamp DESC
        LIMIT %s
        """,
        (limit,),
    )
    sessions = []
    for row in cur.fetchall():
        session = dict(row)
        # Get children
        cur.execute(
            "SELECT id, narrative FROM memories WHERE parent_id = %s ORDER BY id",
            (row["id"],),
        )
        session["changes"] = [dict(r) for r in cur.fetchall()]
        sessions.append(session)

    conn.close()
    return sessions


def main():
    import argparse

    parser = argparse.ArgumentParser(description="CC session → graph")
    sub = parser.add_subparsers(dest="cmd")

    p_dep = sub.add_parser("deposit", help="Deposit a session")
    p_dep.add_argument("session_id")
    p_dep.add_argument("theme", nargs="?", default="")

    p_load = sub.add_parser("load", help="Load recent sessions")
    p_load.add_argument("limit", type=int, nargs="?", default=3)

    args = parser.parse_args()

    if args.cmd == "deposit":
        # Read changes from session_manager
        try:
            from lab.claudecode.session_manager import _get_session

            session = _get_session(args.session_id)
            changes = session.get("key_changes", []) if session else []
        except Exception:
            changes = []
        result = deposit_session(args.session_id, args.theme, changes)
        print(json.dumps(result, indent=2))

    elif args.cmd == "load":
        sessions = load_recent_sessions(args.limit)
        for s in sessions:
            print(f"\n{s['id']}: {s['narrative']}")
            for c in s.get("changes", []):
                print(f"  - {c['narrative'][:100]}")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
