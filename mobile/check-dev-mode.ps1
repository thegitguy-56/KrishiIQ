# Check if Windows Developer Mode is enabled (required for Flutter plugins)
$regPath = "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\AppModelUnlock"
$enabled = $false
if (Test-Path $regPath) {
    $v = Get-ItemProperty -Path $regPath -Name AllowDevelopmentWithoutDevLicense -ErrorAction SilentlyContinue
    $enabled = ($v.AllowDevelopmentWithoutDevLicense -eq 1)
}
if ($enabled) {
    Write-Host "Developer Mode: ON — you can run: flutter run -d windows" -ForegroundColor Green
} else {
    Write-Host "Developer Mode: OFF — Flutter cannot build until this is enabled." -ForegroundColor Red
    Write-Host ""
    Write-Host "Fix (takes ~30 seconds):" -ForegroundColor Yellow
    Write-Host "  1. Press Win+I (Settings)"
    Write-Host "  2. System  ->  For developers  (or Privacy & security -> For developers)"
    Write-Host "  3. Turn ON: Developer Mode"
    Write-Host "  4. Confirm the dialog"
    Write-Host "  5. Close this terminal, open a NEW one"
    Write-Host "  6. cd mobile; . .\flutter-env.ps1; flutter run -d windows"
    Write-Host ""
    Write-Host "Opening settings now..."
    Start-Process "ms-settings:developers"
}
