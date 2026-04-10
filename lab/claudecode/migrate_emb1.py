"""
G-EMB1 migration: move inline embeddings from memories.embedding → memory_embeddings.

Run while Igor is PAUSED (not running).
Safe to re-run — uses INSERT OR IGNORE and migration marker.

Usage:
    python3 ~/TheIgors/lab/claudecode/migrate_emb1.py
"""

import json
import sqlite3
import time
from pathlib import Path
import os

DB_PATH = Path(
    os.getenv("IGOR_DB_PATH", Path.home() / ".TheIgors/Igor-wild-0001/wild-0001.db")
)


def main():
    if not DB_PATH.exists():
        print(f"ERROR: DB not found at {DB_PATH}")
        return

    print(f"DB: {DB_PATH} ({DB_PATH.stat().st_size // 1024 // 1024} MB)")

    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row

    # Ensure memory_embeddings table exists
    conn.execute("""
        CREATE TABLE IF NOT EXISTS memory_embeddings (
            memory_id TEXT PRIMARY KEY,
            embedding  TEXT NOT NULL
        )
    """)
    conn.commit()
    print("memory_embeddings table: OK")

    # Check if already migrated
    already_done = conn.execute(
        "SELECT 1 FROM _migrations WHERE name = 'emb1_migrate_inline'"
    ).fetchone()
    if already_done:
        print("Migration already applied (marker present). Nothing to do.")
        conn.close()
        return

    # Count source rows
    total = conn.execute(
        "SELECT COUNT(*) FROM memories WHERE embedding IS NOT NULL AND embedding != 'null'"
    ).fetchone()[0]
    print(f"Memories with inline embedding: {total}")

    if total == 0:
        print("No inline embeddings to migrate.")
    else:
        # Copy embeddings to memory_embeddings
        print("Copying embeddings to memory_embeddings ...")
        t0 = time.time()
        conn.execute("""
            INSERT OR IGNORE INTO memory_embeddings(memory_id, embedding)
            SELECT id, embedding FROM memories
            WHERE embedding IS NOT NULL AND embedding != 'null'
        """)
        conn.commit()
        copied = conn.execute("SELECT COUNT(*) FROM memory_embeddings").fetchone()[0]
        print(f"  Copied: {copied} rows in {time.time()-t0:.1f}s")

        # NULL out inline embeddings
        print("NULLing out memories.embedding ...")
        t1 = time.time()
        conn.execute("UPDATE memories SET embedding = NULL WHERE embedding IS NOT NULL")
        conn.commit()
        nulled = conn.execute(
            "SELECT COUNT(*) FROM memories WHERE embedding IS NULL"
        ).fetchone()[0]
        print(f"  NULLed: {nulled} rows in {time.time()-t1:.1f}s")

    # Insert migration marker
    from datetime import datetime

    conn.execute(
        "INSERT OR IGNORE INTO _migrations(name, applied_at) VALUES (?, ?)",
        ("emb1_migrate_inline", datetime.now().isoformat()),
    )
    conn.commit()
    print("Migration marker written.")

    conn.close()

    # VACUUM — must run outside any transaction, with isolation_level=None
    print(f"\nRunning VACUUM on {DB_PATH} ...")
    before_mb = DB_PATH.stat().st_size // 1024 // 1024
    t2 = time.time()
    vconn = sqlite3.connect(str(DB_PATH), isolation_level=None)
    vconn.execute("VACUUM")
    vconn.close()
    after_mb = DB_PATH.stat().st_size // 1024 // 1024
    print(f"  VACUUM done in {time.time()-t2:.1f}s: {before_mb}MB → {after_mb}MB")

    print("\nG-EMB1 migration complete. Safe to restart Igor.")


if __name__ == "__main__":
    main()
