# igor.ps1 — minimal Igor launcher (D321, Windows).
# Equivalent to the Linux `igor` bash wrapper.
# Signed by sign_igor_script.ps1 — do not edit without re-signing.
#
# Usage:
#   .\igor.ps1                     # start with default instance
#   igor                           # if igor.bat is in PATH
#
# This script's only job: find Python + ensure venv exists, then hand off
# to wild_igor\setup_assets\installer.py (platform-smart Python).
# All restart logic, migration, and crash recovery live in installer.py.

$repoRoot   = Split-Path -Parent $MyInvocation.MyCommand.Definition
$venvPython = "$repoRoot\venv\Scripts\python.exe"
$installer  = "$repoRoot\wild_igor\setup_assets\installer.py"
$requirements = "$repoRoot\wild_igor\requirements.txt"

if (-not (Test-Path $venvPython)) {
    Write-Host "[igor] Bootstrapping venv (first run)..." -ForegroundColor Cyan
    python -m venv "$repoRoot\venv"
    & "$repoRoot\venv\Scripts\pip.exe" install --upgrade pip -q
    & "$repoRoot\venv\Scripts\pip.exe" install -r $requirements -q
    Write-Host "[igor] venv ready." -ForegroundColor Green
}

$env:PYTHONUTF8 = '1'
& $venvPython $installer @args
