#!/usr/bin/env bash
# worker_daemon.sh — CC worker daemon.
#
# Polls cc_queue.py next for the highest-priority unclaimed sprint ticket and
# runs `claude /sprint <id>` for each one. Respects the queue gate file
# (~/.TheIgors/cc_channel/queue_gate.json) — sleeps when gate is tripped.
# Self-restarts via exec when this script is updated between iterations.
#
# Launch via: python3 cc_queue.py worker-launch
# Or directly: bash ~/TheIgors/lab/claudecode/worker_daemon.sh

set -uo pipefail

QUEUE_SCRIPT="$HOME/TheIgors/lab/claudecode/cc_queue.py"
CHANNEL_SCRIPT="$HOME/TheIgors/lab/claudecode/channel.py"
VENV="$HOME/TheIgors/venv/bin/activate"
DAEMON_PID_FILE="$HOME/.TheIgors/cc_channel/worker_daemon.pid"
DONE_FLAG="$HOME/.TheIgors/cc_channel/sprint_done.flag"
SPRINT_TIMEOUT_SECS=1800   # 30 min hard ceiling — kill stalled session
SWITCHES_CFG="$HOME/.TheIgors/Igor-wild-0001/igor.switches.cfg"

source "$VENV"

# Write our PID so worker-launch can detect we're alive
echo $$ > "$DAEMON_PID_FILE"
trap 'rm -f "$DAEMON_PID_FILE"; python3 "$CHANNEL_SCRIPT" post "worker daemon stopped (PID $$)" --as worker-daemon 2>/dev/null || true' EXIT

_post() {
    python3 "$CHANNEL_SCRIPT" post "$1" --as worker-daemon 2>/dev/null || true
}

# Reset any tickets left in_progress by a prior daemon run
python3 "$QUEUE_SCRIPT" reset-stale 2>/dev/null | grep -v "^Reset 0" | while IFS= read -r line; do _post "startup: $line"; done || true

_post "worker daemon started (PID $$)"

# Capture our own path and mtime for self-restart detection
SELF="$(realpath "${BASH_SOURCE[0]}")"
SELF_MTIME=$(stat -c %Y "$SELF" 2>/dev/null || echo "0")

while true; do
    # Self-restart: if script was updated since last iteration, exec to reload
    CURRENT_MTIME=$(stat -c %Y "$SELF" 2>/dev/null || echo "0")
    if [ "$SELF_MTIME" != "0" ] && [ "$CURRENT_MTIME" != "$SELF_MTIME" ]; then
        _post "script updated — reloading (exec)"
        exec bash "$SELF"
    fi

    _MAX_DIFF=$(grep -E '^IGOR_MAX_DIFFICULTY=' "$SWITCHES_CFG" 2>/dev/null | tail -1 | cut -d= -f2)
    _NEXT_ARGS="next --worker claude"
    [ -n "$_MAX_DIFF" ] && _NEXT_ARGS="next --worker claude --max-difficulty=$_MAX_DIFF"
    NEXT=$(python3 "$QUEUE_SCRIPT" $_NEXT_ARGS 2>/dev/null)
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
                python3 "$QUEUE_SCRIPT" reset --timeout "$NEXT" 2>/dev/null && _post "timeout reset: $NEXT" || true
                break
            fi
            sleep 5
            ELAPSED=$((ELAPSED + 5))
        done
        wait "$CLAUDE_PID" 2>/dev/null || true

        unset WORKER_TICKET
        # Sloped retry: brief pause after completing a ticket before polling again.
        # Prevents hammering the queue and gives Postgres writes a moment to settle.
        sleep 20
    else
        # Gate tripped or queue empty — slow-poll (5 min).
        # No point checking again sooner — if nothing was available this cycle,
        # the queue won't change in under a minute.
        sleep 300
    fi
done
