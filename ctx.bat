@echo off
setlocal enabledelayedexpansion

:: Calculate absolute workspace bounds
set "CORETEX_DIR=%~dp0"
cd /d "%CORETEX_DIR%"

:: Check if the user built the Docker image
docker image inspect coretex-os >nul 2>&1
if %errorlevel% neq 0 (
    :: Fallback route directly to local virtual environment
    ".venv\Scripts\python.exe" -u -m System.cli %*
    goto :eof
)

:: Build fallback directory to preserve host user ownership boundaries
set "CORETEX_WORKSPACE_MOUNT=%CD%\Workspace"
if not exist "!CORETEX_WORKSPACE_MOUNT!" mkdir "!CORETEX_WORKSPACE_MOUNT!"

:: Process path conversions across arguments with rigid space escaping
set "NEW_ARGS="
for %%A in (%*) do (
    set "ABS_PATH=%%~fA"
    if exist "%%~A" (
        if exist "%%~A\" (
            set "CORETEX_WORKSPACE_MOUNT=!ABS_PATH!"
            set "NEW_ARGS=!NEW_ARGS! "/workspace""
        ) else (
            set "CORETEX_WORKSPACE_MOUNT=%%~dpA"
            :: Clean trailing character backslash checks to protect execution parsers
            if "!CORETEX_WORKSPACE_MOUNT:~-1!"=="\" set "CORETEX_WORKSPACE_MOUNT=!CORETEX_WORKSPACE_MOUNT:~0,-1!"
            set "NEW_ARGS=!NEW_ARGS! "/workspace/%%~nxA""
        )
    ) else (
        set "NEW_ARGS=!NEW_ARGS! "%%~A""
    )
)

:: Dispatch cleanly down the compose runtime pipeline
docker compose run --rm coretex !NEW_ARGS!

endlocal
