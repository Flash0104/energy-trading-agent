#!/bin/bash

# Energy Trading Insight Agent - Deployment Script
# Usage: ./deploy.sh

set -e

echo "🚀 Starting Deployment..."

# 1. Update System
echo "📦 Updating system packages..."
sudo apt-get update && sudo apt-get upgrade -y

# 2. Install Docker & Docker Compose
if ! command -v docker &> /dev/null; then
    echo "🐳 Installing Docker..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo usermod -aG docker $USER
    rm get-docker.sh
else
    echo "✅ Docker is already installed."
fi

# 3. Setup Project
echo "📂 Setting up project..."
# Assuming the repo is cloned or files are copied here.
# If this script is run from the project root:

if [ ! -f .env ]; then
    echo "⚠️ .env file not found! Creating from template..."
    cp .env.template .env
    echo "❗ Please edit .env with your API keys before running docker-compose up"
fi

# 4. Start Services
echo "🔥 Starting services..."
sudo docker compose up -d --build

echo "✅ Deployment Complete!"
echo "API is running on port 8000"
echo "n8n is running on port 5678"
