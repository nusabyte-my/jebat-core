#!/usr/bin/env bash
# Run the authenticated local bridge; ComfyUI itself stays on loopback.
set -euo pipefail
: "${JEBAT_COMFYUI_BRIDGE_TOKEN:?Set a strong bridge token}"
: "${JEBAT_COMFYUI_CHECKPOINT:?Set the checkpoint filename in ComfyUI models/checkpoints}"
export COMFYUI_HOST="${COMFYUI_HOST:-http://127.0.0.1:8188}"
python -m uvicorn jebat.features.image_gen.comfy_bridge:app --host 127.0.0.1 --port 8189
