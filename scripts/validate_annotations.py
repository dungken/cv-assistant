import json
import os
from collections import Counter

def validate_annotations(json_file):
    print(f"Validating {json_file}...")
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    total_items = len(data)
    annotated_items = 0
    entity_counts = Counter()
    issues = []

    for item in data:
        if not item.get('annotations'):
            issues.append(f"Item {item['id']}: No annotations found.")
            continue
        
        annotated_items += 1
        annotation = item['annotations'][0]
        results = annotation.get('result', [])
        
        if not results:
            issues.append(f"Item {item['id']}: Annotation exists but has no labels.")
            continue

        text = item['data'].get('text', '')
        
        for result in results:
            if result['type'] != 'labels':
                continue
            
            val = result['value']
            start = val['start']
            end = val['end']
            annotated_text = val['text']
            labels = val['labels']
            
            # Check label distribution
            for label in labels:
                entity_counts[label] += 1
            
            # Check offset consistency
            original_substring = text[start:end]
            if original_substring != annotated_text:
                issues.append(f"Item {item['id']}: Offset mismatch. Label text '{annotated_text}' vs Original '{original_substring}'")

    print("\n--- Statistics ---")
    print(f"Total Items: {total_items}")
    print(f"Annotated Items: {annotated_items}")
    print("\nEntity Distribution:")
    for label, count in entity_counts.most_common():
        print(f"  {label}: {count}")
    
    print("\n--- Issues ---")
    if not issues:
        print("No issues found!")
    else:
        for issue in issues[:20]: # Show first 20
            print(f"- {issue}")
        if len(issues) > 20:
            print(f"... and {len(issues) - 20} more issues.")

if __name__ == "__main__":
    input_file = "data/annotated/Finance_Finished/Finance_Full_Hieu.json"
    if os.path.exists(input_file):
        validate_annotations(input_file)
    else:
        print(f"File {input_file} not found.")
