# 11. Architecture Decision Records (ADR)

> **Document Version**: 1.0
> **Last Updated**: 2026-01-23
> **Status**: Approved
> **Related Documents**: [08_optimal_solution.md](./08_optimal_solution.md), [09_system_architecture.md](./09_system_architecture.md)

---

## ADR Template

```
# ADR-XXX: Title

## Status
[Proposed | Accepted | Deprecated | Superseded]

## Context
[What is the issue that we're seeing that is motivating this decision?]

## Decision
[What is the change that we're proposing and/or doing?]

## Consequences
[What becomes easier or more difficult to do because of this decision?]
```

---

## ADR-001: Use BERT-base-uncased for NER

### Status
**Accepted**

### Context
We need to choose a pre-trained language model for Named Entity Recognition on CVs. The options considered were:
1. BERT-base-uncased (110M parameters)
2. BERT-base-cased (110M parameters)
3. RoBERTa-base (125M parameters)
4. DistilBERT (66M parameters)
5. Custom training from scratch

Key considerations:
- GPU resources: Google Colab Free (T4 16GB)
- Training data: ~200 annotated CVs
- Target F1: ≥ 75%
- Language: English

### Decision
We will use **bert-base-uncased** as our base model for NER.

**Rationale:**
1. **Uncased vs Cased**: CVs have inconsistent capitalization. Uncased model is more robust to this variation.
2. **BERT vs RoBERTa**: BERT is simpler, has more tutorials, and the performance difference is marginal for our task.
3. **Base vs Large**: Base fits in T4 GPU memory with batch size 16. Large would require smaller batches.
4. **BERT vs DistilBERT**: DistilBERT is faster but ~5% less accurate. We prioritize accuracy.
5. **Pre-trained vs From Scratch**: Pre-trained models require much less data for fine-tuning.

### Consequences

**Positive:**
- Well-documented model with many NER tutorials
- Fits comfortably in T4 GPU memory
- Good balance of accuracy and training speed
- Large community support for troubleshooting

**Negative:**
- Uncased may lose some information (e.g., proper nouns)
- Not the absolute best model available (RoBERTa slightly better)
- Limited to 512 tokens (may truncate long CVs)

**Trade-offs Accepted:**
- Accept uncased limitation for robustness
- Accept 512 token limit (will truncate if needed)

---

## ADR-002: Use Label Studio for Annotation

### Status
**Accepted**

### Context
We need a tool for annotating CVs with Named Entity Recognition labels. Requirements:
- Support BIO tagging scheme
- Team collaboration features
- Export to common formats (CoNLL, JSON)
- Free or open-source
- Self-hostable (data privacy)

Options considered:
1. Label Studio (open-source)
2. Doccano (open-source)
3. Prodigy (commercial)
4. Custom annotation tool
5. Spreadsheet-based manual annotation

### Decision
We will use **Label Studio** (self-hosted) for NER annotation.

**Rationale:**
1. **Free and Open-Source**: Fits $0 budget constraint
2. **Self-Hosted**: Data stays local, addresses privacy concerns
3. **NER Support**: Native NER labeling interface
4. **Export Formats**: Supports CoNLL, JSON, CONLL-U
5. **Multi-User**: Built-in user management for team
6. **Active Development**: Regular updates, good documentation

### Consequences

**Positive:**
- No cost
- Full control over data
- Easy setup (Docker or pip install)
- Intuitive NER annotation interface
- Export directly to training-ready format

**Negative:**
- Self-hosting requires maintenance
- Learning curve for team
- No built-in ML-assisted annotation (unlike Prodigy)

**Trade-offs Accepted:**
- Accept self-hosting overhead for cost savings and privacy
- Accept manual annotation without ML assistance

**Implementation Notes:**
```bash
# Install Label Studio
pip install label-studio

# Start server
label-studio start --port 8080
```

---

## ADR-003: Use FastAPI for Backend

### Status
**Accepted**

### Context
We need a backend framework to serve the NER model and handle CV processing. Requirements:
- Python-based (for ML integration)
- REST API support
- Good performance
- Easy to learn
- Good documentation

Options considered:
1. FastAPI
2. Flask
3. Django
4. Tornado
5. Node.js (Express)

### Decision
We will use **FastAPI** as our backend framework.

**Rationale:**
1. **Python Native**: Seamless integration with PyTorch/Transformers
2. **Performance**: Async support, faster than Flask
3. **Auto Documentation**: Automatic OpenAPI/Swagger docs
4. **Type Safety**: Pydantic validation
5. **Modern**: Uses Python type hints
6. **Easy to Learn**: Simple and intuitive API

### Consequences

**Positive:**
- Automatic API documentation (Swagger UI)
- Type validation with Pydantic
- Native async support for concurrent requests
- Great developer experience
- Active community

**Negative:**
- Newer than Flask (less legacy examples)
- Async can be confusing for beginners
- Smaller ecosystem than Django

**Trade-offs Accepted:**
- Accept learning curve for better tooling
- Choose simplicity over Django's batteries-included approach

**Implementation Example:**
```python
from fastapi import FastAPI, UploadFile
from pydantic import BaseModel

app = FastAPI()

class CVResult(BaseModel):
    cv_id: str
    entities: list

@app.post("/api/upload")
async def upload_cv(file: UploadFile) -> CVResult:
    # Process CV
    return CVResult(cv_id="...", entities=[])
```

---

## ADR-004: Use React with Ant Design for Frontend

### Status
**Accepted**

### Context
We need a frontend framework for the CV-NER web application. Requirements:
- Modern UI/UX
- Component library for fast development
- Good documentation
- Can be learned quickly
- Responsive design

Options considered:
1. React + Ant Design
2. React + Material-UI
3. Vue.js + Vuetify
4. Next.js
5. Plain HTML/CSS/JavaScript

### Decision
We will use **React 18** with **Ant Design 5** for the frontend.

**Rationale:**
1. **React**: Most popular framework, abundant resources
2. **Ant Design**: Enterprise-grade components, good for forms and tables
3. **TypeScript Support**: Type safety
4. **Rapid Development**: Pre-built components
5. **Responsive**: Built-in responsive utilities

### Consequences

**Positive:**
- Rich component library (Upload, Table, Form, etc.)
- Professional look out-of-the-box
- Good documentation
- Large community

**Negative:**
- Learning curve for React beginners
- Bundle size larger than vanilla JS
- Ant Design style may be opinionated

**Trade-offs Accepted:**
- Accept learning curve for faster UI development
- Accept larger bundle size for better DX

**Key Components to Use:**
- `Upload`: For CV PDF upload
- `Table`: For displaying entities
- `Card`: For result sections
- `Form`: For JD input
- `Progress`: For processing indicator

---

## ADR-005: Use Sentence-BERT for Skill Matching

### Status
**Accepted**

### Context
We need a method to match skills from CVs with requirements from job descriptions. Requirements:
- Handle semantic similarity (not just exact match)
- Fast inference
- No training required (use pre-trained)
- Free

Options considered:
1. Exact string matching
2. TF-IDF + Cosine similarity
3. Word2Vec/FastText
4. Sentence-BERT (SBERT)
5. OpenAI Embeddings API

### Decision
We will use **Sentence-BERT** (model: `all-MiniLM-L6-v2`) for semantic skill matching.

**Rationale:**
1. **Semantic Understanding**: Captures meaning, not just keywords
2. **Pre-trained**: No training needed, works out-of-the-box
3. **Fast**: MiniLM is optimized for speed
4. **Free**: No API costs
5. **Good Quality**: Strong performance on semantic similarity tasks

### Consequences

**Positive:**
- Handles synonyms ("JS" ~ "JavaScript")
- Handles related concepts ("Machine Learning" ~ "Deep Learning")
- Fast inference (~10ms per embedding)
- No additional training required

**Negative:**
- May over-match unrelated skills
- 384-dim embeddings (memory for caching)
- Threshold tuning needed

**Trade-offs Accepted:**
- Accept potential over-matching for better recall
- Will tune similarity threshold (start with 0.7)

**Implementation:**
```python
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

model = SentenceTransformer('all-MiniLM-L6-v2')

cv_skills = ["Python", "Machine Learning"]
jd_skills = ["Python programming", "Deep Learning"]

cv_embeddings = model.encode(cv_skills)
jd_embeddings = model.encode(jd_skills)

similarities = cosine_similarity(cv_embeddings, jd_embeddings)
# [[0.85, 0.45],   # Python vs Python programming, Deep Learning
#  [0.30, 0.82]]   # Machine Learning vs Python programming, Deep Learning
```

---

## ADR-006: Use BIO Tagging Scheme

### Status
**Accepted**

### Context
We need a tagging scheme for sequence labeling in NER. Options:
1. BIO (Begin, Inside, Outside)
2. BIOES (Begin, Inside, Outside, End, Single)
3. IOB1 (Inside, Outside, Begin where needed)
4. Custom scheme

### Decision
We will use the **BIO** tagging scheme.

**Rationale:**
1. **Simplicity**: Only 3 tag types per entity
2. **Standard**: Most common scheme in NER literature
3. **Tooling**: seqeval supports BIO natively
4. **Sufficient**: Handles our 8 entity types well

### Consequences

**Positive:**
- Simple to understand and implement
- Fewer labels (17 vs 41 for BIOES with 8 entities)
- Standard evaluation with seqeval

**Negative:**
- Cannot distinguish between consecutive same-type entities
- Less precise than BIOES

**Trade-offs Accepted:**
- Accept ambiguity in consecutive entities (rare in CVs)
- Prioritize simplicity

**Label Set:**
```
Total labels: 21
= 1 (O) + 10 entity types × 2 (B, I)

Labels: O, B-PER, I-PER, B-ORG, I-ORG, B-DATE, I-DATE,
        B-LOC, I-LOC, B-SKILL, I-SKILL, B-DEGREE, I-DEGREE,
        B-MAJOR, I-MAJOR, B-JOB_TITLE, I-JOB_TITLE,
        B-PROJECT, I-PROJECT, B-CERT, I-CERT
```

---

## ADR-007: Use LlamaIndex for RAG Chatbot

### Status
**Accepted**

### Context
We need a framework to build a conversational AI chatbot that can:
- Answer questions about CV improvement
- Provide career guidance
- Use knowledge base for accurate responses
- Integrate with NER and skill matching tools

Options considered:
1. LlamaIndex (formerly GPT Index)
2. LangChain
3. Custom RAG implementation
4. Direct LLM API calls

### Decision
We will use **LlamaIndex** as the RAG framework for the chatbot.

**Rationale:**
1. **Simpler API**: More intuitive than LangChain for RAG
2. **ReAct Agent**: Native support for tool-using agents
3. **Index Types**: Multiple index types for different use cases
4. **Ollama Integration**: Official integration with local LLMs
5. **Active Development**: Frequent updates, good documentation

### Consequences

**Positive:**
- Clean abstractions for RAG pipeline
- Built-in ReAct agent pattern
- Easy tool integration (NER, skill matching)
- Good for prototyping and production

**Negative:**
- Rapidly changing API (breaking changes)
- Less flexible than LangChain for complex chains
- Smaller community than LangChain

**Implementation:**
```python
from llama_index.core import VectorStoreIndex, Settings
from llama_index.llms.ollama import Ollama
from llama_index.core.agent import ReActAgent

Settings.llm = Ollama(model="llama3.2:3b", base_url="http://ollama:11434")

agent = ReActAgent.from_tools(
    tools=[ner_tool, skill_match_tool, career_tool],
    verbose=True
)
```

---

## ADR-008: Use Ollama for Local LLM

### Status
**Accepted**

### Context
We need an LLM provider for the chatbot. Requirements:
- Free (no API costs)
- Local deployment (data privacy)
- Good Vietnamese support
- Reasonable response quality

Options considered:
1. Ollama with Llama 3.2
2. OpenAI API (GPT-4)
3. Claude API
4. Self-hosted vLLM
5. Hugging Face Text Generation Inference

### Decision
We will use **Ollama** running **Llama 3.2 (3B)** locally.

**Rationale:**
1. **Free**: No API costs, unlimited usage
2. **Easy Setup**: Simple installation, Docker support
3. **Privacy**: Data never leaves local infrastructure
4. **Model Quality**: Llama 3.2 3B is capable for our use case
5. **Low Resource**: 3B model fits in 8GB RAM

### Consequences

**Positive:**
- Zero cost for LLM inference
- Full data privacy
- Easy Docker deployment
- Fast local inference

**Negative:**
- Requires decent hardware (8GB+ RAM)
- Smaller model = lower quality than GPT-4
- No internet knowledge (only knowledge base)

**Configuration:**
```yaml
# docker-compose.yml
ollama:
  image: ollama/ollama:latest
  ports:
    - "11434:11434"
  volumes:
    - ollama_data:/root/.ollama
  deploy:
    resources:
      reservations:
        devices:
          - driver: nvidia
            count: 1
            capabilities: [gpu]
```

---

## ADR-009: Use ChromaDB for Vector Store

### Status
**Accepted**

### Context
We need a vector database to store:
- Knowledge base embeddings for RAG
- Conversation history embeddings
- CV content embeddings

Options considered:
1. ChromaDB
2. Pinecone
3. Weaviate
4. Milvus
5. FAISS (in-memory)

### Decision
We will use **ChromaDB** as our vector store.

**Rationale:**
1. **Free**: Open-source, no usage limits
2. **Simple**: Easy setup, Python-native
3. **Persistence**: Built-in SQLite persistence
4. **LlamaIndex**: Official integration
5. **Lightweight**: No heavy infrastructure

### Consequences

**Positive:**
- Easy to set up and maintain
- Native Python integration
- Built-in persistence
- Good for small-medium datasets

**Negative:**
- Not suitable for very large datasets
- Single-node (no distributed)
- Less mature than Pinecone/Weaviate

**Implementation:**
```python
import chromadb
from chromadb.config import Settings

client = chromadb.PersistentClient(
    path="./chroma_data",
    settings=Settings(anonymized_telemetry=False)
)

collection = client.get_or_create_collection(
    name="cv_assistant_knowledge",
    metadata={"hnsw:space": "cosine"}
)
```

---

## ADR-010: Use PostgreSQL for Relational Data

### Status
**Accepted**

### Context
We need a relational database to store:
- User accounts and authentication
- CV metadata and extraction results
- Conversation threads and messages
- Refresh tokens

Options considered:
1. PostgreSQL
2. MySQL
3. SQLite
4. MongoDB

### Decision
We will use **PostgreSQL** for relational data storage.

**Rationale:**
1. **Enterprise-grade**: Reliable, battle-tested
2. **JSON Support**: JSONB for flexible schema
3. **Spring Boot**: Excellent integration
4. **Free**: Open-source
5. **UUID Support**: Native UUID type

### Consequences

**Positive:**
- Rock-solid reliability
- Rich feature set (JSONB, arrays, etc.)
- Excellent tooling
- Wide community support

**Negative:**
- Heavier than SQLite
- Requires separate container
- More setup than file-based DB

---

## ADR-011: Use Spring Boot for API Gateway

### Status
**Accepted**

### Context
We need an API gateway to:
- Handle authentication (JWT)
- Route requests to microservices
- Provide unified API for frontend
- Handle CORS and rate limiting

Options considered:
1. Spring Boot + Spring Security
2. Kong Gateway
3. Nginx + Lua
4. FastAPI as gateway
5. AWS API Gateway

### Decision
We will use **Spring Boot 3** with **Spring Security** as the API Gateway.

**Rationale:**
1. **Enterprise Standard**: Widely used in industry
2. **Security**: Spring Security for JWT auth
3. **Type Safety**: Java/Kotlin strong typing
4. **OpenAPI**: SpringDoc for API documentation
5. **Team Skills**: Good for learning enterprise patterns

### Consequences

**Positive:**
- Robust authentication handling
- Automatic API documentation
- Good for microservices patterns
- Strong type system

**Negative:**
- Heavier than Python alternatives
- More boilerplate code
- Longer development time

---

## ADR-012: Use Docker Compose for Deployment

### Status
**Accepted**

### Context
We need to deploy multiple services:
- Frontend (React)
- API Gateway (Spring Boot)
- 4 Python microservices
- PostgreSQL
- ChromaDB
- Ollama

Options considered:
1. Docker Compose
2. Kubernetes
3. Manual deployment
4. Platform-as-a-Service

### Decision
We will use **Docker Compose** for local and demo deployment.

**Rationale:**
1. **Simplicity**: Easy to understand and manage
2. **Local Dev**: Perfect for development
3. **Demo**: Sufficient for NCKH demo
4. **Reproducible**: Same environment everywhere
5. **All-in-one**: Single command to start all services

### Consequences

**Positive:**
- Simple deployment (docker-compose up)
- Consistent across environments
- Easy to share and reproduce
- Network isolation built-in

**Negative:**
- Not production-grade for scale
- Single-machine only
- No auto-scaling

---

## ADR Summary Table

| ADR | Decision | Status | Date |
|-----|----------|--------|------|
| ADR-001 | BERT-base-uncased for NER | Accepted | 2026-01-23 |
| ADR-002 | Label Studio for Annotation | Accepted | 2026-01-23 |
| ADR-003 | FastAPI for Python Microservices | Accepted | 2026-01-23 |
| ADR-004 | React + Ant Design for Frontend | Accepted | 2026-01-23 |
| ADR-005 | Sentence-BERT for Skill Matching | Accepted | 2026-01-23 |
| ADR-006 | BIO Tagging Scheme (21 labels) | Accepted | 2026-01-23 |
| ADR-007 | LlamaIndex for RAG Chatbot | Accepted | 2026-01-23 |
| ADR-008 | Ollama for Local LLM | Accepted | 2026-01-23 |
| ADR-009 | ChromaDB for Vector Store | Accepted | 2026-01-23 |
| ADR-010 | PostgreSQL for Relational Data | Accepted | 2026-01-23 |
| ADR-011 | Spring Boot for API Gateway | Accepted | 2026-01-23 |
| ADR-012 | Docker Compose for Deployment | Accepted | 2026-01-23 |

---

## Future ADR Candidates

Potential decisions that may need ADRs:
- Model quantization for faster NER inference
- Caching strategy for skill embeddings
- Redis for session management
- Kubernetes for production deployment
- CI/CD pipeline selection

---

*Document created as part of CV-NER Research Project documentation.*
