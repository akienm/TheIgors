#!/usr/bin/env python3
"""
cc_bridge.py — Persistent bidirectional Claude Code ↔ Igor bridge daemon.

Stays connected to Igor's WebSocket. When Igor addresses CC (his message
starts with "CC:" or "CC>"), invokes `claude -p` and sends the response back
as author=claude-code, prefixed "CC> " — visible in the web UI as orange.

Igor can drive: say "CC: what do you think about X"
CC can drive: run igor_talk.py or inject via the bridge's send() helper

Run as background daemon:
    python claudecode/cc_bridge.py &
    # or
    python claudecode/cc_bridge.py --daemon

Logs to ~/.TheIgors/logs/cc_bridge.log
"""

import argparse
import asyncio
import json
import logging
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

try:
    import websockets
except ImportError:
    print("ERROR: websockets not installed. Run: pip install websockets", file=sys.stderr)
    sys.exit(1)

WS_URL      = "ws://localhost:8080/ws"
CLAUDE_BIN  = shutil.which("claude") or "/home/akien/.local/bin/claude"
CLAUDE_TIMEOUT = 120   # seconds per CC response
RECONNECT_DELAY = 5    # seconds between reconnect attempts

LOG_PATH = Path.home() / ".TheIgors" / "logs" / "cc_bridge.log"

# ── Logging ───────────────────────────────────────────────────────────────────

def _setup_logging(verbose: bool) -> logging.Logger:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    log = logging.getLogger("cc_bridge")
    log.setLevel(logging.DEBUG if verbose else logging.INFO)
    fh = logging.FileHandler(LOG_PATH)
    fh.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    log.addHandler(fh)
    if verbose:
        sh = logging.StreamHandler()
        sh.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
        log.addHandler(sh)
    return log


# ── CC invocation ─────────────────────────────────────────────────────────────

def _call_claude(prompt: str, log: logging.Logger) -> str | None:
    """Invoke `claude -p` and return the response text, or None on failure."""
    if not CLAUDE_BIN or not Path(CLAUDE_BIN).exists():
        log.error("claude binary not found at %s", CLAUDE_BIN)
        return None
    try:
        import os
        env = {k: v for k, v in os.environ.items() if k != "CLAUDECODE"}
        result = subprocess.run(
            [CLAUDE_BIN, "-p", prompt],
            capture_output=True,
            text=True,
            timeout=CLAUDE_TIMEOUT,
            env=env,
        )
        if result.returncode != 0:
            log.warning("claude exited %d: %s", result.returncode, result.stderr[:200])
            return result.stdout.strip() or None
        return result.stdout.strip() or None
    except subprocess.TimeoutExpired:
        log.error("claude timed out after %ds", CLAUDE_TIMEOUT)
        return None
    except Exception as e:
        log.error("claude invocation failed: %s", e)
        return None


# ── Bridge loop ───────────────────────────────────────────────────────────────

def _is_cc_addressed(content: str) -> bool:
    """True if Igor is addressing CC in this message."""
    low = content.strip().lower()
    return low.startswith("cc:") or low.startswith("cc>")


def _strip_cc_prefix(content: str) -> str:
    """Remove the CC: / CC> prefix Igor uses to address CC."""
    stripped = content.strip()
    if stripped[:3].lower() in ("cc:", "cc>"):
        return stripped[3:].strip()
    return stripped


async def _bridge(ws_url: str, log: logging.Logger) -> None:
    """One connected session — reconnects on exit."""
    log.info("connecting to %s", ws_url)
    async with websockets.connect(ws_url) as ws:
        log.info("connected")
        # Announce presence
        await ws.send(json.dumps({
            "type": "message",
            "content": "CC> bridge online — say 'CC: <message>' to address me",
            "author": "claude-code",
        }))

        async for raw in ws:
            try:
                msg = json.loads(raw)
            except json.JSONDecodeError:
                continue

            if msg.get("type") != "message":
                continue

            author  = msg.get("author", "")
            content = msg.get("content", "").strip()

            # Only respond to Igor addressing CC directly
            if author != "igor":
                continue
            if not _is_cc_addressed(content):
                continue

            prompt = _strip_cc_prefix(content)
            if not prompt:
                continue

            log.info("Igor→CC: %s", prompt[:120])

            # Run Claude (blocking subprocess — fine in executor for asyncio)
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(None, _call_claude, prompt, log)

            if response:
                log.info("CC→Igor: %s", response[:120])
                reply = f"CC> {response}"
            else:
                reply = "CC> (no response — claude invocation failed)"

            await ws.send(json.dumps({
                "type": "message",
                "content": reply,
                "author": "claude-code",
            }))


async def _run_forever(ws_url: str, log: logging.Logger) -> None:
    """Reconnect loop."""
    while True:
        try:
            await _bridge(ws_url, log)
        except (OSError, ConnectionRefusedError,
                websockets.exceptions.WebSocketException) as e:
            log.warning("disconnected (%s) — retrying in %ds", e, RECONNECT_DELAY)
            await asyncio.sleep(RECONNECT_DELAY)
        except KeyboardInterrupt:
            log.info("shutting down")
            break
        except Exception as e:
            log.error("unexpected error: %s", e)
            await asyncio.sleep(RECONNECT_DELAY)


# ── Entry point ───────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="CC↔Igor bridge daemon")
    parser.add_argument("--url",     default=WS_URL, help="Igor WebSocket URL")
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    log = _setup_logging(args.verbose)
    log.info("cc_bridge starting (claude=%s)", CLAUDE_BIN)

    try:
        asyncio.run(_run_forever(args.url, log))
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
