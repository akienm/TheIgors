#!/usr/bin/env python3
"""
migrate_wg_edges.py — Build wg_edges: semantic similarity edges from nomic-embed-text.

Replaces wg_cooccur (29M corpus co-occurrence rows) with wg_edges (~1.5M semantic
proximity edges). Each word gets its top-K most semantically similar neighbors by
cosine similarity over nomic-embed-text 768-dim embeddings.

Algorithm:
  1. Load ~60K filtered unigrams from wg_word_lang
  2. Compute nomic-embed-text embeddings via Ollama (concurrent workers)
  3. Chunked cosine matrix multiply → top-K neighbors per word
  4. Write wg_edges to SQLite and/or Postgres

Run with Igor DOWN.

Usage:
    python3 claudecode/migrate_wg_edges.py [--dry-run] [--sqlite-only] [--pg-only]
                                            [--workers N] [--top-k N]

Environment:
    IGOR_HOME_DB_URL  — Postgres connection string (required unless --sqlite-only)
    WORD_GRAPH_DB     — SQLite path (default: ~/.TheIgors/word_graph.db)
    OLLAMA_HOST       — Ollama base URL (default: http://localhost:11434)
"""

import argparse
import os
import sqlite3
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import numpy as np
import urllib.request
import json

# ── Config ─────────────────────────────────────────────────────────────────────

PG_URL = os.getenv("IGOR_HOME_DB_URL", "")
SQLITE_PATH = Path(os.getenv("WORD_GRAPH_DB", Path.home() / ".TheIgors/word_graph.db"))
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
EMBED_MODEL = "nomic-embed-text"

EDGES_SCHEMA = """
CREATE TABLE IF NOT EXISTS wg_edges (
    word_a     TEXT NOT NULL,
    word_b     TEXT NOT NULL,
    similarity REAL NOT NULL,
    PRIMARY KEY (word_a, word_b)
);
CREATE INDEX IF NOT EXISTS idx_wge_a ON wg_edges(word_a);
"""

# ── Embedding ──────────────────────────────────────────────────────────────────


def embed_word(word: str) -> tuple[str, list[float]] | None:
    """Call Ollama embeddings endpoint for one word. Returns (word, vector) or None."""
    url = f"{OLLAMA_HOST}/api/embeddings"
    payload = json.dumps({"model": EMBED_MODEL, "prompt": word}).encode()
    req = urllib.request.Request(
        url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
            return word, data["embedding"]
    except Exception as e:
        print(f"  WARNING: embed failed for {word!r}: {e}", file=sys.stderr)
        return None


def compute_embeddings(words: list[str], workers: int) -> tuple[list[str], np.ndarray]:
    """
    Compute embeddings for all words using concurrent Ollama calls.
    Returns (words_with_embeddings, matrix) where matrix is (N, 768).
    """
    total = len(words)
    results: dict[str, list[float]] = {}
    done = 0
    t0 = time.time()

    print(f"  Computing {total:,} embeddings with {workers} workers…")
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {pool.submit(embed_word, w): w for w in words}
        for fut in as_completed(futures):
            result = fut.result()
            if result is not None:
                word, vec = result
                results[word] = vec
            done += 1
            if done % 1000 == 0:
                elapsed = time.time() - t0
                rate = done / elapsed
                remaining = (total - done) / rate if rate > 0 else 0
                print(
                    f"  {done:,}/{total:,} embeddings "
                    f"({rate:.0f}/s, ~{remaining:.0f}s remaining)"
                )

    elapsed = time.time() - t0
    print(f"  Embeddings done: {len(results):,}/{total:,} in {elapsed:.1f}s")

    # Build ordered list and matrix (only words that got embeddings)
    ordered = [w for w in words if w in results]
    matrix = np.array([results[w] for w in ordered], dtype=np.float32)
    return ordered, matrix


def find_top_k_neighbors(
    words: list[str], matrix: np.ndarray, top_k: int, chunk_size: int = 500
) -> list[tuple[str, str, float]]:
    """
    Chunked cosine similarity: for each word, find top-K most similar words.
    Returns list of (word_a, word_b, similarity).
    Excludes self-pairs.
    """
    print(f"\n  Computing top-{top_k} neighbors for {len(words):,} words…")

    # L2-normalize (in-place on a copy)
    norms = np.linalg.norm(matrix, axis=1, keepdims=True)
    norms = np.where(norms == 0, 1.0, norms)
    normed = (matrix / norms).astype(np.float32)

    edges = []
    n = len(words)
    t0 = time.time()

    for start in range(0, n, chunk_size):
        end = min(start + chunk_size, n)
        chunk = normed[start:end]  # (chunk_size, 768)

        # (chunk_size, N) similarity scores
        sims = chunk @ normed.T

        for i, word_a in enumerate(words[start:end]):
            row = sims[i]
            # Zero out self
            row[start + i] = -1.0
            # Top-K indices
            top_idx = np.argpartition(row, -top_k)[-top_k:]
            top_idx = top_idx[np.argsort(row[top_idx])[::-1]]
            for idx in top_idx:
                sim = float(row[idx])
                if sim > 0:
                    edges.append((word_a, words[idx], sim))

        if (start // chunk_size) % 10 == 0:
            elapsed = time.time() - t0
            done_words = end
            rate = done_words / elapsed if elapsed > 0 else 0
            remaining = (n - done_words) / rate if rate > 0 else 0
            print(
                f"  chunk {start}–{end}: {len(edges):,} edges so far "
                f"(~{remaining:.0f}s remaining)"
            )

    elapsed = time.time() - t0
    print(f"  Neighbor search done: {len(edges):,} edges in {elapsed:.1f}s")
    return edges


# ── SQLite ─────────────────────────────────────────────────────────────────────


def load_words_sqlite() -> list[str]:
    if not SQLITE_PATH.exists():
        print(f"  SKIP: SQLite not found at {SQLITE_PATH}")
        return []
    conn = sqlite3.connect(str(SQLITE_PATH))
    rows = conn.execute(
        "SELECT word FROM wg_word_lang "
        "WHERE INSTR(word, '__') = 0 "
        "  AND LENGTH(word) >= 4 "
        "  AND LOWER(word) = word "
        "  AND word GLOB '[a-z]*'"
    ).fetchall()
    conn.close()
    words = [r[0] for r in rows]
    print(f"  Loaded {len(words):,} filtered unigrams from SQLite")
    return words


def write_edges_sqlite(edges: list[tuple[str, str, float]], dry_run: bool) -> None:
    if not SQLITE_PATH.exists():
        print(f"  SKIP: SQLite not found at {SQLITE_PATH}")
        return

    print(f"\n── SQLite: {SQLITE_PATH} ──")
    if dry_run:
        print(f"  Dry run — would write {len(edges):,} edges")
        return

    conn = sqlite3.connect(str(SQLITE_PATH))
    conn.executescript(EDGES_SCHEMA)

    # Truncate any prior run
    conn.execute("DELETE FROM wg_edges")
    conn.commit()

    batch_size = 10_000
    written = 0
    t0 = time.time()
    for i in range(0, len(edges), batch_size):
        batch = edges[i : i + batch_size]
        conn.executemany(
            "INSERT OR REPLACE INTO wg_edges (word_a, word_b, similarity) VALUES (?, ?, ?)",
            batch,
        )
        conn.commit()
        written += len(batch)
        if written % 100_000 == 0:
            print(f"  SQLite: {written:,}/{len(edges):,} rows written")

    conn.close()
    print(f"  SQLite: {written:,} rows written in {time.time()-t0:.1f}s")


# ── Postgres ───────────────────────────────────────────────────────────────────


def load_words_postgres() -> list[str]:
    if not PG_URL:
        return []
    try:
        import psycopg2

        conn = psycopg2.connect(PG_URL)
        cur = conn.cursor()
        cur.execute(
            "SELECT word FROM wg_word_lang "
            "WHERE POSITION('__' IN word) = 0 "
            "  AND LENGTH(word) >= 4 "
            "  AND word ~ '^[a-z]+$'"
        )
        words = [r[0] for r in cur.fetchall()]
        conn.close()
        print(f"  Loaded {len(words):,} filtered unigrams from Postgres")
        return words
    except Exception as e:
        print(f"  ERROR loading from Postgres: {e}")
        return []


def write_edges_postgres(edges: list[tuple[str, str, float]], dry_run: bool) -> None:
    if not PG_URL:
        print("  SKIP: IGOR_HOME_DB_URL not set")
        return

    print("\n── Postgres ──")
    if dry_run:
        print(f"  Dry run — would write {len(edges):,} edges")
        return

    try:
        import psycopg2
        import psycopg2.extras

        conn = psycopg2.connect(PG_URL)
        conn.autocommit = False
        cur = conn.cursor()
    except Exception as e:
        print(f"  ERROR connecting to Postgres: {e}")
        return

    # Create table
    cur.execute(EDGES_SCHEMA)
    conn.commit()

    # Truncate prior run
    cur.execute("DELETE FROM wg_edges")
    conn.commit()

    batch_size = 10_000
    written = 0
    t0 = time.time()
    for i in range(0, len(edges), batch_size):
        batch = edges[i : i + batch_size]
        psycopg2.extras.execute_batch(
            cur,
            "INSERT INTO wg_edges (word_a, word_b, similarity) VALUES (%s, %s, %s) "
            "ON CONFLICT (word_a, word_b) DO UPDATE SET similarity = EXCLUDED.similarity",
            batch,
            page_size=batch_size,
        )
        conn.commit()
        written += len(batch)
        if written % 100_000 == 0:
            print(f"  Postgres: {written:,}/{len(edges):,} rows written")

    cur.close()
    conn.close()
    print(f"  Postgres: {written:,} rows written in {time.time()-t0:.1f}s")


# ── Main ───────────────────────────────────────────────────────────────────────


def main():
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Show plan; write nothing"
    )
    parser.add_argument("--sqlite-only", action="store_true", help="Skip Postgres")
    parser.add_argument(
        "--pg-only",
        action="store_true",
        help="Skip SQLite writes (still loads words from SQLite if pg-only not set)",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=20,
        help="Ollama concurrent workers (default: 20)",
    )
    parser.add_argument(
        "--top-k", type=int, default=20, help="Neighbors per word (default: 20)"
    )
    parser.add_argument(
        "--chunk-size", type=int, default=500, help="Cosine chunk size (default: 500)"
    )
    args = parser.parse_args()

    if args.dry_run:
        print("DRY RUN — no writes\n")

    # ── Load word list ────────────────────────────────────────────────────────
    words = []
    if not args.pg_only:
        words = load_words_sqlite()

    if not words and PG_URL:
        words = load_words_postgres()

    if not words:
        print("ERROR: no words loaded — check WORD_GRAPH_DB or IGOR_HOME_DB_URL")
        sys.exit(1)

    print(f"\nTotal words to embed: {len(words):,}")

    if args.dry_run:
        print(
            f"Would compute {len(words):,} embeddings and ~{len(words)*args.top_k:,} edges"
        )
        print("Dry run done.")
        return

    # ── Compute embeddings ────────────────────────────────────────────────────
    ordered_words, matrix = compute_embeddings(words, workers=args.workers)
    print(f"\nEmbedding matrix: {matrix.shape} ({matrix.nbytes/1e6:.0f} MB)")

    # ── Find top-K neighbors ──────────────────────────────────────────────────
    edges = find_top_k_neighbors(
        ordered_words, matrix, top_k=args.top_k, chunk_size=args.chunk_size
    )

    print(f"\nTotal edges: {len(edges):,}")

    # ── Write ─────────────────────────────────────────────────────────────────
    if not args.pg_only:
        write_edges_sqlite(edges, dry_run=False)

    if not args.sqlite_only:
        write_edges_postgres(edges, dry_run=False)

    print("\nDone.")


if __name__ == "__main__":
    main()
