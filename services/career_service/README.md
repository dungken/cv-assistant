# Career Service

## Overview
Career path recommendation service using O*NET occupational data.

## Quick Start
```bash
pip install -r requirements.txt
python main.py
```

## API Endpoints
| Method | Path | Description |
|--------|------|-------------|
| GET | /health | Health check |
| POST | /recommend | Generate career paths |
| GET | /roles | List/search roles |
| GET | /roles/{code} | Get role details |

## Environment Variables
| Variable | Default | Description |
|----------|---------|-------------|
| CHROMA_PATH | ./knowledge_base/chroma_db | ChromaDB path |
| ONET_PATH | ./knowledge_base/onet/db_28_1_text | O*NET data path |
| SERVICE_PORT | 5003 | Server port |

## Example Request
```bash
curl -X POST http://localhost:5003/recommend \
  -H "Content-Type: application/json" \
  -d '{"current_role": "Software Developer", "target_role": "Data Scientist", "current_skills": ["Python", "SQL"]}'
```

## Testing
```bash
pytest tests/
```
