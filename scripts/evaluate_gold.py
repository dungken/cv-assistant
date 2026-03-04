import torch
import json
import numpy as np
from transformers import AutoTokenizer, AutoModelForTokenClassification, pipeline
from seqeval.metrics import classification_report, f1_score
from pathlib import Path

LABEL_LIST = [
    "O", "B-PER", "I-PER", "B-ORG", "I-ORG", "B-DATE", "I-DATE",
    "B-LOC", "I-LOC", "B-SKILL", "I-SKILL", "B-DEGREE", "I-DEGREE",
    "B-MAJOR", "I-MAJOR", "B-JOB_TITLE", "I-JOB_TITLE", "B-PROJECT",
    "I-PROJECT", "B-CERT", "I-CERT"
]
ID_TO_LABEL = {i: label for i, label in enumerate(LABEL_LIST)}

def evaluate_gold(model_path: str, gold_file: str):
    print(f"Loading model from {model_path}...")
    tokenizer = AutoTokenizer.from_pretrained(model_path)
    model = AutoModelForTokenClassification.from_pretrained(model_path)
    
    # We use a lower-level approach for precise token evaluation
    device = torch.device("cpu")
    model.to(device)
    model.eval()

    print(f"Loading gold standard from {gold_file}...")
    with open(gold_file, 'r') as f:
        gold_samples = [json.loads(line) for line in f]

    all_true = []
    all_pred = []

    for sample in gold_samples:
        tokens = sample['tokens']
        true_tags = sample['ner_tags']
        
        inputs = tokenizer(tokens, is_split_into_words=True, return_tensors="pt", truncation=True, max_length=512)
        with torch.no_grad():
            outputs = model(**inputs).logits
        
        predictions = torch.argmax(outputs, dim=2).squeeze().tolist()
        word_ids = inputs.word_ids()
        
        # Align predictions with original tokens
        # (Same logic as compute_metrics in train_ner.py)
        sample_pred = []
        previous_word_idx = None
        for i, word_idx in enumerate(word_ids):
            if word_idx is None:
                continue
            if word_idx != previous_word_idx:
                sample_pred.append(ID_TO_LABEL[predictions[i]])
            previous_word_idx = word_idx
            
        # Ensure lengths match (truncate if necessary due to tokenizer max_length)
        min_len = min(len(true_tags), len(sample_pred))
        all_true.append(true_tags[:min_len])
        all_pred.append(sample_pred[:min_len])

    print("\n--- Gold Standard Classification Report ---")
    print(classification_report(all_true, all_pred))

if __name__ == "__main__":
    import sys
    checkpoint = sys.argv[1] if len(sys.argv) > 1 else "models/ner/checkpoint"
    evaluate_gold(checkpoint, "data/processed/gold_standard.jsonl")
