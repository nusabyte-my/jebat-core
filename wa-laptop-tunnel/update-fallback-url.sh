# Update VPS router with ngrok URL
# Usage: ./update-fallback-url.sh http://xxxx.ngrok.io

#!/bin/bash
NGROK_URL=${1?"Usage: $0 http://xxxx.ngrok.io"}

# Update running container
docker exec wa-router sh -c "export BAILEYS_URL=${NGROK_URL} && echo 'Updated BAILEYS_URL to ${NGROK_URL}'"

# Or recreate with new env
docker compose -f /tmp/wa-hybrid/docker-compose.wa-hybrid.yml stop wa-router
docker compose -f /tmp/wa-hybrid/docker-compose.wa-hybrid.yml rm -f wa-router

# Start with new URL
BAILEYS_URL=${NGROK_URL} docker compose -f /tmp/wa-hybrid/docker-compose.wa-hybrid.yml up -d wa-router

echo "Router updated. Test with:"
echo "  curl http://localhost:8083/api/v1/admin/overview"
