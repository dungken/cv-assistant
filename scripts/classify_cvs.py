import csv
import os
from pathlib import Path
import pdfplumber
import logging
from collections import Counter

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

import re

# Precise Regex Patterns
SECTORS = {
    "Finance": re.compile(r"finance|audit|accountant|ke-toan|bank|kiem-toan|tai-chinh", re.I),
    "Economy": re.compile(r"marketing|sale|mar|event|brand|account|business|kinh-doanh", re.I),
    "HR_Logistics": re.compile(r"hr|human-resource|admin|nhan-su|logistics|supply|import|export|xuat-nhap-khau|kho-bai", re.I),
    "IT": re.compile(r"software|developer|engineer|tech|web|android|ios|programmer|network|cloud|security|sysadmin|frontend|backend|fullstack|react|java|python|aws|azure|tester|testing|qa|qc|devops|ai|ml|artificial.intelligence|machine.learning|data.scientist|data.engineer|\.(js|py|cpp|java|sql|node)\b|\b(it|data)\b|[-_](it|data)[-_]", re.I)
}

EN_KEYWORDS = ["education", "experience", "skills", "summary", "university", "project", "language", "profile", "contact", "github", "stack", "technologies"]
VN_KEYWORDS = ["học vấn", "kinh nghiệm", "kỹ năng", "tóm tắt", "đại học", "dự án", "ngôn ngữ", "thông tin", "liên hệ"]

def detect_language(text):
    if not text: return "unknown"
    text_lower = text.lower()
    en_score = sum(1 for kw in EN_KEYWORDS if kw in text_lower)
    vn_score = sum(1 for kw in VN_KEYWORDS if kw in text_lower)
    
    if en_score > 3 and vn_score < 2: return "en"
    if vn_score > 3 and en_score < 2: return "vi"
    if en_score > 1 and vn_score > 1: return "mixed"
    return "en" if en_score >= vn_score else "vi"

def detect_major(path):
    for major, pattern in SECTORS.items():
        if pattern.search(path):
            return major
    return "Other"

def analyze_layout_and_type(pdf_path):
    """Estimate layout columns and file type (text vs scan)"""
    try:
        with pdfplumber.open(pdf_path) as pdf:
            if not pdf.pages:
                return "unknown", "unknown"
            
            first_page = pdf.pages[0]
            words = first_page.extract_words()
            
            if not words:
                # If no text extracted, check for images/curves
                if first_page.images or first_page.curves:
                    return "n/a", "scan/img"
                return "n/a", "unknown"

            # Type: Text-based if significant words found
            file_type = "pdf base text"
            if len(words) < 50 and (first_page.images or first_page.curves):
                 file_type = "scan"

            # Layout: Histogram of x0 (left edge)
            x0_coords = [round(w['x0'] / 50) * 50 for w in words] # Bucket by 50 units
            counts = Counter(x0_coords)
            
            # Significant peaks (at least 15% of words)
            peaks = [val for val, count in counts.items() if count > len(words) * 0.15]
            
            if len(peaks) >= 2:
                layout = "2 cột"
            elif len(peaks) == 1:
                layout = "1 cột"
            else:
                layout = "phức tạp"
            
            return layout, file_type

    except Exception as e:
        logger.error(f"Error analyzing {pdf_path}: {e}")
        return "error", "error"

def classify_all(csv_input, csv_output, raw_data_dir=None):
    results = []
    
    # Pre-index local files for O(1) lookup
    local_files_map = {}
    if raw_data_dir:
        logger.info(f"Indexing local files in {raw_data_dir}...")
        for p in Path(raw_data_dir).rglob("*.pdf"):
            local_files_map[p.name] = p
        logger.info(f"Indexed {len(local_files_map)} local files.")

    with open(csv_input, mode='r', encoding='utf-8') as f:
        reader = csv.reader(f)
        for i, row in enumerate(reader):
            if not row: continue
            path = row[0]
            file_name = path.split('/')[-1]
            
            major = detect_major(path)
            
            # Use indexed path
            local_path = local_files_map.get(file_name)
            
            lang = "detecting..."
            layout = "remote"
            f_type = "remote"
            
            if local_path and local_path.exists():
                try:
                    with pdfplumber.open(local_path) as pdf:
                        text = ""
                        for p in pdf.pages[:2]:
                            text += p.extract_text() or ""
                        lang = detect_language(text)
                    
                    layout, f_type = analyze_layout_and_type(local_path)
                except:
                    pass
            else:
                lang = "en" if any(kw in file_name.lower() for kw in ["cv", "resume", "en", "eng"]) else "vi/detect_later"

            results.append({
                "stt": i + 1,
                "ten_file": file_name,
                "ngon_ngu": lang,
                "chuyen_nganh": major,
                "bo_cuc": layout,
                "loai_file": f_type
            })
            
            if i % 100 == 0:
                print(f"Processed {i} entries...")

    # Write Results
    fieldnames = ["stt", "ten_file", "ngon_ngu", "chuyen_nganh", "bo_cuc", "loai_file"]
    with open(csv_output, mode='w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)
    
    print(f"\nClassification report saved to {csv_output}")

if __name__ == "__main__":
    CSV_IN = "data/1_source/DatasetCVs.csv"
    CSV_OUT = "data/1_source/CV_Classification_Report.csv"
    RAW_DIR = "data/3_raw_pdfs" # Check locally first
    classify_all(CSV_IN, CSV_OUT, RAW_DIR)
