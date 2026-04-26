from pydantic import BaseModel
from typing import List, Optional, Dict
from shared.models.base_models import Source
from shared.models.cv_models import CVData

class ChatRequest(BaseModel):
    message: str
    session_id: str = "default"
    include_sources: bool = True
    current_step: Optional[int] = None
    cv_data: Optional[CVData] = None
    active_tool: Optional[str] = None  # US-26: 'match' | 'career' | 'upload' | 'ats' | 'jd' | 'graph' | 'market'
    user_id: Optional[str] = None  # US-27: email or unique user identifier for memory
    tool_context: Optional[str] = None  # Optional UI/tool data snapshot for prompt grounding

class TitleRequest(BaseModel):
    user_message: str
    assistant_message: str
    active_tool: Optional[str] = None
    user_id: Optional[str] = None
    tool_context: Optional[str] = None

class TitleResponse(BaseModel):
    title: str


# ─── US-27: User Memory Models ──────────────────────────────────────────────

class CareerProfile(BaseModel):
    current_role: Optional[str] = None
    current_skills: List[str] = []
    target_role: Optional[str] = None
    timeline_months: Optional[int] = None

class SuggestionRecord(BaseModel):
    type: str  # course, book, skill, certification
    content: str
    given_at: str  # ISO date

class UserMemory(BaseModel):
    user_id: str
    display_name: Optional[str] = None
    tone_preference: str = "professional"  # professional | casual
    language: str = "vi"  # vi | en
    career_profile: CareerProfile = CareerProfile()
    skill_gaps: List[str] = []
    suggestion_history: List[SuggestionRecord] = []
    field_timestamps: Dict[str, str] = {}  # field_name → last_updated ISO
    created_at: str = ""
    updated_at: str = ""

class MemoryUpdateRequest(BaseModel):
    display_name: Optional[str] = None
    tone_preference: Optional[str] = None
    language: Optional[str] = None
    career_profile: Optional[Dict] = None
    skill_gaps: Optional[List[str]] = None

class ChatResponse(BaseModel):
    response: str
    sources: List[Source]
    session_id: str
    timestamp: str

class SessionHistory(BaseModel):
    session_id: str
    messages: List[Dict]
    count: int

class CollectorResponse(BaseModel):
    response: str
    current_step: int
    cv_data: CVData
    session_id: str
    timestamp: str

class CVGenerateRequest(BaseModel):
    cv_data: CVData
    jd_text: Optional[str] = None
    target_language: str = "vi" # Default to Vietnamese

class CVRewriteRequest(BaseModel):
    title: str
    context: str
    raw_points: List[str]
    language: str = "vi"

class CVRewriteResponse(BaseModel):
    rewritten_points: List[str]

class CVOptimizeResponse(BaseModel):
    optimized_cv: CVData
    ats_result: Optional[Dict] = None # Simplified dict for ATS result

# ─── US-17: Optimization Suggestions ─────────────────────────────────────────

class OptimizationSuggestion(BaseModel):
    id: str
    category: str
    priority: str  # critical, important, nice_to_have
    title: str
    description: str
    why: str
    how: str
    evidence: str
    confidence: float
    preview: Optional[str] = None  # Content to be applied (e.g. drafted summary)

class OptimizationResponse(BaseModel):
    suggestions: List[OptimizationSuggestion]
    ats_score: float
    breakdown: Dict[str, float]


# ─── US-29: CV Builder Optimization ──────────────────────────────────────────

class CVSuggestRequest(BaseModel):
    job_title: str
    company: Optional[str] = None
    duration: Optional[str] = None
    raw_input: str
    section: str = "experience"  # experience, summary, projects

class BulletSuggestion(BaseModel):
    id: int
    bullet: str
    star_format: Dict[str, str]
    confidence: float

class CVSuggestResponse(BaseModel):
    job_title: str
    company: Optional[str]
    duration: Optional[str]
    raw_input: str
    suggestions: List[BulletSuggestion]

class CVValidateRequest(BaseModel):
    field: str
    value: str
    field_type: str  # email | phone | date | text | url

class CVValidateResponse(BaseModel):
    field: str
    is_valid: bool
    error: Optional[str] = None
    warning: Optional[str] = None

class CVDraftData(BaseModel):
    user_id: str
    current_step: int
    completed_steps: List[str] = []
    progress_percent: int = 0
    data: CVData
