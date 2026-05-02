#!/usr/bin/env python3
"""
seed_reader_habits.py — Re-express the ebook reader as an Engram habit program.
Ticket: T-reader-as-habit-program.

This is the FIRST COMPLETE MATRIX-LANGUAGE PROGRAM — the ebook reader pipeline
expressed entirely as instantiated Engram template habits.

The Python code (ebook_reader.py) is NOT replaced. Habits delegate to it via
code_ref. The value: the reader becomes a composable habit program — each step
independently scorable by BG, evolvable as a graph node, inspectable via Igor tools.

Pipeline (4 habits, mapped from Python control flow):

  1. READER_QUEUE_ITERATOR   (FILE_ITERATOR)
       source  = tools.ebook_reader:list_reading_sessions
       process = tools.ebook_reader:open_book
       → iterates reading queue, opens each book

  2. READER_BOOK_LOOP        (READER_LOOP)
       queue   = tools.ebook_reader:get_active_book_handle
       parser  = tools.ebook_reader:read_chunk
       → reads book chunk by chunk, deposits INTERPRETIVE nodes

  3. READER_CONCEPT_DEDUP    (SEARCH_AND_RESPOND)
       trigger = "reading concept extracted"
       search  = memory.cortex:search
       → before depositing a concept, checks if similar node already exists

  4. READER_CONCEPT_DEPOSIT  (MEMORY_DEPOSIT)
       deposit = "reading concept"
       classifier = tools.ebook_reader:_reading_extract_worker
       → deposits extracted concept as INTERPRETIVE Memory node

Inter-habit chaining note (scope boundary):
  How habit 1 triggers habit 2 etc. is NOT implemented here — that belongs in
  T-trails-infra. This script proves the templates are expressive enough for
  real programs. Each habit is individually correct; the pipeline wiring is next.

Run from repo root:
  cd ~/TheIgors && source venv/bin/activate
  python3 claudecode/seed_reader_habits.py [--dry-run]

Requires IGOR_HOME_DB_URL or IGOR_DB_PATH.
"""

import sys
import os
import json
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

os.environ.setdefault(
    "IGOR_DB_PATH",
    str(Path.home() / ".TheIgors" / "Igor-wild-0001" / "wild-0001.db"),
)

from wild_igor.igor.tools.template_tools import instantiate_template
from wild_igor.igor.memory.cortex import Cortex

DRY_RUN = "--dry-run" in sys.argv

# ── Template instantiations ────────────────────────────────────────────────────
# Each entry: (template_id, description, params_dict, expected_node_id)

INSTANTIATIONS = [
    # 1. FILE_ITERATOR — iterate reading queue, open each book
    (
        "tpl-file-iterator",
        "READER_QUEUE_ITERATOR — walk reading queue, open books",
        {
            "iterator_name": "reader-queue",
            "source_fn": "tools.ebook_reader:list_reading_sessions",
            "processor_fn": "tools.ebook_reader:open_book",
            "batch_size": 1,
            "cursor_key": "reading_queue_cursor",
        },
        "proc_file_iter_reader_queue",  # expected ID from template expansion
    ),
    # 2. READER_LOOP — read a book chunk by chunk
    (
        "tpl-reader-loop",
        "READER_BOOK_LOOP — read open book chunk by chunk via read_chunk()",
        {
            "reader_name": "ebook",
            "queue_source": "tools.ebook_reader:get_active_book_handle",
            "parser_fn": "tools.ebook_reader:read_chunk",
            "deposit_type": "INTERPRETIVE",
        },
        "proc_reader_ebook",
    ),
    # 3. SEARCH_AND_RESPOND — dedup check before depositing
    (
        "tpl-search-and-respond",
        "READER_CONCEPT_DEDUP — search for existing similar nodes before deposit",
        {
            "trigger_phrase": "reading concept extracted",
            "search_fn": "memory.cortex:search",
            "depth": "medium",
            "twm_ttl": 90,
        },
        "proc_sar_reading_concept_extracted",
    ),
    # 4. MEMORY_DEPOSIT — deposit extracted concept
    (
        "tpl-memory-deposit",
        "READER_CONCEPT_DEPOSIT — classify and deposit reading concept as INTERPRETIVE",
        {
            "deposit_name": "reading concept",
            "classifier_fn": "tools.ebook_reader:_reading_extract_worker",
            "memory_type": "INTERPRETIVE",
        },
        "proc_deposit_reading_concept",
    ),
]


def _get_cortex() -> Cortex:
    db_path = Path(os.environ["IGOR_DB_PATH"])
    return Cortex()


def run():
    print("=== seed_reader_habits.py — Engram reader program ===")
    print(f"  mode: {'DRY RUN' if DRY_RUN else 'LIVE'}")
    print()

    cortex = _get_cortex()
    results = []

    for tpl_id, desc, params, expected_id in INSTANTIATIONS:
        # Check for collision first
        existing = cortex.get(expected_id)
        if existing:
            print(f"  [skip] {expected_id} already exists")
            print(f"         ({desc})")
            results.append(("skip", expected_id))
            print()
            continue

        if DRY_RUN:
            print(f"  [dry]  would instantiate {tpl_id}")
            print(f"         → {expected_id}")
            print(f"         params: {json.dumps(params, indent=None)}")
            results.append(("dry", expected_id))
            print()
            continue

        print(f"  [+]    {desc}")
        result = instantiate_template(tpl_id, json.dumps(params))
        if result.startswith("ERROR"):
            print(f"  ERROR: {result}")
            results.append(("error", expected_id))
        else:
            print(f"         {result.strip()}")
            results.append(("seeded", expected_id))
        print()

    # ── Validation ────────────────────────────────────────────────────────────
    if not DRY_RUN:
        print("=== Validation ===")
        print()
        all_ok = True
        for status, node_id in results:
            if status == "error":
                print(f"  FAIL  {node_id} — seeding errored")
                all_ok = False
                continue
            node = cortex.get(node_id)
            if not node:
                print(f"  FAIL  {node_id} — not found in DB after seed")
                all_ok = False
                continue
            kind = node.metadata.get("habit_type", "?")
            code_ref = node.metadata.get("code_ref", "?")
            pattern = node.metadata.get(
                "template_pattern", node.metadata.get("pattern", "?")
            )
            origin = node.metadata.get("template_origin", "?")
            print(f"  OK    {node_id}")
            print(f"        habit_type={kind}  pattern={pattern}")
            print(f"        code_ref={code_ref}")
            print(f"        origin={origin}")
            print()

        print()
        if all_ok:
            print("Validation PASS — all 4 reader habit nodes present in DB.")
            print()
            print("Reader pipeline expressed as Engram habits:")
            print(
                "  proc_file_iter_reader_queue  (FILE_ITERATOR)  → open books from queue"
            )
            print(
                "  proc_reader_ebook            (READER_LOOP)    → read chunk by chunk"
            )
            print("  proc_sar_reading_concept_..  (SEARCH_AND_RESPOND) → dedup check")
            print(
                "  proc_deposit_reading_concept (MEMORY_DEPOSIT) → deposit INTERPRETIVE node"
            )
            print()
            print("Inter-habit chaining (how step 1 triggers step 2):")
            print(
                "  → NOT wired in this ticket (T-trails-infra). Each habit is individually"
            )
            print("    correct; pipeline orchestration is the next layer.")
        else:
            print("Validation FAIL — check errors above.")
            sys.exit(1)


if __name__ == "__main__":
    run()
