import os
import json
import re
from pathlib import Path
from transformers import pipeline, AutoTokenizer, AutoModelForTokenClassification
import torch

# --- Configuration ---
MODEL_PATH = "models/ner/final"
INPUT_DIRS = [Path("data/raw/seed_jds"), Path("data/raw/synthetic_jds")]
OUTPUT_FILE = Path("data/processed/annotated_hf/jd_train.jsonl")
LABEL_LIST = [
    "O", "B-PER", "I-PER", "B-ORG", "I-ORG", "B-DATE", "I-DATE",
    "B-LOC", "I-LOC", "B-SKILL", "I-SKILL", "B-DEGREE", "I-DEGREE",
    "B-MAJOR", "I-MAJOR", "B-JOB_TITLE", "I-JOB_TITLE", "B-PROJECT",
    "I-PROJECT", "B-CERT", "I-CERT"
]
ID2LABEL = {i: label for i, label in enumerate(LABEL_LIST)}

def main():
    print(f"Loading NER model from {MODEL_PATH}...")
    tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH)
    model = AutoModelForTokenClassification.from_pretrained(MODEL_PATH)
    
    # Simple pipeline for inference
    nlp = pipeline("ner", model=model, tokenizer=tokenizer, aggregation_strategy="none")
    
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    
    jd_files = []
    for d in INPUT_DIRS:
        if d.exists():
            jd_files.extend(list(d.glob("*.txt")))
    
    jd_files = sorted(jd_files)
    print(f"Processing {len(jd_files)} JD files from {INPUT_DIRS}...")
    
    dataset = []
    
    for jd_file in jd_files:
        print(f"  Labeling {jd_file.name}...")
        text = jd_file.read_text(encoding="utf-8").strip()
        if not text:
            continue
            
        # Tokenize by whitespace as base (standard for HuggingFace NER datasets)
        # We need mapping from text to tokens for alignment
        raw_tokens = re.findall(r'\S+|\s+', text) # Preserve whitespace for reconstruction if needed
        # Actually, standard NER datasets often just use whitespace splitting
        tokens = text.split()
        
        # We run the pipeline on the full text
        ner_results = nlp(text)
        
        # Build BIO tags for the tokens (Use 0 for 'O')
        ner_tags = [0] * len(tokens)
        
        # Map character offsets to tokens
        token_offsets = []
        current_offset = 0
        for token in tokens:
            start = text.find(token, current_offset)
            end = start + len(token)
            token_offsets.append((start, end))
            current_offset = end
            
        # Map model results to tokens
        LABEL_MAP = {label: i for i, label in enumerate(LABEL_LIST)}
        
        for res in ner_results:
            # Get the label name from the model output
            ent_type = res['entity']
            if 'LABEL_' in ent_type:
                label_id = int(ent_type.split('_')[-1])
                label_name = model.config.id2label.get(label_id, "O")
            else:
                label_name = ent_type
                
            if label_name == "O":
                continue
                
            start, end = res['start'], res['end']
            
            # Find tokens that overlap with this entity
            for i, (ts, te) in enumerate(token_offsets):
                if ts < end and te > start:
                    target_tag = label_name
                    # If this is not the first token of the entity, convert B- to I-
                    if ts >= start + 2: # heuristic for continuation
                         tag_core = label_name.split('-', 1)[-1]
                         target_tag = f"I-{tag_core}"
                    
                    # Convert string tag to integer ID
                    ner_tags[i] = LABEL_MAP.get(target_tag, 0)

        dataset.append({
            "id": jd_file.stem,
            "tokens": tokens,
            "ner_tags": ner_tags # Now integers
        })

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        for item in dataset:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")
            
    print(f"Successfully saved {len(dataset)} annotated JDs to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
