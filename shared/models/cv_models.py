from pydantic import BaseModel, Field
from typing import List, Optional

class PersonalInfo(BaseModel):
    full_name: str = ""
    email: str = ""
    phone: str = ""
    location: str = ""
    title: str = "" # e.g., Senior Frontend Developer

class Education(BaseModel):
    school: str = ""
    degree: str = ""
    major: str = ""
    start_date: str = ""
    end_date: str = ""
    gpa: Optional[float] = None

class Experience(BaseModel):
    company: str = ""
    position: str = ""
    location: str = ""
    start_date: str = ""
    end_date: str = ""
    description: List[str] = [] # Bullet points

class Project(BaseModel):
    name: str = ""
    description: List[str] = [] # Bullet points
    technologies: List[str] = []
    link: Optional[str] = None

class Certification(BaseModel):
    name: str = ""
    organization: str = ""
    issue_date: str = ""
    expiry_date: Optional[str] = None

class ATSOptimizationResult(BaseModel):
    score: float = 0.0
    suggestions: List[str] = []
    missing_keywords: List[str] = []
    improved_cv: Optional['CVData'] = None

class CVOptimizationResponse(BaseModel):
    cv_id: str
    optimized_cv: 'CVData'
    ats_result: ATSOptimizationResult

class CVData(BaseModel):
    personal_info: PersonalInfo = Field(default_factory=PersonalInfo)
    summary: str = ""
    education: List[Education] = Field(default_factory=list)
    experience: List[Experience] = Field(default_factory=list)
    skills: List[str] = Field(default_factory=list)
    projects: List[Project] = Field(default_factory=list)
    certifications: List[Certification] = Field(default_factory=list)
    section_order: List[str] = Field(default_factory=lambda: ["personal_info", "summary", "experience", "education", "skills", "projects", "certifications"])
