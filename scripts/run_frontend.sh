#!/bin/bash
# ./run_frontend.sh > console_frontend.log 2>&1

set -e
echo "🌐 Starting Frontend..."
export DOCKER_BUILDKIT=1
export COMPOSE_DOCKER_CLI_BUILD=1

if docker compose up --build -d frontend; then
    echo "✅ Frontend is running!"
    echo "URL: http://localhost:5173"
else
    echo "❌ Failed to start Frontend."
    docker compose logs --tail=50 frontend
    exit 1
fi
