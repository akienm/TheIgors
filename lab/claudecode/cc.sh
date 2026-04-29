#!/usr/bin/env bash
# cc.sh — Claude Code launcher for Igor
# CC uses Claude Max auth — no API key required.
# Usage: cc.sh [args passed to claude]

exec claude --dangerously-skip-permissions "$@"
