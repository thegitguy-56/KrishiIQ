# KrishiIQ — Flutter SDK + mobile app setup (Windows)
$ErrorActionPreference = "Stop"

$FlutterRoot = "C:\Users\surya.gollavilli\flutter"
$FlutterBin = Join-Path $FlutterRoot "bin"
$ProjectRoot = Split-Path $PSScriptRoot -Parent
$MobileDir = Join-Path $ProjectRoot "mobile"

Write-Host "=== KrishiIQ Flutter Setup ===" -ForegroundColor Green

# 1. Install Flutter SDK if missing
if (-not (Test-Path (Join-Path $FlutterBin "flutter.bat"))) {
    Write-Host "Cloning Flutter SDK (stable)..." -ForegroundColor Yellow
    git clone https://github.com/flutter/flutter.git -b stable --depth 1 $FlutterRoot
}

$env:Path = "$FlutterBin;" + $env:Path
[Environment]::SetEnvironmentVariable("Path", "$FlutterBin;" + [Environment]::GetEnvironmentVariable("Path", "User"), "User")
Write-Host "Flutter added to user PATH: $FlutterBin" -ForegroundColor Cyan

# 2. Flutter tooling
flutter --version
flutter config --no-analytics
flutter doctor

Write-Host "`nAccept Android licenses (press 'y' for each prompt)..." -ForegroundColor Yellow
flutter doctor --android-licenses

# 3. Generate platform folders (android, windows, etc.)
Set-Location $MobileDir
if (-not (Test-Path "android")) {
    Write-Host "Creating Android / Windows platform projects..." -ForegroundColor Yellow
    flutter create . --org com.krishiiq --project-name krishiiq
}

# 4. Dependencies
flutter pub get

# 5. Patch Android cleartext for local API (dev)
$manifest = Join-Path $MobileDir "android\app\src\main\AndroidManifest.xml"
if (Test-Path $manifest) {
    $xml = Get-Content $manifest -Raw
    if ($xml -notmatch "usesCleartextTraffic") {
        $xml = $xml -replace "<application", '<application android:usesCleartextTraffic="true"'
        Set-Content $manifest $xml -NoNewline
        Write-Host "Enabled cleartext HTTP for local API (Android dev)" -ForegroundColor Cyan
    }
}

# 6. Developer Mode (symlinks for plugins)
$devMode = Get-ItemProperty -Path "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\AppModelUnlock" -Name AllowDevelopmentWithoutDevLicense -ErrorAction SilentlyContinue
if ($devMode.AllowDevelopmentWithoutDevLicense -ne 1) {
    Write-Host "`nEnable Windows Developer Mode (required for Flutter plugins):" -ForegroundColor Yellow
    Write-Host "  Settings > System > For developers > Developer Mode = On"
    Write-Host "  Or run: start ms-settings:developers"
}

Write-Host "`n=== Setup complete ===" -ForegroundColor Green
Write-Host "Flutter SDK: $FlutterRoot"
Write-Host "1. Start backend:  cd backend; python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8001"
Write-Host "2. Run app:        cd mobile; flutter run"
Write-Host "   Windows:        flutter run -d windows"
Write-Host "   Chrome:         flutter run -d chrome"
Write-Host "   Emulator API:   http://10.0.2.2:8001 (already in app_config.dart)"
Write-Host "   Physical phone: edit mobile/lib/config/app_config.dart with your PC IP"
Write-Host "3. Test login:     farmer 9000000002 / farmer123"
Write-Host "4. Android fix:    Install Android Studio cmdline-tools; run flutter doctor --android-licenses"
