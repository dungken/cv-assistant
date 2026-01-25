from pydantic import BaseModel
from typing import List, Optional
from shared.models.base_models import Entity

class ExtractionRequest(BaseModel):
    text: str
    cv_id: Optional[str] = None

class ExtractionResponse(BaseModel):
    entities: List[Entity]
    status: str
