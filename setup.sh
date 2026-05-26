#!/usr/bin/env bash
# --- setup.sh ---
set -e

echo -e "\033[1;36m"
echo " ██████╗ ██████╗ ██████╗ ███████╗████████╗███████╗██╗  ██╗"
echo "██╔════╝██╔═══██╗██╔══██╗██╔════╝╚══██╔══╝██╔════╝╚██╗██╔╝"
echo "██║     ██║   ██║██████╔╝█████╗     ██║   █████╗   ╚███╔╝ "
echo "██║     ██║   ██║██╔══██╗██╔══╝     ██║   ██╔══╝   ██╔██╗ "
echo "╚██████╗╚██████╔╝██║  ██║███████╗   ██║   ███████╗██╔╝ ██╗"
echo " ╚═════╝ ╚═════╝ ╚═╝  ╚═╝╚══════╝   ╚═╝   ╚══════╝╚═╝  ╚═╝"
echo -e "\033[0m"
echo -e "\033[2mBiomimetic Agentic OS // Initialization Probe\033[0m\\n"

MISSING_UTILS=()
for util in curl unzip file; do
    if ! command -v "$util" &> /dev/null; then
        MISSING_UTILS+=("$util")
    fi
done

if [ ${#MISSING_UTILS[@]} -ne 0 ]; then
    echo -e "\033[1;33m[!] Missing required system utilities: ${MISSING_UTILS[*]}\033[0m"
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
    elif command -v brew &> /dev/null; then
        PKG_MANAGER="homebrew"
        INSTALL_CMD="brew install ${MISSING_UTILS[*]}"
    fi

    if [ -n "$PKG_MANAGER" ]; then
        SUDO=""
        if [ "$PKG_MANAGER" != "homebrew" ] && [ "$(id -u)" -ne 0 ] && command -v sudo &> /dev/null; then
            SUDO="sudo"
        fi

        AUTO_INSTALL=false
        if [ "$(id -u)" -eq 0 ] || [ "$CORETEX_HEADLESS" == "1" ]; then
            AUTO_INSTALL=true
        else
            read -p "Would you like to install them via $PKG_MANAGER? (y/n) [y]: " CONFIRM_PKG
            CONFIRM_PKG=${CONFIRM_PKG:-y}
            if [[ "$CONFIRM_PKG" =~ ^[Yy]$ ]]; then
                AUTO_INSTALL=true
            fi
        fi

        if [ "$AUTO_INSTALL" = true ]; then
            echo "[*] Installing system dependencies natively..."
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

# ⚡ FIX: Dual-probe localhost and 127.0.0.1 to prevent IPv6 loopback failures
if curl -s http://127.0.0.1:11434/api/tags > /dev/null || curl -s http://localhost:11434/api/tags > /dev/null; then
    echo -e "[+] \033[1;32mLocal Ollama Engine Detected.\033[0m Private inference interface available."
else
    echo -e "[-] \033[1;33mNo local Ollama detected.\033[0m Cloud infrastructure access keys required."
fi
echo ""

DOCKER_AVAILABLE=false
if command -v docker &> /dev/null; then
    if docker info >/dev/null 2>&1; then
        DOCKER_AVAILABLE=true
    fi
fi

echo -e "\033[1mSelect your preferred deployment architecture:\033[0m"
echo "  [1] Pure Local (Requires 'uv' and Python 3.12+)"
if [ "$DOCKER_AVAILABLE" = true ]; then
    echo "  [2] Isolated Container (Requires Docker - ZERO host dependencies)"
else
    echo "  [2] Isolated Container (UNAVAILABLE - Docker engine not running)"
fi

if [ "$CORETEX_HEADLESS" == "1" ]; then
    DEPLOY_CHOICE="1"
else
    read -p "Enter choice [1]: " DEPLOY_CHOICE
    DEPLOY_CHOICE=${DEPLOY_CHOICE:-1}
fi

if [ -f "./ctx" ]; then
    chmod +x ./ctx
fi

if [ "$DEPLOY_CHOICE" == "2" ] && [ "$DOCKER_AVAILABLE" = true ]; then
    echo -e "\n[*] \033[1;34mBuilding Isolated Docker Sandbox...\033[0m"

    touch .env
    mkdir -p logs System/config Meta

    export UID=$(id -u)
    export GID=$(id -g)
    docker compose build

    echo -e "\n[+] \033[1;32mBuild complete.\033[0m"
    echo -e "[*] Booting Synaptic Genesis inside container context...\n"

    exec ./ctx setup
fi

echo -e "\n[*] \033[1;36mInitializing Pure Local Environment...\033[0m"

if ! command -v uv &> /dev/null; then
    if [ -f "$HOME/.local/bin/uv" ]; then
        export PATH="$HOME/.local/bin:$PATH"
    elif [ -f "$HOME/.cargo/bin/uv" ]; then
        export PATH="$HOME/.cargo/bin:$PATH"
    else
        echo -e "${RED}❌ uv installation failed or could not be found in PATH. Please restart your terminal.${NC}"
        exit 1
    fi
fi

if ! command -v deno &> /dev/null; then
    if [ -f "$HOME/.deno/bin/deno" ]; then
        export PATH="$HOME/.deno/bin:$PATH"
    else
        echo -e "${RED}❌ deno installation failed or could not be found in PATH. Please restart your terminal.${NC}"
        exit 1
    fi
fi

if ! command -v deno &> /dev/null && ! [ -f "$HOME/.deno/bin/deno" ]; then
    echo -e "\033[1;31mERROR: Deno installation failed or is missing from PATH. Please restart your terminal and try again.\033[0m"
    exit 1
fi

mkdir -p logs System/config Meta

echo -e "\033[36m[*] Synchronizing CoreTex dependencies (this may take a moment)...\033[0m"
$UV_BIN sync --all-extras

echo -e "\n[+] Local environment synchronized."
echo -e "[*] Booting Synaptic Genesis...\n"
$UV_BIN run python -m System.cli setup
