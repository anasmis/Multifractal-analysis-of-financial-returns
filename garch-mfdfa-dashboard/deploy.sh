#!/usr/bin/env bash
# Sequential build + deploy for small (free-tier) EC2 instances.
# Building both images at once OOMs on 1 GB RAM, so we build one at a time.
set -euo pipefail

cd "$(dirname "$0")"

echo "==> Building backend image..."
docker compose build backend

echo "==> Building frontend image (this is the heavy one)..."
docker compose build frontend

echo "==> Starting containers..."
docker compose up -d

echo
echo "Done. Open: http://<your-ec2-public-ip>"
docker compose ps
