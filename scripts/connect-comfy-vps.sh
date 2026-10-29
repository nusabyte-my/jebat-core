#!/usr/bin/env bash
# Reverse tunnel: VPS 127.0.0.1:8189 -> workstation 127.0.0.1:8189.
set -euo pipefail
ssh -N -T -o ServerAliveInterval=30 -o ServerAliveCountMax=3 -o ExitOnForwardFailure=yes \
  -R 127.0.0.1:8189:127.0.0.1:8189 \
  root@72.62.255.206
