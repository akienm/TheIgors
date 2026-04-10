# bootstrap_cc.ps1 — CC setup for TheIgors (Windows)
#
# This is now a convenience wrapper around migration_003 in installer.py.
# Running igor.ps1 applies migration_003 automatically.
# Use this script only if you want to set up CC without starting Igor.
#
# Prerequisites: venv must exist (python -m venv venv && venv\Scripts\pip install -r requirements.txt)

$ErrorActionPreference = "Stop"

$RepoRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$Venv = Join-Path $RepoRoot "venv"
$Python = Join-Path $Venv "Scripts\python.exe"

Write-Host "=== TheIgors CC Bootstrap (Windows) ==="

# Check venv
if (-not (Test-Path $Python)) {
    Write-Host "ERROR: venv not found at $Venv"
    Write-Host "Run: python -m venv venv && venv\Scripts\pip install -r wild_igor\requirements.txt"
    exit 1
}

# Run migration_003 directly (no restart loop)
$script = @"
import sys, os
sys.path.insert(0, r'$RepoRoot\wild_igor\setup_assets')
os.environ.setdefault('IGOR_HOME_DB_URL', 'postgresql://igor:choose_a_password@127.0.0.1/Igor-wild-0001')
import logging
logging.basicConfig(format='[bootstrap] %(levelname)s %(message)s', level=logging.INFO, stream=sys.stderr)
from installer import migration_003, _RUNTIME_ROOT
from pathlib import Path
instance_id = os.environ.get('IGOR_INSTANCE_ID', 'Igor-wild-0001')
instance_dir = _RUNTIME_ROOT / instance_id
instance_dir.mkdir(parents=True, exist_ok=True)
migration_003(instance_dir)
"@

& $Python -c $script

Write-Host ""
Write-Host "=== Bootstrap complete ==="
Write-Host "Restart Claude Code to load MCP tools."
Write-Host "Then run /context-load to orient."
