#!/bin/bash
# ./run_ner.sh > console_ner.log 2>&1

set -e
echo "🔍 Starting NER Service..."
export DOCKER_BUILDKIT=1
export COMPOSE_DOCKER_CLI_BUILD=1

if docker compose up --build -d ner_service; then
    echo "✅ NER Service is running!"
    echo "Docs: http://localhost:5005/docs"
else
    echo "❌ Failed to start NER Service."
    docker compose logs --tail=50 ner_service
    exit 1
fi
