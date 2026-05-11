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

# 2. Setup Environment Variables
if [ ! -f .env ]; then
    echo "📄 Creating .env file from template..."
    cp .env.example .env
    echo "⚠️  ACTION REQUIRED: Please open .env and add your API keys."
else
    echo "✅ .env file already exists."
fi

# 3. Hydrate Dependencies
echo "⚡ Syncing OS dependencies..."
uv sync

# Force vault initialization to ensure Obsidian paths exist
uv run python System/cli.py init

uv run playwright install chromium

echo ""
echo "🚀 Brain OS is ready! Run: uv run python System/cli.py 'Your prompt here'"
