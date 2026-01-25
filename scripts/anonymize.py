import re
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def anonymize_text(text: str) -> str:
    """Remove PII from CV text using Regex patterns"""
    if not text:
        return ""

    # Email addresses
    # Pattern: something@something.domain
    text = re.sub(
        r'[\w\.-]+@[\w\.-]+\.\w+',
        '[EMAIL]',
        text
    )

    # Phone numbers (Vietnam & Generic)
    # Supports: 090 123 4567, +84 90 123 4567, 090-123-4567, etc.
    text = re.sub(
        r'(\+?84|0)(3|5|7|8|9|1[2|6|8|9])([0-9]{8})\b', # Basic VN mobile
        '[PHONE]',
        text
    )
    # Generic phone fallback (3-4 digits groups)
    text = re.sub(
        r'\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b',
        '[PHONE]',
        text
    )

    # Links (LinkedIn, GitHub, etc.) to generic placeholders
    # This prevents annotators from clicking through to see real profiles
    text = re.sub(
        r'(https?://)?(www\.)?linkedin\.com/in/[\w-]+',
        '[LINKEDIN]',
        text
    )
    text = re.sub(
        r'(https?://)?(www\.)?github\.com/[\w-]+',
        '[GITHUB]',
        text
    )

    return text

def batch_anonymize(input_dir: str, output_dir: str):
    """Anonymize all text files in input directory"""
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    results = {"processed": 0, "failed": 0}
    
    files = list(input_path.glob("*.txt"))
    logger.info(f"Found {len(files)} files to anonymize.")

    for txt_file in files:
        try:
            text = txt_file.read_text(encoding='utf-8')
            anon_text = anonymize_text(text)
            
            output_file = output_path / txt_file.name
            output_file.write_text(anon_text, encoding='utf-8')
            results["processed"] += 1
        except Exception as e:
            logger.error(f"Failed to anonymize {txt_file.name}: {e}")
            results["failed"] += 1

    return results

if __name__ == "__main__":
    INPUT_DIR = "data/processed"
    OUTPUT_DIR = "data/processed/anonymized" # Create a subdir or separate folder
    
    logger.info("Starting Anonymization...")
    stats = batch_anonymize(INPUT_DIR, OUTPUT_DIR)
    logger.info(f"Complete. Processed: {stats['processed']}, Failed: {stats['failed']}")
    logger.info(f"Anonymized files saved to: {OUTPUT_DIR}")
