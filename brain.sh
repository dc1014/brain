#!/bin/bash
# ⚡ ZERO-DEBT: Unix Spinal Cord
# Automatically calculates its own absolute path to bypass environment traps
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR"

# Bypass 'uv' completely. Use the absolute virtual environment!
./.venv/bin/python -m System.cli "$@"
