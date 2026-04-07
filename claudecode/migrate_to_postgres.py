"""
migrate_to_postgres.py — Two-channel SQLite → Postgres migration for D126.

Splits Igor's data into HOME (global truth) and LOCAL (box-scoped) Postgres DBs.

  HOME  (IGOR_HOME_DB_URL): memories, interpretive_edges, memory_blobs,
                            reading_list, memory_embeddings, _migrations,
                            word-graph tables (wg_*), budget spend/config,
                            notebook entries.

  LOCAL (IGOR_LOCAL_DB_URL): ring_memory, twm_observations.

Usage:
    # Required env vars (or in ~/.TheIgors/Igor-wild-0001/.env):
    #   IGOR_DB_PATH          — source SQLite (main memory DB)
    #   IGOR_HOME_DB_URL      — Postgres DSN for home channel
    #   IGOR_LOCAL_DB_URL     — Postgres DSN for local channel
    #
    python3 claudecode/migrate_to_postgres.py [--dry-run]

Safety:
- Source SQLite is never written to.
- Aborts if target tables already have rows.
- --dry-run prints row counts without writing anything.
"""

from __future__ import annotations

import argparse
import json
import os
import sqlite3
import sys
from pathlib import Path

# ── Env loader ────────────────────────────────────────────────────────────────


def _load_env():
    env_path = (
        Path.home()
        / ".TheIgors"
        / os.getenv("IGOR_INSTANCE_ID", "Igor-wild-0001")
        / ".env"
    )
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, val = line.partition("=")
            os.environ.setdefault(key.strip(), val.strip())


def _sqlite(path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    return conn


def _pg(url: str):
    import psycopg2
    import psycopg2.extras

    conn = psycopg2.connect(url)
    conn.autocommit = False
    return conn


# ── Table definitions ─────────────────────────────────────────────────────────

_HOME_SCHEMA = """
CREATE EXTENSION IF NOT EXISTS pg_trgm;

CREATE TABLE IF NOT EXISTS memories (
    id                  TEXT PRIMARY KEY,
    narrative           TEXT,
    memory_type         TEXT,
    parent_id           TEXT,
    children_ids        TEXT DEFAULT '[]',
    link_ids            TEXT DEFAULT '[]',
    valence             REAL DEFAULT 0.0,
    activation_count    INTEGER DEFAULT 0,
    friction_history    TEXT DEFAULT '[]',
    timestamp           TEXT,
    metadata            JSONB DEFAULT '{}'::jsonb,
    embedding           TEXT,
    arousal             REAL DEFAULT 0.0,
    dominance           REAL DEFAULT 0.0,
    portable            INTEGER DEFAULT 1,
    links_weighted      TEXT DEFAULT '{}',
    last_accessed       TEXT,
    source              TEXT,
    confidence          REAL DEFAULT 1.0,
    context_of_encoding TEXT
);
CREATE INDEX IF NOT EXISTS idx_memories_metadata_gin ON memories USING GIN (metadata);
CREATE INDEX IF NOT EXISTS idx_memories_memory_type  ON memories (memory_type);
CREATE INDEX IF NOT EXISTS idx_memories_parent_id    ON memories (parent_id);
CREATE INDEX IF NOT EXISTS idx_memories_activation   ON memories (activation_count DESC);

CREATE TABLE IF NOT EXISTS interpretive_edges (
    id              SERIAL PRIMARY KEY,
    from_id         TEXT REFERENCES memories(id),
    to_id           TEXT REFERENCES memories(id),
    direction       TEXT,
    condition_csb   TEXT,
    meaning_payload TEXT,
    action_pointer  TEXT,
    weight          REAL DEFAULT 1.0,
    created_at      TEXT,
    layer           TEXT
);
CREATE INDEX IF NOT EXISTS idx_edges_from_id ON interpretive_edges (from_id);
CREATE INDEX IF NOT EXISTS idx_edges_to_id   ON interpretive_edges (to_id);

CREATE TABLE IF NOT EXISTS memory_blobs (
    id          SERIAL PRIMARY KEY,
    memory_id   TEXT REFERENCES memories(id),
    content     TEXT,
    tags        TEXT DEFAULT '[]',
    created_at  TEXT
);
CREATE INDEX IF NOT EXISTS idx_blobs_memory_id ON memory_blobs (memory_id);

CREATE TABLE IF NOT EXISTS reading_list (
    id                      TEXT PRIMARY KEY,
    title                   TEXT,
    author                  TEXT,
    source                  TEXT,
    book_type               TEXT,
    reading_rate            TEXT,
    priority                INTEGER DEFAULT 5,
    status                  TEXT DEFAULT 'pending',
    emotional_significance  TEXT,
    encoding_arousal        REAL DEFAULT 0.5,
    notes                   TEXT,
    added_by                TEXT,
    added_at                TEXT,
    started_at              TEXT,
    completed_at            TEXT
);

CREATE TABLE IF NOT EXISTS memory_embeddings (
    memory_id   TEXT PRIMARY KEY REFERENCES memories(id),
    embedding   TEXT,
    model       TEXT,
    created_at  TEXT
);

CREATE TABLE IF NOT EXISTS _migrations (
    name        TEXT PRIMARY KEY,
    applied_at  TEXT
);
"""

_LOCAL_SCHEMA = """
CREATE TABLE IF NOT EXISTS ring_memory (
    id          SERIAL PRIMARY KEY,
    category    TEXT,
    content     TEXT,
    timestamp   TEXT,
    thread_id   TEXT
);
CREATE INDEX IF NOT EXISTS idx_ring_thread_id  ON ring_memory (thread_id);
CREATE INDEX IF NOT EXISTS idx_ring_category   ON ring_memory (category);

CREATE TABLE IF NOT EXISTS twm_observations (
    id                  SERIAL PRIMARY KEY,
    timestamp           TEXT,
    source              TEXT,
    content_csb         TEXT,
    salience            REAL,
    metadata_json       TEXT,
    integrated          INTEGER DEFAULT 0,
    integration_count   INTEGER DEFAULT 0,
    expires_at          TEXT,
    urgency             REAL DEFAULT 0.5,
    instance_id         TEXT,
    thread_id           TEXT,
    category            TEXT DEFAULT 'observation',
    attractor_weight    REAL DEFAULT 0.0,
    parent_obs_id       INTEGER
);
CREATE INDEX IF NOT EXISTS idx_twm_integrated          ON twm_observations (integrated);
CREATE INDEX IF NOT EXISTS idx_twm_expires_at          ON twm_observations (expires_at);
CREATE INDEX IF NOT EXISTS idx_twm_instance_id         ON twm_observations (instance_id);
CREATE INDEX IF NOT EXISTS idx_twm_instance_integrated ON twm_observations (instance_id, integrated, id ASC);
"""


# ── Table routing ─────────────────────────────────────────────────────────────

# Tables that live in HOME (global truth)
_HOME_TABLES = [
    "memories",
    "interpretive_edges",
    "memory_blobs",
    "reading_list",
    "memory_embeddings",
    "_migrations",
]

# Tables that live in LOCAL (box-scoped)
_LOCAL_TABLES = [
    "ring_memory",
    "twm_observations",
]

# Tables with SERIAL PKs — need sequence reset after copy
_SERIAL_TABLES_HOME = ["interpretive_edges", "memory_blobs"]
_SERIAL_TABLES_LOCAL = ["ring_memory", "twm_observations"]


# ── Migration helpers ─────────────────────────────────────────────────────────


def _table_exists(sq: sqlite3.Connection, name: str) -> bool:
    row = sq.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (name,)
    ).fetchone()
    return bool(row)


def _row_count(sq: sqlite3.Connection, name: str) -> int:
    return sq.execute(f"SELECT COUNT(*) FROM {name}").fetchone()[0]


def _pg_row_count(pg_cur, name: str) -> int:
    pg_cur.execute(f"SELECT COUNT(*) FROM {name}")
    return pg_cur.fetchone()[0]


def _copy_table(sq: sqlite3.Connection, pg_cur, table: str, dry_run: bool) -> int:
    if not _table_exists(sq, table):
        print(f"  SKIP {table} (not in source SQLite)")
        return 0

    src_count = _row_count(sq, table)
    if dry_run:
        print(f"  DRY  {table}: {src_count} rows (not written)")
        return src_count

    # Safety: abort if target already has data
    dst_count = _pg_row_count(pg_cur, table)
    if dst_count > 0:
        print(
            f"  SKIP {table}: target already has {dst_count} rows — skipping to avoid duplicates"
        )
        return 0

    rows = sq.execute(f"SELECT * FROM {table}").fetchall()
    if not rows:
        print(f"  SKIP {table}: 0 rows in source")
        return 0

    cols = list(rows[0].keys())
    col_str = ", ".join(cols)
    placeholders = ", ".join(["%s"] * len(cols))
    insert_sql = f"INSERT INTO {table} ({col_str}) VALUES ({placeholders})"

    data = []
    for row in rows:
        vals = []
        for col, val in zip(cols, row):
            if col == "metadata" and val is not None:
                # Ensure JSONB column gets valid JSON
                try:
                    json.loads(val)
                    vals.append(val)
                except Exception:
                    vals.append("{}")
            else:
                vals.append(val)
        data.append(tuple(vals))

    pg_cur.executemany(insert_sql, data)
    print(f"  COPY {table}: {len(data)} rows")
    return len(data)


def _reset_serial(pg_cur, table: str) -> None:
    """Reset SERIAL sequence to max(id) + 1 so future inserts don't collide."""
    pg_cur.execute(f"SELECT MAX(id) FROM {table}")
    max_id = pg_cur.fetchone()[0]
    if max_id is not None:
        seq_name = f"{table}_id_seq"
        pg_cur.execute(f"SELECT setval('{seq_name}', %s)", (max_id,))
        print(f"  SEQ  {table}: reset to {max_id}")


# ── Main ──────────────────────────────────────────────────────────────────────


def main() -> None:
    parser = argparse.ArgumentParser(description="D126 two-channel Postgres migration")
    parser.add_argument(
        "--dry-run", action="store_true", help="Print counts, no writes"
    )
    args = parser.parse_args()

    _load_env()

    sqlite_path = os.getenv("IGOR_DB_PATH")
    home_url = os.getenv("IGOR_HOME_DB_URL") or os.getenv("IGOR_DB_URL")
    local_url = os.getenv("IGOR_LOCAL_DB_URL")

    if not sqlite_path:
        sys.exit("ERROR: IGOR_DB_PATH not set")
    if not home_url:
        sys.exit("ERROR: IGOR_HOME_DB_URL (or IGOR_DB_URL) not set")
    if not local_url:
        sys.exit("ERROR: IGOR_LOCAL_DB_URL not set")

    sq = _sqlite(sqlite_path)
    print(f"\nSource: {sqlite_path}")
    print(f"Home:   {home_url.split('@')[-1]}")
    print(f"Local:  {local_url.split('@')[-1]}")
    print(f"Mode:   {'DRY RUN' if args.dry_run else 'LIVE'}\n")

    # ── HOME channel ──────────────────────────────────────────────────────────
    print("=== HOME channel ===")
    home_pg = _pg(home_url)
    home_cur = home_pg.cursor()
    try:
        # Create schema
        if not args.dry_run:
            home_cur.execute(_HOME_SCHEMA)
            home_pg.commit()

        total_home = 0
        for table in _HOME_TABLES:
            total_home += _copy_table(sq, home_cur, table, args.dry_run)

        if not args.dry_run:
            for table in _SERIAL_TABLES_HOME:
                if _table_exists(sq, table) and _row_count(sq, table) > 0:
                    _reset_serial(home_cur, table)
            home_pg.commit()
            print(f"\nHOME: {total_home} total rows committed")
        else:
            print(f"\nHOME: {total_home} rows would be copied (dry run)")

    except Exception as e:
        home_pg.rollback()
        print(f"ERROR (home): {e}")
        raise
    finally:
        home_pg.close()

    # ── LOCAL channel ─────────────────────────────────────────────────────────
    print("\n=== LOCAL channel ===")
    local_pg = _pg(local_url)
    local_cur = local_pg.cursor()
    try:
        if not args.dry_run:
            local_cur.execute(_LOCAL_SCHEMA)
            local_pg.commit()

        total_local = 0
        for table in _LOCAL_TABLES:
            total_local += _copy_table(sq, local_cur, table, args.dry_run)

        if not args.dry_run:
            for table in _SERIAL_TABLES_LOCAL:
                if _table_exists(sq, table) and _row_count(sq, table) > 0:
                    _reset_serial(local_cur, table)
            local_pg.commit()
            print(f"\nLOCAL: {total_local} total rows committed")
        else:
            print(f"\nLOCAL: {total_local} rows would be copied (dry run)")

    except Exception as e:
        local_pg.rollback()
        print(f"ERROR (local): {e}")
        raise
    finally:
        sq.close()
        local_pg.close()

    print("\nMigration complete.")
    print("Next: set IGOR_HOME_DB_URL and IGOR_LOCAL_DB_URL in .env and restart Igor.")


if __name__ == "__main__":
    main()
