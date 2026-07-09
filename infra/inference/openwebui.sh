#!/usr/bin/env bash
# Launch OpenWebUI pointing at the Jebat router (unified inference endpoint).
# Requires: python3.11 venv at ~/.local/open-webui/venv with open-webui installed.
# No sudo. Binds :8080. Models are served by the router at :8000.
set -u
VENV="$HOME/.local/open-webui/venv"
if [ ! -x "$VENV/bin/open-webui" ]; then
  echo "[FATAL] open-webui not installed. Install: $VENV/bin/pip install open-webui (python3.11)"
  exit 1
fi
# Point OpenWebUI at the router; disable its own auth for local single-user use.
export OPENAI_API_BASE_URL="http://127.0.0.1:8000/v1"
export WEBUI_AUTH="${WEBUI_AUTH:-False}"
cd "$HOME/.local/open-webui"
exec "$VENV/bin/open-webui" serve
