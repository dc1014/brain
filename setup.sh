#!/usr/bin/env bash
# --- setup.sh ---
set -e

CHECK_ONLY=false
FORCE_DOCKER=false
FORCE_LOCAL=false

usage() {
    cat <<'EOF'
CoreTex OS Setup Utility
Usage: ./setup.sh [OPTIONS]

Options:
  -h, --help    Show this help message and exit
  --check       Verify dependencies without installing or mutating state
  --docker      Build/use the isolated Docker runtime without prompting
  --local       Use the local uv/Deno runtime without prompting
EOF
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        -h|--help)
            usage
            exit 0
            ;;
        --check)
            CHECK_ONLY=true
            ;;
        --docker)
            FORCE_DOCKER=true
            ;;
        --local)
            FORCE_LOCAL=true
            ;;
        *)
            echo "Unknown option: $1" >&2
            usage >&2
            exit 2
            ;;
    esac
    shift
done

if [ "$FORCE_DOCKER" = true ] && [ "$FORCE_LOCAL" = true ]; then
    echo "ERROR: choose either --docker or --local, not both." >&2
    exit 2
fi

# --- FIX 03: Bootstrap PATH for fresh installs so documented commands work instantly ---
export PATH="$HOME/.local/bin:$HOME/.deno/bin:$HOME/.cargo/bin:$PATH"

echo -e "\033[1;36m"
echo " ██████╗ ██████╗ ██████╗ ███████╗████████╗███████╗██╗  ██╗"
echo "██╔════╝██╔═══██╗██╔══██╗██╔════╝╚══██╔══╝██╔════╝╚██╗██╔╝"
echo "██║     ██║   ██║██████╔╝█████╗     ██║   █████╗   ╚███╔╝ "
echo "██║     ██║   ██║██╔══██╗██╔══╝     ██║   ██╔══╝   ██╔██╗ "
echo "╚██████╗╚██████╔╝██║  ██║███████╗   ██║   ███████╗██╔╝ ██╗"
echo " ╚═════╝ ╚═════╝ ╚═╝  ╚═╝╚══════╝   ╚═╝   ╚══════╝╚═╝  ╚═╝"
echo -e "\033[0m"
echo -e "\033[2mBiomimetic Agentic OS // Initialization Probe\033[0m\n"

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
        if [ "$(id -u)" -eq 0 ] || [ "${CORETEX_HEADLESS:-}" = "1" ]; then
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

if curl -s http://127.0.0.1:11434/api/tags > /dev/null || curl -s http://localhost:11434/api/tags > /dev/null; then
    echo -e "[+] \033[1;32mLocal Ollama Engine Detected.\033[0m Private inference interface available."
else
    echo -e "[-] \033[1;33mNo local Ollama detected.\033[0m Cloud infrastructure access keys required."
fi
echo ""

DOCKER_AVAILABLE=false
DOCKER_COMPOSE_AVAILABLE=false
DOCKER_COMPOSE_CMD=(docker compose)
if command -v docker &> /dev/null; then
    if docker info >/dev/null 2>&1; then
        DOCKER_AVAILABLE=true
        if docker compose version >/dev/null 2>&1; then
            DOCKER_COMPOSE_AVAILABLE=true
            DOCKER_COMPOSE_CMD=(docker compose)
        elif command -v docker-compose >/dev/null 2>&1; then
            DOCKER_COMPOSE_AVAILABLE=true
            DOCKER_COMPOSE_CMD=(docker-compose)
        fi
    fi
fi

if [ "$CHECK_ONLY" = true ]; then
    echo "Prerequisite check:"
    echo "  curl: $(command -v curl || echo missing)"
    echo "  unzip: $(command -v unzip || echo missing)"
    echo "  file: $(command -v file || echo missing)"
    echo "  uv: $(command -v uv || echo missing)"
    echo "  deno: $(command -v deno || echo missing)"
    echo "  docker_engine: $DOCKER_AVAILABLE"
    echo "  docker_compose: $DOCKER_COMPOSE_AVAILABLE"
    if [ ${#MISSING_UTILS[@]} -ne 0 ]; then
        exit 1
    fi
    if [ "$FORCE_DOCKER" = true ]; then
        if [ "$DOCKER_AVAILABLE" != true ] || [ "$DOCKER_COMPOSE_AVAILABLE" != true ]; then
            exit 1
        fi
    elif [ "$FORCE_LOCAL" = true ]; then
        if ! command -v uv >/dev/null 2>&1 || ! command -v deno >/dev/null 2>&1; then
            exit 1
        fi
    elif ! command -v uv >/dev/null 2>&1 || ! command -v deno >/dev/null 2>&1; then
        exit 1
    fi
    exit 0
fi

echo -e "\033[1mSelect your preferred deployment architecture:\033[0m"
echo "  [1] Pure Local (Requires 'uv' and Python 3.12+)"
if [ "$DOCKER_AVAILABLE" = true ] && [ "$DOCKER_COMPOSE_AVAILABLE" = true ]; then
    echo "  [2] Isolated Container (Requires Docker - ZERO host dependencies)"
else
    echo "  [2] Isolated Container (UNAVAILABLE - Docker engine not running)"
fi

if [ "$FORCE_DOCKER" = true ]; then
    DEPLOY_CHOICE="2"
elif [ "$FORCE_LOCAL" = true ]; then
    DEPLOY_CHOICE="1"
elif [ "${CORETEX_HEADLESS:-}" = "1" ]; then
    DEPLOY_CHOICE="1"
else
    read -p "Enter choice [1]: " DEPLOY_CHOICE
    DEPLOY_CHOICE=${DEPLOY_CHOICE:-1}
fi

if [ -f "./ctx" ]; then
    chmod +x ./ctx
fi

if [ "$DEPLOY_CHOICE" == "2" ]; then
    if [ "$DOCKER_AVAILABLE" != true ]; then
        echo -e "\033[1;31mERROR: Docker is installed but the engine is not reachable. Start Docker and retry, or run ./setup.sh --local.\033[0m" >&2
        exit 1
    fi
    if [ "$DOCKER_COMPOSE_AVAILABLE" != true ]; then
        echo -e "\033[1;31mERROR: Docker Compose is unavailable. Install the Docker Compose plugin or docker-compose, then retry.\033[0m" >&2
        exit 1
    fi

    echo -e "\n[*] \033[1;34mBuilding Isolated Docker Sandbox...\033[0m"

    touch .env
    mkdir -p logs System/config Meta Workspace

    export HOST_UID=$(id -u)
    export HOST_GID=$(id -g)
    ${DOCKER_COMPOSE_CMD[@]} build

    echo -e "\n[+] \033[1;32mBuild complete.\033[0m"
    echo -e "[*] Booting Synaptic Genesis inside container context...\n"

    exec ./ctx --docker setup
fi

echo -e "\n[*] \033[1;36mInitializing Pure Local Environment...\033[0m"

if ! command -v uv &> /dev/null; then
    echo -e "\033[1;31m❌ uv installation failed or could not be found in PATH. Please restart your terminal.\033[0m"
    exit 1
fi

if ! command -v deno &> /dev/null; then
    echo -e "\033[1;31m❌ deno installation failed or could not be found in PATH. Please restart your terminal.\033[0m"
    exit 1
fi

mkdir -p logs System/config Meta

echo -e "\033[36m[*] Synchronizing CoreTex dependencies (this may take a moment)...\033[0m"
uv sync --all-extras

echo -e "\n[+] Local environment synchronized."
echo -e "[*] Booting Synaptic Genesis...\n"
uv run python -m System.cli setup
