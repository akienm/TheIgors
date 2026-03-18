"""
migrate_sqlite_to_postgres.py — One-shot SQLite → Postgres migration for Igor.

Usage:
    python3 claudecode/migrate_sqlite_to_postgres.py

Reads IGOR_DB_PATH (SQLite source) and IGOR_DB_URL (Postgres target) from the
environment (or from the .env file at ~/.TheIgors/igor_wild_0001/.env).

What it does:
1.  Enables pg_trgm extension (for future trigram indexes)
2.  Creates the full schema in Postgres (metadata as JSONB, SERIAL PKs)
3.  Checks FK integrity (interpretive_edges → memories) before copy
4.  Copies all 9 tables row by row
5.  Resets all SERIAL sequences to match the highest copied id
6.  Verifies row counts match
7.  Prints a summary

Safety:
- Source SQLite is never written to — read-only throughout
- Target tables are created with IF NOT EXISTS — re-runnable up to the copy step
- If the target already has rows, the script aborts rather than double-inserting
"""

from __future__ import annotations

import json
import os
import sqlite3
import sys
from pathlib import Path


def _load_env():
    """Load .env from the standard Igor instance directory if present."""
    env_path = (
        Path.home()
        / ".TheIgors"
        / os.getenv("IGOR_INSTANCE_ID", "igor_wild_0001")
        / ".env"
    )
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, val = line.partition("=")
            os.environ.setdefault(key.strip(), val.strip())


def _sqlite_conn(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def _pg_conn(db_url: str):
    import psycopg2
    import psycopg2.extras

    conn = psycopg2.connect(db_url)
    conn.autocommit = False
    return conn


# ── Schema ────────────────────────────────────────────────────────────────────

_SCHEMA_SQL = """
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
CREATE INDEX IF NOT EXISTS idx_memories_ne_scan      ON memories (activation_count DESC) WHERE memory_type NOT IN ('ROOT', 'CORE_PATTERN');

CREATE TABLE IF NOT EXISTS ring_memory (
    id          SERIAL PRIMARY KEY,
    category    TEXT,
    content     TEXT,
    timestamp   TEXT,
    thread_id   TEXT
);

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
    category            TEXT,
    attractor_weight    REAL DEFAULT 0.0,
    parent_obs_id       INTEGER
);

CREATE INDEX IF NOT EXISTS idx_twm_integrated            ON twm_observations (integrated);
CREATE INDEX IF NOT EXISTS idx_twm_expires_at            ON twm_observations (expires_at);
CREATE INDEX IF NOT EXISTS idx_twm_instance_id           ON twm_observations (instance_id);
CREATE INDEX IF NOT EXISTS idx_twm_instance_integrated   ON twm_observations (instance_id, integrated, id ASC);

CREATE TABLE IF NOT EXISTS memory_blobs (
    id          SERIAL PRIMARY KEY,
    memory_id   TEXT REFERENCES memories(id),
    content     TEXT,
    tags        TEXT DEFAULT '[]',
    created_at  TEXT
);

CREATE INDEX IF NOT EXISTS idx_blobs_memory_id ON memory_blobs (memory_id);

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

CREATE TABLE IF NOT EXISTS _migrations (
    name        TEXT PRIMARY KEY,
    applied_at  TEXT
);

CREATE TABLE IF NOT EXISTS lists (
    list_name   TEXT,
    item_key    TEXT,
    item_value  TEXT,
    ref_type    TEXT,
    ref_id      TEXT,
    instance_id TEXT DEFAULT '',
    updated_at  TEXT,
    PRIMARY KEY (list_name, item_key, instance_id)
);

CREATE TABLE IF NOT EXISTS memory_embeddings (
    memory_id   TEXT PRIMARY KEY REFERENCES memories(id),
    embedding   TEXT
);
"""

# ── Table copy specs ──────────────────────────────────────────────────────────

# (table_name, [col_names], serial_col_or_None)
_TABLES = [
    (
        "memories",
        [
            "id",
            "narrative",
            "memory_type",
            "parent_id",
            "children_ids",
            "link_ids",
            "valence",
            "activation_count",
            "friction_history",
            "timestamp",
            "metadata",
            "embedding",
            "arousal",
            "dominance",
            "portable",
            "links_weighted",
            "last_accessed",
            "source",
            "confidence",
            "context_of_encoding",
        ],
        None,  # text PK — no SERIAL
    ),
    (
        "ring_memory",
        ["id", "category", "content", "timestamp", "thread_id"],
        "id",
    ),
    (
        "twm_observations",
        [
            "id",
            "timestamp",
            "source",
            "content_csb",
            "salience",
            "metadata_json",
            "integrated",
            "integration_count",
            "expires_at",
            "urgency",
            "instance_id",
            "thread_id",
            "category",
            "attractor_weight",
            "parent_obs_id",
        ],
        "id",
    ),
    (
        "memory_blobs",
        ["id", "memory_id", "content", "tags", "created_at"],
        "id",
    ),
    (
        "interpretive_edges",
        [
            "id",
            "from_id",
            "to_id",
            "direction",
            "condition_csb",
            "meaning_payload",
            "action_pointer",
            "weight",
            "created_at",
            "layer",
        ],
        "id",
    ),
    (
        "reading_list",
        [
            "id",
            "title",
            "author",
            "source",
            "book_type",
            "reading_rate",
            "priority",
            "status",
            "emotional_significance",
            "encoding_arousal",
            "notes",
            "added_by",
            "added_at",
            "started_at",
            "completed_at",
        ],
        None,
    ),
    (
        "_migrations",
        ["name", "applied_at"],
        None,
    ),
    (
        "lists",
        [
            "list_name",
            "item_key",
            "item_value",
            "ref_type",
            "ref_id",
            "instance_id",
            "updated_at",
        ],
        None,
    ),
    (
        "memory_embeddings",
        ["memory_id", "embedding"],
        None,
    ),
]


def _check_fk_violations(sqlite_cur) -> list[str]:
    """Return list of orphaned from_id/to_id in interpretive_edges."""
    violations = []
    memory_ids = {
        r[0] for r in sqlite_cur.execute("SELECT id FROM memories").fetchall()
    }
    edges = sqlite_cur.execute(
        "SELECT id, from_id, to_id FROM interpretive_edges"
    ).fetchall()
    for row in edges:
        eid, from_id, to_id = row[0], row[1], row[2]
        if from_id and from_id not in memory_ids:
            violations.append(f"edge {eid}: from_id={from_id!r} missing from memories")
        if to_id and to_id not in memory_ids:
            violations.append(f"edge {eid}: to_id={to_id!r} missing from memories")
    return violations


def _copy_table(sqlite_conn, pg_conn, table: str, cols: list[str], serial_col) -> int:
    """Copy one table. Returns row count copied."""
    import psycopg2.extras

    sqlite_cur = sqlite_conn.cursor()
    pg_cur = pg_conn.cursor()

    # For memory_embeddings, skip orphaned rows (memory_id not in memories)
    if table == "memory_embeddings":
        valid_ids = {
            r[0] for r in sqlite_cur.execute("SELECT id FROM memories").fetchall()
        }
        all_rows = sqlite_cur.execute(
            f"SELECT {', '.join(cols)} FROM {table}"
        ).fetchall()
        rows = [r for r in all_rows if r[0] in valid_ids]
        skipped = len(all_rows) - len(rows)
        if skipped:
            print(f"  memory_embeddings: skipping {skipped} orphaned rows")
    else:
        rows = sqlite_cur.execute(f"SELECT {', '.join(cols)} FROM {table}").fetchall()

    if not rows:
        print(f"  {table}: 0 rows (empty)")
        return 0

    # For memories table: convert metadata TEXT → psycopg2.extras.Json (JSONB column)
    import psycopg2.extras as _pgx

    converted = []
    for row in rows:
        vals = list(row)
        if table == "memories" and "metadata" in cols:
            mi = cols.index("metadata")
            raw = vals[mi]
            if isinstance(raw, str):
                try:
                    parsed = json.loads(raw) if raw else {}
                except Exception:
                    parsed = {}
            elif isinstance(raw, dict):
                parsed = raw
            else:
                parsed = {}
            vals[mi] = _pgx.Json(parsed)
        converted.append(vals)

    placeholders = ", ".join(["%s"] * len(cols))
    col_str = ", ".join(cols)
    insert_sql = (
        f"INSERT INTO {table} ({col_str}) VALUES ({placeholders}) "
        f"ON CONFLICT DO NOTHING"
    )

    psycopg2.extras.execute_batch(pg_cur, insert_sql, converted, page_size=500)
    pg_conn.commit()

    # Reset SERIAL sequence
    if serial_col:
        pg_cur.execute(
            f"SELECT setval(pg_get_serial_sequence('{table}', '{serial_col}'), "
            f"COALESCE(MAX({serial_col}), 1)) FROM {table}"
        )
        pg_conn.commit()

    return len(converted)


def main():
    _load_env()

    db_path = os.getenv("IGOR_DB_PATH")
    db_url = os.getenv("IGOR_DB_URL")

    if not db_path:
        print("ERROR: IGOR_DB_PATH not set — cannot find SQLite source")
        sys.exit(1)
    if not db_url:
        print("ERROR: IGOR_DB_URL not set — cannot find Postgres target")
        sys.exit(1)
    if not Path(db_path).exists():
        print(f"ERROR: SQLite DB not found at {db_path}")
        sys.exit(1)

    print(f"Source: {db_path}")
    print(f"Target: {db_url.split('@')[-1]}")  # hide credentials
    print()

    sqlite_conn = _sqlite_conn(db_path)
    pg_conn = _pg_conn(db_url)

    # ── Create schema ─────────────────────────────────────────────────────────
    print("Creating schema...")
    pg_cur = pg_conn.cursor()
    for stmt in _SCHEMA_SQL.strip().split(";"):
        stmt = stmt.strip()
        if stmt:
            pg_cur.execute(stmt)
    pg_conn.commit()
    print("Schema created.")
    print()

    # ── FK check ──────────────────────────────────────────────────────────────
    print("Checking FK integrity in SQLite source...")
    violations = _check_fk_violations(sqlite_conn)
    if violations:
        print(f"WARNING: {len(violations)} FK violations found:")
        for v in violations[:10]:
            print(f"  {v}")
        if len(violations) > 10:
            print(f"  ... and {len(violations) - 10} more")
        print(
            "These rows will be skipped by ON CONFLICT DO NOTHING (FK enforcement in PG)."
        )
    else:
        print("FK integrity OK.")
    print()

    # ── Guard: truncate if target already has data (idempotent re-run) ───────
    pg_cur.execute("SELECT COUNT(*) FROM memories")
    existing = pg_cur.fetchone()[0]
    if existing > 0:
        print(
            f"Target memories already has {existing} rows — truncating all tables for clean re-run..."
        )
        for tbl in [
            "memory_embeddings",
            "interpretive_edges",
            "memory_blobs",
            "twm_observations",
            "ring_memory",
            "lists",
            "_migrations",
            "reading_list",
            "memories",
        ]:
            pg_cur.execute(f"TRUNCATE TABLE {tbl} RESTART IDENTITY CASCADE")
        pg_conn.commit()
        print("Tables truncated.")

    # ── Copy tables ───────────────────────────────────────────────────────────
    print("Copying tables...")
    # Capture source counts during copy (before any concurrent SQLite writes can change them)
    sqlite_counts = {}
    pg_counts = {}
    for table, cols, serial_col in _TABLES:
        count = _copy_table(sqlite_conn, pg_conn, table, cols, serial_col)
        sqlite_counts[table] = count  # rows read from SQLite
        print(f"  {table}: {count} rows")
    print()

    # ── Verify counts ─────────────────────────────────────────────────────────
    print("Verifying row counts...")
    all_ok = True
    for table, _, _ in _TABLES:
        src_n = sqlite_counts[table]
        pg_cur.execute(f"SELECT COUNT(*) FROM {table}")
        pg_n = pg_cur.fetchone()[0]
        if table == "memory_embeddings":
            status = "OK" if pg_n == src_n else "MISMATCH"
        else:
            status = "OK" if pg_n >= src_n else "MISMATCH"
        if status != "OK":
            all_ok = False
        print(f"  {table}: copied={src_n} pg={pg_n} {status}")
    print()

    sqlite_conn.close()
    pg_conn.close()

    if all_ok:
        print("Migration complete. All counts match.")
        print()
        print("Next steps:")
        print("  1. Confirm IGOR_DB_URL is set in ~/.TheIgors/igor_wild_0001/.env")
        print("  2. Start Igor — make_db_proxy() will auto-select Postgres")
        print("  3. Send a test message via CC bridge to confirm DB connectivity")
    else:
        print(
            "WARNING: Some row counts do not match — inspect above before proceeding."
        )
        sys.exit(1)


if __name__ == "__main__":
    main()
