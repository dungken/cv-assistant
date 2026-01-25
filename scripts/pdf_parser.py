import pdfplumber
import os
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

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
    """Clean extracted text"""
    if not text:
        return ""
    # Remove multiple spaces
    text = ' '.join(text.split())
    # Remove multiple newlines (optional, depending on downstream tasks)
    # text = '\n'.join(line.strip() for line in text.split('\n') if line.strip())
    return text

def batch_parse(input_dir: str, output_dir: str):
    """Parse all PDFs in directory"""
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    results = {"success": 0, "failed": 0, "failed_files": []}

    pdf_files = list(input_path.glob("*.pdf"))
    logger.info(f"Found {len(pdf_files)} PDF files in {input_dir}")

    for pdf_file in pdf_files:
        logger.info(f"Processing: {pdf_file.name}")
        text = parse_pdf(str(pdf_file))
        if text:
            output_file = output_path / f"{pdf_file.stem}.txt"
            output_file.write_text(text, encoding='utf-8')
            results["success"] += 1
            logger.info(f"Saved to: {output_file}")
        else:
            results["failed"] += 1
            results["failed_files"].append(pdf_file.name)
            logger.warning(f"Failed to extract text from: {pdf_file.name}")

    return results

if __name__ == "__main__":
    # Default paths
    INPUT_DIR = "data/raw"
    OUTPUT_DIR = "data/processed"
    
    # Create test dummy if needed
    if not os.path.exists(INPUT_DIR):
        os.makedirs(INPUT_DIR)
        
    results = batch_parse(INPUT_DIR, OUTPUT_DIR)
    logger.info(f"Parsed: {results['success']}, Failed: {results['failed']}")
    if results["failed_files"]:
        logger.info(f"Failed files: {results['failed_files']}")
