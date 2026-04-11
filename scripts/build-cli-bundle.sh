#!/bin/bash
#
# build-cli-bundle.sh
# Copies required files from jebat-core to packages/cli for npm publishing
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
CLI_DIR="$ROOT_DIR/packages/cli"
CORE_DIR="$ROOT_DIR/jebat-core"

echo "🔨 Building CLI bundle..."
echo "   Root: $ROOT_DIR"
echo "   Core: $CORE_DIR"
echo "   CLI:  $CLI_DIR"
echo ""

# Verify directories exist
if [ ! -d "$CORE_DIR" ]; then
  echo "❌ Error: jebat-core directory not found at $CORE_DIR"
  exit 1
fi

if [ ! -d "$CLI_DIR" ]; then
  echo "❌ Error: CLI package directory not found at $CLI_DIR"
  exit 1
fi

# Clean existing bundle files in CLI package (keep bin, lib, package.json)
echo "🧹 Cleaning existing bundle files..."
cd "$CLI_DIR"

# Remove old bundle files if they exist
rm -f AGENTS.md IDENTITY.md MEMORY.md ORCHESTRA.md SOUL.md TOOLS.md USER.md 2>/dev/null || true
rm -rf adapters vault skills 2>/dev/null || true

# Copy identity files
echo "📄 Copying identity files..."
COPY_FILES=(
  "AGENTS.md"
  "IDENTITY.md"
  "MEMORY.md"
  "ORCHESTRA.md"
  "SOUL.md"
  "TOOLS.md"
  "USER.md"
)

for file in "${COPY_FILES[@]}"; do
  if [ -f "$CORE_DIR/$file" ]; then
    cp "$CORE_DIR/$file" "$CLI_DIR/$file"
    echo "   ✓ Copied $file"
  else
    echo "   ⚠ Warning: $file not found in jebat-core"
  fi
done

# Copy adapters directory
echo "📦 Copying adapters..."
if [ -d "$CORE_DIR/adapters" ]; then
  cp -r "$CORE_DIR/adapters" "$CLI_DIR/adapters"
  echo "   ✓ Copied adapters/"
else
  echo "   ⚠ Warning: adapters directory not found in jebat-core"
fi

# Copy vault directory
echo "📦 Copying vault..."
if [ -d "$CORE_DIR/vault" ]; then
  cp -r "$CORE_DIR/vault" "$CLI_DIR/vault"
  echo "   ✓ Copied vault/"
else
  echo "   ⚠ Warning: vault directory not found in jebat-core"
fi

# Copy skills directory
echo "📦 Copying skills..."
if [ -d "$CORE_DIR/skills" ]; then
  cp -r "$CORE_DIR/skills" "$CLI_DIR/skills"
  echo "   ✓ Copied skills/"
else
  echo "   ⚠ Warning: skills directory not found in jebat-core"
fi

# Copy validate-workspace.ps1 if it exists
if [ -f "$CORE_DIR/validate-workspace.ps1" ]; then
  cp "$CORE_DIR/validate-workspace.ps1" "$CLI_DIR/validate-workspace.ps1"
  echo "   ✓ Copied validate-workspace.ps1"
fi

echo ""
echo "✅ CLI bundle built successfully!"
echo ""
echo "📊 Bundle contents:"
echo "   Identity files: ${#COPY_FILES[@]}"
echo "   Adapters: $(ls -1 "$CLI_DIR/adapters" 2>/dev/null | wc -l) files/dirs"
echo "   Vault: $(find "$CLI_DIR/vault" -type f 2>/dev/null | wc -l) files"
echo "   Skills: $(ls -1 "$CLI_DIR/skills" 2>/dev/null | wc -l) dirs"
echo ""
echo "Ready for npm publish!"
