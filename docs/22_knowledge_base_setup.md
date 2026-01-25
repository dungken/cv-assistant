# 22. Knowledge Base Setup - Thiết Lập Knowledge Base

> **Document Version**: 1.0
> **Last Updated**: 2026-01-24
> **Status**: Approved
> **Product Name**: CV Assistant
> **Related Documents**: [09_system_architecture.md](./09_system_architecture.md), [21_chatbot_specification.md](./21_chatbot_specification.md)

---

## 1. Overview

### 1.1 Purpose

Knowledge Base là thành phần cốt lõi của hệ thống CV Assistant, cung cấp context cho chatbot thông qua RAG (Retrieval-Augmented Generation).

### 1.2 Components

```
Knowledge Base Architecture:
├── ChromaDB (Vector Store)
│   ├── cv_assistant_kb (main collection)
│   ├── conversations_{user_id} (per-user memory)
│   └── user_cvs_{user_id} (uploaded CV data)
│
├── Embedding Model
│   └── all-MiniLM-L6-v2 (384 dimensions)
│
└── Data Sources
    ├── O*NET Database (Jobs & Skills)
    ├── CV Writing Guides
    ├── Career Path Data
    └── User-Uploaded CVs
```

---

## 2. Data Sources

### 2.1 O*NET Database

**Source**: O*NET Resource Center (https://www.onetcenter.org/database.html)
**Format**: Text/Excel Database (db_28_1_text.zip)
**Content**:
- `Occupation Data.txt`: Job titles, descriptions.
- `Skills.txt`: Skills linked to occupations.
- `Knowledge.txt`: Knowledge domains.

### 2.2 CV Writing Guides

**Sources**:
- Best practice guides (internal)
- Resume writing tips
- Industry-specific templates

**Structure**:

```yaml
CV Writing Guides:
  sections:
    - name: "Contact Information"
      tips:
        - "Include professional email only"
        - "Add LinkedIn profile URL"
      examples:
        - good: "john.doe@gmail.com"
        - bad: "coolguy123@yahoo.com"

    - name: "Professional Summary"
      tips:
        - "Keep to 3-4 sentences"
        - "Highlight key achievements"
      template: |
        [Years] experienced [Role] with expertise in
        [Key Skills]. Proven track record of [Achievement].

    - name: "Work Experience"
      tips:
        - "Use action verbs"
        - "Quantify achievements"
      action_verbs:
        - "Developed"
        - "Implemented"
        - "Led"
        - "Optimized"

  industry_specific:
    - industry: "Technology"
      emphasis: ["Technical skills", "Projects", "GitHub"]
    - industry: "Finance"
      emphasis: ["Quantitative skills", "Certifications", "Education"]
```

### 2.3 Career Path Data

**Structure**:

```yaml
Career Paths:
  paths:
    - title: "Junior Developer to Tech Lead"
      stages:
        - role: "Junior Developer"
          typical_duration: "1-2 years"
          key_skills: ["Coding", "Testing", "Git"]

        - role: "Mid-level Developer"
          typical_duration: "2-3 years"
          key_skills: ["System Design", "Code Review", "Mentoring"]

        - role: "Senior Developer"
          typical_duration: "2-3 years"
          key_skills: ["Architecture", "Technical Leadership"]

        - role: "Tech Lead"
          typical_duration: "ongoing"
          key_skills: ["Team Management", "Strategic Planning"]

  skill_gaps:
    - from_role: "Junior Developer"
      to_role: "Senior Developer"
      required_skills:
        - "System Design"
        - "Performance Optimization"
        - "Security Best Practices"
      recommended_certifications:
        - "AWS Solutions Architect"
        - "Kubernetes Administrator"
```

---

## 3. ChromaDB Setup

### 3.1 Installation

```bash
# Install ChromaDB
pip install chromadb

# Install embedding model
pip install sentence-transformers
```

### 3.2 Collection Configuration

```python
import chromadb
from chromadb.config import Settings

# Initialize ChromaDB with persistence
client = chromadb.Client(Settings(
    chroma_db_impl="duckdb+parquet",
    persist_directory="./data/chroma_db",
    anonymized_telemetry=False
))

# Create main knowledge base collection
kb_collection = client.get_or_create_collection(
    name="cv_assistant_kb",
    metadata={
        "description": "Main knowledge base for CV Assistant",
        "version": "1.0",
        "created_at": "2026-01-24"
    }
)
```

### 3.3 Embedding Configuration

```python
from sentence_transformers import SentenceTransformer
from chromadb.utils import embedding_functions

# Use all-MiniLM-L6-v2 for embeddings
embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)

# Apply to collection
kb_collection = client.get_or_create_collection(
    name="cv_assistant_kb",
    embedding_function=embedding_fn
)
```

---

## 4. Data Ingestion

### 4.1 O*NET Data Ingestion

```python
import json
from typing import List, Dict

class ONetIngester:
    def __init__(self, collection):
        self.collection = collection

    def ingest_occupations(self, onet_dir: str):
        """Ingest O*NET occupations from Text Database"""
        import pandas as pd
        from pathlib import Path
        
        # Load Occupation Data.txt
        occ_file = Path(onet_dir) / "Occupation Data.txt"
        df = pd.read_csv(occ_file, sep="\t")

        documents = []
        metadatas = []
        ids = []

        for _, row in df.iterrows():
            # Create document text
            doc = f"""
            Occupation: {row['Title']}
            Code: {row['O*NET-SOC Code']}
            Description: {row['Description']}
            """

            documents.append(doc.strip())
            metadatas.append({
                "type": "occupation",
                "code": row['O*NET-SOC Code'],
                "title": row['Title']
            })
            ids.append(f"occ_{row['O*NET-SOC Code']}")

        # Add to collection (batch logic...)


    def ingest_skills(self, skills_file: str):
        """Ingest O*NET skills taxonomy"""
        with open(skills_file, 'r') as f:
            skills = json.load(f)

        documents = []
        metadatas = []
        ids = []

        for skill in skills:
            doc = f"""
            Skill: {skill['name']}
            Category: {skill['category']}
            Description: {skill['description']}
            """

            documents.append(doc.strip())
            metadatas.append({
                "type": "skill",
                "skill_id": skill['id'],
                "category": skill['category']
            })
            ids.append(f"skill_{skill['id']}")

        self.collection.add(
            documents=documents,
            metadatas=metadatas,
            ids=ids
        )
```

### 4.2 CV Writing Guides Ingestion

```python
class CVGuideIngester:
    def __init__(self, collection):
        self.collection = collection

    def ingest_guides(self, guides_dir: str):
        """Ingest CV writing guides"""
        import os
        import glob

        guide_files = glob.glob(os.path.join(guides_dir, "*.md"))

        documents = []
        metadatas = []
        ids = []

        for idx, file_path in enumerate(guide_files):
            with open(file_path, 'r') as f:
                content = f.read()

            # Chunk the content
            chunks = self._chunk_content(content, chunk_size=500)

            for chunk_idx, chunk in enumerate(chunks):
                documents.append(chunk)
                metadatas.append({
                    "type": "cv_guide",
                    "source": os.path.basename(file_path),
                    "chunk_idx": chunk_idx
                })
                ids.append(f"guide_{idx}_{chunk_idx}")

        self.collection.add(
            documents=documents,
            metadatas=metadatas,
            ids=ids
        )

    def _chunk_content(self, content: str, chunk_size: int = 500) -> List[str]:
        """Split content into overlapping chunks"""
        words = content.split()
        chunks = []
        overlap = 50  # Word overlap

        for i in range(0, len(words), chunk_size - overlap):
            chunk = ' '.join(words[i:i + chunk_size])
            if chunk.strip():
                chunks.append(chunk)

        return chunks
```

### 4.3 User CV Ingestion

```python
class UserCVIngester:
    def __init__(self, client, embedding_fn):
        self.client = client
        self.embedding_fn = embedding_fn

    def ingest_user_cv(self, user_id: str, cv_text: str, entities: List[Dict]):
        """Store user's CV data for personalized recommendations"""

        # Get or create user-specific collection
        collection = self.client.get_or_create_collection(
            name=f"user_cvs_{user_id}",
            embedding_function=self.embedding_fn
        )

        # Store CV text
        collection.add(
            documents=[cv_text],
            metadatas=[{
                "type": "cv_text",
                "user_id": user_id,
                "timestamp": datetime.now().isoformat()
            }],
            ids=[f"cv_{user_id}_{datetime.now().timestamp()}"]
        )

        # Store extracted entities
        for entity in entities:
            collection.add(
                documents=[entity['text']],
                metadatas=[{
                    "type": "cv_entity",
                    "entity_type": entity['type'],
                    "user_id": user_id
                }],
                ids=[f"entity_{user_id}_{entity['type']}_{hash(entity['text'])}"]
            )
```

---

## 5. Retrieval Configuration

### 5.1 Query Pipeline

```python
class KnowledgeRetriever:
    def __init__(self, collection):
        self.collection = collection

    def query(self, query_text: str, n_results: int = 5,
              filter_type: str = None) -> List[Dict]:
        """Retrieve relevant documents"""

        where_filter = None
        if filter_type:
            where_filter = {"type": filter_type}

        results = self.collection.query(
            query_texts=[query_text],
            n_results=n_results,
            where=where_filter,
            include=["documents", "metadatas", "distances"]
        )

        return self._format_results(results)

    def _format_results(self, results) -> List[Dict]:
        """Format ChromaDB results"""
        formatted = []

        for i in range(len(results['documents'][0])):
            formatted.append({
                "content": results['documents'][0][i],
                "metadata": results['metadatas'][0][i],
                "distance": results['distances'][0][i] if 'distances' in results else None
            })

        return formatted

    def hybrid_query(self, query_text: str, user_id: str = None) -> List[Dict]:
        """Query both general KB and user-specific data"""

        # Query general knowledge base
        general_results = self.query(query_text, n_results=3)

        # Query user-specific data if available
        user_results = []
        if user_id:
            try:
                user_collection = self.client.get_collection(f"user_cvs_{user_id}")
                user_results = user_collection.query(
                    query_texts=[query_text],
                    n_results=2
                )
            except:
                pass  # User collection doesn't exist

        return {
            "general": general_results,
            "personalized": user_results
        }
```

### 5.2 LlamaIndex Integration

```python
from llama_index.core import VectorStoreIndex
from llama_index.vector_stores.chroma import ChromaVectorStore

class LlamaIndexKB:
    def __init__(self, chroma_collection):
        self.vector_store = ChromaVectorStore(
            chroma_collection=chroma_collection
        )
        self.index = VectorStoreIndex.from_vector_store(
            vector_store=self.vector_store
        )

    def get_retriever(self, similarity_top_k: int = 5):
        """Get retriever for LlamaIndex agent"""
        return self.index.as_retriever(
            similarity_top_k=similarity_top_k
        )

    def get_query_engine(self):
        """Get query engine for direct queries"""
        return self.index.as_query_engine()
```

---

## 6. Collection Management

### 6.1 Collection Statistics

```python
def get_collection_stats(collection) -> Dict:
    """Get statistics for a collection"""
    count = collection.count()

    # Get sample to understand data distribution
    sample = collection.peek(limit=10)

    # Count by type
    type_counts = {}
    all_items = collection.get(include=["metadatas"])
    for metadata in all_items['metadatas']:
        item_type = metadata.get('type', 'unknown')
        type_counts[item_type] = type_counts.get(item_type, 0) + 1

    return {
        "total_documents": count,
        "type_distribution": type_counts,
        "sample_size": len(sample['documents'])
    }
```

### 6.2 Data Updates

```python
def update_knowledge_base(collection, data_source: str):
    """Incremental update of knowledge base"""

    # Get existing IDs
    existing = collection.get(include=[])
    existing_ids = set(existing['ids'])

    # Load new data
    new_data = load_data_source(data_source)

    updates = []
    additions = []

    for item in new_data:
        if item['id'] in existing_ids:
            updates.append(item)
        else:
            additions.append(item)

    # Update existing
    if updates:
        collection.update(
            ids=[u['id'] for u in updates],
            documents=[u['document'] for u in updates],
            metadatas=[u['metadata'] for u in updates]
        )

    # Add new
    if additions:
        collection.add(
            ids=[a['id'] for a in additions],
            documents=[a['document'] for a in additions],
            metadatas=[a['metadata'] for a in additions]
        )

    return {
        "updated": len(updates),
        "added": len(additions)
    }
```

---

## 7. Initialization Script

### 7.1 Full Setup Script

```python
#!/usr/bin/env python3
"""
Knowledge Base Initialization Script
Run once to set up the CV Assistant knowledge base
"""

import os
import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions

def initialize_knowledge_base():
    print("Initializing CV Assistant Knowledge Base...")

    # 1. Setup ChromaDB
    client = chromadb.Client(Settings(
        chroma_db_impl="duckdb+parquet",
        persist_directory="./data/chroma_db",
        anonymized_telemetry=False
    ))

    # 2. Setup embedding function
    embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )

    # 3. Create main collection
    kb_collection = client.get_or_create_collection(
        name="cv_assistant_kb",
        embedding_function=embedding_fn,
        metadata={"version": "1.0"}
    )

    # 4. Ingest O*NET data
    print("Ingesting O*NET data...")
    onet_ingester = ONetIngester(kb_collection)
    onet_ingester.ingest_occupations("./data/onet/occupations.json")
    onet_ingester.ingest_skills("./data/onet/skills.json")

    # 5. Ingest CV guides
    print("Ingesting CV writing guides...")
    guide_ingester = CVGuideIngester(kb_collection)
    guide_ingester.ingest_guides("./data/cv_guides/")

    # 6. Verify
    stats = get_collection_stats(kb_collection)
    print(f"Knowledge Base initialized with {stats['total_documents']} documents")
    print(f"Type distribution: {stats['type_distribution']}")

    # 7. Persist
    client.persist()
    print("Knowledge Base persisted to disk.")

if __name__ == "__main__":
    initialize_knowledge_base()
```

---

## 8. Maintenance

### 8.1 Backup & Restore

```bash
# Backup ChromaDB data
tar -czvf chroma_backup_$(date +%Y%m%d).tar.gz ./data/chroma_db/

# Restore from backup
tar -xzvf chroma_backup_YYYYMMDD.tar.gz -C ./data/
```

### 8.2 Health Check

```python
def health_check(client) -> Dict:
    """Check knowledge base health"""
    try:
        # Check main collection
        kb = client.get_collection("cv_assistant_kb")
        kb_count = kb.count()

        # Test query
        results = kb.query(
            query_texts=["software developer skills"],
            n_results=1
        )
        query_works = len(results['documents'][0]) > 0

        return {
            "status": "healthy",
            "document_count": kb_count,
            "query_functional": query_works
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }
```

---

## 9. Performance Tuning

### 9.1 Chunk Size Optimization

```yaml
Recommended Chunk Sizes:
  cv_guides: 500 words (with 50 word overlap)
  occupations: Full document (typically < 300 words)
  skills: Full document (typically < 100 words)
  career_paths: 300 words per stage

Rationale:
  - Smaller chunks = more precise retrieval
  - Larger chunks = better context preservation
  - Overlap prevents information loss at boundaries
```

### 9.2 Index Optimization

```python
# For large collections, consider using HNSW index
collection = client.get_or_create_collection(
    name="cv_assistant_kb",
    embedding_function=embedding_fn,
    metadata={
        "hnsw:space": "cosine",
        "hnsw:construction_ef": 200,
        "hnsw:search_ef": 100,
        "hnsw:M": 16
    }
)
```

---

*Document created as part of CV Assistant Research Project documentation.*
