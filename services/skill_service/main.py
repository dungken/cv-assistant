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
    LearningPathRequest, LearningPathResponse, PathStepResponse, JDLabel,
    CVUpsertRequest, CVUpsertResponse,
    HealthScoreResponse, SkillAlertsResponse, AlertItem,
    OpportunityWindowResponse, OpportunityJDItem,
    LearningPathMeRequest,
    FreshnessHistoryResponse, FreshnessHistoryPoint,
)
from services.skill_service.services.learning_path import LearningPathOptimizer
from services.skill_service.services.lp_benchmark import JD as LP_JD, TestCase as LP_TestCase
from services.skill_service.services.freshness_engine import (
    CVSkillInput, record_history_and_alert,
)
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
_lp_optimizer = None

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

def get_lp_optimizer() -> LearningPathOptimizer:
    global _lp_optimizer
    if _lp_optimizer is None:
        _lp_optimizer = LearningPathOptimizer(get_ontology())
    return _lp_optimizer

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

@app.post("/learning-path", response_model=LearningPathResponse)
def learning_path(
    request: LearningPathRequest,
    optimizer: LearningPathOptimizer = Depends(get_lp_optimizer),
):
    """Tuần 12 — Learning Path Optimizer (chuong3/3.3)."""
    tc = LP_TestCase(
        test_id="api",
        description="",
        role=request.role,
        S_user=request.cv_skills,
        JDs=[LP_JD(id=j.id, required=j.required) for j in request.jds],
        budget=request.budget_weeks,
    )
    try:
        result, explained = optimizer.optimize(tc, algorithm=request.algorithm)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("learning_path failed: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

    coverage = (
        100.0 * explained.jd_unlocked_count / max(explained.jd_unlocked_total, 1)
    )
    return LearningPathResponse(
        algorithm=explained.algorithm,
        total_weeks=explained.total_weeks,
        jd_unlocked_count=explained.jd_unlocked_count,
        jd_unlocked_total=explained.jd_unlocked_total,
        coverage_percent=round(coverage, 2),
        steps=[PathStepResponse(**s.__dict__) for s in explained.steps],
        runtime_ms=round(1000 * result.runtime_s, 3),
    )


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
    """Background job: recompute Freshness Score for `user_id` and persist
    history + alerts. Opens its own DB session because the request-scoped
    session is already closed by the time this runs.
    """
    db = SessionLocal()
    try:
        cv = cv_store.get_cv(db, user_id)
        if cv is None:
            logger.warning("BG recompute: no CV for user_id=%s", user_id)
            return
        engine = get_freshness_engine()
        cv_inputs = [
            CVSkillInput(name=s["name"], last_used_year=s.get("last_used_year"))
            for s in cv.skills_with_recency
        ]
        result = engine.compute(db=db, cv_skills=cv_inputs, role=cv.target_role)
        record_history_and_alert(db=db, user_id=user_id, result=result)
        logger.info(
            "BG recompute done user=%s role=%s score=%.2f cold_start=%s",
            user_id, cv.target_role, result.score, result.cold_start,
        )
    except Exception as e:
        logger.error("BG recompute failed for user=%s: %s", user_id, e, exc_info=True)
    finally:
        db.close()


# ─── Tuần 14: user-state endpoints ────────────────────────────────────────────

@app.post("/cv/me", response_model=CVUpsertResponse)
def upsert_cv(
    request: CVUpsertRequest,
    background_tasks: BackgroundTasks,
    db = Depends(get_db),
):
    """Insert/update the user's CV. Triggers a background Freshness recompute
    per §3.2.5 ("Sự kiện: User upload CV mới → BackgroundTask")."""
    skills = [s.dict() for s in request.skills]
    rec = cv_store.upsert_cv(
        db, request.user_id, request.target_role, skills,
        years_experience=request.years_experience,
        preferred_location=request.preferred_location,
        preferred_work_modes=request.preferred_work_modes,
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
    engine: CVFreshnessEngine = Depends(get_freshness_engine),
    db = Depends(get_db),
):
    """Compute current Freshness Score for `user_id` using their stored CV.
    By default also writes to history and fires an alert if the score dropped."""
    cv = cv_store.get_cv(db, user_id)
    if cv is None:
        raise HTTPException(status_code=404, detail=f"No CV stored for user_id={user_id}")
    cv_inputs = [
        CVSkillInput(name=s["name"], last_used_year=s.get("last_used_year"))
        for s in cv.skills_with_recency
    ]
    try:
        result = engine.compute(db=db, cv_skills=cv_inputs, role=cv.target_role)
    except Exception as e:
        logger.error("health-score failed: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

    history_recorded = False
    if persist:
        try:
            record_history_and_alert(db=db, user_id=user_id, result=result)
            history_recorded = True
        except Exception as e:
            logger.error("history record failed: %s", e, exc_info=True)

    return HealthScoreResponse(
        user_id=user_id, role=result.role,
        score=result.score, snapshot_date=result.snapshot_date.isoformat(),
        contributions=[SkillContributionItem(**c.__dict__) for c in result.contributions],
        ideal_skills=result.ideal_skills, missing_ideal=result.missing_ideal,
        cold_start=result.cold_start, history_recorded=history_recorded,
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


@app.post("/learning-path/me", response_model=LearningPathResponse)
def learning_path_me(
    request: LearningPathMeRequest,
    optimizer: LearningPathOptimizer = Depends(get_lp_optimizer),
    db = Depends(get_db),
):
    """User-facing variant of /learning-path: builds the JD target set
    automatically from recent crawl data instead of requiring the client to
    pass it (§3.3.1 step "Xác định tập JD mục tiêu")."""
    cv = cv_store.get_cv(db, request.user_id)
    if cv is None:
        raise HTTPException(status_code=404, detail=f"No CV stored for user_id={request.user_id}")
    skill_names = [s["name"] for s in cv.skills_with_recency]
    # Pull recent JDs that aren't already easily satisfied (ATS too high) nor
    # too far out of reach (ATS too low). The opportunity helper computes a
    # coverage ratio we can reuse here.
    opps = find_opportunities(
        db=db, cv_skills=skill_names, target_role=cv.target_role,
        cv_years=cv.years_experience,
        cv_location=cv.preferred_location,
        cv_work_modes=cv.preferred_work_modes or None,
        days=request.days, limit=request.max_jds, min_match=0.4,
    )
    # Filter:
    # - Drop "too easy" JDs (composite ≥ 0.85 — user can already apply)
    # - Drop JDs where the experience gap is too large (cv_years < min_exp - 2):
    #   no amount of learning skill fixes "needs 5y, you have 1y". This
    #   aligns the optimizer with real hiring constraints (§3.1).
    def _exp_reachable(o):
        if cv.years_experience is None or o.min_exp is None:
            return True
        return float(cv.years_experience) >= float(o.min_exp) - 2.0
    target_opps = [o for o in opps if o.match_score < 0.85 and _exp_reachable(o)]
    if not target_opps:
        raise HTTPException(
            status_code=422,
            detail="No JDs in the target window (0.4 ≤ coverage < 0.85). "
                   "Try widening `days` or check crawler data freshness.",
        )

    # Feed only *required* skills to the optimizer — those are the actual
    # blockers. Preferred skills are nice-to-have and shouldn't drive what we
    # tell the user to learn. (matched + missing_required = full required set.)
    tc = LP_TestCase(
        test_id=f"me-{request.user_id}",
        description=f"User {request.user_id} → {cv.target_role}",
        role=cv.target_role,
        S_user=skill_names,
        JDs=[
            LP_JD(id=o.jd_key, required=list({*o.matched_skills, *o.missing_required}))
            for o in target_opps
        ],
        budget=request.budget_weeks,
    )
    try:
        result, explained = optimizer.optimize(tc, algorithm=request.algorithm)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    coverage = 100.0 * explained.jd_unlocked_count / max(explained.jd_unlocked_total, 1)
    # Build human labels + URLs for every jd_key the optimizer might mention
    # so the frontend can render clickable links instead of raw 16-char hashes.
    jd_labels = {
        o.jd_key: JDLabel(
            label=f"{o.title} — {o.company}" if o.company else o.title,
            url=o.url,
        )
        for o in target_opps
    }
    return LearningPathResponse(
        algorithm=explained.algorithm,
        total_weeks=explained.total_weeks,
        jd_unlocked_count=explained.jd_unlocked_count,
        jd_unlocked_total=explained.jd_unlocked_total,
        coverage_percent=round(coverage, 2),
        steps=[PathStepResponse(**s.__dict__) for s in explained.steps],
        runtime_ms=round(1000 * result.runtime_s, 3),
        jd_labels=jd_labels,
    )


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=settings.service_port)
