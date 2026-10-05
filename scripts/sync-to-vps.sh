#!/bin/bash
# sync-to-vps.sh — Syncs code from local workspace to VPS code folder
# Usage: ./sync-to-vps.sh

set -e

VPS_HOST="root@72.62.255.206"
VPS_CODE_DIR="/var/www/jebat-core"
# Repo root, not scripts/ — this rsync is destructive (--delete); mirroring
# scripts/ over /var/www/jebat-core would wipe the API host's code tree.
LOCAL_DIR="$(cd "$(dirname "$0")/.." && pwd)"

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
echo "Next step: restart services on the VPS (pm2 restart jebat-api jebat-mcp jebat-webui --update-env)"
echo "or run scripts/deploy-tar-over-ssh.sh (BACKUP=1) for a full deployment."
