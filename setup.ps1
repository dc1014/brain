# --- setup.ps1 ---
$ErrorActionPreference = "Stop"

Clear-Host
Write-Host "====================================================" -ForegroundColor Cyan
Write-Host "  ______  ______   ______   ______ ______ ______ _  _  " -ForegroundColor Cyan
Write-Host " / _____ /  __  \ /  __  \ / ____ /__  __ / ____ / / / / " -ForegroundColor Cyan
Write-Host " / /     / /  / / / /__/ / / ___    / /   / ___  \  / /  " -ForegroundColor Cyan
Write-Host " / /____ / /__/ / /  __  / /____   / /   / /____ / / \ \ " -ForegroundColor Cyan
Write-Host " \______ \______/ /_/  \_ \_____/   /_/   \_____/_/   \_\" -ForegroundColor Cyan
Write-Host "====================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Biomimetic Agentic OS // Initialization Probe" -ForegroundColor DarkGray
Write-Host ""

# 1. Probe for Air-Gapped AI (Ollama)
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

$DockerAvailable = $false
if ($null -ne (Get-Command docker -ErrorAction SilentlyContinue)) {
    docker info >$null 2>&1
    if ($?) {
        $DockerAvailable = $true
    }
}

Write-Host "Select your preferred deployment architecture:" -ForegroundColor White
Write-Host "  [1] Pure Local (Requires uv and Python 3.12+)"
if ($DockerAvailable) {
    Write-Host "  [2] Isolated Container (Requires Docker - ZERO host dependencies)"
} else {
    Write-Host "  [2] Isolated Container (UNAVAILABLE - Docker engine not running)" -ForegroundColor Gray
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
    Write-Host "[*] Booting Synaptic Genesis inside container context...`n" -ForegroundColor Cyan

    .\ctx.bat setup
    exit
}

Write-Host "`n[*] Initializing Pure Local Environment..." -ForegroundColor Cyan

# Helper function to dynamically pull the latest PATH variables after an installation
function Refresh-EnvPath {
    $env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path", "User")
}

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
        } else {
            Write-Error -Message "Aborting. uv is required for local installation."
            exit 1
        }
    }
    Refresh-EnvPath
}

# Dynamically resolve the binary path using Get-Command
$UvCmd = Get-Command uv -ErrorAction SilentlyContinue
if ($null -eq $UvCmd) {
    Write-Error "uv installation failed or could not be found in PATH. Please restart your terminal."
    exit 1
}
$UvBin = $UvCmd.Source

if ($null -eq (Get-Command deno -ErrorAction SilentlyContinue)) {
    Write-Host "`n[*] Installing Deno WASM Sandbox locally..." -ForegroundColor Cyan
    irm https://deno.land/install.ps1 | iex
    Refresh-EnvPath
}

$DenoCmd = Get-Command deno -ErrorAction SilentlyContinue
if ($null -eq $DenoCmd) {
    Write-Error "deno installation failed or could not be found in PATH. Please restart your terminal."
    exit 1
}

# ⚡ FIX: Explicitly create required folders BEFORE running Genesis
foreach ($dir in "logs", "System\config", "Meta") {
    if (-not (Test-Path $dir)) { New-Item -ItemType Directory -Path $dir -Force > $null }
}

# ⚡ FIX: Use the modern uv workspace synchronization
& $UvBin sync --all-extras

Write-Host "`n[+] Local environment synchronized." -ForegroundColor Green
Write-Host "[*] Booting Synaptic Genesis...`n" -ForegroundColor Cyan

& $UvBin run python -m System.cli setup
