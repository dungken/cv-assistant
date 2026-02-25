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
    text = re.sub(
        r'[\w\.-]+@[\w\.-]+\.\w+',
        '[EMAIL]',
        text
    )

    # Phone numbers (Vietnam & Generic)
    # Handles: 0918 573 026, 0918.573.026, +84918573026, 0918573026, etc.
    text = re.sub(
        r'(\+?84|0)(3|5|7|8|9|1[2|6|8|9])([\s\.]?[0-9]){8}\b',
        '[PHONE]',
        text
    )
    # Generic 10-digit formats with separators
    text = re.sub(
        r'\b\d{3,4}[-.\s]?\d{3}[-.\s]?\d{3,4}\b',
        '[PHONE]',
        text
    )

    # Links (LinkedIn, GitHub)
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

def batch_anonymize_recursive(input_root: str, output_root: str):
    """Anonymize all text files in all batch subdirectories"""
    input_path = Path(input_root)
    output_path = Path(output_root)
    output_path.mkdir(parents=True, exist_ok=True)

    # Look for batch folders like Batch_1_IT
    batch_folders = [f for f in input_path.iterdir() if f.is_dir()]
    
    for batch in batch_folders:
        logger.info(f"--- Anonymizing Batch: {batch.name} ---")
        dest_batch = output_path / batch.name
        dest_batch.mkdir(parents=True, exist_ok=True)
        
        txt_files = list(batch.glob("*.txt"))
        success = 0
        
        for txt_file in txt_files:
            try:
                text = txt_file.read_text(encoding='utf-8')
                anon_text = anonymize_text(text)
                output_file = dest_batch / txt_file.name
                output_file.write_text(anon_text, encoding='utf-8')
                success += 1
            except Exception as e:
                logger.error(f"Failed to anonymize {txt_file.name}: {e}")

        logger.info(f"Batch {batch.name}: {success} files anonymized.")

if __name__ == "__main__":
    INPUT_DIR = "data/4_processed/raw_extracted"
    OUTPUT_DIR = "data/4_processed/anonymized"
    
    logger.info("Starting Recursive Anonymization...")
    batch_anonymize_recursive(INPUT_DIR, OUTPUT_DIR)
