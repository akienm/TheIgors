"""ticket_prefix_refit.py — Retroactive prefix refit for open tickets.

Applies status prefixes to all pending/in_progress/blocked ticket titles:
  DESIGNED:     all 4 description sections present
  NEEDS DESIGN: some sections present but not all
  NEW:          no structured description sections

Done tickets are left alone — CLOSED: is applied going forward by /done.

Usage:
  python3 lab/claudecode/ticket_prefix_refit.py [--dry-run]
"""

from __future__ import annotations

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

KNOWN_PREFIXES = ("DESIGNED: ", "NEEDS DESIGN: ", "NEW: ", "CLOSED: ")
OPEN_STATUSES = ("pending", "in_progress", "blocked", "open")
SECTIONS = (
    "**Affected files:**",
    "**Design rules:**",
    "**Scope boundary:**",
    "**Test plan:**",
)


def _strip_prefix(title: str) -> str:
    for p in KNOWN_PREFIXES:
        if title.startswith(p):
            return title[len(p) :]
    return title


def _assign_prefix(desc: str) -> str:
    hits = sum(1 for s in SECTIONS if s in desc)
    if hits == 4:
        return "DESIGNED: "
    if hits > 0:
        return "NEEDS DESIGN: "
    return "NEW: "


def main(dry_run: bool = False) -> None:
    from lab.claudecode.cc_queue import load_tasks, save_tasks

    tasks = load_tasks()
    changed = []

    for t in tasks:
        if t.get("status") not in OPEN_STATUSES:
            continue
        bare = _strip_prefix(t.get("title", ""))
        prefix = _assign_prefix(t.get("description") or "")
        new_title = prefix + bare
        if new_title != t.get("title"):
            changed.append((t["id"], t["title"], new_title))
            if not dry_run:
                t["title"] = new_title

    if not dry_run and changed:
        save_tasks(tasks)

    if changed:
        for tid, old, new in changed:
            marker = "[DRY] " if dry_run else ""
            print(f"{marker}{tid}:")
            print(f"  - {old}")
            print(f"  + {new}")
    else:
        print("No changes needed.")

    print(f"\n{'[DRY-RUN] ' if dry_run else ''}{len(changed)} ticket(s) updated.")


if __name__ == "__main__":
    dry_run = "--dry-run" in sys.argv
    main(dry_run=dry_run)
