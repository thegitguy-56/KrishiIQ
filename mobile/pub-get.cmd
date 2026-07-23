@echo off
cd /d "%~dp0"
call "%~dp0flutter.cmd" pub get
pause
