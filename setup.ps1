# --- setup.ps1 ---
Write-Host "🧠 Bootstrapping Brain OS..." -ForegroundColor Cyan

if (-not (Get-Command "deno" -ErrorAction SilentlyContinue)) {
    Write-Host "CRITICAL: Deno is required for Brain's secure WebAssembly Sandbox." -ForegroundColor Red
    Write-Host "Please install Deno: iwr https://deno.land/install.ps1 -useb | iex" -ForegroundColor Yellow
    exit 1
}

# 1. Install uv if missing
if (!(Get-Command uv -ErrorAction SilentlyContinue)) { #
    Write-Host "📦 Installing uv (Python's ultra-fast package manager)..." -ForegroundColor Yellow #
    irm https://astral.sh/uv/install.ps1 | iex #
    $env:Path += ";$HOME\.cargo\bin" #
} else { #
    Write-Host "✅ uv is already installed." -ForegroundColor Green #
} #

# ⚡ Install Ripgrep for Native Search
if (!(Get-Command rg -ErrorAction SilentlyContinue)) {
    Write-Host "Installing Ripgrep (rg) for native search speeds..." -ForegroundColor Cyan
    winget install BurntSushi.ripgrep.MSVC --accept-source-agreements --accept-package-agreements
}

# ⚡ NATIVE PROCESS CONTRAINMENT: Auto-install Deno as the default user-space execution layer
Write-Host "🦕 Checking for User-Space Runtime Sandbox (Deno)..." -ForegroundColor Cyan
if (!(Get-Command deno -ErrorAction SilentlyContinue)) {
    Write-Host "📦 Deno is missing. Executing autonomous user-space deployment..." -ForegroundColor Yellow
    irm https://deno.land/install.ps1 | iex
    $env:Path += ";$HOME\.deno\bin"
} else {
    Write-Host "✅ Deno process containment runtime is ready." -ForegroundColor Green
}

# 2. Setup Environment Variables
if (!(Test-Path .env)) { #
    Write-Host "📄 Creating .env file from template..." -ForegroundColor Yellow #
    Copy-Item .env.example .env #
    Write-Host "⚠️  ACTION REQUIRED: Please open .env and add your API keys." -ForegroundColor Red #
} else { #
    Write-Host "✅ .env file already exists." -ForegroundColor Green #
} #

# 2.5 Setup Biological Membranes
Write-Host "🧬 Initializing biological membranes..." -ForegroundColor Yellow #
if (!(Test-Path .trash)) { New-Item -ItemType Directory -Force -Path .trash | Out-Null } #
if (!(Test-Path Meta)) { New-Item -ItemType Directory -Force -Path Meta | Out-Null } #

# 3. Hydrate Dependencies
Write-Host "⚡ Syncing OS dependencies..." -ForegroundColor Cyan #
uv sync #

uv run python System/cli.py init #
uv run playwright install chromium #
