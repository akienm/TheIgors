#!/usr/bin/env python3
"""
seed_training_corpus.py — Queue pre-extracted training corpus files for book_learner.

Adds all .txt files from ~/.TheIgors/training_corpus/ to learn_queue.json as
file:// entries so drain_learn_queue.py processes them through book_learner.

Usage:
  python3 claudecode/seed_training_corpus.py [--corpus-dir PATH] [--dry-run]

Options:
  --corpus-dir PATH   Override corpus directory (default: ~/.TheIgors/training_corpus)
  --dry-run           Print what would be queued without writing
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

REPO = Path(__file__).parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "wild_igor"))

# Load .env before importing igor modules
env_path = Path.home() / ".TheIgors" / "Igor-wild-0001" / ".env"
if env_path.exists():
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, _, v = line.partition("=")
            import os

            os.environ.setdefault(k.strip(), v.strip())

from igor.paths import paths


def main():
    parser = argparse.ArgumentParser(
        description="Seed training corpus into learn queue"
    )
    parser.add_argument(
        "--corpus-dir",
        default=str(Path.home() / ".TheIgors" / "training_corpus"),
        help="Directory of .txt files to queue (default: ~/.TheIgors/training_corpus)",
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Print plan without writing"
    )
    args = parser.parse_args()

    corpus = Path(args.corpus_dir)
    if not corpus.exists():
        print(f"ERROR: corpus directory not found: {corpus}")
        sys.exit(1)

    files = sorted(corpus.glob("*.txt"))
    if not files:
        print(f"No .txt files found in {corpus}")
        sys.exit(0)

    queue_path = paths().learn_queue
    try:
        existing = json.loads(queue_path.read_text()) if queue_path.exists() else []
    except Exception:
        existing = []

    existing_urls = {e.get("url") for e in existing}

    new_entries = []
    skipped = 0
    for f in files:
        url = f.as_uri()  # file:///home/akien/.TheIgors/training_corpus/xxx.txt
        if url in existing_urls:
            skipped += 1
            continue
        new_entries.append(
            {
                "url": url,
                "title": f.stem,
                "topic": "training_corpus",
                "added_at": datetime.now().isoformat(),
                "cloud_ok": False,  # local-only — these are background training files
                "done": False,
            }
        )

    print(f"Corpus: {len(files)} files in {corpus}")
    print(f"Already queued: {skipped}")
    print(f"New to queue: {len(new_entries)}")

    if args.dry_run:
        for e in new_entries[:10]:
            print(f"  would add: {e['title']} ({e['url']})")
        if len(new_entries) > 10:
            print(f"  ... and {len(new_entries) - 10} more")
        print("(dry run — nothing written)")
        return

    combined = existing + new_entries
    queue_path.parent.mkdir(parents=True, exist_ok=True)
    queue_path.write_text(json.dumps(combined, indent=2))
    print(f"Written {len(new_entries)} entries to {queue_path}")
    print(
        f"Queue total: {len(combined)} ({len([e for e in combined if not e.get('done')])} pending)"
    )


if __name__ == "__main__":
    main()
