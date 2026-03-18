@echo off
:: sign_igor_script.bat
:: Signs start_igor_windows.ps1 with the local AkienLocalSigning cert.
:: Creates the cert if it doesn't exist yet.
:: Run this after any edit to start_igor_windows.ps1, or on a fresh machine.
:: Will self-elevate to admin if needed.

:: --- Self-elevation ---
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo Requesting admin elevation...
    powershell -Command "Start-Process '%~f0' -Verb RunAs"
    exit /b
)

:: --- Run signing logic ---
powershell -ExecutionPolicy Bypass -Command "
$scriptPath = 'C:\Users\akien\OneDrive\AkiensWorkshop\dev\src\TheIgors\start_igor_windows.ps1'

# Find existing cert or create a new one
$cert = Get-ChildItem Cert:\CurrentUser\My | Where-Object { $_.Subject -eq 'CN=AkienLocalSigning' -and $_.HasPrivateKey } | Select-Object -First 1

if (-not $cert) {
    Write-Host 'Creating new self-signed cert...' -ForegroundColor Yellow
    $cert = New-SelfSignedCertificate ``
        -Subject 'CN=AkienLocalSigning' ``
        -CertStoreLocation 'Cert:\CurrentUser\My' ``
        -KeyUsage DigitalSignature ``
        -Type CodeSigningCert

    Export-Certificate -Cert $cert -FilePath `"$env:TEMP\akien_signing.cer`" | Out-Null
    Import-Certificate -FilePath `"$env:TEMP\akien_signing.cer`" -CertStoreLocation 'Cert:\CurrentUser\TrustedPublisher' | Out-Null
    Import-Certificate -FilePath `"$env:TEMP\akien_signing.cer`" -CertStoreLocation 'Cert:\CurrentUser\Root' | Out-Null
    Write-Host 'Cert created and trusted.' -ForegroundColor Green
} else {
    Write-Host 'Found existing cert.' -ForegroundColor Cyan
}

$result = Set-AuthenticodeSignature -FilePath $scriptPath -Certificate $cert
if ($result.Status -eq 'Valid') {
    Write-Host 'Script signed successfully.' -ForegroundColor Green
} else {
    Write-Host ('Signing result: ' + $result.Status) -ForegroundColor Red
}
"

pause
