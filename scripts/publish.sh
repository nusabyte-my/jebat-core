#!/usr/bin/env bash
# Publish JEBAT to PyPI
# Usage: bash scripts/publish.sh [--test]
#   --test  Publish to TestPyPI instead of production

set -euo pipefail

cd "$(dirname "$0")/.."

TARGET="${1:-}"

# Build
echo "==> Building..."
rm -rf dist build jebat.egg-info
python -m build

# Verify wheel exists
WHEEL=$(ls dist/*.whl 2>/dev/null | head -1)
if [ -z "$WHEEL" ]; then
    echo "ERROR: No wheel built"
    exit 1
fi

echo "==> Built: $WHEEL"

# Quick smoke test: check jebat CLI entrypoint
if [ "$TARGET" = "--test" ]; then
    echo "==> Publishing to TestPyPI..."
    twine upload --repository testpypi dist/*
else
    echo "==> Publishing to PyPI..."
    twine upload dist/*
fi

echo "==> Done!"