# NER Service

## Overview
Named Entity Recognition service for CV information extraction.

## Quick Start
```bash
pip install -r requirements.txt
python main.py
```

## API Endpoints
| Method | Path | Description |
|--------|------|-------------|
| GET | /health | Health check |
| POST | /extract | Extract entities from text |

## Environment Variables
| Variable | Default | Description |
|----------|---------|-------------|
| SERVICE_PORT | 5001 | Server port |
| MODEL_PATH | ./models/ner | Model directory |

## Testing
```bash
pytest tests/
```
