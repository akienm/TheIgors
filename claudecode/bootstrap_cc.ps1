# bootstrap_cc.ps1 — Bring Claude Code to life for TheIgors on Windows
# Run from repo root: .\claudecode\bootstrap_cc.ps1
#
# What this does:
#   1. Seeds CC memory files for this project
#   2. Writes .claude\settings.local.json with correct MCP paths
#
# Prerequisites: venv must exist (python -m venv venv && venv\Scripts\pip install -r requirements.txt)

$ErrorActionPreference = "Stop"

$RepoRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$Venv = Join-Path $RepoRoot "venv"
$Python = Join-Path $Venv "Scripts\python.exe"
$McpScript = Join-Path $RepoRoot "claudecode\igor_mcp.py"
$SeedDir = Join-Path $RepoRoot "claudecode\cc_memory_seed"

Write-Host "=== TheIgors CC Bootstrap (Windows) ==="
Write-Host "Repo: $RepoRoot"

# Check venv
if (-not (Test-Path $Python)) {
    Write-Host "ERROR: venv not found at $Venv"
    Write-Host "Run: python -m venv venv && venv\Scripts\pip install -r requirements.txt"
    exit 1
}

# Compute CC project memory path
# CC uses the project path with separators replaced by dashes
# e.g. C:\automation\local\TheIgors -> -C-automation-local-TheIgors
$ProjectKey = $RepoRoot -replace ":", "" -replace "\\", "-" -replace "/", "-"
if (-not $ProjectKey.StartsWith("-")) { $ProjectKey = "-$ProjectKey" }
$MemoryDir = Join-Path $env:APPDATA "Claude\projects\$ProjectKey\memory"
New-Item -ItemType Directory -Force -Path $MemoryDir | Out-Null

# Seed memory files (don't overwrite existing)
if (Test-Path $SeedDir) {
    $seeded = 0; $skipped = 0
    Get-ChildItem "$SeedDir\*.md" | ForEach-Object {
        $dest = Join-Path $MemoryDir $_.Name
        if (-not (Test-Path $dest)) {
            Copy-Item $_.FullName $dest
            $seeded++
        } else {
            $skipped++
        }
    }
    Write-Host "Memory: seeded=$seeded skipped=$skipped (existing files not overwritten)"
} else {
    Write-Host "WARNING: memory seed dir not found at $SeedDir"
}

# DB URL and CC send URL (override via env vars if needed)
$DbUrl = if ($env:IGOR_HOME_DB_URL) { $env:IGOR_HOME_DB_URL } else { "postgresql://igor:choose_a_password@localhost/igor_wild_0001" }
$CcSend = if ($env:CC_SEND_URL) { $env:CC_SEND_URL } else { "http://localhost:8080/api/cc_send" }

# Write settings.local.json
$SettingsLocal = Join-Path $RepoRoot ".claude\settings.local.json"
$config = [ordered]@{
    mcpServers = [ordered]@{
        igor = [ordered]@{
            command = $Python
            args    = @($McpScript)
            env     = [ordered]@{
                IGOR_HOME_DB_URL = $DbUrl
                CC_SEND_URL      = $CcSend
            }
        }
    }
}
$config | ConvertTo-Json -Depth 5 | Set-Content -Encoding UTF8 $SettingsLocal

Write-Host "Written: $SettingsLocal"
Write-Host ""
Write-Host "=== Bootstrap complete ==="
Write-Host "Restart Claude Code to load MCP tools."
Write-Host "Then run /context-load to orient."
