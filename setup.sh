#!/usr/bin/env bash
# --- setup.sh ---
set -e

echo -e "\033[1;36m"
echo "██████╗ ██████╗  █████╗ ██╗███╗   ██╗"
echo "██╔══██╗██╔══██╗██╔══██╗██║████╗  ██║"
echo "██████╔╝██████╔╝███████║██║██╔██╗ ██║"
echo "██╔══██╗██╔══██╗██╔══██║██║██║╚██╗██║"
echo "██████╔╝██║  ██║██║  ██║██║██║ ╚████║"
echo "╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝╚═╝  ╚═══╝"
echo -e "\033[0m"
echo -e "\033[2mBiomimetic Agentic OS // Initialization Probe\033[0m\n"

# 1. Probe for Air-Gapped AI (Ollama)
if curl -s http://localhost:11434/api/tags > /dev/null; then
    echo -e "🧠 \033[1;32mLocal Ollama Engine Detected.\033[0m Air-gapped execution is available."
else
    echo -e "☁️  \033[1;33mNo local Ollama detected.\033[0m Cloud LLM keys will be required."
fi
echo ""

# 2. Probe for Docker
DOCKER_AVAILABLE=false
if command -v docker &> /dev/null; then
    DOCKER_AVAILABLE=true
fi

# 3. Environment Selection
echo -e "\033[1mSelect your preferred deployment architecture:\033[0m"
echo "  [1] Pure Local (Requires 'uv' and Python 3.12+)"
if [ "$DOCKER_AVAILABLE" = true ]; then
    echo "  [2] Isolated Container (Requires Docker - ZERO host dependencies)"
else
    echo "  [2] Isolated Container (UNAVAILABLE - Docker not found)"
fi

read -p "Enter choice [1]: " DEPLOY_CHOICE
DEPLOY_CHOICE=${DEPLOY_CHOICE:-1}

if [ "$DEPLOY_CHOICE" == "2" ] && [ "$DOCKER_AVAILABLE" = true ]; then
    echo -e "\n🐳 \033[1;34mBuilding Isolated Docker Sandbox...\033[0m"
    docker compose build
    echo -e "\n✅ \033[1;32mBuild complete.\033[0m"
    echo "To run Brain OS in the container, use the wrapper script: ./brain"
    exit 0
fi

# 4. Pure Local Setup
echo -e "\n⚡ \033[1;36mInitializing Pure Local Environment...\033[0m"

# Enforce persistent PATH updates across profile files
SHELL_PROFILE=""
if [[ "$SHELL" == */zsh ]]; then
    SHELL_PROFILE="$HOME/.zshrc"
elif [[ "$SHELL" == */bash ]]; then
    SHELL_PROFILE="$HOME/.bashrc"
fi

if ! command -v uv &> /dev/null; then
    read -p "The 'uv' package manager is missing. Install it? (y/n) [y]: " INSTALL_UV
    INSTALL_UV=${INSTALL_UV:-y}
    if [[ "$INSTALL_UV" =~ ^[Yy]$ ]]; then
        curl -LsSf https://astral.sh/uv/install.sh | sh
        # ⚡ REALIGNMENT: Standard standalone uv installs map directly to .local/bin
        export PATH="$HOME/.local/bin:$PATH"
        if [ -n "$SHELL_PROFILE" ] && [ -f "$SHELL_PROFILE" ]; then
            if ! grep -q ".local/bin" "$SHELL_PROFILE"; then
                echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$SHELL_PROFILE"
            fi
        fi
    else
        echo -e "\033[1;31mAborting. 'uv' is required for local installation.\033[0m"
        exit 1
    fi
fi

# Auto-install Deno locally to satisfy marketed Agentic features
if ! command -v deno &> /dev/null; then
    echo -e "\n🦕 \033[1;34mInstalling Deno WASM Sandbox locally...\033[0m"
    curl -fsSL https://deno.land/install.sh | sh
    export DENO_INSTALL="$HOME/.deno"
    export PATH="$DENO_INSTALL/bin:$PATH"
    if [ -n "$SHELL_PROFILE" ] && [ -f "$SHELL_PROFILE" ]; then
        if ! grep -q ".deno/bin" "$SHELL_PROFILE"; then
            echo 'export DENO_INSTALL="$HOME/.deno"' >> "$SHELL_PROFILE"
            echo 'export PATH="$DENO_INSTALL/bin:$PATH"' >> "$SHELL_PROFILE"
        fi
    fi
fi

uv venv
uv pip install -e .
uv pip install -e ./Sense

echo -e "\n✅ \033[1;32mLocal environment synchronized.\033[0m"
if [ -n "$SHELL_PROFILE" ]; then
    echo -e "\033[1;33m🛑 IMPORTANT: Run 'source $SHELL_PROFILE' or restart your terminal to activate PATH layers.\033[0m\n"
fi
echo "Booting Synaptic Genesis...\n"
uv run python -m System.cli setup
