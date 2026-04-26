import functools
import logging
import re
from typing import List, Dict, Any, Optional
from pathlib import Path
from transformers import pipeline

from services.ner_service.models.schemas import Entity
from shared.utils.cv_parser import SmartCVParser

logger = logging.getLogger(__name__)

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
        """Atomic entity extraction with detokenization.
        Chunks long texts to avoid BERT 512-token truncation."""
        if self.nlp:
            # BERT max is 512 subword tokens ≈ 350–400 chars safe per chunk
            CHUNK_CHARS = 380
            OVERLAP_CHARS = 40

            if len(text) <= CHUNK_CHARS:
                chunks = [(text, 0)]
            else:
                chunks = []
                pos = 0
                while pos < len(text):
                    chunks.append((text[pos:pos + CHUNK_CHARS], pos))
                    pos += CHUNK_CHARS - OVERLAP_CHARS

            raw_entities: List[Entity] = []
            seen_spans: set = set()
            for chunk_text, offset in chunks:
                results = self.nlp(chunk_text)
                for res in results:
                    abs_start = res['start'] + offset
                    abs_end   = res['end']   + offset
                    span_key  = (abs_start, abs_end, res['entity_group'])
                    if span_key in seen_spans:
                        continue
                    seen_spans.add(span_key)
                    raw_entities.append(Entity(
                        text=res['word'],
                        type=res['entity_group'],
                        start=abs_start,
                        end=abs_end,
                        confidence=float(res['score'])
                    ))
            return self._post_process_entities(raw_entities)
        
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

    def batch_extract(self, texts: List[str]) -> List[List[Entity]]:
        """Process multiple texts efficiently."""
        if self.nlp:
            # transformers pipeline handles lists efficiently
            results_list = self.nlp(texts)
            all_entities = []
            for results in results_list:
                entities = []
                for res in results:
                    entities.append(Entity(
                        text=res['word'],
                        type=res['entity_group'],
                        start=res['start'],
                        end=res['end'],
                        confidence=float(res['score'])
                    ))
                all_entities.append(self._post_process_entities(entities))
            return all_entities
        
        return [self.extract(t) for t in texts]

    # Well-known compound skills that BERT often splits into separate entities
    _COMPOUND_SKILLS = {
        ("ci", "cd"): "CI/CD",
        ("ci/cd",): "CI/CD",
        ("react", "native"): "React Native",
        ("node", "js"): "Node.js",
        ("vue", "js"): "Vue.js",
        ("next", "js"): "Next.js",
        ("nuxt", "js"): "Nuxt.js",
        ("nest", "js"): "NestJS",
        ("angular", "js"): "Angular",
        ("ruby", "on", "rails"): "Ruby on Rails",
        ("react", "js"): "React",
        ("spring", "boot"): "Spring Boot",
        ("machine", "learning"): "Machine Learning",
        ("deep", "learning"): "Deep Learning",
        ("natural", "language", "processing"): "NLP",
        ("computer", "vision"): "Computer Vision",
        ("data", "science"): "Data Science",
        ("data", "engineering"): "Data Engineering",
        ("unit", "testing"): "Unit Testing",
        ("web", "security"): "Web Security",
        ("power", "bi"): "Power BI",
        ("material", "ui"): "Material UI",
        ("ant", "design"): "Ant Design",
        ("domain", "driven", "design"): "Domain-Driven Design",
        ("clean", "architecture"): "Clean Architecture",
        ("design", "patterns"): "Design Patterns",
        ("functional", "programming"): "Functional Programming",
        ("api", "gateway"): "API Gateway",
        ("event", "driven"): "Event-Driven",
    }

    # Normalization rules for spacing/casing artifacts from BERT tokenization
    _SKILL_NORMALIZE_MAP = {
        r"\.\s+net\b": ".NET",
        r"react\s*\.\s*js": "React.js",
        r"node\s*\.\s*js": "Node.js",
        r"vue\s*\.\s*js": "Vue.js",
        r"next\s*\.\s*js": "Next.js",
        r"nuxt\s*\.\s*js": "Nuxt.js",
        r"nest\s*js": "NestJS",
        r"angular\s*js": "Angular",
        r"express\s*\.\s*js": "Express.js",
        r"c\s*#": "C#",
        r"c\s*\+\s*\+": "C++",
        r"rx\s*js": "RxJS",
        r"type\s*script": "TypeScript",
        r"java\s*script": "JavaScript",
        r"mongo\s*db": "MongoDB",
        r"postgre\s*sql": "PostgreSQL",
        r"my\s*sql": "MySQL",
        r"spring\s*boot": "Spring Boot",
        r"git\s*hub": "GitHub",
        r"git\s*lab": "GitLab",
    }

    def _normalize_skill_text(self, text: str) -> str:
        """Fix common BERT tokenization artifacts in skill names."""
        for pattern, replacement in self._SKILL_NORMALIZE_MAP.items():
            text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
        return text.strip()

    def _split_conjunction_entities(self, entities: List[Entity]) -> List[Entity]:
        """Split entities like 'React and TypeScript' into separate skills."""
        split_result = []
        conjunctions = re.compile(r"\s+(?:and|or|&|và|hoặc|,\s*and|,\s*or)\s+", re.I)

        for ent in entities:
            if ent.type == "SKILL" and conjunctions.search(ent.text):
                parts = conjunctions.split(ent.text)
                offset = ent.start
                for part in parts:
                    part = part.strip().strip(",").strip()
                    if part and len(part) >= 1:
                        split_result.append(Entity(
                            text=part,
                            type=ent.type,
                            start=offset,
                            end=offset + len(part),
                            confidence=ent.confidence
                        ))
                    offset += len(part) + 5  # approx space for conjunction
            else:
                split_result.append(ent)
        return split_result

    def _merge_adjacent_same_type(self, entities: List[Entity]) -> List[Entity]:
        """Merge adjacent entities of the same type that are close together.
        Handles cases like CI (SKILL) + CD (SKILL) → CI/CD."""
        if len(entities) < 2:
            return entities

        merged = [entities[0]]
        for ent in entities[1:]:
            last = merged[-1]
            gap = ent.start - last.end

            # Merge adjacent same-type SKILL entities if gap <= 3 chars
            # (covers "CI/CD", "CI / CD", "CI-CD" patterns)
            if (last.type == ent.type == "SKILL" and gap <= 3):
                # Check if this is a known compound
                combined_key = (last.text.lower().strip(), ent.text.lower().strip())
                if combined_key in self._COMPOUND_SKILLS:
                    last.text = self._COMPOUND_SKILLS[combined_key]
                    last.end = ent.end
                    last.confidence = max(last.confidence, ent.confidence)
                    continue

            # Also merge same-type adjacent entities for non-SKILL types
            # (handles split JOB_TITLE like "Senior" + "Frontend Developer")
            if (last.type == ent.type and last.type in ("JOB_TITLE", "ORG", "LOC", "DEGREE", "MAJOR")
                    and gap <= 3):
                last.text = last.text.rstrip() + " " + ent.text.lstrip()
                last.end = ent.end
                last.confidence = (last.confidence + ent.confidence) / 2
                continue

            merged.append(ent)
        return merged

    def _post_process_entities(self, entities: List[Entity]) -> List[Entity]:
        """Merge BERT subword tokens (##), fix spacing, and deduplicate."""
        if not entities:
            return []

        # 1. Cleaning and Subword Merging
        merged = []
        for ent in entities:
            # Clean up the (cid:xxx) artifacts often found in PDFs
            text = re.sub(r"\(cid:\d+\)", " ", ent.text)
            # Strip punctuation artifacts EARLY so merge step sees clean text
            # e.g. BERT returns "CD (" → "CD", allowing CI+CD merge
            text = re.sub(r'^[\(\)\[\]\{\},\.\|:;\s]+', '', text)
            text = re.sub(r'[\(\)\[\]\{\},\.\|:;\s]+$', '', text)
            # Normalize spacing artifacts in skill names
            text = self._normalize_skill_text(text)

            if text.startswith("##") and merged:
                last = merged[-1]
                if abs(last.end - ent.start) <= 2:
                    last.text += text[2:]
                    last.end = ent.end
                    last.confidence = (last.confidence + ent.confidence) / 2
                else:
                    ent.text = text[2:]
                    merged.append(ent)
            else:
                ent.text = text
                merged.append(ent)

        # 2. Merge adjacent same-type entities (CI+CD→CI/CD, Senior+Frontend Developer)
        merged = self._merge_adjacent_same_type(merged)

        # 3. Split conjunction entities (React and TypeScript → React, TypeScript)
        merged = self._split_conjunction_entities(merged)

        # 4. Final normalization pass on each entity text
        for ent in merged:
            ent.text = self._normalize_skill_text(ent.text)

        # 5. Filtering and Deduplication
        final = []
        seen = set()

        JUNK_PATTERNS = [
            r"^com$", r"^gmail$", r"^github$", r"^linkedin$", r"^www$", r"^http$", r"^https$",
            r"^png$", r"^jpg$", r"^vnpay$", r"^cid$", r"^blob$", r"^master$", r"^dungken$",
            r"^topic$", r"^prize$", r"^award$", r"^scientific$", r"^research$", r"^student$",
            r"^esu$", r"^dung$", r"^bui$", r"^dinh$", r"^hoang$", r"^ng$",
            r"^cao$", r"^xuan$", r"^diep$"
        ]

        SKILL_BLACKLIST = {
            "architecture", "media", "admin", "code", "engineering", "complex", "logic",
            "implementation", "refactoring", "system", "integration", "linked", "linkedin",
            "team", "project", "management", "communication", "problem", "solving",
            "english", "vietnamese", "tiếng anh", "tiếng việt",
            "end", "da", "full", "stack", "front", "back", "web", "app",
            "strong", "solid", "good", "excellent", "proficient", "familiar",
            "experience", "knowledge", "understanding", "ability", "skill",
            "years", "year", "minimum", "senior", "junior", "mid",
            "company", "position", "role", "job", "work", "working",
            "cd", "ci", "sre", "qa", "pm", "it",
            "service", "server", "client", "data", "file", "user",
            "test", "build", "run", "set", "get", "use",
        }

        for ent in merged:
            ent.text = ent.text.strip()
            if not ent.text or len(ent.text) < 2:
                if len(ent.text) == 1 and ent.text.upper() in ["C", "R"] and ent.type == "SKILL":
                    pass
                else:
                    continue

            if ent.text.lower() in [",", ".", "|", "-", ":", "(", ")", "[", "]", "{", "}"]:
                continue

            if any(re.match(p, ent.text.lower()) for p in JUNK_PATTERNS):
                continue

            if ent.type == "SKILL" and ent.text.lower() in SKILL_BLACKLIST:
                continue

            # Remove trailing/leading punctuation artifacts
            ent.text = re.sub(r'^[\(\)\[\]\{\}\-,\.\|:]+', '', ent.text).strip()
            ent.text = re.sub(r'[\(\)\[\]\{\}\-,\.\|:]+$', '', ent.text).strip()
            if not ent.text or (len(ent.text) < 2 and ent.text.upper() not in ["C", "R"]):
                continue

            # Drop low-confidence entities (BERT is unsure)
            if ent.confidence < 0.40:
                continue

            # Deduplication: case-insensitive, type-aware, position-tolerant
            dedup_key = f"{ent.text.lower()}_{ent.type}"
            if dedup_key in seen:
                continue

            seen.add(dedup_key)
            final.append(ent)

        return final

    def extract_structured(self, file_path: str) -> Dict[str, Any]:
        """Hierarchical extraction by sectioning via Docling Markdown."""
        import time
        start_time = time.time()
        
        markdown_text = self.parser.get_markdown(file_path)
        if not markdown_text:
            return {"error": "Failed to parse file"}

        sections = self.parser.identify_sections(markdown_text)
        
        structured_data = {
            "summary": "",
            "experience": [],
            "projects": [],
            "education": [],
            "certifications": [],
            "skills": {},
            "languages": [],
            "raw_text": markdown_text,
            "metadata": {}
        }
        
        # Metadata extraction
        parser_metadata = self.parser.get_metadata(file_path)
        
        # Simple Language Detection
        vi_chars = r'[àáảãạăằắẳẵặâầấẩẫậèéẻẽẹêềếểễệìíỉĩịòóỏõọôồốổỗộơờớởỡợùúủũụưừứửữựỳýỷỹỵđ]'
        is_vi = bool(re.search(vi_chars, markdown_text, re.IGNORECASE))
        
        structured_data["metadata"] = {
            "language": "vi" if is_vi else "en",
            "pages": parser_metadata.get("pages", 0),
            "parse_method": parser_metadata.get("parse_method", "unknown"),
            "parse_time_ms": int((time.time() - start_time) * 1000)
        }

        # Process Summary (with contact filtering)
        if "SUMMARY" in sections:
            contact_markers = ["/envelope", "/github", "/linkedin", "/globe", "@", "HCMC", "VIETNAM"]
            lines = []
            for l in sections["SUMMARY"]:
                if not any(m in l["text"] for m in contact_markers):
                    lines.append(l["text"])
            structured_data["summary"] = "\n".join(lines)
            
        # Track all extracted skills globally for high-quality sidebar mapping
        all_extracted_skills = set()
        
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
                    anchor = item["anchor"]
                    # Skip items that are just contact info incorrectly recognized as a section item
                    contact_patterns = [r"@", r"\d{10}", r"linkedin\.com", r"github\.com"]
                    if any(re.search(p, anchor) for p in contact_patterns):
                        continue
                    if len(anchor.split()) < 4 and any(n in anchor.lower() for n in ["hoang", "dinh", "bui", "dung", "ken", "cao", "xuan", "diep"]):
                        # Likely the user's name appearing as a header
                        continue

                    full_text = " ".join([l["text"] for l in item["raw_lines"] if l["text"]])
                    entities = self.extract(full_text)
                    
                    # Store found skills globally
                    for e in entities:
                        if e.type == "SKILL":
                            all_extracted_skills.add(e.text)
                    
                    # Clean up table artifacts in description
                    clean_content = []
                    for line in item["content"]:
                        # Strip | and --- table markers
                        line = re.sub(r"^[\|\-\s]+", "", line)
                        line = re.sub(r"[\|\-\s]+$", "", line)
                        line = line.replace("|", " ").strip()
                        if line: clean_content.append(line)

                    # Group entities within this item
                    item_data = {
                        "anchor": anchor,
                        "entities": [e.dict() for e in entities],
                        "description": "\n".join(clean_content) # Preserve line breaks
                    }
                    structured_data[key].append(item_data)
                
        # Process Languages
        if "LANGUAGES" in sections:
            for line_obj in sections["LANGUAGES"]:
                text = line_obj["text"].strip()
                if text and len(text) < 50:
                    structured_data["languages"].append(text.replace("- ", "").replace("* ", ""))

        # Process Skills (Nested)
        if "SKILLS" in sections:
            current_category = "General"
            for line_obj in sections["SKILLS"]:
                text = line_obj["text"].strip()
                if not text: continue
                
                # In Markdown, skills often appear in lists or bold categories
                skills_text = text
                
                # Priority: Header-like bold lines as categories
                # Case 1: **Category Name**
                if (text.startswith("**") and text.endswith("**")) and len(text.split()) < 4:
                    current_category = text.replace("**", "").strip()
                    if current_category not in structured_data["skills"]:
                        structured_data["skills"][current_category] = []
                    continue
                
                # Case 2: "Category Name:" (with or without skills after colon)
                if ":" in text and len(text.split(":")[0]) < 35:
                    parts = text.split(":", 1)
                    potential_category = parts[0].replace("**", "").replace("*", "").replace("-", "").strip()
                    # Only accept as category if the prefix doesn't look like a standard sentence
                    if len(potential_category.split()) < 5:
                        current_category = potential_category
                        skills_text = parts[1].strip()
                        if current_category not in structured_data["skills"]:
                            structured_data["skills"][current_category] = []
                
                if not skills_text or skills_text.lower() in ["none", "n/a", "-"]:
                    continue
                
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
        
        # Final Harvesting: Add skills found in descriptions but not in the "Skills" section
        if all_extracted_skills:
            # Create a fallback category for skills discovered in text
            if "Technical Background" not in structured_data["skills"]:
                structured_data["skills"]["Technical Background"] = []
                
            # Collect all categorized skills for easy lookup
            categorized_skills_pool = set()
            for skills in structured_data["skills"].values():
                for s in skills:
                    categorized_skills_pool.add(s.lower())
            
            for skill in all_extracted_skills:
                if skill.lower() not in categorized_skills_pool:
                    structured_data["skills"]["Technical Background"].append(skill)
                    categorized_skills_pool.add(skill.lower())
                    
        return structured_data
