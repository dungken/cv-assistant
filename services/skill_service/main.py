import warnings
warnings.filterwarnings("ignore", category=UserWarning, module="pydantic")
import sys
import os
from pathlib import Path
import requests
import uuid

# Add project root to path for shared imports
sys.path.append(str(Path(__file__).parent.parent.parent))

from fastapi import FastAPI, Depends, HTTPException, Query, BackgroundTasks
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
    ATSScoreRequest, ATSScoreResponse, MarketOverviewResponse,
    FreshnessRequest, FreshnessResponse, SkillContributionItem,
    CVUpsertRequest, CVUpsertResponse,
    HealthScoreResponse, SkillAlertsResponse, AlertItem,
    OpportunityWindowResponse, OpportunityJDItem,
    FreshnessHistoryResponse, FreshnessHistoryPoint,
    MultiCriteriaResponse, DimensionScoreItem,
)
from dataclasses import asdict as _dataclass_asdict
from services.skill_service.services.freshness_engine import (
    CVSkillInput, record_history_and_alert,
    MultiCriteriaFreshnessEngine, CVProfileInput,
)


def _dim_to_item(d):
    """Convert engine's DimensionScore (with nested DimensionDetail dataclass)
    to API DimensionScoreItem. Uses asdict to recursively flatten nested
    dataclasses so Pydantic can validate the inputs list."""
    return DimensionScoreItem(**_dataclass_asdict(d))


def _apply_llm_tips(user_id: str, profile: "CVProfileInput", result) -> None:
    """In-place: replace rule-based tips with LLM-generated tips when available.
    Silently no-op if Groq disabled / fails. Breakdown stays rule-based."""
    try:
        from services.skill_service.services.freshness_advisor import enrich_tips
        skill_res = result.skill_result
        top_contribs = []
        if skill_res and skill_res.contributions:
            top_contribs = [c.skill for c in sorted(
                skill_res.contributions, key=lambda c: c.contribution, reverse=True
            )[:5]]
        llm_tips = enrich_tips(
            user_id=user_id,
            role=result.role,
            seniority=result.seniority or "junior",
            snapshot_date=result.snapshot_date.isoformat(),
            cv_skills=[s.name for s in profile.skills],
            dimensions=result.dimensions,
            missing_top_market=(skill_res.missing_ideal if skill_res else None),
            top_contributors=top_contribs,
        )
        if not llm_tips:
            return
        for dim in result.dimensions:
            new_tips = llm_tips.get(dim.name)
            if new_tips and dim.detail:
                dim.detail.tips = new_tips
    except Exception as e:
        logger.warning("LLM tips enrich failed (keeping rule-based): %s", e)
from services.skill_service.services import cv_store
from services.skill_service.services.opportunity_window import find_opportunities
from services.skill_service.models.database import FreshnessAlertDB, FreshnessHistoryDB
from services.skill_service.services.db_session import SessionLocal
from services.skill_service.services.matcher import SkillMatcher
from services.skill_service.services.explainer import SkillGapExplainer
from services.skill_service.services.ontology import SkillOntology
from services.skill_service.services.course_service import CourseService
from services.skill_service.services.ats_engine import ATSScoringEngine
from services.skill_service.services.market_analyzer import MarketAnalyzer
from services.skill_service.services.market_intel import get_dashboard as get_market_intel_dashboard
from services.skill_service.services.freshness_engine import (
    CVFreshnessEngine, CVSkillInput,
)
from services.skill_service.services.db_session import init_db, get_db
from datetime import date as _date
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
_freshness_engine = None

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

def get_freshness_engine() -> CVFreshnessEngine:
    global _freshness_engine
    if _freshness_engine is None:
        _freshness_engine = CVFreshnessEngine(get_ontology())
    return _freshness_engine


_multi_engine = None
def get_multi_engine() -> MultiCriteriaFreshnessEngine:
    """Singleton MultiCriteriaFreshnessEngine — 8 dimensions (chuong3/3.2)."""
    global _multi_engine
    if _multi_engine is None:
        _multi_engine = MultiCriteriaFreshnessEngine(get_ontology(), get_freshness_engine())
    return _multi_engine


def _build_profile_from_cv(cv) -> CVProfileInput:
    """Helper: build CVProfileInput from CVRecord (cv_store)."""
    extras = cv.profile_extras or {}
    return CVProfileInput(
        skills=[
            CVSkillInput(name=s["name"], last_used_year=s.get("last_used_year"))
            for s in cv.skills_with_recency
        ],
        role=cv.target_role,
        seniority=extras.get("seniority") or "junior",
        years_experience=cv.years_experience,
        past_job_titles=list(extras.get("past_job_titles") or []),
        num_projects=int(extras.get("num_projects") or 0),
        project_skill_counts=list(extras.get("project_skill_counts") or []),
        degree=extras.get("degree"),
        major=extras.get("major"),
        achievement_text=extras.get("achievement_text") or "",
        language_text=extras.get("language_text") or "",
        has_contact=bool(extras.get("has_contact", True)),
        has_summary=bool(extras.get("has_summary", False)),
        has_education=bool(extras.get("has_education", False)),
        has_experience=bool(extras.get("has_experience", False)),
        has_skills=bool(extras.get("has_skills", True)),
        has_projects=bool(extras.get("has_projects", False)),
    )

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


@app.get("/market-intel/dashboard")
def market_intel_dashboard(
    source: str = Query("all"),
    role_group: str | None = Query(None),
    seniority: str | None = Query(None),
    db = Depends(get_db),
):
    """Aggregated payload for the /market-intel page.

    Single endpoint returning KPIs + 8 chart datasets so the frontend renders
    in one round-trip. All aggregations run in Postgres against jd_raw.
    """
    return get_market_intel_dashboard(db, source=source, role_group=role_group, seniority=seniority)


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



@app.post("/cv/freshness", response_model=FreshnessResponse)
def cv_freshness(
    request: FreshnessRequest,
    engine: CVFreshnessEngine = Depends(get_freshness_engine),
    db = Depends(get_db),
):
    """Tuần 10 — CV Freshness Score (chuong3/3.2)."""
    snapshot = _date.fromisoformat(request.snapshot_date) if request.snapshot_date else _date.today()
    cv_inputs = [CVSkillInput(name=s.name, last_used_year=s.last_used_year) for s in request.cv_skills]
    try:
        result = engine.compute(db=db, cv_skills=cv_inputs, role=request.role, snapshot_date=snapshot)
    except Exception as e:
        logger.error("Freshness computation failed: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

    return FreshnessResponse(
        score=result.score,
        role=result.role,
        snapshot_date=result.snapshot_date.isoformat(),
        contributions=[SkillContributionItem(**c.__dict__) for c in result.contributions],
        ideal_skills=result.ideal_skills,
        missing_ideal=result.missing_ideal,
        cold_start=result.cold_start,
    )


# ─── Tuần 14: BackgroundTask for Freshness recompute ──────────────────────────

def _recompute_freshness_bg(user_id: str) -> None:
    """Background job: recompute Multi-criteria Freshness 8 dim for `user_id`
    + persist Skill-dim history & alerts. Opens its own DB session because the
    request-scoped session is already closed by the time this runs.
    """
    db = SessionLocal()
    try:
        cv = cv_store.get_cv(db, user_id)
        if cv is None:
            logger.warning("BG recompute: no CV for user_id=%s", user_id)
            return
        profile = _build_profile_from_cv(cv)
        multi_result = get_multi_engine().compute(db=db, profile=profile)
        # Persist Skill-dimension history (existing time-series + alerts pipeline).
        if multi_result.skill_result is not None:
            record_history_and_alert(db=db, user_id=user_id, result=multi_result.skill_result)
        logger.info(
            "BG recompute done user=%s role=%s total=%.2f cold_start=%s dims=%s",
            user_id, cv.target_role, multi_result.score, multi_result.cold_start,
            {d.name: d.score for d in multi_result.dimensions},
        )
    except Exception as e:
        logger.error("BG recompute failed for user=%s: %s", user_id, e, exc_info=True)
    finally:
        db.close()


# ─── Tuần 14: user-state endpoints ────────────────────────────────────────────

@app.get("/cv/me")
def get_saved_cv(user_id: str = Query(...), db = Depends(get_db)):
    """Return saved CV config (target_role, seniority, years_experience,
    preferred_location, preferred_work_modes, extras) so frontend can
    prefill the 'Mục tiêu Ứng tuyển' form. 404 if user chưa upsert lần nào."""
    cv = cv_store.get_cv(db, user_id)
    if cv is None:
        raise HTTPException(status_code=404, detail="No CV saved")
    extras = cv.profile_extras or {}
    return {
        "user_id": cv.user_id,
        "target_role": cv.target_role,
        "years_experience": cv.years_experience,
        "preferred_location": cv.preferred_location,
        "preferred_work_modes": cv.preferred_work_modes or [],
        "seniority": extras.get("seniority"),
        "skill_count": len(cv.skills_with_recency or []),
        "updated_at": cv.updated_at.isoformat() if cv.updated_at else None,
    }


@app.post("/cv/me", response_model=CVUpsertResponse)
def upsert_cv(
    request: CVUpsertRequest,
    background_tasks: BackgroundTasks,
    db = Depends(get_db),
):
    """Insert/update the user's CV. Triggers a background Freshness recompute
    per §3.2.5 ("Sự kiện: User upload CV mới → BackgroundTask")."""
    skills = [s.dict() for s in request.skills]
    # Collect 8-dim profile extras — only non-None fields go through so
    # partial updates preserve previously-set keys (handled in cv_store).
    extras: dict = {}
    for key in (
        "seniority", "past_job_titles", "num_projects", "project_skill_counts",
        "degree", "major", "achievement_text", "language_text",
        "has_contact", "has_summary", "has_education",
        "has_experience", "has_skills", "has_projects",
    ):
        val = getattr(request, key, None)
        if val is not None:
            extras[key] = val
    rec = cv_store.upsert_cv(
        db, request.user_id, request.target_role, skills,
        years_experience=request.years_experience,
        preferred_location=request.preferred_location,
        preferred_work_modes=request.preferred_work_modes,
        profile_extras=extras if extras else None,
    )
    background_tasks.add_task(_recompute_freshness_bg, request.user_id)
    return CVUpsertResponse(
        user_id=rec.user_id, target_role=rec.target_role,
        skill_count=len(rec.skills_with_recency),
        updated_at=rec.updated_at.isoformat(),
        recompute_scheduled=True,
    )


@app.get("/health-score", response_model=HealthScoreResponse)
def health_score(
    user_id: str = Query(...),
    persist: bool = Query(True, description="Insert into history + fire alerts"),
    db = Depends(get_db),
):
    """Compute Multi-criteria Freshness Score (8 dim) for `user_id` using
    their stored CV. Returns total + per-dimension breakdown for the radar
    chart. Persists Skill-dim history & fires alerts when score drops."""
    cv = cv_store.get_cv(db, user_id)
    if cv is None:
        raise HTTPException(status_code=404, detail=f"No CV stored for user_id={user_id}")
    try:
        profile = _build_profile_from_cv(cv)
        result = get_multi_engine().compute(db=db, profile=profile)
        _apply_llm_tips(user_id, profile, result)
    except Exception as e:
        logger.error("health-score failed: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

    history_recorded = False
    if persist and result.skill_result is not None:
        try:
            record_history_and_alert(db=db, user_id=user_id, result=result.skill_result)
            history_recorded = True
        except Exception as e:
            logger.error("history record failed: %s", e, exc_info=True)

    skill_res = result.skill_result
    return HealthScoreResponse(
        user_id=user_id,
        role=result.role,
        score=result.score,
        snapshot_date=result.snapshot_date.isoformat(),
        contributions=[SkillContributionItem(**c.__dict__) for c in (skill_res.contributions if skill_res else [])],
        ideal_skills=skill_res.ideal_skills if skill_res else [],
        missing_ideal=skill_res.missing_ideal if skill_res else [],
        cold_start=result.cold_start,
        history_recorded=history_recorded,
        dimensions=[_dim_to_item(d) for d in result.dimensions],
        seniority=result.seniority,
    )


@app.get("/cv/freshness-multi", response_model=MultiCriteriaResponse)
def cv_freshness_multi(
    user_id: str = Query(...),
    db = Depends(get_db),
):
    """Dedicated endpoint returning Multi-criteria Freshness 8-dim breakdown
    (chuong3/3.2). Same logic as /health-score but doesn't persist history —
    useful for live recompute previews (e.g. user editing skills inline)."""
    cv = cv_store.get_cv(db, user_id)
    if cv is None:
        raise HTTPException(status_code=404, detail=f"No CV stored for user_id={user_id}")
    try:
        profile = _build_profile_from_cv(cv)
        result = get_multi_engine().compute(db=db, profile=profile)
        _apply_llm_tips(user_id, profile, result)
    except Exception as e:
        logger.error("freshness-multi failed: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

    skill_res = result.skill_result
    return MultiCriteriaResponse(
        user_id=user_id,
        role=result.role,
        seniority=result.seniority,
        snapshot_date=result.snapshot_date.isoformat(),
        score=result.score,
        dimensions=[_dim_to_item(d) for d in result.dimensions],
        skill_contributions=[SkillContributionItem(**c.__dict__) for c in (skill_res.contributions if skill_res else [])],
        ideal_skills=skill_res.ideal_skills if skill_res else [],
        missing_ideal=skill_res.missing_ideal if skill_res else [],
        cold_start=result.cold_start,
    )


@app.post("/cv/simulate", response_model=HealthScoreResponse)
def simulate_freshness(
    request: CVUpsertRequest,
    db = Depends(get_db),
):
    """Tuần 16 — What-if Simulation endpoint.
    Computes 8-dim freshness using the provided hypothetical profile without saving it."""
    skills = [s.dict() for s in request.skills]
    
    cv = cv_store.get_cv(db, request.user_id)
    if cv is not None:
        profile = _build_profile_from_cv(cv)
        # Override skills with the simulated ones
        profile.skills = [CVSkillInput(name=s["name"], last_used_year=s.get("last_used_year")) for s in skills]
        # Allow overriding seniority if passed
        if request.seniority:
            profile.seniority = request.seniority
    else:
        profile = CVProfileInput(
            skills=[CVSkillInput(name=s["name"], last_used_year=s.get("last_used_year")) for s in skills],
            role=request.target_role,
            seniority=request.seniority or "junior",
            years_experience=request.years_experience,
            past_job_titles=request.past_job_titles or [],
            num_projects=request.num_projects or 0,
            project_skill_counts=request.project_skill_counts or [],
            degree=request.degree,
            major=request.major,
            achievement_text=request.achievement_text or "",
            language_text=request.language_text or "",
            has_contact=request.has_contact if request.has_contact is not None else True,
            has_summary=request.has_summary if request.has_summary is not None else False,
            has_education=request.has_education if request.has_education is not None else False,
            has_experience=request.has_experience if request.has_experience is not None else False,
            has_skills=request.has_skills if request.has_skills is not None else True,
            has_projects=request.has_projects if request.has_projects is not None else False,
        )
    try:
        result = get_multi_engine().compute(db=db, profile=profile)
    except Exception as e:
        logger.error("simulate_freshness failed: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

    skill_res = result.skill_result
    return HealthScoreResponse(
        user_id=request.user_id,
        role=result.role,
        score=result.score,
        snapshot_date=result.snapshot_date.isoformat(),
        contributions=[SkillContributionItem(**c.__dict__) for c in (skill_res.contributions if skill_res else [])],
        ideal_skills=skill_res.ideal_skills if skill_res else [],
        missing_ideal=skill_res.missing_ideal if skill_res else [],
        cold_start=result.cold_start,
        history_recorded=False,
        dimensions=[_dim_to_item(d) for d in result.dimensions],
        seniority=result.seniority,
    )



@app.get("/freshness/history", response_model=FreshnessHistoryResponse)
def freshness_history(
    user_id: str = Query(...),
    role: str = Query(None),
    limit: int = Query(60, ge=1, le=365),
    db = Depends(get_db),
):
    """Return Freshness Score time-series for the user (most-recent N points
    by `snapshot_date`). Used by the dashboard time-series chart (§3.5)."""
    q = db.query(FreshnessHistoryDB).filter(FreshnessHistoryDB.user_id == user_id)
    if role:
        q = q.filter(FreshnessHistoryDB.role == role)
    rows = q.order_by(FreshnessHistoryDB.snapshot_date.desc()).limit(limit).all()
    rows.reverse()  # send chronological asc to the chart
    return FreshnessHistoryResponse(
        user_id=user_id, role=role,
        points=[
            FreshnessHistoryPoint(
                snapshot_date=r.snapshot_date.isoformat(),
                score=r.score,
                cold_start=bool(r.cold_start),
            )
            for r in rows
        ],
    )


@app.get("/skill-alerts", response_model=SkillAlertsResponse)
def skill_alerts(
    user_id: str = Query(...),
    limit: int = Query(20, ge=1, le=100),
    db = Depends(get_db),
):
    """Return the most recent score-drop alerts for the user (§3.2.5)."""
    rows = (
        db.query(FreshnessAlertDB)
        .filter(FreshnessAlertDB.user_id == user_id)
        .order_by(FreshnessAlertDB.fired_at.desc())
        .limit(limit)
        .all()
    )
    items = [
        AlertItem(
            id=r.id, user_id=r.user_id, role=r.role,
            fired_at=r.fired_at.isoformat(),
            prev_score=r.prev_score, new_score=r.new_score,
            delta=r.delta, reason=r.reason or "",
        )
        for r in rows
    ]
    return SkillAlertsResponse(user_id=user_id, alerts=items)


@app.get("/opportunity-window", response_model=OpportunityWindowResponse)
def opportunity_window(
    user_id: str = Query(...),
    days: int = Query(7, ge=1, le=30),
    limit: int = Query(10, ge=1, le=50),
    min_match: float = Query(0.5, ge=0.0, le=1.0),
    db = Depends(get_db),
):
    """Return recent JDs that match the user's CV well (§FR-D1)."""
    cv = cv_store.get_cv(db, user_id)
    if cv is None:
        raise HTTPException(status_code=404, detail=f"No CV stored for user_id={user_id}")
    skill_names = [s["name"] for s in cv.skills_with_recency]
    opps = find_opportunities(
        db=db, cv_skills=skill_names, target_role=cv.target_role,
        cv_years=cv.years_experience,
        cv_location=cv.preferred_location,
        cv_work_modes=cv.preferred_work_modes or None,
        days=days, limit=limit, min_match=min_match,
    )
    return OpportunityWindowResponse(
        user_id=user_id, role=cv.target_role, days=days,
        items=[OpportunityJDItem(**o.__dict__) for o in opps],
    )


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=settings.service_port)
