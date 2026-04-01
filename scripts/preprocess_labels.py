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

def process_file(input_file: str, output_file: str):
    """Process a single Label Studio JSON file and save as Hugging Face JSONL."""
    if not os.path.exists(input_file):
        print(f"Error: {input_file} not found.")
        return
        
    print(f"Loading {input_file}...")
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    print(f"  Converting {len(data)} items...")
    hf_dataset = label_studio_to_bio(data)
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    print(f"  Saving {len(hf_dataset)} processed samples to {output_file}...")
    save_as_jsonl(hf_dataset, output_file)

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Preprocess Label Studio JSON exports to HF JSONL format.")
    parser.add_argument("--input_dir", default="data/annotated", help="Directory containing Label Studio JSON exports")
    parser.add_argument("--output_dir", default="data/processed/annotated_hf", help="Directory to save HF JSONL files")
    args = parser.parse_args()

    input_path = Path(args.input_dir)
    output_path = Path(args.output_dir)

    # Process all .json files in input_dir and its subdirectories
    json_files = list(input_path.glob("**/*.json"))
    
    if not json_files:
        print(f"No .json files found in {args.input_dir}")
        return

    print(f"Found {len(json_files)} JSON files. Starting batch processing...")
    
    for json_file in json_files:
        # Avoid processing files that are actually output or metadata
        if "gold_standard" in json_file.name.lower() or "distribution" in json_file.parts:
            continue
            
        # Create a matching output filename
        # e.g., Finance_Finished/Finance_Full_Hieu.json -> finance_full_hieu.jsonl
        rel_path = json_file.relative_to(input_path)
        output_file_name = rel_path.name.lower().replace(".json", ".jsonl")
        
        # If the file is in a subdirectory, we might want to preserve some naming
        if len(rel_path.parts) > 1:
             output_file_name = f"{rel_path.parent.name.lower()}_{output_file_name}"
             
        final_output_path = output_path / output_file_name
        
        process_file(str(json_file), str(final_output_path))
    
    print("\nAll files processed successfully!")

if __name__ == "__main__":
    main()
