"""
retrain_word_graph.py — train all corpus books into the Postgres word graph.

Safe to run overnight: resource-gated, resumable, checkpoints every 10 books.
Run from repo root:
  nohup python claudecode/retrain_word_graph.py > /tmp/retrain_wg.log 2>&1 &

Postgres-backed since T-sqlite-out-word-graph-db (2026-05-02). Tables live
in clan.wg_* on the home_db; writes are synchronous via make_home_proxy.
"""

import gc, sys, os, time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from devices.igor.cognition.word_graph import WordGraph
from devices.igor.cognition import training_corpus as tc

BATCH_SIZE = 10  # close + reopen WordGraph instance every N books to GC

RAM_PAUSE_PCT = float(os.getenv("RETRAIN_RAM_PAUSE", "70"))
CPU_PAUSE_PCT = float(os.getenv("RETRAIN_CPU_PAUSE", "90"))
PAUSE_SECS = int(os.getenv("RETRAIN_PAUSE_SECS", "30"))

print(f"Word graph    : Postgres clan.wg_*", flush=True)
print(f"Corpus index  : {tc.INDEX_FILE}", flush=True)
print(f"RAM pause at  : {RAM_PAUSE_PCT}%  CPU pause at: {CPU_PAUSE_PCT}%", flush=True)
print(flush=True)

index = tc._load_index()
pending = [
    (bid, m) for bid, m in index.items() if m["status"] in ("pending", "in_progress")
]
complete = [(bid, m) for bid, m in index.items() if m["status"] == "complete"]
print(
    f"Total: {len(index)}  to train: {len(pending)}  already done: {len(complete)}",
    flush=True,
)
print(flush=True)

if not pending:
    print("Nothing to train — all books complete.", flush=True)
    sys.exit(0)


def _check_resources() -> None:
    """Block until RAM and CPU are under thresholds."""
    try:
        import psutil

        while True:
            vm = psutil.virtual_memory()
            load = os.getloadavg()[0] / (os.cpu_count() or 1) * 100
            if vm.percent < RAM_PAUSE_PCT and load < CPU_PAUSE_PCT:
                break
            print(
                f"  [pause] RAM {vm.percent:.0f}%  CPU {load:.0f}% — waiting {PAUSE_SECS}s...",
                flush=True,
            )
            time.sleep(PAUSE_SECS)
    except Exception:
        pass


def _recycle_wg() -> WordGraph:
    """GC and rebuild the WordGraph instance to free per-instance caches."""
    gc.collect()
    return WordGraph(name="word_graph")


wg = WordGraph(name="word_graph")

for i, (book_id, meta) in enumerate(pending, 1):
    _check_resources()

    print(f"[{i}/{len(pending)}] {meta['title'][:65]}  (id={book_id})", flush=True)
    result = tc.train(book_id, wg)
    print(f"           {result}", flush=True)

    # Every BATCH_SIZE books: GC and recycle the WordGraph instance.
    # No more WAL/SQLite checkpoint — Postgres writes are synchronous.
    if i % BATCH_SIZE == 0:
        print(f"  [recycle] GC + rebuilding WordGraph...", flush=True)
        wg = _recycle_wg()

        try:
            import psutil

            vm = psutil.virtual_memory()
            print(f"  [recycle] RAM {vm.percent:.0f}%", flush=True)
        except Exception:
            pass
        print(flush=True)

print("All done.", flush=True)
