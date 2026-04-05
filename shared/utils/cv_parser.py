import re
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path

try:
    from docling.document_converter import DocumentConverter, PdfFormatOption
    from docling.datamodel.pipeline_options import PdfPipelineOptions, TableFormerMode
    from docling.datamodel.base_models import InputFormat
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
        "SUMMARY": [
            "summary", "profile", "about me", "giới thiệu", "tóm tắt", 
            "professional summary", "personal profile", "objective", "career objective",
            "mục tiêu nghề nghiệp"
        ],
        "EXPERIENCE": [
            "experience", "work history", "employment", "kinh nghiệm", 
            "quá trình làm việc", "work experience", "experience & projects", 
            "career history", "professional experience", "kinh nghiệm làm việc"
        ],
        "PROJECTS": [
            "projects", "personal projects", "dự án", "project experience", 
            "tiêu biểu", "academic projects", "dự án cá nhân", "key projects"
        ],
        "EDUCATION": [
            "education", "academic", "học vấn", "đào tạo", 
            "education & qualifications", "background", "trình độ học vấn"
        ],
        "SKILLS": [
            "skills", "technical skills", "kỹ năng", "năng lực", 
            "specialization", "expertise", "competencies", "skills & technologies",
            "kỹ năng chuyên môn", "công nghệ sử dụng"
        ],
        "CERTIFICATIONS": [
            "certifications", "awards", "chứng chỉ", "giải thưởng", 
            "achievements", "honors", "chứng chỉ & giải thưởng", "awards & honors"
        ],
        "LANGUAGES": ["languages", "ngôn ngữ", "foreign languages"]
    }

    def __init__(self):
        if HAS_DOCLING:
            # Configure DocumentConverter with advanced options for 2-column layouts
            pipeline_options = PdfPipelineOptions()
            # Use accurate mode for better boundary detection in multi-column layouts
            pipeline_options.table_structure_options.mode = TableFormerMode.ACCURATE
            # Disable cell matching to prevent merging separate columns incorrectly
            pipeline_options.table_structure_options.do_cell_matching = False
            
            self.converter = DocumentConverter(
                format_options={
                    InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
                }
            )
            logger.info("Docling initialized with ACCURATE pipeline for layout awareness")
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
                # Store page count in an instance variable for later retrieval
                self._last_page_count = len(result.document.pages) if hasattr(result.document, 'pages') else 0
                return result.document.export_to_markdown()
            except Exception as e:
                logger.warning(f"Docling failed, falling back to pdfplumber: {e}")

        # Fallback to pdfplumber
        if HAS_PDFPLUMBER:
            try:
                logger.info(f"Converting PDF to text with pdfplumber: {pdf_path}")
                with pdfplumber.open(pdf_path) as pdf:
                    self._last_page_count = len(pdf.pages)
                    return self._pdfplumber_extract(pdf_path)
            except Exception as e:
                logger.error(f"pdfplumber also failed: {e}")
                self._last_page_count = 0
                return ""

        logger.error("No PDF parser available (install docling or pdfplumber)")
        self._last_page_count = 0
        return ""

    def get_metadata(self, pdf_path: str) -> Dict[str, Any]:
        """Extra metadata like page count."""
        return {
            "pages": getattr(self, "_last_page_count", 0),
            "parse_method": "docling" if HAS_DOCLING else "pdfplumber"
        }

    def identify_sections(self, markdown_text: str) -> Dict[str, List[Dict[str, Any]]]:
        """Segment Markdown into sections based on headers and bold markers."""
        sections = {"HEADER": []}
        current_section = "HEADER"
        
        lines = markdown_text.splitlines()
        
        for line in lines:
            stripped_line = line.strip()
            if not stripped_line: continue
            
            # Detect section headers (Markdown headers #, ##, ### or bold lines)
            header_match = re.match(r"^(#+)\s+(.*)", stripped_line)
            is_new_section = False
            
            potential_header = ""
            if header_match:
                potential_header = header_match.group(2).strip().upper()
            elif (stripped_line.startswith("**") and stripped_line.endswith("**")) or (stripped_line.startswith("__") and stripped_line.endswith("__")):
                # Bold line might be a section header if it's short
                potential_header = stripped_line.replace("**", "").replace("__", "").strip().upper()
            
            # Detect plain text section headers (short lines matching keywords)
            if not potential_header:
                if 2 < len(stripped_line) < 40 and len(stripped_line.split()) < 5:
                    potential_header = stripped_line.upper()

            if potential_header:
                for section, keywords in self.SECTION_KEYWORDS.items():
                    # Flexible matching: Exact match, Startswith + Colon, or just Startswith for common keywords
                    if any(kw.upper() == potential_header or 
                           potential_header.startswith(kw.upper() + ":") or
                           (len(kw) >= 5 and potential_header.startswith(kw.upper() + " ")) 
                           for kw in keywords):
                        current_section = section
                        if current_section not in sections:
                            sections[current_section] = []
                        is_new_section = True
                        break
            
            # Detect Contact Info / Socials even if not a section (to separate from Summary)
            contact_markers = ["/envelope", "/github", "/linkedin", "/globe", "@", "HCMC", "VIETNAM", "HONEYPOT"]
            if current_section == "SUMMARY" and any(m in line for m in contact_markers):
                if "HEADER" not in sections: sections["HEADER"] = []
                sections["HEADER"].append({"text": stripped_line, "is_bold": False})
                continue

            if not is_new_section:
                sections[current_section].append({
                    "text": stripped_line, 
                    "is_bold": stripped_line.startswith("**") or stripped_line.startswith("__")
                })
        
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
            
            # Sub-headers within a project or job should NOT trigger a new item
            SUB_HEADERS = ["RESPONSIBILITY", "TARGET", "ROLE", "STACK", "TECH STACK", "DESCRIPTION", "TECHNOLOGIES", "EXPECTED"]
            upper_text = text.upper().replace("#", "").replace("*", "").strip()
            is_sub_header = any(upper_text.startswith(kw) for kw in SUB_HEADERS)
            
            if not is_sub_header:
                # Markdown Headers (##, ###) are strong indicators of new items (e.g. ## Project Name)
                if text.startswith("##") or text.startswith("###"):
                    is_new_item = True
                # Bold lines with few words and no delimiters like commas/pipes are usually job titles or project names
                elif (text.startswith("**") and not re.search(r"[,/|•]", text) and len(text.split()) < 8):
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
