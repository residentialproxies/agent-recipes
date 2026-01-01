#!/bin/bash
set -e

# Deployment script for VPS (107.174.42.198)
# This script syncs code and deploys the FastAPI backend

VPS_HOST="107.174.42.198"
VPS_USER="root"
VPS_PATH="/opt/docker-projects/agent-recipes"
LOCAL_PATH="/Volumes/SSD/dev/new/agent-recipes"

echo "🚀 Deploying agent-recipes to VPS..."

# 1. Sync code to VPS
echo "📦 Syncing code to VPS..."
rsync -avz --exclude 'node_modules' \
  --exclude '.git' \
  --exclude '.venv' \
  --exclude '__pycache__' \
  --exclude '*.pyc' \
  --exclude '.pytest_cache' \
  --exclude '.next' \
  --exclude 'site' \
  --exclude '.env' \
  "${LOCAL_PATH}/" \
  "${VPS_USER}@${VPS_HOST}:${VPS_PATH}/"

echo "✅ Code synced successfully"

# 2. Deploy on VPS
echo "🐳 Deploying with Docker..."
ssh "${VPS_USER}@${VPS_HOST}" "cd ${VPS_PATH} && \
  docker-compose down && \
  docker-compose pull || true && \
  docker-compose build --no-cache && \
  docker-compose up -d"

echo "✅ Deployment complete!"
echo "🌐 Backend should be available at: http://${VPS_HOST}:8000"
echo "📊 Check logs with: ssh ${VPS_USER}@${VPS_HOST} 'cd ${VPS_PATH} && docker-compose logs -f'"
