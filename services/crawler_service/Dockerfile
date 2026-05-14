# Build stage
FROM python:3.10-slim AS builder

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY services/crawler_service/requirements.txt .
RUN pip install --user --no-cache-dir --extra-index-url https://download.pytorch.org/whl/cpu -r requirements.txt

# Final stage
FROM python:3.10-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*

COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH

COPY shared/ ./shared/
COPY services/crawler_service/ ./services/crawler_service/

ENV PYTHONPATH=/app
ENV SERVICE_PORT=5006

EXPOSE 5006

CMD ["python", "services/crawler_service/main.py"]
