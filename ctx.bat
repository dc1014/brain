@echo off
setlocal enabledelayedexpansion

set "CORETEX_DIR=%~dp0"
cd /d "%CORETEX_DIR%"

:: Check if the user explicitly requested Docker
if "%1"=="--docker" (
    shift
    goto run_docker
)

:run_local
".venv\Scripts\python.exe" -u -m System.cli %*
goto :eof

:run_docker
set "CORETEX_WORKSPACE_MOUNT=%CD%\Workspace"
if not exist "!CORETEX_WORKSPACE_MOUNT!" mkdir "!CORETEX_WORKSPACE_MOUNT!"

set "NEW_ARGS="
:loop
if "%1"=="" goto run_docker_cmd
set "ARG=%1"
set "ABS_PATH=%~f1"
if exist "%~1" (
    if exist "%~1\" (
        set "CORETEX_WORKSPACE_MOUNT=!ABS_PATH!"
        set "NEW_ARGS=!NEW_ARGS! "/workspace""
    ) else (
        set "CORETEX_WORKSPACE_MOUNT=%~dp1"
        if "!CORETEX_WORKSPACE_MOUNT:~-1!"=="\" set "CORETEX_WORKSPACE_MOUNT=!CORETEX_WORKSPACE_MOUNT:~0,-1!"
        set "NEW_ARGS=!NEW_ARGS! "/workspace/%~nx1""
    )
) else (
    set "NEW_ARGS=!NEW_ARGS! "%~1""
)
shift
goto loop

:run_docker_cmd
docker compose run --rm coretex !NEW_ARGS!
endlocal
