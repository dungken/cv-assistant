import csv
import random
import os
import re
from pathlib import Path

def generate_cv_links(csv_path, samples_per_batch=300):
    prefix = "https://vieclamadmin.ueh.edu.vn"
    output_dir = Path("data/2_links")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Priority based patterns to avoid pollution
    # IT is listed last to act as a more specific catch-all for tech terms
    patterns = {
        "Batch_3_Finance": re.compile(r"finance|audit|accountant|ke-toan|bank|kiem-toan|tai-chinh", re.I),
        "Batch_2_Economy": re.compile(r"marketing|sale|mar|event|brand|account|business|kinh-doanh", re.I),
        "Batch_4_HR_Logistics": re.compile(r"hr|human-resource|admin|nhan-su|logistics|supply|import|export|xuat-nhap-khau|kho-bai", re.I),
        "Batch_1_IT": re.compile(r"software|developer|engineer|tech|web|android|ios|programmer|network|cloud|security|sysadmin|frontend|backend|fullstack|react|java|python|aws|azure|tester|testing|qa|qc|devops|ai|ml|artificial.intelligence|machine.learning|data.scientist|data.engineer|\.(js|py|cpp|java|sql|node)\b|\b(it|data)\b|[-_](it|data)[-_]", re.I)
    }

    # Initialize results
    batch_results = {name: [] for name in patterns.keys()}
    english_hints = ["cv", "resume", "recruit", "intern", "engineer", "analyst", "manager", "specialist"]

    with open(csv_path, mode='r', encoding='utf-8') as f:
        reader = csv.reader(f)
        for row in reader:
            if not row: continue
            path = row[0]
            if not path.lower().endswith('.pdf'): continue
            
            # Categorize based on batch regex (priority by dict order)
            for name, pattern in patterns.items():
                if pattern.search(path):
                    # Scoring for English bias (simple check)
                    score = sum(1 for hint in english_hints if hint in path.lower())
                    batch_results[name].append((score, prefix + path))
                    break

    # Sample and Save
    print("=== Generating Refined Batch Link Files ===")
    for batch_name, links in batch_results.items():
        links.sort(key=lambda x: x[0], reverse=True)
        candidates = links[:max(samples_per_batch, 600)]
        random.shuffle(candidates)
        sampled = candidates[:min(len(candidates), samples_per_batch)]

        output_file = output_dir / f"{batch_name}_links.txt"
        with open(output_file, 'w') as out_f:
            for _, link in sampled:
                out_f.write(link + "\n")
        
        print(f"Batch: {batch_name} -> {len(sampled)} links saved to {output_file}")

if __name__ == "__main__":
    CSV_FILE = "data/1_source/DatasetCVs.csv"
    samples_per_category = 300
    generate_cv_links(CSV_FILE, samples_per_batch=samples_per_category)
