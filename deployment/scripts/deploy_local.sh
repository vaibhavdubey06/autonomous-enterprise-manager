#!/bin/bash
set -e

echo "Deploying Autonomous Enterprise Manager locally using Docker Compose..."

cd "$(dirname "$0")/../compose"

# Build and start the dev stack
docker-compose -f docker-compose.dev.yml up --build -d

echo "Waiting for services to become healthy..."
sleep 15

echo "Deployment complete."
echo "Backend: http://localhost:8000"
echo "Frontend: http://localhost:8501"
