from pydantic import BaseModel
from typing import List, Optional

class CareerRequest(BaseModel):
    current_role: str
    target_role: Optional[str] = None
    current_skills: List[str] = []

class CareerStep(BaseModel):
    step: int
    role: str
    role_code: Optional[str] = None
    timeframe: str
    skills_to_learn: List[str]
    description: str

class CareerPath(BaseModel):
    path_type: str  # conservative, moderate, ambitious
    total_time: str
    steps: List[CareerStep]

class SkillGap(BaseModel):
    current: List[str]
    required: List[str]
    missing: List[str]
    overlap: List[str] = []
    readiness_score: float = 0.0

class RelatedRole(BaseModel):
    title: str
    code: str
    description: str = ""
    timeframe: str = ""

class CareerRecommendation(BaseModel):
    current_role: str
    target_role: str
    experience_level: str = ""
    skill_gap: SkillGap
    paths: List[CareerPath]
    related_roles: List[RelatedRole] = []
