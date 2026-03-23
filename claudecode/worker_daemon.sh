#!/usr/bin/env bash
# worker_daemon.sh — CC worker daemon.
#
# Runs in one konsole. Polls the task queue for pending tickets and runs
# `claude /sprint <id>` for each one. No xdotool injection needed.
#
# Launch via: python3 cc_queue.py worker-launch
# Or directly: bash ~/TheIgors/claudecode/worker_daemon.sh

set -uo pipefail

QUEUE_SCRIPT="$HOME/TheIgors/claudecode/cc_queue.py"
CHANNEL_SCRIPT="$HOME/TheIgors/claudecode/channel.py"
VENV="$HOME/TheIgors/venv/bin/activate"
DAEMON_PID_FILE="$HOME/.TheIgors/cc_channel/worker_daemon.pid"
DONE_FLAG="$HOME/.TheIgors/cc_channel/sprint_done.flag"
POLL_INTERVAL=20
SPRINT_TIMEOUT_SECS=5400   # 90 min hard ceiling — kill stalled session

source "$VENV"

# Write our PID so worker-launch can detect we're alive
echo $$ > "$DAEMON_PID_FILE"
trap 'rm -f "$DAEMON_PID_FILE"; python3 "$CHANNEL_SCRIPT" post "worker daemon stopped (PID $$)" --as worker-daemon 2>/dev/null || true' EXIT

_post() {
    python3 "$CHANNEL_SCRIPT" post "$1" --as worker-daemon 2>/dev/null || true
}

_next_ticket() {
    python3 "$QUEUE_SCRIPT" list 2>/dev/null \
        | grep '⬜' | head -1 | sed 's/^[^[]*\[\([^]]*\)\].*/\1/'
}

_post "worker daemon started (PID $$)"

while true; do
    NEXT=$(_next_ticket)
    if [ -n "$NEXT" ]; then
        _post "starting sprint: $NEXT"
        rm -f "$DONE_FLAG"   # clear any stale flag before launch
        export WORKER_TICKET="$NEXT"

        # Launch claude in background — sprint skill never self-exits
        claude --dangerously-skip-permissions "/sprint $NEXT" &
        CLAUDE_PID=$!

        # Poll for done-flag or natural exit; enforce hard timeout
        ELAPSED=0
        while kill -0 "$CLAUDE_PID" 2>/dev/null; do
            if [ -f "$DONE_FLAG" ]; then
                DONE_TICKET=$(cat "$DONE_FLAG" 2>/dev/null || echo "unknown")
                _post "sprint done: $DONE_TICKET — killing session (PID $CLAUDE_PID)"
                kill "$CLAUDE_PID" 2>/dev/null || true
                rm -f "$DONE_FLAG"
                break
            fi
            if [ "$ELAPSED" -ge "$SPRINT_TIMEOUT_SECS" ]; then
                _post "sprint timeout: $NEXT — killing stalled session (PID $CLAUDE_PID)"
                kill "$CLAUDE_PID" 2>/dev/null || true
                break
            fi
            sleep 5
            ELAPSED=$((ELAPSED + 5))
        done
        wait "$CLAUDE_PID" 2>/dev/null || true

        unset WORKER_TICKET
        # session dead — loop immediately for next ticket
    else
        sleep "$POLL_INTERVAL"
    fi
done
