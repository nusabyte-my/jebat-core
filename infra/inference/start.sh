#!/usr/bin/env bash
# Start the whole Jebat inference stack:
#   - Ollama (if not running)
#   - llama.cpp server (optional, only if a model is configured)
#   - The unified router on :8000 (the single endpoint clients use)
set -u
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CFG="$ROOT/config.yaml"
VENV="$ROOT/venv"
PID="$ROOT/.pids"

mkdir -p "$PID"

# --- 1. Ollama --------------------------------------------------------------
if pgrep -x ollama >/dev/null 2>&1; then
  echo "[ok] ollama already running"
else
  echo "[*] starting ollama serve (background)..."
  # Ollama is a user-space binary; no sudo needed.
  ollama serve >/dev/null 2>&1 &
  echo $! > "$PID/ollama.pid"
  # wait for it to come up
  for i in $(seq 1 20); do
    curl -sS -m 2 http://127.0.0.1:11434 >/dev/null 2>&1 && break
    sleep 0.5
  done
  echo "[ok] ollama up"
fi

# --- 2. llama.cpp server (optional) ----------------------------------------
LLAMA_BIN="$VENV/bin/llama-server"
if [ -x "$LLAMA_BIN" ] && grep -q 'llamacpp' "$CFG" 2>/dev/null; then
  # only launch if a model path is configured
  if grep -qE 'path:' "$CFG"; then
    echo "[*] launching llama.cpp server on :8081 ..."
    "$LLAMA_BIN" \
      --host 127.0.0.1 --port 8081 \
      --model "$(grep -oE '/[^ ]+\.gguf' "$CFG" | head -1)" \
      --ctx-size 8192 --threads 8 \
      >"$ROOT/llamacpp.log" 2>&1 &
    echo $! > "$PID/llamacpp.pid"
    echo "[ok] llama.cpp pid $(cat "$PID/llamacpp.pid")"
  else
    echo "[skip] llama.cpp: no model path configured in config.yaml"
  fi
fi

# --- 3. Router --------------------------------------------------------------
echo "[*] starting Jebat router on :8000 ..."
"$VENV/bin/python" "$ROOT/router.py" >"$ROOT/router.log" 2>&1 &
echo $! > "$PID/router.pid"
for i in $(seq 1 20); do
  curl -sS -m 2 http://127.0.0.1:8000/health >/dev/null 2>&1 && break
  sleep 0.5
done
echo "=========================================================="
echo " Jebat Inference ready."
echo "  Unified endpoint : http://127.0.0.1:8000/v1"
echo "  Ollama direct    : http://127.0.0.1:11434"
echo "  llama.cpp direct : http://127.0.0.1:8081 (if enabled)"
echo "  Health check     : curl http://127.0.0.1:8000/health"
echo "=========================================================="
