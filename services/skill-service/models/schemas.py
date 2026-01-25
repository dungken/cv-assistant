from pydantic import BaseModel
from typing import List, Optional

class SkillMatchRequest(BaseModel):
    cv_skills: List[str]
    jd_text: str

class SemanticMatch(BaseModel):
    cv_skill: str
    jd_skill: str
    similarity: float

class SkillMatchResponse(BaseModel):
    jd_skills_extracted: List[str]
    exact_matches: List[str]
    semantic_matches: List[SemanticMatch]
    overall_score: float
    recommendations: List[str]
