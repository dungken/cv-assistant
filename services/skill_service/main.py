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
from typing import List, Optional
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
    HealthScoreResponse,
    OpportunityWindowResponse, OpportunityJDItem,
    MultiCriteriaResponse, DimensionScoreItem,
)
from dataclasses import asdict as _dataclass_asdict
from services.skill_service.services.freshness_engine import (
    CVSkillInput,
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
    db = Depends(get_db),
):
    """Compute Multi-criteria Freshness Score (8 dim) for `user_id` using
    their stored CV. Returns total + per-dimension breakdown for the radar chart."""
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


@app.get("/opportunity-window", response_model=OpportunityWindowResponse)
def opportunity_window(
    user_id: str = Query(...),
    days: int = Query(30, ge=1, le=180),
    limit: int = Query(20, ge=1, le=100),
    min_match: float = Query(0.4, ge=0.0, le=1.0),
    work_modes: Optional[List[str]] = Query(None,
        description="Override CV's preferred_work_modes (csv-style query: ?work_modes=remote&work_modes=hybrid)"),
    sort: str = Query("match", regex="^(match|newest|salary)$"),
    db = Depends(get_db),
):
    """Return recent JDs that match the user's CV well (§FR-D1) + aggregate insights + per-JD status."""
    cv = cv_store.get_cv(db, user_id)
    if cv is None:
        raise HTTPException(status_code=404, detail=f"No CV stored for user_id={user_id}")
    skill_names = [s["name"] for s in cv.skills_with_recency]
    effective_modes = work_modes if work_modes is not None else (cv.preferred_work_modes or None)
    opps, aggregate = find_opportunities(
        db=db, cv_skills=skill_names, target_role=cv.target_role,
        cv_years=cv.years_experience,
        cv_location=cv.preferred_location,
        cv_work_modes=effective_modes,
        days=days, limit=limit, min_match=min_match,
        ontology=get_ontology(),
    )

    # Override sort if user picks newest/salary (default 'match' đã được handle bên engine)
    if sort == "newest":
        opps.sort(key=lambda o: o.posted_date, reverse=True)
    elif sort == "salary":
        opps.sort(key=lambda o: (o.salary_max or o.salary_min or 0), reverse=True)

    # Attach user JD statuses (saved/applied/...) — bulk fetch để O(1)
    jd_keys = [o.jd_key for o in opps]
    status_map = _bulk_get_jd_statuses(db, user_id, jd_keys) if jd_keys else {}

    items = []
    for o in opps:
        d = dict(o.__dict__)
        d["status"] = status_map.get(o.jd_key, "new")
        items.append(OpportunityJDItem(**d))

    return OpportunityWindowResponse(
        user_id=user_id, role=cv.target_role, days=days,
        items=items,
        aggregate=aggregate,
    )


# ─── JD Status tracking (saved/applied/interview/rejected) ────────────────────

def _bulk_get_jd_statuses(db, user_id: str, jd_keys: list[str]) -> dict[str, str]:
    """Fetch JD status for all jd_keys at once. Returns {jd_key: status}."""
    if not jd_keys:
        return {}
    from services.skill_service.models.database import UserJdStatusDB
    rows = (
        db.query(UserJdStatusDB)
        .filter(UserJdStatusDB.user_id == user_id, UserJdStatusDB.jd_key.in_(jd_keys))
        .all()
    )
    return {r.jd_key: r.status for r in rows}


@app.put("/jd-status")
def upsert_jd_status(
    user_id: str = Query(...),
    jd_key: str = Query(...),
    status: str = Query(..., regex="^(new|saved|applied|interview|rejected)$"),
    db = Depends(get_db),
):
    """Set per-user JD status. status='new' will delete the row (treat as default)."""
    from services.skill_service.models.database import UserJdStatusDB
    from datetime import datetime as _dt
    row = (
        db.query(UserJdStatusDB)
        .filter(UserJdStatusDB.user_id == user_id, UserJdStatusDB.jd_key == jd_key)
        .one_or_none()
    )
    if status == "new":
        if row:
            db.delete(row)
            db.commit()
        return {"status": "new", "jd_key": jd_key}
    if row:
        row.status = status
        row.updated_at = _dt.utcnow()
    else:
        row = UserJdStatusDB(user_id=user_id, jd_key=jd_key, status=status, updated_at=_dt.utcnow())
        db.add(row)
    db.commit()
    return {"status": status, "jd_key": jd_key}


@app.get("/jd-status/stats")
def jd_status_stats(user_id: str = Query(...), db = Depends(get_db)):
    """Counts per status — used for filter tabs."""
    from services.skill_service.models.database import UserJdStatusDB
    from sqlalchemy import func
    rows = (
        db.query(UserJdStatusDB.status, func.count(UserJdStatusDB.id))
        .filter(UserJdStatusDB.user_id == user_id)
        .group_by(UserJdStatusDB.status)
        .all()
    )
    return {"counts": {status: cnt for status, cnt in rows}}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=settings.service_port)
