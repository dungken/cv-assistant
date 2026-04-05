import logging
import json
import re
from typing import List, Dict, Any, Optional
from shared.models.cv_models import CVData
from services.chatbot_service.models.schemas import OptimizationSuggestion, OptimizationResponse

logger = logging.getLogger(__name__)

class OptimizationService:
    """Service for generating explainable CV optimization suggestions using LLM."""

    OPTIMIZATION_PROMPT = """You are a Senior Technical Recruiter and Career Coach. 
    Analyze the following CV data and its ATS (Applicant Tracking System) score breakdown.
    
    TASK:
    Generate 3-5 HIGH-IMPACT suggestions to improve the CV's performance for the target role.
    
    INPUT:
    - CV: {cv_json}
    - ATS Score Breakdown: {ats_json}
    - JD (if provided): {jd_text}
    
    GUIDELINES:
    1. EXPLAIN WHY: Connect each suggestion to recruiter psychology or ATS technical behavior.
    2. EXPLAIN HOW: Provide step-by-step instructions.
    3. PROVIDE EVIDENCE: Use industry data or JD-specific references.
    4. PROVIDE PREVIEW: If the suggestion is about adding content (like a summary), provide a high-quality draft.
    5. CATEGORIZE: Content, Keywords, Format, or Structure.
    6. PRIORITY: critical (red line issue), important (significant boost), nice_to_have (polishing).
    
    OUTPUT:
    Return exactly a JSON list of objects matching this structure:
    [
      {{
        "id": "sug-001",
        "category": "Content",
        "priority": "critical",
        "title": "...",
        "description": "...",
        "why": "...",
        "how": "...",
        "evidence": "...",
        "confidence": 0.95,
        "preview": "..."
      }}
    ]
    No conversational text.
    """

    def __init__(self, llm_handler_fn):
        self.llm_handler = llm_handler_fn

    def get_suggestions(self, cv_data: CVData, ats_result: Dict, jd_text: Optional[str] = None) -> List[OptimizationSuggestion]:
        """Generate explainable suggestions based on CV and ATS analysis."""
        
        system_prompt = self.OPTIMIZATION_PROMPT.format(
            cv_json=cv_data.json(),
            ats_json=json.dumps(ats_result),
            jd_text=jd_text or "No JD provided."
        )

        try:
            # Short-circuit if CV is empty
            if not cv_data.experience and not cv_data.skills:
                return []

            response = self.llm_handler([{"role": "user", "content": "Generate 3-5 professional optimization suggestions."}], system_prompt)
            
            # Extract JSON list from response
            match = re.search(r'\[.*\]', response, re.DOTALL)
            if match:
                raw_suggestions = json.loads(match.group(0))
                suggestions = []
                for s in raw_suggestions:
                    try:
                        suggestions.append(OptimizationSuggestion(**s))
                    except Exception as e:
                        logger.warning(f"Failed to parse suggestion item: {e}")
                return suggestions
            
            return []
        except Exception as e:
            logger.error(f"Error in OptimizationService.get_suggestions: {e}")
            return []
