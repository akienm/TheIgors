#!/usr/bin/env python3
"""
github_sync.py — Organizer step 0: sync GitHub issues → Postgres.

DB is source of truth after sync. GitHub is the upstream source.
Deltas are printed so the Organizer can summarise what changed.

Usage:
    python3 claudecode/github_sync.py sync        — pull GitHub → DB, print delta
    python3 claudecode/github_sync.py list        — show current DB state
    python3 claudecode/github_sync.py delta       — show changes since last sync
    python3 claudecode/github_sync.py push-queue  — create GH Issues for cc_queue tickets
                                                    missing github_issue field; write numbers back

Ref: D130, T-organizer-github-sync, T-github-issues-sync
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


QUEUE_PATH = os.path.expanduser("~/.TheIgors/cc_channel/queue.json")
CLOSED_TICKETS_PATH = os.path.expanduser("~/.TheIgors/claudecode/closed_tickets.txt")


def cmd_push_queue():
    """Create GitHub Issues for cc_queue tickets that lack a github_issue number.

    For each non-done ticket with github_issue == None:
    1. Creates a GH Issue titled "[T-xxx] <title>"
    2. Writes the returned issue number back via cc_queue.py set-github-issue
    """
    if not os.path.exists(QUEUE_PATH):
        print("Queue empty — nothing to push.")
        return

    with open(QUEUE_PATH) as f:
        tasks = json.load(f)

    to_push = [
        t for t in tasks if t.get("status") != "done" and not t.get("github_issue")
    ]

    if not to_push:
        print("All non-done tickets already have github_issue numbers.")
        return

    print(f"Creating GH Issues for {len(to_push)} ticket(s)...")
    created = 0
    for t in to_push:
        tid = t["id"]
        title = f"[{tid}] {t['title']}"
        body_parts = [f"cc_queue ticket: **{tid}**\n"]
        if t.get("description"):
            body_parts.append(t["description"])
        if t.get("epic"):
            body_parts.append(f"\n**Epic**: {t['epic']}")
        if t.get("size"):
            body_parts.append(f"**Size**: {t['size']}")
        if t.get("priority"):
            body_parts.append(f"**Priority**: {t['priority']}")
        body = "\n".join(body_parts)

        cmd = [
            "gh",
            "issue",
            "create",
            "--repo",
            REPO,
            "--title",
            title,
            "--body",
            body,
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"  ERROR creating issue for {tid}: {result.stderr.strip()}")
            continue

        # gh issue create prints the URL on stdout: https://github.com/.../issues/NNN
        url = result.stdout.strip()
        try:
            issue_num = int(url.rstrip("/").split("/")[-1])
        except (ValueError, IndexError):
            print(f"  WARNING: could not parse issue number from: {url}")
            continue

        # Write number back to queue
        wb = subprocess.run(
            [
                "python3",
                os.path.expanduser("~/TheIgors/claudecode/cc_queue.py"),
                "set-github-issue",
                tid,
                str(issue_num),
            ],
            capture_output=True,
            text=True,
        )
        if wb.returncode != 0:
            print(f"  WARNING: set-github-issue failed for {tid}: {wb.stderr.strip()}")
        else:
            print(f"  {tid} → GH #{issue_num}  {url}")
            created += 1

    print(f"\nDone — created {created} issue(s).")


# ── Entry point ───────────────────────────────────────────────────────────────


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "sync"

    if cmd == "push-queue":
        cmd_push_queue()
        return

    if not DB_URL:
        print("ERROR: IGOR_HOME_DB_URL not set", file=sys.stderr)
        sys.exit(1)

    if cmd == "sync":
        cmd_sync()
    elif cmd == "list":
        state = sys.argv[2] if len(sys.argv) > 2 else "open"
        cmd_list(state)
    elif cmd == "delta":
        cmd_delta()
    else:
        print(f"Unknown command: {cmd}  (sync|list|delta|push-queue)")
        sys.exit(2)


if __name__ == "__main__":
    main()
