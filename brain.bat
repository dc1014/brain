@echo off
setlocal enabledelayedexpansion

:: Calculate absolute workspace bounds
set "BRAIN_DIR=%~dp0"
cd /d "%BRAIN_DIR%"

if not exist ".venv" (
    echo 🧠 Brain OS: Virtual environment missing. Initiating automatic synaptic bootstrapping...

    where uv >nul 2>nul
    if !errorlevel! neq 0 (
        echo 📦 Installing uv ^(Python's ultra-fast package manager^)...
        powershell -ExecutionPolicy Bypass -Command "irm https://astral.sh/uv/install.ps1 | iex"
        set "PATH=%USERPROFILE%\.cargo\bin;%PATH%"
    )

    echo ⚡ Syncing OS dependencies and configuring workspace...
    uv sync
    if !errorlevel! neq 0 exit /b !errorlevel!

    echo 👁️  Installing browser subsystems for raw transduction ^(Playwright^)...
    uv run playwright install chromium

    echo ✅ Workspace hydrated successfully!
    echo.

    if "%~1"="" (
        set "ARGS=setup"
    ) else (
        set "ARGS=%*"
    )
) else (
    set "ARGS=%*"
)

if "%ARGS%"="" (
    ".venv\Scripts\python.exe" -u -m System.cli
) else (
    ".venv\Scripts\python.exe" -u -m System.cli %ARGS%
)

endlocal
