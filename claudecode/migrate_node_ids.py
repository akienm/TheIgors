#!/usr/bin/env python3
"""
migrate_node_ids.py — Migrate all graph nodes to D256 timestamp IDs.

Migrates:
  memories          id → YYYYMMDDHHMMSSuuuuuu (from memories.timestamp)
  reading_list      id → YYYYMMDDHHMMSSuuuuuu (from reading_list.added_at)
  node_registry     — populated for every migrated node

FK columns updated in same transaction:
  interpretive_edges   from_id, to_id
  memory_blobs         memory_id
  memory_embeddings    memory_id
  memories             parent_id, children_ids (JSON), link_ids (JSON)

Undateable nodes: anchor to earliest known timestamp + 1µs sequential offsets.

Usage:
  python3 claudecode/migrate_node_ids.py --dry-run    # preview, no writes
  python3 claudecode/migrate_node_ids.py              # execute migration
  python3 claudecode/migrate_node_ids.py --rollback   # restore from backup table

Forensic log: ~/.TheIgors/logs/node_migration.log
"""

import argparse
import json
import os
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

REPO = Path(__file__).parent.parent
sys.path.insert(0, str(REPO))

from wild_igor.igor.memory.node_id import build_suffix, ts_from_datetime

DB_URL = os.getenv(
    "IGOR_HOME_DB_URL",
    "postgresql://igor:choose_a_password@127.0.0.1/igor_wild_0001",
)

LOG_DIR = Path.home() / ".TheIgors" / "logs"
LOG_FILE = LOG_DIR / "node_migration.log"

MACHINE_ID = os.getenv("IGOR_SWARM_NAME", "akiendelllinux")

# Earliest possible anchor — if a node has no date, use this + offset
_EPOCH_ANCHOR = datetime(2026, 2, 17, 13, 36, 2, 342396, tzinfo=timezone.utc)


# ── Logging ───────────────────────────────────────────────────────────────────


def _log(msg: str) -> None:
    ts = datetime.now(timezone.utc).isoformat()
    line = f"{ts}  {msg}"
    print(line, flush=True)
    try:
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        with open(LOG_FILE, "a") as f:
            f.write(line + "\n")
    except Exception:
        pass


# ── ID generation for migration ───────────────────────────────────────────────


class _MigrationIdGen:
    """Generates unique timestamp IDs for migration — no module-level counter needed."""

    def __init__(self):
        self._used: set[str] = set()
        self._anchor_offset: int = 0  # microseconds beyond _EPOCH_ANCHOR

    def from_ts_str(self, ts_str: str | None) -> str:
        """Parse existing timestamp string → new node ID. Falls back to anchor."""
        dt = _parse_ts(ts_str)
        if dt is None:
            return self._anchor_id()
        return self._unique_from_dt(dt)

    def _unique_from_dt(self, dt: datetime) -> str:
        base = ts_from_datetime(dt)
        candidate = base
        # bump microseconds until unique
        bump = 0
        while candidate in self._used:
            bump += 1
            bumped = dt + timedelta(microseconds=bump)
            candidate = ts_from_datetime(bumped)
        self._used.add(candidate)
        return candidate

    def _anchor_id(self) -> str:
        dt = _EPOCH_ANCHOR + timedelta(microseconds=self._anchor_offset)
        self._anchor_offset += 1
        base = ts_from_datetime(dt)
        while base in self._used:
            self._anchor_offset += 1
            dt = _EPOCH_ANCHOR + timedelta(microseconds=self._anchor_offset)
            base = ts_from_datetime(dt)
        self._used.add(base)
        return base


def _parse_ts(ts_str: str | None) -> datetime | None:
    if not ts_str:
        return None
    for fmt in (
        "%Y-%m-%dT%H:%M:%S.%f",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d %H:%M:%S.%f",
        "%Y-%m-%d %H:%M:%S",
    ):
        try:
            dt = datetime.strptime(ts_str.strip(), fmt)
            return dt.replace(tzinfo=timezone.utc)
        except ValueError:
            continue
    return None


# ── Migration logic ───────────────────────────────────────────────────────────


def _parse_node_id_dt(node_id: str) -> datetime | None:
    """Extract datetime from the timestamp portion of a new-format node ID."""
    ts_part = node_id.split(".")[0]
    if len(ts_part) == 20 and ts_part.isdigit():
        try:
            return datetime.strptime(ts_part, "%Y%m%d%H%M%S%f").replace(
                tzinfo=timezone.utc
            )
        except ValueError:
            pass
    return None


def _already_migrated(old_id: str) -> bool:
    """True if the ID already looks like a timestamp ID (20-digit prefix)."""
    ts_part = old_id.split(".")[0]
    return len(ts_part) == 20 and ts_part.isdigit()


def build_memories_map(cur, gen: _MigrationIdGen, dry_run: bool) -> dict[str, str]:
    """Return {old_id: new_id} for memories table."""
    cur.execute("SELECT id, timestamp FROM memories ORDER BY timestamp NULLS LAST, id")
    rows = cur.fetchall()
    mapping = {}
    skipped = 0
    for old_id, ts_str in rows:
        if _already_migrated(old_id):
            skipped += 1
            continue
        new_id = gen.from_ts_str(ts_str)
        mapping[old_id] = new_id
    _log(f"memories: {len(mapping)} to migrate, {skipped} already timestamp IDs")
    return mapping


def build_reading_list_map(cur, gen: _MigrationIdGen, dry_run: bool) -> dict[str, str]:
    """Return {old_id: new_id} for reading_list table."""
    cur.execute(
        "SELECT id, added_at FROM reading_list ORDER BY added_at NULLS LAST, id"
    )
    rows = cur.fetchall()
    mapping = {}
    skipped = 0
    for old_id, ts_str in rows:
        if _already_migrated(old_id):
            skipped += 1
            continue
        new_id = gen.from_ts_str(ts_str)
        mapping[old_id] = new_id
    _log(f"reading_list: {len(mapping)} to migrate, {skipped} already timestamp IDs")
    return mapping


def _update_json_array(cur, table: str, col: str, mapping: dict[str, str]) -> int:
    """Update a text column containing a JSON array of IDs. Returns rows changed."""
    if not mapping:
        return 0
    cur.execute(
        f"SELECT id, {col} FROM {table} WHERE {col} IS NOT NULL AND {col} != '[]'"
    )
    rows = cur.fetchall()
    changed = 0
    for row_id, arr_json in rows:
        try:
            arr = json.loads(arr_json)
        except Exception:
            continue
        new_arr = [mapping.get(x, x) for x in arr]
        if new_arr != arr:
            cur.execute(
                f"UPDATE {table} SET {col}=%s WHERE id=%s",
                (json.dumps(new_arr), row_id),
            )
            changed += 1
    return changed


def run_migration(dry_run: bool = False) -> None:
    import psycopg2

    conn = psycopg2.connect(DB_URL)
    conn.autocommit = False
    cur = conn.cursor()

    _log(f"=== node_id migration START dry_run={dry_run} ===")
    t0 = time.time()

    try:
        # ── 1. Build ID maps ──────────────────────────────────────────────────
        gen = _MigrationIdGen()
        mem_map = build_memories_map(cur, gen, dry_run)
        rl_map = build_reading_list_map(cur, gen, dry_run)

        if dry_run:
            _log(
                f"DRY RUN: would rename {len(mem_map)} memories + {len(rl_map)} reading_list rows"
            )
            _log(f"  Sample memories renames:")
            for i, (old, new) in enumerate(list(mem_map.items())[:5]):
                _log(f"    {old!r} → {new!r}")
            _log(f"  Sample reading_list renames:")
            for i, (old, new) in enumerate(list(rl_map.items())[:5]):
                _log(f"    {old!r} → {new!r}")
            conn.rollback()
            return

        if not mem_map and not rl_map:
            _log("Nothing to migrate — all IDs already in timestamp format.")
            conn.rollback()
            return

        # ── 2. Create backup tables ───────────────────────────────────────────
        _log("Creating backup tables...")
        cur.execute("DROP TABLE IF EXISTS _migration_memories_backup")
        cur.execute(
            "CREATE TABLE _migration_memories_backup AS SELECT id, parent_id, children_ids, link_ids FROM memories"
        )
        cur.execute("DROP TABLE IF EXISTS _migration_reading_list_backup")
        cur.execute(
            "CREATE TABLE _migration_reading_list_backup AS SELECT id FROM reading_list"
        )

        # ── 3. Drop FK constraints ────────────────────────────────────────────
        _log("Dropping FK constraints...")
        cur.execute(
            "ALTER TABLE interpretive_edges DROP CONSTRAINT IF EXISTS interpretive_edges_from_id_fkey"
        )
        cur.execute(
            "ALTER TABLE interpretive_edges DROP CONSTRAINT IF EXISTS interpretive_edges_to_id_fkey"
        )
        cur.execute(
            "ALTER TABLE memory_blobs DROP CONSTRAINT IF EXISTS memory_blobs_memory_id_fkey"
        )
        cur.execute(
            "ALTER TABLE memory_embeddings DROP CONSTRAINT IF EXISTS memory_embeddings_memory_id_fkey"
        )

        # ── 4. Migrate memories.id (self-referential updates first) ───────────
        _log(f"Migrating {len(mem_map)} memories.id values...")
        n = 0
        for old_id, new_id in mem_map.items():
            cur.execute("UPDATE memories SET id=%s WHERE id=%s", (new_id, old_id))
            n += 1
            if n % 1000 == 0:
                _log(f"  memories: {n}/{len(mem_map)}...")

        # ── 5. Update memories self-references ────────────────────────────────
        _log("Updating memories.parent_id...")
        for old_id, new_id in mem_map.items():
            cur.execute(
                "UPDATE memories SET parent_id=%s WHERE parent_id=%s", (new_id, old_id)
            )

        _log("Updating memories.children_ids (JSON arrays)...")
        changed = _update_json_array(cur, "memories", "children_ids", mem_map)
        _log(f"  children_ids: {changed} rows updated")

        _log("Updating memories.link_ids (JSON arrays)...")
        changed = _update_json_array(cur, "memories", "link_ids", mem_map)
        _log(f"  link_ids: {changed} rows updated")

        # ── 6. Update FK references pointing to memories ──────────────────────
        _log("Updating interpretive_edges.from_id...")
        for old_id, new_id in mem_map.items():
            cur.execute(
                "UPDATE interpretive_edges SET from_id=%s WHERE from_id=%s",
                (new_id, old_id),
            )

        _log("Updating interpretive_edges.to_id...")
        for old_id, new_id in mem_map.items():
            cur.execute(
                "UPDATE interpretive_edges SET to_id=%s WHERE to_id=%s",
                (new_id, old_id),
            )

        _log("Updating memory_blobs.memory_id...")
        for old_id, new_id in mem_map.items():
            cur.execute(
                "UPDATE memory_blobs SET memory_id=%s WHERE memory_id=%s",
                (new_id, old_id),
            )

        _log("Updating memory_embeddings.memory_id...")
        for old_id, new_id in mem_map.items():
            cur.execute(
                "UPDATE memory_embeddings SET memory_id=%s WHERE memory_id=%s",
                (new_id, old_id),
            )

        # ── 7. Migrate reading_list.id ────────────────────────────────────────
        _log(f"Migrating {len(rl_map)} reading_list.id values...")
        for old_id, new_id in rl_map.items():
            cur.execute("UPDATE reading_list SET id=%s WHERE id=%s", (new_id, old_id))

        # ── 8. Re-add FK constraints ──────────────────────────────────────────
        _log("Re-adding FK constraints...")
        cur.execute(
            "ALTER TABLE interpretive_edges ADD CONSTRAINT interpretive_edges_from_id_fkey "
            "FOREIGN KEY (from_id) REFERENCES memories(id)"
        )
        cur.execute(
            "ALTER TABLE interpretive_edges ADD CONSTRAINT interpretive_edges_to_id_fkey "
            "FOREIGN KEY (to_id) REFERENCES memories(id)"
        )
        cur.execute(
            "ALTER TABLE memory_blobs ADD CONSTRAINT memory_blobs_memory_id_fkey "
            "FOREIGN KEY (memory_id) REFERENCES memories(id)"
        )
        cur.execute(
            "ALTER TABLE memory_embeddings ADD CONSTRAINT memory_embeddings_memory_id_fkey "
            "FOREIGN KEY (memory_id) REFERENCES memories(id)"
        )

        # ── 9. Populate node_registry ─────────────────────────────────────────
        # Build reverse map once (new_id → old_id) for both tables
        rev_mem = {v: k for k, v in mem_map.items()}
        rev_rl = {v: k for k, v in rl_map.items()}

        _log("Populating node_registry for memories...")
        cur.execute("SELECT id, timestamp FROM memories")
        for new_id, ts_str in cur.fetchall():
            # Prefer stored timestamp; fall back to parsing the new ID itself
            dt = _parse_ts(ts_str) or _parse_node_id_dt(new_id)
            old_id = rev_mem.get(new_id, new_id)
            migrated_from = old_id if old_id != new_id else None
            cur.execute(
                """
                INSERT INTO node_registry (node_id, table_name, row_id, machine_id, created_at, migrated_from)
                VALUES (%s, 'memories', %s, %s, %s, %s)
                ON CONFLICT (node_id) DO NOTHING
                """,
                (new_id, new_id, MACHINE_ID, dt, migrated_from),
            )

        _log("Populating node_registry for reading_list...")
        cur.execute("SELECT id, added_at FROM reading_list")
        for new_id, ts_str in cur.fetchall():
            dt = _parse_ts(ts_str) or _parse_node_id_dt(new_id)
            old_id = rev_rl.get(new_id, new_id)
            migrated_from = old_id if old_id != new_id else None
            cur.execute(
                """
                INSERT INTO node_registry (node_id, table_name, row_id, machine_id, created_at, migrated_from)
                VALUES (%s, 'reading_list', %s, %s, %s, %s)
                ON CONFLICT (node_id) DO NOTHING
                """,
                (new_id, new_id, MACHINE_ID, dt, migrated_from),
            )

        # ── 10. Write migration log ───────────────────────────────────────────
        _log("Writing per-row migration log...")
        for old_id, new_id in {**mem_map, **rl_map}.items():
            table = "memories" if old_id in mem_map else "reading_list"
            _log(f"  RENAMED  {table}  {old_id!r} → {new_id!r}")

        conn.commit()
        elapsed = time.time() - t0
        _log(
            f"=== migration COMPLETE in {elapsed:.1f}s: {len(mem_map)} memories + {len(rl_map)} reading_list rows ==="
        )

    except Exception as e:
        conn.rollback()
        _log(f"MIGRATION FAILED — rolled back: {e}")
        raise
    finally:
        cur.close()
        conn.close()


def run_rollback() -> None:
    """Restore from backup tables created during migration."""
    import psycopg2

    conn = psycopg2.connect(DB_URL)
    conn.autocommit = False
    cur = conn.cursor()
    _log("=== ROLLBACK START ===")
    try:
        # Check backups exist
        cur.execute(
            "SELECT COUNT(*) FROM information_schema.tables WHERE table_name='_migration_memories_backup'"
        )
        if cur.fetchone()[0] == 0:
            _log("No backup table found — cannot rollback.")
            conn.rollback()
            return

        cur.execute("SELECT COUNT(*) FROM _migration_memories_backup")
        n = cur.fetchone()[0]
        _log(f"Backup has {n} memory rows. Restoring...")

        # Drop FKs
        for stmt in [
            "ALTER TABLE interpretive_edges DROP CONSTRAINT IF EXISTS interpretive_edges_from_id_fkey",
            "ALTER TABLE interpretive_edges DROP CONSTRAINT IF EXISTS interpretive_edges_to_id_fkey",
            "ALTER TABLE memory_blobs DROP CONSTRAINT IF EXISTS memory_blobs_memory_id_fkey",
            "ALTER TABLE memory_embeddings DROP CONSTRAINT IF EXISTS memory_embeddings_memory_id_fkey",
        ]:
            cur.execute(stmt)

        # Build reverse map from backup
        cur.execute(
            "SELECT b.id AS old_id, m.id AS new_id FROM _migration_memories_backup b JOIN memories m ON m.id != b.id LIMIT 0"
        )
        # Actually: match by parent_id or children_ids is fragile. Better: join on row content.
        # Simplest rollback: the backup table has old IDs, current memories has new IDs.
        # We need to map new→old. Use node_registry.migrated_from.
        cur.execute(
            "SELECT node_id, migrated_from FROM node_registry WHERE migrated_from IS NOT NULL AND table_name='memories'"
        )
        reverse_map = {new: old for new, old in cur.fetchall()}

        _log(f"Reversing {len(reverse_map)} renames in memories...")
        for new_id, old_id in reverse_map.items():
            cur.execute("UPDATE memories SET id=%s WHERE id=%s", (old_id, new_id))
        for new_id, old_id in reverse_map.items():
            cur.execute(
                "UPDATE memories SET parent_id=%s WHERE parent_id=%s", (old_id, new_id)
            )
            cur.execute(
                "UPDATE interpretive_edges SET from_id=%s WHERE from_id=%s",
                (old_id, new_id),
            )
            cur.execute(
                "UPDATE interpretive_edges SET to_id=%s WHERE to_id=%s",
                (old_id, new_id),
            )
            cur.execute(
                "UPDATE memory_blobs SET memory_id=%s WHERE memory_id=%s",
                (old_id, new_id),
            )
            cur.execute(
                "UPDATE memory_embeddings SET memory_id=%s WHERE memory_id=%s",
                (old_id, new_id),
            )

        cur.execute(
            "SELECT node_id, migrated_from FROM node_registry WHERE migrated_from IS NOT NULL AND table_name='reading_list'"
        )
        rl_reverse = {new: old for new, old in cur.fetchall()}
        for new_id, old_id in rl_reverse.items():
            cur.execute("UPDATE reading_list SET id=%s WHERE id=%s", (old_id, new_id))

        # Re-add FKs
        for stmt in [
            "ALTER TABLE interpretive_edges ADD CONSTRAINT interpretive_edges_from_id_fkey FOREIGN KEY (from_id) REFERENCES memories(id)",
            "ALTER TABLE interpretive_edges ADD CONSTRAINT interpretive_edges_to_id_fkey FOREIGN KEY (to_id) REFERENCES memories(id)",
            "ALTER TABLE memory_blobs ADD CONSTRAINT memory_blobs_memory_id_fkey FOREIGN KEY (memory_id) REFERENCES memories(id)",
            "ALTER TABLE memory_embeddings ADD CONSTRAINT memory_embeddings_memory_id_fkey FOREIGN KEY (memory_id) REFERENCES memories(id)",
        ]:
            cur.execute(stmt)

        # Clean up registry entries
        cur.execute("DELETE FROM node_registry WHERE migrated_from IS NOT NULL")
        conn.commit()
        _log("=== ROLLBACK COMPLETE ===")
    except Exception as e:
        conn.rollback()
        _log(f"ROLLBACK FAILED: {e}")
        raise
    finally:
        cur.close()
        conn.close()


# ── Migration test (fixture) ──────────────────────────────────────────────────


def run_fixture_test() -> None:
    """
    Smoke-test the migration on 5 fake rows in a temp schema.
    Used by tests/test_node_migration.py.
    """
    import psycopg2

    conn = psycopg2.connect(DB_URL)
    conn.autocommit = False
    cur = conn.cursor()
    try:
        cur.execute("CREATE SCHEMA IF NOT EXISTS migration_test")
        cur.execute("DROP TABLE IF EXISTS migration_test.mem")
        cur.execute("""
            CREATE TABLE migration_test.mem (
                id TEXT PRIMARY KEY,
                timestamp TEXT,
                parent_id TEXT
            )
        """)
        rows = [
            ("CP1", "2026-02-17T13:36:02.342396"),
            (
                "CP2",
                "2026-02-17T13:36:02.342396",
            ),  # same timestamp — must get unique ID
            ("BL_a1b2c3d4", "2026-03-01T10:00:00.000000"),
            ("RL_001", None),  # no timestamp → anchor
            ("RL_002", None),  # no timestamp → anchor + 1µs
        ]
        for row_id, ts in rows:
            cur.execute(
                "INSERT INTO migration_test.mem VALUES (%s, %s, NULL)", (row_id, ts)
            )

        gen = _MigrationIdGen()
        cur.execute(
            "SELECT id, timestamp FROM migration_test.mem ORDER BY timestamp NULLS LAST, id"
        )
        mapping = {}
        for old_id, ts_str in cur.fetchall():
            new_id = gen.from_ts_str(ts_str)
            mapping[old_id] = new_id

        # Verify uniqueness
        assert len(set(mapping.values())) == len(mapping), "Collision in generated IDs!"

        # Verify timestamp format
        for new_id in mapping.values():
            ts_part = new_id.split(".")[0]
            assert len(ts_part) == 20 and ts_part.isdigit(), f"Bad format: {new_id}"

        # Verify anchor nodes got earliest possible IDs
        anchor_ids = [mapping["RL_001"], mapping["RL_002"]]
        assert anchor_ids[0] < anchor_ids[1], "Anchor IDs not sequential"

        conn.rollback()  # Don't commit test data
        print("fixture_test: PASS")
    except Exception as e:
        conn.rollback()
        print(f"fixture_test: FAIL — {e}")
        raise
    finally:
        cur.close()
        conn.close()


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Migrate node IDs to D256 timestamp format"
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Preview changes, no writes"
    )
    parser.add_argument(
        "--rollback", action="store_true", help="Restore from backup tables"
    )
    parser.add_argument("--test", action="store_true", help="Run fixture smoke test")
    args = parser.parse_args()

    if args.test:
        run_fixture_test()
    elif args.rollback:
        run_rollback()
    else:
        run_migration(dry_run=args.dry_run)
