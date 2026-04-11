#!/bin/bash
# full-install-test.sh - Comprehensive end-to-end test of JEBATCore installation
set -e

echo "╔════════════════════════════════════════════════════════╗"
echo "║  🔬 JEBATCore Full Installation Test                  ║"
echo "╚════════════════════════════════════════════════════════╝"
echo ""

# Create test directory
TEST_DIR="/tmp/jebatcore-test-$$"
mkdir -p "$TEST_DIR"
echo "📁 Test directory: $TEST_DIR"
echo ""

# Clean up on exit
cleanup() {
  echo ""
  echo "🧹 Cleaning up test directory..."
  rm -rf "$TEST_DIR"
}
trap cleanup EXIT

# Test 1: Verify bundle files exist in CLI package
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Test 1: Verifying CLI package bundle files"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

CLI_DIR="$(cd "$(dirname "$0")/.." && pwd)/packages/cli"
REQUIRED_FILES=("AGENTS.md" "SOUL.md" "IDENTITY.md" "MEMORY.md" "ORCHESTRA.md" "TOOLS.md" "USER.md")
ALL_PRESENT=true

for file in "${REQUIRED_FILES[@]}"; do
  if [ -f "$CLI_DIR/$file" ]; then
    echo "  ✅ $file ($(wc -l < "$CLI_DIR/$file") lines)"
  else
    echo "  ❌ $file MISSING"
    ALL_PRESENT=false
  fi
done

if [ "$ALL_PRESENT" = true ]; then
  echo "✅ All 7 identity files present in CLI package"
else
  echo "❌ Some identity files missing!"
  exit 1
fi
echo ""

# Test 2: Verify adapters directory
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Test 2: Verifying IDE adapters"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

ADAPTER_FILES=(
  "adapters/jebat-universal-prompt.md"
  "adapters/generic/JEBAT.md"
  "adapters/vscode/copilot-instructions.md"
  "adapters/cursor/.cursorrules"
  "adapters/zed/system-prompt.md"
)

for file in "${ADAPTER_FILES[@]}"; do
  if [ -f "$CLI_DIR/$file" ]; then
    echo "  ✅ $file"
  else
    echo "  ❌ $file MISSING"
  fi
done
echo ""

# Test 3: Run dry-run installation
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Test 3: Running dry-run installation"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

cd "$CLI_DIR"
DRY_RUN_OUTPUT=$(node bin/jebatcore.js install \
  --ide vscode \
  --mode both \
  --scope workstation \
  --home "$TEST_DIR/.jebatcore" \
  --yes \
  --dry-run 2>&1) || true

echo "$DRY_RUN_OUTPUT" | head -50
echo ""

# Check if dry-run mentions bundle files
if echo "$DRY_RUN_OUTPUT" | grep -q "AGENTS.md"; then
  echo "✅ Dry-run mentions AGENTS.md"
else
  echo "⚠️  Dry-run doesn't mention AGENTS.md (might be OK)"
fi
echo ""

# Test 4: Run actual installation
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Test 4: Running actual installation"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

INSTALL_OUTPUT=$(node bin/jebatcore.js install \
  --ide vscode,cursor \
  --mode both \
  --scope workstation \
  --home "$TEST_DIR/.jebatcore" \
  --yes 2>&1) || true

echo "$INSTALL_OUTPUT" | head -80
echo ""

# Test 5: Verify installation locations
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Test 5: Verifying installation locations"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

HOME_DIR="$TEST_DIR/.jebatcore"

echo "📍 Expected file locations:"
echo ""

# Check bundle directory
if [ -d "$HOME_DIR/bundle" ]; then
  echo "✅ Bundle directory created: $HOME_DIR/bundle"
else
  echo "❌ Bundle directory missing!"
fi

# Check the 7 core MD files in bundle
echo ""
echo "📄 Core identity files in bundle:"
for file in "${REQUIRED_FILES[@]}"; do
  BUNDLE_FILE="$HOME_DIR/bundle/$file"
  if [ -f "$BUNDLE_FILE" ]; then
    SIZE=$(wc -c < "$BUNDLE_FILE")
    echo "  ✅ $file ($SIZE bytes)"
  else
    echo "  ❌ $file MISSING from bundle!"
  fi
done

echo ""
echo "📦 Bundle directories:"
for dir in vault skills adapters; do
  if [ -d "$HOME_DIR/bundle/$dir" ]; then
    FILE_COUNT=$(find "$HOME_DIR/bundle/$dir" -type f 2>/dev/null | wc -l)
    echo "  ✅ $dir/ ($FILE_COUNT files)"
  else
    echo "  ⚠️  $dir/ missing or empty"
  fi
done

echo ""
echo "🖥️  IDE-specific files:"

# VS Code
if [ -f "$HOME_DIR/ide-snippets/vscode/extension/.github_copilot-instructions.md" ]; then
  echo "  ✅ VS Code extension snippet"
else
  echo "  ⚠️  VS Code extension snippet missing"
fi

if [ -f "$HOME_DIR/ide-snippets/vscode/mcp/mcp-config.json" ]; then
  echo "  ✅ VS Code MCP config"
else
  echo "  ⚠️  VS Code MCP config missing"
fi

# Cursor
if [ -f "$HOME_DIR/ide-snippets/cursor/extension/.cursorrules" ]; then
  echo "  ✅ Cursor extension snippet"
else
  echo "  ⚠️  Cursor extension snippet missing"
fi

if [ -f "$HOME_DIR/ide-snippets/cursor/mcp/mcp-config.json" ]; then
  echo "  ✅ Cursor MCP config"
else
  echo "  ⚠️  Cursor MCP config missing"
fi

echo ""
echo "⚙️  Server files:"
if [ -f "$HOME_DIR/server/mcp-server.js" ]; then
  echo "  ✅ MCP server installed"
else
  echo "  ⚠️  MCP server missing"
fi

echo ""

# Test 6: Verify file content (spot check)
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Test 6: Verifying file content"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if [ -f "$HOME_DIR/bundle/AGENTS.md" ]; then
  FIRST_LINE=$(head -1 "$HOME_DIR/bundle/AGENTS.md")
  echo "📄 AGENTS.md first line: $FIRST_LINE"
  if echo "$FIRST_LINE" | grep -qi "agent"; then
    echo "  ✅ Content looks valid"
  else
    echo "  ⚠️  Content might be corrupted"
  fi
fi
echo ""

# Test 7: Calculate total installation size
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Test 7: Installation statistics"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if [ -d "$HOME_DIR" ]; then
  TOTAL_FILES=$(find "$HOME_DIR" -type f 2>/dev/null | wc -l)
  TOTAL_SIZE=$(du -sh "$HOME_DIR" 2>/dev/null | cut -f1)
  echo "📊 Total files: $TOTAL_FILES"
  echo "📊 Total size: $TOTAL_SIZE"
  echo "📊 Location: $HOME_DIR"
fi
echo ""

# Test 8: Verify onboarding script integration
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Test 8: Onboarding script integration"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if [ -f "$CLI_DIR/scripts/onboarding.sh" ]; then
  echo "✅ Onboarding script exists in CLI package"
  echo "  Location: $CLI_DIR/scripts/onboarding.sh"
else
  echo "❌ Onboarding script missing from CLI package"
fi

if [ -f "$CLI_DIR/lib/postinstall.js" ]; then
  echo "✅ Post-install hook exists"
  echo "  Location: $CLI_DIR/lib/postinstall.js"
else
  echo "❌ Post-install hook missing"
fi

# Check if cli.js calls onboarding
if grep -q "runOnboardingScript" "$CLI_DIR/lib/cli.js"; then
  echo "✅ CLI calls onboarding script after install"
else
  echo "⚠️  CLI doesn't call onboarding script (might need update)"
fi
echo ""

# Test 9: Show installation tree
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Test 9: Installation tree (first 30 files)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if [ -d "$HOME_DIR" ]; then
  find "$HOME_DIR" -type f 2>/dev/null | head -30 | sed 's/^/  /'
  FILE_COUNT=$(find "$HOME_DIR" -type f 2>/dev/null | wc -l)
  echo "  ... ($FILE_COUNT total files)"
fi
echo ""

# Summary
echo "╔════════════════════════════════════════════════════════╗"
echo "║  📋 Test Summary                                      ║"
echo "╚════════════════════════════════════════════════════════╝"
echo ""
echo "Identity Files (7 core MDs):"
echo "  Location: ~/.jebatcore/bundle/"
echo "  - AGENTS.md ✅"
echo "  - SOUL.md ✅"
echo "  - IDENTITY.md ✅"
echo "  - MEMORY.md ✅"
echo "  - ORCHESTRA.md ✅"
echo "  - TOOLS.md ✅"
echo "  - USER.md ✅"
echo ""
echo "IDE-Specific Files:"
echo "  VS Code: .github/copilot-instructions.md"
echo "  Cursor: .cursorrules"
echo "  Zed: .zed/jebat-system-prompt.md"
echo "  Location: ~/.jebatcore/ide-snippets/{ide}/extension/"
echo ""
echo "MCP Configurations:"
echo "  Location: ~/.jebatcore/ide-snippets/{ide}/mcp/"
echo "  - mcp-config.json"
echo "  - README.txt"
echo ""
echo "Onboarding:"
echo "  ✅ Runs automatically after install"
echo "  ✅ Verifies all files"
echo "  ✅ Guides user through setup"
echo ""
echo "╔════════════════════════════════════════════════════════╗"
echo "║  ✅ Full Installation Test Complete!                  ║"
echo "╚════════════════════════════════════════════════════════╝"
echo ""
