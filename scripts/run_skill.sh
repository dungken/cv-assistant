#!/bin/bash
# ./run_skill.sh > console_skill.log 2>&1

set -e
echo "🧠 Starting Skill Service..."
export DOCKER_BUILDKIT=1
export COMPOSE_DOCKER_CLI_BUILD=1

if docker compose up --build -d skill_service; then
    echo "✅ Skill Service is running!"
    echo "Docs: http://localhost:5002/docs"
else
    echo "❌ Failed to start Skill Service."
    docker compose logs --tail=50 skill_service
    exit 1
fi
