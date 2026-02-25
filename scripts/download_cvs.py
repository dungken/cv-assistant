import os
import requests
import time
from pathlib import Path

def download_cvs_batched(links_dir, raw_output_dir):
    """Download CVs into batch-specific folders"""
    links_path = Path(links_dir)
    raw_path = Path(raw_output_dir)
    raw_path.mkdir(parents=True, exist_ok=True)
    
    link_files = list(links_path.glob("*_links.txt"))
    if not link_files:
        print(f"No link files found in {links_dir}")
        return

    for link_file in link_files:
        batch_name = link_file.stem.replace("_links", "")
        batch_dest = raw_path / batch_name
        batch_dest.mkdir(parents=True, exist_ok=True)
        
        links = []
        with open(link_file, 'r') as f:
            links = [line.strip() for line in f if line.strip().startswith("https://")]

        print(f"\n--- Processing {batch_name} ({len(links)} links) ---")
        success = 0
        failed = 0

        for i, link in enumerate(links):
            file_name = link.split('/')[-1]
            if not file_name.lower().endswith('.pdf'):
                file_name += ".pdf"
                
            dest_file = batch_dest / file_name
            
            if dest_file.exists():
                continue

            try:
                # Moderate pace to avoid server blocks
                response = requests.get(link, timeout=15)
                if response.status_code == 200:
                    dest_file.write_bytes(response.content)
                    success += 1
                else:
                    print(f"Failed {file_name}: Status {response.status_code}")
                    failed += 1
            except Exception as e:
                print(f"Error {file_name}: {e}")
                failed += 1
            
            if i % 10 == 0:
                print(f"Progress: {i}/{len(links)}...")
            
            time.sleep(0.3)

        print(f"Batch {batch_name} Result: Success {success}, Failed {failed}")

if __name__ == "__main__":
    LINKS_DIR = "data/2_links"
    RAW_DIR = "data/3_raw_pdfs"
    download_cvs_batched(LINKS_DIR, RAW_DIR)
