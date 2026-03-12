#!/usr/bin/env python3
"""
cc_deposit.py — Direct graph node deposit for Claude Code's hot session.

Claude Code calls this after answering an Igor escalation to deposit the
generalizable pattern. No OR call — CC's own reasoning IS the answer;
we just store it.

Usage:
  venv/bin/python claudecode/cc_deposit.py \
    --type procedural \
    --trigger "edit source file patch" \
    --parent_cp CP4 \
    --narrative "When editing source: read first, patch_source_file, run_syntax_check."

  --type: procedural | factual | interpretive
  --trigger: 2-8 words that fire this habit (procedural only; ignored for factual)
  --parent_cp: CP1-CP6 (optional)
  --narrative: 1-2 sentence generalizable pattern (required)
  --confidence: 0.0-1.0 (default 0.75)
  --tags: comma-separated tags (optional, factual/interpretive)
"""
import argparse
import hashlib
import os
import sys
from pathlib import Path

REPO = Path(__file__).parent.parent
sys.path.insert(0, str(REPO))

env_path = Path.home() / ".TheIgors" / "igor_wild_0001" / ".env"
if env_path.exists():
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, _, v = line.partition("=")
            os.environ.setdefault(k.strip(), v.strip())

from wild_igor.igor.memory.cortex import Cortex
from wild_igor.igor.memory.models import Memory, MemoryType

DB_PATH = Path(os.environ.get(
    "IGOR_DB_PATH",
    Path.home() / ".TheIgors" / "igor_wild_0001" / "wild-0001.db"
))

_TYPE_MAP = {
    "procedural":    MemoryType.PROCEDURAL,
    "factual":       MemoryType.FACTUAL,
    "interpretive":  MemoryType.INTERPRETIVE,
}


def main():
    parser = argparse.ArgumentParser(description="Deposit a graph node from CC hot session")
    parser.add_argument("--type",       required=True, choices=list(_TYPE_MAP))
    parser.add_argument("--narrative",  required=True)
    parser.add_argument("--trigger",    default="")
    parser.add_argument("--parent_cp",  default="")
    parser.add_argument("--confidence", type=float, default=0.75)
    parser.add_argument("--tags",       default="")
    args = parser.parse_args()

    # Stable ID from narrative hash so re-runs upsert cleanly
    node_id = "ICC_HOT_" + hashlib.sha256(args.narrative.encode()).hexdigest()[:12].upper()

    metadata: dict = {"source": "hot_cc_session", "confidence": args.confidence}
    if args.trigger:
        metadata["trigger"] = args.trigger
    if args.parent_cp:
        metadata["parent_cp"] = args.parent_cp
    if args.tags:
        metadata["tags"] = [t.strip() for t in args.tags.split(",")]

    mem = Memory(
        id=node_id,
        narrative=args.narrative,
        memory_type=_TYPE_MAP[args.type],
        activation_count=0,
        valence=0.7,
        confidence=args.confidence,
        metadata=metadata,
    )

    cortex = Cortex(DB_PATH)
    cortex.store(mem)
    print(f"deposited {node_id} ({args.type}): {args.narrative[:80]}")


if __name__ == "__main__":
    main()
