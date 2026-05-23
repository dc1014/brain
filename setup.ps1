$ErrorActionPreference = "Stop"

Write-Host "🧠 Bootstrapping Brain Core..." -ForegroundColor Cyan

# 1. Ensure the ultra-fast 'uv' package manager is installed
if (!(Get-Command "uv" -ErrorAction SilentlyContinue)) {
    Write-Host "[⚡] Installing 'uv' package manager..." -ForegroundColor Yellow
    Invoke-WebRequest -Uri https://astral.sh/uv/install.ps1 -UseBasicParsing | Invoke-Expression
    $env:Path += ";$HOME\.cargo\bin"
}

# 2. Instantly resolve and hydrate the minimal core environment
Write-Host "[⚡] Syncing core neural pathways..." -ForegroundColor Cyan
uv sync

# 3. Hand off execution to the Interactive Setup Wizard
Write-Host "[🧠] Awakening..." -ForegroundColor Green
uv run python -m System.core.onboarding.genesis
