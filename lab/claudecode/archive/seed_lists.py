"""
seed_lists.py — D095: seed the Registry:Tags list with initial canonical tags.

Run once (idempotent — list_set is upsert):
    python3 ~/TheIgors/lab/claudecode/seed_lists.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from wild_igor.igor.memory.cortex import Cortex

DB_PATH = Path.home() / ".TheIgors" / "Igor-wild-0001" / "wild-0001.db"

REGISTRY_TAGS = [
    ("project", "a long-lived initiative with its own memory/habit graph"),
    ("template", "reusable project scaffold (instantiate to create a new project)"),
    ("registry", "a list that catalogs other lists, tags, or capabilities"),
    ("software", "software development project"),
    ("cc_ops", "habit executable directly via CC bridge /api/execute_habit"),
]


def main():
    cortex = Cortex()
    for tag_name, description in REGISTRY_TAGS:
        cortex.list_set(
            list_name="Registry:Tags",
            item_key=tag_name,
            item_value=description,
            ref_type="string",
        )
        print(f"  seeded Registry:Tags / {tag_name}")

    # Verify
    items = cortex.list_all("Registry:Tags")
    print(f"\nRegistry:Tags now has {len(items)} items:")
    for item in items:
        print(f"  {item['item_key']:16s}  {item['item_value']}")


if __name__ == "__main__":
    main()
