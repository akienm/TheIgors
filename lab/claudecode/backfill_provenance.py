#!/usr/bin/env python3
"""
backfill_provenance.py — T-provenance-coverage-enforcement

Backfill deposited_by and deposited_at on existing memories where we can
infer provenance from existing data (source column, metadata.source,
book_title, etc.).

Usage:
    IGOR_HOME_DB_URL=postgresql://... python3 lab/claudecode/backfill_provenance.py [--dry-run]
"""

import json
import os
import sys
from datetime import datetime

DB_URL = os.environ.get("IGOR_HOME_DB_URL", "")
if not DB_URL:
    print("IGOR_HOME_DB_URL not set")
    sys.exit(1)


def run(dry_run: bool = False):
    import psycopg2

    conn = psycopg2.connect(DB_URL)
    conn.autocommit = False
    cur = conn.cursor()

    # Set search_path
    cur.execute("SET search_path TO instance, clan, infra, public")

    # Count current gaps
    cur.execute("""
        SELECT count(*) FROM memories
        WHERE NOT jsonb_exists(metadata, 'deposited_by')
    """)
    gap_count = cur.fetchone()[0]
    print(f"Memories missing deposited_by: {gap_count}")

    # Strategy 1: source column → deposited_by
    cur.execute("""
        SELECT count(*) FROM memories
        WHERE source IS NOT NULL AND source != ''
          AND NOT jsonb_exists(metadata, 'deposited_by')
    """)
    s1_count = cur.fetchone()[0]
    print(f"  Can fill from source column: {s1_count}")

    if not dry_run and s1_count > 0:
        cur.execute("""
            UPDATE memories
            SET metadata = jsonb_set(
                jsonb_set(metadata, '{deposited_by}', to_jsonb(source)),
                '{deposited_at}', to_jsonb(timestamp::text)
            )
            WHERE source IS NOT NULL AND source != ''
              AND NOT jsonb_exists(metadata, 'deposited_by')
        """)
        print(f"  Updated {cur.rowcount} rows from source column")

    # Strategy 2: metadata.source → deposited_by (for memories with no source column)
    cur.execute("""
        SELECT count(*) FROM memories
        WHERE (source IS NULL OR source = '')
          AND jsonb_exists(metadata, 'source')
          AND NOT jsonb_exists(metadata, 'deposited_by')
    """)
    s2_count = cur.fetchone()[0]
    print(f"  Can fill from metadata.source: {s2_count}")

    if not dry_run and s2_count > 0:
        cur.execute("""
            UPDATE memories
            SET metadata = jsonb_set(
                jsonb_set(metadata, '{deposited_by}', metadata->'source'),
                '{deposited_at}', to_jsonb(timestamp::text)
            )
            WHERE (source IS NULL OR source = '')
              AND jsonb_exists(metadata, 'source')
              AND NOT jsonb_exists(metadata, 'deposited_by')
        """)
        print(f"  Updated {cur.rowcount} rows from metadata.source")

    # Strategy 3: book_title present → deposited_by = 'reading'
    cur.execute("""
        SELECT count(*) FROM memories
        WHERE jsonb_exists(metadata, 'book_title')
          AND NOT jsonb_exists(metadata, 'deposited_by')
    """)
    s3_count = cur.fetchone()[0]
    print(f"  Can fill from book_title presence: {s3_count}")

    if not dry_run and s3_count > 0:
        cur.execute("""
            UPDATE memories
            SET metadata = jsonb_set(
                jsonb_set(metadata, '{deposited_by}', '"reading"'),
                '{deposited_at}', to_jsonb(timestamp::text)
            )
            WHERE jsonb_exists(metadata, 'book_title')
              AND NOT jsonb_exists(metadata, 'deposited_by')
        """)
        print(f"  Updated {cur.rowcount} rows from book_title")

    # Strategy 4: memory_type based defaults for remaining
    cur.execute("""
        SELECT memory_type, count(*) FROM memories
        WHERE NOT jsonb_exists(metadata, 'deposited_by')
        GROUP BY memory_type ORDER BY count(*) DESC
    """)
    remaining = cur.fetchall()
    if remaining:
        print(f"  Remaining gaps by type:")
        for mt, cnt in remaining:
            print(f"    {mt}: {cnt}")

    # Stamp deposited_by='genesis' on remaining (they're from initial setup)
    cur.execute("""
        SELECT count(*) FROM memories
        WHERE NOT jsonb_exists(metadata, 'deposited_by')
    """)
    genesis_count = cur.fetchone()[0]
    print(f"  Remaining after all strategies: {genesis_count} (will tag as 'genesis')")

    if not dry_run and genesis_count > 0:
        cur.execute("""
            UPDATE memories
            SET metadata = jsonb_set(
                jsonb_set(metadata, '{deposited_by}', '"genesis"'),
                '{deposited_at}', to_jsonb(timestamp::text)
            )
            WHERE NOT jsonb_exists(metadata, 'deposited_by')
        """)
        print(f"  Updated {cur.rowcount} rows as genesis")

    # Final count
    cur.execute("""
        SELECT count(*) FROM memories WHERE NOT jsonb_exists(metadata, 'deposited_by')
    """)
    final_gap = cur.fetchone()[0]

    if dry_run:
        print(
            f"\nDRY RUN — no changes made. Would fill {gap_count - final_gap} memories."
        )
        conn.rollback()
    else:
        conn.commit()
        print(f"\nDone. Remaining gaps: {final_gap}")

    cur.close()
    conn.close()


if __name__ == "__main__":
    dry = "--dry-run" in sys.argv
    run(dry_run=dry)
