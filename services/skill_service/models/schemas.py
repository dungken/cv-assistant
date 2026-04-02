from pydantic import BaseModel
from typing import List, Dict, Optional

class SkillMatchRequest(BaseModel):
    cv_skills: List[str]
    jd_text: str

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

class SkillMatchResponse(BaseModel):
    jd_skills_extracted: List[str]
    exact_matches: List[str]
    ontology_matches: List[OntologyMatch] = []
    semantic_matches: List[SemanticMatch]
    missing_skills: List[str] = []
    overall_score: float
    cv_profile: Dict[str, List[str]] = {}
    recommendations: List[str]
    skill_gap_explanation: Optional[SkillGapExplanation] = None
