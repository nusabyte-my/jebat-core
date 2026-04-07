#!/usr/bin/env bash
set -euo pipefail

if [[ ! -f deploy/vps/.env.production ]]; then
  cp deploy/vps/.env.production.example deploy/vps/.env.production
  echo "Created deploy/vps/.env.production from template. Fill in real API keys before starting." >&2
fi

docker compose -f deploy/vps/docker-compose.prod.yml up -d --build
