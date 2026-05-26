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
if not exist ".venv\Scripts\python.exe" (
    echo [!] Local environment ^(.venv^) not found.
    echo.
    echo If you installed CoreTex via Docker, you must run it with the Docker flag:
    echo    .\ctx.bat --docker [commands]
    echo.
    echo Otherwise, please run .\setup.ps1 to initialize the local environment.
    exit /b 1
)

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
docker image inspect coretex >nul 2>&1
if errorlevel 1 (
    echo [!] Docker runtime requested, but the coretex image is not built.
    echo Run .\setup.ps1 -Docker first, or build with Docker Compose.
    exit /b 1
)

docker compose run --rm coretex !NEW_ARGS!
endlocal
