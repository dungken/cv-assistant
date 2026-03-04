import json
import os
import re
from pathlib import Path
from typing import List, Dict, Any, Tuple

def tokenize_with_offsets(text: str) -> List[Dict[str, Any]]:
    """Tokenize text and keep track of character offsets."""
    tokens = []
    # Tokenizer that splits on whitespace and punctuation
    for match in re.finditer(r'\S+', text):
        tokens.append({
            'text': match.group(),
            'start': match.start(),
            'end': match.end()
        })
    return tokens

def label_studio_to_bio(label_studio_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Convert Label Studio export to a list of tokenized samples with BIO tags."""
    dataset = []
    
    for item in label_studio_data:
        # Some items might not have annotations
        if not item.get('annotations'):
            continue
            
        # Get the first annotation result
        # (Assuming one annotator or we take the first completed)
        annotation = item['annotations'][0]
        results = annotation.get('result', [])
        
        # Get source text
        text = item['data'].get('text')
        if not text:
            continue
            
        # Tokenize
        tokens_info = tokenize_with_offsets(text)
        tokens = [t['text'] for t in tokens_info]
        ner_tags = ['O'] * len(tokens_info)
        
        # Sort results by start offset to handle entities properly
        sorted_results = sorted(results, key=lambda x: x['value']['start'])
        
        for entity in sorted_results:
            if entity['type'] != 'labels':
                continue
                
            e_start = entity['value']['start']
            e_end = entity['value']['end']
            label = entity['value']['labels'][0]
            
            # Find tokens that overlap with this entity
            first_token_idx = -1
            for i, t in enumerate(tokens_info):
                if t['start'] <= e_start < t['end']:
                    first_token_idx = i
                    break
            
            if first_token_idx == -1:
                # Handle edge case where e_start is exactly t['end'] or between tokens
                # This can happen with punctuation or leading/trailing spaces in labels
                for i, t in enumerate(tokens_info):
                    if t['start'] >= e_start:
                        first_token_idx = i
                        break
            
            if first_token_idx != -1:
                # Assign B-tag
                if ner_tags[first_token_idx] == 'O':
                    ner_tags[first_token_idx] = f"B-{label}"
                
                # Find subsequent tokens that are within the entity range
                for i in range(first_token_idx + 1, len(tokens_info)):
                    t = tokens_info[i]
                    if t['start'] < e_end:
                        if ner_tags[i] == 'O':
                             ner_tags[i] = f"I-{label}"
                    else:
                        break
        
        dataset.append({
            'id': item['id'],
            'tokens': tokens,
            'ner_tags': ner_tags
        })
        
    return dataset

def save_as_jsonl(dataset: List[Dict[str, Any]], output_path: str):
    """Save dataset in JSONL format."""
    with open(output_path, 'w', encoding='utf-8') as f:
        for entry in dataset:
            f.write(json.dumps(entry, ensure_ascii=False) + '\n')

def main():
    input_file = "data/annotated/Finance_Finished/Finance_Full_Hieu.json"
    output_file = "data/processed/annotated_hf/finance_hieu.jsonl"
    
    if not os.path.exists(input_file):
        print(f"Error: {input_file} not found.")
        return
        
    print(f"Loading {input_file}...")
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    print(f"Converting {len(data)} items...")
    hf_dataset = label_studio_to_bio(data)
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    print(f"Saving {len(hf_dataset)} processed samples to {output_file}...")
    save_as_jsonl(hf_dataset, output_file)
    print("Done!")

if __name__ == "__main__":
    main()
