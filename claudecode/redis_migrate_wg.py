"""
redis_migrate_wg.py — Migrate SQLite word graph to Redis (D121).

Migrates all 5 tables:
  wg_cooccur (29.3M)  → wg:cooccur:{word_a} sorted sets
  wg_word_docs (6.4M) → wg:wd:{word} sorted sets
  wg_word_lang (2.1M) → wg:lang:{word} strings
  wg_idf (2.1M)       → wg:idf:{word} strings
  wg_meta (2)         → wg:meta hash

After migration: set IGOR_REDIS_WORD_GRAPH_HOST=localhost and
IGOR_REDIS_WG_SHADOW=false in ~/.TheIgors/Igor-wild-0001/.env

Run from repo root:
  python claudecode/redis_migrate_wg.py

Options:
  --dry-run  Count rows and estimate Redis ops without writing
  --tables   Comma-separated table names (default: all)
  --batch    Batch size for pipeline execute (default: 5000)
  --host     Redis host (default: localhost)
  --port     Redis port (default: 6379)
"""

import argparse
import sqlite3
import sys
import time
from pathlib import Path

SQLITE_PATH = Path.home() / ".TheIgors" / "word_graph.db"
BATCH_DEFAULT = 5000


def migrate_cooccur(r, cursor, batch: int, dry_run: bool) -> int:
    """wg_cooccur → wg:cooccur:{word_a} sorted sets (29.3M rows, batched)."""
    cursor.execute("SELECT count(*) FROM wg_cooccur")
    total = cursor.fetchone()[0]
    print(f"  wg_cooccur: {total:,} rows")
    if dry_run:
        return total

    cursor.execute("SELECT word_a, word_b, score FROM wg_cooccur ORDER BY word_a")
    done = 0
    pipe = r.pipeline(transaction=False)
    t0 = time.monotonic()

    for word_a, word_b, score in cursor:
        pipe.zadd(f"wg:cooccur:{word_a}", {word_b: float(score)})
        done += 1
        if done % batch == 0:
            pipe.execute()
            pipe = r.pipeline(transaction=False)
            elapsed = time.monotonic() - t0
            rate = done / elapsed
            eta = (total - done) / rate if rate > 0 else 0
            print(
                f"    {done:,}/{total:,} ({100*done/total:.1f}%) rate={rate:.0f}/s ETA={eta:.0f}s",
                end="\r",
                flush=True,
            )

    if pipe.command_stack:
        pipe.execute()

    elapsed = time.monotonic() - t0
    print(f"\n    Done: {done:,} entries in {elapsed:.0f}s ({done/elapsed:.0f}/s)")
    return done


def migrate_word_docs(r, cursor, batch: int, dry_run: bool) -> int:
    """wg_word_docs → wg:wd:{word} sorted sets (6.4M rows)."""
    cursor.execute("SELECT count(*) FROM wg_word_docs")
    total = cursor.fetchone()[0]
    print(f"  wg_word_docs: {total:,} rows")
    if dry_run:
        return total

    cursor.execute("SELECT word, doc_id, weight FROM wg_word_docs ORDER BY word")
    done = 0
    pipe = r.pipeline(transaction=False)
    t0 = time.monotonic()

    for word, doc_id, weight in cursor:
        pipe.zadd(f"wg:wd:{word}", {doc_id: float(weight)})
        done += 1
        if done % batch == 0:
            pipe.execute()
            pipe = r.pipeline(transaction=False)
            elapsed = time.monotonic() - t0
            rate = done / elapsed
            print(
                f"    {done:,}/{total:,} ({100*done/total:.1f}%) rate={rate:.0f}/s",
                end="\r",
                flush=True,
            )

    if pipe.command_stack:
        pipe.execute()

    elapsed = time.monotonic() - t0
    print(f"\n    Done: {done:,} entries in {elapsed:.0f}s ({done/elapsed:.0f}/s)")
    return done


def migrate_word_lang(r, cursor, batch: int, dry_run: bool) -> int:
    """wg_word_lang → wg:lang:{word} strings (2.1M rows)."""
    cursor.execute("SELECT count(*) FROM wg_word_lang")
    total = cursor.fetchone()[0]
    print(f"  wg_word_lang: {total:,} rows")
    if dry_run:
        return total

    cursor.execute("SELECT word, lang FROM wg_word_lang")
    done = 0
    pipe = r.pipeline(transaction=False)
    t0 = time.monotonic()

    for word, lang in cursor:
        pipe.set(f"wg:lang:{word}", lang)
        done += 1
        if done % batch == 0:
            pipe.execute()
            pipe = r.pipeline(transaction=False)

    if pipe.command_stack:
        pipe.execute()

    elapsed = time.monotonic() - t0
    print(f"    Done: {done:,} entries in {elapsed:.0f}s")
    return done


def migrate_idf(r, cursor, batch: int, dry_run: bool) -> int:
    """wg_idf → wg:idf:{word} strings (2.1M rows)."""
    cursor.execute("SELECT count(*) FROM wg_idf")
    total = cursor.fetchone()[0]
    print(f"  wg_idf: {total:,} rows")
    if dry_run:
        return total

    cursor.execute("SELECT word, score FROM wg_idf")
    done = 0
    pipe = r.pipeline(transaction=False)
    t0 = time.monotonic()

    for word, score in cursor:
        pipe.set(f"wg:idf:{word}", str(score))
        done += 1
        if done % batch == 0:
            pipe.execute()
            pipe = r.pipeline(transaction=False)

    if pipe.command_stack:
        pipe.execute()

    elapsed = time.monotonic() - t0
    print(f"    Done: {done:,} entries in {elapsed:.0f}s")
    return done


def migrate_meta(r, cursor, dry_run: bool) -> int:
    """wg_meta → wg:meta hash."""
    cursor.execute("SELECT key, value FROM wg_meta")
    rows = cursor.fetchall()
    print(f"  wg_meta: {len(rows)} rows")
    if dry_run:
        return len(rows)

    for key, value in rows:
        r.hset("wg:meta", key, value)
    print(f"    Done: {len(rows)} entries")
    return len(rows)


def main():
    parser = argparse.ArgumentParser(
        description="Migrate SQLite word graph to Redis (D121)"
    )
    parser.add_argument("--dry-run", action="store_true", help="Count rows, no writes")
    parser.add_argument("--tables", default="all", help="Comma-separated table names")
    parser.add_argument(
        "--batch", type=int, default=BATCH_DEFAULT, help="Pipeline batch size"
    )
    parser.add_argument("--host", default="localhost", help="Redis host")
    parser.add_argument("--port", type=int, default=6379, help="Redis port")
    parser.add_argument("--db-path", default=str(SQLITE_PATH), help="SQLite path")
    args = parser.parse_args()

    tables_arg = args.tables
    all_tables = {"cooccur", "word_docs", "word_lang", "idf", "meta"}
    if tables_arg == "all":
        tables = all_tables
    else:
        tables = set(tables_arg.split(","))

    print(f"SQLite: {args.db_path}")
    print(f"Redis:  {args.host}:{args.port}")
    print(f"Tables: {', '.join(sorted(tables))}")
    print(f"Batch:  {args.batch}")
    print(f"Mode:   {'DRY RUN' if args.dry_run else 'LIVE'}")
    print()

    if not args.dry_run:
        try:
            import redis as _r

            r = _r.Redis(host=args.host, port=args.port, decode_responses=True)
            r.ping()
            print(f"Redis connection OK")
        except Exception as e:
            print(f"ERROR: Redis connection failed: {e}")
            sys.exit(1)

        # Check existing key count
        existing = r.dbsize()
        if existing > 1000:
            print(
                f"WARNING: Redis already has {existing:,} keys. "
                "Use FLUSHDB first if you want a clean migration."
            )
            resp = input("Continue? [y/N] ").strip().lower()
            if resp != "y":
                print("Aborted.")
                sys.exit(0)
    else:
        r = None

    db = sqlite3.connect(args.db_path)
    db.execute("PRAGMA journal_mode=WAL")
    db.execute("PRAGMA cache_size=-65536")  # 64MB cache
    cursor = db.cursor()

    t_start = time.monotonic()

    if "cooccur" in tables:
        migrate_cooccur(r, cursor, args.batch, args.dry_run)

    if "word_docs" in tables:
        migrate_word_docs(r, cursor, args.batch, args.dry_run)

    if "word_lang" in tables:
        migrate_word_lang(r, cursor, args.batch, args.dry_run)

    if "idf" in tables:
        migrate_idf(r, cursor, args.batch, args.dry_run)

    if "meta" in tables:
        migrate_meta(r, cursor, args.dry_run)

    db.close()
    elapsed = time.monotonic() - t_start

    if not args.dry_run and r:
        key_count = r.dbsize()
        mem_info = r.info("memory")
        used_mb = mem_info.get("used_memory", 0) / (1024 * 1024)
        print(f"\nMigration complete in {elapsed:.0f}s")
        print(f"Redis keys: {key_count:,}  Memory: {used_mb:.0f}MB")
        print(f"\nNext steps:")
        print(f"  1. Add to ~/.TheIgors/Igor-wild-0001/.env:")
        print(f"     IGOR_REDIS_WORD_GRAPH_HOST=localhost")
        print(f"     IGOR_REDIS_WG_SHADOW=false")
        print(f"  2. Restart Igor (exit code 42 or restart)")
        print(f"  3. Test: ask Igor to predict words")
    else:
        print(f"\nDry run complete in {elapsed:.0f}s")


if __name__ == "__main__":
    main()
