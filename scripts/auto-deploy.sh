#!/bin/bash
# auto-deploy.sh — GitHub push webhook deployer for JEBAT.
#
# Topology (2026-09):
#   .65 (nusabyte.cloud)  = PUBLIC host. Runs nginx for jebat.online, holds the
#                           git checkout, and receives the GitHub push webhook.
#                           It does NOT run the API.
#   .206 (nusabytePro)    = API host. Runs PM2 `jebat-api` on :8000. Has NO git
#                           repo. .65 tunnels :8000 -> .206 for public /api/.
#
# This script runs on .65. It updates the local git checkout, then propagates
# ONLY the files changed in the pushed commit range to .206 (targeted rsync,
# never --delete on the whole tree — .206 carries untracked dirs like
# integrations/pi and packages/jebat-cli/dist that .65 does not have), backs up
# the current .206 state first for rollback, and restarts the live API there.
#
# If it is ever run directly on the API host (pm2 jebat-api present locally),
# it detects that and restarts in place instead of propagating.
set -euo pipefail

REPO_DIR="${JEBAT_REPO_DIR:-/var/www/jebat-core}"
WEB_DIR="${JEBAT_WEB_DIR:-/var/www/jebat.online}"

# API host (where the real jebat-api PM2 process lives).
API_HOST="${JEBAT_API_HOST:-root@72.62.255.206}"
API_DIR="${JEBAT_API_DIR:-/var/www/jebat-core}"
API_PORT="${JEBAT_API_PORT:-8000}"
API_PM2_NAME="${JEBAT_PM2_NAME:-jebat-api}"
# All PM2 apps that must reload code after a deploy (api, mcp server, webui).
PM2_APPS="${JEBAT_PM2_APPS:-jebat-api jebat-mcp jebat-webui}"

SSH_OPTS="-o BatchMode=yes -o StrictHostKeyChecking=accept-new -o ConnectTimeout=10"

START_TIME=$(date +%s)
COMMIT="${JEBAT_DEPLOY_COMMIT:-unknown}"
DELIVERY="${JEBAT_DEPLOY_DELIVERY:-unknown}"

echo "[$(date)] JEBAT auto-deploy starting (commit=$COMMIT delivery=$DELIVERY)"

cd "$REPO_DIR"

# ── 1. Advance the git checkout, capture the changed range ────────────────
echo "[1/6] Updating git checkout..."
OLD=$(git rev-parse HEAD)
git fetch --quiet origin main
git reset --hard --quiet origin/main
NEW=$(git rev-parse HEAD)
SHORT=$(git rev-parse --short HEAD)
echo "  $OLD -> $NEW ($SHORT)"

if [ "$OLD" = "$NEW" ]; then
    echo "  no new commits; nothing to do."
    echo "JEBAT_DEPLOY_RESULT=noop" > /tmp/jebat-deploy-last.json
    echo "JEBAT_DEPLOY_COMMIT=$SHORT" >> /tmp/jebat-deploy-last.json
    exit 0
fi

# Files added/copied/modified/renamed/type-changed vs deleted in the range.
EXISTING=$(git diff --name-only --diff-filter=ACMRT "$OLD" "$NEW" || true)
DELETED=$(git diff --name-only --diff-filter=D "$OLD" "$NEW" || true)
ALL_CHANGED=$(git diff --name-only "$OLD" "$NEW" || true)

if [ -z "$ALL_CHANGED" ]; then
    echo "  commit range touched no files; skipping propagation."
fi

# ── 2. Install deps locally if requirements changed ───────────────────────
if echo "$ALL_CHANGED" | grep -qE '^(requirements[^/]*\.txt|pyproject\.toml)$'; then
    echo "[2/6] requirements changed — installing deps on .65..."
    REQ="requirements.txt"; [ -f requirements.prod.txt ] && REQ="requirements.prod.txt"
    if [ -f .venv/bin/pip ]; then .venv/bin/pip install -r "$REQ" --quiet || true
    else pip install -r "$REQ" --quiet --break-system-packages || true; fi
else
    echo "[2/6] no dependency changes; skipping local pip."
fi

# ── 3. Landing page + static assets (served by nginx on .65) ──────────────
# The web root is NOT a git checkout — it is a plain static directory that
# nginx serves. Copy the page AND mirror assets/ so image changes ship too.
echo "[3/6] Updating landing page + assets..."
if [ -f index.html ]; then
    cp index.html "$WEB_DIR/index.html"
    echo "  index.html updated"
fi
if [ -d assets ]; then
    mkdir -p "$WEB_DIR/assets"
    # --delete keeps the web root from accumulating orphaned images; scope is
    # the assets dir only, never the whole site.
    if command -v rsync &>/dev/null; then
        rsync -a --delete "$REPO_DIR/assets/" "$WEB_DIR/assets/"
    else
        cp -a "$REPO_DIR/assets/." "$WEB_DIR/assets/"
    fi
    echo "  assets mirrored ($(du -sh "$WEB_DIR/assets" 2>/dev/null | cut -f1))"
fi
chown -R www-data:www-data "$WEB_DIR" 2>/dev/null || true

# ── 4. Decide propagation target ──────────────────────────────────────────
# If the API runs here (webhook on the API host), restart in place.
# Otherwise push changed files to the remote API host.
restart_local() {
    command -v pm2 &>/dev/null || return 1
    pm2 describe "$API_PM2_NAME" &>/dev/null || return 1
    for app in $PM2_APPS; do
        pm2 describe "$app" &>/dev/null && pm2 restart "$app" --update-env || true
    done
    pm2 save --force || true
    return 0
}

if restart_local; then
    echo "[4/6] restarted $API_PM2_NAME locally."
    HEALTH_URL="http://127.0.0.1:$API_PORT/health"
    HEALTH_HOST=""
else
    echo "[4/6] API not local — propagating to $API_HOST..."
    # 4a. Back up the files we are about to change on the API host.
    BK="/root/jebat-deploy-backup-$(date +%s)"
    ssh $SSH_OPTS "$API_HOST" "mkdir -p '$BK' && cd '$API_DIR' && \
        printf '%s\n' '$ALL_CHANGED' | tar czf '$BK/pre.tgz' --ignore-failed-read -T - 2>/dev/null; \
        echo \"  backup: $BK/pre.tgz (\$(du -h '$BK/pre.tgz' 2>/dev/null | cut -f1))\"" || \
        echo "  WARNING: backup failed (continuing)"

    # 4b. Targeted rsync of existing changed files (NO --delete on the tree).
    if [ -n "$EXISTING" ]; then
        printf '%s\n' "$EXISTING" | while read -r f; do [ -f "$f" ] && echo "$f"; done \
            > /tmp/jebat-deploy-files.txt
        N=$(wc -l < /tmp/jebat-deploy-files.txt)
        echo "  rsyncing $N changed file(s) to $API_HOST:$API_DIR"
        rsync -az --files-from=/tmp/jebat-deploy-files.txt \
            -e "ssh $SSH_OPTS" "$REPO_DIR/" "$API_HOST:$API_DIR/"
    fi

    # 4c. Remove files deleted in the commit range (tracked deletions only).
    if [ -n "$DELETED" ]; then
        echo "  removing $(echo "$DELETED" | wc -l) deleted file(s) on $API_HOST"
        printf '%s\n' "$DELETED" | ssh $SSH_OPTS "$API_HOST" \
            "cd '$API_DIR' && xargs -r rm -f"
    fi

    # 4d. Install deps on the API host if requirements changed.
    if echo "$ALL_CHANGED" | grep -qE '^(requirements[^/]*\.txt|pyproject\.toml)$'; then
        echo "  installing deps on $API_HOST..."
        ssh $SSH_OPTS "$API_HOST" "cd '$API_DIR' && \
            { [ -f .venv/bin/pip ] && .venv/bin/pip install -r requirements.txt --quiet \
              || pip install -r requirements.txt --quiet --break-system-packages; } || true"
    fi

    # 4e. Restart every live JEBAT service on the remote host (api, mcp, webui).
    echo "[5/6] Restarting [$PM2_APPS] on $API_HOST..."
    ssh $SSH_OPTS "$API_HOST" "cd '$API_DIR' && for app in $PM2_APPS; do \
        pm2 describe \$app >/dev/null 2>&1 && pm2 restart \$app --update-env; done && \
        pm2 save --force" || echo "  WARNING: pm2 restart failed on $API_HOST"
    HEALTH_URL="http://127.0.0.1:$API_PORT/health"
    HEALTH_HOST="$API_HOST"
fi

# ── 6. Verify ─────────────────────────────────────────────────────────────
echo "[6/6] Verifying..."
sleep 5
if [ -n "$HEALTH_HOST" ]; then
    HEALTH=$(ssh $SSH_OPTS "$HEALTH_HOST" "curl -sf --max-time 8 '$HEALTH_URL'" 2>/dev/null || echo "unreachable")
else
    HEALTH=$(curl -sf --max-time 8 "$HEALTH_URL" 2>/dev/null || echo "unreachable")
fi
echo "  API health: $HEALTH"

END_TIME=$(date +%s)
ELAPSED=$((END_TIME - START_TIME))

if echo "$HEALTH" | grep -q healthy; then
    echo "[$(date)] deploy SUCCESS ($ELAPSED s) commit=$SHORT"
    { echo "JEBAT_DEPLOY_RESULT=success"; echo "JEBAT_DEPLOY_COMMIT=$SHORT"; echo "JEBAT_DEPLOY_TIME=$ELAPSED"; } \
        > /tmp/jebat-deploy-last.json
else
    echo "[$(date)] deploy FAILED — API not healthy ($ELAPSED s) commit=$SHORT"
    { echo "JEBAT_DEPLOY_RESULT=failed"; echo "JEBAT_DEPLOY_COMMIT=$SHORT"; echo "JEBAT_DEPLOY_TIME=$ELAPSED"; } \
        > /tmp/jebat-deploy-last.json
    exit 1
fi
