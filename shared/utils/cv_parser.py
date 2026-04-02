import re
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path

try:
    from docling.document_converter import DocumentConverter
    HAS_DOCLING = True
except ImportError:
    HAS_DOCLING = False

try:
    import pdfplumber
    HAS_PDFPLUMBER = True
except ImportError:
    HAS_PDFPLUMBER = False

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SmartCVParser:
    """
    Advanced CV parser that handles sectioning and visual-aware grouping.
    Uses Docling if available, falls back to pdfplumber.
    """

    SECTION_KEYWORDS = {
        "SUMMARY": ["summary", "profile", "about me", "giới thiệu", "tóm tắt", "professional summary", "personal profile"],
        "EXPERIENCE": ["experience", "work history", "employment", "kinh nghiệm", "quá trình làm việc", "work experience", "experience & projects", "career history"],
        "PROJECTS": ["projects", "personal projects", "dự án", "project experience", "tiêu biểu", "academic projects"],
        "EDUCATION": ["education", "academic", "học vấn", "đào tạo", "education & qualifications"],
        "SKILLS": ["skills", "technical skills", "kỹ năng", "năng lực", "specialization", "expertise", "competencies"],
        "CERTIFICATIONS": ["certifications", "awards", "chứng chỉ", "giải thưởng", "achievements", "honors"]
    }

    def __init__(self):
        if HAS_DOCLING:
            self.converter = DocumentConverter()
        else:
            self.converter = None
            logger.info("Docling not available, using pdfplumber fallback")

    def _pdfplumber_extract(self, pdf_path: str) -> str:
        """Extract text from PDF using pdfplumber."""
        text_lines = []
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text_lines.append(page_text)
        return "\n".join(text_lines)

    def get_markdown(self, pdf_path: str) -> str:
        """Convert PDF to Markdown using Docling or pdfplumber fallback."""
        # Try Docling first
        if self.converter is not None:
            try:
                logger.info(f"Converting PDF to Markdown with Docling: {pdf_path}")
                result = self.converter.convert(pdf_path)
                return result.document.export_to_markdown()
            except Exception as e:
                logger.warning(f"Docling failed, falling back to pdfplumber: {e}")

        # Fallback to pdfplumber
        if HAS_PDFPLUMBER:
            try:
                logger.info(f"Converting PDF to text with pdfplumber: {pdf_path}")
                return self._pdfplumber_extract(pdf_path)
            except Exception as e:
                logger.error(f"pdfplumber also failed: {e}")
                return ""

        logger.error("No PDF parser available (install docling or pdfplumber)")
        return ""

    def identify_sections(self, markdown_text: str) -> Dict[str, List[Dict[str, Any]]]:
        """Segment Markdown into sections based on headers."""
        sections = {"HEADER": []}
        current_section = "HEADER"
        
        lines = markdown_text.splitlines()
        
        for line in lines:
            if not line.strip(): continue
            
            # Detect section headers (Markdown headers #, ##, ### or bold lines)
            header_match = re.match(r"^(#+)\s+(.*)", line)
            is_new_section = False
            
            potential_header = ""
            if header_match:
                potential_header = header_match.group(2).strip().upper()
            elif line.startswith("**") and line.endswith("**"):
                # Bold line might be a section header if it's short
                potential_header = line.replace("**", "").strip().upper()
            
            # Also detect plain text section headers (short lines matching keywords)
            if not potential_header:
                stripped = line.strip()
                if len(stripped.split()) < 5:
                    potential_header = stripped.upper()

            if potential_header:
                for section, keywords in self.SECTION_KEYWORDS.items():
                    if any(kw.upper() in potential_header for kw in keywords) and len(potential_header.split()) < 5:
                        current_section = section
                        if current_section not in sections:
                            sections[current_section] = []
                        is_new_section = True
                        break
            
            if not is_new_section:
                sections[current_section].append({"text": line, "is_bold": line.startswith("**")})
        
        return sections

    def group_items(self, section_lines: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Group lines into logical items (e.g., job entries) using Markdown structure."""
        items = []
        current_item = None
        
        for line_obj in section_lines:
            text = line_obj["text"].strip()
            if not text: continue
            
            # In Markdown, new items often start with a header level or a bold line
            # Docling might produce ## Employer or **Employer**
            is_new_item = False
            if text.startswith("###") or (text.startswith("**") and not re.search(r"[,/|•]", text) and len(text.split()) < 10):
                is_new_item = True
            elif self._contains_date(text) and not current_item:
                is_new_item = True
                
            if is_new_item:
                if current_item:
                    items.append(current_item)
                current_item = {
                    "anchor": text.replace("#", "").replace("**", "").strip(),
                    "content": [],
                    "raw_lines": [line_obj]
                }
            elif current_item:
                current_item["content"].append(text)
                current_item["raw_lines"].append(line_obj)
            else:
                # First line in section if no anchor found
                current_item = {
                    "anchor": text.replace("#", "").replace("**", "").strip(),
                    "content": [],
                    "raw_lines": [line_obj]
                }
        
        if current_item:
            items.append(current_item)
            
        return items

    def _contains_date(self, text: str) -> bool:
        """Helper to detect date patterns."""
        date_patterns = [
            r"\d{4}",
            r"(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)",
            r"(Tháng|Tháng \d+)",
            r"Present|Hiện tại"
        ]
        return any(re.search(p, text, re.I) for p in date_patterns)

    def get_visual_lines(self, pdf_path: str):
        """Compatibility wrapper for extract_structured."""
        return self.get_markdown(pdf_path)
