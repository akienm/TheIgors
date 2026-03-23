#!/usr/bin/env bash
# bootstrap_cc.sh — Bring Claude Code to life for TheIgors on Linux
# Run from repo root: bash claudecode/bootstrap_cc.sh
#
# What this does:
#   1. Seeds CC memory files for this project
#   2. Writes .claude/settings.local.json with correct MCP paths
#
# Prerequisites: venv must exist (python3 -m venv venv && venv/bin/pip install -r requirements.txt)

set -e
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV="$REPO_ROOT/venv"
PYTHON="$VENV/bin/python"
MCP_SCRIPT="$REPO_ROOT/claudecode/igor_mcp.py"
SEED_DIR="$REPO_ROOT/claudecode/cc_memory_seed"

echo "=== TheIgors CC Bootstrap (Linux) ==="
echo "Repo: $REPO_ROOT"

# Check venv
if [ ! -f "$PYTHON" ]; then
    echo "ERROR: venv not found at $VENV"
    echo "Run: python3 -m venv venv && venv/bin/pip install -r requirements.txt"
    exit 1
fi

# Compute CC project memory path
# CC uses the project path with slashes replaced by dashes
PROJECT_KEY=$(echo "$REPO_ROOT" | sed 's|/|-|g')
MEMORY_DIR="$HOME/.claude/projects/$PROJECT_KEY/memory"
mkdir -p "$MEMORY_DIR"

# Seed memory files (don't overwrite existing — local changes take precedence)
if [ -d "$SEED_DIR" ]; then
    seeded=0
    skipped=0
    for f in "$SEED_DIR"/*.md; do
        fname=$(basename "$f")
        dest="$MEMORY_DIR/$fname"
        if [ ! -f "$dest" ]; then
            cp "$f" "$dest"
            seeded=$((seeded + 1))
        else
            skipped=$((skipped + 1))
        fi
    done
    echo "Memory: seeded=$seeded skipped=$skipped (existing files not overwritten)"
else
    echo "WARNING: memory seed dir not found at $SEED_DIR"
fi

# Write settings.local.json
SETTINGS_LOCAL="$REPO_ROOT/.claude/settings.local.json"

# Prompt for DB URL if not in env
DB_URL="${IGOR_HOME_DB_URL:-postgresql://igor:choose_a_password@127.0.0.1/igor_wild_0001}"
CC_SEND="${CC_SEND_URL:-http://localhost:8080/api/cc_send}"

cat > "$SETTINGS_LOCAL" << EOF
{
  "mcpServers": {
    "igor": {
      "command": "$PYTHON",
      "args": ["$MCP_SCRIPT"],
      "env": {
        "IGOR_HOME_DB_URL": "$DB_URL",
        "CC_SEND_URL": "$CC_SEND"
      }
    }
  }
}
EOF

echo "Written: $SETTINGS_LOCAL"
echo ""
echo "=== Bootstrap complete ==="
echo "Restart Claude Code to load MCP tools."
echo "Then run /context-load to orient."
