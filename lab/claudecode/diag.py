#!/usr/bin/env python3
"""
Igor diagnostics — common inspection queries.

Usage:
  python3 claudecode/diag.py <command> [args]

Commands:
  perf          Pipeline timing summary for today (preparse/reasoning/total)
  memory-stats  Memory count, type breakdown, embedding coverage
  habits        All PROC memories (habits)
  recent-turns  Last N turns from interaction log (default 20)
  errors        Recent errors log tail
  ne-stats      NE run frequency + timing today
  embed-check   Time a live nomic-embed-text call
  db-size       DB and cache sizes
"""

import sys
import os
import sqlite3
from pathlib import Path
from datetime import date

DB = Path.home() / ".TheIgors/Igor-wild-0001/wild-0001.db"
LOGS = Path.home() / ".TheIgors/logs"
TODAY = date.today().strftime("%Y%m%d")


def cmd_perf(args):
    trace = LOGS / f"pipeline_trace.{TODAY}.log"
    if not trace.exists():
        print(f"No trace for today: {trace}")
        return
    steps = {"preparse_search": [], "reasoning": [], "TOTAL": []}
    with trace.open() as f:
        for line in f:
            for step in steps:
                if f"|step={step}|" in line:
                    ms_part = [p for p in line.split("|") if p.startswith("ms=")]
                    if ms_part:
                        steps[step].append(int(ms_part[0][3:]))
    print(f"Pipeline timing today ({TODAY}):")
    for step, vals in steps.items():
        if not vals:
            print(f"  {step}: no data")
            continue
        vals.sort()
        n = len(vals)
        p50 = vals[n // 2]
        p95 = vals[int(n * 0.95)]
        worst = vals[-1]
        avg = sum(vals) // n
        print(
            f"  {step:20s}  n={n:3d}  avg={avg:6d}ms  p50={p50:6d}ms  p95={p95:6d}ms  worst={worst:7d}ms"
        )

    # Habit fire rate
    trace = LOGS / f"pipeline_trace.{TODAY}.log"
    total_turns = 0
    habit_fires = 0
    habit_names = {}
    with trace.open() as f:
        for line in f:
            if "|step=bg_prospect|" in line:
                total_turns += 1
                parts = {
                    p.split("=")[0]: p.split("=")[1]
                    for p in line.split("|")
                    if "=" in p
                }
                h = parts.get("habit", "none")
                if h and h != "none":
                    habit_fires += 1
                    habit_names[h] = habit_names.get(h, 0) + 1
    if total_turns:
        rate = habit_fires / total_turns * 100
        print(f"\n  Habit fire rate: {habit_fires}/{total_turns} turns ({rate:.0f}%)")
        if habit_names:
            for name, count in sorted(habit_names.items(), key=lambda x: -x[1])[:10]:
                print(f"    {name}: {count}")


def cmd_memory_stats(args):
    db = sqlite3.connect(DB)
    total = db.execute("SELECT COUNT(*) FROM memories").fetchone()[0]
    with_emb = db.execute(
        "SELECT COUNT(*) FROM memories WHERE embedding IS NOT NULL"
    ).fetchone()[0]
    print(
        f"Total memories: {total}  (with embedding: {with_emb}, missing: {total - with_emb})"
    )
    print("\nBy type:")
    for row in db.execute(
        "SELECT memory_type, COUNT(*) as n FROM memories GROUP BY memory_type ORDER BY n DESC"
    ):
        print(f"  {row[0]:20s} {row[1]}")
    print("\nMissing embeddings by type:")
    for row in db.execute(
        "SELECT memory_type, COUNT(*) as n FROM memories WHERE embedding IS NULL GROUP BY memory_type ORDER BY n DESC"
    ):
        print(f"  {row[0]:20s} {row[1]}")


def cmd_habits(args):
    db = sqlite3.connect(DB)
    rows = db.execute(
        "SELECT id, narrative FROM memories WHERE memory_type='PROCEDURAL' ORDER BY narrative"
    ).fetchall()
    print(f"Habits (PROCEDURAL): {len(rows)}")
    for r in rows:
        print(f"  {r[0][:8]}  {r[1][:100]}")


def cmd_recent_turns(args):
    n = int(args[0]) if args else 20
    log = LOGS / f"interaction.{TODAY}.log"
    if not log.exists():
        print(f"No interaction log for today: {log}")
        return
    lines = log.read_text().splitlines()
    print(f"Last {n} turns ({TODAY}):")
    for line in lines[-n:]:
        parts = line.split("|")
        if len(parts) >= 6:
            ts, turn, ch, tier, ms, cost = parts[:6]
            inp = parts[6][:60] if len(parts) > 6 else ""
            print(f"  {ts[11:19]}  {tier:8s}  {ms:8s}  {cost:10s}  {inp}")


def cmd_errors(args):
    n = int(args[0]) if args else 30
    log = LOGS / "errors.log"
    if not log.exists():
        print("No errors.log")
        return
    lines = log.read_text().splitlines()
    print(f"Last {n} error lines:")
    for line in lines[:n]:
        print(" ", line)


def cmd_ne_stats(args):
    trace = LOGS / f"pipeline_trace.{TODAY}.log"
    if not trace.exists():
        print(f"No trace for today")
        return
    ne_times = []
    with trace.open() as f:
        for line in f:
            if "|step=ne|" in line:
                ms_part = [p for p in line.split("|") if p.startswith("ms=")]
                if ms_part:
                    ne_times.append(int(ms_part[0][3:]))
    if not ne_times:
        print("No NE runs today")
        return
    ne_times.sort()
    n = len(ne_times)
    print(f"NE runs today: {n}")
    print(
        f"  avg={sum(ne_times)//n}ms  p50={ne_times[n//2]}ms  p95={ne_times[int(n*0.95)]}ms  worst={ne_times[-1]}ms"
    )


def cmd_embed_check(args):
    import time

    try:
        import ollama

        t = time.time()
        r = ollama.embeddings(
            model="nomic-embed-text", prompt="diagnostics embedding speed check"
        )
        ms = (time.time() - t) * 1000
        print(f"nomic-embed-text: {ms:.0f}ms  dims={len(r['embedding'])}")
    except Exception as e:
        print(f"Embedding failed: {e}")


def cmd_db_size(args):
    db_path = DB
    cache_dir = Path.home() / ".TheIgors/cache/embeddings"

    def sz(p):
        try:
            b = (
                p.stat().st_size
                if p.is_file()
                else sum(f.stat().st_size for f in p.iterdir())
            )
            return f"{b / 1024 / 1024:.1f}MB"
        except Exception:
            return "?"

    def count(p):
        try:
            return len(list(p.iterdir()))
        except Exception:
            return "?"

    print(f"wild-0001.db:        {sz(db_path)}")
    # word_graph.db removed in T-sqlite-out-word-graph-db (Postgres-backed now)
    print(f"embedding cache:     {sz(cache_dir)}  ({count(cache_dir)} files)")


COMMANDS = {
    "perf": cmd_perf,
    "memory-stats": cmd_memory_stats,
    "habits": cmd_habits,
    "recent-turns": cmd_recent_turns,
    "errors": cmd_errors,
    "ne-stats": cmd_ne_stats,
    "embed-check": cmd_embed_check,
    "db-size": cmd_db_size,
}

if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] not in COMMANDS:
        print(__doc__)
        sys.exit(1)
    COMMANDS[sys.argv[1]](sys.argv[2:])
