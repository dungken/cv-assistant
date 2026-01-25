"""
Shared Pydantic Models - CV Assistant
"""
from pydantic import BaseModel
from typing import List, Optional, Any
from datetime import datetime


class Entity(BaseModel):
    """NER Entity model."""
    text: str
    type: str  # PER, ORG, DATE, LOC, SKILL, DEGREE, MAJOR, JOB_TITLE, PROJECT, CERT
    start: int
    end: int
    confidence: float


class Source(BaseModel):
    """RAG Source model."""
    title: str
    type: str  # "job", "guide", "cv"
    relevance: float


class SuccessResponse(BaseModel):
    """Standard success wrapper."""
    success: bool = True
    data: Any
    message: Optional[str] = None


class ErrorResponse(BaseModel):
    """Standard error wrapper."""
    success: bool = False
    error: str
    code: int
