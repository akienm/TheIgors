#!/usr/bin/env python3
"""
migrate_lemmatize.py — Rebuild word graph tables using lemmatized vocabulary.

What this does:
  1. Loads all unique words from wg_word_lang (both SQLite and Postgres)
  2. Computes canonical lemma for each word (WordNet verb→noun fallback)
  3. Writes wg_lemma_map table: original_word → lemma
  4. Rebuilds wg_word_lang: only canonical lemmas remain
  5. Rebuilds wg_word_docs: merges inflection rows (same lemma+doc_id → MAX weight)
  6. Does NOT touch wg_cooccur — that's replaced entirely by T-db-wg-replace-cooccur

Run with Igor DOWN. Postgres and SQLite are both migrated.

Usage:
    python3 claudecode/migrate_lemmatize.py [--dry-run] [--sqlite-only] [--pg-only]

Environment:
    IGOR_HOME_DB_URL  — Postgres connection string (required unless --sqlite-only)
    WORD_GRAPH_DB     — SQLite path (default: ~/.TheIgors/word_graph.db)
"""

import argparse
import os
import sqlite3
import sys
import time
from pathlib import Path

# ── Config ─────────────────────────────────────────────────────────────────────

PG_URL = os.getenv("IGOR_HOME_DB_URL", "")
SQLITE_PATH = Path(os.getenv("WORD_GRAPH_DB", Path.home() / ".TheIgors/word_graph.db"))

LEMMA_MAP_SCHEMA_SQLITE = """
CREATE TABLE IF NOT EXISTS wg_lemma_map (
    word  TEXT PRIMARY KEY,
    lemma TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_wglm_lemma ON wg_lemma_map(lemma);
"""

LEMMA_MAP_SCHEMA_PG = """
CREATE TABLE IF NOT EXISTS wg_lemma_map (
    word  TEXT PRIMARY KEY,
    lemma TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_wglm_lemma ON wg_lemma_map(lemma);
"""

# ── Lemmatizer ─────────────────────────────────────────────────────────────────

_lemmatizer = None
_cache: dict[str, str] = {}


def _init_lemmatizer():
    global _lemmatizer
    try:
        from nltk.stem import WordNetLemmatizer

        _lemmatizer = WordNetLemmatizer()
        # Warm up — first call loads the corpus
        _lemmatizer.lemmatize("test", "v")
        print("  Lemmatizer ready (WordNet)")
    except Exception as e:
        print(f"  WARNING: WordNet not available ({e}) — identity lemmatizer")
        _lemmatizer = None


def lemmatize(word: str) -> str:
    """Reduce to canonical form. English only (WordNet). Cached."""
    if word in _cache:
        return _cache[word]
    if _lemmatizer is None:
        return word
    # Skip non-ASCII-dominant tokens (French/Dutch words — WordNet doesn't help)
    if not word.isascii():
        _cache[word] = word
        return word
    v = _lemmatizer.lemmatize(word, "v")
    result = v if v != word else _lemmatizer.lemmatize(word, "n")
    _cache[word] = result
    return result


def lemmatize_token(token: str) -> str:
    """Handle both unigrams and bigrams (word1__word2 → lemma1__lemma2)."""
    if "__" in token:
        parts = token.split("__", 1)
        return f"{lemmatize(parts[0])}__{lemmatize(parts[1])}"
    return lemmatize(token)


# ── SQLite migration ────────────────────────────────────────────────────────────


def migrate_sqlite(dry_run: bool) -> dict:
    if not SQLITE_PATH.exists():
        print(f"  SKIP: SQLite not found at {SQLITE_PATH}")
        return {}

    print(f"\n── SQLite: {SQLITE_PATH} ──")
    conn = sqlite3.connect(str(SQLITE_PATH))
    conn.row_factory = sqlite3.Row

    # 1. Load all words
    t0 = time.time()
    words = [r[0] for r in conn.execute("SELECT word FROM wg_word_lang").fetchall()]
    print(f"  Loaded {len(words):,} words in {time.time()-t0:.1f}s")

    # 2. Build lemma map
    t0 = time.time()
    lemma_map = {w: lemmatize_token(w) for w in words}
    unique_lemmas = set(lemma_map.values())
    print(
        f"  Built lemma map: {len(words):,} → {len(unique_lemmas):,} unique lemmas "
        f"({len(words)-len(unique_lemmas):,} merged) in {time.time()-t0:.1f}s"
    )

    if dry_run:
        # Show sample merges
        merges = [(w, l) for w, l in lemma_map.items() if w != l][:20]
        print(
            f"\n  Sample merges ({len([x for x in lemma_map.items() if x[0]!=x[1]]):,} total):"
        )
        for w, l in merges:
            print(f"    {w} → {l}")
        conn.close()
        return lemma_map

    # 3. Create wg_lemma_map table
    conn.executescript(LEMMA_MAP_SCHEMA_SQLITE)
    conn.executemany(
        "INSERT OR REPLACE INTO wg_lemma_map (word, lemma) VALUES (?, ?)",
        lemma_map.items(),
    )
    conn.commit()
    print(f"  wg_lemma_map: {len(lemma_map):,} rows written")

    # 4. Rebuild wg_word_lang — keep only canonical lemmas, preserve lang
    t0 = time.time()
    conn.execute(
        "CREATE TABLE IF NOT EXISTS wg_word_lang_new (word TEXT PRIMARY KEY, lang TEXT NOT NULL DEFAULT 'en')"
    )
    # For each lemma, take the lang of any of its source words (first wins)
    conn.execute("""
        INSERT OR IGNORE INTO wg_word_lang_new (word, lang)
        SELECT m.lemma, wl.lang
        FROM wg_word_lang wl
        JOIN wg_lemma_map m ON wl.word = m.word
    """)
    new_lang_count = conn.execute("SELECT COUNT(*) FROM wg_word_lang_new").fetchone()[0]
    conn.execute("DROP TABLE wg_word_lang")
    conn.execute("ALTER TABLE wg_word_lang_new RENAME TO wg_word_lang")
    conn.commit()
    print(
        f"  wg_word_lang: {len(words):,} → {new_lang_count:,} rows in {time.time()-t0:.1f}s"
    )

    # 5. Rebuild wg_word_docs — merge inflections, keep MAX(weight) per (lemma, doc_id)
    t0 = time.time()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS wg_word_docs_new (
            word   TEXT NOT NULL,
            doc_id TEXT NOT NULL,
            weight REAL NOT NULL DEFAULT 1.0,
            PRIMARY KEY (word, doc_id)
        )
    """)
    conn.execute("""
        INSERT OR REPLACE INTO wg_word_docs_new (word, doc_id, weight)
        SELECT m.lemma, wd.doc_id, MAX(wd.weight)
        FROM wg_word_docs wd
        JOIN wg_lemma_map m ON wd.word = m.word
        GROUP BY m.lemma, wd.doc_id
    """)
    old_docs_count = conn.execute("SELECT COUNT(*) FROM wg_word_docs").fetchone()[0]
    new_docs_count = conn.execute("SELECT COUNT(*) FROM wg_word_docs_new").fetchone()[0]
    conn.execute("DROP TABLE wg_word_docs")
    conn.execute("ALTER TABLE wg_word_docs_new RENAME TO wg_word_docs")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_wgd_doc ON wg_word_docs(doc_id)")
    conn.commit()
    print(
        f"  wg_word_docs: {old_docs_count:,} → {new_docs_count:,} rows in {time.time()-t0:.1f}s"
    )

    # 6. Update wg_meta word_count
    conn.execute(
        "INSERT OR REPLACE INTO wg_meta (key, value) VALUES ('word_count', ?)",
        (str(new_lang_count),),
    )
    conn.commit()
    conn.close()
    print(f"  SQLite migration complete.")
    return lemma_map


# ── Postgres migration ──────────────────────────────────────────────────────────


def migrate_postgres(lemma_map: dict, dry_run: bool):
    if not PG_URL:
        print("\n  SKIP: IGOR_HOME_DB_URL not set")
        return

    print(f"\n── Postgres ──")
    try:
        import psycopg2
        import psycopg2.extras

        conn = psycopg2.connect(PG_URL)
        conn.autocommit = False
        cur = conn.cursor()
    except Exception as e:
        print(f"  ERROR connecting to Postgres: {e}")
        return

    if not lemma_map:
        # Load from PG if SQLite was skipped
        print("  Loading words from Postgres...")
        cur.execute("SELECT word FROM wg_word_lang")
        words = [r[0] for r in cur.fetchall()]
        lemma_map = {w: lemmatize_token(w) for w in words}
        print(
            f"  Built lemma map: {len(words):,} → {len(set(lemma_map.values())):,} lemmas"
        )

    if dry_run:
        print("  Dry run — skipping Postgres writes")
        conn.close()
        return

    # 3. Create wg_lemma_map
    cur.execute(LEMMA_MAP_SCHEMA_PG)
    psycopg2.extras.execute_batch(
        cur,
        "INSERT INTO wg_lemma_map (word, lemma) VALUES (%s, %s) ON CONFLICT(word) DO UPDATE SET lemma=EXCLUDED.lemma",
        list(lemma_map.items()),
        page_size=10000,
    )
    conn.commit()
    print(f"  wg_lemma_map: {len(lemma_map):,} rows written")

    # 4. Rebuild wg_word_lang
    t0 = time.time()
    cur.execute(
        "CREATE TABLE IF NOT EXISTS wg_word_lang_new (word TEXT PRIMARY KEY, lang TEXT NOT NULL DEFAULT 'en')"
    )
    cur.execute("""
        INSERT INTO wg_word_lang_new (word, lang)
        SELECT DISTINCT m.lemma, wl.lang
        FROM wg_word_lang wl
        JOIN wg_lemma_map m ON wl.word = m.word
        ON CONFLICT(word) DO NOTHING
    """)
    cur.execute("SELECT COUNT(*) FROM wg_word_lang_new")
    new_lang_count = cur.fetchone()[0]
    cur.execute("DROP TABLE wg_word_lang")
    cur.execute("ALTER TABLE wg_word_lang_new RENAME TO wg_word_lang")
    conn.commit()
    print(f"  wg_word_lang: → {new_lang_count:,} rows in {time.time()-t0:.1f}s")

    # 5. Rebuild wg_word_docs
    t0 = time.time()
    cur.execute("SELECT COUNT(*) FROM wg_word_docs")
    old_count = cur.fetchone()[0]
    cur.execute("""
        CREATE TABLE wg_word_docs_new (
            word   TEXT NOT NULL,
            doc_id TEXT NOT NULL,
            weight REAL NOT NULL DEFAULT 1.0,
            PRIMARY KEY (word, doc_id)
        )
    """)
    cur.execute("""
        INSERT INTO wg_word_docs_new (word, doc_id, weight)
        SELECT m.lemma, wd.doc_id, MAX(wd.weight)
        FROM wg_word_docs wd
        JOIN wg_lemma_map m ON wd.word = m.word
        GROUP BY m.lemma, wd.doc_id
    """)
    cur.execute("SELECT COUNT(*) FROM wg_word_docs_new")
    new_count = cur.fetchone()[0]
    cur.execute("DROP TABLE wg_word_docs")
    cur.execute("ALTER TABLE wg_word_docs_new RENAME TO wg_word_docs")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_wgd_doc ON wg_word_docs(doc_id)")
    conn.commit()
    print(
        f"  wg_word_docs: {old_count:,} → {new_count:,} rows in {time.time()-t0:.1f}s"
    )

    # 6. Update wg_meta
    cur.execute(
        "INSERT INTO wg_meta (key, value) VALUES (%s, %s) ON CONFLICT(key) DO UPDATE SET value=EXCLUDED.value",
        ("word_count", str(new_lang_count)),
    )
    conn.commit()
    cur.close()
    conn.close()
    print(f"  Postgres migration complete.")


# ── Main ───────────────────────────────────────────────────────────────────────


def main():
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Show what would change; write nothing"
    )
    parser.add_argument("--sqlite-only", action="store_true", help="Skip Postgres")
    parser.add_argument("--pg-only", action="store_true", help="Skip SQLite")
    args = parser.parse_args()

    if args.dry_run:
        print("DRY RUN — no writes will happen\n")

    _init_lemmatizer()

    lemma_map = {}
    if not args.pg_only:
        lemma_map = migrate_sqlite(args.dry_run)

    if not args.sqlite_only:
        migrate_postgres(lemma_map, args.dry_run)

    print("\nDone.")


if __name__ == "__main__":
    main()
