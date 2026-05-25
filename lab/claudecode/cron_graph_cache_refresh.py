"""
cron_graph_cache_refresh.py — Daily GraphCache maintenance (D126 Step 5).

Runs once per day (3 AM by default via crontab). Decides between:
  - global_cache_refresh(): prune Redis to top-N by this box's access count
  - global_cache_flush():   full wipe + rebuild when top-N composition changed

How it detects composition change:
  Compare current top-N word list to the last known list stored in
  ~/.TheIgors/logs/wg_top_n_snapshot.json. If Jaccard similarity < 0.7,
  the composition has shifted enough to warrant a full flush.

Usage (crontab):
    0 3 * * * /path/to/venv/bin/python /path/to/claudecode/cron_graph_cache_refresh.py >> ~/.TheIgors/logs/graph_cache_refresh.log 2>&1
"""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path


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


_SNAPSHOT_PATH = Path.home() / ".TheIgors" / "logs" / "wg_top_n_snapshot.json"
_FLUSH_THRESHOLD = float(
    os.getenv("IGOR_WG_FLUSH_THRESHOLD", "0.7")
)  # Jaccard similarity


def _jaccard(a: list[str], b: list[str]) -> float:
    sa, sb = set(a), set(b)
    if not sa and not sb:
        return 1.0
    return len(sa & sb) / len(sa | sb)


def _load_snapshot() -> list[str]:
    try:
        if _SNAPSHOT_PATH.exists():
            return json.loads(_SNAPSHOT_PATH.read_text()).get("words", [])
    except Exception:
        pass
    return []


def _save_snapshot(words: list[str]) -> None:
    try:
        _SNAPSHOT_PATH.parent.mkdir(parents=True, exist_ok=True)
        _SNAPSHOT_PATH.write_text(
            json.dumps({"words": words, "ts": time.strftime("%Y-%m-%dT%H:%M:%S")})
        )
    except Exception as e:
        print(f"[cron_refresh] snapshot save failed: {e}")


def main():
    _load_env()

    # Add repo to path
    repo = Path(__file__).parent.parent
    sys.path.insert(0, str(repo))

    from devices.igor.memory.db_proxy import make_home_proxy, make_local_proxy
    from devices.igor.memory.graph_cache import GraphCache
    from devices.igor.memory.pending_replies import PendingReplyStore
    from devices.igor.paths import paths

    db_path = Path(os.getenv("IGOR_DB_PATH", str(paths().instance / "wild-0001.db")))

    home = make_home_proxy(db_path)
    local = make_local_proxy(db_path)

    # Wire pending drain first (clear any backlog before refresh)
    store = PendingReplyStore(local, home)
    drain_result = store.drain()
    print(f"[cron_refresh] pending drain: {drain_result}")

    cache = GraphCache(home, local, pending_store=store)

    # Flush in-memory access log to DB before comparing top-N
    cache._flush_access_log()

    # Get current top-N from this box's access log
    top_n = cache.max_words
    current = cache.get_my_top_n(top_n)
    previous = _load_snapshot()

    if not previous:
        # First run — just refresh, no comparison possible
        print(f"[cron_refresh] first run — prewarm {top_n} words")
        result = cache.prewarm(top_n)
        print(f"[cron_refresh] prewarm: {result} words loaded")
    else:
        similarity = _jaccard(current[:top_n], previous[:top_n])
        print(
            f"[cron_refresh] top-N Jaccard similarity={similarity:.3f} (threshold={_FLUSH_THRESHOLD})"
        )

        if similarity < _FLUSH_THRESHOLD:
            print("[cron_refresh] composition changed → global_cache_flush")
            result = cache.global_cache_flush()
        else:
            print("[cron_refresh] composition stable → global_cache_refresh")
            result = cache.global_cache_refresh(top_n)

        print(f"[cron_refresh] result: {result}")

    _save_snapshot(current)
    print(f"[cron_refresh] done at {time.strftime('%Y-%m-%dT%H:%M:%S')}")


if __name__ == "__main__":
    main()
