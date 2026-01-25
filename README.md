# CV Assistant

CV Assistant is an AI-powered tool designed to help users optimize their Curriculum Vitae (CV) based on job descriptions and industry standards using O*NET data.

## Project Structure

```
cv-assistant/
├── data/
│   ├── raw/                    # Raw CVs (not in git)
│   ├── processed/              # Processed text
│   ├── annotated/              # Annotated data
│   └── splits/                 # train/val/test
├── models/
│   ├── ner/                    # NER model checkpoints
│   └── embeddings/             # Embedding cache
├── knowledge_base/
│   ├── onet/                   # O*NET data
│   ├── cv_guides/              # CV writing guides
│   └── chroma_db/              # ChromaDB storage
├── services/
│   ├── ner_service/            # FastAPI NER
│   ├── skill_service/          # FastAPI Skill
│   ├── career_service/         # FastAPI Career
│   ├── chatbot_service/        # FastAPI Chatbot
│   └── api_gateway/            # API Gateway
├── frontend/                   # React application
├── notebooks/                  # Jupyter notebooks
├── scripts/                    # Utility scripts
└── docs/                       # Project documentation
```

## Setup Instructions

### Prerequisites
- Python 3.10
- Docker (optional, for Label Studio)

### Installation

1. Clone the repository:
   ```bash
   git clone <repository_url>
   cd cv-assistant
   ```

2. Create and activate virtual environment:
   ```bash
   python3.10 -m venv cv_assistant_env
   source cv_assistant_env/bin/activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Development

- **Label Studio**: Run `label-studio start` to access the annotation interface at http://localhost:8080.
- **Notebooks**: Launch `jupyter notebook` to explore data processing and training steps.
