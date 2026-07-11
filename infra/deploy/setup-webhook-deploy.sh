#!/bin/bash
# setup-webhook-deploy.sh — one-command setup for GitHub webhook auto-deployer
#
# Prerequisites:
#   - Run as root on the VPS
#   - nginx already installed and configured for jebat.online
#   - repo already cloned at /var/www/jebat-core
#
# Usage:
#   curl -fsSL https://jebat.online/setup-webhook-deploy.sh | bash -s -- --secret your-webhook-secret
#   # or locally:
#   sudo bash infra/deploy/setup-webhook-deploy.sh --secret your-webhook-secret

set -e

SECRET=""
PORT="8081"
REPO_DIR="/var/www/jebat-core"
WEBHOOK_SCRIPT="$REPO_DIR/infra/deploy/deploy-webhook.py"
NGINX_CONF_SRC="$REPO_DIR/infra/deploy/nginx.webhook.conf"  # reference only (injected into main config)
SERVICE_FILE="/etc/systemd/system/jebat-deploy-webhook.service"

while [ $# -gt 0 ]; do
    case "$1" in
        --secret) SECRET="$2"; shift 2 ;;
        --port) PORT="$2"; shift 2 ;;
        --help)
            echo "Usage: $0 --secret <webhook-secret> [--port 8081]"
            exit 0
            ;;
        *) echo "Unknown: $1"; exit 1 ;;
    esac
done

if [ -z "$SECRET" ]; then
    echo "ERROR: --secret is required (set a random string, then use it in GitHub webhook settings)"
    exit 1
fi

if [ ! -d "$REPO_DIR" ]; then
    echo "ERROR: $REPO_DIR not found. Clone the repo first:"
    echo "  git clone https://github.com/nusabyte-my/jebat-core.git $REPO_DIR"
    exit 1
fi

echo "============================================"
echo " JEBAT Auto-Deploy Webhook — Setup"
echo "============================================"
echo "  Repo:       $REPO_DIR"
echo "  Port:       $PORT"
echo "  Secret:     ${SECRET:0:4}... (set)"
echo ""

# ── 1. Inject webhook location into main jebat.online nginx config ──
echo "[1/4] Adding /deploy-webhook to nginx..."
NGINX_MAIN="/etc/nginx/sites-enabled/jebat.online"
if [ -f "$NGINX_MAIN" ]; then
    # Inject the location block before the final closing brace
    sed -i '/^}$/i\
    # JEBAT auto-deploy webhook (added by setup-webhook-deploy.sh)\
    location /deploy-webhook {\
        proxy_pass http://127.0.0.1:'"$PORT"';\
        proxy_set_header Host $host;\
        proxy_set_header X-Real-IP $remote_addr;\
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;\
        proxy_set_header X-Forwarded-Proto https;\
        proxy_buffering off;\
        proxy_cache off;\
        proxy_read_timeout 120s;\
        proxy_send_timeout 30s;\
        client_max_body_size 10m;\
        access_log /var/log/nginx/deploy-webhook.access.log;\
        error_log  /var/log/nginx/deploy-webhook.error.log;\
    }' "$NGINX_MAIN"
    echo "  injected location into $NGINX_MAIN"
else
    echo "  WARNING: $NGINX_MAIN not found — add webhook location manually"
fi

# ── 2. Systemd service ─────────────────────────────────────────
echo "[2/4] Installing systemd service..."
cat > "$SERVICE_FILE" <<SERVICE
[Unit]
Description=JEBAT Auto-Deploy Webhook Listener
After=network.target

[Service]
ExecStart=$REPO_DIR/infra/deploy/deploy-webhook.py --port $PORT --secret $SECRET
WorkingDirectory=$REPO_DIR
Restart=always
RestartSec=5
User=root

[Install]
WantedBy=multi-user.target
SERVICE

chmod 644 "$SERVICE_FILE"
echo "  service: $SERVICE_FILE"

# ── 3. Make scripts executable ─────────────────────────────────
echo "[3/4] Making scripts executable..."
chmod +x "$WEBHOOK_SCRIPT" 2>/dev/null || true
chmod +x "$REPO_DIR/scripts/auto-deploy.sh" 2>/dev/null || true
echo "  done"

# ── 4. Enable and start ────────────────────────────────────────
echo "[4/4] Starting service..."
systemctl daemon-reload
systemctl enable jebat-deploy-webhook
systemctl restart jebat-deploy-webhook

sleep 2
if systemctl is-active --quiet jebat-deploy-webhook; then
    echo "  OK: jebat-deploy-webhook is running"
else
    echo "  FAILED: check 'journalctl -u jebat-deploy-webhook -n 30'"
    exit 1
fi

# Reload nginx (test config first, then reload)
nginx -t 2>/dev/null && (systemctl reload nginx 2>/dev/null || nginx -s reload 2>/dev/null) && \
    echo "  nginx reloaded" || echo "  WARNING: nginx config test failed — check 'nginx -t'"

echo ""
echo "============================================"
echo "  SETUP COMPLETE"
echo "============================================"
echo ""
echo "Next step: Add webhook in GitHub:"
echo "  1. Go to: https://github.com/nusabyte-my/jebat-core/settings/hooks"
echo "  2. Click 'Add webhook'"
echo "  3. Payload URL: https://jebat.online/deploy-webhook"
echo "  4. Content type: application/json"
echo "  5. Secret: $SECRET"
echo "  6. Events: Just the push event"
echo "  7. Active: ✅"
echo "  8. Add webhook"
echo ""
echo "Test: git push main → webhook fires → auto-deploy runs"
echo "Logs: journalctl -u jebat-deploy-webhook -f"
