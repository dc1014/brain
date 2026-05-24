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
echo -e "\033[2mBiomimetic Agentic OS // Initialization Probe\033[0m\\n"

# Ensure core system utilities are available across minimal or bare-metal environments
MISSING_UTILS=()
for util in curl unzip file; do
    if ! command -v "$util" &> /dev/null; then
        MISSING_UTILS+=("$util")
    fi
done

if [ ${#MISSING_UTILS[@]} -ne 0 ]; then
    echo -e "\033[1;33m⚠️ Missing required system utilities: ${MISSING_UTILS[*]}\033[0m"

    PKG_MANAGER=""
    INSTALL_CMD=""
    UPDATE_CMD=""

    if command -v apt-get &> /dev/null; then
        PKG_MANAGER="apt"
        UPDATE_CMD="apt-get update -y"
        INSTALL_CMD="apt-get install -y ${MISSING_UTILS[*]}"
    elif command -v dnf &> /dev/null; then
        PKG_MANAGER="dnf"
        INSTALL_CMD="dnf install -y ${MISSING_UTILS[*]}"
    elif command -v yum &> /dev/null; then
        PKG_MANAGER="yum"
        INSTALL_CMD="yum install -y ${MISSING_UTILS[*]}"
    elif command -v pacman &> /dev/null; then
        PKG_MANAGER="pacman"
        INSTALL_CMD="pacman -Sy --noconfirm ${MISSING_UTILS[*]}"
    elif command -v apk &> /dev/null; then
        PKG_MANAGER="apk"
        INSTALL_CMD="apk add ${MISSING_UTILS[*]}"
    fi

    if [ -n "$PKG_MANAGER" ]; then
        SUDO=""
        if [ "$(id -u)" -ne 0 ] && command -v sudo &> /dev/null; then
            SUDO="sudo"
        fi

        # Prevent input loops in headless setups, automated scripts, or root containers
        AUTO_INSTALL=false
        if [ "$(id -u)" -eq 0 ] || [ "$BRAIN_OS_HEADLESS" == "1" ]; then
            AUTO_INSTALL=true
        else
            read -p "Would you like to install them via $PKG_MANAGER? (y/n) [y]: " CONFIRM_PKG
            CONFIRM_PKG=${CONFIRM_PKG:-y}
            if [[ "$CONFIRM_PKG" =~ ^[Yy]$ ]]; then
                AUTO_INSTALL=true
            fi
        fi

        if [ "$AUTO_INSTALL" = true ]; then
            echo "Installing system dependencies..."
            if [ -n "$UPDATE_CMD" ]; then
                $SUDO $UPDATE_CMD
            fi
            $SUDO $INSTALL_CMD
        else
            echo -e "\033[1;31mAborting. System utilities [${MISSING_UTILS[*]}] are required to continue.\033[0m"
            exit 1
        fi
    else
        echo -e "\033[1;31mERROR: Unsupported package manager. Please install [${MISSING_UTILS[*]}] manually.\033[0m"
        exit 1
    fi
fi

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

# Ensure Deno is installed locally for the WASM sandbox environment
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
uv run python main.py setup
