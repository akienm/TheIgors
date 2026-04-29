#!/usr/bin/env bash
# hot_cc.sh — Igor's persistent hot Claude Code reasoning session.
#
# Maintains a warm CC session with codebase context loaded.
# On every escalation, CC answers AND deposits graph nodes via cc_deposit.py.
# Session survives across Igor restarts; resets after 24h or on --reset.
#
# Usage:
#   hot_cc.sh "question or task for CC"
#   hot_cc.sh --reset        # force new session (e.g. after major code changes)
#   hot_cc.sh --status       # show current session age and ID

set -euo pipefail

# CC uses Claude Max auth — no API key required.

SESSION_FILE="$HOME/.TheIgors/Igor-wild-0001/cc_session_id"
SESSION_MAX_AGE=86400   # 24 hours in seconds
REPO="$HOME/TheIgors"
INIT_PROMPT_FILE="$REPO/claudecode/hot_cc_init.md"

# ── Helpers ──────────────────────────────────────────────────────────────────

session_age_seconds() {
    if [ -f "$SESSION_FILE" ]; then
        echo $(( $(date +%s) - $(stat -c %Y "$SESSION_FILE") ))
    else
        echo 99999999
    fi
}

session_is_fresh() {
    [ -f "$SESSION_FILE" ] && [ "$(session_age_seconds)" -lt "$SESSION_MAX_AGE" ]
}

# ── Commands ─────────────────────────────────────────────────────────────────

if [ "${1:-}" = "--reset" ]; then
    rm -f "$SESSION_FILE"
    echo "Hot CC session reset. Next call will start fresh."
    exit 0
fi

if [ "${1:-}" = "--status" ]; then
    if session_is_fresh; then
        AGE=$(session_age_seconds)
        ID=$(cat "$SESSION_FILE")
        echo "Session active: ${ID} (${AGE}s old, max ${SESSION_MAX_AGE}s)"
    else
        echo "No active session (will warm on next call)."
    fi
    exit 0
fi

if [ $# -eq 0 ]; then
    echo "Usage: hot_cc.sh \"question for CC\"" >&2
    echo "       hot_cc.sh --reset | --status" >&2
    exit 1
fi

PROMPT="$1"

# ── Session management ────────────────────────────────────────────────────────

cd "$REPO"

if ! session_is_fresh; then
    # Cold start: send init prompt, store session ID
    echo "[hot_cc] Warming session..." >&2
    INIT_RESULT=$(claude --dangerously-skip-permissions \
        --output-format json \
        -p "$(cat "$INIT_PROMPT_FILE")" 2>/dev/null)

    NEW_ID=$(echo "$INIT_RESULT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('session_id',''))" 2>/dev/null || true)
    if [ -n "$NEW_ID" ] && [ "$NEW_ID" != "null" ]; then
        echo "$NEW_ID" > "$SESSION_FILE"
        echo "[hot_cc] Session started: $NEW_ID" >&2
    else
        # jq unavailable or unexpected format — fall back to plain cc.sh
        echo "[hot_cc] Warning: could not capture session ID; falling back to stateless call." >&2
        exec "$REPO/claudecode/cc.sh" -p "$PROMPT"
    fi
fi

SESSION_ID=$(cat "$SESSION_FILE")

# ── Send the actual question ──────────────────────────────────────────────────

RESULT=$(claude --dangerously-skip-permissions \
    --resume "$SESSION_ID" \
    --output-format json \
    -p "$PROMPT" 2>/dev/null)

# Update session ID (may rotate after each turn)
NEW_ID=$(echo "$RESULT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('session_id',''))" 2>/dev/null || true)
if [ -n "$NEW_ID" ] && [ "$NEW_ID" != "null" ]; then
    echo "$NEW_ID" > "$SESSION_FILE"
fi

# Print the answer
echo "$RESULT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('result','(no result)'))" 2>/dev/null \
    || echo "$RESULT"
