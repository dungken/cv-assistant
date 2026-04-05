import json
import logging
import requests
import re
from typing import Dict, Any, List, Optional
from services.ner_service.config import settings

logger = logging.getLogger(__name__)

class JDRefiner:
    """Uses a local LLM (via Ollama) to refine BERT extraction results with semantic understanding."""

    def __init__(self):
        self.url = settings.ollama_url
        self.enabled = settings.enable_llm_refinement

    def refine(self, raw_text: str, curr_data: Dict[str, Any]) -> Dict[str, Any]:
        """Refines JD extraction data using LLM reasoning."""
        if not self.enabled:
            return curr_data

        prompt = self._build_prompt(raw_text, curr_data)
        
        try:
            response = requests.post(
                self.url,
                json={
                    "model": "llama3.2:1b",
                    "prompt": prompt,
                    "stream": False,
                    "format": "json"
                },
                timeout=15
            )
            
            if response.status_code == 200:
                result = response.json()
                refined_json = json.loads(result.get("response", "{}"))
                return self._merge_results(curr_data, refined_json)
            else:
                logger.warning(f"Ollama refiner failed with status {response.status_code}")
        except Exception as e:
            logger.error(f"Error during LLM refinement: {e}")
        
        return curr_data

    def _build_prompt(self, text: str, data: Dict[str, Any]) -> str:
        """Constructs a precise prompt for Llama-3.2:1b."""
        return f"""You are an expert HR data extractor. Given a Job Description and preliminary extraction, refine and correct the data. Output ONLY valid JSON.

RULES:
1. refined_title: The exact job position (e.g. "Senior Angular Developer"). NOT company name, NOT department.
2. refined_company: The hiring company name. Remove artifacts like "logo", "image", "banner". Keep the actual company name only.
3. skills_required: Technical skills explicitly REQUIRED in the JD (in "Requirements" / "Must have" sections).
   - Each skill should be a single technology name: "React", "TypeScript", "Docker", etc.
   - Normalize names: "react js" → "React", "node" → "Node.js", ".net" → ".NET", "C #" → "C#", "Rxjs" → "RxJS".
   - Do NOT include soft skills (communication, teamwork) or benefits (MacBook, salary).
   - Do NOT include vague terms (system, architecture, code, implementation).
4. skills_preferred: Technical skills listed as "nice to have", "bonus", "preferred", "a plus".
5. seniority: One of: "intern", "junior", "mid", "senior", "lead".
6. min_exp / max_exp: Integer years. Use null if not mentioned.
7. location: City/country of work location. Empty string if not mentioned.

IMPORTANT: Keep all skills from the preliminary data that are valid technical skills. Only remove obvious errors. Add any skills you find in the JD text that were missed.

JD TEXT:
\"\"\"{text[:3000]}\"\"\"

PRELIMINARY DATA:
{json.dumps(data, indent=2, ensure_ascii=False)}

OUTPUT (valid JSON only, no explanation):
{{
  "refined_title": "string",
  "refined_company": "string",
  "seniority": "string",
  "min_exp": number_or_null,
  "max_exp": number_or_null,
  "skills_required": ["string"],
  "skills_preferred": ["string"],
  "location": "string"
}}"""

    def _merge_results(self, original: Dict[str, Any], refined: Dict[str, Any]) -> Dict[str, Any]:
        """Safely merges LLM refinements into the original data structure.

        Strategy: BERT results are authoritative. LLM only:
        1. Fixes title/company naming artifacts (its strength).
        2. Adds skills that BERT missed (supplement, not replace).
        3. Does NOT override seniority/experience — BERT + heuristics are more reliable
           than a 1B-param model for these structured fields.
        """
        out = original.copy()

        # LLM is good at cleaning title/company artifacts
        if refined.get("refined_title") and len(refined["refined_title"].strip()) > 2:
            out["title"] = refined["refined_title"].strip()
        if refined.get("refined_company") and len(refined["refined_company"].strip()) > 1:
            out["company"] = refined["refined_company"].strip()

        # Seniority & Experience: NEVER override BERT — heuristic extraction
        # is more reliable than a 1B model for structured fields.
        # Only fill in if BERT found absolutely nothing.
        bert_min = original.get("min_exp", 0)
        if bert_min == 0:
            if "min_exp" in refined and isinstance(refined["min_exp"], (int, float)) and refined["min_exp"] > 0:
                out["min_exp"] = int(refined["min_exp"])
            if refined.get("seniority") and refined["seniority"].lower() in ("intern", "junior", "mid", "senior", "lead"):
                out["seniority"] = refined["seniority"].lower()
        if original.get("max_exp") is None and "max_exp" in refined:
            val = refined["max_exp"]
            out["max_exp"] = int(val) if isinstance(val, (int, float)) and val > 0 else None

        # Location: accept LLM if BERT had nothing
        if not original.get("location") and refined.get("location") and len(refined["location"].strip()) > 1:
            out["location"] = refined["location"].strip()

        # Skills: ADDITIVE ONLY — LLM can add NEW skills BERT missed,
        # but CANNOT move skills between required/preferred lists.
        # Also, LLM-added skills MUST actually appear in the JD text (anti-hallucination).
        bert_req = set(original.get("skills_required", []))
        bert_pref = set(original.get("skills_preferred", []))
        all_bert_skills_lower = {s.lower() for s in bert_req | bert_pref}
        raw_text_lower = raw_text.lower()

        if refined.get("skills_required"):
            for s in refined["skills_required"]:
                if isinstance(s, str) and len(s) > 2 and s.lower() not in all_bert_skills_lower:
                    # Anti-hallucination: skill must appear in the JD text
                    if re.search(r'\b' + re.escape(s.lower()) + r'\b', raw_text_lower):
                        bert_req.add(s)
                        all_bert_skills_lower.add(s.lower())
            out["skills_required"] = sorted(bert_req)

        if refined.get("skills_preferred"):
            for s in refined["skills_preferred"]:
                if isinstance(s, str) and len(s) > 2 and s.lower() not in all_bert_skills_lower:
                    if re.search(r'\b' + re.escape(s.lower()) + r'\b', raw_text_lower):
                        bert_pref.add(s)
                        all_bert_skills_lower.add(s.lower())
            out["skills_preferred"] = sorted(bert_pref)

        return out
