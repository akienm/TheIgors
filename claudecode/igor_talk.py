#!/usr/bin/env python3
"""
igor_talk.py — Claude Code ↔ Igor WebSocket bridge.

Usage:
    python igor_talk.py "your message here"
    python igor_talk.py --csb "message"   # wraps in [CC_MESSAGE] CSB block
    python igor_talk.py --timeout 60 "message"
    echo "message" | python igor_talk.py  # reads from stdin if no arg

Exit codes:
    0  — got a response
    1  — Igor unreachable or timed out
    2  — usage error

The script connects to Igor's WebSocket, sends a message, waits for his response,
prints it, and exits. Claude Code can then read the output and continue the
conversation by calling this script again.

Igor sees author="claude-code" in the incoming queue (not "web-user") so he
knows the message is machine-to-machine.
"""

import asyncio
import json
import ssl
import sys
import argparse
from datetime import datetime

try:
    import websockets
except ImportError:
    print(
        "ERROR: websockets not installed. Run: pip install websockets", file=sys.stderr
    )
    sys.exit(1)

WS_URL = "wss://localhost:8080/ws"


def _ssl_ctx() -> ssl.SSLContext:
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    return ctx


DEFAULT_TIMEOUT = 90  # Igor can take a while on complex turns


def _csb_wrap(content: str) -> str:
    """Wrap message in a CSB block so Igor recognises it as CC → Igor."""
    ts = datetime.now().strftime("%Y-%m-%dT%H:%M")
    return (
        f"[CC_MESSAGE|{ts}|from=claude-code]\n" f"{content.strip()}\n" f"[/CC_MESSAGE]"
    )


async def _talk(message: str, timeout: int, url: str = WS_URL) -> int:
    try:
        async with websockets.connect(url, ssl=_ssl_ctx()) as ws:
            payload = json.dumps(
                {"type": "message", "content": message, "author": "claude-code"}
            )
            await ws.send(payload)

            deadline = asyncio.get_event_loop().time() + timeout
            while True:
                remaining = deadline - asyncio.get_event_loop().time()
                if remaining <= 0:
                    print(
                        "ERROR: Timed out waiting for Igor's response.", file=sys.stderr
                    )
                    return 1
                try:
                    raw = await asyncio.wait_for(ws.recv(), timeout=remaining)
                except asyncio.TimeoutError:
                    print(
                        "ERROR: Timed out waiting for Igor's response.", file=sys.stderr
                    )
                    return 1

                try:
                    msg = json.loads(raw)
                except json.JSONDecodeError:
                    continue

                # Skip our own echo-back and activity frames
                if msg.get("type") == "activity":
                    continue
                if msg.get("type") == "message" and msg.get("author") in (
                    "user",
                    "claude-code",
                ):
                    continue

                # Igor's response — collect all messages until quiet for 5s
                if msg.get("type") == "message":
                    author = msg.get("author", "Igor")
                    content = msg.get("content", "")
                    ts = msg.get("ts", "")
                    print(f"[{author}|{ts}]\n{content}")
                    # Keep reading for up to 5 more seconds in case more follows
                    while True:
                        try:
                            raw2 = await asyncio.wait_for(ws.recv(), timeout=5.0)
                            msg2 = json.loads(raw2)
                            if msg2.get("type") == "activity":
                                continue
                            if msg2.get("type") == "message" and msg2.get("author") in (
                                "user",
                                "claude-code",
                            ):
                                continue
                            if msg2.get("type") == "message":
                                a2 = msg2.get("author", "Igor")
                                c2 = msg2.get("content", "")
                                t2 = msg2.get("ts", "")
                                print(f"\n[{a2}|{t2}]\n{c2}")
                        except (asyncio.TimeoutError, json.JSONDecodeError):
                            break
                    return 0

    except (
        OSError,
        ConnectionRefusedError,
        websockets.exceptions.InvalidURI,
        websockets.exceptions.WebSocketException,
    ) as e:
        print(f"ERROR: Cannot connect to Igor at {WS_URL}: {e}", file=sys.stderr)
        return 1


def main():
    parser = argparse.ArgumentParser(
        description="Send a message to Igor via WebSocket and print his response."
    )
    parser.add_argument(
        "message", nargs="?", help="Message to send (or pipe via stdin)"
    )
    parser.add_argument(
        "--csb", action="store_true", help="Wrap message in [CC_MESSAGE] CSB block"
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=DEFAULT_TIMEOUT,
        help=f"Seconds to wait for response (default {DEFAULT_TIMEOUT})",
    )
    parser.add_argument(
        "--url", default=WS_URL, help=f"WebSocket URL (default {WS_URL})"
    )

    args = parser.parse_args()

    # Get message from arg or stdin
    if args.message:
        message = args.message
    elif not sys.stdin.isatty():
        message = sys.stdin.read().strip()
    else:
        parser.print_help()
        sys.exit(2)

    if not message:
        print("ERROR: Empty message.", file=sys.stderr)
        sys.exit(2)

    if args.csb:
        message = _csb_wrap(message)

    exit_code = asyncio.run(_talk(message, args.timeout, args.url))
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
