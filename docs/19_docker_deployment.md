# 19. Docker Deployment Guide

> **Document Version**: 1.0
> **Last Updated**: 2026-01-23
> **Status**: Approved
> **Product Name**: CV Assistant
> **Related Documents**: [09_system_architecture.md](./09_system_architecture.md)

---

## 1. Overview

This document provides comprehensive Docker deployment configuration for CV Assistant, including all microservices, databases, and AI components.

### 1.1 Hardware Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| **CPU** | 4 cores | 8+ cores |
| **RAM** | 16 GB | 32 GB |
| **Storage** | 50 GB SSD | 100 GB SSD |
| **GPU** | Not required | Optional (CUDA) |

**Target Hardware**: Acer Aspire 7, 16GB RAM, CPU-only

### 1.2 Service Summary

| Service | Image/Build | Port | Purpose |
|---------|-------------|------|---------|
| Frontend | Node.js build | 3000 | React UI |
| API Gateway | Java Spring Boot | 8080 | Auth + Routing |
| NER Service | Python FastAPI | 5001 | CV extraction |
| Skill Service | Python FastAPI | 5002 | Skill matching |
| Career Service | Python FastAPI | 5003 | Career paths |
| Chatbot Service | Python FastAPI | 5004 | Conversational AI |
| PostgreSQL | postgres:15 | 5432 | Main database |
| ChromaDB | chromadb/chroma | 8000 | Vector database |
| Ollama | ollama/ollama | 11434 | LLM server |

---

## 2. Directory Structure

```
cv-assistant/
├── docker-compose.yml
├── docker-compose.dev.yml
├── docker-compose.prod.yml
├── .env
├── .env.example
├── frontend/
│   ├── Dockerfile
│   └── nginx.conf
├── api-gateway/
│   └── Dockerfile
├── services/
│   ├── ner-service/
│   │   ├── Dockerfile
│   │   └── requirements.txt
│   ├── skill-service/
│   │   ├── Dockerfile
│   │   └── requirements.txt
│   ├── career-service/
│   │   ├── Dockerfile
│   │   └── requirements.txt
│   └── chatbot-service/
│       ├── Dockerfile
│       └── requirements.txt
├── scripts/
│   ├── init-db.sql
│   ├── seed-data.sh
│   └── pull-models.sh
└── volumes/
    ├── postgres-data/
    ├── chroma-data/
    └── ollama-models/
```

---

## 3. Docker Compose Configuration

### 3.1 Main docker-compose.yml

```yaml
version: '3.8'

services:
  # ===========================================
  # DATABASES
  # ===========================================

  postgres:
    image: postgres:15-alpine
    container_name: cv-assistant-postgres
    restart: unless-stopped
    environment:
      POSTGRES_USER: ${DB_USER:-cvassistant}
      POSTGRES_PASSWORD: ${DB_PASSWORD:-cvassistant123}
      POSTGRES_DB: ${DB_NAME:-cv_assistant}
    ports:
      - "5432:5432"
    volumes:
      - postgres-data:/var/lib/postgresql/data
      - ./scripts/init-db.sql:/docker-entrypoint-initdb.d/init.sql
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${DB_USER:-cvassistant}"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - cv-assistant-network

  chromadb:
    image: chromadb/chroma:0.4.22
    container_name: cv-assistant-chromadb
    restart: unless-stopped
    environment:
      CHROMA_SERVER_HOST: 0.0.0.0
      CHROMA_SERVER_HTTP_PORT: 8000
      ANONYMIZED_TELEMETRY: "false"
    ports:
      - "8000:8000"
    volumes:
      - chroma-data:/chroma/chroma
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/api/v1/heartbeat"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - cv-assistant-network

  # ===========================================
  # LLM SERVER
  # ===========================================

  ollama:
    image: ollama/ollama:latest
    container_name: cv-assistant-ollama
    restart: unless-stopped
    ports:
      - "11434:11434"
    volumes:
      - ollama-models:/root/.ollama
    environment:
      - OLLAMA_HOST=0.0.0.0
      - OLLAMA_NUM_PARALLEL=2
      - OLLAMA_MAX_LOADED_MODELS=1
    deploy:
      resources:
        limits:
          memory: 8G
        reservations:
          memory: 4G
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:11434/api/tags"]
      interval: 30s
      timeout: 10s
      retries: 3
    networks:
      - cv-assistant-network

  # ===========================================
  # PYTHON MICROSERVICES
  # ===========================================

  ner-service:
    build:
      context: ./services/ner-service
      dockerfile: Dockerfile
    container_name: cv-assistant-ner
    restart: unless-stopped
    ports:
      - "5001:5001"
    environment:
      - SERVICE_NAME=ner-service
      - SERVICE_PORT=5001
      - LOG_LEVEL=${LOG_LEVEL:-INFO}
      - MODEL_PATH=/app/models/ner_model
    volumes:
      - ./models/ner:/app/models/ner_model:ro
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:5001/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    depends_on:
      postgres:
        condition: service_healthy
    networks:
      - cv-assistant-network

  skill-service:
    build:
      context: ./services/skill-service
      dockerfile: Dockerfile
    container_name: cv-assistant-skill
    restart: unless-stopped
    ports:
      - "5002:5002"
    environment:
      - SERVICE_NAME=skill-service
      - SERVICE_PORT=5002
      - LOG_LEVEL=${LOG_LEVEL:-INFO}
      - CHROMADB_HOST=chromadb
      - CHROMADB_PORT=8000
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:5002/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    depends_on:
      chromadb:
        condition: service_healthy
    networks:
      - cv-assistant-network

  career-service:
    build:
      context: ./services/career-service
      dockerfile: Dockerfile
    container_name: cv-assistant-career
    restart: unless-stopped
    ports:
      - "5003:5003"
    environment:
      - SERVICE_NAME=career-service
      - SERVICE_PORT=5003
      - LOG_LEVEL=${LOG_LEVEL:-INFO}
      - ONET_DATA_PATH=/app/data/onet
    volumes:
      - ./data/onet:/app/data/onet:ro
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:5003/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    networks:
      - cv-assistant-network

  chatbot-service:
    build:
      context: ./services/chatbot-service
      dockerfile: Dockerfile
    container_name: cv-assistant-chatbot
    restart: unless-stopped
    ports:
      - "5004:5004"
    environment:
      - SERVICE_NAME=chatbot-service
      - SERVICE_PORT=5004
      - LOG_LEVEL=${LOG_LEVEL:-INFO}
      - OLLAMA_HOST=ollama
      - OLLAMA_PORT=11434
      - OLLAMA_MODEL=${OLLAMA_MODEL:-llama3.2:3b}
      - CHROMADB_HOST=chromadb
      - CHROMADB_PORT=8000
      - NER_SERVICE_URL=http://ner-service:5001
      - SKILL_SERVICE_URL=http://skill-service:5002
      - CAREER_SERVICE_URL=http://career-service:5003
    deploy:
      resources:
        limits:
          memory: 4G
        reservations:
          memory: 2G
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:5004/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    depends_on:
      ollama:
        condition: service_healthy
      chromadb:
        condition: service_healthy
      ner-service:
        condition: service_healthy
      skill-service:
        condition: service_healthy
      career-service:
        condition: service_healthy
    networks:
      - cv-assistant-network

  # ===========================================
  # API GATEWAY (Java Spring Boot)
  # ===========================================

  api-gateway:
    build:
      context: ./api-gateway
      dockerfile: Dockerfile
    container_name: cv-assistant-gateway
    restart: unless-stopped
    ports:
      - "8080:8080"
    environment:
      - SPRING_PROFILES_ACTIVE=${SPRING_PROFILE:-prod}
      - SERVER_PORT=8080
      - DB_HOST=postgres
      - DB_PORT=5432
      - DB_NAME=${DB_NAME:-cv_assistant}
      - DB_USER=${DB_USER:-cvassistant}
      - DB_PASSWORD=${DB_PASSWORD:-cvassistant123}
      - JWT_SECRET=${JWT_SECRET:-your-super-secret-jwt-key-min-256-bits}
      - JWT_EXPIRATION=${JWT_EXPIRATION:-86400000}
      - NER_SERVICE_URL=http://ner-service:5001
      - SKILL_SERVICE_URL=http://skill-service:5002
      - CAREER_SERVICE_URL=http://career-service:5003
      - CHATBOT_SERVICE_URL=http://chatbot-service:5004
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/actuator/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    depends_on:
      postgres:
        condition: service_healthy
      ner-service:
        condition: service_healthy
      skill-service:
        condition: service_healthy
      career-service:
        condition: service_healthy
      chatbot-service:
        condition: service_healthy
    networks:
      - cv-assistant-network

  # ===========================================
  # FRONTEND (React)
  # ===========================================

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
      args:
        - REACT_APP_API_URL=${API_URL:-http://localhost:8080}
    container_name: cv-assistant-frontend
    restart: unless-stopped
    ports:
      - "3000:80"
    depends_on:
      api-gateway:
        condition: service_healthy
    networks:
      - cv-assistant-network

# ===========================================
# NETWORKS
# ===========================================

networks:
  cv-assistant-network:
    driver: bridge
    name: cv-assistant-network

# ===========================================
# VOLUMES
# ===========================================

volumes:
  postgres-data:
    name: cv-assistant-postgres-data
  chroma-data:
    name: cv-assistant-chroma-data
  ollama-models:
    name: cv-assistant-ollama-models
```

---

## 4. Individual Dockerfiles

### 4.1 NER Service Dockerfile

```dockerfile
# services/ner-service/Dockerfile
FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 5001

# Health check
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD curl -f http://localhost:5001/health || exit 1

# Run application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "5001"]
```

**requirements.txt**:
```
fastapi==0.109.0
uvicorn[standard]==0.27.0
transformers==4.37.0
torch==2.1.2
pydantic==2.5.3
python-multipart==0.0.6
PyPDF2==3.0.1
python-docx==1.1.0
httpx==0.26.0
```

### 4.2 Skill Service Dockerfile

```dockerfile
# services/skill-service/Dockerfile
FROM python:3.10-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 5002

HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD curl -f http://localhost:5002/health || exit 1

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "5002"]
```

**requirements.txt**:
```
fastapi==0.109.0
uvicorn[standard]==0.27.0
sentence-transformers==2.3.1
chromadb==0.4.22
pydantic==2.5.3
numpy==1.26.3
httpx==0.26.0
```

### 4.3 Career Service Dockerfile

```dockerfile
# services/career-service/Dockerfile
FROM python:3.10-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 5003

HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD curl -f http://localhost:5003/health || exit 1

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "5003"]
```

**requirements.txt**:
```
fastapi==0.109.0
uvicorn[standard]==0.27.0
pydantic==2.5.3
pandas==2.1.4
httpx==0.26.0
```

### 4.4 Chatbot Service Dockerfile

```dockerfile
# services/chatbot-service/Dockerfile
FROM python:3.10-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 5004

HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD curl -f http://localhost:5004/health || exit 1

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "5004"]
```

**requirements.txt**:
```
fastapi==0.109.0
uvicorn[standard]==0.27.0
llama-index==0.10.0
llama-index-llms-ollama==0.1.0
llama-index-embeddings-huggingface==0.1.0
chromadb==0.4.22
pydantic==2.5.3
httpx==0.26.0
python-multipart==0.0.6
```

### 4.5 API Gateway Dockerfile

```dockerfile
# api-gateway/Dockerfile
FROM eclipse-temurin:17-jdk-alpine AS builder

WORKDIR /app

# Copy gradle files
COPY gradle gradle
COPY gradlew .
COPY build.gradle.kts .
COPY settings.gradle.kts .

# Download dependencies
RUN ./gradlew dependencies --no-daemon

# Copy source code
COPY src src

# Build application
RUN ./gradlew bootJar --no-daemon

# Production stage
FROM eclipse-temurin:17-jre-alpine

WORKDIR /app

# Create non-root user
RUN addgroup -g 1000 appgroup && adduser -u 1000 -G appgroup -D appuser

# Copy jar from builder
COPY --from=builder /app/build/libs/*.jar app.jar

# Set ownership
RUN chown -R appuser:appgroup /app
USER appuser

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:8080/actuator/health || exit 1

ENTRYPOINT ["java", "-jar", "app.jar"]
```

### 4.6 Frontend Dockerfile

```dockerfile
# frontend/Dockerfile
# Build stage
FROM node:20-alpine AS builder

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci

# Copy source code
COPY . .

# Build arguments
ARG REACT_APP_API_URL
ENV REACT_APP_API_URL=$REACT_APP_API_URL

# Build application
RUN npm run build

# Production stage
FROM nginx:alpine

# Copy nginx config
COPY nginx.conf /etc/nginx/nginx.conf

# Copy built files
COPY --from=builder /app/build /usr/share/nginx/html

# Create non-root user
RUN chown -R nginx:nginx /usr/share/nginx/html

EXPOSE 80

HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:80/health || exit 1

CMD ["nginx", "-g", "daemon off;"]
```

**nginx.conf**:
```nginx
# frontend/nginx.conf
user nginx;
worker_processes auto;
error_log /var/log/nginx/error.log warn;
pid /var/run/nginx.pid;

events {
    worker_connections 1024;
}

http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;

    log_format main '$remote_addr - $remote_user [$time_local] "$request" '
                    '$status $body_bytes_sent "$http_referer" '
                    '"$http_user_agent" "$http_x_forwarded_for"';

    access_log /var/log/nginx/access.log main;

    sendfile on;
    keepalive_timeout 65;
    gzip on;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml;

    server {
        listen 80;
        server_name localhost;
        root /usr/share/nginx/html;
        index index.html;

        # Health check endpoint
        location /health {
            return 200 'OK';
            add_header Content-Type text/plain;
        }

        # React Router support
        location / {
            try_files $uri $uri/ /index.html;
        }

        # Cache static assets
        location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2)$ {
            expires 1y;
            add_header Cache-Control "public, immutable";
        }

        # API proxy (optional, if not using separate gateway)
        location /api/ {
            proxy_pass http://api-gateway:8080/api/;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection 'upgrade';
            proxy_set_header Host $host;
            proxy_cache_bypass $http_upgrade;
        }
    }
}
```

---

## 5. Environment Configuration

### 5.1 .env.example

```bash
# Database Configuration
DB_USER=cvassistant
DB_PASSWORD=cvassistant123
DB_NAME=cv_assistant

# JWT Configuration
JWT_SECRET=your-super-secret-jwt-key-must-be-at-least-256-bits-long
JWT_EXPIRATION=86400000

# Ollama Configuration
OLLAMA_MODEL=llama3.2:3b

# API Configuration
API_URL=http://localhost:8080

# Spring Profile
SPRING_PROFILE=prod

# Logging
LOG_LEVEL=INFO
```

### 5.2 Development Environment (.env.dev)

```bash
# Development overrides
DB_USER=cvassistant_dev
DB_PASSWORD=dev_password
DB_NAME=cv_assistant_dev
JWT_SECRET=dev-jwt-secret-key-for-development-only-not-for-production
SPRING_PROFILE=dev
LOG_LEVEL=DEBUG
```

---

## 6. Database Initialization

### 6.1 init-db.sql

```sql
-- scripts/init-db.sql

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Users table
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    name VARCHAR(255) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_login_at TIMESTAMP WITH TIME ZONE,
    is_active BOOLEAN DEFAULT TRUE
);

CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);

-- CVs table
CREATE TABLE IF NOT EXISTS cvs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    filename VARCHAR(255) NOT NULL,
    raw_text TEXT,
    extraction_result JSONB,
    status VARCHAR(50) DEFAULT 'pending',
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_cvs_user_id ON cvs(user_id);
CREATE INDEX IF NOT EXISTS idx_cvs_status ON cvs(status);

-- Threads table (conversation threads)
CREATE TABLE IF NOT EXISTS threads (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(500),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_threads_user_id ON threads(user_id);
CREATE INDEX IF NOT EXISTS idx_threads_updated_at ON threads(updated_at DESC);

-- Messages table
CREATE TABLE IF NOT EXISTS messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    thread_id UUID NOT NULL REFERENCES threads(id) ON DELETE CASCADE,
    role VARCHAR(20) NOT NULL,
    content TEXT NOT NULL,
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_messages_thread_id ON messages(thread_id);
CREATE INDEX IF NOT EXISTS idx_messages_created_at ON messages(created_at);

-- Refresh tokens table
CREATE TABLE IF NOT EXISTS refresh_tokens (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token_hash VARCHAR(255) NOT NULL,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    revoked_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX IF NOT EXISTS idx_refresh_tokens_user_id ON refresh_tokens(user_id);
CREATE INDEX IF NOT EXISTS idx_refresh_tokens_expires ON refresh_tokens(expires_at);

-- Update timestamp trigger
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply trigger to tables
CREATE TRIGGER update_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_cvs_updated_at
    BEFORE UPDATE ON cvs
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_threads_updated_at
    BEFORE UPDATE ON threads
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Grant permissions
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO cvassistant;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO cvassistant;
```

---

## 7. Scripts

### 7.1 Pull Models Script

```bash
#!/bin/bash
# scripts/pull-models.sh

echo "=== Pulling Ollama Models ==="

# Wait for Ollama to be ready
until curl -s http://localhost:11434/api/tags > /dev/null 2>&1; do
    echo "Waiting for Ollama to start..."
    sleep 5
done

echo "Ollama is ready. Pulling models..."

# Pull Llama 3.2 (3B parameter model)
echo "Pulling llama3.2:3b..."
docker exec cv-assistant-ollama ollama pull llama3.2:3b

# Verify model is available
echo "Verifying model..."
docker exec cv-assistant-ollama ollama list

echo "=== Model pull complete ==="
```

### 7.2 Seed Data Script

```bash
#!/bin/bash
# scripts/seed-data.sh

echo "=== Seeding Database ==="

# Create test user
docker exec cv-assistant-postgres psql -U cvassistant -d cv_assistant -c "
INSERT INTO users (email, password_hash, name)
VALUES ('test@example.com', '\$2a\$10\$dummyhash', 'Test User')
ON CONFLICT (email) DO NOTHING;
"

echo "=== Seed complete ==="
```

### 7.3 Startup Script

```bash
#!/bin/bash
# scripts/start.sh

set -e

echo "=== Starting CV Assistant ==="

# Check if .env exists
if [ ! -f .env ]; then
    echo "Creating .env from .env.example..."
    cp .env.example .env
fi

# Start infrastructure first
echo "Starting databases..."
docker compose up -d postgres chromadb

# Wait for databases
echo "Waiting for databases to be healthy..."
sleep 10

# Start Ollama
echo "Starting Ollama..."
docker compose up -d ollama

# Wait for Ollama and pull model
echo "Waiting for Ollama to be ready..."
sleep 30
./scripts/pull-models.sh

# Start all services
echo "Starting all services..."
docker compose up -d

# Show status
echo "=== Services Status ==="
docker compose ps

echo "=== CV Assistant is starting ==="
echo "Frontend: http://localhost:3000"
echo "API Gateway: http://localhost:8080"
echo "API Docs: http://localhost:8080/swagger-ui.html"
```

### 7.4 Stop Script

```bash
#!/bin/bash
# scripts/stop.sh

echo "=== Stopping CV Assistant ==="

docker compose down

echo "=== All services stopped ==="
```

### 7.5 Cleanup Script

```bash
#!/bin/bash
# scripts/cleanup.sh

echo "=== Cleaning up CV Assistant ==="

# Stop all containers
docker compose down -v

# Remove volumes (WARNING: This deletes all data!)
read -p "Delete all data volumes? (y/N): " confirm
if [ "$confirm" = "y" ]; then
    docker volume rm cv-assistant-postgres-data cv-assistant-chroma-data cv-assistant-ollama-models 2>/dev/null || true
    echo "Volumes removed."
fi

# Remove images
read -p "Remove Docker images? (y/N): " confirm
if [ "$confirm" = "y" ]; then
    docker compose down --rmi all
    echo "Images removed."
fi

echo "=== Cleanup complete ==="
```

---

## 8. Development Configuration

### 8.1 docker-compose.dev.yml

```yaml
version: '3.8'

# Development overrides
# Usage: docker compose -f docker-compose.yml -f docker-compose.dev.yml up

services:
  postgres:
    ports:
      - "5432:5432"
    environment:
      POSTGRES_USER: cvassistant_dev
      POSTGRES_PASSWORD: dev_password

  ner-service:
    build:
      context: ./services/ner-service
      dockerfile: Dockerfile.dev
    volumes:
      - ./services/ner-service:/app
    environment:
      - LOG_LEVEL=DEBUG

  skill-service:
    build:
      context: ./services/skill-service
      dockerfile: Dockerfile.dev
    volumes:
      - ./services/skill-service:/app
    environment:
      - LOG_LEVEL=DEBUG

  career-service:
    build:
      context: ./services/career-service
      dockerfile: Dockerfile.dev
    volumes:
      - ./services/career-service:/app
    environment:
      - LOG_LEVEL=DEBUG

  chatbot-service:
    build:
      context: ./services/chatbot-service
      dockerfile: Dockerfile.dev
    volumes:
      - ./services/chatbot-service:/app
    environment:
      - LOG_LEVEL=DEBUG

  api-gateway:
    environment:
      - SPRING_PROFILES_ACTIVE=dev

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile.dev
    volumes:
      - ./frontend/src:/app/src
    ports:
      - "3000:3000"
    environment:
      - REACT_APP_API_URL=http://localhost:8080
```

### 8.2 Development Dockerfile (Python)

```dockerfile
# Dockerfile.dev (for Python services)
FROM python:3.10-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
COPY requirements-dev.txt .
RUN pip install --no-cache-dir -r requirements.txt -r requirements-dev.txt

# Run with reload for development
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "5001", "--reload"]
```

---

## 9. Resource Optimization

### 9.1 Memory Allocation (16GB Total)

| Service | Memory Limit | Memory Reservation |
|---------|--------------|-------------------|
| Ollama | 8 GB | 4 GB |
| Chatbot Service | 4 GB | 2 GB |
| NER Service | 2 GB | 1 GB |
| Other Services | 512 MB each | 256 MB each |
| PostgreSQL | 1 GB | 512 MB |
| ChromaDB | 1 GB | 512 MB |

### 9.2 CPU-Only Optimizations

```yaml
# Additional settings for CPU-only systems
ollama:
  environment:
    - OLLAMA_NUM_PARALLEL=1        # Reduce parallel requests
    - OLLAMA_MAX_LOADED_MODELS=1   # Only load one model
    - OLLAMA_KEEP_ALIVE=5m         # Unload model after 5 minutes idle
```

---

## 10. Health Monitoring

### 10.1 Health Check Endpoints

| Service | Endpoint | Expected Response |
|---------|----------|-------------------|
| NER | `GET /health` | `{"status": "healthy"}` |
| Skill | `GET /health` | `{"status": "healthy"}` |
| Career | `GET /health` | `{"status": "healthy"}` |
| Chatbot | `GET /health` | `{"status": "healthy"}` |
| API Gateway | `GET /actuator/health` | `{"status": "UP"}` |
| PostgreSQL | `pg_isready` | Exit code 0 |
| ChromaDB | `GET /api/v1/heartbeat` | `{"nanosecond heartbeat": ...}` |
| Ollama | `GET /api/tags` | `{"models": [...]}` |

### 10.2 Monitoring Commands

```bash
# Check all services status
docker compose ps

# View logs
docker compose logs -f [service_name]

# Check resource usage
docker stats

# Check network
docker network inspect cv-assistant-network
```

---

## 11. Troubleshooting

### 11.1 Common Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| Ollama OOM | Model too large | Use smaller model or increase memory |
| Slow responses | CPU bottleneck | Reduce parallel requests |
| DB connection failed | Service started before DB | Use healthcheck dependencies |
| ChromaDB errors | Persistence issues | Check volume permissions |

### 11.2 Debug Commands

```bash
# Check service logs
docker logs cv-assistant-chatbot --tail 100

# Enter container shell
docker exec -it cv-assistant-chatbot /bin/bash

# Check Ollama models
docker exec cv-assistant-ollama ollama list

# Test database connection
docker exec cv-assistant-postgres psql -U cvassistant -d cv_assistant -c "\dt"

# Check ChromaDB
curl http://localhost:8000/api/v1/heartbeat
```

---

## 12. Production Checklist

- [ ] Update all default passwords in `.env`
- [ ] Set proper JWT_SECRET (256+ bits)
- [ ] Configure HTTPS/SSL certificates
- [ ] Set up monitoring (Prometheus/Grafana)
- [ ] Configure log aggregation
- [ ] Set up automated backups for PostgreSQL
- [ ] Configure rate limiting
- [ ] Set resource limits for all services
- [ ] Test disaster recovery procedures

---

*Document created as part of CV Assistant Research Project documentation.*
