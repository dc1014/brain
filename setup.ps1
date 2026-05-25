# --- setup.ps1 ---
$ErrorActionPreference = "Stop"

Clear-Host
Write-Host " ██████╗ ██████╗ ██████╗ ███████╗████████╗███████╗██╗  ██╗" -ForegroundColor Cyan
Write-Host "██╔════╝██╔═══██╗██╔══██╗██╔════╝╚══██╔══╝██╔════╝╚██╗██╔╝" -ForegroundColor Cyan
Write-Host "██║     ██║   ██║██████╔╝█████╗     ██║   █████╗   ╚███╔╝ " -ForegroundColor Cyan
Write-Host "██║     ██║   ██║██╔══██╗██╔══╝     ██║   ██╔══╝   ██╔██╗ " -ForegroundColor Cyan
Write-Host "╚██████╗╚██████╔╝██║  ██║███████╗   ██║   ███████╗██╔╝ ██╗" -ForegroundColor Cyan
Write-Host " ╚═════╝ ╚═════╝ ╚═╝  ╚═╝╚══════╝   ╚═╝   ╚══════╝╚═╝  ╚══╝" -ForegroundColor Cyan
Write-Host ""
Write-Host "Biomimetic Agentic OS // Initialization Probe" -ForegroundColor DarkGray
Write-Host ""

try {
    $OllamaCheck = Invoke-WebRequest -Uri "http://localhost:11434/api/tags" -UseBasicParsing -TimeoutSec 2 -ErrorAction SilentlyContinue
    if ($OllamaCheck.StatusCode -eq 200) {
        Write-Host "[+] Local Ollama Engine Detected. Air-gapped execution is available." -ForegroundColor Green
    } else {
        Write-Host "[-] No local Ollama detected. Cloud LLM keys will be required." -ForegroundColor Yellow
    }
} catch {
    Write-Host "[-] No local Ollama detected. Cloud LLM keys will be required." -ForegroundColor Yellow
}
Write-Host ""

$DockerAvailable = $null -ne (Get-Command docker -ErrorAction SilentlyContinue)

Write-Host "Select your preferred deployment architecture:" -ForegroundColor White
Write-Host "  [1] Pure Local (Requires uv and Python 3.12+)"
if ($DockerAvailable) {
    Write-Host "  [2] Isolated Container (Requires Docker - ZERO host dependencies)"
} else {
    Write-Host "  [2] Isolated Container (UNAVAILABLE - Docker not found)" -ForegroundColor Gray
}

$AutoInstall = $false
if ($env:CORETEX_HEADLESS -eq "1") {
    $AutoInstall = $true
    $DeployChoice = "1"
} else {
    $DeployChoice = Read-Host "Enter choice [1]"
    if ([string]::IsNullOrEmpty($DeployChoice)) { $DeployChoice = "1" }
}

if ($DeployChoice -eq "2" -and $DockerAvailable) {
    Write-Host "`n[*] Building Isolated Docker Sandbox..." -ForegroundColor Cyan

    if (-not (Test-Path .env)) { New-Item -Path . -Name ".env" -ItemType "file" > $null }
    foreach ($dir in "logs", "System\config", "Meta", "Workspace") {
        if (-not (Test-Path $dir)) { New-Item -ItemType Directory -Path $dir > $null }
    }

    docker compose build
    Write-Host "`n[+] Build complete." -ForegroundColor Green
    Write-Host "Booting Synaptic Genesis inside container context...`n" -ForegroundColor Cyan

    .\ctx.bat setup
    exit
}

Write-Host "`n[*] Initializing Pure Local Environment..." -ForegroundColor Cyan

if ($null -eq (Get-Command uv -ErrorAction SilentlyContinue)) {
    if ($AutoInstall) {
        Write-Host "[*] Installing uv automatically in headless mode..." -ForegroundColor Cyan
        Set-ExecutionPolicy -ExecutionPolicy Bypass -Scope Process -Force
        irm https://astral.sh/uv/install.ps1 | iex
    } else {
        $InstallUV = Read-Host "The uv package manager is missing. Install it? (y/n) [y]"
        if ([string]::IsNullOrEmpty($InstallUV)) { $InstallUV = "y" }
        if ($InstallUV -match "^[Yy]$") {
            irm https://astral.sh/uv/install.ps1 | iex
            $env:Path = [System.Environment]::GetEnvironmentVariable("Path", "User") + ";" + [System.Environment]::GetEnvironmentVariable("Path", "Machine")
        } else {
            Write-Error -Message "Aborting. uv is required for local installation."
            exit 1
        }
    }
}

if ($null -eq (Get-Command deno -ErrorAction SilentlyContinue)) {
    Write-Host "`n[*] Installing Deno WASM Sandbox locally..." -ForegroundColor Cyan
    irm https://deno.land/install.ps1 | iex
    $env:Path = [System.Environment]::GetEnvironmentVariable("Path", "User") + ";" + [System.Environment]::GetEnvironmentVariable("Path", "Machine")
}

uv venv
uv pip install -e .
uv pip install -e ./Sense

Write-Host "`n[+] Local environment synchronized." -ForegroundColor Green
Write-Host "Booting Synaptic Genesis...`n" -ForegroundColor Cyan

uv run python -m System.cli setup
