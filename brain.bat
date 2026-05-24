@echo off
setlocal enabledelayedexpansion

:: Calculate absolute workspace bounds
set "BRAIN_DIR=%~dp0"
cd /d "%BRAIN_DIR%"

:: Check if the user built the Docker image
docker image inspect brain-os >nul 2>&1
if %errorlevel% equ 0 (
    docker compose run --rm brain %*
    goto :eof
)

:: ⚡ THE PASSTHROUGH FIX: Forward raw parameters directly using %*
".venv\Scripts\python.exe" -u -m System.cli %*

endlocal
