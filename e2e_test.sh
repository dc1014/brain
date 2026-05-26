#!/usr/bin/env bash
set -e

echo "Running E2E Clean Host Verification..."
./setup.sh --help
./setup.sh --check || true
CORETEX_HEADLESS=1 ./setup.sh
./ctx --help
./ctx status
./ctx task --help
uv run pytest -q

echo "✅ Clean Host E2E Passed!"
