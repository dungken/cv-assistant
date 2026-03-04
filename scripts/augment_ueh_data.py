import json
import random
from pathlib import Path

# UEH Context Data
DEGREES = [
    "Bachelor", "Bachelor of Arts", "Bachelor of Science", "B.A.", "B.S.",
    "BBA", "Bachelor of Business Administration", "Master", "Master of Science",
    "M.S.", "MBA", "Cử nhân", "Thạc sĩ"
]

MAJORS = [
    "Finance", "Accounting", "Business Administration", "Marketing",
    "International Business", "Economics", "Management Information Systems",
    "Data Science", "Logistics", "Supply Chain Management", "Commercial Law",
    "Computer Science", "Information Technology", "Software Engineering",
    "Mechanical Engineering", "Graphic Design", "Human Resources",
    "Tài chính", "Kế toán", "Quản trị kinh doanh", "Kinh doanh quốc tế",
    "Công nghệ thông tin", "Khoa học máy tính"
]

UNIVERSITIES = [
    "University of Economics Ho Chi Minh City", "UEH",
    "Foreign Trade University", "FTU",
    "RMIT University", "RMIT",
    "Vietnam National University", "VNU",
    "Ho Chi Minh City University of Technology", "HCMUT",
    "National Economics University", "NEU",
    "Harvard University", "Stanford University",
    "Đại học Bách Khoa", "Đại học Ngoại thương", "Đại học Quốc gia"
]

TEMPLATES = [
    # English
    "{degree} in {major} - {university}",
    "{degree} of {major} | {university}",
    "Major: {major} | {university}",
    "{university} | {degree} in {major}",
    "Education: {degree}, {major} at {university}",
    "{major} Degree from {university}",
    # Vietnamese
    "{degree} chuyên ngành {major} - {university}",
    "Trường {university} - {degree} {major}",
    "Ngành {major} - {university}",
    "Học vấn: {university}, {degree} {major}"
]

def generate_synthetic_data(num_samples=100) -> list:
    """Generates synthetic BIO-tagged data for Degree/Major/Org."""
    synthetic_data = []
    
    for i in range(num_samples):
        degree = random.choice(DEGREES)
        major = random.choice(MAJORS)
        uni = random.choice(UNIVERSITIES)
        template = random.choice(TEMPLATES)
        
        text = template.format(degree=degree, major=major, university=uni)
        
        # Simple whitespace tokenizer for synthetic data
        tokens = text.split()
        ner_tags = ["O"] * len(tokens)
        
        # Helper to tag a span
        def tag_span(target_str, label):
            target_tokens = target_str.split()
            # Find the target sequence in the main tokens
            for j in range(len(tokens) - len(target_tokens) + 1):
                if tokens[j:j+len(target_tokens)] == target_tokens:
                    ner_tags[j] = f"B-{label}"
                    for k in range(1, len(target_tokens)):
                        ner_tags[j+k] = f"I-{label}"
                    break
        
        if "{degree}" in template: tag_span(degree, "DEGREE")
        if "{major}" in template: tag_span(major, "MAJOR")
        if "{university}" in template: tag_span(uni, "ORG")
            
        synthetic_data.append({
            "id": 1000 + i,
            "tokens": tokens,
            "ner_tags": ner_tags
        })
        
    return synthetic_data

if __name__ == "__main__":
    # Generate 150 synthetic samples
    print("Generating 150 synthetic UEH Education samples...")
    syn_data = generate_synthetic_data(150)
    
    output_path = "data/processed/annotated_hf/synthetic_ueh.jsonl"
    with open(output_path, "w", encoding="utf-8") as f:
        for item in syn_data:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")
            
    print(f"Saved synthetic data to {output_path}")
    print("Sample:")
    print(json.dumps(syn_data[0], indent=2, ensure_ascii=False))
