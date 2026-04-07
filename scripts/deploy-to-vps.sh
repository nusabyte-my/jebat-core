#!/bin/bash
# deploy-to-vps.sh — Syncs code from local workspace to VPS and deploys
# Usage: ./deploy-to-vps.sh

set -e

VPS_HOST="root@72.62.254.65"
VPS_CODE_DIR="/var/www/jebat-core"
VPS_WEB_DIR="/var/www/jebat.online"
LOCAL_DIR="$(cd "$(dirname "$0")/.." && pwd)"

echo "⚔️  JEBAT VPS Deployer"
echo "======================"
echo ""
echo "Source: $LOCAL_DIR"
echo "VPS Code: $VPS_HOST:$VPS_CODE_DIR"
echo "VPS Web:  $VPS_HOST:$VPS_WEB_DIR"
echo ""

# Step 1: Create code directory on VPS if it doesn't exist
echo "📁 Setting up VPS code directory..."
ssh $VPS_HOST "mkdir -p $VPS_CODE_DIR $VPS_WEB_DIR"

# Step 2: Sync code to VPS (excluding node_modules, .next, .git, etc.)
echo "🔄 Syncing code to VPS..."
rsync -avz --delete \
  --exclude='node_modules' \
  --exclude='.next' \
  --exclude='.git' \
  --exclude='jebat-core' \
  --exclude='jebat-online' \
  --exclude='out' \
  --exclude='__pycache__' \
  --exclude='*.pyc' \
  --exclude='.env' \
  --exclude='.claude' \
  --exclude='.gemini' \
  --exclude='*.egg-info' \
  "$LOCAL_DIR/" "$VPS_HOST:$VPS_CODE_DIR/"

echo "✅ Code synced to $VPS_CODE_DIR"

# Step 3: Build frontend on VPS
echo "🔨 Building frontend on VPS..."
ssh $VPS_HOST "cd $VPS_CODE_DIR/apps/web && npm install && npx next build"

# Step 4: Deploy frontend build to web directory
echo "🚀 Deploying frontend to web directory..."
ssh $VPS_HOST "rm -rf $VPS_WEB_DIR/_next $VPS_WEB_DIR/dashboard $VPS_WEB_DIR/demo $VPS_WEB_DIR/docs $VPS_WEB_DIR/onboarding $VPS_WEB_DIR/setup $VPS_WEB_DIR/integration $VPS_WEB_DIR/gelanggang $VPS_WEB_DIR/guides $VPS_WEB_DIR/index.html $VPS_WEB_DIR/*.svg $VPS_WEB_DIR/*.ico $VPS_WEB_DIR/*.txt $VPS_WEB_DIR/__next* $VPS_WEB_DIR/404 $VPS_WEB_DIR/404.html $VPS_WEB_DIR/_not-found 2>/dev/null"
ssh $VPS_HOST "cp -r $VPS_CODE_DIR/apps/web/out/* $VPS_WEB_DIR/ && chown -R www-data:www-data $VPS_WEB_DIR/"

# Step 5: Restart backend API
echo "🔄 Restarting backend API..."
ssh $VPS_HOST "cd $VPS_CODE_DIR/apps/api && pkill -f jebat_api 2>/dev/null || true; nohup python -m services.api.jebat_api > /var/log/jebat-api.log 2>&1 &"

# Step 6: Verify deployment
echo ""
echo "🔍 Verifying deployment..."
sleep 3
HEALTH=$(ssh $VPS_HOST "curl -s http://localhost:8000/api/v1/health" 2>/dev/null || echo "API offline")
LANDING=$(ssh $VPS_HOST "curl -s -o /dev/null -w '%{http_code}' https://jebat.online/" 2>/dev/null || echo "000")
GELANGGANG=$(ssh $VPS_HOST "curl -s -o /dev/null -w '%{http_code}' https://jebat.online/gelanggang/" 2>/dev/null || echo "000")

echo ""
echo "📊 Deployment Results:"
echo "   API Health: $HEALTH"
echo "   Landing: HTTP $LANDING"
echo "   Gelanggang: HTTP $GELANGGANG"
echo ""

if [ "$LANDING" = "200" ] && [ "$GELANGGANG" = "200" ]; then
  echo "✅ Deployment successful!"
  echo "   🌐 https://jebat.online"
  echo "   🏛️ https://jebat.online/gelanggang/"
else
  echo "⚠️  Some services may need attention"
  echo "   SSH: ssh $VPS_HOST"
  echo "   Check: tail -f /var/log/nginx/error.log"
  echo "   Check: tail -f /var/log/jebat-api.log"
fi
