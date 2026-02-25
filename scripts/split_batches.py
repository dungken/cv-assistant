import os
import shutil
import random
from pathlib import Path

def finalize_distribution(anonymized_root, output_root):
    """Pick 1 common CV and 50 unique CVs per batch from the anonymized folders"""
    anon_path = Path(anonymized_root)
    root_path = Path(output_root)
    
    # Reset final distribution directory
    if root_path.exists():
        shutil.rmtree(root_path)
    root_path.mkdir(parents=True, exist_ok=True)
    
    batch_folders = [f for f in anon_path.iterdir() if f.is_dir() and f.name.startswith("Batch_")]
    
    # 1. Pick 01 common CV for Calibration from any batch
    all_files = []
    for batch in batch_folders:
        all_files.extend([(batch.name, f.name) for f in batch.glob("*.txt")])
    
    if not all_files:
        print("Error: No anonymized files found.")
        return

    random.seed(42) # For reproducibility
    common_batch, common_file = random.choice(all_files)
    print(f"Calibration CV selected: {common_file} (from {common_batch})")
    
    calib_path = root_path / "CV_CHUNG_CALIBRATION"
    calib_path.mkdir(parents=True, exist_ok=True)
    shutil.copy(anon_path / common_batch / common_file, calib_path / common_file)

    # 2. Fill batches (50 unique each)
    for batch in batch_folders:
        batch_folder = root_path / batch.name
        batch_folder.mkdir(parents=True, exist_ok=True)
        
        # Get all files in this batch except common
        available = [f.name for f in batch.glob("*.txt") if f.name != common_file]
        
        # Pick exactly 50
        if len(available) < 50:
            print(f"Warning: {batch.name} only has {len(available)} unique English CVs.")
            selected = available
        else:
            selected = random.sample(available, 50)
            
        for f in selected:
            shutil.copy(batch / f, batch_folder / f)
        
        print(f"Distributed {len(selected)} CVs to {batch.name}")

    print(f"\nDistribution complete in {output_root}")

if __name__ == "__main__":
    ANON_DIR = "data/4_processed/anonymized"
    FINAL_DIR = "data/5_distribution"
    finalize_distribution(ANON_DIR, FINAL_DIR)
