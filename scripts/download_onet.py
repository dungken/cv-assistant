import os
import requests
import zipfile
import io
from pathlib import Path

def download_onet_db(output_dir: str):
    """Download O*NET 28.1 Database (Text)"""
    url = "https://www.onetcenter.org/dl_files/database/db_28_1_text.zip"
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    print(f"Downloading from {url}...")
    try:
        response = requests.get(url)
        response.raise_for_status()
        
        print("Extracting...")
        with zipfile.ZipFile(io.BytesIO(response.content)) as z:
            # Extract only necessary files to save space/time if needed
            # But extracting all is safer for finding the right path
            z.extractall(output_path)
            
        print(f"O*NET database downloaded to {output_path}")
        
    except Exception as e:
        print(f"Error downloading O*NET data: {e}")

if __name__ == "__main__":
    download_onet_db("knowledge_base/onet")
