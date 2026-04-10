#!/usr/bin/env python3
"""
run_phrase_test.py — Send each phrase from automated_phrase_response_test.txt
to Igor via cc_send, one at a time, with a 5-minute gap between each.

Saves progress to a state file so it can resume after interruption.
Exits when all phrases have been sent.

Usage:
    python3 ~/TheIgors/lab/claudecode/run_phrase_test.py
    python3 ~/TheIgors/lab/claudecode/run_phrase_test.py --reset   # start over
"""

import argparse
import json
import ssl
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

PHRASES_FILE = Path(
    "/home/akien/TheIgorsProject/akien/automated_phrase_response_test.txt"
)
STATE_FILE = Path.home() / ".TheIgors" / "phrase_test_state.json"
URL = "https://localhost:8080/api/cc_send"
INTERVAL_SEC = 5 * 60  # 5 minutes


def load_phrases() -> list[str]:
    lines = PHRASES_FILE.read_text().splitlines()
    return [l.strip() for l in lines if l.strip()]


def load_state() -> dict:
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text())
    return {"next_index": 0}


def save_state(state: dict) -> None:
    STATE_FILE.write_text(json.dumps(state))


def send(phrase: str) -> bool:
    payload = json.dumps({"content": phrase}).encode()
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    req = urllib.request.Request(
        URL,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=10, context=ctx):
            return True
    except urllib.error.URLError as e:
        print(f"  ERROR: {e}", file=sys.stderr)
        return False


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--reset", action="store_true", help="Start over from phrase 1")
    args = parser.parse_args()

    phrases = load_phrases()
    total = len(phrases)

    if args.reset:
        save_state({"next_index": 0})

    state = load_state()
    idx = state["next_index"]

    if idx >= total:
        print("All phrases already sent. Use --reset to run again.")
        sys.exit(0)

    print(f"Phrase test — {total} phrases, starting at #{idx + 1}, 5-min intervals")

    while idx < total:
        phrase = phrases[idx]
        print(f"[{idx + 1:03d}/{total}] {phrase[:70]}", flush=True)
        ok = send(phrase)
        if ok:
            print(f"  sent", flush=True)
        idx += 1
        save_state({"next_index": idx})

        if idx < total:
            print(f"  waiting 5 min...", flush=True)
            time.sleep(INTERVAL_SEC)

    print(f"\nDone — all {total} phrases sent.")


if __name__ == "__main__":
    main()
