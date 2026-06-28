@echo off
cd /d "%~dp0"
for %%f in (*.ps1) do powershell -ExecutionPolicy Bypass -File "%%f"
pause
