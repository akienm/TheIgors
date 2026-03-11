"""
retrain_word_graph.py — train all corpus books into the SQLite word graph.

Safe to run overnight: resource-gated, resumable, checkpoints every 10 books.
Run from repo root:
  nohup python claudecode/retrain_word_graph.py > /tmp/retrain_wg.log 2>&1 &
"""
import gc, sys, os, time, sqlite3
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.environ.setdefault("IGOR_DB_PATH",
    str(Path.home() / ".TheIgors" / "igor_wild_0001" / "wild-0001.db"))

from wild_igor.igor.cognition.word_graph import WordGraph, default_cache_path
from wild_igor.igor.cognition import training_corpus as tc

WG_PATH    = default_cache_path("word_graph")
BATCH_SIZE = 10   # close + reopen connection every N books to flush WAL + GC

RAM_PAUSE_PCT  = float(os.getenv("RETRAIN_RAM_PAUSE",  "70"))
CPU_PAUSE_PCT  = float(os.getenv("RETRAIN_CPU_PAUSE",  "90"))
PAUSE_SECS     = int(os.getenv("RETRAIN_PAUSE_SECS",   "30"))

print(f"Word graph DB : {WG_PATH}", flush=True)
print(f"Corpus index  : {tc.INDEX_FILE}", flush=True)
print(f"RAM pause at  : {RAM_PAUSE_PCT}%  CPU pause at: {CPU_PAUSE_PCT}%", flush=True)
print(flush=True)

index = tc._load_index()
pending  = [(bid, m) for bid, m in index.items() if m["status"] in ("pending", "in_progress")]
complete = [(bid, m) for bid, m in index.items() if m["status"] == "complete"]
print(f"Total: {len(index)}  to train: {len(pending)}  already done: {len(complete)}", flush=True)
print(flush=True)

if not pending:
    print("Nothing to train — all books complete.", flush=True)
    sys.exit(0)


def _check_resources() -> None:
    """Block until RAM and CPU are under thresholds."""
    try:
        import psutil
        while True:
            vm   = psutil.virtual_memory()
            load = os.getloadavg()[0] / (os.cpu_count() or 1) * 100
            if vm.percent < RAM_PAUSE_PCT and load < CPU_PAUSE_PCT:
                break
            print(f"  [pause] RAM {vm.percent:.0f}%  CPU {load:.0f}% — waiting {PAUSE_SECS}s...", flush=True)
            time.sleep(PAUSE_SECS)
    except Exception:
        pass


def _checkpoint_and_reload(wg_path: Path) -> WordGraph:
    """Force WAL flush, close, GC, reopen clean connection."""
    try:
        conn = sqlite3.connect(str(wg_path))
        conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
        conn.close()
    except Exception:
        pass
    gc.collect()
    return WordGraph(name=wg_path.stem, db_path=wg_path)


wg = WordGraph(name=WG_PATH.stem, db_path=WG_PATH)

for i, (book_id, meta) in enumerate(pending, 1):
    _check_resources()

    print(f"[{i}/{len(pending)}] {meta['title'][:65]}  (id={book_id})", flush=True)
    result = tc.train(book_id, wg, WG_PATH)
    print(f"           {result}", flush=True)

    # Every BATCH_SIZE books: checkpoint WAL, close, GC, reopen
    if i % BATCH_SIZE == 0:
        print(f"  [checkpoint] flushing WAL and recycling connection...", flush=True)
        wg = _checkpoint_and_reload(WG_PATH)

        try:
            import psutil
            vm = psutil.virtual_memory()
            wal = WG_PATH.with_suffix(".db-wal")
            wal_mb = wal.stat().st_size // (1024*1024) if wal.exists() else 0
            print(f"  [checkpoint] RAM {vm.percent:.0f}%  WAL {wal_mb}MB", flush=True)
        except Exception:
            pass
        print(flush=True)

# Final checkpoint
print("Final checkpoint...", flush=True)
wg = _checkpoint_and_reload(WG_PATH)
print("All done.", flush=True)
