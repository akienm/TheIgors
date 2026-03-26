# start_igor_windows.ps1
# Starts Igor using the shared Postgres DB on akiendelllinux.
# Instance determined by IGOR_INSTANCE_ID env var (default: igor_wild_windows_0001).
# Run from anywhere - paths are derived from this script's location.
# Usage: .\start_igor_windows.ps1

$repoRoot = Split-Path -Parent $MyInvocation.MyCommand.Definition
$instanceId = if ($env:IGOR_INSTANCE_ID) { $env:IGOR_INSTANCE_ID } else { "igor_wild_windows_0001" }
$venvPython = "$env:USERPROFILE\.TheIgors\venv\Scripts\python.exe"
$envFile = "$env:USERPROFILE\.TheIgors\$instanceId\.env"

# Load .env into this session
if (Test-Path $envFile) {
    Get-Content $envFile | ForEach-Object {
        if ($_ -match '^\s*([^#][^=]+)=(.*)$') {
            [System.Environment]::SetEnvironmentVariable($matches[1].Trim(), $matches[2].Trim(), 'Process')
        }
    }
} else {
    if (-not $env:IGOR_HOME_DB_URL) {
        Write-Error -Message ".env not found at $envFile and IGOR_HOME_DB_URL not set - run the bootstrap first."
        exit 1
    }
    Write-Host "No .env file found - using environment variables." -ForegroundColor Yellow
}

if (-not (Test-Path $venvPython)) {
    Write-Error -Message "venv not found at $venvPython - run the bootstrap first."
    exit 1
}

Write-Host "Starting Igor ($instanceId)..." -ForegroundColor Cyan
Set-Location "$repoRoot\wild_igor"
& $venvPython -m igor.main
# MIIFcwYJKoZIhvcNAQcCoIIFZDCCBWACAQExCzAJBgUrDgMCGgUAMGkGCisGAQQB
# gjcCAQSgWzBZMDQGCisGAQQBgjcCAR4wJgIDAQAABBAfzDtgWUsITrck0sYpfvNR
# AgEAAgEAAgEAAgEAAgEAMCEwCQYFKw4DAhoFAAQUjoHVPNV+kspFLlCXnoxh6gsl
# VLGgggMMMIIDCDCCAfCgAwIBAgIQK3nQLMsP9J9GW9CbSPCSLDANBgkqhkiG9w0B
# AQsFADAcMRowGAYDVQQDDBFBa2llbkxvY2FsU2lnbmluZzAeFw0yNjAzMTgwMzA3
# MDNaFw0yNzAzMTgwMzI3MDNaMBwxGjAYBgNVBAMMEUFraWVuTG9jYWxTaWduaW5n
# MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEArJ59QIpXz6FtJ+3bvGsk
# aCTZYFLGgSoToECMspnHsJxDWUVYGxXHY6SVx+Lh6ooHI7DwmPFvxSoITUgiIXvr
# ECxv8UhSwSKIK3ROxwrVAQ6su2FEkvn/U6+/gXHU4zwY0NvPp39P+9WtO+JgVWti
# NIKc3+8LffCukYVwDi9NV0xbXd00AYiH/vSs04EsvLFAWDg9BqWcsV01rfaJWrr7
# 4AEqhfpzpP9wVltORNS/yD3RkYZ2CzyT0O9O0OK1ouNub24ISgfnw8ipeVLDcygN
# z8TiaAIua1B23s0812pooRAIOYlkoRYt93dejNawy8AvGQcW3OfrGcBt8JrfC0wM
# hQIDAQABo0YwRDAOBgNVHQ8BAf8EBAMCB4AwEwYDVR0lBAwwCgYIKwYBBQUHAwMw
# HQYDVR0OBBYEFIv+WEkaM/p5xy/fzYTt4B8AYWyYMA0GCSqGSIb3DQEBCwUAA4IB
# AQCamCcAO46WxyGbLKhjTrLkiMnMt+/0BvZwdlxpVXiN0kbxd+TUea3atDieFAJa
# xPH86ITaMhsm+qRdGN8fNxqNo9kqyrLagxtqgMazot7lcl5E2PV9/wz9G/a/2KtQ
# c/hJbD6x13GqJIGsQhf2aS5Wierg2blWmZzqnJ4xdIBe1dQoCy8MIxxazj4HxV4w
# SDMkwE+/LPSO33RQrdHgWiHVWCN6LvZn6qQ7PO/SYolF+CADUIx0A+VfHI/iy9ze
# WeTOauFsEJrJedqb/oUTjpQl/tx04KzEc3o+zWm9dGrLs5fyaWqyZC8RP+qBc9YF
# E/Jucrb8FdsOvI9ho6k5Cz2ZMYIB0TCCAc0CAQEwMDAcMRowGAYDVQQDDBFBa2ll
# bkxvY2FsU2lnbmluZwIQK3nQLMsP9J9GW9CbSPCSLDAJBgUrDgMCGgUAoHgwGAYK
# KwYBBAGCNwIBDDEKMAigAoAAoQKAADAZBgkqhkiG9w0BCQMxDAYKKwYBBAGCNwIB
# BDAcBgorBgEEAYI3AgELMQ4wDAYKKwYBBAGCNwIBFTAjBgkqhkiG9w0BCQQxFgQU
# l7F1wP8a0Msc58VTMXWKhP+LXgkwDQYJKoZIhvcNAQEBBQAEggEAEwXZ+92Unopc
# DE39kMYumlNbN+uHcsebUd9vFxrJId1jnbDJu4nvncQrTuBC4iF81gfLEm3/H5/K
# bRiT/w/R+rU1oenPlb/dVr1G3TWy92/5GqKwaT0N/PvnO4w4d6B/IhtjkI6gbxgy
# 1bD0xqlcVzIrohKJernLqgA9AnoAgsxIgyZhKQT2YQUMDbwY7tYMf5j83mmWxRVa
# Rj9sqjk+sgywTb0S0sjaA6SWqqtXa2e5F795QyjQOTxxHWSCYRlhgPSShvUeZ9KL
# B6wwx5MGn8NZ6tENu12wUhCTtYdPGItAGbC4lIyAdR2joFAtU7CsFVA2/0vbGBVB
# R6aJSompSA==
# SIG # End signature block
