# Load Flutter into this PowerShell session (run: . .\flutter-env.ps1)
$FlutterBin = "C:\Users\surya.gollavilli\flutter\bin"
if (-not (Test-Path "$FlutterBin\flutter.bat")) {
    Write-Error "Flutter not found at $FlutterBin. Run ..\scripts\setup-flutter.ps1 first."
    exit 1
}
# Reload PATH from registry (fixes terminals opened before PATH was set)
$env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" +
            [System.Environment]::GetEnvironmentVariable("Path", "User")
if ($env:Path -notlike "*$FlutterBin*") {
    $env:Path = "$FlutterBin;" + $env:Path
}
$AndroidSdk = "$env:LOCALAPPDATA\Android\Sdk"
if (Test-Path $AndroidSdk) {
    $env:ANDROID_HOME = $AndroidSdk
    $env:Path = "$AndroidSdk\platform-tools;$env:Path"
}
Write-Host "Flutter ready: $(flutter --version 2>&1 | Select-Object -First 1)" -ForegroundColor Green
