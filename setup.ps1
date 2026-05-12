Write-Host "🧠 Bootstrapping Brain OS..." -ForegroundColor Cyan

# 1. Install uv if missing
if (!(Get-Command uv -ErrorAction SilentlyContinue)) {
    Write-Host "📦 Installing uv (Python's ultra-fast package manager)..." -ForegroundColor Yellow
    irm https://astral.sh/uv/install.ps1 | iex
    $env:Path += ";$HOME\.cargo\bin"
} else {
    Write-Host "✅ uv is already installed." -ForegroundColor Green
}

# 2. Setup Environment Variables
if (!(Test-Path .env)) {
    Write-Host "📄 Creating .env file from template..." -ForegroundColor Yellow
    Copy-Item .env.example .env
    Write-Host "⚠️  ACTION REQUIRED: Please open .env and add your API keys." -ForegroundColor Red
} else {
    Write-Host "✅ .env file already exists." -ForegroundColor Green
}

# 2.5 Setup Biological Membranes (Trash & Memory)
Write-Host "🧬 Initializing biological membranes..." -ForegroundColor Yellow
if (!(Test-Path .trash)) { New-Item -ItemType Directory -Force -Path .trash | Out-Null }
if (!(Test-Path Meta)) { New-Item -ItemType Directory -Force -Path Meta | Out-Null }

# 3. Hydrate Dependencies
Write-Host "⚡ Syncing OS dependencies..." -ForegroundColor Cyan
uv sync

# Force vault initialization to ensure Obsidian paths exist
uv run python System/cli.py init

uv run playwright install chromium

Write-Host "`n🚀 Brain OS is ready! Run: uv run python System/cli.py 'Your prompt here'" -ForegroundColor Green
