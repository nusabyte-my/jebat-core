#!/usr/bin/env bash
# Publish JEBATCore npm package
# Usage: bash scripts/publish-npm.sh [--test]
#   --test  Dry-run (npm pack --dry-run)

set -euo pipefail

cd "$(dirname "$0")/../jebatcore"

TARGET="${1:-}"

echo "==> Packing jebatcore..."
npm pack --dry-run

if [ "$TARGET" = "--test" ]; then
    echo "==> Dry-run only — no publish"
    exit 0
fi

echo ""
echo "Ready to publish? (Ctrl+C to cancel)"
echo "  pkg: jebatcore@$(node -e "console.log(require('./package.json').version)")"
echo ""
read -rp "Press Enter to publish (or Ctrl+C to abort)... " _unused

echo "==> Publishing to npm..."
npm publish

echo "==> Done! Published jebatcore@$(node -e "console.log(require('./package.json').version)")"