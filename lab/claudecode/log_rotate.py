"""
log_rotate.py — Truncate oversized Igor runtime logs to last N lines.

Rotates any .log file under ~/.TheIgors that exceeds MAX_BYTES by:
  1. Keeping the last TAIL_LINES lines → written to <file>.log
  2. Moving the original to <file>.log.1 (single backup)

Safe to run while Igor is running — the rotation write is atomic (write
to tmp, rename). Plain-file writers (db_queries.log etc.) lose a brief
window; RotatingFileHandler writers handle it transparently on next write.

Usage:
    python3 lab/claudecode/log_rotate.py          # dry-run
    python3 lab/claudecode/log_rotate.py --run     # live rotation
    python3 lab/claudecode/log_rotate.py --run --dir /path/to/logs
"""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

MAX_BYTES = 10 * 1024 * 1024   # 10 MB
TAIL_LINES = 10_000


def rotate_file(path: Path, dry_run: bool = True) -> bool:
    """Rotate one log file. Returns True if rotated (or would rotate)."""
    size = path.stat().st_size
    if size < MAX_BYTES:
        return False

    backup = path.with_suffix(path.suffix + ".1")
    size_mb = size / 1024 / 1024
    print(f"  {'WOULD rotate' if dry_run else 'rotating'} {path.name} ({size_mb:.1f}M) → keep last {TAIL_LINES} lines")

    if dry_run:
        return True

    # Read tail
    text = path.read_text(errors="replace")
    lines = text.splitlines(keepends=True)
    tail = lines[-TAIL_LINES:]

    # Atomic rotation: write tail to tmp, back up original, rename tmp
    tmp = path.with_suffix(".log.tmp")
    try:
        tmp.write_text("".join(tail), encoding="utf-8", errors="replace")
        if backup.exists():
            backup.unlink()
        shutil.copy2(path, backup)
        tmp.replace(path)
    finally:
        if tmp.exists():
            tmp.unlink(missing_ok=True)

    return True


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Rotate oversized Igor runtime logs")
    parser.add_argument("--run", action="store_true", help="Apply rotation (default: dry-run)")
    parser.add_argument("--dir", help="Log directory to scan (default: ~/.TheIgors/**)")
    args = parser.parse_args(argv)

    dry_run = not args.run
    if dry_run:
        print("DRY RUN — pass --run to apply")

    base = Path(args.dir) if args.dir else Path.home() / ".TheIgors"
    log_files = sorted(base.rglob("*.log"))

    rotated = 0
    for f in log_files:
        try:
            if rotate_file(f, dry_run=dry_run):
                rotated += 1
        except Exception as exc:
            print(f"  ERROR {f.name}: {exc}", file=sys.stderr)

    print(f"\n{'Would rotate' if dry_run else 'Rotated'} {rotated} file(s) (threshold {MAX_BYTES // 1024 // 1024}MB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
