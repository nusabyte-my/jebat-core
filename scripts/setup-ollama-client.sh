#!/bin/bash
###############################################################################
# Jebat Agent - VPS Setup Script
# Configures VPS to use central Ollama server
#
# Usage:
#   ssh my-vps 'bash -s' < scripts/setup-ollama-server.sh    # On Ollama server
#   ssh jebat-vps 'bash -s' < scripts/setup-ollama-client.sh # On client VPS
###############################################################################

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

OLLAMA_SERVER="${OLLAMA_SERVER:-72.62.255.206}"
OLLAMA_PORT="${OLLAMA_PORT:-11434}"

log() { echo -e "${BLUE}[$(date '+%H:%M:%S')]${NC} $1"; }
success() { echo -e "${GREEN}[✓]${NC} $1"; }
warn() { echo -e "${YELLOW}[⚠]${NC} $1"; }

echo ""
echo "==================================================================="
echo -e "${BLUE}JEBAT AGENT - OLLAMA CLIENT SETUP${NC}"
echo "==================================================================="
echo ""
log "Configuring this VPS to use Ollama server at ${OLLAMA_SERVER}:${OLLAMA_PORT}"

# Set environment variables
log "Setting OLLAMA_HOST environment variable..."
echo "OLLAMA_HOST=http://${OLLAMA_SERVER}:${OLLAMA_PORT}" | sudo tee -a /etc/environment > /dev/null
export OLLAMA_HOST=http://${OLLAMA_SERVER}:${OLLAMA_PORT}

# Add to shell profiles
grep -q "OLLAMA_HOST" ~/.bashrc 2>/dev/null || echo "export OLLAMA_HOST=http://${OLLAMA_SERVER}:${OLLAMA_PORT}" >> ~/.bashrc
grep -q "OLLAMA_HOST" ~/.zshrc 2>/dev/null || echo "export OLLAMA_HOST=http://${OLLAMA_SERVER}:${OLLAMA_PORT}" >> ~/.zshrc 2>/dev/null || true

success "Environment variables configured"

# Test connection
log "Testing connection to Ollama server..."
if curl -s --connect-timeout 5 http://${OLLAMA_SERVER}:${OLLAMA_PORT}/api/tags > /dev/null; then
    success "Connected to Ollama server!"
    
    # List available models
    echo ""
    echo -e "${GREEN}Available Models:${NC}"
    curl -s http://${OLLAMA_SERVER}:${OLLAMA_PORT}/api/tags | python3 -c "
import sys, json
data = json.load(sys.stdin)
for m in data.get('models', []):
    name = m['name']
    size = m.get('size', 0) / 1e9
    print(f'  ✓ {name:<25} ({size:.1f} GB)')
" 2>/dev/null || echo "  (Could not parse model list)"
else
    warn "Could not connect to Ollama server at ${OLLAMA_SERVER}:${OLLAMA_PORT}"
    echo "  Check firewall rules and Ollama service status"
fi

# Configure Jebat Gateway to use remote Ollama
log "Updating Jebat Gateway configuration..."
JEBAT_CONFIG="$HOME/.jebat/jebat-gateway.json"

if [ -f "$JEBAT_CONFIG" ]; then
    python3 << PYTHON
import json

config_file = "${JEBAT_CONFIG}"

with open(config_file, 'r') as f:
    config = json.load(f)

# Update model provider to use remote Ollama
config['agents']['defaults']['model']['providers'] = {
    "ollama": {
        "endpoint": "http://${OLLAMA_SERVER}:${OLLAMA_PORT}/v1",
        "models": [
            "qwen2.5:14b",
            "hermes3:latest",
            "phi3:latest",
            "mistral:latest",
            "llama3.1:8b"
        ],
        "default_model": "qwen2.5:14b",
        "api_key": "local"
    }
}

config['agents']['defaults']['model']['primary'] = "ollama/qwen2.5:14b"
config['agents']['defaults']['model']['fallbacks'] = [
    "ollama/hermes3:latest",
    "ollama/phi3:latest"
]

with open(config_file, 'w') as f:
    json.dump(config, f, indent=2)

print("Gateway config updated")
PYTHON
    
    success "Jebat Gateway configured"
else
    warn "Jebat Gateway config not found. Run 'npx jebat-agent --full' first."
fi

echo ""
echo "==================================================================="
echo -e "${GREEN}SETUP COMPLETE${NC}"
echo "==================================================================="
echo ""
echo -e "${CYAN}Architecture:${NC}"
echo "  This VPS      → Client (Jebat Gateway + UI)"
echo "  ${OLLAMA_SERVER} → Server (Ollama + Models)"
echo ""
echo -e "${CYAN}Available Models:${NC}"
echo "  • qwen2.5:14b     (Best performance)"
echo "  • hermes3:latest  (Complex reasoning)"
echo "  • phi3:latest     (Fast responses)"
echo "  • mistral:latest  (Balanced)"
echo "  • llama3.1:8b     (General purpose)"
echo "  • codellama:7b    (Coding)"
echo "  • tinyllama:latest (Lightweight)"
echo ""
echo -e "${CYAN}Next Steps:${NC}"
echo "  1. Start Jebat Gateway: npx jebat-gateway start"
echo "  2. Open UI: http://localhost:18789"
echo "  3. Models are served remotely from ${OLLAMA_SERVER}"
echo ""
