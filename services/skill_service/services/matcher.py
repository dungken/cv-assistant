import logging
from typing import List, Dict, Optional, Tuple
import numpy as np
from sentence_transformers import SentenceTransformer
import chromadb
from services.skill_service.models.schemas import (
    SemanticMatch, OntologyMatch, MatchedSkill, MissingSkill, 
    ExtraSkill, ExperienceMatch, EducationMatch
)
from services.skill_service.services.ontology import SkillOntology

logger = logging.getLogger(__name__)

# Singleton ontology instance
_ontology: Optional[SkillOntology] = None

def get_ontology() -> SkillOntology:
    global _ontology
    if _ontology is None:
        _ontology = SkillOntology()
    return _ontology


class SkillMatcher:
    """Ontology-enhanced skill matching with context-aware understanding."""

    def __init__(self, model: SentenceTransformer, collection: chromadb.Collection,
                 onet_collection: chromadb.Collection = None, ner_url: str = None):
        self.model = model
        self.collection = collection
        self.onet_collection = onet_collection
        self.ner_url = ner_url
        self.ontology = get_ontology()

    def extract_skills_from_jd(self, jd_text: str) -> List[str]:
        """Extract skills from JD text. Prefers NER, falls back to O*NET semantic search."""
        extracted = set()

        # 1. Try NER Service
        if self.ner_url:
            try:
                import requests
                logger.info(f"Calling NER service for JD extraction: {self.ner_url}")
                resp = requests.post(self.ner_url, json={"text": jd_text}, timeout=5)
                if resp.status_code == 200:
                    data = resp.json()
                    for ent in data.get("entities", []):
                        if ent.get("type") == "SKILL":
                            extracted.add(ent.get("text"))
                    if extracted:
                        logger.info(f"NER service extracted {len(extracted)} skills.")
                        return list(extracted)
            except Exception as e:
                logger.warning(f"NER service call failed: {e}. Falling back to O*NET search.")

        # 2. Fallback to O*NET Semantic Search
        if not self.onet_collection:
            return ["Python", "JavaScript", "SQL"]

        segments = [s.strip() for s in jd_text.replace("\n", ". ").split(".") if len(s.strip()) > 5]
        for segment in segments:
            results = self.onet_collection.query(
                query_texts=[segment],
                n_results=5
            )
            if results['distances'] and results['distances'][0]:
                for i, distance in enumerate(results['distances'][0]):
                    if distance < 0.45:
                        extracted.add(results['documents'][0][i])

        return list(extracted)

    def match(self, cv_skills: List[str], jd_skills: List[str]) -> Dict:
        """
        Ontology-enhanced matching with 3 tiers:
        1. Exact match (score: 1.0)
        2. Ontology match - same subcategory (score: 0.85)
        3. Semantic match - vector similarity (score: 0.65-0.85)
        """
        cv_skills_lower = [s.lower() for s in cv_skills]
        jd_skills_lower = [s.lower() for s in jd_skills]

        # Track which JD skills are matched
        matched_jd = set()

        # --- Tier 1: Exact matches ---
        exact_matches = list(set(cv_skills_lower) & set(jd_skills_lower))
        matched_jd.update(exact_matches)

        # --- Tier 2: Ontology matches (same subcategory = substitutable) ---
        ontology_matches = []
        remaining_jd = [s for s in jd_skills_lower if s not in matched_jd]

        for jd_skill in remaining_jd:
            ont_distance_best = 1.0
            best_cv_skill = None

            for cv_skill in cv_skills_lower:
                distance = self.ontology.skill_distance(cv_skill, jd_skill)
                if distance < ont_distance_best:
                    ont_distance_best = distance
                    best_cv_skill = cv_skill

            if ont_distance_best <= 0.2 and best_cv_skill:
                explanation = self.ontology.explain_relationship(best_cv_skill, jd_skill)
                ontology_matches.append(OntologyMatch(
                    cv_skill=best_cv_skill,
                    jd_skill=jd_skill,
                    distance=round(ont_distance_best, 2),
                    relationship=explanation,
                    category=self.ontology.get_category(jd_skill) or "Unknown",
                ))
                matched_jd.add(jd_skill)

        # --- Tier 3: Semantic matches (embedding similarity) ---
        semantic_matches = []
        unmatched_jd = [s for s in jd_skills_lower if s not in matched_jd]

        if unmatched_jd and cv_skills_lower:
            jd_embeddings = self.model.encode(unmatched_jd)
            cv_embeddings = self.model.encode(cv_skills_lower)

            for i, jd_skill in enumerate(unmatched_jd):
                jd_emb = jd_embeddings[i]
                similarities = (cv_embeddings @ jd_emb) / (
                    np.linalg.norm(cv_embeddings, axis=1) * np.linalg.norm(jd_emb) + 1e-9
                )

                best_idx = np.argmax(similarities)
                best_similarity = similarities[best_idx]

                if best_similarity > 0.65:
                    semantic_matches.append(SemanticMatch(
                        cv_skill=cv_skills_lower[best_idx],
                        jd_skill=jd_skill,
                        similarity=round(float(best_similarity), 2)
                    ))
                    matched_jd.add(jd_skill)

        # --- Score calculation (weighted by match tier) ---
        total_jd = max(1, len(jd_skills))
        weighted_matches = (
            len(exact_matches) * 1.0 +
            len(ontology_matches) * 0.85 +
            len(semantic_matches) * 0.7
        )
        score = min(100, round((weighted_matches / total_jd) * 100, 1))

        # --- Identify missing skills (gap) ---
        missing_skills = [s for s in jd_skills_lower if s not in matched_jd]

        return {
            "exact_matches": exact_matches,
            "ontology_matches": ontology_matches,
            "semantic_matches": semantic_matches,
            "missing_skills": missing_skills,
            "overall_score": score,
        }

    def match_comprehensive(self, 
                          cv_skills: List[str], 
                          jd_required: List[str], 
                          jd_preferred: List[str],
                          cv_exp: float = 0,
                          jd_min_exp: float = 0,
                          jd_max_exp: Optional[float] = None,
                          cv_edu: Optional[str] = None,
                          jd_edu: Optional[str] = None) -> Dict:
        """
        Deep matching for US-11.
        Weighted score: Skills (60%), Experience (30%), Education (10%).
        """
        # 1. Match Required Skills
        req_res = self.match(cv_skills, jd_required)
        
        # 2. Match Preferred Skills
        pref_res = self.match(cv_skills, jd_preferred)
        
        # Calculate skill score (Required weight 1.0, Preferred weight 0.5)
        total_req = len(jd_required)
        total_pref = len(jd_preferred)
        
        req_match_val = (len(req_res["exact_matches"]) * 1.0 + 
                        len(req_res["ontology_matches"]) * 0.85 + 
                        len(req_res["semantic_matches"]) * 0.7)
        
        pref_match_val = (len(pref_res["exact_matches"]) * 1.0 + 
                         len(pref_res["ontology_matches"]) * 0.85 + 
                         len(pref_res["semantic_matches"]) * 0.7)
        
        skill_score = 0
        if total_req > 0 or total_pref > 0:
            skill_score = (req_match_val + 0.5 * pref_match_val) / (total_req + 0.5 * total_pref) * 100
        skill_score = min(100, round(skill_score, 1))

        # Identify Matched, Missing, Extra
        matched = []
        for s in req_res["exact_matches"]: matched.append(MatchedSkill(skill=s, match_type="exact", cv_mention=s, jd_requirement="required"))
        for m in req_res["ontology_matches"]: matched.append(MatchedSkill(skill=m.jd_skill, match_type="ontology", cv_mention=m.cv_skill, jd_requirement="required"))
        for m in req_res["semantic_matches"]: matched.append(MatchedSkill(skill=m.jd_skill, match_type="semantic", cv_mention=m.cv_skill, jd_requirement="required"))
        
        for s in pref_res["exact_matches"]: matched.append(MatchedSkill(skill=s, match_type="exact", cv_mention=s, jd_requirement="preferred"))
        for m in pref_res["ontology_matches"]: matched.append(MatchedSkill(skill=m.jd_skill, match_type="ontology", cv_mention=m.cv_skill, jd_requirement="preferred"))
        for m in pref_res["semantic_matches"]: matched.append(MatchedSkill(skill=m.jd_skill, match_type="semantic", cv_mention=m.cv_skill, jd_requirement="preferred"))

        missing = []
        for s in req_res["missing_skills"]: missing.append(MissingSkill(skill=s, jd_requirement="required", priority="high", suggestion=f"Key requirement for this role."))
        for s in pref_res["missing_skills"]: missing.append(MissingSkill(skill=s, jd_requirement="preferred", priority="medium", suggestion=f"Would be a strong plus."))

        # Identify Extra Skills (CV skills not in matched)
        matched_cv_skills = {m.cv_mention.lower() for m in matched}
        extra = []
        for s in cv_skills:
            if s.lower() not in matched_cv_skills:
                # Highlight if it's high demand in ontology
                cat = self.ontology.get_category(s)
                extra.append(ExtraSkill(skill=s, relevance="high" if cat else "medium", suggestion=f"Relevant skill in {cat or 'General Engineering'}."))

        # 3. Match Experience
        exp_match = self.match_experience(cv_exp, jd_min_exp, jd_max_exp)
        
        # 4. Match Education
        edu_match = self.match_education(cv_edu, jd_edu)
        
        # Overall Score
        overall_score = round(skill_score * 0.6 + exp_match.score * 0.3 + edu_match.score * 0.1, 1)

        return {
            "overall_score": overall_score,
            "breakdown": {
                "skills": skill_score,
                "experience": exp_match.score,
                "education": edu_match.score
            },
            "skills": {
                "matched": matched,
                "missing": missing,
                "extra": extra
            },
            "experience": exp_match,
            "education": edu_match
        }

    def match_experience(self, current: float, required_min: float, required_max: Optional[float] = None) -> ExperienceMatch:
        status = "match"
        score = 100
        
        if current < required_min:
            gap = required_min - current
            if gap <= 1:
                status = "partial"
                score = 70
            else:
                status = "gap"
                score = max(0, 50 - (gap * 10))
        elif required_max and current > required_max + 5:
            status = "overqualified"
            score = 90
            
        return ExperienceMatch(
            current=current,
            required_min=required_min,
            required_max=required_max,
            status=status,
            score=score
        )

    def match_education(self, current: Optional[str], required: Optional[str]) -> EducationMatch:
        if not required or required.lower() == "none" or required.lower() == "n/a":
            return EducationMatch(current=current, required=required, status="match", score=100)
            
        edu_levels = {"none": 0, "bachelor": 1, "master": 2, "phd": 3}
        current_lvl = edu_levels.get((current or "none").lower(), 0)
        req_lvl = edu_levels.get((required or "none").lower(), 1)
        
        if current_lvl >= req_lvl:
            return EducationMatch(current=current, required=required, status="match", score=100)
        elif current_lvl > 0:
            return EducationMatch(current=current, required=required, status="partial", score=60)
        else:
            return EducationMatch(current=current, required=required, status="gap", score=20)

    def get_recommendations(self, cv_skills: List[str]) -> List[str]:
        """Get relevant jobs based on cv skills."""
        if not self.collection:
            return []

        results = self.collection.query(
            query_texts=[", ".join(cv_skills)],
            n_results=3
        )

        if results['metadatas'] and results['metadatas'][0]:
            return [m.get('title', 'Unknown') for m in results['metadatas'][0]]
        return []
