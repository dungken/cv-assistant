import sys
import os
from pathlib import Path

# Add project root to path for shared imports
sys.path.append(str(Path(__file__).parent.parent.parent))

from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from sentence_transformers import SentenceTransformer

from services.skill_service.config import settings
from services.skill_service.models.schemas import SkillMatchRequest, SkillMatchResponse
from services.skill_service.services.matcher import SkillMatcher
from shared.db.chroma_client import get_collection
from shared.utils.logging_config import setup_logging
from shared.constants import COLLECTION_JOBS

# Setup logger
logger = setup_logging(settings.service_name)

app = FastAPI(title="Skill Service", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global variables for caching
_model = None
_matcher = None

def get_matcher() -> SkillMatcher:
    """Dependency injection for SkillMatcher."""
    global _model, _matcher
    if _model is None:
        logger.info(f"Loading embedding model: {settings.embedding_model}")
        _model = SentenceTransformer(settings.embedding_model)
    
    if _matcher is None:
        try:
            collection = get_collection(COLLECTION_JOBS)
            # Load O*NET collection for intelligent extraction/matching
            onet_collection = get_collection("onet_skills")
            _matcher = SkillMatcher(_model, collection, onet_collection)
        except Exception as e:
            logger.error(f"Failed to initialize matcher: {e}")
            raise HTTPException(status_code=503, detail="Search service unavailable")
            
    return _matcher

@app.get("/health")
def health_check():
    return {"status": "ok", "service": settings.service_name}

@app.post("/match", response_model=SkillMatchResponse)
def match_skills(request: SkillMatchRequest, matcher: SkillMatcher = Depends(get_matcher)):
    """API endpoint to match skills."""
    logger.info(f"Processing match request for {len(request.cv_skills)} skills")
    
    # Extract jd skills
    jd_skills = matcher.extract_skills_from_jd(request.jd_text)
    
    # Match
    results = matcher.match(request.cv_skills, jd_skills)
    
    # Recommend
    recs = matcher.get_recommendations(request.cv_skills)
    
    return SkillMatchResponse(
        jd_skills_extracted=jd_skills,
        exact_matches=results["exact_matches"],
        semantic_matches=results["semantic_matches"],
        overall_score=results["overall_score"],
        recommendations=recs
    )

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=settings.service_port)
