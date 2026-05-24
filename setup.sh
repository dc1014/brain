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
    echo "To run Brain OS in the container, use the wrapper script: ./brain.sh"
    exit 0
fi

# 4. Pure Local Setup (Using uv)
echo -e "\n⚡ \033[1;36mInitializing Pure Local Environment...\033[0m"
if ! command -v uv &> /dev/null; then
    read -p "The 'uv' package manager is missing. Install it? (y/n) [y]: " INSTALL_UV
    INSTALL_UV=${INSTALL_UV:-y}
    if [[ "$INSTALL_UV" =~ ^[Yy]$ ]]; then
        curl -LsSf https://astral.sh/uv/install.sh | sh
        export PATH="$HOME/.cargo/bin:$PATH"
    else
        echo -e "\033[1;31mAborting. 'uv' is required for local installation.\033[0m"
        exit 1
    fi
fi

uv venv
uv pip install -e .
uv pip install -e ./Sense

echo -e "\n✅ \033[1;32mLocal environment synchronized.\033[0m"
echo -e "Booting Synaptic Genesis...\n"
uv run python -m System.cli setup
