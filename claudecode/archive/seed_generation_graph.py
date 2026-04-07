"""
seed_generation_graph.py — G37: Bootstrap the generation (voice) word graph.

Extracts Igor's historical reply text from:
  1. ring_memory DB (category not in user_turn — these are Igor's reasoning entries)
  2. reasoning_calls.log (resp= fields in forensic log)

Seeds wild_igor/cognition/word_graph.py WordGraph(name="generation_graph")
and saves to ~/.TheIgors/generation_graph.json.

Run from repo root:
  python claudecode/seed_generation_graph.py [--dry-run]

The recognition graph (word_graph.json) is built from habit triggers and narratives.
The generation graph is built from Igor's actual historical replies — the residue of
what produced comprehension in the other person.
"""

from __future__ import annotations

import argparse
import re
import sqlite3
import sys
from pathlib import Path

# ── Paths ──────────────────────────────────────────────────────────────────────
REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

DATA_DIR = Path.home() / ".TheIgors" / "Igor-wild-0001"
DB_PATH = DATA_DIR / "wild-0001.db"
LOG_DIR = Path.home() / ".TheIgors" / "logs"
OUTPUT_PATH = Path.home() / ".TheIgors" / "generation_graph.json"


def extract_replies_from_ring(db_path: Path) -> list[str]:
    """
    Extract Igor's reply text from ring_memory.
    Ring entries have the format:  Q: <user> | A: <reply> | intent=...
    We want the A: portion.
    """
    if not db_path.exists():
        print(f"[SKIP] DB not found: {db_path}")
        return []
    replies = []
    try:
        conn = sqlite3.connect(str(db_path))
        cur = conn.execute(
            "SELECT content FROM ring_memory WHERE category != 'user_turn' ORDER BY id DESC LIMIT 2000"
        )
        for (content,) in cur:
            # Extract A: portion from "Q: ... | A: reply | intent=..."
            m = re.search(r'\| A: (.+?)(?:\| intent=|$)', content)
            if m:
                reply = m.group(1).strip()
                if len(reply) > 20:
                    replies.append(reply)
            else:
                # reasoning entries that are just Igor's output
                if len(content) > 20 and not content.startswith("USER_INPUT"):
                    replies.append(content)
        conn.close()
    except Exception as e:
        print(f"[WARN] ring_memory extraction failed: {e}")
    return replies


def extract_replies_from_reasoning_log(log_dir: Path) -> list[str]:
    """
    Extract resp= fields from reasoning_calls.log.
    Format: resp=<text>|tokens=...
    """
    log_file = log_dir / "reasoning_calls.log"
    if not log_file.exists():
        print(f"[SKIP] Log not found: {log_file}")
        return []
    replies = []
    try:
        for line in log_file.read_text(encoding="utf-8", errors="replace").splitlines():
            m = re.search(r'resp=(.+?)(?:\|tokens=|$)', line)
            if m:
                reply = m.group(1).strip()
                if len(reply) > 20:
                    replies.append(reply)
    except Exception as e:
        print(f"[WARN] reasoning_calls.log extraction failed: {e}")
    return replies


def main():
    parser = argparse.ArgumentParser(description="Seed generation graph from Igor's historical replies")
    parser.add_argument("--dry-run", action="store_true", help="Show stats without writing")
    args = parser.parse_args()

    from wild_igor.igor.cognition.word_graph import WordGraph

    print("Extracting Igor's historical replies...")
    ring_replies = extract_replies_from_ring(DB_PATH)
    log_replies = extract_replies_from_reasoning_log(LOG_DIR)
    all_replies = ring_replies + log_replies
    print(f"  ring_memory: {len(ring_replies)} entries")
    print(f"  reasoning_calls.log: {len(log_replies)} entries")
    print(f"  total: {len(all_replies)} reply texts")

    if not all_replies:
        print("[WARN] No replies found — generation graph will be empty.")
        print("  This is expected on a fresh install. The graph will grow naturally.")

    print("Building generation graph...")
    g = WordGraph(name="generation_graph")
    for i, reply in enumerate(all_replies):
        doc_id = f"hist_{i:05d}"
        g.index(doc_id, reply, weight=1.0, lang="en")
    g.build_idf()

    print(f"  {len(g._word_to_ids)} word nodes")
    print(f"  {sum(len(co) for co in g._cooccur.values())} co-occurrence edges")
    print(f"  {g._doc_count} documents indexed")

    if args.dry_run:
        print("[DRY-RUN] Not writing. Pass without --dry-run to save.")
        return

    g.save(OUTPUT_PATH)
    print(f"Saved to {OUTPUT_PATH}")
    print("Done. Restart Igor to load the generation graph (IGOR_DUAL_WORD_GRAPHS=true).")


if __name__ == "__main__":
    main()
