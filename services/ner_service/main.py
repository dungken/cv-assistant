import warnings
warnings.filterwarnings("ignore", category=UserWarning, module="pydantic")
import sys
from pathlib import Path

# Add core to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from fastapi import FastAPI, Depends, HTTPException, UploadFile, File
from typing import List, Optional, Dict, Any
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
import uvicorn
import io
import tempfile
import os
from langdetect import detect, DetectorFactory
DetectorFactory.seed = 0 # For consistent results

from services.ner_service.config import settings
from services.ner_service.models.schemas import (
    ExtractionRequest, ExtractionResponse,
    BatchExtractionRequest, BatchExtractionResponse,
    NormalizationResponse, NormalizedEntity, NormalizationStats,
    Entity,
    JDTextRequest, JDUrlRequest, JDParseResponse
)
from services.ner_service.services.extractor import NERExtractor
from services.ner_service.services.pdf_generator import generate_cv_pdf
from services.ner_service.services.normalizer import DataNormalizer
from services.ner_service.services.jd_parser import JDParser
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

# Create a specialized JD extractor
_jd_extractor = None

def get_jd_extractor() -> NERExtractor:
    global _jd_extractor
    if _jd_extractor is None:
        _jd_extractor = NERExtractor(settings.jd_model_path)
    return _jd_extractor

# Cache normalizer
_normalizer = None

def get_normalizer() -> DataNormalizer:
    global _normalizer
    if _normalizer is None:
        _normalizer = DataNormalizer()
    return _normalizer

# Cache JD parser
_jd_parser = None

def get_jd_parser() -> JDParser:
    global _jd_parser
    if _jd_parser is None:
        _jd_parser = JDParser(extractor=get_jd_extractor())
    return _jd_parser

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/extract", response_model=ExtractionResponse)
def extract_entities(request: ExtractionRequest, extractor: NERExtractor = Depends(get_extractor)):
    logger.info(f"Extraction req for CV: {request.cv_id}")
    entities = extractor.extract(request.text)
    return ExtractionResponse(entities=entities, status="success")

@app.post("/batch-extract", response_model=BatchExtractionResponse)
def batch_extract_entities(request: BatchExtractionRequest, extractor: NERExtractor = Depends(get_extractor)):
    logger.info(f"Batch extraction req for {len(request.texts)} items")
    results = extractor.batch_extract(request.texts)
    return BatchExtractionResponse(results=results, status="success")

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
        # Validate file type (Strictly PDF for now)
        if not filename.lower().endswith(".pdf"):
             raise HTTPException(status_code=400, detail="Only PDF files are supported currently.")
        
        # Check size (Max 10MB)
        if len(content) > 10 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="File size exceeds 10MB limit.")

        logger.info(f"Parsing request for: {filename}")
        
        # Structural parsing
        structured_data = extractor.extract_structured(tmp_path)
        
        if "error" in structured_data:
            raise HTTPException(status_code=500, detail=structured_data["error"])

        # US-24: Language Detection
        raw_text = structured_data.get("raw_text", "")
        detected_lang = "en"
        confidence = 1.0
        if raw_text:
            try:
                detected_lang = detect(raw_text)
                logger.info(f"Detected language: {detected_lang}")
            except:
                logger.warning("Language detection failed, defaulting to 'en'")
        
        structured_data["detected_language"] = detected_lang

        # US-03: Multilingual Normalization
        # Collect all raw entities for bulk normalization
        all_raw_entities = []
        # Flatten entities from sections
        for sec in ["experience", "projects", "education", "certifications"]:
            for item in structured_data.get(sec, []):
                for ent_dict in item.get("entities", []):
                    # Convert dict to Entity model
                    all_raw_entities.append(Entity(**ent_dict))
        
        # Also skills from skills section
        for cat, skills in structured_data.get("skills", {}).items():
            for skill in skills:
                # Skill section doesn't have start/end, default to 0
                all_raw_entities.append(Entity(
                    text=skill, type="SKILL", start=0, end=0, confidence=0.9
                ))

        # Normalize
        normalizer = get_normalizer()
        norm_results = normalizer.normalize_entities(all_raw_entities, structured_data.get("raw_text", ""))
        
        # Add normalization results to response
        structured_data["normalized_entities"] = norm_results["normalized_entities"]
        structured_data["normalization_stats"] = norm_results["stats"]
        
        # Add essential metadata
        structured_data["filename"] = filename
        structured_data["status"] = "success"
        
        return structured_data

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Parsing failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)

@app.post("/generate-pdf")
async def generate_pdf(cv_data: dict):
    """Generate an ATS-compliant PDF from structured CV data."""
    logger.info("Generating ATS-compliant PDF CV")

    pdf_bytes = generate_cv_pdf(cv_data)
    if pdf_bytes is None:
        raise HTTPException(
            status_code=500,
            detail="PDF generation failed. Ensure fpdf2 is installed."
        )

    name = cv_data.get("name", "cv").replace(" ", "_").lower()
    filename = f"{name}_cv.pdf"

    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

@app.post("/normalize", response_model=NormalizationResponse)
def normalize_entities_endpoint(request: Dict[str, Any], normalizer: DataNormalizer = Depends(get_normalizer)):
    """Standalone normalization endpoint for external entities."""
    raw_entities = []
    for ent_data in request.get("entities", []):
        raw_entities.append(Entity(**ent_data))
    
    text_context = request.get("text", "")
    return normalizer.normalize_entities(raw_entities, text_context)


# ── JD (Job Description) Endpoints ──

@app.post("/parse-jd")
async def parse_jd_file(file: UploadFile = File(...), jd_parser: JDParser = Depends(get_jd_parser)):
    """Parse a JD file (PDF/DOCX/TXT) and extract structured information."""
    content = await file.read()
    filename = file.filename or "uploaded_jd.pdf"

    if len(content) > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File size exceeds 10MB limit.")

    allowed_ext = (".pdf", ".docx", ".doc", ".txt")
    if not any(filename.lower().endswith(ext) for ext in allowed_ext):
        raise HTTPException(status_code=400, detail=f"Unsupported file type. Allowed: {', '.join(allowed_ext)}")

    with tempfile.NamedTemporaryFile(suffix=Path(filename).suffix, delete=False) as tmp:
        tmp.write(content)
        tmp_path = tmp.name

    try:
        logger.info(f"Parsing JD file: {filename}")
        result = jd_parser.parse_file(tmp_path)

        if result.get("status") == "error":
            raise HTTPException(status_code=500, detail=result.get("error", "Parsing failed"))

        result["filename"] = filename
        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"JD file parsing failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)


@app.post("/parse-jd-text")
def parse_jd_text(request: JDTextRequest, jd_parser: JDParser = Depends(get_jd_parser)):
    """Parse JD from pasted text."""
    if not request.text.strip():
        raise HTTPException(status_code=400, detail="Text cannot be empty")

    logger.info("Parsing JD from text input")
    result = jd_parser.parse_text(request.text, title=request.title or "", company=request.company or "")
    return result


@app.post("/parse-jd-url")
def parse_jd_url(request: JDUrlRequest, jd_parser: JDParser = Depends(get_jd_parser)):
    """Scrape and parse JD from a URL."""
    if not request.url.strip():
        raise HTTPException(status_code=400, detail="URL cannot be empty")

    logger.info(f"Parsing JD from URL: {request.url}")
    result = jd_parser.parse_url(request.url)

    if result.get("status") == "error":
        raise HTTPException(status_code=422, detail=result.get("error", "URL parsing failed"))

    return result


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=settings.service_port)
