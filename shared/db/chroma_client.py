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


@lru_cache(maxsize=1)
def get_chroma_client() -> chromadb.ClientAPI:
    """
    Get ChromaDB client (Singleton).
    
    Returns:
        chromadb.ClientAPI: Persistent ChromaDB client.
    
    Raises:
        ConnectionError: If ChromaDB is unavailable.
    """
    try:
        client = chromadb.PersistentClient(path=CHROMA_PATH)
        logger.info(f"ChromaDB client initialized at {CHROMA_PATH}")
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
