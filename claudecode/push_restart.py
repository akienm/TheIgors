#!/usr/bin/env python3
"""
push_restart.py — Signal Igor to restart by creating the restart flag file.

Usage:
    python push_restart.py                      # restart Igor-wild-0001 (default)
    python push_restart.py --id Igor-wild-0002  # restart a specific instance

Igor's main loop checks for ~/.TheIgors/<instance_id>/restart.flag each tick.
When found, it deletes the file and exits with code 42 (restart).
No LLM, no arbiter, no safety review — pure operational signal.
"""

import argparse
import os
from pathlib import Path


def push_restart(instance_id: str = "") -> Path:
    if not instance_id:
        instance_id = os.getenv("IGOR_INSTANCE_ID", "Igor-wild-0001")
    flag = Path.home() / ".TheIgors" / instance_id / "restart.flag"
    flag.parent.mkdir(parents=True, exist_ok=True)
    flag.touch()
    return flag


def main():
    parser = argparse.ArgumentParser(
        description="Signal Igor to restart via flag file."
    )
    parser.add_argument(
        "--id",
        default="",
        help="Instance ID (default: IGOR_INSTANCE_ID or Igor-wild-0001)",
    )
    args = parser.parse_args()
    flag = push_restart(args.id)
    print(f"Restart flag created: {flag}")
    print("Igor will restart on its next idle tick (within ~0.5s).")


if __name__ == "__main__":
    main()
