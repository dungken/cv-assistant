#!/bin/bash

# Master Run Script for CV Assistant
# Exit immediately if a command exits with a non-zero status. 
# ./run_project.sh > console.log 2>&1

set -e

echo "🚀 Starting CV Assistant Ecosystem..."

# 1. Setup Environment
if [ ! -d "cv_assistant_env" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv cv_assistant_env
    source cv_assistant_env/bin/activate
    pip install -r requirements.txt
else
    source cv_assistant_env/bin/activate
fi

# 2. Setup Cloud Storage (Optional)
if [ -f "scripts/mount_drive.sh" ] && [ "$USE_DRIVE" = "true" ]; then
    ./scripts/mount_drive.sh
    export DATA_PATH="/mnt/cv_assistant_data"
    export CHROMA_PATH="$DATA_PATH/knowledge_base/chroma_db"
else
    # Default local path
    export CHROMA_PATH="./knowledge_base/chroma_db"
fi

# 3. Ingest O*NET Data (If not already done)
echo "🧠 Checking Skill Intelligence data..."
python3 scripts/ingest_onet_skills.py

# 4. Launch Docker Stack
echo "🐳 Launching Docker containers..."

# Ensure we use BuildKit for faster, reliable builds with Docker V2
export DOCKER_BUILDKIT=1
export COMPOSE_DOCKER_CLI_BUILD=1

if docker compose up --build -d; then
    echo "✅ CV Assistant is running!"
    echo "------------------------------------------------"
    echo "Frontend:   http://localhost:5173"
    echo "Gateway:    http://localhost:8081/swagger-ui.html"
    echo "Chatbot:    http://localhost:5004/docs"
    echo "Skill:      http://localhost:5002/docs"
    echo "Career:     http://localhost:5003/docs"
    echo "NER:        http://localhost:5005/docs"
    echo "------------------------------------------------"
    echo "Run 'docker compose logs -f' to see activity."
else
    echo "❌ Docker build or launch failed!"
    echo "📜 Tailing logs to find the cause..."
    docker compose logs --tail=100
    exit 1
fi
