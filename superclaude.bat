@echo off
REM superclaude.bat — elevate to PowerShell and run superclaude.ps1 (D335)
REM Forwards all arguments to Claude Code via superclaude.ps1

set "SCRIPT_DIR=%~dp0"

REM Try repo-local superclaude.ps1 first, fall back to ~/bin
if exist "%SCRIPT_DIR%superclaude.ps1" (
    powershell -Command "Start-Process powershell -Verb RunAs -ArgumentList '-ExecutionPolicy Bypass -File \"%SCRIPT_DIR%superclaude.ps1\" %*'"
) else if exist "%USERPROFILE%\bin\superclaude.ps1" (
    powershell -Command "Start-Process powershell -Verb RunAs -ArgumentList '-ExecutionPolicy Bypass -File \"%USERPROFILE%\bin\superclaude.ps1\" %*'"
) else (
    echo ERROR: superclaude.ps1 not found
    exit /b 1
)
