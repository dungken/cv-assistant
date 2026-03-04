import logging
from typing import List, Dict, Any, Optional
import chromadb

logger = logging.getLogger(__name__)

class SkillNormalizer:
    """Normalizes raw skill strings to canonical O*NET skills using vector search."""
    
    def __init__(self, collection: chromadb.Collection, threshold: float = 0.7):
        self.collection = collection
        self.threshold = threshold

    def normalize(self, raw_skill: str) -> Optional[Dict[str, Any]]:
        """Find the closest canonical skill for a given raw string."""
        try:
            # Query ChromaDB
            results = self.collection.query(
                query_texts=[raw_skill],
                n_results=1
            )
            
            if not results["documents"] or not results["documents"][0]:
                return None
            
            # Chroma returns distances. For cosine similarity, smaller is better.
            # Convert distance to a similarity score if needed, but here we just check threshold.
            distance = results["distances"][0][0]
            similarity = 1 - distance # Assuming cosine distance [0, 2] -> similarity [1, -1]
            
            if similarity < self.threshold:
                logger.debug(f"Skill '{raw_skill}' normalized match '{results['documents'][0][0]}' below threshold ({similarity:.2f})")
                return None
                
            return {
                "raw": raw_skill,
                "canonical": results["documents"][0][0],
                "id": results["ids"][0][0],
                "metadata": results["metadatas"][0][0],
                "confidence": float(similarity)
            }
            
        except Exception as e:
            logger.error(f"Error normalizing skill '{raw_skill}': {e}")
            return None

    def normalize_list(self, raw_skills: List[str]) -> List[Dict[str, Any]]:
        """Normalize a list of skills, filtering out those below threshold."""
        normalized = []
        for skill in raw_skills:
            norm = self.normalize(skill)
            if norm:
                normalized.append(norm)
        return normalized
