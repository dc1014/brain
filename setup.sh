#!/bin/bash
# --- setup.sh ---
echo "🧠 Bootstrapping Brain OS..."

if ! command -v deno &> /dev/null
then
    echo "CRITICAL: Deno is required for Brain's secure WebAssembly Sandbox."
    echo "Please install Deno: curl -fsSL https://deno.land/install.sh | sh"
    exit 1
fi

# 1. Install uv if missing
if ! command -v uv &> /dev/null; then #
    echo "📦 Installing uv (Python's ultra-fast package manager)..." #
    curl -LsSf https://astral.sh/uv/install.sh | sh #
    source $HOME/.cargo/env #
else #
    echo "✅ uv is already installed." #
fi #

# ⚡ Install Ripgrep for Native Search
if ! command -v rg &> /dev/null; then
    echo -e "${BLUE}Installing Ripgrep (rg) for native search speeds...${NC}"
    if [[ "$OSTYPE" == "darwin"* ]]; then
        brew install ripgrep
    elif command -v apt-get &> /dev/null; then
        sudo apt-get update && sudo apt-get install -y ripgrep
    else
        echo -e "${YELLOW}⚠️ Please install ripgrep manually: https://github.com/BurntSushi/ripgrep${NC}"
    fi
fi

# 1.5. Hardware Senses (Linux Only)
if [[ "$OSTYPE" == "linux-gnu"* ]]; then #
    echo "📦 Checking for Biological Ear hardware drivers (PortAudio)..." #
    if ! dpkg -s portaudio19-dev &> /dev/null; then #
        echo "   Installing portaudio19-dev..." #
        sudo apt-get update && sudo apt-get install -y portaudio19-dev #
    else #
        echo "✅ Hardware drivers installed." #
    fi #
fi #

# ⚡ NATIVE SECURITY CEILING: Inject automatic user-space Deno sandboxing hooks
echo "🦕 Checking for User-Space Runtime Sandbox (Deno)..."
if ! command -v deno &> /dev/null; then
    echo "📦 Deno is missing. Executing autonomous user-space deployment..."
    curl -fsSL https://deno.land/x/install/install.sh | sh
    export DENO_INSTALL="$HOME/.deno"
    export PATH="$DENO_INSTALL/bin:$PATH"
else
    echo "✅ Deno process containment runtime is ready."
fi

# 2. Setup Environment Variables
if [ ! -f .env ]; then #
    echo "📄 Creating .env file from template..." #
    cp .env.example .env #
    echo "⚠️  ACTION REQUIRED: Please open .env and add your API keys." #
else #
    echo "✅ .env file already exists." #
fi #

# 2.5 Setup Biological Membranes
echo "🧬 Initializing biological membranes..." #
mkdir -p .trash #
mkdir -p Meta #

# 3. Hydrate Dependencies
echo "⚡ Syncing OS dependencies..." #
uv sync #

uv run python System/cli.py init #
uv run playwright install chromium #
