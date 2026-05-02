#!/usr/bin/env python3
"""
migrate_claude_budget_db.py — one-shot SQLite → Postgres migration for the
claude_budget.db tracking tables.

Reads the legacy SQLite file (path from paths().instance / claude_budget.db),
INSERTs all rows into Postgres infra.spend / infra.budget_config /
infra.balance_history, verifies counts match, then deletes the SQLite file
(and its hardlink twin under ~/.agent_datacenter/, if present).

Idempotent: skips the migration if the SQLite file is already absent.
Re-running after a successful migration is a no-op.

Pre-flight checks:
  - Postgres tables must exist (cortex migration m053). Aborts if not.
  - Postgres tables must be empty for a clean migration. Pass --force-merge
    to allow an additive insert (existing Postgres rows kept as-is, SQLite
    rows added on top — useful only if you know what you're doing).

Usage:
  python3 lab/claudecode/migrate_claude_budget_db.py            # dry-run report
  python3 lab/claudecode/migrate_claude_budget_db.py --execute  # do it
  python3 lab/claudecode/migrate_claude_budget_db.py --execute --force-merge
"""

from __future__ import annotations

import argparse
import os
import sqlite3
import sys
from pathlib import Path

# Allow running this script directly without PYTHONPATH=.
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))


def _budget_db_path() -> Path:
    from wild_igor.igor.paths import paths

    return paths().instance / "claude_budget.db"


def _agent_datacenter_twin(p: Path) -> Path:
    home = Path.home()
    rel = (
        p.relative_to(home / ".TheIgors")
        if str(p).startswith(str(home / ".TheIgors"))
        else None
    )
    if rel is None:
        return None
    return home / ".agent_datacenter" / rel


def _read_sqlite(db: Path) -> dict:
    if not db.exists():
        return {"spend": [], "config": [], "balance_history": []}
    conn = sqlite3.connect(db)
    conn.row_factory = sqlite3.Row
    spend = [dict(r) for r in conn.execute("SELECT * FROM spend").fetchall()]
    config = [dict(r) for r in conn.execute("SELECT * FROM config").fetchall()]
    history = [
        dict(r) for r in conn.execute("SELECT * FROM balance_history").fetchall()
    ]
    conn.close()
    return {"spend": spend, "config": config, "balance_history": history}


def _pg_counts(proxy):
    with proxy() as c:
        spend = c.execute("SELECT COUNT(*) as n FROM spend").fetchall()[0]["n"]
        cfg = c.execute("SELECT COUNT(*) as n FROM budget_config").fetchall()[0]["n"]
        hist = c.execute("SELECT COUNT(*) as n FROM balance_history").fetchall()[0]["n"]
    return {"spend": spend, "budget_config": cfg, "balance_history": hist}


def _insert_all(proxy, data: dict) -> None:
    with proxy() as c:
        for row in data["spend"]:
            c.execute(
                "INSERT INTO spend (timestamp, model, usd, note) VALUES (?, ?, ?, ?)",
                (row["timestamp"], row["model"], row["usd"], row.get("note", "") or ""),
            )
        for row in data["config"]:
            # SQLite table was named `config`; Postgres is `budget_config`
            c.execute(
                "INSERT OR REPLACE INTO budget_config (key, value) VALUES (?, ?)",
                (row["key"], row["value"]),
            )
        for row in data["balance_history"]:
            c.execute(
                "INSERT INTO balance_history (timestamp, balance, purchased, used) "
                "VALUES (?, ?, ?, ?)",
                (
                    row["timestamp"],
                    row["balance"],
                    row["purchased"],
                    row["used"],
                ),
            )


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--execute", action="store_true", help="Actually do it (default: dry run)."
    )
    ap.add_argument(
        "--force-merge",
        action="store_true",
        help="Allow additive insert into non-empty Postgres tables.",
    )
    args = ap.parse_args()

    os.environ.setdefault(
        "IGOR_HOME_DB_URL",
        "postgresql://igor:choose_a_password@127.0.0.1/Igor-wild-0001",
    )

    db = _budget_db_path()
    twin = _agent_datacenter_twin(db)

    if not db.exists():
        print(f"OK: SQLite file already absent ({db}). Nothing to migrate.")
        return 0

    data = _read_sqlite(db)
    print(f"SQLite source: {db}")
    print(f"  spend rows:           {len(data['spend'])}")
    print(f"  config rows:          {len(data['config'])}")
    print(f"  balance_history rows: {len(data['balance_history'])}")

    from lab.utility_closet.db_proxy import make_home_proxy

    proxy = make_home_proxy()
    try:
        before = _pg_counts(proxy)
    except Exception as exc:
        print(
            f"ERROR: Postgres preflight failed — tables exist? ({exc})", file=sys.stderr
        )
        return 2

    print(f"\nPostgres before:")
    for k, v in before.items():
        print(f"  infra.{k}: {v}")

    nonempty = any(v > 0 for v in before.values())
    if nonempty and not args.force_merge:
        print(
            "\nABORT: Postgres tables already have data. Re-run with --force-merge "
            "to add SQLite rows on top, or TRUNCATE first.",
            file=sys.stderr,
        )
        return 3

    if not args.execute:
        print("\n[DRY RUN] Pass --execute to perform the migration.")
        return 0

    _insert_all(proxy, data)

    after = _pg_counts(proxy)
    expected = {
        "spend": before["spend"] + len(data["spend"]),
        "budget_config": max(before["budget_config"], len(data["config"])),
        "balance_history": before["balance_history"] + len(data["balance_history"]),
    }
    print(f"\nPostgres after:")
    for k, v in after.items():
        marker = "OK" if v == expected[k] else f"MISMATCH (expected {expected[k]})"
        print(f"  infra.{k}: {v}  [{marker}]")

    mismatch = any(after[k] != expected[k] for k in after)
    if mismatch:
        print(
            "\nABORT: row count mismatch — leaving SQLite file in place for inspection."
        )
        return 4

    db.unlink()
    print(f"\nDeleted: {db}")
    if twin and twin.exists():
        twin.unlink()
        print(f"Deleted hardlink twin: {twin}")
    elif twin:
        print(f"Twin already absent: {twin}")

    print("\nMigration complete.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
