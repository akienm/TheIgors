#!/usr/bin/env python3
"""
Run the inner_cc curriculum — deposits programming/architecture graph nodes
into Igor's live DB by walking through CURRICULUM one question at a time.

Each question is one small API call. The run is resumable: already-deposited
topics are skipped by checking for existing ICC_ nodes with matching source_question.

Cost estimate: ~28 questions × ~400 tokens each ≈ 11,200 tokens total
  At gpt-4o-mini rates (~$0.15/1M input + $0.60/1M output): < $0.02 total
  At claude-haiku rates (~$0.25/1M input + $1.25/1M output): < $0.05 total

Run:
  python claudecode/run_inner_cc_curriculum.py            # dry run (print questions)
  python claudecode/run_inner_cc_curriculum.py --run      # actually call + deposit
  python claudecode/run_inner_cc_curriculum.py --run --model openai/gpt-4o-mini
  python claudecode/run_inner_cc_curriculum.py --resume   # skip already-deposited

Akien's icing goes at the bottom of this file in CUSTOM_CURRICULUM.
"""

import argparse
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "wild_igor"))
os.environ.setdefault("IGOR_DB_PATH",
    str(Path.home() / ".TheIgors/igor_wild_0001/wild-0001.db"))

from igor.memory.cortex import Cortex
from igor.tools.inner_cc import CURRICULUM, call_inner_cc

db_path = os.environ["IGOR_DB_PATH"]
cortex = Cortex(Path(db_path))


# ── Akien's icing — add custom questions here ─────────────────────────────────
# These run AFTER the base curriculum. Add anything specific to how YOU think
# about code and architecture. These become Igor's personalized reasoning substrate.

CUSTOM_CURRICULUM = [
    # Examples — replace / extend with your own:
    # ("architecture", "What is Akien's 'How must this work?' heuristic and when does it fire?"),
    # ("pattern", "What is the pattern for designing a system that degrades gracefully under resource pressure?"),
    # ("architecture", "How does Igor's interpretive layer connect values (CP1-CP6) to code decisions?"),
]


def already_deposited(question: str) -> bool:
    """Check if this question was already processed in a previous run."""
    try:
        results = cortex.search(question[:60], limit=5, min_score=0.7)
        for mem in results:
            if mem.metadata.get("source_question", "")[:60] == question[:60]:
                return True
    except Exception:
        pass
    return False


def run_curriculum(questions: list, dry_run: bool, resume: bool, model: str) -> None:
    total = len(questions)
    deposited_total = 0
    skipped = 0
    errors = 0

    print(f"\nInner CC curriculum — {total} questions")
    print(f"Model: {model}")
    print(f"Mode: {'DRY RUN' if dry_run else 'LIVE'}")
    print("─" * 60)

    for i, (mode, question) in enumerate(questions, 1):
        prefix = f"[{i:02d}/{total}] [{mode}]"

        if resume and already_deposited(question):
            print(f"{prefix} SKIP (already deposited): {question[:60]}...")
            skipped += 1
            continue

        print(f"{prefix} {question[:70]}...")

        if dry_run:
            continue

        result = call_inner_cc(
            question=question,
            mode=mode,
            cortex=cortex,
            model=model,
        )

        answer   = result.get("answer", "")
        nodes    = result.get("nodes", [])
        follow   = result.get("follow_up", "")
        n_dep    = len([n for n in nodes if n.get("confidence", 0) >= 0.55])
        deposited_total += n_dep

        status = f"→ {n_dep} node(s) deposited"
        if "error" in answer.lower() or not answer:
            status = "→ ERROR"
            errors += 1
        print(f"  {status}")
        if follow:
            print(f"  follow-up: {follow[:80]}")

        # Brief pause — don't hammer the API
        time.sleep(0.3)

    print("─" * 60)
    if not dry_run:
        print(f"Done. {deposited_total} nodes deposited. {skipped} skipped. {errors} errors.")
    else:
        print(f"Dry run complete. {total} questions ready to run.")
        print("Add --run to execute.")


def main():
    parser = argparse.ArgumentParser(description="Run inner_cc curriculum training")
    parser.add_argument("--run",    action="store_true", help="Actually call API (default: dry run)")
    parser.add_argument("--resume", action="store_true", help="Skip questions already deposited")
    parser.add_argument("--model",  default=os.getenv("INNER_CC_MODEL", "openai/gpt-4o-mini"),
                        help="Model to use (default: INNER_CC_MODEL env or gpt-4o-mini)")
    parser.add_argument("--custom-only", action="store_true",
                        help="Run only CUSTOM_CURRICULUM (Akien's icing), skip base")
    args = parser.parse_args()

    questions = []
    if not args.custom_only:
        questions.extend(CURRICULUM)
    if CUSTOM_CURRICULUM:
        questions.extend(CUSTOM_CURRICULUM)

    run_curriculum(
        questions=questions,
        dry_run=not args.run,
        resume=args.resume,
        model=args.model,
    )


if __name__ == "__main__":
    main()
