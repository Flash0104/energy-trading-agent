#!/bin/bash

USER=root
HOST=$1

if [ -z "$HOST" ]; then
    echo "Usage: ./scripts/deploy.sh <SERVER_IP>"
    exit 1
fi

echo "🚀 Deploying to $HOST..."

# Copy files
scp -r app tests scripts n8n-workflow.json docker-compose.yml Dockerfile requirements.txt $USER@$HOST:~/energy_trading_agent/

# Run setup script remotely
ssh $USER@$HOST "cd ~/energy_trading_agent && chmod +x scripts/setup_server.sh && ./scripts/setup_server.sh"

# Start services
ssh $USER@$HOST "cd ~/energy_trading_agent && docker compose up -d --build"

echo "✅ Deployment complete! Services running on http://$HOST:8000 and http://$HOST:5678"
