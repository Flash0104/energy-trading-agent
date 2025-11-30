#!/bin/bash

# Update and upgrade
apt-get update && apt-get upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# Install Docker Compose
apt-get install -y docker-compose-plugin

# Start Docker
systemctl start docker
systemctl enable docker

echo "✅ Server setup complete! Docker is running."
