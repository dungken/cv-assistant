import logging
from typing import List
from services.ner_service.models.schemas import Entity

logger = logging.getLogger(__name__)

from pathlib import Path
from transformers import pipeline
from services.ner_service.models.schemas import Entity

logger = logging.getLogger(__name__)

class NERExtractor:
    """Handles inference with BERT-based NER model."""
    
    def __init__(self, model_path: str):
        self.model_path = model_path
        self.nlp = None
        
        try:
            if Path(model_path).exists() and any(Path(model_path).iterdir()):
                logger.info(f"Loading NER model from {model_path}...")
                self.nlp = pipeline("ner", model=model_path, tokenizer=model_path, aggregation_strategy="simple")
            else:
                logger.warning(f"Model path {model_path} not found or empty. Running in mock mode.")
        except Exception as e:
            logger.error(f"Error loading model: {e}")
            self.nlp = None

    def extract(self, text: str) -> List[Entity]:
        """Extract entities using the loaded model or fallback to mock logic."""
        if self.nlp:
            results = self.nlp(text)
            entities = []
            for res in results:
                entities.append(Entity(
                    text=res['word'],
                    label=res['entity_group'],
                    start=res['start'],
                    end=res['end'],
                    confidence=float(res['score'])
                ))
            return entities
        
        # Fallback Mock Logic
        logger.info("Mock extraction triggered.")
        entities = []
        mock_keywords = {
            "Python": "SKILL",
            "Java": "SKILL",
            "Finance": "MAJOR",
            "Google": "ORG"
        }
        for kw, label in mock_keywords.items():
            if kw in text:
                entities.append(Entity(
                    text=kw, label=label, 
                    start=text.find(kw), end=text.find(kw)+len(kw), 
                    confidence=0.9
                ))
        return entities

