# install_uc_autostart.ps1 -- register a scheduled task that starts the
# utility closet at user logon. Run ONCE per machine (elevated).
#
# The task runs start_utility_closet.ps1, which is idempotent: if the UC
# is already running it no-ops.
#
# To remove: Unregister-ScheduledTask -TaskName "IgorUtilityCloset" -Confirm:$false

$ErrorActionPreference = 'Stop'

$repoRoot  = Split-Path -Parent $MyInvocation.MyCommand.Definition
$script    = "$repoRoot\start_utility_closet.ps1"
$taskName  = 'IgorUtilityCloset'

if (-not (Test-Path $script)) {
    Write-Host "ERROR: $script not found" -ForegroundColor Red
    exit 1
}

$action = New-ScheduledTaskAction `
    -Execute 'powershell.exe' `
    -Argument "-WindowStyle Hidden -ExecutionPolicy Bypass -File `"$script`""

$trigger = New-ScheduledTaskTrigger -AtLogOn -User $env:USERNAME

$settings = New-ScheduledTaskSettingsSet `
    -ExecutionTimeLimit (New-TimeSpan -Hours 0) `
    -RestartCount 3 `
    -RestartInterval (New-TimeSpan -Minutes 1) `
    -StartWhenAvailable

Register-ScheduledTask `
    -TaskName $taskName `
    -Action $action `
    -Trigger $trigger `
    -Settings $settings `
    -RunLevel Highest `
    -Force | Out-Null

Write-Host "Scheduled task '$taskName' registered - UC will launch at next logon." -ForegroundColor Green
Write-Host "Starting UC now so you don't have to log out..." -ForegroundColor Cyan
& $script
