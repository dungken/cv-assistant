from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from shared.models.base_models import Entity

class ExtractionRequest(BaseModel):
    text: str
    cv_id: Optional[str] = None

class ExtractionResponse(BaseModel):
    entities: List[Entity]
    status: str

class BatchExtractionRequest(BaseModel):
    texts: List[str]

class BatchExtractionResponse(BaseModel):
    results: List[List[Entity]]
    status: str

class NormalizedEntity(BaseModel):
    raw: str
    canonical: str
    type: str
    category: Optional[str] = None
    confidence: float

class NormalizationStats(BaseModel):
    total_items: int
    normalized: int
    needs_review: int
    failed: int
    language_info: Dict[str, Any]

class NormalizationResponse(BaseModel):
    normalized_entities: Dict[str, List[NormalizedEntity]]
    stats: NormalizationStats
    status: str


# --- JD (Job Description) Schemas ---

class JDTextRequest(BaseModel):
    text: str
    title: Optional[str] = ""
    company: Optional[str] = ""

class JDUrlRequest(BaseModel):
    url: str

class JDExtractedSkills(BaseModel):
    required: List[str] = []
    preferred: List[str] = []

class JDSections(BaseModel):
    requirements: List[str] = []
    responsibilities: List[str] = []
    benefits: List[str] = []
    about: List[str] = []
    preferred: List[str] = []

class JDMetadata(BaseModel):
    language: str = "en"
    parse_time_ms: int = 0
    input_method: str = "text"
    source_url: Optional[str] = None

class JDRequirementExtract(BaseModel):
    title: str = ""
    company: str = ""
    min_exp: Optional[int] = 0
    max_exp: Optional[int] = None
    seniority: str = "unspecified"
    skills_required: List[str] = []
    skills_preferred: List[str] = []
    degree_required: Optional[str] = None
    certifications: List[str] = []

class JDParseResponse(BaseModel):
    jd_id: str
    title: str = ""
    company: str = ""
    location: str = ""
    level: str = "unspecified"
    experience_years: str = ""
    min_exp: Optional[int] = 0
    max_exp: Optional[int] = None
    sections: JDSections
    extracted_skills: JDExtractedSkills
    entities: Optional[List[Entity]] = [] # For raw NER results
    analysis: Optional[JDRequirementExtract] = None
    raw_text: str = ""
    metadata: JDMetadata
    status: str = "success"
