#!/bin/bash
# auto-deploy.sh — called by deploy-webhook.py on GitHub push events
set -e

REPO_DIR="/var/www/jebat-core"
WEB_DIR="/var/www/jebat.online"
PUBLIC_WEB_DIR="/var/www/jebat.online"

START_TIME=$(date +%s)

echo "[$(date)] JEBAT auto-deploy starting..."
echo "  commit:   ${JEBAT_DEPLOY_COMMIT:-unknown}"
echo "  delivery: ${JEBAT_DEPLOY_DELIVERY:-unknown}"

if [ ! -d "$REPO_DIR" ]; then
    echo "ERROR: $REPO_DIR does not exist"
    exit 1
fi

cd "$REPO_DIR"

# ── 1. Pull latest code ─────────────────────────────────────────
echo "[1/5] Pulling latest code..."
git fetch origin main
git reset --hard origin/main
COMMIT_SHORT=$(git rev-parse --short HEAD)
echo "  now at $COMMIT_SHORT"

# ── 2. Install dependencies ─────────────────────────────────────
echo "[2/5] Installing Python dependencies..."
REQ_FILE="requirements.txt"
[ -f requirements.prod.txt ] && REQ_FILE="requirements.prod.txt"

if [ -f .venv/bin/pip ]; then
    # Use existing venv
    .venv/bin/pip install -r "$REQ_FILE" --quiet 2>/dev/null && \
        echo "  deps installed via .venv" || true
elif [ -n "$PIP_REQUIRE_VIRTUALENV" ]; then
    # PEP 668 system — bypass with env override
    PIP_REQUIRE_VIRTUALENV=false pip install -r "$REQ_FILE" --quiet 2>/dev/null && \
        echo "  deps installed (PEP 668 bypass)" || true
else
    pip install -r "$REQ_FILE" --quiet --break-system-packages 2>/dev/null && \
        echo "  deps installed" || \
        echo "  WARNING: pip install failed — landing page deploy does not need deps"
fi

# ── 3. Copy landing page ────────────────────────────────────────
echo "[3/5] Deploying landing page..."
if [ -f index.html ]; then
    cp index.html "$WEB_DIR/index.html"
    chown www-data:www-data "$WEB_DIR/index.html" 2>/dev/null || true
    echo "  landing page updated"
fi

# ── 4. Restart backend services ─────────────────────────────────
echo "[4/5] Restarting services..."
# Try PM2 first (current production setup)
if command -v pm2 &>/dev/null; then
    pm2 restart jebat-api 2>/dev/null || \
    pm2 start "python -m uvicorn main:app --host 0.0.0.0 --port 8080 --workers 4" \
        --name jebat-api 2>/dev/null || true
    pm2 save --force 2>/dev/null || true
    echo "  PM2 restart done"
fi
# Also try Docker (alternative setup)
if command -v docker &>/dev/null; then
    docker restart jebat-api jebat-webui 2>/dev/null && echo "  Docker containers restarted" || true
fi

# ── 5. Verify ───────────────────────────────────────────────────
echo "[5/5] Verifying..."
sleep 3
HEALTH=$(curl -sf http://localhost:8080/health 2>/dev/null || echo "unreachable")
echo "  API health: $HEALTH"

END_TIME=$(date +%s)
ELAPSED=$((END_TIME - START_TIME))

echo "[$(date)] deploy complete ($ELAPSED seconds)"
echo "JEBAT_DEPLOY_RESULT=success" > /tmp/jebat-deploy-last.json
echo "JEBAT_DEPLOY_COMMIT=$COMMIT_SHORT" >> /tmp/jebat-deploy-last.json
echo "JEBAT_DEPLOY_TIME=$ELAPSED" >> /tmp/jebat-deploy-last.json
