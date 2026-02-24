# Build stage
FROM python:3.10-slim AS builder

WORKDIR /app

# ner-service might not need build-essential, but for consistency and future-proofing:
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY services/ner_service/requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# Final stage
FROM python:3.10-slim

WORKDIR /app

COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH

COPY shared/ ./shared/
COPY services/ner_service/ ./services/ner_service/

ENV PYTHONPATH=/app
ENV SERVICE_PORT=5001

EXPOSE 5001

CMD ["python", "services/ner_service/main.py"]
