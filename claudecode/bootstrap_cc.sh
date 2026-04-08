#!/usr/bin/env bash
# bootstrap_cc.sh — CC setup for TheIgors (Linux/macOS)
#
# This is now a convenience wrapper around migration_003 in installer.py.
# Running `igor` or `igor.ps1` applies migration_003 automatically.
# Use this script only if you want to set up CC without starting Igor.
#
# Prerequisites: venv must exist (python3 -m venv venv && venv/bin/pip install -r requirements.txt)

set -e
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV="$REPO_ROOT/venv"
PYTHON="$VENV/bin/python"
INSTALLER="$REPO_ROOT/wild_igor/setup_assets/installer.py"

echo "=== TheIgors CC Bootstrap (Linux) ==="

# Check venv
if [ ! -f "$PYTHON" ]; then
    echo "ERROR: venv not found at $VENV"
    echo "Run: python3 -m venv venv && venv/bin/pip install -r wild_igor/requirements.txt"
    exit 1
fi

# Run only migration_003 via the installer's migration system.
# We import and call migration_003 directly to avoid starting the restart loop.
"$PYTHON" -c "
import sys, os
sys.path.insert(0, '$REPO_ROOT/wild_igor/setup_assets')
os.environ.setdefault('IGOR_HOME_DB_URL', 'postgresql://igor:choose_a_password@127.0.0.1/Igor-wild-0001')
import logging
logging.basicConfig(format='[bootstrap] %(levelname)s %(message)s', level=logging.INFO, stream=sys.stderr)
from installer import migration_003, _RUNTIME_ROOT
from pathlib import Path
instance_id = os.environ.get('IGOR_INSTANCE_ID', 'Igor-wild-0001')
instance_dir = _RUNTIME_ROOT / instance_id
instance_dir.mkdir(parents=True, exist_ok=True)
migration_003(instance_dir)
"

echo ""
echo "=== Bootstrap complete ==="
echo "Restart Claude Code to load MCP tools."
echo "Then run /context-load to orient."
