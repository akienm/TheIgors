#!/usr/bin/env python3
"""
Detached overnight reading launcher.
Spawns book_learner processes sequentially, fully detached from the parent shell.
Safe to run multiple times — only starts if no overnight_reading is already running.
"""
import os
import subprocess
import sys
import time
from pathlib import Path

REPO        = Path(__file__).parent.parent
VENV_PY     = REPO / "venv" / "bin" / "python"
BOOK_LEARNER = REPO / "claudecode" / "book_learner.py"
LOG_DIR     = Path.home() / ".TheIgors" / "logs"
DB_PATH     = Path.home() / ".TheIgors" / "igor_wild_0001" / "wild-0001.db"

BOOKS = [
    ("On Intelligence (Hawkins)",         ["--calibre-id", "1959",  "--run"]),
    ("The Political Mind (Lakoff)",        ["--calibre-id", "2241",  "--run"]),
    ("Feeling of What Happens (resume)",   ["--calibre-id", "3023",  "--run", "--resume"]),
    ("Looking for Spinoza (Damasio)",      ["--calibre-id", "3300",  "--run"]),
    ("Illusions (Bach)",                   ["--calibre-id", "831",   "--run"]),
    ("The Moon Is a Harsh Mistress",       ["--calibre-id", "3341",  "--run"]),
]

def main():
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    log_path = LOG_DIR / f"overnight_reading_{time.strftime('%Y%m%d_%H%M')}.log"

    env = os.environ.copy()
    env["IGOR_DB_PATH"] = str(DB_PATH)

    with open(log_path, "w") as log:
        log.write(f"Overnight reading started {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        log.flush()

        for label, args in BOOKS:
            log.write(f"\n{'='*50}\n{time.strftime('%Y-%m-%d %H:%M:%S')} START: {label}\n")
            log.flush()

            cmd = [str(VENV_PY), str(BOOK_LEARNER)] + args + ["--local"]
            result = subprocess.run(
                cmd,
                env=env,
                stdout=log,
                stderr=log,
                stdin=subprocess.DEVNULL,
            )
            log.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} DONE: {label} (exit {result.returncode})\n")
            log.flush()

        log.write(f"\nOvernight reading complete {time.strftime('%Y-%m-%d %H:%M:%S')}\n")

    print(f"Complete. Log: {log_path}")


if __name__ == "__main__":
    # Double-fork to fully detach
    if "--foreground" in sys.argv:
        main()
    else:
        # Fork once
        pid = os.fork()
        if pid > 0:
            print(f"Overnight reading launched (PID {pid}). Log: {LOG_DIR}/overnight_reading_*.log")
            sys.exit(0)
        # Child: create new session, fork again
        os.setsid()
        pid2 = os.fork()
        if pid2 > 0:
            sys.exit(0)
        # Grandchild: fully detached
        os.chdir("/")
        sys.stdin  = open(os.devnull, "r")
        sys.stdout = open(os.devnull, "w")
        sys.stderr = open(os.devnull, "w")
        main()
