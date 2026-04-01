import sys
from pathlib import Path

# Add core to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from fastapi import FastAPI, Depends, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import io
import tempfile
import os

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

@app.post("/parse-cv")
async def parse_and_extract_cv(file: UploadFile = File(...), extractor: NERExtractor = Depends(get_extractor)):
    """Accept a PDF/TXT/DOCX file, extract text, run NER, and return structured entities."""
    content = await file.read()
    filename = file.filename or "uploaded_cv.pdf"
    
    # Save to temp file for coordinate-aware parsing
    with tempfile.NamedTemporaryFile(suffix=Path(filename).suffix, delete=False) as tmp:
        tmp.write(content)
        tmp_path = tmp.name

    try:
        logger.info(f"Structural parsing request for: {filename}")
        
        # New Structured Logic
        if filename.lower().endswith(".pdf"):
            structured_data = extractor.extract_structured(tmp_path)
            
            # Add backward compatibility fields
            all_text = " ".join([l["text"] for l in extractor.parser.get_visual_lines(tmp_path)])
            structured_data["char_count"] = len(all_text)
            
            # Simple grouped entities for old frontends
            legacy_groups = {}
            for item in structured_data.get("experience", []) + structured_data.get("projects", []):
                for ent in item.get("entities", []):
                    etype = ent.get("type", "UNKNOWN")
                    if etype not in legacy_groups: legacy_groups[etype] = []
                    legacy_groups[etype].append(ent.get("text", ""))
            
            structured_data["grouped_entities"] = legacy_groups
            structured_data["entity_count"] = sum(len(v) for v in legacy_groups.values())
            structured_data["raw_text_preview"] = all_text[:500]
            
            structured_data["filename"] = filename
            structured_data["status"] = "success"
            return structured_data
        else:
            # Fallback for non-PDFs (simplified)
            text = content.decode("utf-8", errors="ignore")
            entities = extractor.extract(text)
            return {
                "filename": filename,
                "summary": text[:500],
                "experience": [{"title": "Raw Extraction", "entities": [e.dict() for e in entities]}],
                "status": "success (fallback)"
            }
    except Exception as e:
        logger.error(f"Parsing failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        os.unlink(tmp_path)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=settings.service_port)
