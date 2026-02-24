# Skill Service

## Overview
Skill matching service using semantic search (Sentence-BERT + ChromaDB).

## Quick Start
```bash
pip install -r requirements.txt
python main.py
```

## API Endpoints
| Method | Path | Description |
|--------|------|-------------|
| GET | /health | Health check |
| POST | /match | Match CV skills with JD |
| GET | /search | Search jobs by keyword |

## Environment Variables
| Variable | Default | Description |
|----------|---------|-------------|
| CHROMA_PATH | ./knowledge_base/chroma_db | ChromaDB path |
| SERVICE_PORT | 5002 | Server port |

## Testing
```bash
pytest tests/
```
