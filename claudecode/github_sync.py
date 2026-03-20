#!/usr/bin/env python3
"""
github_sync.py — Organizer step 0: sync GitHub issues → Postgres.

DB is source of truth after sync. GitHub is the upstream source.
Deltas are printed so the Organizer can summarise what changed.

Usage:
    python3 claudecode/github_sync.py sync     — pull GitHub → DB, print delta
    python3 claudecode/github_sync.py list     — show current DB state
    python3 claudecode/github_sync.py delta    — show changes since last sync

Ref: D130, T-organizer-github-sync
"""

import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

REPO = "akienm/TheIgors"
DB_URL = os.getenv("IGOR_HOME_DB_URL") or os.getenv("IGOR_DB_URL")
OPEN_LIMIT = 100
CLOSED_LIMIT = 30  # recently closed — catch human-closed tickets


# ── DB ────────────────────────────────────────────────────────────────────────


def _conn():
    import psycopg2
    import psycopg2.extras

    return psycopg2.connect(DB_URL, cursor_factory=psycopg2.extras.RealDictCursor)


def _load_db() -> dict[int, dict]:
    """Return {number: row} for all tickets in DB."""
    with _conn() as conn:
        with conn.cursor() as c:
            c.execute("SELECT * FROM github_tickets ORDER BY number")
            return {r["number"]: dict(r) for r in c.fetchall()}


def _upsert(conn, ticket: dict):
    with conn.cursor() as c:
        c.execute(
            """
            INSERT INTO github_tickets (number, title, state, body, labels, updated_at, synced_at)
            VALUES (%(number)s, %(title)s, %(state)s, %(body)s, %(labels)s, %(updated_at)s, %(synced_at)s)
            ON CONFLICT (number) DO UPDATE SET
                title      = EXCLUDED.title,
                state      = EXCLUDED.state,
                body       = EXCLUDED.body,
                labels     = EXCLUDED.labels,
                updated_at = EXCLUDED.updated_at,
                synced_at  = EXCLUDED.synced_at
        """,
            ticket,
        )


# ── GitHub ────────────────────────────────────────────────────────────────────


def _gh_issues(state: str, limit: int) -> list[dict]:
    """Fetch issues from GitHub via gh CLI."""
    result = subprocess.run(
        [
            "gh",
            "issue",
            "list",
            "--repo",
            REPO,
            "--state",
            state,
            "--limit",
            str(limit),
            "--json",
            "number,title,state,body,labels,updatedAt",
        ],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print(f"ERROR: gh CLI failed: {result.stderr.strip()}", file=sys.stderr)
        sys.exit(1)
    issues = json.loads(result.stdout)
    now = datetime.now().strftime("%Y-%m-%dT%H:%M")
    rows = []
    for i in issues:
        rows.append(
            {
                "number": i["number"],
                "title": i["title"],
                "state": i["state"].lower(),
                "body": (i.get("body") or "")[:2000],  # cap body size
                "labels": ",".join(l["name"] for l in i.get("labels", [])),
                "updated_at": i.get("updatedAt", ""),
                "synced_at": now,
            }
        )
    return rows


# ── Commands ──────────────────────────────────────────────────────────────────


def cmd_sync():
    """Pull GitHub → DB. Print delta report."""
    print(f"Syncing {REPO} → Postgres...")

    before = _load_db()

    open_issues = _gh_issues("open", OPEN_LIMIT)
    closed_issues = _gh_issues("closed", CLOSED_LIMIT)
    all_issues = {i["number"]: i for i in open_issues + closed_issues}

    now = datetime.now().strftime("%Y-%m-%dT%H:%M")
    new_open = []
    new_closed = []
    reopened = []
    updated = []

    with _conn() as conn:
        for num, ticket in all_issues.items():
            if num not in before:
                if ticket["state"] == "open":
                    new_open.append(ticket)
                else:
                    new_closed.append(ticket)
            else:
                prev = before[num]
                if prev["state"] == "open" and ticket["state"] == "closed":
                    new_closed.append(ticket)
                elif prev["state"] == "closed" and ticket["state"] == "open":
                    reopened.append(ticket)
                elif prev.get("updated_at") != ticket["updated_at"]:
                    updated.append(ticket)
            _upsert(conn, ticket)
        conn.commit()

    # Report
    total_open = len([i for i in all_issues.values() if i["state"] == "open"])
    print(
        f"\nDB updated — {total_open} open, {len(all_issues) - total_open} recently closed tracked"
    )
    print(f"Synced at: {now}")

    if new_open:
        print(f"\n🆕 New open ({len(new_open)}):")
        for i in new_open:
            print(f"  #{i['number']}: {i['title']}")

    if new_closed:
        print(f"\n✅ Newly closed ({len(new_closed)}):")
        for i in new_closed:
            print(f"  #{i['number']}: {i['title']}")

    if reopened:
        print(f"\n🔄 Reopened ({len(reopened)}):")
        for i in reopened:
            print(f"  #{i['number']}: {i['title']}")

    if updated:
        print(f"\n📝 Updated ({len(updated)}):")
        for i in updated:
            print(f"  #{i['number']}: {i['title']}")

    if not any([new_open, new_closed, reopened, updated]):
        print("\nNo changes since last sync.")


def cmd_list(state: str = "open"):
    """Print tickets from DB."""
    with _conn() as conn:
        with conn.cursor() as c:
            if state == "all":
                c.execute(
                    "SELECT number, title, state, labels FROM github_tickets ORDER BY number DESC"
                )
            else:
                c.execute(
                    "SELECT number, title, state, labels FROM github_tickets WHERE state=%s ORDER BY number DESC",
                    (state,),
                )
            rows = c.fetchall()
    if not rows:
        print(f"No {state} tickets in DB. Run: github_sync.py sync")
        return
    for r in rows:
        label_str = f"  [{r['labels']}]" if r.get("labels") else ""
        print(f"  #{r['number']}: {r['title']}{label_str}")
    print(f"\n{len(rows)} tickets ({state})")


def cmd_delta():
    """Show tickets updated since last sync."""
    with _conn() as conn:
        with conn.cursor() as c:
            c.execute("""
                SELECT number, title, state, synced_at
                FROM github_tickets
                ORDER BY synced_at DESC, number DESC
                LIMIT 20
            """)
            rows = c.fetchall()
    if not rows:
        print("No sync data yet. Run: github_sync.py sync")
        return
    last_sync = rows[0]["synced_at"] if rows else "never"
    print(f"Last sync: {last_sync}")
    for r in rows:
        mark = "·" if r["state"] == "open" else "✓"
        print(f"  {mark} #{r['number']}: {r['title']}")


# ── Entry point ───────────────────────────────────────────────────────────────


def main():
    if not DB_URL:
        print("ERROR: IGOR_HOME_DB_URL not set", file=sys.stderr)
        sys.exit(1)

    cmd = sys.argv[1] if len(sys.argv) > 1 else "sync"

    if cmd == "sync":
        cmd_sync()
    elif cmd == "list":
        state = sys.argv[2] if len(sys.argv) > 2 else "open"
        cmd_list(state)
    elif cmd == "delta":
        cmd_delta()
    else:
        print(f"Unknown command: {cmd}  (sync|list|delta)")
        sys.exit(2)


if __name__ == "__main__":
    main()
