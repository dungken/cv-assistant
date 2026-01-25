import sys
from pathlib import Path

# Add core to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from services.ner_service.config import settings
from services.ner_service.models.schemas import ExtractionRequest, ExtractionResponse
from services.ner_service.services.extractor import NERExtractor
from shared.utils.logging_config import setup_logging

# Logger
logger = setup_logging(settings.service_name)

app = FastAPI(title="NER Service", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Cache extractor
_extractor = None

def get_extractor() -> NERExtractor:
    global _extractor
    if _extractor is None:
        _extractor = NERExtractor(settings.model_path)
    return _extractor

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/extract", response_model=ExtractionResponse)
def extract_entities(request: ExtractionRequest, extractor: NERExtractor = Depends(get_extractor)):
    logger.info(f"Extraction req for CV: {request.cv_id}")
    entities = extractor.extract(request.text)
    return ExtractionResponse(entities=entities, status="success")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=settings.service_port)
