#!/bin/bash
# sync-to-vps.sh — Syncs code from local workspace to VPS code folder
# Usage: ./sync-to-vps.sh

set -e

VPS_HOST="root@72.62.254.65"
VPS_CODE_DIR="/var/www/jebat-core"
LOCAL_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "⚔️  JEBAT Sync to VPS"
echo "====================="
echo ""
echo "Source: $LOCAL_DIR"
echo "VPS Code: $VPS_HOST:$VPS_CODE_DIR"
echo ""

# Sync code to VPS (excluding node_modules, .next, .git, etc.)
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

echo ""
echo "✅ Code synced to $VPS_CODE_DIR"
echo ""
echo "Next step: ssh $VPS_HOST 'cd $VPS_CODE_DIR && ./deploy.sh'"
