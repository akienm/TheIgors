#Requires -RunAsAdministrator
<#
.SYNOPSIS
    Igor Windows installer - experimental
.DESCRIPTION
    Idempotent bootstrap for a new Igor Windows node.
    - Installs git, Python 3.12, Ollama if missing
    - Clones / updates repo to C:\automation\local\TheIgors
    - Creates venv + installs requirements
    - Creates instance dir + .env
    - Signs launch scripts with local cert
    - Registers IgorStartup scheduled task
    - Wires up 'igor' command (PATH + PS profile)

    Required system env vars (prompt if absent):
        ANTHROPIC_API_KEY, IGOR_DB_URL, IGOR_INSTANCE_ID
#>

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$RepoRoot    = "C:\automation\local\TheIgors"
$RuntimeRoot = "$env:USERPROFILE\.TheIgors"
$VenvPython  = "$RuntimeRoot\venv\Scripts\python.exe"

# Helpers
function Write-Step($msg) { Write-Host "`n==> $msg" -ForegroundColor Cyan }
function Write-OK($msg)   { Write-Host "    OK  $msg" -ForegroundColor Green }
function Write-Warn($msg) { Write-Host "    WARN $msg" -ForegroundColor Yellow }
function Write-Fail($msg) { Write-Host "    FAIL $msg" -ForegroundColor Red }

function Refresh-Path {
    $env:PATH = [System.Environment]::GetEnvironmentVariable("PATH","Machine") + ";" +
                [System.Environment]::GetEnvironmentVariable("PATH","User")
}

function Require-EnvVar($name, $prompt) {
    $val = [System.Environment]::GetEnvironmentVariable($name, "Machine")
    if (-not $val) { $val = [System.Environment]::GetEnvironmentVariable($name, "User") }
    if (-not $val) { $val = [System.Environment]::GetEnvironmentVariable($name, "Process") }
    if ($val) { Write-OK "$name already set"; return $val }
    $val = Read-Host $prompt
    if (-not $val) { throw "$name is required - aborting" }
    [System.Environment]::SetEnvironmentVariable($name, $val, "Machine")
    [System.Environment]::SetEnvironmentVariable($name, $val, "Process")
    Write-OK "$name set"
    return $val
}

Write-Host "`n================================================" -ForegroundColor Cyan
Write-Host "  Igor Windows Installer (experimental)" -ForegroundColor Cyan
Write-Host "================================================`n" -ForegroundColor Cyan

# Step 1: git
Write-Step "git"
if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    Write-Warn "git not found - installing via winget"
    winget install --id Git.Git -e --source winget --accept-package-agreements --accept-source-agreements
    Refresh-Path
}
if (Get-Command git -ErrorAction SilentlyContinue) {
    Write-OK (git --version)
} else {
    Write-Fail "git still not found after install - open a new elevated shell and re-run"
    exit 1
}

# Step 2: Python 3.12
Write-Step "Python 3.12"
$pyOk = $false
try { py -3.12 --version 2>&1 | Out-Null; $pyOk = $true } catch {}
if (-not $pyOk) {
    Write-Warn "Python 3.12 not found - installing via winget"
    winget install --id Python.Python.3.12 -e --source winget --accept-package-agreements --accept-source-agreements
    Refresh-Path
    try { py -3.12 --version 2>&1 | Out-Null; $pyOk = $true } catch {}
}
if ($pyOk) {
    Write-OK (py -3.12 --version 2>&1)
} else {
    Write-Fail "Python 3.12 still not found - open a new elevated shell and re-run"
    exit 1
}

# Step 3: Ollama
Write-Step "Ollama"
if (-not (Get-Command ollama -ErrorAction SilentlyContinue)) {
    Write-Warn "Ollama not found - installing via winget"
    winget install --id Ollama.Ollama -e --source winget --accept-package-agreements --accept-source-agreements
    Refresh-Path
    Start-Sleep -Seconds 3
}
if (Get-Command ollama -ErrorAction SilentlyContinue) {
    Write-OK "Ollama present"
    $ollamaRunning = $false
    try {
        Invoke-WebRequest -Uri "http://localhost:11434" -UseBasicParsing -TimeoutSec 3 -ErrorAction Stop | Out-Null
        $ollamaRunning = $true
    } catch {}
    if (-not $ollamaRunning) {
        Write-Warn "Ollama server not running - starting in background"
        Start-Process "ollama" -ArgumentList "serve" -WindowStyle Hidden
        Start-Sleep -Seconds 5
    }
    $modelList = (ollama list 2>&1) -join ""
    if ($modelList -notmatch "qwen2\.5:7b") {
        Write-Warn "Pulling qwen2.5:7b - this may take several minutes on first run"
        ollama pull qwen2.5:7b
        Write-OK "qwen2.5:7b ready"
    } else {
        Write-OK "qwen2.5:7b already present"
    }
} else {
    Write-Warn "Ollama install may need a shell restart - skipping model pull for now"
}

# Step 4: Repo
Write-Step "Repo at $RepoRoot"
if (-not (Test-Path "$RepoRoot\.git")) {
    $parent = Split-Path $RepoRoot -Parent
    if (-not (Test-Path $parent)) { New-Item -ItemType Directory -Force -Path $parent | Out-Null }
    git clone https://github.com/akienm/TheIgors.git $RepoRoot
    Write-OK "Cloned"
} else {
    Write-OK "Repo exists - pulling"
    git -C $RepoRoot pull --ff-only
}

# Step 5: Required environment variables
Write-Step "Environment variables"
$anthropicKey = Require-EnvVar "ANTHROPIC_API_KEY" "Anthropic API key"
$dbUrl        = Require-EnvVar "IGOR_DB_URL"       "Igor DB URL (postgres connection string)"
$instanceId   = Require-EnvVar "IGOR_INSTANCE_ID"  "Instance ID (e.g. igor_wild_windows_0001)"

# Step 6: Virtual environment
Write-Step "Venv at $RuntimeRoot\venv"
if (-not (Test-Path $VenvPython)) {
    py -3.12 -m venv "$RuntimeRoot\venv"
    Write-OK "Venv created"
} else {
    Write-OK "Venv exists"
}
Write-Warn "Installing requirements (may take a minute)..."
& $VenvPython -m pip install --upgrade pip --quiet
& $VenvPython -m pip install -r "$RepoRoot\requirements.txt"
Write-OK "Dependencies installed"

# Step 7: Instance directory + .env
Write-Step "Instance dir: $RuntimeRoot\$instanceId"
$instanceDir = "$RuntimeRoot\$instanceId"
New-Item -ItemType Directory -Force -Path $instanceDir | Out-Null

$envFile = "$instanceDir\.env"
if (-not (Test-Path $envFile)) {
    $envContent = @(
        "IGOR_RUNTIME_ROOT=$RuntimeRoot",
        "IGOR_INSTANCE_ID=$instanceId",
        "IGOR_WEB_PORT=8080",
        "IGOR_SELF_EDIT_ENABLED=false",
        "IGOR_TIER5_ENABLED=false",
        "IGOR_ARBITER_ENABLED=false",
        "",
        "# Models",
        "OLLAMA_LOCAL_MODEL=qwen2.5:7b",
        "IGOR_NE_LOCAL_MODEL=qwen2.5:7b",
        "IGOR_WINNOW_LOCAL_MODEL=qwen2.5:7b",
        "OPENROUTER_WINNOW_MODEL=qwen/qwen2.5-7b-instruct",
        "OPENROUTER_CHEAP_MODEL=openai/gpt-4o-mini",
        "OPENROUTER_DEFAULT_MODEL=anthropic/claude-haiku-4.5",
        "OPENROUTER_INTERACTIVE_MODEL=anthropic/claude-sonnet-4.6",
        "IGOR_CLOUD_TRAINING_ENABLED=true",
        "IGOR_TWO_PHASE_CALLS=true",
        "IGOR_NPASS_REPLY=true",
        "IGOR_CONTEXT_WINNOW=true",
        "IGOR_READING_EXTRACT=true",
        "IGOR_HABIT_EXTRACT=true"
    )
    $envContent | Out-File -FilePath $envFile -Encoding ASCII
    Write-OK ".env created"
} else {
    Write-OK ".env already exists - not overwriting"
}

# Step 8: Sign launch scripts
# Done inline rather than calling sign_igor_script.ps1 (that script has OneDrive path hardcoded)
Write-Step "Signing launch scripts"

$cert = Get-ChildItem Cert:\CurrentUser\My |
    Where-Object { $_.Subject -eq 'CN=AkienLocalSigning' -and $_.HasPrivateKey } |
    Select-Object -First 1

if (-not $cert) {
    Write-Warn "No AkienLocalSigning cert found - creating"
    $cert = New-SelfSignedCertificate `
        -Subject 'CN=AkienLocalSigning' `
        -CertStoreLocation 'Cert:\CurrentUser\My' `
        -KeyUsage DigitalSignature `
        -Type CodeSigningCert
    Export-Certificate -Cert $cert -FilePath "$env:TEMP\akien_signing.cer" | Out-Null
    Import-Certificate -FilePath "$env:TEMP\akien_signing.cer" -CertStoreLocation 'Cert:\CurrentUser\TrustedPublisher' | Out-Null
    Import-Certificate -FilePath "$env:TEMP\akien_signing.cer" -CertStoreLocation 'Cert:\CurrentUser\Root' | Out-Null
    Write-OK "Cert created and trusted"
} else {
    Write-OK "Existing AkienLocalSigning cert found"
}

foreach ($script in @("igor_loop.ps1", "start_igor_windows.ps1")) {
    $scriptPath = "$RepoRoot\$script"
    if (-not (Test-Path $scriptPath)) { Write-Warn "$script not found - skipping"; continue }
    $result = Set-AuthenticodeSignature -FilePath $scriptPath -Certificate $cert
    if ($result.Status -eq 'Valid') {
        Write-OK "Signed: $script"
    } else {
        Write-Fail ("Signing failed for " + $script + ": " + $result.Status)
    }
}

# Step 9: Scheduled task
Write-Step "Scheduled task: IgorStartup"
$loopScript = "$RepoRoot\igor_loop.ps1"
$action   = New-ScheduledTaskAction -Execute "powershell.exe" `
                -Argument ("-WindowStyle Normal -ExecutionPolicy Bypass -File `"" + $loopScript + "`"")
$trigger  = New-ScheduledTaskTrigger -AtLogOn
$settings = New-ScheduledTaskSettingsSet `
                -ExecutionTimeLimit (New-TimeSpan -Hours 0) `
                -RestartCount 3 `
                -RestartInterval (New-TimeSpan -Minutes 1)
Register-ScheduledTask -TaskName "IgorStartup" -Action $action -Trigger $trigger `
    -Settings $settings -RunLevel Highest -Force | Out-Null
Write-OK "IgorStartup task registered (runs at login, elevated)"

# Step 10: PATH + 'igor' in PowerShell profile
Write-Step "PATH + PowerShell igor function"

$machinePath = [System.Environment]::GetEnvironmentVariable("PATH", "Machine")
if ($machinePath -notlike "*$RepoRoot*") {
    [System.Environment]::SetEnvironmentVariable("PATH", "$machinePath;$RepoRoot", "Machine")
    Write-OK "Repo root added to machine PATH (effective in new shells)"
} else {
    Write-OK "Repo root already in PATH"
}

$profilePath = $PROFILE.CurrentUserAllHosts
$profileDir  = Split-Path $profilePath -Parent
if (-not (Test-Path $profileDir)) { New-Item -ItemType Directory -Force -Path $profileDir | Out-Null }
if (-not (Test-Path $profilePath)) { New-Item -ItemType File -Force -Path $profilePath | Out-Null }

$existing = Get-Content $profilePath -Raw -ErrorAction SilentlyContinue
if ($existing -notlike "*function igor*") {
    $igorFunc = "`n# Igor launcher - added by install_igor.ps1`nfunction igor { & `"$loopScript`" @args }`n"
    Add-Content -Path $profilePath -Value $igorFunc
    Write-OK "igor function added to PS profile ($profilePath)"
} else {
    Write-OK "igor function already in PS profile"
}

# Done
Write-Host "`n================================================" -ForegroundColor Green
Write-Host "  Install complete: $instanceId" -ForegroundColor Green
Write-Host "================================================" -ForegroundColor Green
Write-Host ""
Write-Host "  Next steps:"
Write-Host "  1. Open a NEW elevated PowerShell"
Write-Host "  2. Type: igor"
Write-Host "     (or run the IgorStartup scheduled task)"
Write-Host ""
Write-Host "  Logs: $RuntimeRoot\logs\"
Write-Host "  .env: $instanceDir\.env"
Write-Host ""
