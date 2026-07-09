#!/usr/bin/env bash
# Stop the Jebat inference stack (router + llama.cpp). Leaves Ollama running
# unless you pass --all (Ollama is often shared with other tools).
set -u
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PID="$ROOT/.pids"

stop() {
  local name="$1" file="$PID/$1.pid"
  if [ -f "$file" ]; then
    local p; p="$(cat "$file")"
    if kill -0 "$p" 2>/dev/null; then
      kill "$p" 2>/dev/null && echo "[ok] stopped $name ($p)"
    fi
    rm -f "$file"
  fi
}

stop router
stop llamacpp

if [ "${1:-}" = "--all" ]; then
  pkill -x ollama 2>/dev/null && echo "[ok] stopped ollama"
fi
echo "done."
