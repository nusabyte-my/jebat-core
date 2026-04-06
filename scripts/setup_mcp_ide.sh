#!/bin/bash
# JEBAT MCP IDE Setup Script
# Automatically configures MCP for your IDE

set -e

echo "🗡️ JEBAT MCP IDE Setup"
echo "======================"
echo ""

# Check if JEBAT is installed
if ! python -c "import jebat" 2>/dev/null; then
    echo "❌ JEBAT not installed. Installing..."
    pip install -e .
fi

# Check if MCP is available
if ! python -c "from mcp.server import Server" 2>/dev/null; then
    echo "📦 Installing MCP library..."
    pip install mcp
fi

# Detect IDE
echo ""
echo "Detecting IDE..."

IDE_CONFIG_DIR=""
IDE_NAME=""

# VSCode
if [ -d "$HOME/.vscode" ] || [ -d "$HOME/.vscode-insiders" ]; then
    IDE_NAME="VSCode"
    IDE_CONFIG_DIR="$HOME/.vscode"
    echo "✓ Found VSCode"
fi

# Zed
if [ -d "$HOME/.config/zed" ]; then
    IDE_NAME="Zed"
    IDE_CONFIG_DIR="$HOME/.config/zed"
    echo "✓ Found Zed"
fi

# Cursor
if [ -d "$HOME/.cursor" ]; then
    IDE_NAME="Cursor"
    IDE_CONFIG_DIR="$HOME/.cursor"
    echo "✓ Found Cursor"
fi

if [ -z "$IDE_NAME" ]; then
    echo "⚠️  No supported IDE found. Manual configuration required."
    echo ""
    echo "See docs/MCP_INTEGRATION_GUIDE.md for manual setup instructions."
    exit 1
fi

echo ""
echo "Configuring MCP for $IDE_NAME..."

# Create config directory
mkdir -p "$IDE_CONFIG_DIR"

# Copy configuration
case $IDE_NAME in
    "VSCode")
        cp ide-configs/vscode/mcp.json "$IDE_CONFIG_DIR/mcp.json"
        cp ide-configs/vscode/keybindings.json "$IDE_CONFIG_DIR/keybindings.json"
        echo "✓ VSCode configuration copied"
        echo "  Config: $IDE_CONFIG_DIR/mcp.json"
        echo "  Keybindings: $IDE_CONFIG_DIR/keybindings.json"
        ;;
    "Zed")
        cp ide-configs/zed/settings.json "$IDE_CONFIG_DIR/settings.json"
        echo "✓ Zed configuration copied"
        echo "  Config: $IDE_CONFIG_DIR/settings.json"
        ;;
    "Cursor")
        mkdir -p "$IDE_CONFIG_DIR/.cursor"
        cp ide-configs/cursor/mcp.json "$IDE_CONFIG_DIR/.cursor/mcp.json"
        echo "✓ Cursor configuration copied"
        echo "  Config: $IDE_CONFIG_DIR/.cursor/mcp.json"
        ;;
esac

# Set environment variable
echo ""
echo "📝 Add this to your shell profile (.bashrc, .zshrc, etc.):"
echo ""
echo "  export JEBAT_API_KEY='your_api_key_here'"
echo "  export JEBAT_MODE='assistant'"
echo ""

# Test MCP server
echo "🧪 Testing MCP server..."
if python -m jebat.mcp.server --help >/dev/null 2>&1; then
    echo "✓ MCP server is working!"
else
    echo "⚠️  MCP server test failed. Check installation."
fi

echo ""
echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Set your JEBAT_API_KEY environment variable"
echo "2. Restart $IDE_NAME"
echo "3. Open a project and try @jebat in chat"
echo ""
echo "For more info: docs/MCP_INTEGRATION_GUIDE.md"
