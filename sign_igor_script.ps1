# sign_igor_script.ps1
# Signs start_igor_windows.ps1 and igor.ps1 with the local AkienLocalSigning cert.
# Creates the cert if it doesn't exist yet.
# Run this after any edit to either script, or on a fresh machine.
# Will self-elevate to admin if needed.

if (-not ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Start-Process powershell -Verb RunAs -ArgumentList "-ExecutionPolicy Bypass -File `"$PSCommandPath`""
    exit
}

$repoRoot = "$env:USERPROFILE\OneDrive\AkiensWorkshop\dev\src\TheIgors"
$scriptsToSign = @(
    "$repoRoot\start_igor_windows.ps1",
    "$repoRoot\igor.ps1"
)

$cert = Get-ChildItem Cert:\CurrentUser\My |
    Where-Object { $_.Subject -eq 'CN=AkienLocalSigning' -and $_.HasPrivateKey } |
    Select-Object -First 1

if (-not $cert) {
    Write-Host 'Creating new self-signed cert...' -ForegroundColor Yellow
    $cert = New-SelfSignedCertificate `
        -Subject 'CN=AkienLocalSigning' `
        -CertStoreLocation 'Cert:\CurrentUser\My' `
        -KeyUsage DigitalSignature `
        -Type CodeSigningCert
    Export-Certificate -Cert $cert -FilePath "$env:TEMP\akien_signing.cer" | Out-Null
    Import-Certificate -FilePath "$env:TEMP\akien_signing.cer" -CertStoreLocation 'Cert:\CurrentUser\TrustedPublisher' | Out-Null
    Import-Certificate -FilePath "$env:TEMP\akien_signing.cer" -CertStoreLocation 'Cert:\CurrentUser\Root' | Out-Null
    Write-Host 'Cert created and trusted.' -ForegroundColor Green
} else {
    Write-Host 'Found existing cert.' -ForegroundColor Cyan
}

foreach ($scriptPath in $scriptsToSign) {
    if (-not (Test-Path $scriptPath)) {
        Write-Host "SKIP (not found): $scriptPath" -ForegroundColor Yellow
        continue
    }
    $result = Set-AuthenticodeSignature -FilePath $scriptPath -Certificate $cert
    if ($result.Status -eq 'Valid') {
        Write-Host "Signed: $(Split-Path -Leaf $scriptPath)" -ForegroundColor Green
    } else {
        Write-Host ("Signing failed for $(Split-Path -Leaf $scriptPath): " + $result.Status) -ForegroundColor Red
    }
}

Read-Host 'Press Enter to close'
