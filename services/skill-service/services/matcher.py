import logging
from typing import List, Dict
import numpy as np
from sentence_transformers import SentenceTransformer
import chromadb
from services.skill_service.models.schemas import SemanticMatch

logger = logging.getLogger(__name__)

class SkillMatcher:
    """Core logic for skill matching and JD extraction."""
    
    def __init__(self, model: SentenceTransformer, collection: chromadb.Collection):
        self.model = model
        self.collection = collection
        # Common tech skill keywords for extraction
        self.skill_keywords = [
            "python", "java", "javascript", "react", "node", "sql", "aws", "docker",
            "kubernetes", "machine learning", "deep learning", "tensorflow", "pytorch",
            "agile", "scrum", "git", "ci/cd", "rest api", "graphql", "mongodb",
            "postgresql", "redis", "linux", "communication", "leadership"
        ]

    def extract_skills_from_jd(self, jd_text: str) -> List[str]:
        """Simple keyword-based extraction."""
        jd_lower = jd_text.lower()
        return [skill for skill in self.skill_keywords if skill in jd_lower]

    def match(self, cv_skills: List[str], jd_skills: List[str]) -> Dict:
        """Calculate matches between CV and JD skills."""
        cv_skills_lower = [s.lower() for s in cv_skills]
        jd_skills_lower = [s.lower() for s in jd_skills]
        
        # Exact matches
        exact_matches = list(set(cv_skills_lower) & set(jd_skills_lower))
        
        # Semantic matches
        semantic_matches = []
        unmatched_jd = [s for s in jd_skills_lower if s not in exact_matches]
        
        for jd_skill in unmatched_jd:
            jd_embedding = self.model.encode(jd_skill)
            best_match = None
            best_similarity = 0.0
            
            for cv_skill in cv_skills_lower:
                if cv_skill not in exact_matches:
                    cv_embedding = self.model.encode(cv_skill)
                    # Cosine similarity
                    similarity = float(
                        (jd_embedding @ cv_embedding) / 
                        (max(0.0001, (jd_embedding @ jd_embedding) ** 0.5 * (cv_embedding @ cv_embedding) ** 0.5))
                    )
                    if similarity > best_similarity and similarity > 0.5:
                        best_similarity = similarity
                        best_match = cv_skill
            
            if best_match:
                semantic_matches.append(SemanticMatch(
                    cv_skill=best_match,
                    jd_skill=jd_skill,
                    similarity=round(best_similarity, 2)
                ))
        
        # Score calculation
        total_jd = max(1, len(jd_skills))
        matched_count = len(exact_matches) + len(semantic_matches) * 0.8
        score = min(100, round((matched_count / total_jd) * 100, 1))
        
        return {
            "exact_matches": exact_matches,
            "semantic_matches": semantic_matches,
            "overall_score": score
        }

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
