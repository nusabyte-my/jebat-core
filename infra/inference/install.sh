#!/usr/bin/env bash
# Install Jebat inference stack into user space (no sudo, persists in /home).
# - creates a venv at ~/.local/jebat-infer/venv
# - installs router deps (fastapi, uvicorn, httpx, pyyaml)
# - builds llama.cpp (llama-server) with CPU + AVX-512 (auto-detected at runtime)
set -euo pipefail
ROOT="$HOME/.local/jebat-infer"
VENV="$ROOT/venv"
mkdir -p "$ROOT"

echo "[*] creating venv at $VENV"
python3 -m venv "$VENV"
# shellcheck disable=SC1091
source "$VENV/bin/activate"

echo "[*] installing router python deps"
pip install --quiet --upgrade pip
pip install --quiet fastapi uvicorn httpx pyyaml

echo "[*] checking build toolchain"
for t in git cmake gcc g++; do
  command -v "$t" >/dev/null 2>&1 || { echo "[FATAL] missing $t"; exit 1; }
done

echo "[*] cloning llama.cpp (shallow)"
cd "$ROOT"
if [ ! -d llama.cpp ]; then
  git clone --depth 1 https://github.com/ggml-org/llama.cpp.git
fi
cd llama.cpp
git pull --ff-only --depth 1 2>/dev/null || true

echo "[*] configuring + building llama-server (Release, native AVX-512)"
cmake -B build -DCMAKE_BUILD_TYPE=Release -DLLAMA_BUILD_SERVER=on -DGGML_NATIVE=on
cmake --build build --config Release -j"$(nproc)"

echo "[*] installing llama-server / llama-cli into venv"
mkdir -p "$VENV/bin"
cp build/bin/llama-server "$VENV/bin/" 2>/dev/null || cp build/llama-server "$VENV/bin/" 2>/dev/null || true
cp build/bin/llama-cli "$VENV/bin/" 2>/dev/null || cp build/llama-cli "$VENV/bin/" 2>/dev/null || true
ls -la "$VENV/bin/" | grep -E 'llama' || true

echo "[DONE] install complete. Binaries in $VENV/bin"
"$VENV/bin/llama-server" --version 2>&1 | head -3 || true
