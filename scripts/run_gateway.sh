#!/bin/bash
# ./2_run_gateway.sh > console_gateway.log 2>&1

set -e
echo "🚀 Starting API Gateway..."
export DOCKER_BUILDKIT=1
export COMPOSE_DOCKER_CLI_BUILD=1

if docker compose up --build -d api_gateway; then
    echo "✅ API Gateway is running!"
    echo "Docs: http://localhost:8081/swagger-ui.html"
else
    echo "❌ Failed to start API Gateway."
    docker compose logs --tail=50 api_gateway
    exit 1
fi
