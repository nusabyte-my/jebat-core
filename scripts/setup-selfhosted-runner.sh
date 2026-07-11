#!/bin/bash
# setup-selfhosted-runner.sh — Install a GitHub Actions self-hosted runner on this machine
#
# Note: This bypasses GitHub billing for Actions minutes. Self-hosted runners
# are free regardless of your GitHub plan.
#
# Prerequisites:
#   - Run as a user with sudo (NOT root)
#   - A GitHub Personal Access Token (classic) with repo scope
#   - The repo must already exist on GitHub
#
# Usage:
#   bash scripts/setup-selfhosted-runner.sh --token ghp_xxxx --repo nusabyte-my/jebat-core
#
# After setup, go to GitHub → Settings → Actions → Runners to verify.

set -e

TOKEN=""
REPO="nusabyte-my/jebat-core"
RUNNER_DIR="/opt/actions-runner"

while [ $# -gt 0 ]; do
    case "$1" in
        --token) TOKEN="$2"; shift 2 ;;
        --repo) REPO="$2"; shift 2 ;;
        --dir) RUNNER_DIR="$2"; shift 2 ;;
        --help) echo "Usage: $0 --token <ghp_xxx> [--repo nusabyte-my/jebat-core] [--dir /opt/actions-runner]"; exit 0 ;;
        *) echo "Unknown: $1"; exit 1 ;;
    esac
done

if [ -z "$TOKEN" ]; then
    echo "ERROR: --token is required"
    exit 1
fi

echo "============================================"
echo " JEBAT Self-Hosted Runner — Setup"
echo "============================================"
echo "  Repo:  $REPO"
echo "  Dir:   $RUNNER_DIR"
echo ""

ARCH=$(uname -m)
case "$ARCH" in
    x86_64)  RUNNER_ARCH="x64" ;;
    aarch64) RUNNER_ARCH="arm64" ;;
    armv7l)  RUNNER_ARCH="arm" ;;
    *) echo "Unsupported arch: $ARCH"; exit 1 ;;
esac

# 1. Create runner user if needed
if ! id -u runner &>/dev/null; then
    echo "[1/6] Creating 'runner' user..."
    sudo useradd -m -s /bin/bash runner
    sudo passwd -d runner
else
    echo "[1/6] 'runner' user exists"
fi

# 2. Install dependencies
echo "[2/6] Installing dependencies..."
sudo apt-get update -qq
sudo apt-get install -y -qq curl jq

# 3. Download and install runner
echo "[3/6] Downloading GitHub Actions runner..."
sudo mkdir -p "$RUNNER_DIR"
sudo chown runner:runner "$RUNNER_DIR"

RUNNER_VERSION=$(curl -s https://api.github.com/repos/actions/runner/releases/latest | jq -r '.tag_name' | sed 's/^v//')
DOWNLOAD_URL="https://github.com/actions/runner/releases/download/v${RUNNER_VERSION}/actions-runner-linux-${RUNNER_ARCH}-${RUNNER_VERSION}.tar.gz"

echo "  Version: $RUNNER_VERSION"
echo "  Arch:    $RUNNER_ARCH"
echo "  URL:     $DOWNLOAD_URL"

sudo -u runner bash -c "cd '$RUNNER_DIR' && curl -sSL '$DOWNLOAD_URL' -o runner.tar.gz && tar xzf runner.tar.gz && rm runner.tar.gz"

# 4. Get runner token
echo "[4/6] Obtaining runner registration token..."
# Use GitHub API to get a runner token (PAT-based)
TOKEN_URL="https://api.github.com/repos/$REPO/actions/runners/registration-token"
REG_TOKEN=$(curl -s -X POST "$TOKEN_URL" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Accept: application/vnd.github.v3+json" | jq -r '.token')

if [ -z "$REG_TOKEN" ] || [ "$REG_TOKEN" = "null" ]; then
    echo "  Failed to get registration token. Check your PAT."
    echo "  Alternative: Get token manually from GitHub → Settings → Actions → Runners → New runner"
    echo "  Then run: sudo -u runner $RUNNER_DIR/config.sh --url https://github.com/$REPO --token <MANUAL_TOKEN>"
    exit 1
fi

# 5. Configure runner
echo "[5/6] Configuring runner..."
sudo -u runner bash -c "cd '$RUNNER_DIR' && \
    ./config.sh --url 'https://github.com/$REPO' --token '$REG_TOKEN' \
    --name 'jebat-vps-runner' --labels 'jebat,self-hosted,linux,$ARCH' \
    --replace --unattended"

# 6. Install as systemd service
echo "[6/6] Installing systemd service..."
sudo bash -c "cd '$RUNNER_DIR' && ./svc.sh install runner && ./svc.sh start"

sleep 2
if systemctl is-active --quiet actions.runner.$REPO.jebat-vps-runner.service 2>/dev/null; then
    echo ""
    echo "============================================"
    echo "  RUNNER INSTALLED AND ACTIVE"
    echo "============================================"
    echo ""
    echo "  Verify at: https://github.com/$REPO/settings/actions/runners"
    echo "  Logs: journalctl -u actions.runner.$REPO.jebat-vps-runner -f"
    echo ""
    echo "  Now update your workflow files to use: runs-on: [self-hosted, jebat, linux]"
else
    echo "  Service may need manual start. Check: systemctl status actions.runner.*"
fi
