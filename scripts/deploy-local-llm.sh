#!/bin/bash
###############################################################################
# Jebat Agent - VPS Local LLM Deployment Script
# Installs AirLLM + Local Models (Hermes3, Gemma, and better alternatives)
# 
# Usage:
#   chmod +x scripts/deploy-local-llm.sh
#   ./scripts/deploy-local-llm.sh [--model hermes3|gemma|phi|qwen|all]
#
# Tested: Ubuntu 22.04/24.04, 16GB+ RAM, 4GB+ VRAM (optional)
###############################################################################

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# Configuration
JEBAT_DIR="$HOME/.jebat"
MODELS_DIR="$JEBAT_DIR/models"
VENV_DIR="$JEBAT_DIR/venv-llm"
LOG_FILE="$JEBAT_DIR/logs/llm-setup.log"

# Default model
MODEL_CHOICE="${1:---model all}"

# Functions
log() {
    echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1" | tee -a "$LOG_FILE"
}

success() {
    echo -e "${GREEN}[✓]${NC} $1" | tee -a "$LOG_FILE"
}

warn() {
    echo -e "${YELLOW}[⚠]${NC} $1" | tee -a "$LOG_FILE"
}

error() {
    echo -e "${RED}[✗]${NC} $1" | tee -a "$LOG_FILE"
}

info() {
    echo -e "${CYAN}[ℹ]${NC} $1" | tee -a "$LOG_FILE"
}

# Check system requirements
check_requirements() {
    log "Checking system requirements..."
    
    # Check RAM
    TOTAL_RAM_MB=$(free -m | awk '/^Mem:/{print $2}')
    if [ "$TOTAL_RAM_MB" -lt 8000 ]; then
        warn "System RAM: ${TOTAL_RAM_MB}MB (recommended: 16GB+)"
        warn "AirLLM can work with less RAM but performance will be limited"
    else
        success "System RAM: ${TOTAL_RAM_MB}MB"
    fi
    
    # Check disk space
    DISK_AVAIL_GB=$(df -BG / | awk 'NR==2{print $4}' | tr -d 'G')
    if [ "$DISK_AVAIL_GB" -lt 20 ]; then
        error "Insufficient disk space: ${DISK_AVAIL_GB}GB (need 20GB+)"
        exit 1
    else
        success "Disk space: ${DISK_AVAIL_GB}GB available"
    fi
    
    # Check GPU (optional)
    if command -v nvidia-smi &> /dev/null; then
        GPU_MEM=$(nvidia-smi --query-gpu=memory.total --format=csv,noheader,nounits | head -1)
        success "GPU detected: ${GPU_MEM}MB VRAM"
        HAS_GPU=true
    else
        warn "No GPU detected - will use CPU mode (slower but functional)"
        HAS_GPU=false
    fi
    
    # Check Python
    if ! command -v python3 &> /dev/null; then
        error "Python 3 not found"
        exit 1
    fi
    
    PYTHON_VERSION=$(python3 --version | awk '{print $2}')
    success "Python: $PYTHON_VERSION"
}

# Install system dependencies
install_system_deps() {
    log "Installing system dependencies..."
    
    sudo apt-get update -qq
    
    # Core dependencies
    sudo apt-get install -y -qq \
        python3-pip \
        python3-venv \
        git \
        curl \
        wget \
        build-essential \
        gcc \
        g++ \
        libgl1 \
        libglib2.0-0 \
        >/dev/null 2>&1
    
    success "System dependencies installed"
}

# Create Python virtual environment
setup_venv() {
    log "Setting up Python virtual environment..."
    
    mkdir -p "$JEBAT_DIR"
    
    if [ -d "$VENV_DIR" ]; then
        warn "Virtual environment exists, updating..."
    else
        python3 -m venv "$VENV_DIR"
        success "Virtual environment created at $VENV_DIR"
    fi
    
    # Activate venv
    source "$VENV_DIR/bin/activate"
    
    # Upgrade pip
    pip install --upgrade pip --quiet
    
    success "Python environment ready"
}

# Install AirLLM and dependencies
install_airllm() {
    log "Installing AirLLM and dependencies..."
    
    source "$VENV_DIR/bin/activate"
    
    # Core ML libraries
    pip install --quiet \
        torch \
        torchvision \
        torchaudio \
        transformers \
        accelerate \
        bitsandbytes \
        safetensors \
        huggingface-hub
    
    # AirLLM - runs LLMs with minimal RAM
    pip install --quiet airllm
    
    # Additional utilities
    pip install --quiet \
        sentencepiece \
        protobuf \
        peft \
        optimum
    
    # GPU support (if available)
    if [ "$HAS_GPU" = true ]; then
        log "Installing GPU support..."
        pip install --quiet flash-attn --no-build-isolation 2>/dev/null || \
            warn "flash-attn installation failed (optional)"
    fi
    
    success "AirLLM and dependencies installed"
}

# Download and setup Hermes3 model
setup_hermes3() {
    log "Setting up Hermes3 model..."
    
    source "$VENV_DIR/bin/activate"
    
    HERMES_DIR="$MODELS_DIR/hermes3-8b"
    
    if [ -d "$HERMES_DIR" ]; then
        warn "Hermes3 model already exists at $HERMES_DIR"
        read -p "Redownload? (y/N): " -r
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            success "Using existing Hermes3 model"
            return
        fi
    fi
    
    mkdir -p "$HERMES_DIR"
    
    # Download Hermes3 (using transformers + AirLLM)
    python3 << 'PYTHON_SCRIPT'
from transformers import AutoTokenizer, AutoModelForCausalLM
from airllm import AutoModel
import os

model_name = "NousResearch/Hermes-3-Llama-3.1-8B"
model_dir = os.path.expanduser("~/.jebat/models/hermes3-8b")

print(f"Downloading {model_name}...")
print("This may take a while (~16GB download)")

# Download tokenizer
tokenizer = AutoTokenizer.from_pretrained(
    model_name,
    cache_dir=model_dir,
    trust_remote_code=True
)

# Download model with 4-bit quantization for efficiency
model = AutoModel.from_pretrained(
    model_name,
    cache_dir=model_dir,
    compression='4bit',  # 4-bit quantization
    trust_remote_code=True
)

print(f"Model saved to {model_dir}")
PYTHON_SCRIPT
    
    success "Hermes3 model setup complete"
}

# Download and setup Gemma 4 model via Ollama
setup_gemma() {
    log "Setting up Gemma 4 model (via Ollama)..."

    source "$VENV_DIR/bin/activate"

    GEMMA_DIR="$MODELS_DIR/gemma4"

    if [ -d "$GEMMA_DIR" ]; then
        warn "Gemma 4 model already exists at $GEMMA_DIR"
        read -p "Redownload? (y/N): " -r
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            success "Using existing Gemma 4 model"
            return
        fi
    fi

    mkdir -p "$GEMMA_DIR"

    # Install Ollama if not present
    if ! command -v ollama &> /dev/null; then
        log "Installing Ollama..."
        curl -fsSL https://ollama.com/install.sh | sh
        success "Ollama installed"
    fi

    # Start Ollama service
    log "Starting Ollama service..."
    ollama serve &
    sleep 3

    # Pull Gemma 4 with 4-bit quantization (default in Ollama)
    log "Downloading Gemma 4 from Ollama library..."
    log "This may take a while (~5-9GB download depending on variant)"

    # Default is 4-bit quantized, ~5GB
    ollama pull gemma4 2>&1 | tee -a "$LOG_FILE"

    success "Gemma 4 model setup complete"
}

# Better alternatives: Phi-3 Mini (Microsoft)
setup_phi3() {
    log "Setting up Phi-3 Mini (RECOMMENDED for local deployment)..."
    
    source "$VENV_DIR/bin/activate"
    
    PHI_DIR="$MODELS_DIR/phi-3-mini"
    
    if [ -d "$PHI_DIR" ]; then
        warn "Phi-3 model already exists at $PHI_DIR"
        read -p "Redownload? (y/N): " -r
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            success "Using existing Phi-3 model"
            return
        fi
    fi
    
    mkdir -p "$PHI_DIR"
    
    python3 << 'PYTHON_SCRIPT'
from transformers import AutoTokenizer, AutoModelForCausalLM
from airllm import AutoModel
import os

# Phi-3 Mini 3.8B - excellent performance/size ratio
model_name = "microsoft/Phi-3-mini-4k-instruct"
model_dir = os.path.expanduser("~/.jebat/models/phi-3-mini")

print(f"Downloading {model_name}...")
print("This may take a while (~8GB download)")
print("Phi-3 Mini offers better performance than Gemma 2B")

tokenizer = AutoTokenizer.from_pretrained(
    model_name,
    cache_dir=model_dir,
    trust_remote_code=True
)

model = AutoModel.from_pretrained(
    model_name,
    cache_dir=model_dir,
    compression='4bit',
    trust_remote_code=True
)

print(f"Model saved to {model_dir}")
PYTHON_SCRIPT
    
    success "Phi-3 Mini model setup complete"
}

# Better alternative: Qwen2.5 (Alibaba)
setup_qwen() {
    log "Setting up Qwen2.5 (BEST for local deployment)..."
    
    source "$VENV_DIR/bin/activate"
    
    QWEN_DIR="$MODELS_DIR/qwen2.5-3b"
    
    if [ -d "$QWEN_DIR" ]; then
        warn "Qwen2.5 model already exists at $QWEN_DIR"
        read -p "Redownload? (y/N): " -r
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            success "Using existing Qwen2.5 model"
            return
        fi
    fi
    
    mkdir -p "$QWEN_DIR"
    
    python3 << 'PYTHON_SCRIPT'
from transformers import AutoTokenizer, AutoModelForCausalLM
from airllm import AutoModel
import os

# Qwen2.5 3B - current best for local deployment
model_name = "Qwen/Qwen2.5-3B-Instruct"
model_dir = os.path.expanduser("~/.jebat/models/qwen2.5-3b")

print(f"Downloading {model_name}...")
print("This may take a while (~7GB download)")
print("Qwen2.5 3B offers state-of-the-art performance for its size")

tokenizer = AutoTokenizer.from_pretrained(
    model_name,
    cache_dir=model_dir
)

model = AutoModel.from_pretrained(
    model_name,
    cache_dir=model_dir,
    compression='4bit'
)

print(f"Model saved to {model_dir}")
PYTHON_SCRIPT
    
    success "Qwen2.5 model setup complete"
}

# Create model launcher script
create_model_launcher() {
    log "Creating model launcher scripts..."
    
    mkdir -p "$JEBAT_DIR/bin"
    
    # Main launcher
    cat > "$JEBAT_DIR/bin/run-model.sh" << 'EOF'
#!/bin/bash
###############################################################################
# Jebat Local Model Launcher
# Usage: ~/.jebat/bin/run-model.sh [model_name] [port]
#
# Models: hermes3, gemma, phi3, qwen
# Port: default 8080
###############################################################################

MODEL_NAME="${1:-qwen}"
PORT="${2:-8080}"
JEBAT_DIR="$HOME/.jebat"
VENV_DIR="$JEBAT_DIR/venv-llm"

source "$VENV_DIR/bin/activate"

case "$MODEL_NAME" in
    hermes3)
        MODEL_PATH="$JEBAT_DIR/models/hermes3-8b"
        MODEL_ID="NousResearch/Hermes-3-Llama-3.1-8B"
        ;;
    gemma|gemma4)
        MODEL_PATH="$JEBAT_DIR/models/gemma4"
        MODEL_ID="gemma4"
        USE_OLLAMA=true
        ;;
    phi3)
        MODEL_PATH="$JEBAT_DIR/models/phi-3-mini"
        MODEL_ID="microsoft/Phi-3-mini-4k-instruct"
        ;;
    qwen)
        MODEL_PATH="$JEBAT_DIR/models/qwen2.5-3b"
        MODEL_ID="Qwen/Qwen2.5-3B-Instruct"
        ;;
    *)
        echo "Unknown model: $MODEL_NAME"
        echo "Available: hermes3, gemma4, phi3, qwen"
        exit 1
        ;;
esac

echo "Starting $MODEL_NAME on port $PORT..."
echo "Model: $MODEL_ID"
echo "Path: $MODEL_PATH"
echo ""

if [ "$USE_OLLAMA" = true ]; then
    # Use Ollama API for Gemma 4
    python3 << PYTHON
from flask import Flask, request, jsonify
import subprocess
import json

app = Flask(__name__)

@app.route('/health', methods=['GET'])
def health():
    return jsonify({
        "status": "healthy",
        "model": "${MODEL_ID}",
        "port": ${PORT},
        "backend": "ollama"
    })

@app.route('/v1/chat/completions', methods=['POST'])
def chat_completion():
    data = request.json
    messages = data.get('messages', [])
    
    # Call Ollama API
    result = subprocess.run(
        ['ollama', 'chat', '${MODEL_ID}', '--messages', json.dumps(messages)],
        capture_output=True,
        text=True
    )
    
    response = result.stdout.strip()
    
    return jsonify({
        "choices": [{
            "message": {
                "role": "assistant",
                "content": response
            }
        }]
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=${PORT})
PYTHON
else
    # Use AirLLM for other models
    python3 << PYTHON
from airllm import AutoModel
from transformers import AutoTokenizer
from flask import Flask, request, jsonify
import os

app = Flask(__name__)

# Load model
print("Loading model (this may take a minute)...")
tokenizer = AutoTokenizer.from_pretrained("${MODEL_ID}", cache_dir="${MODEL_PATH}")
model = AutoModel.from_pretrained("${MODEL_PATH}", compression='4bit')
print("Model loaded successfully!")

@app.route('/health', methods=['GET'])
def health():
    return jsonify({
        "status": "healthy",
        "model": "${MODEL_ID}",
        "port": ${PORT},
        "backend": "airllm"
    })

@app.route('/v1/chat/completions', methods=['POST'])
def chat_completion():
    data = request.json
    messages = data.get('messages', [])
    
    # Convert messages to prompt
    prompt = tokenizer.apply_chat_template(
        messages, 
        tokenize=False, 
        add_generation_prompt=True
    )
    
    # Generate response
    input_ids = tokenizer(prompt, return_tensors='pt').input_ids
    output = model.generate(
        input_ids,
        max_new_tokens=512,
        temperature=0.7,
        do_sample=True
    )
    
    response = tokenizer.decode(output[0], skip_special_tokens=True)
    
    return jsonify({
        "choices": [{
            "message": {
                "role": "assistant",
                "content": response
            }
        }]
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=${PORT})
PYTHON
fi
EOF
    
    chmod +x "$JEBAT_DIR/bin/run-model.sh"
    success "Model launcher created at $JEBAT_DIR/bin/run-model.sh"
}

# Create systemd service
create_systemd_service() {
    log "Creating systemd service..."
    
    SERVICE_FILE="/etc/systemd/system/jebat-llm.service"
    
    sudo tee "$SERVICE_FILE" > /dev/null << EOF
[Unit]
Description=Jebat Local LLM Service
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$JEBAT_DIR
ExecStart=$JEBAT_DIR/bin/run-model.sh qwen 8080
Restart=always
RestartSec=10
Environment=PATH=$VENV_DIR/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin
Environment=JEBAT_SECURITY_LEVEL=enterprise

# Security hardening
NoNewPrivileges=true
ProtectSystem=strict
ProtectHome=read-only
PrivateTmp=true

[Install]
WantedBy=multi-user.target
EOF
    
    sudo systemctl daemon-reload
    sudo systemctl enable jebat-llm
    
    success "Systemd service created (jebat-llm)"
    info "Start with: sudo systemctl start jebat-llm"
    info "Check status: sudo systemctl status jebat-llm"
    info "View logs: sudo journalctl -u jebat-llm -f"
}

# Update Jebat Gateway config
update_gateway_config() {
    log "Updating Jebat Gateway configuration..."
    
    CONFIG_FILE="$JEBAT_DIR/jebat-gateway.json"
    
    if [ -f "$CONFIG_FILE" ]; then
        # Add local model configuration
        python3 << 'PYTHON'
import json

config_file = "/home/humm1ngb1rd/.jebat/jebat-gateway.json"

with open(config_file, 'r') as f:
    config = json.load(f)

# Add local model provider
if 'local' not in config.get('agents', {}).get('defaults', {}).get('model', {}).get('providers', {}):
    config['agents']['defaults']['model']['providers'] = config['agents']['defaults']['model'].get('providers', {})
    config['agents']['defaults']['model']['providers']['local'] = {
        "endpoint": "http://localhost:8080/v1",
        "models": [
            "qwen2.5-3b",
            "phi-3-mini",
            "hermes3-8b",
            "gemma4"
        ],
        "default_model": "qwen2.5-3b",
        "api_key": "local"
    }
    
    # Set local as primary
    config['agents']['defaults']['model']['primary'] = "local/qwen2.5-3b"
    config['agents']['defaults']['model']['fallbacks'] = [
        "local/phi-3-mini",
        "local/gemma4",
        "local/hermes3-8b"
    ]

with open(config_file, 'w') as f:
    json.dump(config, f, indent=2)

print("Gateway config updated with local models")
PYTHON
    fi
    
    success "Gateway configuration updated"
}

# Print summary
print_summary() {
    echo ""
    echo "==================================================================="
    echo -e "${GREEN}JEBAT LOCAL LLM DEPLOYMENT COMPLETE${NC}"
    echo "==================================================================="
    echo ""
    echo -e "${CYAN}Models Installed:${NC}"
    [ -d "$MODELS_DIR/hermes3-8b" ] && echo -e "  ${GREEN}✓${NC} Hermes3 8B (4-bit quantized)"
    [ -d "$MODELS_DIR/gemma4" ] && echo -e "  ${GREEN}✓${NC} Gemma 4 (Ollama, 4-bit quantized)"
    [ -d "$MODELS_DIR/phi-3-mini" ] && echo -e "  ${GREEN}✓${NC} Phi-3 Mini 3.8B (4-bit quantized)"
    [ -d "$MODELS_DIR/qwen2.5-3b" ] && echo -e "  ${GREEN}✓${NC} Qwen2.5 3B (4-bit quantized) - RECOMMENDED"
    echo ""
    echo -e "${CYAN}Quick Start:${NC}"
    echo "  Start model: ~/.jebat/bin/run-model.sh gemma4 8080"
    echo "  Test endpoint: curl http://localhost:8080/health"
    echo "  Use as service: sudo systemctl start jebat-llm"
    echo ""
    echo -e "${CYAN}Model Comparison:${NC}"
    echo "  Qwen2.5 3B    - Best performance/size ratio (RECOMMENDED)"
    echo "  Phi-3 Mini    - Excellent for instruction following"
    echo "  Hermes3 8B    - Best for complex reasoning (needs 16GB+ RAM)"
    echo "  Gemma 4       - Latest Google model, great all-rounder (via Ollama)"
    echo ""
    echo -e "${CYAN}Integration:${NC}"
    echo "  Models are now available in Jebat Gateway"
    echo "  Primary: local/qwen2.5-3b"
    echo "  API: http://localhost:8080/v1/chat/completions"
    echo ""
    echo "==================================================================="
    echo ""
}

# Main execution
main() {
    echo ""
    echo "==================================================================="
    echo -e "${BLUE}JEBAT AGENT - LOCAL LLM DEPLOYMENT${NC}"
    echo "==================================================================="
    echo ""
    
    # Create log directory
    mkdir -p "$JEBAT_DIR/logs"
    
    # Parse arguments
    case "$MODEL_CHOICE" in
        --model) MODEL_CHOICE="${2:-all}" ;;
        hermes3|gemma|phi3|qwen) MODEL_CHOICE="$1" ;;
        *) MODEL_CHOICE="all" ;;
    esac
    
    log "Starting deployment with model: $MODEL_CHOICE"
    
    # Run setup
    check_requirements
    install_system_deps
    setup_venv
    install_airllm
    
    # Install requested models
    case "$MODEL_CHOICE" in
        hermes3)
            setup_hermes3
            ;;
        gemma)
            setup_gemma
            ;;
        phi3)
            setup_phi3
            ;;
        qwen)
            setup_qwen
            ;;
        all)
            setup_qwen        # Best first
            setup_phi3        # Second best
            setup_hermes3     # Third
            setup_gemma       # Lightest
            ;;
    esac
    
    # Create launcher and service
    create_model_launcher
    create_systemd_service
    update_gateway_config
    print_summary
}

# Run main
main "$@"
