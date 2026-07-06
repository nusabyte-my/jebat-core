#!/bin/bash
# setup.sh — Set up training environment
# Usage: bash setup.sh

set -e
cd "$(dirname "$0")"

echo "=== JEBAT-Builder Training Setup ==="

# Create venv with uv
if [ ! -d ".venv" ]; then
    echo "[1/3] Creating virtual environment..."
    uv venv .venv --python 3.12
else
    echo "[1/3] Virtual environment exists."
fi

# Activate
source .venv/Scripts/activate

# Install deps
echo "[2/3] Installing dependencies..."
uv pip install -r requirements.txt

# Install PyTorch with CUDA
echo "[3/3] Installing PyTorch with CUDA 12.4..."
uv pip install "torch==2.5.1" --index-url https://download.pytorch.org/whl/cu124

# Verify
echo ""
echo "=== Verifying ==="
python -c "
import torch
print(f'PyTorch: {torch.__version__}')
print(f'CUDA: {torch.cuda.is_available()}')
if torch.cuda.is_available():
    print(f'GPU: {torch.cuda.get_device_name(0)}')
    print(f'VRAM: {torch.cuda.get_device_properties(0).total_memory/1024**3:.1f} GB')
from transformers import AutoModelForCausalLM
from peft import LoraConfig
from trl import SFTTrainer
print('All imports OK')
"

echo ""
echo "=== Setup Complete ==="
echo ""
echo "Usage:"
echo "  source .venv/Scripts/activate"
echo "  python train.py                   # Full training (3 epochs, ~30-60 min)"
echo "  python train.py --epochs 1        # Quick test (~10-20 min)"
echo "  python train.py --test-only       # Test saved model"
echo "  python train.py --export          # Export to GGUF"
echo "  python train.py --deploy          # Deploy to .206 server"
