#!/usr/bin/env bash
#
# JEBAT Core installer — Hermes-style bootstrap.
# One script, three surfaces: CLI, Desktop, MCP. No sudo required.
#
#   curl -fsSL https://raw.githubusercontent.com/nusabyte-my/jebat-core/main/install.sh | bash
#   curl -fsSL https://raw.githubusercontent.com/nusabyte-my/jebat-core/main/install.sh | bash -s -- --desktop
#   curl -fsSL https://raw.githubusercontent.com/nusabyte-my/jebat-core/main/install.sh | bash -s -- --mcp
#
# Profiles:
#   (default)      install the JEBAT CLI only
#   --cli          CLI only (explicit)
#   --desktop      CLI + Desktop launcher (Electron app)
#   --mcp          CLI + MCP server (stdio + IDE config helper)
#   --all          everything above
#   --no-inference skip the local unified inference stack (Ollama/llama.cpp/router/OpenWebUI)
#
set -euo pipefail

# ── constants ────────────────────────────────────────────────────────
JEBAT_VERSION="8.2.0"
REPO_URL="https://github.com/nusabyte-my/jebat-core.git"
INSTALL_DIR="${JEBAT_HOME:-$HOME/.local/jebat}"
BIN_DIR="$HOME/.local/bin"
VENV_DIR="$INSTALL_DIR/venv"
PY_REQ="3.11"

# profile flags
DO_CLI=1
DO_DESKTOP=0
DO_MCP=0
DO_INFERENCE=1

# ── helpers ───────────────────────────────────────────────────────────
c_banner() { printf '\033[1;35m%s\033[0m\n' "$1"; }
c_step()   { printf '\033[1;36m  ›\033[0m %s\n' "$1"; }
c_ok()     { printf '\033[1;32m  ✓\033[0m %s\n' "$1"; }
c_warn()   { printf '\033[1;33m  !\033[0m %s\n' "$1"; }
c_fail()   { printf '\033[1;31m  ✗\033[0m %s\n' "$1"; }
c_comp()   { printf '\033[1;34m    ├─\033[0m %s\n' "$1"; }

need_cmd() { command -v "$1" >/dev/null 2>&1 || { c_fail "required: $1"; exit 1; }; }

# ── MCP config emission (agent / IDE setup, no install required) ─────────
# Prints a ready-to-paste MCP server config for the requested client.
# Two transports are offered:
#   - stdio  : runs the local JEBAT MCP server (needs the package installed)
#   - http   : zero-install public endpoint (https://mcp.jebat.online/mcp)
print_mcp_config() {
  local client="${1:-generic}"
  local py="${2:-python3}"
  local stdio='"jebat": { "command": "'"$py"'", "args": ["-m", "jebat.mcp.server"], "env": { "JEBAT_MCP_TRANSPORT": "stdio" } }'
  local http='"jebat-online": { "url": "https://mcp.jebat.online/mcp" }'
  local body
  body=$(cat <<JSON
{
  "mcpServers": {
    $stdio,
    $http
  }
}
JSON
)
  case "$client" in
    cursor|vscode)
      # Cursor and VS Code consume the same mcpServers shape.
      printf '%s\n' "$body"
      ;;
    claude)
      # Claude Desktop config file (claude_desktop_config.json)
      printf '%s\n' "$body"
      ;;
    zed)
      # Zed uses context_servers with a stdio source.
      cat <<JSON
{
  "context_servers": {
    "jebat": {
      "source": { "type": "stdio", "command": "$py", "args": ["-m", "jebat.mcp.server"] }
    }
  }
}
JSON
      ;;
    generic|*)
      printf '%s\n' "$body"
      ;;
  esac
  echo >&2 "Paste the config above into your IDE's MCP settings."
  echo >&2 "Prefer the zero-install 'jebat-online' HTTP endpoint (no local install needed)."
}

# ── parse args ────────────────────────────────────────────────────────
ASSUME_YES=0
QUIET=0
MCP_CONFIG_CLIENT=""
MCP_ONLY=0
PRINT_HELP=0
for a in "$@"; do
  case "$a" in
    --cli)        DO_CLI=1 ;;
    --desktop)    DO_CLI=1; DO_DESKTOP=1 ;;
    --mcp)        DO_CLI=1; DO_MCP=1 ;;
    --all)        DO_CLI=1; DO_DESKTOP=1; DO_MCP=1 ;;
    --no-inference) DO_INFERENCE=0 ;;
    -y|--yes|--assume-yes) ASSUME_YES=1 ;;
    -q|--quiet)   QUIET=1 ;;
    --mcp-only)   DO_CLI=0; DO_DESKTOP=0; DO_INFERENCE=0; DO_MCP=1; MCP_ONLY=1 ;;
    --print-mcp-config) MCP_CONFIG_CLIENT="generic" ;;
    --print-mcp-config=*) MCP_CONFIG_CLIENT="${a#*=}" ;;
    -h|--help)    PRINT_HELP=1 ;;
    *) c_warn "unknown flag: $a (ignored)";;
  esac
done

# Agents / CI are non-interactive: auto-assume-yes unless overridden.
if [ "$ASSUME_YES" -eq 0 ] && [ ! -t 1 ]; then
  ASSUME_YES=1
fi

if [ "$PRINT_HELP" -eq 1 ]; then
  sed -n '2,20p' "$0"
  exit 0
fi

# Emit a ready-to-paste MCP config for the requested IDE client and exit.
# Usage: install.sh --print-mcp-config=cursor   (cursor|vscode|claude|zed|generic)
if [ -n "$MCP_CONFIG_CLIENT" ]; then
  PY_BIN="$(command -v python3 || command -v python || echo python3)"
  print_mcp_config "$MCP_CONFIG_CLIENT" "$PY_BIN"
  exit 0
fi

# When only emitting MCP config, skip the rest of the install.
if [ "$MCP_ONLY" -eq 1 ]; then
  c_ok "MCP config written to $INSTALL_DIR/mcp.ide.json"
  exit 0
fi

# ── banner ─────────────────────────────────────────────────────────────
if [ "$QUIET" -eq 0 ]; then
  echo
  c_banner "🗡️  JEBAT Core — Sovereign Agent OS  v$JEBAT_VERSION"
  c_banner "    installing for: $(whoami)@$(uname -s) $(uname -m)"
  echo
  c_step "selected components:"
  [ "$DO_CLI" -eq 1 ]        && c_comp "CLI            (jebat repl / chat / code / agent / think)"
  [ "$DO_DESKTOP" -eq 1 ]    && c_comp "Desktop        (Stealth-Dark WebUI with full Agent OS)"
  [ "$DO_MCP" -eq 1 ]        && c_comp "MCP surface    (47 tools over stdio/HTTP/streamable-http on :8206)"
  [ "$DO_INFERENCE" -eq 1 ]  && c_comp "Inference stack (Ollama + llama.cpp + router + OpenWebUI)"
  echo
fi

# ── preflight ─────────────────────────────────────────────────────────
c_step "preflight checks"
need_cmd python3
need_cmd git
PYV=$(python3 -c 'import sys;print("%d.%d"%sys.version_info[:2])')
c_ok "python3 $PYV found"
command -v node >/dev/null 2>&1 && c_ok "node $(node -v) found" || c_warn "node not found — DESIGNmd CLI + Desktop need it (npm install -g designmd later)"
mkdir -p "$BIN_DIR" "$INSTALL_DIR"
c_ok "install dir: $INSTALL_DIR"

# ── clone / update source ──────────────────────────────────────────────
c_step "fetching JEBAT Core source"
if [ -d "$INSTALL_DIR/.git" ]; then
  git -C "$INSTALL_DIR" pull --ff-only >/dev/null 2>&1 && c_ok "updated existing checkout" || c_warn "pull failed; using existing tree"
else
  git clone --depth 1 "$REPO_URL" "$INSTALL_DIR" >/dev/null 2>&1 && c_ok "cloned $REPO_URL" || { c_fail "clone failed (network?)"; exit 1; }
fi

# ── python venv ───────────────────────────────────────────────────────
c_step "provisioning Python virtualenv"
if [ ! -x "$VENV_DIR/bin/python" ]; then
  python3 -m venv "$VENV_DIR"
  c_ok "created venv at $VENV_DIR"
else
  c_ok "venv already present"
fi
# shellcheck disable=SC1091
source "$VENV_DIR/bin/activate"
python -m pip install --quiet --upgrade pip
c_ok "pip upgraded"

# ── install CLI (editable from checkout) ───────────────────────────────
c_step "installing JEBAT CLI"
# The cloned repo root is the package (pyproject defines `jebat`).
# Some layouts nest it under ./jebat-core — detect by pyproject presence.
SRC="$INSTALL_DIR"
if [ ! -f "$SRC/pyproject.toml" ] && [ -f "$INSTALL_DIR/jebat-core/pyproject.toml" ]; then
  SRC="$INSTALL_DIR/jebat-core"
fi
pip install --quiet -e "${SRC}[security,channels]" >/dev/null 2>&1 && c_ok "jebat CLI installed (editable from $SRC + security,channels extras)" || { c_fail "pip install failed"; exit 1; }

# launcher on PATH
cat > "$BIN_DIR/jebat" <<EOF
#!/usr/bin/env bash
exec "$VENV_DIR/bin/jebat" "\$@"
EOF
chmod +x "$BIN_DIR/jebat"
c_ok "launcher: $BIN_DIR/jebat"

# ── default inference provider (local unified router) ─────────────────
c_step "configuring default inference provider (local unified router)"
python3 - <<PY
import json, os
p = os.path.expanduser("~/.jebat/jebat-cli-providers.json")
os.makedirs(os.path.dirname(p), exist_ok=True)
# Fresh-install default: the LOCAL unified router (OpenAI-compatible) at
# http://127.0.0.1:8000/v1, which merges Ollama + llama.cpp backends.
# This works out-of-the-box (no external dependency).
# When you stand up the public API, swap jebat-online's api_base to
# https://jebat.online/v1 (see infra/inference/Caddyfile.example).
defaults = {
    "jebat-online": {
        "id": "jebat-online",
        "name": "JEBAT Online (local router)",
        "api_base": "http://127.0.0.1:8000/v1",
        "model": "qwen2.5:3b",
        "api_key": None,
        "kind": "openai",
        "active": True,
    },
    "ollama-local": {
        "id": "ollama-local",
        "name": "Ollama (local)",
        "api_base": "http://127.0.0.1:11434",
        "model": "qwen2.5:3b",
        "api_key": None,
        "kind": "ollama",
        "active": False,
    },
}
# Preserve any existing provider config (e.g. from a prior /provider add).
if os.path.exists(p):
    try:
        existing = json.load(open(p))
        if isinstance(existing, dict) and existing:
            defaults = existing
    except Exception:
        pass
json.dump(defaults, open(p, "w"), indent=2)
print("wrote", p)
PY
c_ok "default provider: local unified router (http://127.0.0.1:8000/v1) — OpenAI-compatible"
c_warn "to use the public endpoint later, set jebat-online api_base -> https://jebat.online/v1 (see infra/inference/Caddyfile.example)"

# ── DESIGNmd CLI (companion tool) ──────────────────────────────────────
c_step "installing DESIGNmd CLI"
if command -v node >/dev/null 2>&1; then
  if command -v designmd >/dev/null 2>&1; then
    c_ok "designmd already installed ($(designmd --version 2>/dev/null))"
  else
    npm install -g designmd >/dev/null 2>&1 && c_ok "designmd installed ($(designmd --version 2>/dev/null))" || c_warn "designmd install failed — run: npm install -g designmd"
  fi
else
  c_warn "node missing — skip designmd; install later: npm install -g designmd"
fi

# ── MCP / Desktop surfaces (optional) ──────────────────────────────────
if [ "$DO_MCP" -eq 1 ]; then
  c_step "configuring MCP surface"

  # Install standalone MCP entry point
  if [ -f "$SRC/jebat-mcp" ]; then
    install -m 755 "$SRC/jebat-mcp" "$BIN_DIR/jebat-mcp"
    c_ok "standalone entry point: $BIN_DIR/jebat-mcp"
  fi

  # Write IDE config snippet (local stdio + zero-install public HTTP endpoint)
  PYTHON_BIN="$(command -v python3)"
  cat > "$INSTALL_DIR/mcp.ide.json" <<JSON
{
  "mcpServers": {
    "jebat": {
      "command": "$PYTHON_BIN",
      "args": ["-m", "jebat.mcp.server"],
      "env": {"JEBAT_MCP_TRANSPORT": "stdio"}
    },
    "jebat-online": {
      "url": "https://mcp.jebat.online/mcp"
    }
  }
}
JSON
  c_ok "IDE snippet: $INSTALL_DIR/mcp.ide.json"
  c_ok "MCP server exposes 47 tools over stdio/HTTP/streamable-http"
  c_ok "zero-install public endpoint: https://mcp.jebat.online/mcp"
  c_ok "generate IDE configs:  curl -fsSL https://raw.githubusercontent.com/nusabyte-my/jebat-core/main/install.sh | bash -s -- --print-mcp-config=cursor"
  c_ok "start local MCP server: jebat mcp serve --port 8206"
fi

if [ "$DO_DESKTOP" -eq 1 ]; then
  c_step "Desktop surface"
  c_ok "Desktop UI ships with the full Jebat workspace (jebat-dev) — run 'jebat desktop' once that code is installed"
  c_warn "headless/minimal hosts: install Electron once with 'npm i -g electron' for offline desktop"
fi

# ── Unified inference stack (optional) ─────────────────────────────────
if [ "$DO_INFERENCE" -eq 1 ]; then
  c_step "local unified inference stack"
  INFRA="$INSTALL_DIR/infra/inference"
  if [ -d "$INFRA" ]; then
    c_ok "config + router at: $INFRA"
    c_ok "backends: llama.cpp (CPU/AVX512 + Iris Xe Vulkan), Ollama, remote vLLM/Ollama"
    c_ok "router endpoint: http://127.0.0.1:8000/v1  (OpenAI-compatible, merges all backends)"
    c_ok "OpenWebUI: http://127.0.0.1:8080  (pointed at the router)"
    c_warn "start it with: $INFRA/start.sh   (or systemd --user: jebat-router.service etc.)"
  else
    c_warn "inference stack not found in checkout; skipping"
  fi
fi

# ── done ───────────────────────────────────────────────────────────────
echo
c_banner "✅ JEBAT Core v$JEBAT_VERSION installed."
echo
c_step "what's installed:"
echo "    ✓ Agent Loop with adaptive context windowing"
echo "    ✓ 6-type memory system with Ghost DB vector search"
echo "    ✓ Working memory persistence across sessions"
echo "    ✓ Cost tracking per LLM iteration"
echo "    ✓ Ultra-Loop (perception/cognition/memory/action/learning)"
echo "    ✓ Self-learning with UCB1 strategy selection"
echo "    ✓ 17 LLM providers with auto-failover"
echo "    ✓ 47 MCP tools (stdio/HTTP/streamable-http)"
echo "    ✓ 6 Grafana dashboards (context budget, LLM health, etc.)"
echo
c_step "verify:"
echo "    jebat --help              # core commands: repl / chat / code / agent / think"
echo "    jebat repl                # interactive REPL with memory persistence"
echo "    jebat chat 'hello'        # one-shot chat"
echo "    jebat agent 'task'        # run agent with tool execution"
echo "    jebat think --mode deep   # Ultra-Think with 7 reasoning modes"
echo "    jebat mcp serve           # start MCP server (stdio)"
echo "    jebat mcp serve --port 8206  # start MCP server (HTTP)"
[ "$DO_INFERENCE" -eq 1 ]&& echo "    infra/inference/start.sh  # boot local LLMs (Ollama + llama.cpp)"
echo
c_step "IDE integration:"
echo "    VS Code / Cursor:  Add MCP config from $INSTALL_DIR/mcp.ide.json"
echo "    Claude Desktop:    Copy mcp.ide.json to ~/Library/Application Support/Claude/"
echo "    Zed / Windsurf:    Add MCP server in settings"
echo
c_step "ensure PATH includes ~/.local/bin:"
case ":$PATH:" in *":$HOME/.local/bin:"*) ;; *) echo '    export PATH="$HOME/.local/bin:$PATH"  # add to ~/.bashrc / ~/.zshrc'; ;; esac
echo
c_step "documentation:"
echo "    https://jebat.online/docs"
echo "    https://github.com/nusabyte-my/jebat-core"
echo
