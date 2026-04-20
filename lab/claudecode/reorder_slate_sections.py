#!/usr/bin/env python3
"""
reorder_slate_sections.py — one-shot: reorder existing slate files to salience-first.

T-slate-section-reorder / D-slate-salience-order-2026-04-20.

New section order (salience-first):
    1. ## Next up       — what to work on now (was: Planned — next up)
    2. ## Blocked       — unblockable candidates
    3. ## After that    — rest of queue (was: Planned — remaining / Planned)
    4. ## Decided       — decisions filed this session
    5. ## Done          — shipped today (was: Done today)
    6. ## Ad hoc        — preserved as-is at end (legacy catch-all)
    7. ## Slate summary — preserved as-is at very end (historical recap)

Parses existing slate, renames sections by longest-match prefix, re-emits
in canonical order. Sections not in the rename map are preserved in a
stable order after the canonical ones. File header (# Slate YYYY-MM-DD)
and any pre-section content are preserved verbatim.

Usage:
    python3 reorder_slate_sections.py --dry-run
    python3 reorder_slate_sections.py
"""

from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path

SLATES_DIR = Path(os.path.expanduser("~/.TheIgors/claudecode"))
SLATE_FILE_RE = re.compile(r"^(\d{8})\.slate\.txt$")

# longest-match-first; header text is what follows "## "
RENAME_MAP = [
    ("Planned — next up", "Next up"),
    ("Planned — remaining", "After that"),
    ("Done today", "Done"),
    ("Planned", "After that"),
]

# Canonical order (sections not listed appear after, preserving file order)
CANONICAL_ORDER = [
    "Next up",
    "Blocked",
    "After that",
    "Decided",
    "Done",
    "Ad hoc",
    "Slate summary",
]


def rename_header(header_text: str) -> str:
    """Rename a section header by longest-match prefix. Preserves suffix."""
    for old, new in RENAME_MAP:
        if header_text == old:
            return new
        if header_text.startswith(old + " "):
            return new + header_text[len(old) :]
    return header_text


def parse_slate(content: str) -> tuple[str, list[tuple[str, list[str]]]]:
    """Split slate into (preamble, [(section_name, body_lines), ...])."""
    lines = content.splitlines()
    preamble: list[str] = []
    sections: list[tuple[str, list[str]]] = []
    current_name: str | None = None
    current_body: list[str] = []
    for line in lines:
        m = re.match(r"^##\s+(.+?)\s*$", line)
        if m:
            if current_name is None:
                # everything before first section
                pass
            else:
                sections.append((current_name, current_body))
            current_name = m.group(1)
            current_body = []
        else:
            if current_name is None:
                preamble.append(line)
            else:
                current_body.append(line)
    if current_name is not None:
        sections.append((current_name, current_body))
    return ("\n".join(preamble), sections)


def canonical_rank(name: str) -> int | None:
    """Return rank if name starts with a canonical key, else None.
    Matches longest canonical first to avoid e.g. 'Done' swallowing a future
    'Done something-specific' before a more-specific rule ever lands.
    """
    for i, canon in enumerate(CANONICAL_ORDER):
        if (
            name == canon
            or name.startswith(canon + " ")
            or name.startswith(canon + "—")
        ):
            return i
    return None


def sort_sections(
    sections: list[tuple[str, list[str]]],
) -> list[tuple[str, list[str]]]:
    """Sort by canonical prefix; unknown sections keep original order after."""
    indexed = list(enumerate(sections))
    unknown_base = len(CANONICAL_ORDER)

    def key(t):
        idx, (name, _) = t
        rank = canonical_rank(name)
        return (rank if rank is not None else unknown_base + idx, idx)

    indexed.sort(key=key)
    return [s for _, s in indexed]


def render_slate(preamble: str, sections: list[tuple[str, list[str]]]) -> str:
    parts: list[str] = []
    if preamble.strip():
        parts.append(preamble)
    else:
        parts.append(preamble)  # keep the blank line discipline
    for name, body in sections:
        parts.append(f"## {name}")
        # Trim trailing blank lines from body, we'll add exactly one
        while body and not body[-1].strip():
            body = body[:-1]
        if body:
            parts.append("\n".join(body))
        parts.append("")  # one blank after each section
    result = "\n".join(parts)
    # Ensure trailing newline, no double blanks at very end
    result = result.rstrip() + "\n"
    return result


def transform(content: str) -> str:
    preamble, sections = parse_slate(content)
    renamed = [(rename_header(name), body) for name, body in sections]
    sorted_sections = sort_sections(renamed)
    return render_slate(preamble, sorted_sections)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args()

    slates = sorted(p for p in SLATES_DIR.iterdir() if SLATE_FILE_RE.match(p.name))
    print(f"Slates: {len(slates)}")
    print(f"Mode: {'DRY RUN' if args.dry_run else 'LIVE'}")
    print()

    changed = 0
    unchanged = 0
    for slate in slates:
        before = slate.read_text()
        after = transform(before)
        if before == after:
            unchanged += 1
            print(f"  {slate.name:30s} unchanged")
            continue
        changed += 1
        if args.dry_run:
            print(
                f"  {slate.name:30s} would change ({len(before)} → {len(after)} bytes)"
            )
        else:
            slate.write_text(after)
            print(f"  {slate.name:30s} rewrote ({len(before)} → {len(after)} bytes)")

    print()
    print(f"Changed: {changed}, unchanged: {unchanged}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
