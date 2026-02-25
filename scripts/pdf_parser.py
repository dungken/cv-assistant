import pdfplumber
import os
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def is_english(text):
    """Simple heuristic to check if text is predominantly English"""
    if not text: return False
    # Check for common English stop words or headings
    english_keywords = ["education", "experience", "skills", "summary", "university", "project", "language", "github", "stack", "technologies", "certifications", "contact", "profile"]
    text_lower = text.lower()
    score = sum(1 for kw in english_keywords if kw in text_lower)
    # If at least 3 headings or keywords found, consider it likely English-scope
    return score >= 3

def parse_pdf(pdf_path: str) -> str:
    """Extract text from PDF file"""
    text = ""
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
    except Exception as e:
        logger.error(f"Error parsing {pdf_path}: {e}")
        return None

    return clean_text(text)

def clean_text(text: str) -> str:
    """Clean extracted text and remove non-printable characters"""
    if not text:
        return ""
    # Filter out non-printable characters (fix binary file grep issue)
    text = "".join(c for c in text if c.isprintable() or c in "\n\t")
    text = ' '.join(text.split())
    return text

def batch_parse_recursive(input_root: str, output_root: str):
    """Parse all PDFs in all batch subdirectories"""
    input_path = Path(input_root)
    output_path = Path(output_root)
    output_path.mkdir(parents=True, exist_ok=True)

    batch_folders = [f for f in input_path.iterdir() if f.is_dir()]
    
    for batch in batch_folders:
        logger.info(f"--- Parsing Batch: {batch.name} ---")
        dest_batch = output_path / batch.name
        dest_batch.mkdir(parents=True, exist_ok=True)
        
        pdf_files = list(batch.glob("*.pdf"))
        success = 0
        skipped_non_english = 0
        
        for pdf_file in pdf_files:
            text = parse_pdf(str(pdf_file))
            if text:
                if is_english(text):
                    output_file = dest_batch / f"{pdf_file.stem}.txt"
                    output_file.write_text(text, encoding='utf-8')
                    success += 1
                else:
                    skipped_non_english += 1
            
        logger.info(f"Batch {batch.name}: {success} English CVs parsed, {skipped_non_english} skipped (not English).")

if __name__ == "__main__":
    INPUT_DIR = "data/3_raw_pdfs"
    OUTPUT_DIR = "data/4_processed/raw_extracted"
    batch_parse_recursive(INPUT_DIR, OUTPUT_DIR)
