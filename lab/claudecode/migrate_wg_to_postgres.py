#!/usr/bin/env python3
"""
migrate_wg_to_postgres.py — Migrate word graph SQLite → Postgres (D126).

Copies wg_cooccur, wg_word_docs, wg_idf, wg_word_lang, wg_meta from the
SQLite word_graph.db into the Postgres home DB.

Safety:
- Source SQLite never written to.
- Aborts per-table if Postgres already has rows (use --force to overwrite).
- --dry-run prints counts only.
- Re-runnable: skips tables that already have data unless --force.

Usage:
    python3 claudecode/migrate_wg_to_postgres.py [--dry-run] [--force]
    python3 claudecode/migrate_wg_to_postgres.py --tables wg_cooccur wg_idf
"""

from __future__ import annotations

import argparse
import os
import sqlite3
import sys
import time
from pathlib import Path

# ── Env loader ────────────────────────────────────────────────────────────────

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))


def _load_env():
    instance_id = os.getenv("IGOR_INSTANCE_ID", "Igor-wild-0001")
    env_path = Path.home() / ".TheIgors" / instance_id / ".env"
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, val = line.partition("=")
            os.environ.setdefault(key.strip(), val.strip())


_load_env()

# ── Config ────────────────────────────────────────────────────────────────────

from wild_igor.igor.paths import paths as _paths  # noqa: E402

WG_SQLITE = _paths().word_graph("word_graph")
PG_URL = os.getenv("IGOR_HOME_DB_URL") or os.getenv("IGOR_DB_URL")

BATCH_SIZE = 50_000

# Tables ordered by dependency (meta first, then data)
ALL_TABLES = ["wg_meta", "wg_word_lang", "wg_idf", "wg_word_docs", "wg_cooccur"]

# Schema for each table (CREATE TABLE IF NOT EXISTS — mirrors word_graph.py _SCHEMA)
_SCHEMAS = {
    "wg_meta": """
        CREATE TABLE IF NOT EXISTS wg_meta (
            key   TEXT PRIMARY KEY,
            value TEXT NOT NULL
        )""",
    "wg_word_lang": """
        CREATE TABLE IF NOT EXISTS wg_word_lang (
            word TEXT PRIMARY KEY,
            lang TEXT NOT NULL DEFAULT 'en'
        )""",
    "wg_idf": """
        CREATE TABLE IF NOT EXISTS wg_idf (
            word  TEXT PRIMARY KEY,
            score REAL NOT NULL DEFAULT 0.0
        )""",
    "wg_word_docs": """
        CREATE TABLE IF NOT EXISTS wg_word_docs (
            word   TEXT NOT NULL,
            doc_id TEXT NOT NULL,
            weight REAL NOT NULL DEFAULT 1.0,
            PRIMARY KEY (word, doc_id)
        );
        CREATE INDEX IF NOT EXISTS idx_wgd_doc ON wg_word_docs(doc_id)""",
    "wg_cooccur": """
        CREATE TABLE IF NOT EXISTS wg_cooccur (
            word_a TEXT NOT NULL,
            word_b TEXT NOT NULL,
            score  REAL NOT NULL DEFAULT 0.0,
            PRIMARY KEY (word_a, word_b)
        );
        CREATE INDEX IF NOT EXISTS idx_wgc_a        ON wg_cooccur(word_a);
        CREATE INDEX IF NOT EXISTS idx_wgc_covering ON wg_cooccur(word_a, word_b, score)""",
}

# Columns per table
_COLS = {
    "wg_meta": ["key", "value"],
    "wg_word_lang": ["word", "lang"],
    "wg_idf": ["word", "score"],
    "wg_word_docs": ["word", "doc_id", "weight"],
    "wg_cooccur": ["word_a", "word_b", "score"],
}


# ── Helpers ───────────────────────────────────────────────────────────────────


def _pg():
    import psycopg2

    conn = psycopg2.connect(PG_URL)
    conn.autocommit = False
    return conn


def _sqlite():
    conn = sqlite3.connect(str(WG_SQLITE))
    conn.row_factory = sqlite3.Row
    return conn


def _pg_count(pg, table: str) -> int:
    cur = pg.cursor()
    try:
        cur.execute(f"SELECT COUNT(*) FROM {table}")
        return cur.fetchone()[0]
    except Exception:
        pg.rollback()
        return -1  # table doesn't exist yet


def _sq_count(sq, table: str) -> int:
    row = sq.execute(f"SELECT COUNT(*) FROM {table}").fetchone()
    return row[0] if row else 0


def _ensure_schema(pg, table: str) -> None:
    cur = pg.cursor()
    for stmt in _SCHEMAS[table].split(";"):
        stmt = stmt.strip()
        if stmt:
            cur.execute(stmt)
    pg.commit()


def _migrate_table(pg, sq, table: str, force: bool, dry_run: bool) -> None:
    from psycopg2.extras import execute_values

    cols = _COLS[table]
    col_str = ", ".join(cols)
    placeholders = ", ".join(["%s"] * len(cols))

    sq_total = _sq_count(sq, table)
    pg_existing = _pg_count(pg, table)
    pg_label = f"{pg_existing:,}" if pg_existing >= 0 else "table missing"

    print(f"\n  {table}: {sq_total:,} source rows, {pg_label} already in Postgres")

    if pg_existing > 0 and not force:
        print(
            f"  SKIP — Postgres already has {pg_existing:,} rows (use --force to overwrite)"
        )
        return

    if dry_run:
        print(f"  DRY RUN — would migrate {sq_total:,} rows")
        return

    if pg_existing > 0 and force:
        print(f"  FORCE — truncating {pg_existing:,} existing rows")
        pg.cursor().execute(f"TRUNCATE TABLE {table} CASCADE")
        pg.commit()

    _ensure_schema(pg, table)

    insert_sql = f"INSERT INTO {table} ({col_str}) VALUES %s " f"ON CONFLICT DO NOTHING"

    offset = 0
    migrated = 0
    t0 = time.time()

    while True:
        rows = sq.execute(
            f"SELECT {col_str} FROM {table} LIMIT {BATCH_SIZE} OFFSET {offset}"
        ).fetchall()
        if not rows:
            break

        batch = [tuple(r[c] for c in cols) for r in rows]
        execute_values(pg.cursor(), insert_sql, batch)
        pg.commit()

        migrated += len(batch)
        offset += BATCH_SIZE
        elapsed = time.time() - t0
        rate = migrated / elapsed if elapsed > 0.1 else 0
        pct = 100 * migrated / sq_total if sq_total else 100
        print(
            f"  {table}: {migrated:,}/{sq_total:,} ({pct:.1f}%) "
            f"@ {rate:,.0f} rows/s",
            end="\r",
            flush=True,
        )

    print(f"\n  {table}: done — {migrated:,} rows in {time.time()-t0:.1f}s")


# ── Main ──────────────────────────────────────────────────────────────────────


def main():
    parser = argparse.ArgumentParser(description="Migrate word graph SQLite → Postgres")
    parser.add_argument("--dry-run", action="store_true", help="Print counts only")
    parser.add_argument("--force", action="store_true", help="Overwrite existing rows")
    parser.add_argument(
        "--tables",
        nargs="+",
        choices=ALL_TABLES,
        help="Migrate only these tables (default: all)",
    )
    args = parser.parse_args()

    tables = args.tables or ALL_TABLES

    if not PG_URL:
        print("ERROR: IGOR_HOME_DB_URL / IGOR_DB_URL not set")
        sys.exit(1)

    if not WG_SQLITE.exists():
        print(f"ERROR: SQLite word graph not found: {WG_SQLITE}")
        sys.exit(1)

    print(f"Source:      {WG_SQLITE}")
    print(f"Destination: {PG_URL.split('@')[-1]}")  # hide credentials
    print(f"Tables:      {', '.join(tables)}")
    print(f"Batch size:  {BATCH_SIZE:,}")
    if args.dry_run:
        print("Mode:        DRY RUN")
    elif args.force:
        print("Mode:        FORCE (truncate + re-migrate)")
    else:
        print("Mode:        SKIP existing tables")

    pg = _pg()
    sq = _sqlite()

    t_start = time.time()
    for table in tables:
        _migrate_table(pg, sq, table, force=args.force, dry_run=args.dry_run)

    sq.close()
    pg.close()

    print(f"\nTotal time: {time.time()-t_start:.1f}s")
    if not args.dry_run:
        print("Migration complete. Run Igor to verify.")


if __name__ == "__main__":
    main()
