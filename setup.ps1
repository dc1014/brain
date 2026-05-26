# --- setup.ps1 ---
param(
    [switch]$Check,
    [switch]$Docker,
    [switch]$Local,
    [switch]$Help
)

$ErrorActionPreference = "Stop"

function Show-Usage {
    Write-Host "CoreTex OS Setup Utility"
    Write-Host "Usage: .\setup.ps1 [OPTIONS]"
    Write-Host ""
    Write-Host "Options:"
    Write-Host "  -Help      Show this help message and exit"
    Write-Host "  -Check     Verify dependencies without installing or mutating state"
    Write-Host "  -Docker    Build/use the isolated Docker runtime without prompting"
    Write-Host "  -Local     Use the local uv/Deno runtime without prompting"
}

function Test-DockerComposeAvailable {
    if ($null -eq (Get-Command docker -ErrorAction SilentlyContinue)) { return $false }
    docker compose version >$null 2>&1
    return $LASTEXITCODE -eq 0
}

function Test-CommandAvailable {
    param([Parameter(Mandatory = $true)][string]$Name)
    return $null -ne (Get-Command $Name -ErrorAction SilentlyContinue)
}

function Confirm-DefaultYes {
    param([Parameter(Mandatory = $true)][string]$Prompt)
    if ($env:CORETEX_HEADLESS -eq "1") { return $true }
    $Reply = Read-Host "$Prompt (y/n) [y]"
    if ([string]::IsNullOrEmpty($Reply)) { $Reply = "y" }
    return $Reply -match "^[Yy]$"
}

function Refresh-EnvPath {
    $MachinePath = [System.Environment]::GetEnvironmentVariable("Path", "Machine")
    $UserPath = [System.Environment]::GetEnvironmentVariable("Path", "User")
    $LocalUv = Join-Path $env:USERPROFILE ".local\bin"
    $CargoBin = Join-Path $env:USERPROFILE ".cargo\bin"
    $DenoBin = Join-Path $env:USERPROFILE ".deno\bin"
    $env:Path = "$LocalUv;$CargoBin;$DenoBin;$MachinePath;$UserPath"
}

function Resolve-InstalledUv {
    $UvCmd = Get-Command uv -ErrorAction SilentlyContinue
    if ($null -ne $UvCmd) { return $UvCmd.Source }
    foreach ($Candidate in @(
        (Join-Path $env:USERPROFILE ".local\bin\uv.exe"),
        (Join-Path $env:USERPROFILE ".cargo\bin\uv.exe")
    )) {
        if (Test-Path $Candidate) { return $Candidate }
    }
    return $null
}

function Install-UvRuntime {
    $Existing = Resolve-InstalledUv
    if ($null -ne $Existing) { return $Existing }
    if (-not (Confirm-DefaultYes "The uv package manager is missing. Install it now?")) {
        Write-Error -Message "Aborting. uv is required for local installation."
        exit 1
    }
    Write-Host "[*] Downloading uv package manager (this may take a moment)..." -ForegroundColor Cyan
    Set-ExecutionPolicy -ExecutionPolicy Bypass -Scope Process -Force
    irm https://astral.sh/uv/install.ps1 | iex
    Refresh-EnvPath
    $Installed = Resolve-InstalledUv
    if ($null -eq $Installed) {
        Write-Error "uv installation failed or could not be found in PATH. Restart your terminal or add .local\bin to PATH."
        exit 1
    }
    return $Installed
}

function Install-DenoRuntime {
    if (Test-CommandAvailable "deno") { return }
    if (-not (Confirm-DefaultYes "The Deno WASM sandbox runtime is missing. Install it now?")) {
        Write-Error -Message "Aborting. deno is required for local installation."
        exit 1
    }
    Write-Host "`n[*] Downloading Deno WASM Sandbox locally (this may take a moment)..." -ForegroundColor Cyan
    irm https://deno.land/install.ps1 | iex
    Refresh-EnvPath
    if (Test-CommandAvailable "deno") { return }
    $DefaultDeno = Join-Path $env:USERPROFILE ".deno\bin\deno.exe"
    if (-not (Test-Path $DefaultDeno)) {
        Write-Error "deno installation failed or could not be found in PATH. Restart your terminal or add .deno\bin to PATH."
        exit 1
    }
}

function Invoke-DockerCompose {
    param([Parameter(ValueFromRemainingArguments = $true)][string[]]$ComposeArgs)
    & docker compose @ComposeArgs
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
}

if ($Help) {
    Show-Usage
    exit 0
}

if ($Docker -and $Local) {
    Write-Error "Choose either -Docker or -Local, not both."
    exit 2
}

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
$OllamaFound = $false
try {
    $OllamaCheck = Invoke-WebRequest -Uri "http://127.0.0.1:11434/api/tags" -UseBasicParsing -TimeoutSec 2 -ErrorAction SilentlyContinue
    if ($OllamaCheck.StatusCode -eq 200) { $OllamaFound = $true }
} catch { }

if (-not $OllamaFound) {
    try {
        $OllamaCheck2 = Invoke-WebRequest -Uri "http://localhost:11434/api/tags" -UseBasicParsing -TimeoutSec 2 -ErrorAction SilentlyContinue
        if ($OllamaCheck2.StatusCode -eq 200) { $OllamaFound = $true }
    } catch { }
}

if ($OllamaFound) {
    Write-Host "[+] Local Ollama Engine Detected. Air-gapped execution is available." -ForegroundColor Green
} else {
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
$DockerComposeAvailable = $DockerAvailable -and (Test-DockerComposeAvailable)

if ($Check) {
    Write-Host "Prerequisite check:"
    Write-Host "  uv: $($null -ne (Get-Command uv -ErrorAction SilentlyContinue))"
    Write-Host "  deno: $($null -ne (Get-Command deno -ErrorAction SilentlyContinue))"
    Write-Host "  docker_engine: $DockerAvailable"
    Write-Host "  docker_compose: $DockerComposeAvailable"

    if ($Docker) {
        if (-not ($DockerAvailable -and $DockerComposeAvailable)) { exit 1 }
    } elseif ($Local) {
        if (($null -eq (Get-Command uv -ErrorAction SilentlyContinue)) -or ($null -eq (Get-Command deno -ErrorAction SilentlyContinue))) { exit 1 }
    } elseif (($null -eq (Get-Command uv -ErrorAction SilentlyContinue)) -or ($null -eq (Get-Command deno -ErrorAction SilentlyContinue))) {
        exit 1
    }
    exit 0
}

Write-Host "Select your preferred deployment architecture:" -ForegroundColor White
Write-Host "  [1] Pure Local (Requires uv and Python 3.12+)"
if ($DockerAvailable -and $DockerComposeAvailable) {
    Write-Host "  [2] Isolated Container (Requires Docker - ZERO host dependencies)"
} else {
    Write-Host "  [2] Isolated Container (UNAVAILABLE - Docker engine not running)" -ForegroundColor Gray
}

$AutoInstall = $false
if ($Docker) {
    $DeployChoice = "2"
} elseif ($Local) {
    $DeployChoice = "1"
} elseif ($env:CORETEX_HEADLESS -eq "1") {
    $AutoInstall = $true
    $DeployChoice = "1"
} else {
    $DeployChoice = Read-Host "Enter choice [1]"
    if ([string]::IsNullOrEmpty($DeployChoice)) { $DeployChoice = "1" }
}

if ($DeployChoice -eq "2") {
    if (-not $DockerAvailable) {
        Write-Error "Docker is installed but the engine is not reachable. Start Docker and retry, or run .\setup.ps1 -Local."
        exit 1
    }
    if (-not $DockerComposeAvailable) {
        Write-Error "Docker Compose is unavailable. Install Docker Desktop with Compose support, then retry."
        exit 1
    }

    Write-Host "`n[*] Building Isolated Docker Sandbox..." -ForegroundColor Cyan

    if (-not (Test-Path .env)) { New-Item -Path . -Name ".env" -ItemType "file" > $null }
    foreach ($dir in "logs", "System\config", "Meta", "Workspace") {
        if (-not (Test-Path $dir)) { New-Item -ItemType Directory -Path $dir > $null }
    }

    Invoke-DockerCompose build
    Write-Host "`n[+] Build complete." -ForegroundColor Green
    Write-Host "[*] Booting Synaptic Genesis inside container context...`n" -ForegroundColor Cyan

    # Force docker fallback execution to prevent missing venv crash
    .\ctx.bat --docker setup
    exit
}

Write-Host "`n[*] Initializing Pure Local Environment..." -ForegroundColor Cyan

$UvBin = Install-UvRuntime
Install-DenoRuntime

foreach ($dir in "logs", "System\config", "Meta") {
    if (-not (Test-Path $dir)) { New-Item -ItemType Directory -Path $dir -Force > $null }
}

Write-Host "`n[*] Synchronizing CoreTex dependencies (this may take a moment)..." -ForegroundColor Cyan
& $UvBin sync --all-extras

Write-Host "`n[+] Local environment synchronized." -ForegroundColor Green
Write-Host "[*] Booting Synaptic Genesis...`n" -ForegroundColor Cyan

& $UvBin run python -m System.cli setup
