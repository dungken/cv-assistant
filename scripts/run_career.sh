#!/bin/bash
# ./run_career.sh > console_career.log 2>&1

set -e
echo "📈 Starting Career Service..."
export DOCKER_BUILDKIT=1
export COMPOSE_DOCKER_CLI_BUILD=1

if docker compose up --build -d career_service; then
    echo "✅ Career Service is running!"
    echo "Docs: http://localhost:5003/docs"
else
    echo "❌ Failed to start Career Service."
    docker compose logs --tail=50 career_service
    exit 1
fi
