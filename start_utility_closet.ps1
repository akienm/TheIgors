# start_utility_closet.ps1 -- ensure the utility closet is running (Windows).
# Idempotent: if already running + healthy, returns immediately.
# Called by: superclaude.ps1, igor.ps1, and the IgorUtilityCloset scheduled task.

$ErrorActionPreference = 'Stop'

$repoRoot    = Split-Path -Parent $MyInvocation.MyCommand.Definition
$venvPython  = "$repoRoot\venv\Scripts\python.exe"
$ucServer    = "$repoRoot\lab\claudecode\utility_closet_server.py"
$runtimeRoot = "$env:USERPROFILE\.TheIgors"
$logDir      = "$runtimeRoot\logs"
$logFile     = "$logDir\utility_closet.log"
$stdoutLog   = "$logDir\uc_stdout.log"
$stderrLog   = "$logDir\uc_stderr.log"

if (-not (Test-Path $venvPython)) {
    Write-Host "[uc] venv python missing at $venvPython - run igor.ps1 once to bootstrap" -ForegroundColor Yellow
    exit 1
}
if (-not (Test-Path $ucServer)) {
    Write-Host "[uc] utility_closet_server.py missing at $ucServer" -ForegroundColor Yellow
    exit 1
}

New-Item -ItemType Directory -Force -Path $logDir | Out-Null

function Test-UcHealthy {
    # Run --check; suppress all output including Python stderr (logging).
    # Return $true iff exit code is 0. Local ErrorActionPreference override
    # because Python writes log lines to stderr, which PS's 'Stop' policy
    # would otherwise treat as a fatal error.
    $savedEAP = $ErrorActionPreference
    $ErrorActionPreference = 'Continue'
    try {
        $null = & $venvPython $ucServer --check *>&1
        return $LASTEXITCODE -eq 0
    } finally {
        $ErrorActionPreference = $savedEAP
    }
}

# Already running?
if (Test-UcHealthy) {
    Write-Host "[uc] running" -ForegroundColor DarkGreen
    exit 0
}

# Start detached. Use python.exe (not pythonw.exe) -- pythonw.exe -WindowStyle Hidden
# loses its stdio handles via Start-Process and uvicorn's startup stalls silently.
# python.exe with RedirectStandardOutput/Error works consistently. The brief console
# flash is the trade-off; users can register the scheduled task (install_uc_autostart.ps1)
# to avoid it entirely since the task infrastructure launches headless.
Write-Host "[uc] starting..." -ForegroundColor Cyan
$proc = Start-Process `
    -FilePath $venvPython `
    -ArgumentList $ucServer `
    -WorkingDirectory $repoRoot `
    -WindowStyle Hidden `
    -PassThru `
    -RedirectStandardOutput $stdoutLog `
    -RedirectStandardError  $stderrLog

# Wait up to 10s for health
for ($i = 0; $i -lt 10; $i++) {
    Start-Sleep -Seconds 1
    if (Test-UcHealthy) {
        Write-Host "[uc] started (pid $($proc.Id))" -ForegroundColor Green
        exit 0
    }
}

Write-Host "[uc] WARNING: did not report healthy within 10s (continuing anyway)" -ForegroundColor Yellow
Write-Host "[uc] check log: $logFile" -ForegroundColor Yellow
exit 0
