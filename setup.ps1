# --- setup.ps1 ---
$ErrorActionPreference = "Stop"

Write-Host "`n██████╗ ██████╗  █████╗ ██╗███╗   ██╗" -ForegroundColor Cyan
Write-Host "██╔══██╗██╔══██╗██╔══██╗██║████╗  ██║" -ForegroundColor Cyan
Write-Host "██████╔╝██████╔╝███████║██║██╔██╗ ██║" -ForegroundColor Cyan
Write-Host "██╔══██╗██╔══██╗██╔══██║██║██║╚██╗██║" -ForegroundColor Cyan
Write-Host "██████╔╝██║  ██║██║  ██║██║██║ ╚████║" -ForegroundColor Cyan
Write-Host "╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝╚═╝  ╚═══╝" -ForegroundColor Cyan
Write-Host "Biomimetic Agentic OS // Initialization Probe`n" -ForegroundColor DarkGray

# 1. Probe for Ollama
$ollamaRunning = $false
try {
    $response = Invoke-RestMethod -Uri "http://localhost:11434/api/tags" -Method Get -ErrorAction SilentlyContinue
    $ollamaRunning = $true
    Write-Host "🧠 Local Ollama Engine Detected. Air-gapped execution is available.`n" -ForegroundColor Green
} catch {
    Write-Host "☁️ No local Ollama detected. Cloud LLM keys will be required.`n" -ForegroundColor Yellow
}

# 2. Probe for Docker
$dockerAvailable = $false
if (Get-Command "docker" -ErrorAction SilentlyContinue) {
    $dockerAvailable = $true
}

# 3. Environment Selection
Write-Host "Select your preferred deployment architecture:" -ForegroundColor White
Write-Host "  [1] Pure Local (Requires 'uv' and Python 3.12+)"
if ($dockerAvailable) {
    Write-Host "  [2] Isolated Container (Requires Docker - ZERO host dependencies)"
} else {
    Write-Host "  [2] Isolated Container (UNAVAILABLE - Docker not found)" -ForegroundColor DarkGray
}

$deployChoice = Read-Host "Enter choice [1]"
if ([string]::IsNullOrWhiteSpace($deployChoice)) { $deployChoice = "1" }

if ($deployChoice -eq "2" -and $dockerAvailable) {
    Write-Host "`n🐳 Building Isolated Docker Sandbox..." -ForegroundColor Cyan
    docker compose build
    Write-Host "`n✅ Build complete." -ForegroundColor Green
    Write-Host "To run Brain OS in the container, use the wrapper script: .\brain.bat"
    exit
}

# 4. Pure Local Setup
Write-Host "`n⚡ Initializing Pure Local Environment..." -ForegroundColor Cyan
if (-not (Get-Command "uv" -ErrorAction SilentlyContinue)) {
    $installUv = Read-Host "The 'uv' package manager is missing. Install it? (y/n) [y]"
    if ([string]::IsNullOrWhiteSpace($installUv)) { $installUv = "y" }

    if ($installUv -match "^[yY]") {
        Invoke-WebRequest -Uri "https://astral.sh/uv/install.ps1" -OutFile "install_uv.ps1"
        powershell -ExecutionPolicy ByPass -File "install_uv.ps1"
        Remove-Item "install_uv.ps1"
        $env:Path += ";$HOME\.cargo\bin"
        [Environment]::SetEnvironmentVariable("Path", [Environment]::GetEnvironmentVariable("Path", "User") + ";$HOME\.cargo\bin", "User")
    } else {
        Write-Host "Aborting. 'uv' is required for local installation." -ForegroundColor Red
        exit
    }
}

# 🛡️ Fix Blocker 3: Auto-install Deno on Windows for local execution compliance
if (-not (Get-Command "deno" -ErrorAction SilentlyContinue)) {
    Write-Host "`n🦕 Installing Deno WASM Sandbox locally..." -ForegroundColor Cyan
    irm https://deno.land/install.ps1 | iex
    $env:Path += ";$HOME\.deno\bin"
    [Environment]::SetEnvironmentVariable("Path", [Environment]::GetEnvironmentVariable("Path", "User") + ";$HOME\.deno\bin", "User")
}

uv venv
uv pip install -e .
uv pip install -e ./Sense

Write-Host "`n✅ Local environment synchronized." -ForegroundColor Green
Write-Host "🛑 IMPORTANT: Restart your PowerShell console window to reload updated environment variables." -ForegroundColor Yellow
Write-Host "Booting Synaptic Genesis...`n"
uv run python main.py setup
