#!/bin/bash
# ./run_chatbot.sh > console_chatbot.log 2>&1

set -e
echo "🤖 Starting Chatbot Service..."
export DOCKER_BUILDKIT=1
export COMPOSE_DOCKER_CLI_BUILD=1

if docker compose up --build -d chatbot_service; then
    echo "✅ Chatbot Service is running!"
    echo "Docs: http://localhost:5004/docs"
else
    echo "❌ Failed to start Chatbot Service."
    docker compose logs --tail=50 chatbot_service
    exit 1
fi
