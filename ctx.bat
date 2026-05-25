@echo off
setlocal enabledelayedexpansion

set "CORETEX_DIR=%~dp0"
cd /d "%CORETEX_DIR%"

docker image inspect coretex-os >nul 2>&1
if %errorlevel% neq 0 (
    ".venv\Scripts\python.exe" -u -m System.cli %*
    goto :eof
)

set "CORETEX_WORKSPACE_MOUNT=%CD%\Workspace"
if not exist "!CORETEX_WORKSPACE_MOUNT!" mkdir "!CORETEX_WORKSPACE_MOUNT!"

set "NEW_ARGS="
for %%A in (%*) do (
    set "ABS_PATH=%%~fA"
    if exist "%%~A" (
        if exist "%%~A\" (
            set "CORETEX_WORKSPACE_MOUNT=!ABS_PATH!"
            set "NEW_ARGS=!NEW_ARGS! "/workspace""
        ) else (
            set "CORETEX_WORKSPACE_MOUNT=%%~dpA"
            if "!CORETEX_WORKSPACE_MOUNT:~-1!"=="\" set "CORETEX_WORKSPACE_MOUNT=!CORETEX_WORKSPACE_MOUNT:~0,-1!"
            set "NEW_ARGS=!NEW_ARGS! "/workspace/%%~nxA""
        )
    ) else (
        set "NEW_ARGS=!NEW_ARGS! "%%~A""
    )
)

docker compose run --rm coretex !NEW_ARGS!

endlocal
