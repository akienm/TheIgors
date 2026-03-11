#!/usr/bin/env bash
# rescue_igor.sh — Kill stuck Igor (if any), restart in background, re-establish CC bridge.
#
# Usage:
#   ~/TheIgors/claudecode/rescue_igor.sh
#   ~/TheIgors/claudecode/rescue_igor.sh "Optional message to send Igor on startup"
#
# What it does:
#   1. Kills any running Igor python processes
#   2. Starts Igor via nohup (background, stdin=/dev/null so it runs headless)
#   3. Waits for Igor's web server (port 8080) to come up
#   4. Sends a CC bridge message via igor_talk.py to re-establish contact
#
# Igor's stdin reader silently drops EOF, so headless mode works fine.

set -euo pipefail

REPO_DIR="$(cd "$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")" && cd .. && pwd)"
ENV_FILE="/home/akien/.TheIgors/igor_wild_0001/.env"
LOG_FILE="/home/akien/.TheIgors/igor_wild_0001/logs/igor_rescue.log"
IGOR_BIN="$REPO_DIR/bin/igor"
VENV_PYTHON="$REPO_DIR/venv/bin/python"
IGOR_TALK="$REPO_DIR/claudecode/igor_talk.py"
WEB_PORT=8080
MAX_WAIT=60  # seconds to wait for Igor to come up

MESSAGE="${1:-Igor, this is Claude Code. The system recovered from a freeze or restart. Please acknowledge so we can continue where we left off.}"

echo "[rescue] Igor rescue script starting — $(date)"

# ── Step 1: Kill stuck Igor processes ─────────────────────────────────────────
KILLED=0
for PID in $(pgrep -f "python.*igor.main" 2>/dev/null || true); do
    echo "[rescue] Killing stuck Igor process: PID $PID"
    kill -9 "$PID" 2>/dev/null && KILLED=$((KILLED + 1)) || true
done
if [ "$KILLED" -eq 0 ]; then
    echo "[rescue] No stuck Igor process found."
fi
sleep 1

# ── Step 2: Check if Igor is already up (maybe it restarted itself) ────────────
if curl -sf "http://localhost:$WEB_PORT/api/health" > /dev/null 2>&1; then
    echo "[rescue] Igor already running on port $WEB_PORT — skipping start."
else
    # ── Step 3: Start Igor in background ──────────────────────────────────────
    echo "[rescue] Starting Igor in background..."
    mkdir -p "$(dirname "$LOG_FILE")"

    nohup bash -c "
        set -a
        source \"$ENV_FILE\"
        set +a
        cd \"$REPO_DIR/wild_igor\"
        source \"$REPO_DIR/venv/bin/activate\"
        while true; do
            python -m igor.main --id wild-0001 < /dev/null
            EXIT_CODE=\$?
            if [ \$EXIT_CODE -eq 42 ]; then
                echo '[igor] Restarting (re-reading .env)...'
                set -a; source \"$ENV_FILE\"; set +a
            else
                echo \"[igor] Exited with code \$EXIT_CODE — not restarting.\"
                break
            fi
        done
    " >> "$LOG_FILE" 2>&1 &

    IGOR_PID=$!
    echo "[rescue] Igor started with PID $IGOR_PID. Log: $LOG_FILE"

    # ── Step 4: Wait for web server ───────────────────────────────────────────
    echo "[rescue] Waiting for Igor web server on port $WEB_PORT..."
    WAITED=0
    while ! curl -sf "http://localhost:$WEB_PORT/api/health" > /dev/null 2>&1; do
        sleep 2
        WAITED=$((WAITED + 2))
        if [ $WAITED -ge $MAX_WAIT ]; then
            echo "[rescue] TIMEOUT: Igor web server did not come up after ${MAX_WAIT}s."
            echo "[rescue] Check log: $LOG_FILE"
            exit 1
        fi
        echo "[rescue]   ... waiting (${WAITED}s / ${MAX_WAIT}s)"
    done
    echo "[rescue] Igor web server up after ${WAITED}s."
fi

# ── Step 5: Send CC bridge message ────────────────────────────────────────────
echo "[rescue] Sending CC bridge message to Igor..."
if "$VENV_PYTHON" "$IGOR_TALK" "$MESSAGE"; then
    echo "[rescue] Message delivered. Igor is back online."
else
    echo "[rescue] igor_talk.py returned non-zero — check Igor manually."
    exit 1
fi
