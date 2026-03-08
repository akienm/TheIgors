#!/usr/bin/env bash
# cc.sh — Claude Code launcher for Igor
# Sets ANTHROPIC_API_KEY from REAL_ANTHROPIC_API_KEY before invoking claude.
# Usage: cc.sh [args passed to claude]

if [ -z "$REAL_ANTHROPIC_API_KEY" ]; then
    echo "ERROR: REAL_ANTHROPIC_API_KEY is not set in the environment." >&2
    exit 1
fi

export ANTHROPIC_API_KEY="$REAL_ANTHROPIC_API_KEY"
exec claude "$@"
