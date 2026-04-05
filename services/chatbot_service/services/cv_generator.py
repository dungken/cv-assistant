import logging
import json
import re
from typing import List, Dict, Any, Tuple, Optional
from shared.models.cv_models import CVData, Experience, Project, ATSOptimizationResult

logger = logging.getLogger(__name__)

class CVGeneratorService:
    """Service for AI-powered CV generation and optimization."""

    REWRITE_PROMPT = """You are a Professional CV Expert. Your task is to rewrite the describing points of a job experience or project into a professional, high-impact format (STAR/Action-Verb).

    GUIDELINES:
    1. USE STAR FORMAT: Situation, Task, Action, Result. Focus on results and quantifiable metrics.
    2. START WITH ACTION VERBS: Developed, Spearheaded, Orchestrated, Optimized, etc.
    3. KEEP IT CONCISE: Each point should be a single, impactful sentence.
    4. LANGUAGE: Maintain the original language (Vietnamese or English).
    5. QUANTIFY: Use numbers/percentages if provided or imply them based on context.

    INPUT DATA:
    - Position/Project: {title}
    - Company/Environment: {context}
    - Raw Points: {raw_points}

    OUTPUT:
    Return exactly a JSON list of strings (bullet points). No conversational text.
    Format: ["Point 1", "Point 2", ...]
    """

    ATS_PROMPT = """You are an ATS (Applicant Tracking System) Specialist. Analyze the following CV data against the target Job Description (JD).

    TASK:
    1. Calculate a MATCH SCORE (0-100).
    2. Identify MISSING KEYWORDS (Skills, Tools, Methodologies).
    3. Provide SPECIFIC IMPROVEMENT SUGGESTIONS.

    INPUT:
    - CV: {cv_json}
    - Target JD: {jd_text}

    OUTPUT:
    Return exactly a JSON object with this structure:
    {{
        "score": 85,
        "missing_keywords": ["Kubernetes", "gRPC"],
        "suggestions": ["Add more details about CI/CD pipeline", "Quantify React achievements"]
    }}
    """

    def __init__(self, llm_handler_fn):
        """
        Args:
            llm_handler_fn: A function that takes (messages, system_prompt) and returns LLM string.
        """
        self.llm_handler = llm_handler_fn

    def rewrite_bullet_points(self, title: str, context: str, raw_points: List[str]) -> List[str]:
        """Rewrite raw bullet points into STAR format."""
        if not raw_points:
            return []

        system_prompt = self.REWRITE_PROMPT.format(
            title=title,
            context=context,
            raw_points="\n".join([f"- {p}" for p in raw_points])
        )
        
        try:
            response = self.llm_handler([{"role": "user", "content": "Rewrite these bullet points professionally."}], system_prompt)
            # Extract JSON list
            match = re.search(r'\[.*\]', response, re.DOTALL)
            if match:
                return json.loads(match.group(0))
            return raw_points # Fallback
        except Exception as e:
            logger.error(f"Error in rewrite_bullet_points: {e}")
            return raw_points

    def optimize_ats(self, cv_data: CVData, jd_text: str) -> ATSOptimizationResult:
        """Analyze CV against JD and return optimization metrics."""
        if not jd_text:
            return ATSOptimizationResult(score=0, suggestions=["Please provide a target JD for optimization."])

        cv_json = cv_data.json()
        system_prompt = self.ATS_PROMPT.format(
            cv_json=cv_json,
            jd_text=jd_text
        )

        try:
            response = self.llm_handler([{"role": "user", "content": "Analyze my ATS score."}], system_prompt)
            match = re.search(r'\{.*\}', response, re.DOTALL)
            if match:
                data = json.loads(match.group(0))
                return ATSOptimizationResult(
                    score=data.get("score", 0),
                    missing_keywords=data.get("missing_keywords", []),
                    suggestions=data.get("suggestions", [])
                )
            return ATSOptimizationResult(score=0, suggestions=["Failed to analyze ATS score."])
        except Exception as e:
            logger.error(f"Error in optimize_ats: {e}")
            return ATSOptimizationResult(score=0, suggestions=[f"Internal error: {str(e)}"])

    def suggest_section_order(self, cv_data: CVData) -> List[str]:
        """Determine optimal section order based on experience density."""
        default_order = ["personal_info", "experience", "education", "skills", "projects", "certifications"]
        
        # Rule 1: If user has < 1 years experience or no experience items, put education first
        exp_count = len(cv_data.experience)
        if exp_count == 0:
            return ["personal_info", "education", "skills", "projects", "certifications"]
        
        # Rule 2: If fresh grad (determined by latest education end_date vs current date, simplified logic here)
        # For now, keep it simple.
        return default_order
