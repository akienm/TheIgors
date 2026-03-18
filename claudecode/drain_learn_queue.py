#!/usr/bin/env python3
"""
drain_learn_queue.py — Background overnight learning queue runner.

Loops over ~/.TheIgors/learn_queue.json and launches book_learner for each
pending item, then exits when the queue is empty.

Pacing: LAUNCH_DELAY seconds between launches (default 60) so we don't
hammer the machine or OpenRouter.  Each book_learner itself runs as a
further detached subprocess — this script just orchestrates the launches.

Usage (called by learner.py or directly):
  python3 claudecode/drain_learn_queue.py [--delay SECS]
"""

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path

# ── Paths ─────────────────────────────────────────────────────────────────────
REPO = Path(__file__).parent.parent
VENV_PYTHON = REPO / "venv" / "bin" / "python"
BOOK_LEARNER = REPO / "claudecode" / "book_learner.py"
sys.path.insert(0, str(REPO))
from wild_igor.igor.paths import paths as _igor_paths  # noqa: E402

QUEUE_FILE = _igor_paths().learn_queue
LOG_DIR = _igor_paths().logs
LOG_FILE = LOG_DIR / "drain_learn_queue.log"
PID_FILE = _igor_paths().drain_pid

DEFAULT_LAUNCH_DELAY = 60  # seconds between launches
MAX_BOOK_LEARNER_AGE_MINUTES = 45  # kill book_learner if stuck longer than this

# G-OVN-4 / G-QP3: adaptive concurrency — scales with observed system load
# cpu_pct < 40 and mem_gb > 4  → up to 4 concurrent (idle overnight machine)
# cpu_pct < 70 and mem_gb > 2  → up to 2 concurrent (normal load)
# otherwise                    → 1 (busy / low mem)
_CONCURRENCY_TABLE = [
    (40, 4.0, 4),
    (70, 2.0, 2),
    (100, 0.0, 1),
]


def _adaptive_max_concurrent() -> int:
    """Return concurrency cap based on current CPU load and available memory."""
    try:
        import psutil

        cpu = psutil.cpu_percent(interval=1)
        mem_gb = psutil.virtual_memory().available / (1024**3)
        for cpu_thresh, mem_thresh, cap in _CONCURRENCY_TABLE:
            if cpu < cpu_thresh and mem_gb > mem_thresh:
                return cap
        return 1
    except Exception:
        return 2  # safe fallback if psutil unavailable


_CLOUD_OK_OVERRIDE_FILE = Path.home() / ".TheIgors" / "cloud_ok_override.json"


def _is_cloud_ok_override() -> bool:
    """True if a cloud_ok override is currently active (D071)."""
    try:
        if not _CLOUD_OK_OVERRIDE_FILE.exists():
            return False
        data = json.loads(_CLOUD_OK_OVERRIDE_FILE.read_text())
        if not data.get("active", False):
            return False
        expires = data.get("expires")
        if expires:
            from datetime import datetime as _dt

            if _dt.now() > _dt.fromisoformat(expires):
                return False
        return True
    except Exception:
        return False


def _log(msg: str) -> None:
    ts = time.strftime("%Y-%m-%dT%H:%M:%S")
    line = f"{ts}  {msg}\n"
    print(line, end="", flush=True)
    try:
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        with open(LOG_FILE, "a") as f:
            f.write(line)
    except Exception:
        pass


def _load_queue() -> list:
    try:
        if QUEUE_FILE.exists():
            return json.loads(QUEUE_FILE.read_text())
    except Exception:
        pass
    return []


def _save_queue(q: list) -> None:
    QUEUE_FILE.write_text(json.dumps(q, indent=2))


_IGOR_DB_PATH = Path(
    os.environ.get(
        "IGOR_DB_PATH",
        Path.home() / ".TheIgors" / "igor_wild_0001" / "wild-0001.db",
    )
)


def _set_reading_list_in_progress(calibre_id: int) -> None:
    """G-RL3: mark reading_list entry in_progress when drain launches it."""
    try:
        import sqlite3 as _sqlite3

        conn = _sqlite3.connect(str(_IGOR_DB_PATH))
        conn.execute(
            "UPDATE reading_list SET status='in_progress', started_at=datetime('now')"
            " WHERE source=? AND status='queued'",
            (f"calibre://{calibre_id}",),
        )
        conn.commit()
        conn.close()
    except Exception as e:
        _log(f"reading_list update failed: {e}")


def _another_drain_running() -> bool:
    """True if another drain_learn_queue.py Python process is already running (not us).

    Matches only processes where the script path appears as a standalone cmdline
    argument (i.e., the Python interpreter's argv[1]), not shell wrapper processes
    where the path is embedded inside a -c string.
    """
    try:
        import psutil

        my_pid = os.getpid()
        script_path = str(Path(__file__).resolve())
        for proc in psutil.process_iter(["pid", "cmdline"]):
            if proc.pid == my_pid:
                continue
            cmdline = proc.info.get("cmdline") or []
            # Match Python processes where our script is an explicit argument,
            # not shell processes with it buried in a -c "..." string.
            if any(c == script_path for c in cmdline):
                return True
        return False
    except Exception:
        return False


def _reap_hung_learners() -> int:
    """Kill book_learner processes older than MAX_BOOK_LEARNER_AGE_MINUTES. Returns kill count."""
    killed = 0
    try:
        import psutil

        now = time.time()
        for proc in psutil.process_iter(["pid", "cmdline", "create_time"]):
            cmdline = proc.info.get("cmdline") or []
            if not any("book_learner" in c for c in cmdline):
                continue
            age_minutes = (now - proc.info["create_time"]) / 60
            if age_minutes > MAX_BOOK_LEARNER_AGE_MINUTES:
                _log(f"Killing hung book_learner pid={proc.pid} age={age_minutes:.0f}m")
                proc.kill()
                killed += 1
    except Exception as e:
        _log(f"_reap_hung_learners error: {e}")
    return killed


def _count_running_learners() -> int:
    """Count currently running book_learner.py processes via psutil (G-OVN-4)."""
    try:
        import psutil

        count = 0
        for proc in psutil.process_iter(["cmdline"]):
            cmdline = proc.info.get("cmdline") or []
            if any("book_learner" in c for c in cmdline):
                count += 1
        return count
    except Exception:
        return 0


def _launch(entry: dict) -> bool:
    python = str(VENV_PYTHON) if VENV_PYTHON.exists() else sys.executable
    url = entry.get("url", "")
    title = entry.get("title", url)[:80]
    # D071: --local flag only if queue item has cloud_ok=False AND no override active.
    # book_learner also checks cloud_ok_override per chunk, so this is belt-and-suspenders.
    use_local = not entry.get("cloud_ok", True) and not _is_cloud_ok_override()
    cmd = [python, str(BOOK_LEARNER), "--run", "--resume"]
    if use_local:
        cmd.append("--local")

    calibre_id_for_status: int | None = None
    if url.startswith("calibre://"):
        try:
            cid = int(url[len("calibre://") :])
            cmd += ["--calibre-id", str(cid)]
            calibre_id_for_status = cid
        except ValueError:
            _log(f"SKIP bad calibre URL: {url}")
            return False
    elif url:
        cmd += ["--url", url, "--title", title]
    else:
        _log("SKIP empty entry")
        return False

    try:
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        log_file = open(LOG_DIR / "book_learner.log", "a")
        subprocess.Popen(cmd, stdout=log_file, stderr=log_file, start_new_session=True)
        if calibre_id_for_status is not None:
            _set_reading_list_in_progress(calibre_id_for_status)
        return True
    except Exception as e:
        _log(f"LAUNCH ERROR: {e}")
        return False


def main() -> None:
    parser = argparse.ArgumentParser(description="Drain the Igor learn queue")
    parser.add_argument(
        "--delay",
        type=float,
        default=DEFAULT_LAUNCH_DELAY,
        help=f"Seconds between launches (default {DEFAULT_LAUNCH_DELAY})",
    )
    args = parser.parse_args()

    # Single-instance guard: exit if another drain is already running.
    # (Cron fires every 30 min; without this every invocation stacks up.)
    if _another_drain_running():
        print(f"drain_learn_queue: already running — exiting", flush=True)
        return

    # Write PID file so learner.py can detect we're running
    PID_FILE.write_text(str(os.getpid()))

    try:
        _log(f"drain_learn_queue: starting (pid={os.getpid()}, delay={args.delay}s)")

        while True:
            q = _load_queue()
            pending = [e for e in q if not e.get("done")]

            if not pending:
                _log("drain_learn_queue: queue empty — exiting")
                break

            entry = pending[0]
            title = entry.get("title", entry.get("url", "?"))[:60]

            # G-OVN-4 / G-QP3: adaptive concurrency cap based on system load.
            # Reap hung learners before checking count so stale processes don't
            # block the queue indefinitely.
            _reap_hung_learners()
            running = _count_running_learners()
            cap = _adaptive_max_concurrent()
            if running >= cap:
                _log(
                    f"Concurrency cap ({cap}) reached ({running} running, cap={cap}) — sleeping {args.delay}s"
                )
                time.sleep(args.delay)
                continue

            _log(f"Launching: {title} ({running} running, cap={cap})")

            ok = _launch(entry)
            entry["done"] = True  # mark done regardless — skip permanent failures
            _save_queue(q)

            if ok:
                _log(f"Launched OK: {title}")
            else:
                _log(f"FAILED (skipped): {title}")

            remaining = len([e for e in _load_queue() if not e.get("done")])
            if remaining:
                _log(f"{remaining} item(s) remaining — sleeping {args.delay}s")
                time.sleep(args.delay)

        _log("drain_learn_queue: done")
    finally:
        try:
            PID_FILE.unlink(missing_ok=True)
        except Exception:
            pass


if __name__ == "__main__":
    main()
