#!/usr/bin/env python3
"""
reading_integrator.py — T-reading-integration #295: second-pass pipeline.

Backfills the 5 integration steps for existing reading memories that were
deposited without full encoding (BL_* from book_learner, READ_* from ebook_reader):

  1. Embed    — computes and stores embedding (makes node findable by semantic search)
  2. Link     — finds similar existing nodes, creates weighted edges
  3. Spine    — groups by book_title, creates/finds BOOK_ + CHAPTER_ spine nodes,
                sets parent_id and adds_child entries
  4. Interp   — adds interpretive_edge from best-matching CP if none exists
  5. Arousal  — sets arousal from CP keyword affinity if still at 0.0

Usage:
  python3 claudecode/reading_integrator.py --book "Descartes Error"
  python3 claudecode/reading_integrator.py --all
  python3 claudecode/reading_integrator.py --all --dry-run

Options:
  --book STR    Process only nodes with this book_title in metadata
  --all         Process all reading/book_learner memories missing embeddings
  --dry-run     Show what would be done without writing anything
  --batch INT   Nodes per run (default: 200; avoid Ollama overload)
  --link-top N  Max link edges to create per node (default: 3)
"""

import argparse
import hashlib
import json
import logging
import os
import sys
import time
from datetime import datetime
from pathlib import Path

REPO = Path(__file__).parent.parent
sys.path.insert(0, str(REPO))

env_path = Path.home() / ".TheIgors" / "Igor-wild-0001" / ".env"
if env_path.exists():
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, _, v = line.partition("=")
            os.environ.setdefault(k.strip(), v.strip())

from igor.cognition import milieu as _milieu_mod
from igor.memory.cortex import Cortex
from igor.memory.models import Memory, MemoryType

from lab.utility_closet.agent_base import get_logger

LOG_PATH = Path.home() / ".TheIgors" / "logs" / "reading_integrator.log"

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
logger = get_logger("reading_integrator")


def _log(msg: str) -> None:
    logger.info(msg)
    try:
        LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        entry = f"{datetime.now().isoformat()} {msg}\n"
        existing = LOG_PATH.read_text() if LOG_PATH.exists() else ""
        LOG_PATH.write_text(entry + existing)
    except Exception:
        pass


# ── Spine helpers ─────────────────────────────────────────────────────────────


def _book_node_id(book_title: str) -> str:
    h = hashlib.md5(book_title.encode()).hexdigest()[:8].upper()
    return f"BOOK_{h}"


def _chapter_node_id(book_node_id: str, chapter_num: int) -> str:
    return f"{book_node_id}_CH{chapter_num:03d}"


def _ensure_book_node(
    cortex: Cortex, book_title: str, author: str, dry_run: bool
) -> str:
    nid = _book_node_id(book_title)
    if cortex.get(nid) is None and not dry_run:
        mem = Memory(
            id=nid,
            narrative=f"Book: {book_title} by {author}",
            memory_type=MemoryType.FACTUAL,
            source="reading_integrator",
            confidence=1.0,
            context_of_encoding="book_spine",
            metadata={"book_title": book_title, "book_author": author, "spine": True},
        )
        cortex.store(mem)
    return nid


def _ensure_chapter_node(
    cortex: Cortex,
    book_node_id: str,
    book_title: str,
    chapter_num: int,
    chapter_title: str,
    dry_run: bool,
) -> str:
    nid = _chapter_node_id(book_node_id, chapter_num)
    if cortex.get(nid) is None and not dry_run:
        narrative = f"Chapter {chapter_num}"
        if chapter_title:
            narrative += f": {chapter_title}"
        narrative += f" — {book_title[:40]}"
        mem = Memory(
            id=nid,
            narrative=narrative,
            memory_type=MemoryType.FACTUAL,
            parent_id=book_node_id,
            source="reading_integrator",
            confidence=1.0,
            context_of_encoding="book_spine",
            metadata={
                "book_title": book_title,
                "chapter": chapter_num,
                "chapter_title": chapter_title,
                "spine": True,
            },
        )
        cortex.store(mem)
        try:
            cortex.add_child(book_node_id, nid)
        except Exception:
            pass
    return nid


# ── Candidate fetch ───────────────────────────────────────────────────────────


def _fetch_candidates(cortex: Cortex, book_filter: str, batch: int) -> list:
    """
    Return reading/book_learner memories that are missing embeddings.
    book_filter: book_title substring to match (empty = all).
    Uses cortex DB connection (Postgres-aware via db_proxy).
    """
    try:
        with cortex._db() as conn:
            rows = conn.execute(
                """
                SELECT m.id, m.narrative, m.memory_type, m.parent_id, m.metadata,
                       m.arousal, m.confidence, m.source
                FROM memories m
                LEFT JOIN memory_embeddings me ON me.memory_id = m.id
                WHERE m.source IN ('reading', 'book_learner')
                  AND me.memory_id IS NULL
                LIMIT ?
                """,
                (batch,),
            ).fetchall()
    except Exception as e:
        logger.warning(f"_fetch_candidates query failed: {e}")
        return []

    # Convert rows to dicts for uniform access
    col_names = [
        "id",
        "narrative",
        "memory_type",
        "parent_id",
        "metadata",
        "arousal",
        "confidence",
        "source",
    ]
    dict_rows = []
    for r in rows:
        if hasattr(r, "keys"):
            dict_rows.append(dict(r))
        else:
            dict_rows.append(dict(zip(col_names, r)))

    if book_filter:
        out = []
        bf = book_filter.lower()
        for r in dict_rows:
            meta_raw = r.get("metadata")
            meta = (
                json.loads(meta_raw) if isinstance(meta_raw, str) else (meta_raw or {})
            )
            title = (meta.get("book_title") or meta.get("book") or "").lower()
            if bf in title:
                out.append(r)
        return out
    return dict_rows


# ── Per-node integration ──────────────────────────────────────────────────────


def _integrate_node(
    cortex: Cortex,
    row,
    spine_cache: dict,
    link_top: int,
    dry_run: bool,
) -> dict:
    """
    Run all 5 integration steps for one memory row.
    Returns a stats dict: {embed, links, spine, interp, arousal}.
    """
    mem = cortex.get(row["id"])
    if mem is None:
        return {
            "embed": False,
            "links": 0,
            "spine": False,
            "interp": False,
            "arousal": False,
        }

    meta = json.loads(row["metadata"]) if row["metadata"] else {}
    book_title = meta.get("book_title") or meta.get("book") or ""
    author = meta.get("book_author") or ""
    chapter_num = meta.get("chunk_position", 0) // 15  # rough chapter from chunk_pos
    chapter_title = meta.get("chapter_title", "")
    stats = {
        "embed": False,
        "links": 0,
        "spine": False,
        "interp": False,
        "arousal": False,
    }

    # Step 1: Embed
    try:
        if not dry_run:
            cortex._get_or_compute_embedding(mem)
        stats["embed"] = True
    except Exception as e:
        _log(f"  [embed FAIL] {mem.id}: {e}")

    # Step 2: Link — search for similar nodes, create weighted edges
    if stats["embed"] and not dry_run:
        try:
            results = cortex.search(mem.narrative, limit=link_top + 1)
            related = [r for r in results if r.id != mem.id][:link_top]
            if related:
                # Re-store with link_to to write edges
                cortex.store(mem, link_to=related)
                stats["links"] = len(related)
        except Exception as e:
            _log(f"  [link FAIL] {mem.id}: {e}")

    # Step 3: Spine — build BOOK_/CHAPTER_ hierarchy, set parent_id
    if book_title:
        try:
            book_nid = _ensure_book_node(cortex, book_title, author, dry_run)
            ch_nid = _ensure_chapter_node(
                cortex, book_nid, book_title, chapter_num, chapter_title, dry_run
            )
            spine_cache[book_nid] = True
            if not dry_run and mem.parent_id != ch_nid:
                mem.parent_id = ch_nid
                cortex.store(mem)
                try:
                    cortex.add_child(ch_nid, mem.id)
                except Exception:
                    pass
            stats["spine"] = True
        except Exception as e:
            _log(f"  [spine FAIL] {mem.id}: {e}")

    # Step 4: Interpretive bridge — retired (relied on SQLite cortex._db; Postgres path TBD)

    # Step 5: Arousal — set from milieu state if still at 0.0
    if (mem.arousal or 0.0) == 0.0:
        try:
            _ms = _milieu_mod.read_state()
            arousal = _ms.arousal if _ms else 0.5
            if not dry_run:
                mem.arousal = arousal
                cortex.store(mem)
            stats["arousal"] = True
        except Exception as e:
            _log(f"  [arousal FAIL] {mem.id}: {e}")

    return stats


# ── Main ──────────────────────────────────────────────────────────────────────


def run(args) -> None:
    db_path = Path(
        os.environ.get(
            "IGOR_DB_PATH",
            str(Path.home() / ".TheIgors" / "Igor-wild-0001" / "wild-0001.db"),
        )
    )
    cortex = Cortex()

    candidates = _fetch_candidates(cortex, args.book or "", args.batch)
    if not candidates:
        print("No unembedded reading memories found — nothing to integrate.")
        return

    mode = "DRY RUN" if args.dry_run else "LIVE"
    print(f"Reading integrator — {mode}")
    print(f"Candidates: {len(candidates)} nodes")
    print("─" * 60)

    _log(
        f"start: {len(candidates)} candidates, book_filter={args.book!r}, dry={args.dry_run}"
    )

    total = {"embed": 0, "links": 0, "spine": 0, "interp": 0, "arousal": 0}
    spine_cache: dict = {}

    for i, row in enumerate(candidates):
        meta = json.loads(row["metadata"]) if row["metadata"] else {}
        book = (meta.get("book_title") or meta.get("book") or "?")[:40]
        print(
            f"[{i+1:>3}/{len(candidates)}] {row['id']}  {book[:30]}  {str(row['narrative'] or '')[:50]}"
        )

        stats = _integrate_node(cortex, row, spine_cache, args.link_top, args.dry_run)

        flags = []
        if stats["embed"]:
            flags.append("embed")
            total["embed"] += 1
        if stats["links"]:
            flags.append(f"links={stats['links']}")
            total["links"] += stats["links"]
        if stats["spine"]:
            flags.append("spine")
            total["spine"] += 1
        if stats["interp"]:
            flags.append("interp")
            total["interp"] += 1
        if stats["arousal"]:
            flags.append("arousal")
            total["arousal"] += 1

        print(f"         → {', '.join(flags) if flags else 'no changes'}")
        _log(f"  {row['id']}: {', '.join(flags) or 'no changes'}")

        # Small delay to not hammer Ollama
        if not args.dry_run and stats["embed"]:
            time.sleep(0.3)

    print("─" * 60)
    summary = (
        f"Done. embedded={total['embed']} linked={total['links']} "
        f"spined={total['spine']} interp={total['interp']} arousal={total['arousal']}"
    )
    print(summary)
    _log(summary)


def main():
    parser = argparse.ArgumentParser(
        description="Reading integrator — backfill encoding"
    )
    parser.add_argument("--book", default="", help="Filter by book_title substring")
    parser.add_argument(
        "--all", action="store_true", help="Process all unembedded reading nodes"
    )
    parser.add_argument("--dry-run", action="store_true", help="Show plan, no writes")
    parser.add_argument(
        "--batch", type=int, default=200, help="Max nodes to process (default 200)"
    )
    parser.add_argument(
        "--link-top", type=int, default=3, help="Max link edges per node (default 3)"
    )
    args = parser.parse_args()

    if not args.all and not args.book:
        print("Specify --all or --book <title>")
        sys.exit(1)

    run(args)


if __name__ == "__main__":
    main()
