#!/usr/bin/env python3
"""stale_ticket_sweeper.py — T-stale-ticket-sweeper (D-workflow-overhaul-2026-04-20).

Scans queue.json for pending tickets that have sat for >= N weeks without
motion, plus gated tickets where the gate condition may have resolved. Emits
a report to stdout + appends a one-liner to today's slate under ## Ad hoc
so CC picks it up in context-load.

Does NOT auto-run /review on flagged tickets — /review is a human-invoked
skill that needs judgment. The sweeper just flags candidates.

Default: weekly cadence (call from Igor idle push_source, or cron, or
manually). Threshold: 4 weeks pending without status change.

Usage:
    stale_ticket_sweeper.py                       — default run
    stale_ticket_sweeper.py --weeks 8             — raise threshold
    stale_ticket_sweeper.py --include-gated       — also flag gated tickets
                                                    whose gate text mentions
                                                    a ticket that has shipped
    stale_ticket_sweeper.py --json                — emit machine-readable output
    stale_ticket_sweeper.py --dry-run             — don't touch the slate
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

SLATE_DIR = Path.home() / ".TheIgors/claudecode"

DEFAULT_WEEKS = 4


def _load_queue() -> list[dict]:
    import sys as _sys

    _sys.path.insert(0, str(Path(__file__).resolve().parent))
    from cc_queue import load_tasks

    return load_tasks()


def _parse_iso(ts: str | None) -> datetime | None:
    if not ts:
        return None
    try:
        return datetime.fromisoformat(ts.replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        return None


def _ticket_age_days(t: dict) -> float | None:
    """Rough age heuristic: most recent of (claimed_at, completed_at, added)
    compared to now. Falls back to None if no dates available.
    """
    now = datetime.now(timezone.utc)
    # We don't have an explicit added_at field; claimed_at / completed_at are
    # populated once motion happens. A pending ticket that never moved has
    # neither. Heuristic: if status=pending and claimed_at is null, age is
    # effectively "since file was edited" — not trackable per-ticket without
    # a git-blame pass. For now, use claimed_at if present; flag tickets
    # without timestamps separately.
    candidate = _parse_iso(t.get("claimed_at")) or _parse_iso(t.get("completed_at"))
    if not candidate:
        return None
    return (now - candidate).total_seconds() / 86400.0


def sweep(weeks: int = DEFAULT_WEEKS, include_gated: bool = False) -> dict:
    """Return a report dict."""
    threshold_days = weeks * 7
    tasks = _load_queue()
    pending_stale: list[dict] = []
    pending_unstamped: list[dict] = []
    gated_maybe_unlockable: list[dict] = []

    done_ids = {t["id"] for t in tasks if t.get("status") == "done"}

    for t in tasks:
        status = t.get("status")
        if status == "pending":
            age = _ticket_age_days(t)
            if age is None:
                pending_unstamped.append(t)
            elif age >= threshold_days:
                pending_stale.append({"ticket": t, "age_days": round(age, 1)})
            if include_gated and t.get("gate"):
                gate_text = (t.get("gate") or "").lower()
                # naive check: does the gate mention any done ticket id?
                for did in done_ids:
                    if did.lower() in gate_text:
                        gated_maybe_unlockable.append(
                            {"ticket": t, "possibly_resolved_by": did}
                        )
                        break

    return {
        "run_at": datetime.now(timezone.utc).isoformat(),
        "threshold_weeks": weeks,
        "pending_stale": pending_stale,
        "pending_unstamped_count": len(pending_unstamped),
        "gated_maybe_unlockable": gated_maybe_unlockable,
    }


def render_report(report: dict) -> str:
    lines = []
    lines.append(
        f"# Stale ticket sweep — {report['run_at']} (threshold {report['threshold_weeks']} weeks)"
    )
    lines.append("")

    pending_stale = report["pending_stale"]
    lines.append(
        f"## Pending > {report['threshold_weeks']} weeks ({len(pending_stale)})"
    )
    if not pending_stale:
        lines.append("(none)")
    else:
        for row in pending_stale:
            t = row["ticket"]
            lines.append(
                f"- {t['id']} — {row['age_days']}d — {t.get('title', '?')} — "
                f"/review: still real? premise rotted? decision reversed?"
            )
    lines.append("")

    lines.append(f"## Pending without timestamps ({report['pending_unstamped_count']})")
    lines.append(
        "Tickets with no claimed_at/completed_at — age not trackable per-ticket. "
        "Run git blame on queue.json if triage needed."
    )
    lines.append("")

    if report["gated_maybe_unlockable"]:
        lines.append("## Gated — possibly unlockable")
        for row in report["gated_maybe_unlockable"]:
            t = row["ticket"]
            lines.append(
                f"- {t['id']} — gated: {(t.get('gate') or '')[:80]} — "
                f"but {row['possibly_resolved_by']} has shipped. Consider ungate."
            )
        lines.append("")

    return "\n".join(lines)


def append_to_slate(report: dict) -> None:
    today = datetime.now().strftime("%Y%m%d")
    slate_path = SLATE_DIR / f"{today}.slate.txt"
    if not slate_path.exists():
        # Also try YYYY-MM-DD naming in case the slate convention shifts
        alt = SLATE_DIR / f"{datetime.now().strftime('%Y-%m-%d')}.slate.txt"
        if alt.exists():
            slate_path = alt
        else:
            return  # no slate to append to
    n = len(report["pending_stale"])
    g = len(report["gated_maybe_unlockable"])
    line = (
        f"- stale-sweeper ({report['run_at'][:10]}): "
        f"{n} pending>{report['threshold_weeks']}wk, "
        f"{g} gated-maybe-unlockable, "
        f"{report['pending_unstamped_count']} pending-unstamped. "
        f"See ~/.TheIgors/claudecode/logs/stale_sweep_{report['run_at'][:10]}.md"
    )
    content = slate_path.read_text()
    if "## Ad hoc" in content:
        before, _, after = content.partition("## Ad hoc")
        new = before + "## Ad hoc\n" + line + "\n" + after.split("\n", 1)[1]
        slate_path.write_text(new)
    else:
        slate_path.write_text(content + f"\n## Ad hoc\n{line}\n")


def write_log(report: dict, rendered: str) -> Path:
    log_dir = Path.home() / ".TheIgors/claudecode/logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / f"stale_sweep_{report['run_at'][:10]}.md"
    log_path.write_text(rendered)
    return log_path


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--weeks", type=int, default=DEFAULT_WEEKS)
    p.add_argument("--include-gated", action="store_true")
    p.add_argument("--json", action="store_true")
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args()

    report = sweep(args.weeks, args.include_gated)

    if args.json:
        print(json.dumps(report, indent=2, default=str))
        return 0

    rendered = render_report(report)
    print(rendered)

    if not args.dry_run:
        log_path = write_log(report, rendered)
        append_to_slate(report)
        print(f"\n[wrote log → {log_path}; appended one-liner to today's slate]")
    else:
        print("\n[dry-run: not touching slate or log]")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
