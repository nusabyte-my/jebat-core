#!/usr/bin/env bash
# ============================================================================
# JEBAT Core — CachyOS / Arch installer
#
#   unzip jebatcore-YYYYMMDD.zip -d ~/projects
#   cd ~/projects/jebatcore
#   ./install-cachyos.sh
#
# Options:
#   --prefix DIR   install dir for the venv   (default: <this dir>/.venv)
#   --no-deps      skip pacman, assume python/git present
#   --no-ollama    skip the Ollama check
#   --with-mcp     also register jebat-mcp for Kiro/Cursor/VS Code
#   --run          start the CLI when done
#
# Arch's system python is PEP-668 externally managed. Everything goes in a
# venv; nothing is installed with --break-system-packages.
# ============================================================================
set -Eeuo pipefail

REPO_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$REPO_DIR/.venv"
BIN_DIR="$HOME/.local/bin"
DO_DEPS=1
DO_OLLAMA=1
DO_MCP=0
DO_RUN=0

while (($#)); do
  case "$1" in
    --prefix) VENV_DIR="${2:?--prefix needs a path}"; shift 2 ;;
    --no-deps) DO_DEPS=0; shift ;;
    --no-ollama) DO_OLLAMA=0; shift ;;
    --with-mcp) DO_MCP=1; shift ;;
    --run) DO_RUN=1; shift ;;
    -h|--help) awk 'NR>1 && /^#/{ sub(/^# ?/,""); if ($0 ~ /^=+$/) next; print; next } NR>1{exit}' "${BASH_SOURCE[0]}"; exit 0 ;;
    *) printf 'unknown option: %s\n' "$1" >&2; exit 2 ;;
  esac
done

step() { printf '\n\033[1;35m==> %s\033[0m\n' "$*"; }
ok()   { printf '    \033[1;32m✓\033[0m %s\n' "$*"; }
warn() { printf '    \033[1;33m!\033[0m %s\n' "$*"; }
die()  { printf '\n\033[1;31mERROR:\033[0m %s\n' "$*" >&2; exit 1; }

trap 'die "failed at line $LINENO"' ERR

# ── 0. sanity ───────────────────────────────────────────────────────────────
[[ -f "$REPO_DIR/pyproject.toml" && -d "$REPO_DIR/jebat" ]] \
  || die "run this from the jebatcore repo root (pyproject.toml + jebat/ not found)"

if [[ -r /etc/os-release ]]; then
  . /etc/os-release
  case "${ID:-}${ID_LIKE:-}" in
    *arch*|*cachyos*) ok "detected ${PRETTY_NAME:-Arch family}" ;;
    *) warn "${PRETTY_NAME:-unknown distro} — script targets pacman; continuing anyway" ;;
  esac
fi

# ── 1. system packages ──────────────────────────────────────────────────────
if ((DO_DEPS)); then
  step "system packages (pacman)"
  PKGS=(python python-pip git base-devel)
  command -v uv >/dev/null || PKGS+=(uv)
  # build headers asyncpg / cryptography / numpy may need
  PKGS+=(python-setuptools)
  if ! sudo -n true 2>/dev/null; then
    warn "sudo will ask for your password"
  fi
  sudo pacman -Sy --needed --noconfirm "${PKGS[@]}"
  ok "pacman packages present"
else
  step "system packages — skipped (--no-deps)"
fi

command -v python3 >/dev/null || die "python3 not found"

# Arch tracks the newest CPython, which can be 3.14+ where half of the wheel
# set (asyncpg, scikit-learn, pandas) has no prebuilt wheel yet. Prefer 3.12/3.13.
pick_python() {
  local c
  for c in python3.12 python3.13 python3.11; do
    command -v "$c" >/dev/null && { printf '%s' "$c"; return; }
  done
  printf '%s' "python3"
}
SYS_PY="$(pick_python)"
PYV="$("$SYS_PY" -c 'import sys;print("%d.%d"%sys.version_info[:2])')"
"$SYS_PY" -c 'import sys;raise SystemExit(0 if sys.version_info>=(3,11) else 1)' \
  || die "python 3.11+ required, found $PYV ($SYS_PY)"

case "$PYV" in
  3.12|3.13) ok "python $PYV via $SYS_PY" ;;
  *)
    warn "python $PYV ($SYS_PY) — some deps may lack wheels; install python312 from the AUR"
    warn "or rerun with:  sudo pacman -S --needed python312 && ./install-cachyos.sh"
    ;;
esac

# ── 2. venv ─────────────────────────────────────────────────────────────────
step "virtualenv → $VENV_DIR"
if [[ ! -x "$VENV_DIR/bin/python" ]]; then
  "$SYS_PY" -m venv "$VENV_DIR"
fi
"$VENV_DIR/bin/python" -m pip install --upgrade pip wheel setuptools >/dev/null
ok "venv ready: $("$VENV_DIR/bin/python" -V)"

# ── 3. dependencies ─────────────────────────────────────────────────────────
step "python dependencies (this takes a few minutes)"
# requirements.txt is the real runtime set. pyproject's deps drag in torch,
# which JEBAT never imports — do not install from pyproject.
if ! "$VENV_DIR/bin/python" -m pip install -r "$REPO_DIR/requirements.txt"; then
  warn "pip failed — retrying via uv (often fixes missing wheels/build deps)"
  if command -v uv >/dev/null; then
    uv pip install --python "$VENV_DIR/bin/python" -r "$REPO_DIR/requirements.txt" \
      || die "dependency install failed (pip and uv)"
  else
    die "dependency install failed; install uv (sudo pacman -S uv) and rerun"
  fi
fi

step "editable install (jebat console script + packages)"
"$VENV_DIR/bin/python" -m pip install -e "$REPO_DIR" --no-deps \
  || die "editable install failed"
ok "jebat $( "$VENV_DIR/bin/python" -c 'import jebat,pathlib;print(getattr(jebat,"__version__","?"))' 2>/dev/null || echo installed )"

# ── 4. .env ─────────────────────────────────────────────────────────────────
step "environment file"
if [[ -f "$REPO_DIR/.env" ]]; then
  ok ".env already present — left untouched"
elif [[ -f "$REPO_DIR/.env.example" ]]; then
  cp "$REPO_DIR/.env.example" "$REPO_DIR/.env"
  warn ".env created from .env.example — add your API keys"
else
  warn "no .env and no .env.example; skipping"
fi
chmod 600 "$REPO_DIR/.env" 2>/dev/null || true

# ── 5. launchers ────────────────────────────────────────────────────────────
step "launchers in $BIN_DIR"
mkdir -p "$BIN_DIR"

cat >"$BIN_DIR/jebat" <<EOF
#!/usr/bin/env bash
# generated by jebatcore/install-cachyos.sh
exec "$VENV_DIR/bin/python" -m jebat_cli_new.jebat "\$@"
EOF

cat >"$BIN_DIR/jebat-mcp" <<EOF
#!/usr/bin/env bash
# stdio MCP server for IDEs; extra args pass through (--transport http --port 8101)
exec "$VENV_DIR/bin/python" "$REPO_DIR/jebat-mcp" "\$@"
EOF

chmod +x "$BIN_DIR/jebat" "$BIN_DIR/jebat-mcp"
ok "jebat, jebat-mcp"

case ":$PATH:" in
  *":$BIN_DIR:"*) ok "$BIN_DIR on PATH" ;;
  *) warn "$BIN_DIR is not on PATH — add: export PATH=\"\$HOME/.local/bin:\$PATH\"" ;;
esac

# ── 6. ollama (optional inference) ──────────────────────────────────────────
if ((DO_OLLAMA)); then
  step "local inference"
  if command -v ollama >/dev/null; then
    if curl -fsS -m 3 http://127.0.0.1:11434/api/tags >/dev/null 2>&1; then
      ok "ollama running on :11434"
    else
      warn "ollama installed but not answering — start it: systemctl --user start ollama"
    fi
  else
    warn "ollama not installed (optional): sudo pacman -S ollama && systemctl enable --now ollama"
  fi
fi

# ── 7. IDE MCP registration (optional) ──────────────────────────────────────
if ((DO_MCP)); then
  step "IDE MCP registration"
  KCFG="$HOME/.kiro/settings/mcp.json"
  if [[ -d "$HOME/.kiro" ]]; then
    mkdir -p "$(dirname "$KCFG")"
    [[ -f "$KCFG" ]] && cp "$KCFG" "$KCFG.bak-$(date +%Y%m%d-%H%M%S)"
    "$VENV_DIR/bin/python" - "$KCFG" "$VENV_DIR/bin/python" "$REPO_DIR/jebat-mcp" <<'PY'
import json, sys, os
cfg, py, entry = sys.argv[1:4]
d = {}
if os.path.exists(cfg):
    try:
        d = json.load(open(cfg, encoding="utf-8-sig"))
    except Exception:
        d = {}
d.setdefault("mcpServers", {})["jebat"] = {
    "command": py, "args": [entry],
    "env": {"PYTHONUTF8": "1", "PYTHONIOENCODING": "utf-8"},
    "timeout": 180000,
}
json.dump(d, open(cfg, "w", encoding="utf-8"), indent=2)
print("    wrote", cfg)
PY
    ok "kiro mcp.json updated"
  else
    warn "no ~/.kiro — skipped Kiro registration"
  fi
fi

# ── 8. smoke test ───────────────────────────────────────────────────────────
step "smoke test"
"$VENV_DIR/bin/python" -c "import jebat, jebat_cli_new.jebat; print('    import ok')" \
  || die "JEBAT does not import"
printf '%s\n' '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-06-18","capabilities":{},"clientInfo":{"name":"install","version":"1"}}}' \
  | timeout 60 "$BIN_DIR/jebat-mcp" 2>/dev/null | grep -q '"serverInfo"' \
  && ok "jebat-mcp answers an MCP initialize" \
  || warn "jebat-mcp did not answer in 60s (check .env / logs)"

step "done"
cat <<EOF

  JEBAT is installed.

    jebat                 start the CLI
    jebat-mcp             stdio MCP server for IDEs
    jebat-mcp --transport streamable-http --port 8101
                          local HTTP MCP endpoint
    $VENV_DIR/bin/python  interpreter with all deps

  Next: put your API keys in $REPO_DIR/.env

EOF

if ((DO_RUN)); then
  exec "$BIN_DIR/jebat"
fi
