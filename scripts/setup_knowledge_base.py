import chromadb
from chromadb.config import Settings
import os
import pandas as pd
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))
from shared.db.chroma_client import get_chroma_client

def setup_chromadb():
    """Initialize ChromaDB with persistent storage"""
    return get_chroma_client()

def create_collection(client, name: str):
    """Create or get collection"""
    return client.get_or_create_collection(
        name=name,
        metadata={"hnsw:space": "cosine"}
    )

def parse_onet_files(onet_dir: str):
    """Parse Occupation and Skills files from O*NET"""
    onet_path = Path(onet_dir)
    db_dir = list(onet_path.glob("db_*_text"))[0] # Find extracted folder
    
    logger.info(f"Parsing O*NET data from {db_dir}...")
    
    # Load Occupations
    occ_file = db_dir / "Occupation Data.txt"
    occ_df = pd.read_csv(occ_file, sep="\t")
    
    # Load Skills (Optional - for enrichment)
    # This might be large, so we process it carefully or join
    # For MVP, we might just use Title + Description from Occupation Data
    
    documents = []
    metadatas = []
    ids = []
    
    for _, row in occ_df.iterrows():
        # Clean Description
        desc = str(row['Description']).strip() if pd.notna(row['Description']) else ""
        if not desc:
            continue
            
        # Create rich text representation
        text = f"Job Title: {row['Title']}\nDescription: {desc}"
        
        documents.append(text)
        metadatas.append({
            "type": "occupation",
            "code": row['O*NET-SOC Code'],
            "title": row['Title']
        })
        ids.append(f"occ_{row['O*NET-SOC Code']}")
        
    return documents, metadatas, ids

def ingest_onet_jobs(client, onet_dir: str):
    """Ingest O*NET occupation data"""
    collection = create_collection(client, "onet_jobs")
    
    # Check if empty (dumb check for now)
    if collection.count() > 0:
        logger.info(f"Collection 'onet_jobs' already has {collection.count()} items. Skipping ingestion.")
        return collection

    documents, metadatas, ids = parse_onet_files(onet_dir)
    
    logger.info(f"Ingesting {len(documents)} occupations...")
    
    # Batch insert
    batch_size = 100
    for i in range(0, len(documents), batch_size):
        collection.add(
            documents=documents[i:i+batch_size],
            metadatas=metadatas[i:i+batch_size],
            ids=ids[i:i+batch_size]
        )
        if (i+1) % 500 == 0:
            logger.info(f"Ingested {i+batch_size} / {len(documents)}")

    logger.info("Ingestion complete.")
    return collection

def ingest_cv_guides(client, guide_dir: str):
    """Ingest CV writing guides"""
    collection = create_collection(client, "cv_guides")
    
    # Placeholder logic
    guide_path = Path(guide_dir)
    if not guide_path.exists():
        logger.warning(f"Guide directory {guide_dir} not found. Skipping.")
        return
        
    documents = []
    metadatas = []
    ids = []
    
    for md_file in guide_path.glob("*.md"):
        text = md_file.read_text(encoding='utf-8')
        documents.append(text)
        metadatas.append({"title": md_file.stem, "type": "guide"})
        ids.append(f"guide_{md_file.stem}")
        
    if documents:
        collection.add(documents=documents, metadatas=metadatas, ids=ids)
        logger.info(f"Ingested {len(documents)} guides.")

def test_retrieval(client):
    """Test knowledge base retrieval"""
    collection = client.get_collection("onet_jobs")
    query = "machine learning python"
    results = collection.query(
        query_texts=[query],
        n_results=1
    )
    logger.info(f"Test Query: '{query}'")
    logger.info("Result:")
    # Fix accessing results structure
    if results['documents'] and len(results['documents'][0]) > 0:
        logger.info(f"- {results['documents'][0][0][:200]}...")
    else:
        logger.warning("No results found.")

if __name__ == "__main__":
    client = setup_chromadb()
    
    try:
        ingest_onet_jobs(client, "knowledge_base/onet")
    except Exception as e:
        logger.error(f"Failed to ingest O*NET: {e}")
        
    ingest_cv_guides(client, "knowledge_base/cv_guides")
    
    test_retrieval(client)
