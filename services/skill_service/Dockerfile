# Build stage
FROM python:3.10-slim AS builder

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY services/skill_service/requirements.txt .
RUN pip install --user --no-cache-dir --extra-index-url https://download.pytorch.org/whl/cpu -r requirements.txt

# Final stage
FROM python:3.10-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*

# Copy only installed packages
COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH

# Copy shared library and service code
COPY shared/ ./shared/
COPY services/skill_service/ ./services/skill_service/

RUN mkdir -p /app/knowledge_base

ENV PYTHONPATH=/app
ENV SERVICE_PORT=5002

EXPOSE 5002

CMD ["python", "services/skill_service/main.py"]
