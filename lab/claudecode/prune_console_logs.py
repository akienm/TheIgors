"""
prune_console_logs.py — remove console log files older than RETENTION_DAYS.

Scans $UNSEEN_UNIVERSITY_HOME/logs/*/YYYYMMDD.console.log and deletes any
file whose date is older than RETENTION_DAYS (default 7) days ago.

Safe to run as a cron job or on each session start. Idempotent.

Usage:
    python3 prune_console_logs.py [--days 7] [--dry-run]
"""

from __future__ import annotations

import argparse
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path


def _log_root() -> Path:
    home = os.environ.get("UNSEEN_UNIVERSITY_HOME", str(Path.home() / ".unseen_university"))
    return Path(home) / "logs"


def prune(retention_days: int = 7, dry_run: bool = False) -> int:
    """Delete console logs older than retention_days. Returns count deleted."""
    root = _log_root()
    if not root.exists():
        return 0

    cutoff = datetime.now(timezone.utc) - timedelta(days=retention_days)
    deleted = 0

    for log_file in root.rglob("*.console.log"):
        stem = log_file.stem.replace(".console", "")
        try:
            file_date = datetime.strptime(stem, "%Y%m%d").replace(tzinfo=timezone.utc)
        except ValueError:
            continue
        if file_date < cutoff:
            if dry_run:
                print(f"[dry-run] would delete: {log_file}")
            else:
                log_file.unlink(missing_ok=True)
                print(f"deleted: {log_file}")
            deleted += 1

    return deleted


def main() -> None:
    parser = argparse.ArgumentParser(description="Prune old console log files")
    parser.add_argument("--days", type=int, default=7, help="Retention period in days")
    parser.add_argument("--dry-run", action="store_true", help="Print what would be deleted")
    args = parser.parse_args()

    n = prune(retention_days=args.days, dry_run=args.dry_run)
    print(f"{'[dry-run] ' if args.dry_run else ''}pruned {n} console log(s)")
    sys.exit(0)


if __name__ == "__main__":
    main()
