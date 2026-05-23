#!/usr/bin/env bash
set -e

echo -e "\033[1;36m🧠 Bootstrapping Brain Core...\033[0m"

# 1. Ensure the ultra-fast 'uv' package manager is installed
if ! command -v uv &> /dev/null; then
    echo -e "\033[0;33m[⚡] Installing 'uv' package manager...\033[0m"
    curl -LsSf https://astral.sh/uv/install.sh | sh
    source "$HOME/.cargo/env"
fi

# 2. Instantly resolve and hydrate the minimal core environment
echo -e "\033[0;36m[⚡] Syncing core neural pathways...\033[0m"
uv sync

# 3. Hand off execution to the Interactive Setup Wizard
echo -e "\033[1;32m[🧠] Awakening...\033[0m"
exec uv run python -m System.core.onboarding.genesis
