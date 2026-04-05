import warnings
warnings.filterwarnings("ignore", category=UserWarning, module="pydantic")
import sys
import os
from pathlib import Path
import requests
import uuid

# Add project root to path for shared imports
sys.path.append(str(Path(__file__).parent.parent.parent))

from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import List
import uvicorn
from sentence_transformers import SentenceTransformer

from services.skill_service.config import settings
from services.skill_service.models.schemas import (
    SkillMatchRequest, SkillMatchResponse, SkillGapExplanation,
    SkillNodeResponse, GraphDataResponse, SkillSearchResponse,
    OntologyStatsResponse, CategoriesResponse, MultiSkillMatchRequest,
    MultiSkillMatchResponse, CVDetails,
    BookmarkRequest, ProgressUpdateRequest, Course, LearningRoadmap,
    ATSScoreRequest, ATSScoreResponse, MarketOverviewResponse
)
from services.skill_service.services.matcher import SkillMatcher
from services.skill_service.services.explainer import SkillGapExplainer
from services.skill_service.services.ontology import SkillOntology
from services.skill_service.services.course_service import CourseService
from services.skill_service.services.ats_engine import ATSScoringEngine
from services.skill_service.services.market_analyzer import MarketAnalyzer
from services.skill_service.services.db_session import init_db, get_db
from shared.db.chroma_client import get_collection
from shared.utils.logging_config import setup_logging
from shared.constants import COLLECTION_JOBS

# Setup logger
logger = setup_logging(settings.service_name)

app = FastAPI(title="Skill Service", version="1.0.0")

# Initialize isolated PostgreSQL tables for skill_service
init_db()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global variables for caching (Intelligence models/Ontology)
_model = None
_matcher = None
_ontology = None
_ats_engine = None
_market_analyzer = None

def get_ontology() -> SkillOntology:
    """Singleton ontology instance."""
    global _ontology
    if _ontology is None:
        _ontology = SkillOntology()
    return _ontology

def get_matcher() -> SkillMatcher:
    """Dependency injection for SkillMatcher."""
    global _model, _matcher
    if _model is None:
        logger.info(f"Loading embedding model: {settings.embedding_model}")
        _model = SentenceTransformer(settings.embedding_model)
    
    if _matcher is None:
        try:
            collection = get_collection(COLLECTION_JOBS)
            onet_collection = get_collection("onet_skills")
            _matcher = SkillMatcher(_model, collection, onet_collection, settings.ner_service_url)
        except Exception as e:
            logger.error(f"Failed to initialize matcher: {e}")
            raise HTTPException(status_code=503, detail="Search service unavailable")
            
    return _matcher

def get_ats_engine(matcher: SkillMatcher = Depends(get_matcher)) -> ATSScoringEngine:
    """Dependency injection for ATSScoringEngine."""
    global _ats_engine
    if _ats_engine is None:
        _ats_engine = ATSScoringEngine(matcher)
    return _ats_engine

def get_market_analyzer() -> MarketAnalyzer:
    """Dependency injection for MarketAnalyzer."""
    global _market_analyzer
    if _market_analyzer is None:
        collection = get_collection("market_jds")
        _market_analyzer = MarketAnalyzer(collection)
    return _market_analyzer

def get_course_service() -> CourseService:
    """Dependency injection for CourseService."""
    return CourseService()

def get_structured_jd(jd_text: str):
    """Deep JD parsing."""
    try:
        url = settings.ner_service_url.replace("/extract", "/parse-jd-text")
        resp = requests.post(url, json={"text": jd_text}, timeout=10)
        if resp.status_code == 200:
            return resp.json()
    except Exception as e:
        logger.error(f"Failed to parse via NER: {e}")
    return None

@app.get("/health")
def health_check():
    return {"status": "ok", "service": settings.service_name}

@app.post("/match", response_model=SkillMatchResponse)
def match_skills(
    request: SkillMatchRequest, 
    matcher: SkillMatcher = Depends(get_matcher),
    course_service: CourseService = Depends(get_course_service)
):
    """Skill Gap & Roadmap."""
    cv_details = request.cv_details or CVDetails(skills=request.cv_skills)
    jd_info = get_structured_jd(request.jd_text)
    
    if not jd_info:
        jd_skills = matcher.extract_skills_from_jd(request.jd_text)
        jd_req = jd_skills
        jd_pref = []
        jd_title, jd_company = "Unknown Position", "Unknown Company"
        jd_min_exp, jd_max_exp = 0, None
        jd_edu = None
    else:
        jd_skills_data = jd_info.get("extracted_skills", {})
        jd_req = jd_skills_data.get("required", [])
        jd_pref = jd_skills_data.get("preferred", [])
        jd_title = jd_info.get("title", "Unknown Position")
        jd_company = jd_info.get("company", "Unknown Company")
        jd_min_exp = jd_info.get("min_exp", 0)
        jd_max_exp = jd_info.get("max_exp")
        jd_edu = jd_info.get("degree_required")

    results = matcher.match_comprehensive(
        cv_skills=cv_details.skills,
        jd_required=jd_req,
        jd_preferred=jd_pref,
        cv_exp=cv_details.experience_years,
        jd_min_exp=jd_min_exp,
        jd_max_exp=jd_max_exp,
        cv_edu=cv_details.education_level,
        jd_edu=jd_edu
    )

    all_jd_skills = jd_req + jd_pref
    missing_skills_simple = [s.skill for s in results["skills"]["missing"]]
    explainer = SkillGapExplainer(matcher.ontology)
    gap_explanation = explainer.analyze_gap(cv_details.skills, all_jd_skills, missing_skills_simple, results["overall_score"])

    missing_skills_data = [{"skill": s.skill, "priority": s.priority} for s in results["skills"]["missing"]]
    course_recs = course_service.get_recommendations(missing_skills_simple)
    roadmap = course_service.generate_roadmap(missing_skills_data)
    recs = matcher.get_recommendations(cv_details.skills)

    return SkillMatchResponse(
        analysis_id=f"ana-{uuid.uuid4().hex[:8]}",
        jd_title=jd_title, jd_company=jd_company,
        overall_score=results["overall_score"], breakdown=results["breakdown"],
        skills=results["skills"], experience=results["experience"], education=results["education"],
        recommendations=recs, course_recommendations=course_recs, learning_roadmap=roadmap,
        skill_gap_explanation=SkillGapExplanation(**gap_explanation),
        jd_skills_extracted=all_jd_skills, missing_skills=missing_skills_simple,
    )

@app.post("/match/multi", response_model=MultiSkillMatchResponse)
def match_multi(request: MultiSkillMatchRequest, matcher: SkillMatcher = Depends(get_matcher)):
    results = []
    for jd_text in request.jd_texts[:5]:
        sub_req = SkillMatchRequest(cv_details=request.cv_details, jd_text=jd_text)
        results.append(match_skills(sub_req, matcher))
    results.sort(key=lambda x: -x.overall_score)
    return MultiSkillMatchResponse(results=results)


@app.post("/cv/ats-score", response_model=ATSScoreResponse)
def get_ats_score(
    request: ATSScoreRequest,
    engine: ATSScoringEngine = Depends(get_ats_engine)
):
    """US-18: ATS Scoring."""
    try:
        logger.info("Calculating ATS score...")
        result = engine.calculate_score(request.cv_data, request.jd_text)
        logger.info(f"ATS score calculated: {result.total_score}")
        return result
    except Exception as e:
        logger.error(f"Error calculating ATS score: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))



@app.get("/market/overview", response_model=MarketOverviewResponse)
def get_market_overview(
    industry: str = Query(None),
    analyzer: MarketAnalyzer = Depends(get_market_analyzer)
):
    """US-19: Market analysis dashboard data."""
    return analyzer.get_overview(industry=industry)


@app.get("/ontology/skill/{name}", response_model=SkillNodeResponse)
def get_skill_node(name: str, ontology: SkillOntology = Depends(get_ontology)):
    node = ontology.get_skill_node(name)
    if not node: raise HTTPException(status_code=404)
    return SkillNodeResponse(**node)

@app.get("/ontology/graph", response_model=GraphDataResponse)
def get_graph_data(center: str = None, depth: int = 1, max_nodes: int = 80, ontology: SkillOntology = Depends(get_ontology)):
    return GraphDataResponse(**ontology.get_graph_data(center, depth, max_nodes))

@app.get("/ontology/search", response_model=SkillSearchResponse)
def search_skills(q: str = Query(..., min_length=1), limit: int = 20, ontology: SkillOntology = Depends(get_ontology)):
    results = ontology.search_skills(q, limit)
    return SkillSearchResponse(results=results, total=len(results))

@app.get("/ontology/categories", response_model=CategoriesResponse)
def get_categories(ontology: SkillOntology = Depends(get_ontology)):
    return CategoriesResponse(categories=ontology.get_all_categories())

@app.post("/courses/bookmark")
def toggle_bookmark(request: BookmarkRequest, course_service: CourseService = Depends(get_course_service)):
    return {"is_bookmarked": course_service.toggle_bookmark(request.course_id, request.user_id)}

@app.patch("/courses/progress")
def update_progress(request: ProgressUpdateRequest, course_service: CourseService = Depends(get_course_service)):
    course_service.update_progress(request.course_id, request.progress, request.user_id)
    return {"status": "success"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=settings.service_port)
