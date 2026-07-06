#!/bin/bash
# deploy_model.sh — Upload GGUF to .206 and create Ollama model
# Usage: bash deploy_model.sh <path-to-gguf-file>
#
# Prerequisites:
#   - SSH key configured for root@72.62.255.206
#   - GGUF file from Colab (downloaded to local machine)

set -e

GGUF_PATH="${1:-jebat-builder-Q4_K_M.gguf}"
SERVER="root@72.62.255.206"
REMOTE_PATH="/tmp/jebat-builder.gguf"

if [ ! -f "$GGUF_PATH" ]; then
    echo "Error: GGUF file not found: $GGUF_PATH"
    echo "Usage: bash deploy_model.sh <path-to-gguf-file>"
    exit 1
fi

SIZE=$(du -h "$GGUF_PATH" | cut -f1)
echo "=== JEBAT-Builder Model Deployment ==="
echo "File: $GGUF_PATH ($SIZE)"
echo "Server: $SERVER"
echo ""

# Step 1: Upload GGUF
echo "[1/3] Uploading GGUF to server..."
scp "$GGUF_PATH" "$SERVER:$REMOTE_PATH"
echo "  Done."

# Step 2: Create Modelfile on server
echo "[2/3] Creating Modelfile on server..."
ssh "$SERVER" "cat > /tmp/Modelfile << 'EOF'
FROM /tmp/jebat-builder.gguf

PARAMETER temperature 0.7
PARAMETER top_p 0.9
PARAMETER num_ctx 4096

SYSTEM \"\"\"You are JEBAT-Builder, a specialized coding AI assistant created by NusaByte. You are part of the JEBAT Sovereign AI Platform v7.0. Write clean, production-ready code. Follow JEBAT coding conventions. Prefer dark-themed terminal UIs. Reference DESIGN.md tokens for UI code. Always consider security implications.\"\"\"
EOF"
echo "  Done."

# Step 3: Create Ollama model
echo "[3/3] Creating Ollama model..."
ssh "$SERVER" "ollama create jebat-builder -f /tmp/Modelfile"
echo "  Done."

# Verify
echo ""
echo "=== Verifying ==="
curl -s https://jebat.online/ollama/api/tags | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    models = [m['name'] for m in data.get('models', [])]
    print(f'Models available: {models}')
    if 'jebat-builder' in [m.split(':')[0] for m in models]:
        print('SUCCESS: jebat-builder model is live!')
    else:
        print('WARNING: jebat-builder not found in models list')
except:
    print('ERROR: Could not verify model status')
"

echo ""
echo "=== Deployment Complete ==="
echo "Test it:"
echo "  curl https://jebat.online/ollama/v1/chat/completions \\"
echo "    -H 'Content-Type: application/json' \\"
echo "    -d '{\"model\":\"jebat-builder\",\"messages\":[{\"role\":\"user\",\"content\":\"Create a FastAPI endpoint\"}]}'"
echo ""
echo "Or use with JEBAT CLI:"
echo "  jebat chat --model jebat-builder \"Create a REST API\""
