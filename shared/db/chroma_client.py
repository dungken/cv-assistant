"""
Shared ChromaDB Client
Singleton pattern to avoid multiple connections.
"""
import chromadb
from functools import lru_cache
import logging
import os

logger = logging.getLogger(__name__)

CHROMA_PATH = os.getenv("CHROMA_PATH", "./knowledge_base/chroma_db")
CHROMA_HOST = os.getenv("CHROMA_HOST")
CHROMA_PORT = os.getenv("CHROMA_PORT", "8000")

@lru_cache(maxsize=10)
def get_chroma_client(host: str = None, port: int = None) -> chromadb.ClientAPI:
    """
    Get ChromaDB client.
    Args:
        host: Optional host override.
        port: Optional port override.
    """
    # Use provided args, then env vars, then defaults
    h = host or CHROMA_HOST
    p = port or int(CHROMA_PORT)
    
    try:
        if h:
            client = chromadb.HttpClient(host=h, port=p)
            logger.info(f"ChromaDB connected via HTTP to {h}:{p}")
        else:
            client = chromadb.PersistentClient(path=CHROMA_PATH)
            logger.info(f"ChromaDB client initialized locally at {CHROMA_PATH}")
        return client
    except Exception as e:
        logger.error(f"Failed to connect to ChromaDB: {e}")
        raise ConnectionError(f"ChromaDB unavailable: {e}")


def get_collection(name: str) -> chromadb.Collection:
    """
    Get a collection by name.
    
    Args:
        name: Collection name.
    
    Returns:
        chromadb.Collection: The requested collection.
    
    Raises:
        ValueError: If collection doesn't exist.
    """
    client = get_chroma_client()
    try:
        return client.get_collection(name)
    except Exception as e:
        raise ValueError(f"Collection '{name}' not found: {e}")
