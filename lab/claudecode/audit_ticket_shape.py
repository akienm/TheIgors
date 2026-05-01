"""audit_ticket_shape.py — pre-sprint shape filter for ticket queue.

Runs the structured shape checks that every ticket should pass before being
sprintable. The discipline: don't give Igor (or any worker) work whose shape
hasn't been verified — that's the failure mode where Opus says "this would be
hard for me," meaning it's definitely too hard for smaller models.

## What it checks
1. Has the ticket got a description / notes / body at all?
2. Does it name the affected files (any phrasing — formal "Affected files:"
   header, "## Shape" section, backtick-quoted file paths, etc)?
3. Does it describe a test plan (or explicitly waive it)?
4. Is it a self-declared epic / vision / discussion (auto-exempt)?

## How to invoke
    python3 lab/claudecode/audit_ticket_shape.py             # default report
    python3 lab/claudecode/audit_ticket_shape.py --verbose   # show every ticket

## Read order vs filing-time /audit-ticket
This is the BATCH check across the whole open queue. The /audit-ticket skill
runs the same shape-checks at filing time (one-ticket gate). They share the
classification logic.

## History
- v1 (2026-05-01): literal "affected files" string match — hugely false-positive.
- v2 (2026-05-01): broader regex set + epic auto-detection.
- v3 (2026-05-01): notes-aware (some tickets store description in `notes`).
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

QUEUE_PATH = Path.home() / ".TheIgors" / "cc_channel" / "queue.json"


def get_full_desc(t: dict) -> str:
    """Description can live in description, body, or notes — concat all three."""
    parts = []
    for key in ("description", "body", "notes"):
        v = (t.get(key) or "").strip()
        if v:
            parts.append(v)
    return "\n\n".join(parts)


_AFFECTED_PATTERNS = [
    r"\*?\*?affected\s+files?\*?\*?\s*:",
    r"##\s+affected",
    r"##\s+shape\b",
    r"\*?\*?modifies?\*?\*?\s*:",
    r"\bfile\s*\(?s?\)?\s*to\s+(touch|edit|modify|change)",
    r"^\s*-\s+(/?[a-z_]+/[a-z_/]+\.py)",
    r"`[a-z_/]+\.py`",
    r"`[a-z_]+:[a-z_]+`",
]


def has_affected_files(desc: str) -> bool:
    if not desc:
        return False
    for p in _AFFECTED_PATTERNS:
        if re.search(p, desc, re.IGNORECASE | re.MULTILINE):
            return True
    return False


_TEST_PLAN_PATTERNS = [
    r"\*?\*?test\s+plan\*?\*?\s*:",
    r"##\s+test",
    r"\bno\s+tests?\s+(because|needed)",
    r"\btests?\s+(in|for|cover|verify)",
    r"\btest\s+(file|case|suite)",
    r"\btests/test_",
    r"contract\s+tests?",
    r"regression\s+tests?",
]


def has_test_plan(desc: str) -> bool:
    if not desc:
        return False
    for p in _TEST_PLAN_PATTERNS:
        if re.search(p, desc, re.IGNORECASE):
            return True
    return False


_EPIC_MARKERS = [
    "epic:",
    "umbrella ticket",
    "tracking ticket",
    "vision-level placeholder",
    "vision-level",
    "design conversation",
    "sketch, not binding",
    "to be refined at sprint",
]


def is_epic_or_vision(t: dict) -> bool:
    """Tickets explicitly framed as vision/epic/discussion — exempt from sprint-ready filter.

    Three escape hatches: (1) `epic` tag, (2) size=discussion, (3) self-declared
    via marker phrases in description/title.
    """
    tags = [tag.lower() for tag in (t.get("tags") or [])]
    if "epic" in tags:
        return True
    if t.get("size") == "discussion":
        return True
    desc = get_full_desc(t).lower()
    title = (t.get("title") or "").lower()
    return any(m in desc or m in title for m in _EPIC_MARKERS)


def classify(t: dict) -> str:
    """Return one of: 'epic', 'empty', 'no-affected', 'no-test-plan', 'well-formed'."""
    desc = get_full_desc(t)
    if not desc.strip():
        return "empty"
    if is_epic_or_vision(t):
        return "epic"
    files = has_affected_files(desc)
    tests = has_test_plan(desc)
    if files and tests:
        return "well-formed"
    if not files:
        return "no-affected"
    return "no-test-plan"


def audit_queue(queue_path: Path = QUEUE_PATH, verbose: bool = False) -> dict:
    """Run shape audit across all pending tickets. Returns counts + lists."""
    with open(queue_path) as f:
        queue = json.load(f)
    pending = [t for t in queue if t.get("status") == "pending"]

    buckets: dict[str, list[str]] = {
        "well-formed": [],
        "epic": [],
        "empty": [],
        "no-affected": [],
        "no-test-plan": [],
    }

    for t in pending:
        cls = classify(t)
        tid = t.get("id", "?")
        size = t.get("size", "?")
        title = (t.get("title") or "")[:55]
        buckets[cls].append(
            f"{tid} ({size}): {title}"
            if verbose or cls != "well-formed"
            else f"{tid} ({size})"
        )

    return {
        "total_pending": len(pending),
        "buckets": buckets,
    }


def print_report(result: dict, verbose: bool = False) -> None:
    total = result["total_pending"]
    b = result["buckets"]
    print(f"\n{'=' * 70}")
    print(f"PRE-SPRINT SHAPE AUDIT — {total} pending tickets")
    print("=" * 70)
    print(f"\nWell-formed (sprint-ready):  {len(b['well-formed'])}")
    print(f"Epic/vision (exempt):        {len(b['epic'])}")
    print(f"Empty:                       {len(b['empty'])}")
    print(f"Missing affected files:      {len(b['no-affected'])}")
    print(f"Missing test plan:           {len(b['no-test-plan'])}")

    for bucket_name in ("empty", "no-affected", "no-test-plan", "epic"):
        items = b[bucket_name]
        if items:
            print(f"\n--- {bucket_name.upper().replace('-', ' ')} ({len(items)}) ---")
            for x in items:
                print(f"  {x}")

    if verbose and b["well-formed"]:
        print(f"\n--- WELL-FORMED ({len(b['well-formed'])}) ---")
        for x in b["well-formed"]:
            print(f"  {x}")


def main(argv: list[str] | None = None) -> int:
    argv = argv or sys.argv[1:]
    verbose = "--verbose" in argv or "-v" in argv
    result = audit_queue(verbose=verbose)
    print_report(result, verbose=verbose)
    findings = (
        len(result["buckets"]["empty"])
        + len(result["buckets"]["no-affected"])
        + len(result["buckets"]["no-test-plan"])
    )
    return 0 if findings == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
