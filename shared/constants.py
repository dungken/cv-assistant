"""
Shared Project Constants
"""

# Default labels for Label Studio and NER
ENTITY_TYPES = [
    "PER", "ORG", "DATE", "LOC", "SKILL", 
    "DEGREE", "MAJOR", "JOB_TITLE", "PROJECT", "CERT"
]

# ChromaDB Collection Names
COLLECTION_JOBS = "onet_jobs"
COLLECTION_GUIDES = "cv_guides"
COLLECTION_CV_TEXT = "cv_text"
COLLECTION_CONVERSATIONS = "conversations"

# Default Model
DEFAULT_EMBEDDING_MODEL = "all-MiniLM-L6-v2"
