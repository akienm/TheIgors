@echo off
rem igor.bat — entry point: type "igor" to start Igor on Windows
rem Add the TheIgors repo root to your PATH to use from anywhere.
powershell.exe -ExecutionPolicy Bypass -File "%~dp0igor_loop.ps1" %*
