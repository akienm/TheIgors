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
QUEUE_FILE = Path.home() / ".TheIgors" / "learn_queue.json"
LOG_DIR = Path.home() / ".TheIgors" / "logs"
LOG_FILE = LOG_DIR / "drain_learn_queue.log"
PID_FILE = Path.home() / ".TheIgors" / "drain_learn_queue.pid"

DEFAULT_LAUNCH_DELAY = 60  # seconds between launches
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

    if url.startswith("calibre://"):
        try:
            cid = int(url[len("calibre://") :])
            cmd += ["--calibre-id", str(cid)]
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
            _log(f"Launching: {title}")

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
