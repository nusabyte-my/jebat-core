#!/bin/bash
# deploy-to-vps.sh — Syncs code from local workspace to VPS and deploys
# Usage: ./deploy-to-vps.sh

set -e

# Production Mainframe VPS (.206)
VPS_HOST="root@72.62.255.206"
VPS_KEY="$HOME/.ssh/id_ed25519_vps"
VPS_CODE_DIR="/var/www/jebat-core"
VPS_WEB_DIR="/var/www/jebat.online/out"
PUBLIC_VPS_HOST="root@72.62.254.65"
PUBLIC_WEB_DIR="/var/www/jebat.online"
LOCAL_DIR="$(cd "$(dirname "$0")/.." && pwd)"
AUTH_HELPER="$LOCAL_DIR/scripts/vps_auth_helper.py"

SSH_OPTS="-o StrictHostKeyChecking=no"
if [ -f "$VPS_KEY" ]; then
  SSH_OPTS="-i $VPS_KEY $SSH_OPTS"
fi

echo "⚔️  JEBAT VPS Deployer (.206 Mainframe)"
echo "====================================="
echo ""
echo "Source: $LOCAL_DIR"
echo "VPS Code: $VPS_HOST:$VPS_CODE_DIR"
echo "VPS Web:  $VPS_HOST:$VPS_WEB_DIR"
echo "Public Web: $PUBLIC_VPS_HOST:$PUBLIC_WEB_DIR"
echo "Using Key: $VPS_KEY"
echo "Automating with: $AUTH_HELPER"
echo ""

# Helper function to run commands with automated password
run_auth() {
    python3 "$AUTH_HELPER" "$1"
}

# Step 1: Create code directory on VPS if it doesn't exist
echo "📁 Setting up VPS code directory..."
run_auth "ssh $SSH_OPTS $VPS_HOST \"mkdir -p $VPS_CODE_DIR $VPS_WEB_DIR\""

# Step 2: Sync code to VPS (excluding node_modules, .next, .git, etc.)
echo "🔄 Syncing code to VPS..."
run_auth "rsync -avz --delete \
  -e \"ssh $SSH_OPTS\" \
  --exclude='node_modules' \
  --exclude='.next' \
  --exclude='.git' \
  --exclude='jebat-core' \
  --exclude='jebat-online' \
  --exclude='out' \
  --exclude='__pycache__' \
  --exclude='*.pyc' \
  --exclude='.env*' \
  --exclude='.jebat' \
  --exclude='training/output' \
  --exclude='training/*.gguf' \
  --exclude='jebat-npm/*.tgz' \
  --exclude='.claude' \
  --exclude='.gemini' \
  --exclude='*.egg-info' \
  --exclude='.venv*' \
  --exclude='llama.cpp' \
  --exclude='models' \
  --exclude='.qwen' \
  \"$LOCAL_DIR/\" $VPS_HOST:$VPS_CODE_DIR/"

echo "✅ Code synced to $VPS_CODE_DIR"

# Step 3: Publish the current static landing page.
echo "🚀 Deploying landing page to web directory..."
run_auth "ssh $SSH_OPTS $VPS_HOST \"cp $VPS_CODE_DIR/index.html $VPS_WEB_DIR/index.html && chown www-data:www-data $VPS_WEB_DIR/index.html\""

# The public Cloudflare-facing node serves the landing root from .65.
echo "🌐 Publishing landing page to public web root..."
run_auth "scp -o StrictHostKeyChecking=no \"$LOCAL_DIR/index.html\" $PUBLIC_VPS_HOST:$PUBLIC_WEB_DIR/index.html"
run_auth "ssh -o StrictHostKeyChecking=no $PUBLIC_VPS_HOST \"chown www-data:www-data $PUBLIC_WEB_DIR/index.html\""

# Step 5: Install dependencies and Restart backend API
echo "🔄 Restarting backend API..."
run_auth "ssh $SSH_OPTS $VPS_HOST \"docker restart jebat-api jebat-webui\""

# Step 6: Verify deployment
echo ""
echo "🔍 Verifying deployment..."
sleep 5
HEALTH=$(run_auth "ssh $SSH_OPTS $VPS_HOST \"curl -s http://localhost:8000/api/v1/health\"" 2>/dev/null || echo "API offline")
LANDING=$(run_auth "ssh $SSH_OPTS $VPS_HOST \"curl -s -o /dev/null -w '%{http_code}' https://127.0.0.1/ -H 'Host: jebat.online' -k\"" 2>/dev/null || echo "000")
GELANGGANG=$(run_auth "ssh $SSH_OPTS $VPS_HOST \"curl -s -o /dev/null -w '%{http_code}' https://127.0.0.1/gelanggang/ -H 'Host: jebat.online' -k\"" 2>/dev/null || echo "000")

echo ""
echo "📊 Deployment Results:"
echo "   API Health: $HEALTH"
echo "   Landing: HTTP $LANDING"
echo "   Gelanggang: HTTP $GELANGGANG"
echo ""

if [ "$LANDING" = "200" ] || [ "$LANDING" = "301" ] || [ "$LANDING" = "308" ]; then
  echo "✅ Deployment successful on .206!"
  echo "   🌐 https://jebat.online"
else
  echo "⚠️  Some services may need attention on .206"
  echo "   Check: docker logs jebat-api"
fi
