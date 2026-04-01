from pydantic import BaseModel
from typing import List, Optional, Dict
from shared.models.base_models import Source

class ChatRequest(BaseModel):
    message: str
    session_id: str = "default"
    include_sources: bool = True

class ChatResponse(BaseModel):
    response: str
    sources: List[Source]
    session_id: str
    timestamp: str

class SessionHistory(BaseModel):
    session_id: str
    messages: List[Dict]
    count: int
