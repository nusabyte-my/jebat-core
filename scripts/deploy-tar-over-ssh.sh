#!/bin/bash
# deploy-tar-over-ssh.sh — code sync for hosts without local rsync (e.g. Windows Git Bash)
#
# Mirrors scripts/sync-to-vps.sh (same host, same destination, same exclusions)
# but ships the tree as a tar stream over ssh instead of rsync. Differences
# from rsync --delete:
#   - files deleted locally are NOT removed on the server (overlay update) —
#     safer by default; run scripts/sync-to-vps.sh from an rsync-capable box
#     when you need exact mirroring.
#   - the payload never contains .env, .git, venvs, node_modules, local model
#     weights (gguf-models/), or local state (memory/, vault/, dotdirs), so
#     server-side secrets, deps, and .jebat runtime state survive.
#
# Usage:
#   DRY_RUN=1 bash scripts/deploy-tar-over-ssh.sh          # verify only
#   BACKUP=1 bash scripts/deploy-tar-over-ssh.sh           # tar the server dir first
#   bash scripts/deploy-tar-over-ssh.sh                    # deploy
#
# Env overrides: VPS_HOST, VPS_CODE_DIR, TMPDIR, EXTRA_PRUNE
#   EXTRA_PRUNE="training integrations"  — skip extra top-level dirs (space-
#   separated) when the target only needs the runtime tree. Overlay semantics
#   leave any server-side copies of skipped dirs untouched.

set -euo pipefail

VPS_HOST="${VPS_HOST:-root@72.62.255.206}"
VPS_CODE_DIR="${VPS_CODE_DIR:-/var/www/jebat-core}"
LOCAL_DIR="$(cd "$(dirname "$0")/.." && pwd)"
STAMP="$(date +%Y%m%d-%H%M%S)"
DRY_RUN="${DRY_RUN:-0}"
BACKUP="${BACKUP:-0}"

echo "⚔️  JEBAT tar-over-ssh sync"
echo "   Source:   $LOCAL_DIR"
echo "   Dest:     $VPS_HOST:$VPS_CODE_DIR"
echo "   Mode:     $([ "$DRY_RUN" = "1" ] && echo "DRY RUN" || echo "DEPLOY")$([ "$BACKUP" = "1" ] && echo " + server backup")"
echo ""

cd "$LOCAL_DIR"

# Optional extra top-level prunes (see header).
EXTRA_PRUNE="${EXTRA_PRUNE:-}"
EXTRA_PATHS=()
for d in $EXTRA_PRUNE; do EXTRA_PATHS+=(-o -path "./$d"); done

# Prune during traversal (fast): every root dotdir (.git, .venv, .jebat, .freebuff,
# local tooling...), dependency/build dirs, local-only weights and state.
find . \
  \( -type d -path './.*' \
     -o -type d \( -name node_modules -o -name __pycache__ -o -name '*.egg-info' \
        -o -name venv -o -name dist \) \
     -o -type d \( -path './gguf-models' -o -path './jebat-core' -o -path './jebat-online' \
        -o -path './out' -o -path './memory' -o -path './vault' \
        ${EXTRA_PATHS[@]+"${EXTRA_PATHS[@]}"} \) \
  \) -prune \
  -o -type f \( ! -name '*.pyc' ! -name '*.png' ! -name '.env' ! -name '*.npy' \) -print \
  > /tmp/jebat-deploy-files.$$.txt
PAYLIST=/tmp/jebat-deploy-files.$$.txt
trap 'rm -f "$PAYLIST"' EXIT
COUNT=$(wc -l < "$PAYLIST")
echo "📦 Payload: $COUNT files"
echo ""

if [ "$DRY_RUN" = "1" ]; then
  echo "🔍 DRY RUN — payload health checks:"
  echo "   top-level entries:"
  cut -c3- "$PAYLIST" | cut -d/ -f1 | sort | uniq -c | sort -rn | head -12 | sed 's/^/     /'
  echo "   .env leaked? $(grep -c '^\./\.env$' "$PAYLIST" || true) (must be 0)"
  echo "   PNG leaked?  $(grep -c '\.png$' "$PAYLIST" || true) (must be 0)"
  echo "   gguf/model weights leaked? $(grep -c 'gguf-models/' "$PAYLIST" || true) (must be 0)"
  echo "Dry run OK. Re-run without DRY_RUN=1 to deploy."
  exit 0
fi

echo "🔗 Streaming and extracting..."
tar -cf - -T "$PAYLIST" \
  | ssh -o BatchMode=yes "$VPS_HOST" "
      set -e
      mkdir -p '$VPS_CODE_DIR'
      if [ '$BACKUP' = '1' ]; then
        echo '   💾 Backing up server dir...'
        tar -czf /root/jebat-runtime-backup-$STAMP.tar.gz -C '$VPS_CODE_DIR' . 2>/dev/null || true
      fi
      tar -xf - -C '$VPS_CODE_DIR'
      echo '   ✓ extracted'
    "

echo ""
echo "✅ Synced to $VPS_CODE_DIR"
echo "Next step: restart services, e.g."
echo "  ssh $VPS_HOST 'pm2 restart jebat-api jebat-mcp jebat-webui --update-env && pm2 save'"
