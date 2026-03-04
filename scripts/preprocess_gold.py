import json
import os
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from scripts.preprocess_labels import label_studio_to_bio, save_as_jsonl

def main():
    input_file = "data/gold_standard.json"
    output_file = "data/processed/gold_standard.jsonl"
    
    if not os.path.exists(input_file):
        print(f"Error: {input_file} not found.")
        return
        
    print(f"Loading {input_file}...")
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    print(f"Converting {len(data)} items to BIO format...")
    hf_dataset = label_studio_to_bio(data)
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    print(f"Saving {len(hf_dataset)} processed samples to {output_file}...")
    save_as_jsonl(hf_dataset, output_file)
    print("Gold standard preprocessing complete!")

if __name__ == "__main__":
    main()
