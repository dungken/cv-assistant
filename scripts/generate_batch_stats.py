import os
import pandas as pd
from pathlib import Path

# Paths
REPORT_PATH = "data/1_source/CV_Classification_Report.csv"
DIST_DIR = "data/5_distribution"

def generate_stats():
    if not os.path.exists(REPORT_PATH):
        print(f"Error: Report not found at {REPORT_PATH}")
        return

    # Load report
    df_report = pd.read_csv(REPORT_PATH)
    # Mapping for quick lookup: ten_file -> metadata
    # We strip extensions for the key to match .txt files easily
    metadata_map = {}
    for _, row in df_report.iterrows():
        base = os.path.splitext(row['ten_file'])[0]
        metadata_map[base] = {
            'ngon_ngu': row['ngon_ngu'],
            'chuyen_nganh': row['chuyen_nganh'],
            'bo_cuc': row['bo_cuc'],
            'loai_file': row['loai_file']
        }

    dist_path = Path(DIST_DIR)
    batches = [d for d in dist_path.iterdir() if d.is_dir()]

    for batch in batches:
        print(f"Processing stats for {batch.name}...")
        files = list(batch.glob("*.txt"))
        
        batch_data = []
        for f in files:
            original_base = f.stem # ID-Filename
            
            meta = metadata_map.get(original_base, {
                'ngon_ngu': 'unknown',
                'chuyen_nganh': 'unknown',
                'bo_cuc': 'unknown',
                'loai_file': 'unknown'
            })
            
            entry = {'file_name': f.name}
            entry.update(meta)
            batch_data.append(entry)

        if batch_data:
            df_batch = pd.DataFrame(batch_data)
            # Reorder columns
            cols = ['file_name', 'ngon_ngu', 'chuyen_nganh', 'bo_cuc', 'loai_file']
            df_batch = df_batch[cols]
            
            output_file = batch / f"Batch_Summary_{batch.name}.csv"
            df_batch.to_csv(output_file, index=False, encoding='utf-8-sig')
            print(f"  Generated: {output_file}")

if __name__ == "__main__":
    generate_stats()
