@echo off
setlocal enabledelayedexpansion

:: Calculate absolute workspace bounds
set "BRAIN_DIR=%~dp0"
cd /d "%BRAIN_DIR%"

:: Check if the user built the Docker image
docker image inspect brain-os >nul 2>&1
if %errorlevel% neq 0 (
    :: Fallback route directly to local virtual environment
    ".venv\Scripts\python.exe" -u -m System.cli %*
    goto :eof
)

:: Initialize default workspace parameters safely
set "BRAIN_WORKSPACE_MOUNT=%CD%\Workspace"
if not exist "!BRAIN_WORKSPACE_MOUNT!" mkdir "!BRAIN_WORKSPACE_MOUNT!"

:: Process path conversions across arguments
set "NEW_ARGS="
for %%A in (%*) do (
    set "CURRENT_ARG=%%~A"
    if exist "%%~A" (
        :: Extract absolute windows host path reference
        set "BRAIN_WORKSPACE_MOUNT=%%~fA"
        set "NEW_ARGS=!NEW_ARGS! /workspace"
    ) else (
        set "NEW_ARGS=!NEW_ARGS! %%A"
    )
)

:: Dispatch cleanly down the compose runtime pipeline
docker compose run --rm brain !NEW_ARGS!

endlocal
