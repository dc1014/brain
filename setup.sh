#!/usr/bin/env bash
# --- setup.sh ---
set -e

CHECK_ONLY=false
FORCE_DOCKER=false
FORCE_LOCAL=false
CORETEX_MIN_PYTHON="${CORETEX_MIN_PYTHON:-3.12}"

usage() {
    cat <<'EOF'
CoreTex OS Setup Utility
Usage: ./setup.sh [OPTIONS]

Options:
  -h, --help    Show this help message and exit
  --check       Verify dependencies without installing or mutating state
  --docker      Build/use the isolated Docker runtime without prompting
  --local       Use the local uv/Deno runtime without prompting

Examples:
  ./setup.sh --check
  ./setup.sh --docker
  ./setup.sh --local
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

command_exists() {
    command -v "$1" >/dev/null 2>&1
}

python_version_available() {
    command_exists python3 && python3 - <<PY >/dev/null 2>&1
import sys
need = tuple(int(part) for part in "$CORETEX_MIN_PYTHON".split("."))
sys.exit(0 if sys.version_info[:2] >= need else 1)
PY
}

python_install_hint() {
    if command_exists apt-get; then
        echo "sudo apt-get update && sudo apt-get install -y python3 python3-venv"
    elif command_exists dnf; then
        echo "sudo dnf install -y python3"
    elif command_exists yum; then
        echo "sudo yum install -y python3"
    elif command_exists pacman; then
        echo "sudo pacman -Sy --noconfirm python"
    elif command_exists apk; then
        echo "sudo apk add python3 py3-pip"
    elif command_exists brew; then
        echo "brew install python@${CORETEX_MIN_PYTHON}"
    else
        echo "Install Python ${CORETEX_MIN_PYTHON}+ from https://www.python.org/downloads/"
    fi
}

install_python_runtime() {
    if python_version_available; then
        return 0
    fi
    local hint
    hint="$(python_install_hint)"
    echo -e "\033[1;33m[!] Python ${CORETEX_MIN_PYTHON}+ is required for local setup.\033[0m"
    echo "Suggested install command: $hint"
    if ! confirm_default_yes "Install Python prerequisites now?"; then
        echo -e "\033[1;31mAborting. Install Python ${CORETEX_MIN_PYTHON}+ manually, or run ./setup.sh --docker.\033[0m" >&2
        return 1
    fi
    SUDO=""
    if [ "$(id -u)" -ne 0 ] && command_exists sudo; then SUDO="sudo"; fi
    if command_exists apt-get; then
        $SUDO apt-get update -y
        $SUDO apt-get install -y python3 python3-venv
    elif command_exists dnf; then
        $SUDO dnf install -y python3
    elif command_exists yum; then
        $SUDO yum install -y python3
    elif command_exists pacman; then
        $SUDO pacman -Sy --noconfirm python
    elif command_exists apk; then
        $SUDO apk add python3 py3-pip
    elif command_exists brew; then
        brew install "python@${CORETEX_MIN_PYTHON}"
    else
        echo -e "\033[1;31mERROR: unsupported package manager. $hint\033[0m" >&2
        return 1
    fi
    if ! python_version_available; then
        echo -e "\033[1;31mERROR: Python ${CORETEX_MIN_PYTHON}+ still unavailable after install. Try opening a new terminal or run ./setup.sh --docker.\033[0m" >&2
        return 1
    fi
}

print_next_steps() {
    cat <<'EOF'

Next steps:
  0. RESTART YOUR TERMINAL (or run: source ~/.bashrc / source ~/.zshrc)
  1. Run: ./ctx status
  2. Try: ./ctx task "Summarize this repository in five bullets"
  3. Re-run diagnostics anytime with: ./setup.sh --check

🔒 SECURITY NOTICE: CoreTex OS installs in "Safe-by-Default" (Advisory) mode.
To allow the agent to autonomously execute code, scripts, or terminal commands:
Open your `.env` file and set CORETEX_ENABLE_CODE_EXECUTION=true
EOF
}

confirm_default_yes() {
    local prompt="$1"
    if [ "${CORETEX_HEADLESS:-}" = "1" ]; then
        return 0
    fi
    read -r -p "$prompt (y/n) [y]: " reply
    reply=${reply:-y}
    [[ "$reply" =~ ^[Yy]$ ]]
}

install_uv_runtime() {
    if command_exists uv; then
        return 0
    fi
    if ! command_exists curl; then
        echo -e "\033[1;31mERROR: curl is required to install uv.\033[0m" >&2
        return 1
    fi
    if ! confirm_default_yes "The uv package manager is missing. Install it now?"; then
        echo -e "\033[1;31mAborting. uv is required for local installation.\033[0m" >&2
        return 1
    fi
    echo -e "\033[36m[*] Installing uv package manager...\033[0m"
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.local/bin:$HOME/.cargo/bin:$PATH"
    if ! command_exists uv; then
        echo -e "\033[1;31mERROR: uv installation completed but uv was not found in PATH. Restart your terminal or add ~/.local/bin to PATH.\033[0m" >&2
        return 1
    fi
}

install_deno_runtime() {
    if command_exists deno; then
        return 0
    fi
    if ! command_exists curl || ! command_exists unzip; then
        echo -e "\033[1;31mERROR: curl and unzip are required to install Deno.\033[0m" >&2
        return 1
    fi
    if ! confirm_default_yes "The Deno WASM sandbox runtime is missing. Install it now?"; then
        echo -e "\033[1;31mAborting. deno is required for local installation.\033[0m" >&2
        return 1
    fi
    echo -e "\033[36m[*] Installing Deno WASM sandbox runtime...\033[0m"
    curl -fsSL https://deno.land/install.sh | sh
    export PATH="$HOME/.deno/bin:$PATH"
    if ! command_exists deno; then
        echo -e "\033[1;31mERROR: Deno installation completed but deno was not found in PATH. Restart your terminal or add ~/.deno/bin to PATH.\033[0m" >&2
        return 1
    fi
}

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
    if ! command_exists "$util"; then
        MISSING_UTILS+=("$util")
    fi
done

if [ ${#MISSING_UTILS[@]} -ne 0 ]; then
    echo -e "\033[1;33m[!] Missing required system utilities: ${MISSING_UTILS[*]}\033[0m"
    PKG_MANAGER=""
    INSTALL_CMD=""
    UPDATE_CMD=""

    if command_exists apt-get; then
        PKG_MANAGER="apt"
        UPDATE_CMD="apt-get update -y"
        INSTALL_CMD="apt-get install -y ${MISSING_UTILS[*]}"
    elif command_exists dnf; then
        PKG_MANAGER="dnf"
        INSTALL_CMD="dnf install -y ${MISSING_UTILS[*]}"
    elif command_exists yum; then
        PKG_MANAGER="yum"
        INSTALL_CMD="yum install -y ${MISSING_UTILS[*]}"
    elif command_exists pacman; then
        PKG_MANAGER="pacman"
        INSTALL_CMD="pacman -Sy --noconfirm ${MISSING_UTILS[*]}"
    elif command_exists apk; then
        PKG_MANAGER="apk"
        INSTALL_CMD="apk add ${MISSING_UTILS[*]}"
    elif command_exists brew; then
        PKG_MANAGER="homebrew"
        INSTALL_CMD="brew install ${MISSING_UTILS[*]}"
    fi

    if [ -n "$PKG_MANAGER" ]; then
        SUDO=""
        if [ "$PKG_MANAGER" != "homebrew" ] && [ "$(id -u)" -ne 0 ] && command_exists sudo; then
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
            if [ "$PKG_MANAGER" != "homebrew" ] && [ "$(id -u)" -ne 0 ] && [ -z "$SUDO" ]; then
                echo -e "\033[1;31mCannot install system dependencies: non-root user and sudo is unavailable.\033[0m" >&2
                echo "Run manually as an admin/root user:" >&2
                if [ -n "$UPDATE_CMD" ]; then echo "  $UPDATE_CMD" >&2; fi
                echo "  $INSTALL_CMD" >&2
                exit 1
            fi
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
if command_exists docker; then
    if docker info >/dev/null 2>&1; then
        DOCKER_AVAILABLE=true
        if docker compose version >/dev/null 2>&1; then
            DOCKER_COMPOSE_AVAILABLE=true
            DOCKER_COMPOSE_CMD=(docker compose)
        elif command_exists docker-compose; then
            DOCKER_COMPOSE_AVAILABLE=true
            DOCKER_COMPOSE_CMD=(docker-compose)
        fi
    fi
fi

if [ "$CHECK_ONLY" = true ]; then
    CHECK_FAILED=false
    echo "Prerequisite check:"
    echo "  curl: $(command -v curl || echo missing)"
    echo "  unzip: $(command -v unzip || echo missing)"
    echo "  file: $(command -v file || echo missing)"
    echo "  python3_${CORETEX_MIN_PYTHON}_plus: $(python_version_available && echo true || echo false)"
    echo "  uv: $(command -v uv || echo missing)"
    echo "  deno: $(command -v deno || echo missing)"
    echo "  docker_engine: $DOCKER_AVAILABLE"
    echo "  docker_compose: $DOCKER_COMPOSE_AVAILABLE"
    if [ ${#MISSING_UTILS[@]} -ne 0 ]; then
        CHECK_FAILED=true
    fi
    if [ "$FORCE_DOCKER" = true ]; then
        if [ "$DOCKER_AVAILABLE" != true ] || [ "$DOCKER_COMPOSE_AVAILABLE" != true ]; then
            CHECK_FAILED=true
        fi
    elif [ "$FORCE_LOCAL" = true ]; then
        if ! python_version_available || ! command -v uv >/dev/null 2>&1 || ! command -v deno >/dev/null 2>&1; then
            CHECK_FAILED=true
        fi
    elif ! python_version_available || ! command -v uv >/dev/null 2>&1 || ! command -v deno >/dev/null 2>&1; then
        CHECK_FAILED=true
    fi
    if [ "$CHECK_FAILED" = true ]; then
        echo "Result: missing required prerequisites for the selected setup path."
        exit 1
    fi
    echo "Result: ready."
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
    if ! command_exists docker; then
        echo -e "\033[1;31mERROR: Docker is not installed. Install Docker Desktop/Engine and retry, or run ./setup.sh --local.\033[0m" >&2
        exit 1
    fi
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
    print_next_steps

    echo -e "[*] Booting Synaptic Genesis inside container context...\n"

    exec ./ctx --docker setup
fi

echo -e "\n[*] \033[1;36mInitializing Pure Local Environment...\033[0m"

install_python_runtime

install_uv_runtime
install_deno_runtime

mkdir -p logs System/config Meta

echo -e "\033[36m[*] Synchronizing CoreTex dependencies (this may take a moment)...\033[0m"
uv sync --all-extras

echo -e "\n[+] Local environment synchronized."
print_next_steps

echo -e "[*] Booting Synaptic Genesis...\n"
uv run python -m System.cli setup
