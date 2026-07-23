# KrishiIQ mobile — run with Flutter on PATH
param(
    [string[]]$FlutterArgs = @("run", "-d", "windows")
)
$ErrorActionPreference = "Stop"
. "$PSScriptRoot\flutter-env.ps1"
Set-Location $PSScriptRoot
flutter pub get
flutter @FlutterArgs
