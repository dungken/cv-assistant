from pydantic import BaseModel, Field
from typing import List, Dict, Optional
from shared.models.cv_models import CVData

class CVDetails(BaseModel):
    skills: List[str]
    experience_years: float = 0.0
    education_level: Optional[str] = None  # Ph.D, Master, Bachelor, None

class SkillMatchRequest(BaseModel):
    cv_skills: List[str] = [] # Legacy support
    cv_details: Optional[CVDetails] = None
    jd_text: str
    jd_id: Optional[str] = None

class MultiSkillMatchRequest(BaseModel):
    cv_details: CVDetails
    jd_texts: List[str]


# ─── Knowledge Graph / Ontology Schemas ──────────────────────────────────────

class SkillNodeResponse(BaseModel):
    """Full skill node with relationships and metadata."""
    skill_id: str
    name: str
    category: Optional[str] = None
    subcategory: Optional[str] = None
    level_range: List[str] = ["intermediate", "advanced"]
    description: str = ""
    demand_score: float = 0.5
    trending: bool = False
    relationships: Dict[str, List[str]] = {}
    required_by: List[str] = []
    leads_from: List[str] = []


class GraphNode(BaseModel):
    id: str
    label: str
    category: str = "Other"
    demand: float = 0.5
    trending: bool = False
    distance: int = 0


class GraphEdge(BaseModel):
    source: str
    target: str
    type: str


class GraphDataResponse(BaseModel):
    """Graph data for visualization (nodes + edges)."""
    nodes: List[GraphNode] = []
    edges: List[GraphEdge] = []


class SkillSearchResult(BaseModel):
    name: str
    category: str = ""
    subcategory: str = ""
    demand: float = 0.5
    trending: bool = False
    score: float = 0.0


class SkillSearchResponse(BaseModel):
    results: List[SkillSearchResult] = []
    total: int = 0


class OntologyStatsResponse(BaseModel):
    total_nodes: int = 0
    total_edges: int = 0
    edge_counts: Dict[str, int] = {}
    category_counts: Dict[str, int] = {}
    connectivity: float = 0.0
    categories: int = 0


class CategoriesResponse(BaseModel):
    categories: List[str] = []

class SemanticMatch(BaseModel):
    cv_skill: str
    jd_skill: str
    similarity: float

class OntologyMatch(BaseModel):
    cv_skill: str
    jd_skill: str
    distance: float
    relationship: str
    category: str

class SkillGapExplanation(BaseModel):
    summary: str = ""
    score_interpretation: str = ""
    gap_by_category: Dict = {}
    priority_skills: List[Dict] = []
    learning_plan: List[Dict] = []
    transferable_strengths: List[Dict] = []
    total_estimated_weeks: int = 0

class MatchedSkill(BaseModel):
    skill: str
    match_type: str  # exact, ontology, semantic
    cv_mention: str
    jd_requirement: str  # required, preferred

class MissingSkill(BaseModel):
    skill: str
    jd_requirement: str
    priority: str
    suggestion: str

class ExtraSkill(BaseModel):
    skill: str
    relevance: str
    suggestion: str

class ExperienceMatch(BaseModel):
    current: float
    required_min: float
    required_max: Optional[float] = None
    status: str  # match, partial, gap
    score: float

class EducationMatch(BaseModel):
    current: Optional[str]
    required: Optional[str]
    status: str
    score: float

class Course(BaseModel):
    id: str
    title: str
    platform: str
    url: str
    rating: float
    duration_hours: float
    price: float
    level: str
    skills: List[str]
    is_bookmarked: bool = False
    progress: float = 0.0

class LearningPhase(BaseModel):
    phase: str
    weeks: str
    skills: List[str]
    courses: List[Course] = []
    estimated_hours: float = 0.0

class LearningRoadmap(BaseModel):
    total_weeks: int
    phases: List[LearningPhase]
    current_progress: float = 0.0

class BookmarkRequest(BaseModel):
    course_id: str
    user_id: Optional[str] = "default_user"

class ProgressUpdateRequest(BaseModel):
    course_id: str
    progress: float  # 0.0 to 1.0
    user_id: Optional[str] = "default_user"

class SkillMatchResponse(BaseModel):
    analysis_id: str = "ana-123"
    jd_title: str = "Unknown Role"
    jd_company: str = "Unknown Company"
    overall_score: float
    breakdown: Dict[str, float] = Field(default_factory=lambda: {"skills": 0, "experience": 0, "education": 0})
    skills: Dict[str, List] = Field(default_factory=lambda: {"matched": [], "missing": [], "extra": []})
    experience: Optional[ExperienceMatch] = None
    education: Optional[EducationMatch] = None
    recommendations: List[str] = [] # Keeping for legacy
    course_recommendations: List[Course] = [] # US-12
    learning_roadmap: Optional[LearningRoadmap] = None # US-12
    skill_gap_explanation: Optional[SkillGapExplanation] = None
    # For legacy frontend support
    jd_skills_extracted: List[str] = []
    exact_matches: List[str] = []
    ontology_matches: List[OntologyMatch] = []
    semantic_matches: List[SemanticMatch] = []
    missing_skills: List[str] = []
    cv_profile: Dict[str, List[str]] = {}

class MultiSkillMatchResponse(BaseModel):
    results: List[SkillMatchResponse]

# ─── US-18: ATS Scoring Schemas ───────────────────────────────────────────────

class ATSScoreRequest(BaseModel):
    cv_data: CVData
    jd_text: Optional[str] = None

class ATSIssue(BaseModel):
    category: str
    severity: str  # high, medium, low
    message: str
    suggestion: str

class ATSScoreResponse(BaseModel):
    cv_id: str = "unknown"
    total_score: float
    breakdown: Dict[str, float]
    issues: List[ATSIssue]
    benchmark_avg: float = 70.0

# ─── US-19: Market Dashboard Schemas ──────────────────────────────────────────

class SkillTrend(BaseModel):
    name: str
    count: int
    percentage: float
    growth: float = 0.0

class SkillCorrelation(BaseModel):
    skill_a: str
    skill_b: str
    weight: float

class SalaryStats(BaseModel):
    category: str
    min_salary: float
    max_salary: float
    median_salary: float
    currency: str = "USD"

class MarketOverviewResponse(BaseModel):
    top_skills: List[SkillTrend]
    industry_distribution: Dict[str, int]
    location_distribution: Dict[str, int]
    salary_overview: List[SalaryStats]
    correlations: List[SkillCorrelation]
