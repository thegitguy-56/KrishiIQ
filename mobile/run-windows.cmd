@echo off
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0check-dev-mode.ps1"
call "%~dp0flutter.cmd" pub get
call "%~dp0flutter.cmd" run -d windows
pause
