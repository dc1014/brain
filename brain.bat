@echo off
setlocal
:: Automatically calculates the absolute path to the Brain directory
set "BRAIN_DIR=%~dp0"
cd /d "%BRAIN_DIR%"

:: Bypass 'uv' completely. Use the absolute virtual environment!
".venv\Scripts\python.exe" -u -m System.cli %*
endlocal
