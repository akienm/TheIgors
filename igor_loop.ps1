# igor_loop.ps1 — Igor launcher with git-pull-and-restart loop (Windows)
# Equivalent to the Linux `igor` bash wrapper.
# Signed by sign_igor_script.ps1 — do not edit without re-signing.
#
# Usage:
#   .\igor_loop.ps1                     # start with default instance
#   igor                                # if igor.bat is in PATH

$repoRoot = Split-Path -Parent $MyInvocation.MyCommand.Definition

# ── Discover instance ───────────────────────────────────────────────────────
$runtimeRoot = if ($env:IGOR_RUNTIME_ROOT) { $env:IGOR_RUNTIME_ROOT } else { "$env:USERPROFILE\.TheIgors" }
$instanceId  = if ($env:IGOR_INSTANCE_ID)  { $env:IGOR_INSTANCE_ID }  else {
    $found = Get-ChildItem "$runtimeRoot" -Recurse -Filter ".env" -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($found) { $found.Directory.Name } else { "igor_wild_windows_0001" }
}

$envFile    = "$runtimeRoot\$instanceId\.env"
$venvPython = "$runtimeRoot\venv\Scripts\python.exe"

if (-not (Test-Path $envFile)) {
    Write-Error ".env not found at $envFile — run the bootstrap first."
    exit 1
}
if (-not (Test-Path $venvPython)) {
    Write-Error "venv not found at $venvPython — run the bootstrap first."
    exit 1
}

# ── Restart loop ────────────────────────────────────────────────────────────
# Exit code 42 = restart requested (mirrors Linux igor bash wrapper).
# Any other code = clean stop.
$exitCode = 0
do {
    # Pull latest code before each run
    Write-Host "[igor_loop] git pull..." -ForegroundColor DarkCyan
    git -C $repoRoot pull --ff-only 2>&1

    # Load .env for this run (re-read on every restart so changes take effect)
    Get-Content $envFile | ForEach-Object {
        if ($_ -match '^\s*([^#=][^=]*)=(.*)$') {
            $k = $matches[1].Trim()
            $v = $matches[2].Trim().Trim('"').Trim("'")
            [System.Environment]::SetEnvironmentVariable($k, $v, 'Process')
        }
    }

    Write-Host "[igor_loop] Starting Igor ($instanceId)..." -ForegroundColor Cyan
    Set-Location "$repoRoot\wild_igor"
    & $venvPython -m igor.main
    $exitCode = $LASTEXITCODE

    if ($exitCode -eq 42) {
        Write-Host "[igor_loop] Restarting (re-reading .env + pulling latest)..." -ForegroundColor Cyan
    } else {
        Write-Host "[igor_loop] Igor exited (code $exitCode)." -ForegroundColor Yellow
    }
} while ($exitCode -eq 42)
