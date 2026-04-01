import logging
import re
from typing import List, Dict, Any
from services.ner_service.models.schemas import Entity

logger = logging.getLogger(__name__)

from pathlib import Path
from transformers import pipeline
from shared.utils.cv_parser import SmartCVParser

class NERExtractor:
    """Handles inference with BERT-based NER model and structural grouping."""
    
    def __init__(self, model_path: str):
        self.model_path = model_path
        self.nlp = None
        self.parser = SmartCVParser()
        
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
        """Atomic entity extraction with detokenization."""
        if self.nlp:
            results = self.nlp(text)
            entities = []
            for res in results:
                entities.append(Entity(
                    text=res['word'],
                    type=res['entity_group'],
                    start=res['start'],
                    end=res['end'],
                    confidence=float(res['score'])
                ))
            return self._post_process_entities(entities)
        
        # Fallback Mock Logic
        logger.info("Mock extraction triggered.")
        entities = []
        mock_keywords = {
            "Python": "SKILL", "Java": "SKILL", "SQL": "SKILL", 
            "Node.js": "SKILL", "React": "SKILL", "Finance": "MAJOR", 
            "Google": "ORG", "Data Analyst": "JOB_TITLE", "UEH": "ORG"
        }
        for kw, label in mock_keywords.items():
            if kw.lower() in text.lower():
                start_idx = text.lower().find(kw.lower())
                entities.append(Entity(
                    text=kw, type=label, start=start_idx, 
                    end=start_idx + len(kw), confidence=0.9
                ))
        return entities

    def _post_process_entities(self, entities: List[Entity]) -> List[Entity]:
        """Merge BERT subword tokens (##) and fix spacing."""
        if not entities:
            return []
            
        merged = []
        for ent in entities:
            text = ent.text
            # Clean up the (cid:xxx) artifacts often found in PDFs
            text = re.sub(r"\(cid:\d+\)", " ", text)
            
            if text.startswith("##") and merged:
                last = merged[-1]
                last.text += text[2:]
                last.end = ent.end
                # Average the confidence
                last.confidence = (last.confidence + ent.confidence) / 2
            else:
                ent.text = text
                merged.append(ent)
        
        # Final pass: clean up whitespace in merged texts
        for m in merged:
            m.text = m.text.strip()
            
        return merged

    def extract_structured(self, pdf_path: str) -> Dict[str, Any]:
        """Hierarchical extraction by sectioning via Docling Markdown."""
        markdown_text = self.parser.get_markdown(pdf_path)
        if not markdown_text:
            return {"error": "Failed to parse PDF"}

        sections = self.parser.identify_sections(markdown_text)
        
        structured_data = {
            "summary": "",
            "experience": [],
            "projects": [],
            "education": [],
            "certifications": [],
            "skills": {},
            "raw_text_preview": markdown_text[:2000] # For debugging
        }
        
        # Process Summary
        if "SUMMARY" in sections:
            structured_data["summary"] = "\n".join([l["text"] for l in sections["SUMMARY"]])
            
        # Process Experience, Projects, Education, Certifications
        for sec_name, key in [
            ("EXPERIENCE", "experience"), 
            ("PROJECTS", "projects"), 
            ("EDUCATION", "education"),
            ("CERTIFICATIONS", "certifications")
        ]:
            if sec_name in sections:
                items = self.parser.group_items(sections[sec_name])
                for item in items:
                    full_text = " ".join([l["text"] for l in item["raw_lines"]])
                    entities = self.extract(full_text)
                    
                    # Group entities within this item
                    item_data = {
                        "anchor": item["anchor"],
                        "entities": [e.dict() for e in entities],
                        "description": " ".join(item["content"])
                    }
                    structured_data[key].append(item_data)
                
        # Process Skills (Nested)
        if "SKILLS" in sections:
            current_category = "General"
            for line_obj in sections["SKILLS"]:
                text = line_obj["text"].strip()
                if not text: continue
                
                # In Markdown, skills often appear in lists or bold categories
                skills_text = text
                
                # Priority: Header-like bold lines as categories
                if text.startswith("**") and text.endswith("**") and len(text.split()) < 4:
                    current_category = text.replace("**", "").strip()
                    continue
                
                # Pattern: Category: Skill1, Skill2
                if ":" in text and len(text.split(":")[0]) < 30:
                    parts = text.split(":", 1)
                    current_category = parts[0].replace("**", "").strip()
                    skills_text = parts[1].strip()
                
                ents = self.extract(skills_text)
                skills_list = [e.text for e in ents if e.type == "SKILL"]
                
                # Fallback: if no skills found with NER, split by common separators
                if (not skills_list or len(skills_list) < 2) and ("," in skills_text or "/" in skills_text or "|" in skills_text):
                    # Clean up bullet markers and periods
                    clean_text = re.sub(r"^[-•\*◦\.]\s*", "", skills_text)
                    raw_items = [s.strip() for s in re.split(r"[,/|•\.]", clean_text) if s.strip()]
                    skills_list = [s for s in raw_items if 2 <= len(s) < 40]
                
                if current_category not in structured_data["skills"]:
                    structured_data["skills"][current_category] = []
                
                for s in skills_list:
                    if s not in structured_data["skills"][current_category]:
                        structured_data["skills"][current_category].append(s)
                
        return structured_data
