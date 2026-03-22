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
POLL_INTERVAL=20

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
        export WORKER_TICKET="$NEXT"
        claude --dangerously-skip-permissions "/sprint $NEXT" || true
        unset WORKER_TICKET
        # claude exited — loop immediately for next ticket
    else
        sleep "$POLL_INTERVAL"
    fi
done
