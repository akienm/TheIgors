#!/usr/bin/env python3
"""
phrase_regression.py — send test phrases to Igor via CC bridge at intervals.

Usage:
  python claudecode/phrase_regression.py [--file PATH] [--delay 300] [--passes 2] [--random]

Reads phrases from a file (one per line; blank lines ignored).
Sends each phrase to Igor via POST /api/cc_send.
Waits --delay seconds between phrases.
Runs --passes full passes through the list.
--random shuffles phrase order each pass.

Log: ~/.TheIgors/logs/phrase_regression.log (prepend newest-first).
"""

import argparse
import json
import random
import sys
import time
import urllib.request
from datetime import datetime
from pathlib import Path

LOG_PATH = Path.home() / ".TheIgors" / "logs" / "phrase_regression.log"
CC_BRIDGE = "http://localhost:8080/api/cc_send"


def _log(msg: str) -> None:
    ts = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    line = f"{ts}  {msg}"
    print(line)
    try:
        existing = LOG_PATH.read_text() if LOG_PATH.exists() else ""
        LOG_PATH.write_text(line + "\n" + existing)
    except Exception:
        pass


def _send(phrase: str) -> bool:
    try:
        payload = json.dumps({"content": phrase}).encode()
        req = urllib.request.Request(
            CC_BRIDGE,
            data=payload,
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.status == 200
    except Exception as e:
        _log(f"SEND_FAIL phrase='{phrase[:40]}' err={e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Phrase regression runner for Igor")
    parser.add_argument(
        "--file",
        default=str(
            Path.home()
            / "TheIgorsProject"
            / "akien"
            / "automated_phrase_response_test.txt"
        ),
        help="Path to phrase file",
    )
    parser.add_argument(
        "--delay",
        type=int,
        default=300,
        help="Seconds between phrases (default 300 = 5min)",
    )
    parser.add_argument(
        "--passes", type=int, default=2, help="Number of full passes (default 2)"
    )
    parser.add_argument(
        "--random", action="store_true", help="Randomize phrase order each pass"
    )
    args = parser.parse_args()

    phrase_file = Path(args.file)
    if not phrase_file.exists():
        print(f"ERROR: file not found: {phrase_file}")
        sys.exit(1)

    phrases = [
        line.strip() for line in phrase_file.read_text().splitlines() if line.strip()
    ]

    if not phrases:
        print("ERROR: no phrases found in file")
        sys.exit(1)

    _log(
        f"START passes={args.passes} phrases={len(phrases)} delay={args.delay}s "
        f"random={args.random} file={phrase_file.name}"
    )

    for pass_num in range(1, args.passes + 1):
        order = list(range(len(phrases)))
        if args.random:
            random.shuffle(order)

        _log(
            f"PASS {pass_num}/{args.passes} begin order={'random' if args.random else 'sequential'}"
        )

        for idx, phrase_idx in enumerate(order):
            phrase = phrases[phrase_idx]
            _log(
                f"SEND pass={pass_num} phrase={idx+1}/{len(phrases)} text='{phrase[:60]}'"
            )
            ok = _send(phrase)
            if ok:
                _log(f"SENT ok — check interaction log in ~2min for response")
            else:
                _log(f"SENT failed — Igor may not be running")

            if not (pass_num == args.passes and idx == len(order) - 1):
                _log(f"WAIT {args.delay}s")
                time.sleep(args.delay)

    _log(f"DONE {args.passes} pass(es) complete")


if __name__ == "__main__":
    main()
