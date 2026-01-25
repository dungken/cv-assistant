# Chatbot Service

## Overview
Conversational AI service with RAG using Ollama (Llama 3.2) and ChromaDB.

## Quick Start
```bash
pip install -r requirements.txt
python main.py
```

## API Endpoints
| Method | Path | Description |
|--------|------|-------------|
| GET | /health | Health check |
| POST | /chat | Send message to chatbot |

## Environment Variables
| Variable | Default | Description |
|----------|---------|-------------|
| OLLAMA_URL | http://localhost:11434 | Ollama server URL |
| MODEL_NAME | llama3.2:3b | LLM model |
| CHROMA_PATH | ./knowledge_base/chroma_db | ChromaDB path |
| SERVICE_PORT | 5004 | Server port |

## Testing
```bash
pytest tests/
```
