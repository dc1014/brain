#!/bin/bash
echo "🧠 Bootstrapping Brain OS..."

# 1. Install uv if missing
if ! command -v uv &> /dev/null; then
    echo "📦 Installing uv (Python's ultra-fast package manager)..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    # Source the path so it's immediately available
    source $HOME/.cargo/env
else
    echo "✅ uv is already installed."
fi

# 1.5. Hardware Senses (Linux Only)
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    echo "📦 Checking for Biological Ear hardware drivers (PortAudio)..."
    if ! dpkg -s portaudio19-dev &> /dev/null; then
        echo "   Installing portaudio19-dev..."
        sudo apt-get update && sudo apt-get install -y portaudio19-dev
    else
        echo "✅ Hardware drivers installed."
    fi
fi

# 1.8. Check for Docker (Tier 1 Sandbox Requirement)
echo "🐳 Checking for Docker (Required for Tier 1 Sandbox)..."
if ! command -v docker &> /dev/null; then
    echo "⚠️  WARNING: Docker is not installed. Tier 1 Hardware Isolation (microsandbox) will fail."
    echo "   Please install Docker Engine: https://docs.docker.com/engine/install/"
else
    echo "✅ Docker is installed."
    if ! docker info &> /dev/null; then
        echo "⚠️  WARNING: Docker daemon is not running. Please start Docker before using Tier 1 isolation."
    fi
fi

# 2. Setup Environment Variables
if [ ! -f .env ]; then
    echo "📄 Creating .env file from template..."
    cp .env.example .env
    echo "⚠️  ACTION REQUIRED: Please open .env and add your API keys."
else
    echo "✅ .env file already exists."
fi

# 2.5 Setup Biological Membranes (Trash & Memory)
echo "🧬 Initializing biological membranes..."
mkdir -p .trash
mkdir -p Meta

# 3. Hydrate Dependencies
echo "⚡ Syncing OS dependencies..."
uv sync

# Force vault initialization to ensure Obsidian paths exist
uv run python System/cli.py init

uv run playwright install chromium
