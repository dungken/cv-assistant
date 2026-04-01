import logging
from typing import List, Dict
import numpy as np
from sentence_transformers import SentenceTransformer
import chromadb
from services.skill_service.models.schemas import SemanticMatch

logger = logging.getLogger(__name__)

class SkillMatcher:
    """Core logic for skill matching and JD extraction using O*NET taxonomy."""
    
    def __init__(self, model: SentenceTransformer, collection: chromadb.Collection, onet_collection: chromadb.Collection = None, ner_url: str = None):
        self.model = model
        self.collection = collection  # Job collection for recommendations
        self.onet_collection = onet_collection  # O*NET skills collection
        self.ner_url = ner_url

    def extract_skills_from_jd(self, jd_text: str) -> List[str]:
        """
        Extract skills from JD text. Prefers NER service, falls back to O*NET semantic search.
        """
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
                    # Lower threshold for fallback to be more inclusive
                    if distance < 0.45: 
                        extracted.add(results['documents'][0][i])
        
        return list(extracted)

    def match(self, cv_skills: List[str], jd_skills: List[str]) -> Dict:
        """Calculate matches between CV and JD skills using vector similarity."""
        cv_skills_lower = [s.lower() for s in cv_skills]
        jd_skills_lower = [s.lower() for s in jd_skills]
        
        # Exact matches
        exact_matches = list(set(cv_skills_lower) & set(jd_skills_lower))
        
        # Semantic matches
        semantic_matches = []
        unmatched_jd = [s for s in jd_skills_lower if s not in exact_matches]
        
        if unmatched_jd and cv_skills_lower:
            # Encode everything in batches
            jd_embeddings = self.model.encode(unmatched_jd)
            cv_embeddings = self.model.encode(cv_skills_lower)
            
            for i, jd_skill in enumerate(unmatched_jd):
                jd_emb = jd_embeddings[i]
                # Calculate similarities with all CV skills
                similarities = (cv_embeddings @ jd_emb) / (
                    np.linalg.norm(cv_embeddings, axis=1) * np.linalg.norm(jd_emb) + 1e-9
                )
                
                best_idx = np.argmax(similarities)
                best_similarity = similarities[best_idx]
                
                if best_similarity > 0.65: # Threshold for "match"
                    semantic_matches.append(SemanticMatch(
                        cv_skill=cv_skills_lower[best_idx],
                        jd_skill=jd_skill,
                        similarity=round(float(best_similarity), 2)
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
