import requests
import os
import json

def test_structural_parsing(pdf_path, api_url="http://localhost:5005/parse-cv"):
    if not os.path.exists(pdf_path):
        print(f"Error: File {pdf_path} not found.")
        return

    print(f"Testing structural parsing for: {pdf_path}")
    
    with open(pdf_path, 'rb') as f:
        files = {'file': (os.path.basename(pdf_path), f, 'application/pdf')}
        try:
            r = requests.post(api_url, files=files, timeout=30)
            r.raise_for_status()
            data = r.json()
            
            print("\n--- Structured Response ---")
            print(f"Status: {data.get('status')}")
            print(f"Summary: {data.get('summary', '')[:100]}...")
            
            print(f"\nExperience Items: {len(data.get('experience', []))}")
            for item in data.get('experience', []):
                print(f"- {item.get('anchor')}")
                # print(f"  Entities: {len(item.get('entities', []))}")

            print(f"\nProject Items: {len(data.get('projects', []))}")
            for item in data.get('projects', []):
                print(f"- {item.get('anchor')}")
                
            print(f"\nSkills Categories: {list(data.get('skills', {}).keys())}")
            
            # Save output for inspection
            output_file = "structural_output_test.json"
            with open(output_file, 'w', encoding='utf-8') as f_out:
                json.dump(data, f_out, indent=2, ensure_ascii=False)
            print(f"\nFull response saved to {output_file}")
            
        except Exception as e:
            print(f"Request failed: {e}")

if __name__ == "__main__":
    PDF_FILE = "/home/dungken/Desktop/Workspace/utc2/cv_assistant/data/3_raw_pdfs/Batch_1_IT/158393-quach-le-nhat-quang-quach-le-nhat-quang-intern-software-engineer.pdf"
    test_structural_parsing(PDF_FILE)
