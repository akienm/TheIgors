"""
seed_annotation_habit.py — seeds PROC_ANNOTATE_LEARNING (#252).

Fires when Akien says "this worked", "didn't work", "mark that", etc.
Dispatches annotate_learning tool to deposit EXPERIENTIAL node.

Run once: python3 claudecode/seed_annotation_habit.py
"""

import os
import sys
import sqlite3
import json
import uuid
from pathlib import Path

DB_PATH = os.environ.get(
    "IGOR_DB_PATH",
    os.path.expanduser("~/.TheIgors/Igor-wild-0001/wild-0001.db"),
)

HABIT = {
    "id": "PROC_ANNOTATE_LEARNING",
    "narrative": (
        "When Akien says something worked or didn't work, deposit it as a personal "
        "EXPERIENTIAL memory with high confidence. Dispatch annotate_learning tool."
    ),
    "memory_type": "PROCEDURAL",
    "parent_id": "CP2",  # "I look for patterns" — learning from experience
    "children_ids": "[]",
    "link_ids": "[]",
    "valence": 0.4,
    "activation_count": 0,
    "friction_history": "[]",
    "metadata": json.dumps(
        {
            "trigger": (
                "this worked|that worked|didn't work|did not work|mark that|worked for me|"
                "failed for me|that approach works|that approach failed|remember this worked|"
                "annotate|this technique works|that technique failed|works well|doesn't work"
            ),
            "habit_type": "action",
            "code_ref": "tools.learner:annotate_learning",
            "inertia": 0.30,
            "source": "seed",
        }
    ),
    "portable": 1,
    "source": "seed",
    "confidence": 1.0,
    "context_of_encoding": "seed_annotation_habit.py",
}


def seed():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    existing = conn.execute(
        "SELECT id FROM memories WHERE id = ?", (HABIT["id"],)
    ).fetchone()

    if existing:
        print(f"PROC_ANNOTATE_LEARNING already exists — skipping.")
        conn.close()
        return

    ts = __import__("time").strftime("%Y-%m-%dT%H:%M:%S")
    conn.execute(
        """INSERT INTO memories
           (id, narrative, memory_type, parent_id, children_ids, link_ids,
            valence, activation_count, friction_history, timestamp, metadata,
            portable, source, confidence, context_of_encoding)
           VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (
            HABIT["id"],
            HABIT["narrative"],
            HABIT["memory_type"],
            HABIT["parent_id"],
            HABIT["children_ids"],
            HABIT["link_ids"],
            HABIT["valence"],
            HABIT["activation_count"],
            HABIT["friction_history"],
            ts,
            HABIT["metadata"],
            HABIT["portable"],
            HABIT["source"],
            HABIT["confidence"],
            HABIT["context_of_encoding"],
        ),
    )
    conn.commit()
    conn.close()
    print(f"Seeded PROC_ANNOTATE_LEARNING → DB: {DB_PATH}")


if __name__ == "__main__":
    seed()
