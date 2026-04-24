#!/usr/bin/env python3
"""cleanup_kernel_debris.py — T-kernel-debris-db-cleanup one-shot.

Context
───────
Three 2026-04-05 CC-to-Igor negation memories ("SPAWNIF belongs in
cognition/node_executor.py — NOT brainstem/kernel.py") kept feeding the tier2
retrieval stack as co-activation signal for 'brainstem/kernel.py'. The
negation doesn't survive tokenization, so the LLM just sees the forbidden
path co-located with SITUATE/HIGH-inertia language and reaches for it.

Action
──────
1. Delete the 3 stale memories (two duplicate FACTUAL ingests + one EPISODIC).
2. Flag the two parent tickets (T-scope-guard-reattempt-loop,
   T-scope-guard-echo-dedup) with
   metadata['superseded_by']='T-situate-kernel-hallucination-fix' so
   retrieval deprioritizes them but they remain readable.

Idempotent: guarded by id existence. SLATE-20260414 (REFERENCE) is a
generated slate snapshot — left alone per ticket scope.
"""

from __future__ import annotations

import json
import os
import sys

import psycopg2

DB_URL = os.getenv("IGOR_HOME_DB_URL")
if not DB_URL:
    print("IGOR_HOME_DB_URL is required", file=sys.stderr)
    sys.exit(1)


TO_DELETE = [
    "20260405215531513683",  # FACTUAL, ch=repl
    "20260405215531481693",  # FACTUAL, ch=web:?
    "20260405213427317066",  # EPISODIC
]

TO_FLAG = [
    "T-scope-guard-reattempt-loop",
    "T-scope-guard-echo-dedup",
]

SUPERSEDED_BY = "T-situate-kernel-hallucination-fix"


def main() -> int:
    conn = psycopg2.connect(DB_URL)
    cur = conn.cursor()
    cur.execute("SET search_path TO clan, public")

    cur.execute(
        "SELECT COUNT(*) FROM memories WHERE narrative ILIKE %s",
        ("%brainstem/kernel%",),
    )
    before = cur.fetchone()[0]
    print(f"before: {before} memories reference brainstem/kernel.py")

    deleted = 0
    for mid in TO_DELETE:
        # Clean FK children first (embeddings, blobs, interpretive edges to/from)
        cur.execute("DELETE FROM memory_embeddings WHERE memory_id = %s", (mid,))
        cur.execute("DELETE FROM memory_blobs WHERE memory_id = %s", (mid,))
        cur.execute(
            "DELETE FROM interpretive_edges WHERE from_id = %s OR to_id = %s",
            (mid, mid),
        )
        cur.execute("DELETE FROM memories WHERE id = %s", (mid,))
        if cur.rowcount:
            deleted += 1
            print(f"  deleted {mid}")
        else:
            print(f"  skipped {mid} (not present)")

    flagged = 0
    for tid in TO_FLAG:
        cur.execute("SELECT metadata FROM memories WHERE id = %s", (tid,))
        row = cur.fetchone()
        if not row:
            print(f"  skipped {tid} (not present)")
            continue
        meta = row[0] or {}
        if isinstance(meta, str):
            meta = json.loads(meta) if meta else {}
        if meta.get("superseded_by") == SUPERSEDED_BY:
            print(f"  already flagged {tid}")
            continue
        meta["superseded_by"] = SUPERSEDED_BY
        cur.execute(
            "UPDATE memories SET metadata = %s::jsonb WHERE id = %s",
            (json.dumps(meta), tid),
        )
        flagged += 1
        print(f"  flagged {tid} superseded_by={SUPERSEDED_BY}")

    conn.commit()

    cur.execute(
        "SELECT COUNT(*) FROM memories WHERE narrative ILIKE %s",
        ("%brainstem/kernel%",),
    )
    after = cur.fetchone()[0]
    print(f"after: {after} memories reference brainstem/kernel.py")
    print(f"deleted {deleted} / flagged {flagged}")

    conn.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
