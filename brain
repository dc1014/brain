#!/bin/bash
# ⚡ ZERO-DEBT: Unix Spinal Cord
# Automatically calculates its own absolute path to bypass environment traps
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR"

# 1. If the user explicitly built the Docker sandbox, route through containment
if command -v docker &> /dev/null && docker image inspect brain-os &> /dev/null; then
    exec docker compose run --rm brain "$@"
fi

# 2. Otherwise, route directly to the lightning-fast local virtual environment
exec ./.venv/bin/python -m System.cli "$@"
