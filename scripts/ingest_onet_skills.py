import chromadb
from chromadb.config import Settings
import os
import pandas as pd
from pathlib import Path
import logging
import sys

# Add project root to path for shared imports
sys.path.append(str(Path(__file__).parent.parent))

from shared.db.chroma_client import get_chroma_client, get_collection
# from shared.constants import COLLECTION_JOBS # We'll create a new one though

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

COLLECTION_SKILLS = "onet_skills"

def create_collection(client, name: str):
    """Create or get collection with cosine similarity"""
    return client.get_or_create_collection(
        name=name,
        metadata={"hnsw:space": "cosine"}
    )

def ingest_general_skills(collection, onet_db_dir: Path):
    """Ingest skills from Skills.txt"""
    skills_file = onet_db_dir / "Skills.txt"
    if not skills_file.exists():
        logger.error(f"Skills file not found: {skills_file}")
        return

    # O*NET Skills.txt is tab-separated
    df = pd.read_csv(skills_file, sep="\t")
    
    # We only want unique Element Names (the actual skill name)
    # The file has multiple entries per skill (for different occupations)
    unique_skills = df[['Element Name']].drop_duplicates()
    
    logger.info(f"Uploading {len(unique_skills)} general skills...")
    
    documents = []
    metadatas = []
    ids = []
    
    for _, row in unique_skills.iterrows():
        skill_name = row['Element Name']
        documents.append(skill_name)
        metadatas.append({"type": "general_skill", "source": "ONET_Skills"})
        ids.append(f"skill_{skill_name.lower().replace(' ', '_')}")
        
    # Batch update
    if documents:
        collection.upsert(documents=documents, metadatas=metadatas, ids=ids)

def ingest_tech_skills(collection, onet_db_dir: Path):
    """Ingest examples from Technology Skills.txt"""
    tech_file = onet_db_dir / "Technology Skills.txt"
    if not tech_file.exists():
        logger.error(f"Tech skills file not found: {tech_file}")
        return

    df = pd.read_csv(tech_file, sep="\t")
    
    # We want Example values (e.g., Python, Adobe Acrobat)
    # Filter unique technology examples
    unique_tech = df[['Example']].drop_duplicates()
    
    logger.info(f"Uploading {len(unique_tech)} technology skills...")
    
    documents = []
    metadatas = []
    ids = []
    
    for _, row in unique_tech.iterrows():
        tech_name = str(row['Example'])
        if not tech_name or tech_name == 'nan':
            continue
            
        documents.append(tech_name)
        metadatas.append({"type": "tech_skill", "source": "ONET_Tech"})
        # Avoid ID collisions with general skills, use tech_ prefix
        ids.append(f"tech_{tech_name.lower().replace(' ', '_').replace('/', '_')}")
        
    # Batch update in chunks to avoid large requests
    batch_size = 500
    for i in range(0, len(documents), batch_size):
        collection.upsert(
            documents=documents[i:i+batch_size],
            metadatas=metadatas[i:i+batch_size],
            ids=ids[i:i+batch_size]
        )

import argparse

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ingest O*NET skills into ChromaDB")
    parser.add_argument("--force", action="store_true", help="Force ingestion even if data exists")
    args = parser.parse_args()

    # Initialize client
    client = get_chroma_client()
    collection = create_collection(client, COLLECTION_SKILLS)
    
    # Optimization: Skip if data already exists
    current_count = collection.count()
    if current_count > 0 and not args.force:
        logger.info(f"💾 Collection '{COLLECTION_SKILLS}' already contains {current_count} items. Skipping ingestion.")
        logger.info("Use --force if you need to re-ingest the data.")
        sys.exit(0)
    # Locate O*NET data
    onet_base = Path("knowledge_base/onet")
    try:
        onet_db_dir = list(onet_base.glob("db_*_text"))[0]
        
        logger.info("Starting O*NET Skill Intelligence Ingestion...")
        ingest_general_skills(collection, onet_db_dir)
        ingest_tech_skills(collection, onet_db_dir)
        logger.info(f"Finished! Total items in {COLLECTION_SKILLS}: {collection.count()}")
        
    except IndexError:
        logger.error("O*NET data directory (db_*_text) not found in knowledge_base/onet")
