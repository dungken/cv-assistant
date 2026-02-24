#!/bin/bash
# ./1_run_infra.sh > console_infra.log 2>&1

set -e
echo "🔧 Starting Infrastructure (PostgreSQL & ChromaDB)..."
export DOCKER_BUILDKIT=1
export COMPOSE_DOCKER_CLI_BUILD=1
export CHROMA_PATH="./knowledge_base/chroma_db"

if docker compose up -d postgres chromadb; then
    echo "✅ Infrastructure is UP!"
    echo "PostgreSQL: localhost:5432"
    echo "ChromaDB:   localhost:8000"
else
    echo "❌ Failed to start infrastructure."
    docker compose logs --tail=50 postgres chromadb
    exit 1
fi
