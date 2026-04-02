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
from services.skill_service.models.schemas import SkillMatchRequest, SkillMatchResponse, SkillGapExplanation
from services.skill_service.services.matcher import SkillMatcher
from services.skill_service.services.explainer import SkillGapExplainer
from services.skill_service.services.ontology import SkillOntology
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
            _matcher = SkillMatcher(_model, collection, onet_collection, settings.ner_service_url)
        except Exception as e:
            logger.error(f"Failed to initialize matcher: {e}")
            raise HTTPException(status_code=503, detail="Search service unavailable")
            
    return _matcher

@app.get("/health")
def health_check():
    return {"status": "ok", "service": settings.service_name}

@app.post("/match", response_model=SkillMatchResponse)
def match_skills(request: SkillMatchRequest, matcher: SkillMatcher = Depends(get_matcher)):
    """API endpoint to match skills with ontology-enhanced matching and explainable gap analysis."""
    logger.info(f"Processing match request for {len(request.cv_skills)} skills")

    # Extract jd skills
    jd_skills = matcher.extract_skills_from_jd(request.jd_text)

    # Match (3-tier: exact + ontology + semantic)
    results = matcher.match(request.cv_skills, jd_skills)

    # Explainable skill gap analysis
    explainer = SkillGapExplainer(matcher.ontology)
    gap_explanation = explainer.analyze_gap(
        cv_skills=request.cv_skills,
        jd_skills=jd_skills,
        missing_skills=results.get("missing_skills", []),
        match_score=results["overall_score"],
    )

    # Recommend
    recs = matcher.get_recommendations(request.cv_skills)

    return SkillMatchResponse(
        jd_skills_extracted=jd_skills,
        exact_matches=results["exact_matches"],
        ontology_matches=results.get("ontology_matches", []),
        semantic_matches=results["semantic_matches"],
        missing_skills=results.get("missing_skills", []),
        overall_score=results["overall_score"],
        cv_profile=results.get("cv_profile", {}),
        recommendations=recs,
        skill_gap_explanation=SkillGapExplanation(**gap_explanation),
    )

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=settings.service_port)
