#!/usr/bin/env python3
"""review_manager.py — /review findings persistence.

Helper for /review skill to write findings to infra.review_findings table.

Usage:
    review_manager.py write \
      --mode filing \
      --ticket T-xxx \
      --verdict PASS \
      --findings 'finding 1' 'finding 2' \
      --checks '{"duplicate": {...}, "already_done": {...}}'

    review_manager.py write \
      --mode code \
      --commit abc123 \
      --verdict MUST-FIX \
      --findings 'finding 1'

    review_manager.py stats --mode filing --days 7
    review_manager.py confidence --check duplicate --days 30
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import psycopg2
from psycopg2.extras import execute_values


def get_db_url() -> str:
    """Get Postgres connection URL from env or default."""
    return os.environ["IGOR_HOME_DB_URL"]


def write_findings(
    mode: str,
    verdict: str,
    findings: list[str],
    checks: dict | None = None,
    ticket_id: str | None = None,
    plan_id: str | None = None,
    pr_number: int | None = None,
    commit_hash: str | None = None,
    override: bool = False,
    override_reason: str | None = None,
) -> int:
    """Write a review finding to the DB. Returns the inserted ID."""
    db_url = get_db_url()
    try:
        conn = psycopg2.connect(db_url)
        cur = conn.cursor()

        cur.execute(
            """
            INSERT INTO infra.review_findings
            (mode, verdict, findings, checks, ticket_id, plan_id, pr_number, commit_hash, override, override_reason)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
            """,
            (
                mode,
                verdict,
                findings,
                json.dumps(checks) if checks else None,
                ticket_id,
                plan_id,
                pr_number,
                commit_hash,
                override,
                override_reason,
            ),
        )
        row_id = cur.fetchone()[0]
        conn.commit()
        cur.close()
        conn.close()
        return row_id
    except psycopg2.Error as e:
        print(f"DB error: {e}", file=sys.stderr)
        raise


def get_check_confidence(check_name: str, days: int = 30) -> dict:
    """
    Compute confidence for a specific check over last N days.

    Returns: {total: int, verdicts: {PASS: int, AMEND: int, ...}, confidence: float}
    """
    db_url = get_db_url()
    try:
        conn = psycopg2.connect(db_url)
        cur = conn.cursor()

        since = datetime.now(timezone.utc) - timedelta(days=days)
        cur.execute(
            """
            SELECT COUNT(*) as total,
                   COUNT(CASE WHEN override THEN 1 END) as overrides,
                   COUNT(CASE WHEN verdict = 'PASS' THEN 1 END) as pass_count
            FROM infra.review_findings
            WHERE created_at >= %s
              AND checks->>%s IS NOT NULL
            """,
            (since, check_name),
        )
        row = cur.fetchone()
        cur.close()
        conn.close()

        if not row or row[0] == 0:
            return {"total": 0, "confidence": 0.5}  # default neutral

        total, overrides, pass_count = row
        # Confidence = (pass_count - overrides) / total
        # Lower overrides = higher confidence in the check
        confidence = (pass_count - overrides) / total if total > 0 else 0.5
        return {
            "total": total,
            "pass_count": pass_count,
            "overrides": overrides,
            "confidence": max(0.0, min(1.0, confidence)),  # clamp to [0,1]
        }

    except psycopg2.Error as e:
        print(f"DB error: {e}", file=sys.stderr)
        return {"total": 0, "confidence": 0.5}


def get_stats(mode: str | None = None, days: int = 7) -> dict:
    """Get review statistics for the given mode and time window."""
    db_url = get_db_url()
    try:
        conn = psycopg2.connect(db_url)
        cur = conn.cursor()

        since = datetime.now(timezone.utc) - timedelta(days=days)
        where_clause = "WHERE created_at >= %s"
        params = [since]

        if mode:
            where_clause += " AND mode = %s"
            params.append(mode)

        cur.execute(
            f"""
            SELECT mode, verdict, COUNT(*) as count
            FROM infra.review_findings
            {where_clause}
            GROUP BY mode, verdict
            ORDER BY mode, count DESC
            """,
            params,
        )
        rows = cur.fetchall()
        cur.close()
        conn.close()

        stats = {}
        for row_mode, verdict, count in rows:
            if row_mode not in stats:
                stats[row_mode] = {}
            stats[row_mode][verdict] = count

        return stats

    except psycopg2.Error as e:
        print(f"DB error: {e}", file=sys.stderr)
        return {}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    subparsers = p.add_subparsers(dest="cmd")

    # write subcommand
    write_p = subparsers.add_parser("write", help="Write a review finding")
    write_p.add_argument(
        "--mode", required=True, choices=["filing", "plan", "code", "pr"]
    )
    write_p.add_argument("--verdict", required=True)
    write_p.add_argument("--findings", nargs="*", default=[])
    write_p.add_argument("--checks", type=json.loads, default=None)
    write_p.add_argument("--ticket", default=None)
    write_p.add_argument("--plan", default=None)
    write_p.add_argument("--pr", type=int, default=None)
    write_p.add_argument("--commit", default=None)
    write_p.add_argument("--override", action="store_true")
    write_p.add_argument("--override-reason", default=None)

    # stats subcommand
    stats_p = subparsers.add_parser("stats", help="Show review statistics")
    stats_p.add_argument("--mode", default=None)
    stats_p.add_argument("--days", type=int, default=7)

    # confidence subcommand
    conf_p = subparsers.add_parser(
        "confidence", help="Check confidence for a specific check"
    )
    conf_p.add_argument("--check", required=True, help="Check name (e.g., 'duplicate')")
    conf_p.add_argument("--days", type=int, default=30)

    args = p.parse_args()

    if args.cmd == "write":
        row_id = write_findings(
            mode=args.mode,
            verdict=args.verdict,
            findings=args.findings,
            checks=args.checks,
            ticket_id=args.ticket,
            plan_id=args.plan,
            pr_number=args.pr,
            commit_hash=args.commit,
            override=args.override,
            override_reason=args.override_reason,
        )
        print(f"Written review_findings record id={row_id}")
        return 0

    elif args.cmd == "stats":
        stats = get_stats(mode=args.mode, days=args.days)
        print(json.dumps(stats, indent=2))
        return 0

    elif args.cmd == "confidence":
        conf = get_check_confidence(args.check, days=args.days)
        print(json.dumps(conf, indent=2))
        return 0

    else:
        p.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())
