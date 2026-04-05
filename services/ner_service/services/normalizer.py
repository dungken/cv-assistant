import json
import re
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path
from langdetect import detect, detect_langs, DetectorFactory
from dateparser import parse as parse_date
from services.ner_service.models.schemas import Entity, NormalizedEntity, NormalizationStats

# Ensure consistent results for langdetect
DetectorFactory.seed = 0

logger = logging.getLogger(__name__)

class DataNormalizer:
    """
    Multilingual data normalization for CV entities (Skills, Dates, Organizations).
    Focuses on English-centric output.
    """

    def __init__(self):
        self.resources_path = Path(__file__).parent.parent / "resources"
        self.skill_map = self._load_map("skill_map.json")
        self.uni_map = self._load_map("uni_map.json")
        
        # Skill categories (Extended taxonomy)
        self.skill_categories = {
            "JavaScript": "Programming Language",
            "TypeScript": "Programming Language",
            "Python": "Programming Language",
            "Java": "Programming Language",
            "C++": "Programming Language",
            "React": "Frontend Framework",
            "Vue.js": "Frontend Framework",
            "Node.js": "Backend Runtime",
            "Docker": "DevOps Tool",
            "Kubernetes": "DevOps Tool",
            "Machine Learning": "AI/ML",
            "Deep Learning": "AI/ML",
            "Natural Language Processing": "AI/ML"
        }

    def _load_map(self, filename: str) -> Dict[str, str]:
        path = self.resources_path / filename
        if path.exists():
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        logger.warning(f"Map file {filename} not found at {path}")
        return {}

    def detect_language(self, text: str) -> Dict[str, Any]:
        """Detect primary language and mixed status."""
        if not text or len(text.strip()) < 10:
            return {"primary": "unknown", "confidence": 0.0, "is_mixed": False}
        
        try:
            # Check for Vietnamese characters first (very reliable for VN)
            vi_chars = r'[àáảãạăằắẳẵặâầấẩẫậèéẻẽẹêềếểễệìíỉĩịòóỏõọôồốổỗộơờớởỡợùúủũụưừứửữợỳýỷỹỵđ]'
            has_vi = bool(re.search(vi_chars, text, re.IGNORECASE))
            
            langs = detect_langs(text)
            primary = langs[0].lang
            confidence = langs[0].prob
            
            # Check for mixed content: multiple languages detected OR 
            # Vietnamese characters in an English-detected string OR
            # Common English technical terms in a Vietnamese-detected string
            tech_terms = r'\b(software|engineer|developer|data|server|cloud|framework|library)\b'
            has_tech_terms = bool(re.search(tech_terms, text, re.IGNORECASE))
            
            is_mixed = len(langs) > 1 or (has_vi and primary == 'en') or (primary == 'vi' and has_tech_terms)
            
            if has_vi and primary != 'vi' and confidence < 0.9:
                primary = 'vi' # Override if VN chars present and EN confidence not high
                
            return {
                "primary": primary,
                "confidence": confidence,
                "is_mixed": is_mixed,
                "has_vietnamese": has_vi
            }
        except Exception as e:
            logger.error(f"Language detection failed: {e}")
            return {"primary": "en", "confidence": 1.0, "is_mixed": False}

    def normalize_skill(self, raw_skill: str) -> NormalizedEntity:
        """Map skill to canonical name and category."""
        clean_skill = raw_skill.strip().lower()
        
        # 1. Direct map lookup
        canonical = self.skill_map.get(clean_skill, raw_skill.strip())
        
        # 2. Heuristic for variations (.js, js, etc)
        if canonical == raw_skill.strip():
            if clean_skill.endswith("js"):
                potential_base = clean_skill[:-2].strip()
                if potential_base in self.skill_map:
                    canonical = self.skill_map[potential_base]
            elif clean_skill.endswith(".js"):
                potential_base = clean_skill[:-3].strip()
                if potential_base in self.skill_map:
                    canonical = self.skill_map[potential_base]

        category = self.skill_categories.get(canonical, "Technical Skill")
        
        return NormalizedEntity(
            raw=raw_skill,
            canonical=canonical,
            type="SKILL",
            category=category,
            confidence=1.0 if canonical != raw_skill else 0.8
        )

    def normalize_date(self, raw_date: str) -> NormalizedEntity:
        """Standardize date to YYYY-MM or 'present'."""
        clean_date = raw_date.strip().lower()
        
        # Handle "present" / "hiện tại"
        if any(p in clean_date for p in ["present", "hiện tại", "now", "đến nay"]):
            return NormalizedEntity(
                raw=raw_date,
                canonical="present",
                type="DATE",
                confidence=1.0
            )

        # Use dateparser for flexible parsing
        # Try both EN and VI locales
        dt = parse_date(clean_date, languages=['en', 'vi'])
        
        if dt:
            canonical = dt.strftime("%Y-%m")
            return NormalizedEntity(
                raw=raw_date,
                canonical=canonical,
                type="DATE",
                confidence=0.95
            )
        
        # Fallback: Regex for YYYY
        year_match = re.search(r"\d{4}", clean_date)
        if year_match:
            return NormalizedEntity(
                raw=raw_date,
                canonical=year_match.group(0),
                type="DATE",
                confidence=0.7
            )

        return NormalizedEntity(
            raw=raw_date,
            canonical=raw_date,
            type="DATE",
            confidence=0.0
        )

    def normalize_org(self, raw_org: str) -> NormalizedEntity:
        """Expand organization abbreviations (mostly VN Unis)."""
        clean_org = raw_org.strip()
        
        # 1. Direct map lookup
        canonical = self.uni_map.get(clean_org, clean_org)
        
        # 2. Case-insensitive lookup if failed
        if canonical == clean_org:
            clean_org_lower = clean_org.lower()
            for k, v in self.uni_map.items():
                if k.lower() == clean_org_lower:
                    canonical = v
                    break
        
        return NormalizedEntity(
            raw=raw_org,
            canonical=canonical,
            type="ORG",
            confidence=1.0 if canonical != raw_org else 0.6
        )

    def normalize_entities(self, entities: List[Entity], text_context: str = "") -> Dict[str, Any]:
        """Orchestrate normalization for a list of entities."""
        lang_info = self.detect_language(text_context)
        normalized_results = {
            "SKILL": [],
            "DATE": [],
            "ORG": [],
            "OTHERS": []
        }
        
        stats = {
            "total_items": len(entities),
            "normalized": 0,
            "needs_review": 0,
            "failed": 0
        }

        for ent in entities:
            norm_ent = None
            if ent.type == "SKILL":
                norm_ent = self.normalize_skill(ent.text)
                normalized_results["SKILL"].append(norm_ent)
            elif ent.type == "DATE":
                norm_ent = self.normalize_date(ent.text)
                normalized_results["DATE"].append(norm_ent)
            elif ent.type == "ORG":
                norm_ent = self.normalize_org(ent.text)
                normalized_results["ORG"].append(norm_ent)
            else:
                # Pass through others
                norm_ent = NormalizedEntity(
                    raw=ent.text,
                    canonical=ent.text,
                    type=ent.type,
                    confidence=ent.confidence
                )
                normalized_results["OTHERS"].append(norm_ent)
            
            # Update stats
            if norm_ent and norm_ent.canonical != norm_ent.raw:
                stats["normalized"] += 1
            elif norm_ent and norm_ent.confidence < 0.5:
                stats["failed"] += 1
            else:
                stats["needs_review"] += 1

        return {
            "normalized_entities": normalized_results,
            "stats": {**stats, "language_info": lang_info},
            "status": "success"
        }
