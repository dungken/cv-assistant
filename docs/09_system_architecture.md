# 09. System Architecture - Thiết Kế Kiến Trúc

> **Document Version**: 2.0
> **Last Updated**: 2026-01-23
> **Status**: Approved
> **Product Name**: CV Assistant
> **Related Documents**: [08_optimal_solution.md](./08_optimal_solution.md), [10_risk_analysis.md](./10_risk_analysis.md)

---

## 1. Architecture Overview

### 1.1 Microservices Architecture (5 Services)

```
┌─────────────────────────────────────────────────────────────────┐
│                    FRONTEND (React)                              │
│                    Port: 3000                                    │
│                    ChatGPT-style UI                              │
└─────────────────────┬───────────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────────┐
│              API GATEWAY (Java Spring Boot)                      │
│              Port: 8080                                          │
│              - Authentication (JWT)                              │
│              - Request routing                                   │
│              - User management                                   │
└─────────────────────┬───────────────────────────────────────────┘
                      │
    ┌─────────────────┼─────────────────┬─────────────────┐
    ▼                 ▼                 ▼                 ▼
┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────────────┐
│ NER     │    │ Skill   │    │ Career  │    │ Chatbot         │
│ Service │    │ Match   │    │ Recom.  │    │ Service         │
│ FastAPI │    │ FastAPI │    │ FastAPI │    │ FastAPI         │
│ :5001   │    │ :5002   │    │ :5003   │    │ :5004           │
│         │    │         │    │         │    │ LlamaIndex      │
│         │    │         │    │         │    │ + Llama 3.2     │
└─────────┘    └─────────┘    └─────────┘    └─────────────────┘
    │                │                │                │
    └────────────────┴────────────────┴────────────────┘
                              │
              ┌───────────────┼───────────────┐
              ▼               ▼               ▼
      ┌───────────┐   ┌───────────┐   ┌───────────┐
      │PostgreSQL │   │ ChromaDB  │   │  Ollama   │
      │  :5432    │   │  :8000    │   │  :11434   │
      │ Users,CVs │   │ RAG,Chat  │   │ Llama 3.2 │
      └───────────┘   └───────────┘   └───────────┘
```

### 1.2 Service Summary Table

| # | Service | Technology | Port | Purpose |
|---|---------|------------|------|---------|
| 1 | Frontend | React 18 | 3000 | ChatGPT-style UI |
| 2 | API Gateway | Java Spring Boot | 8080 | Auth + Routing |
| 3 | NER Service | Python FastAPI | 5001 | CV information extraction |
| 4 | Skill Matching | Python FastAPI | 5002 | JD-CV skill comparison |
| 5 | Career Recommend | Python FastAPI | 5003 | Career roadmap generation |
| 6 | Chatbot Service | Python FastAPI + LlamaIndex | 5004 | Conversational AI |
| 7 | PostgreSQL | Database | 5432 | Users, CVs, results |
| 8 | ChromaDB | Vector DB | 8000 | RAG, conversation history |
| 9 | Ollama | LLM Server | 11434 | Serve Llama 3.2 |

### 1.3 Component Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                     Component Diagram - CV Assistant                         │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │                   Frontend (React 18 - ChatGPT Style)                 │   │
│  │  ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────────────┐ │   │
│  │  │ ChatPage   │ │ ThreadList │ │ MessageView│ │ Common Components  │ │   │
│  │  └────────────┘ └────────────┘ └────────────┘ │ - Header/Sidebar   │ │   │
│  │  ┌────────────┐ ┌────────────┐ ┌────────────┐ │ - LoadingSpinner   │ │   │
│  │  │ LoginPage  │ │ ProfilePage│ │ UploadCV   │ │ - MessageBubble    │ │   │
│  │  └────────────┘ └────────────┘ └────────────┘ └────────────────────┘ │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                      │                                       │
│                                      │ HTTP/REST + JWT                       │
│                                      ▼                                       │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │                   API Gateway (Spring Boot 3.x)                       │   │
│  │  ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────────────┐ │   │
│  │  │ Auth       │ │ Chat       │ │ User       │ │ Utils              │ │   │
│  │  │ Controller │ │ Controller │ │ Controller │ │ - JWTUtil          │ │   │
│  │  │ - login    │ │ - message  │ │ - profile  │ │ - SecurityConfig   │ │   │
│  │  │ - register │ │ - threads  │ │ - cv_mgmt  │ │ - CORS             │ │   │
│  │  └────────────┘ └────────────┘ └────────────┘ └────────────────────┘ │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                      │                                       │
│              ┌───────────────────────┼───────────────────────┐              │
│              ▼                       ▼                       ▼              │
│  ┌────────────────────┐ ┌────────────────────┐ ┌────────────────────────┐   │
│  │  Chatbot Service   │ │  NER Service       │ │  Skill Match Service   │   │
│  │  (FastAPI + Index) │ │  (FastAPI + BERT)  │ │  (FastAPI + SBERT)     │   │
│  │  ┌──────────────┐  │ │  ┌──────────────┐  │ │  ┌──────────────────┐  │   │
│  │  │ LlamaIndex   │  │ │  │ NER Model    │  │ │  │ Skill Taxonomy   │  │   │
│  │  │ ReAct Agent  │  │ │  │ BERT + Head  │  │ │  │ O*NET Based      │  │   │
│  │  └──────────────┘  │ │  └──────────────┘  │ │  └──────────────────┘  │   │
│  │  ┌──────────────┐  │ │  ┌──────────────┐  │ │  ┌──────────────────┐  │   │
│  │  │ RAG Pipeline │  │ │  │ PDF Parser   │  │ │  │ Sentence-BERT    │  │   │
│  │  └──────────────┘  │ │  └──────────────┘  │ │  └──────────────────┘  │   │
│  └────────────────────┘ └────────────────────┘ └────────────────────────┘   │
│              │                       │                       │              │
│  ┌────────────────────┐              │              ┌────────────────────┐   │
│  │ Career Recommend   │              │              │  Data Stores       │   │
│  │ Service (FastAPI)  │              │              │  ┌──────────────┐  │   │
│  │  ┌──────────────┐  │              │              │  │ PostgreSQL   │  │   │
│  │  │ O*NET Data   │  │              │              │  │ Users, CVs   │  │   │
│  │  │ Career Paths │  │              │              │  └──────────────┘  │   │
│  │  └──────────────┘  │              │              │  ┌──────────────┐  │   │
│  └────────────────────┘              │              │  │ ChromaDB     │  │   │
│                                      │              │  │ RAG, Memory  │  │   │
│                         ┌────────────┴────────────┐ │  └──────────────┘  │   │
│                         │      Ollama Server      │ │  ┌──────────────┐  │   │
│                         │      Llama 3.2 (3B)     │ │  │ File Storage │  │   │
│                         │      CPU-only           │ │  │ PDFs, Exports│  │   │
│                         └─────────────────────────┘ │  └──────────────┘  │   │
│                                                     └────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Technology Stack Details

### 2.1 Frontend Stack

```
Frontend Technology Stack:
├── Framework: React 18
│   ├── Hooks for state management
│   ├── Functional components
│   ├── React Router for navigation
│   └── Context API for global state
│
├── UI Library: Tailwind CSS + shadcn/ui
│   ├── ChatGPT-style components
│   ├── Responsive design
│   ├── Dark/Light mode
│   └── Custom message bubbles
│
├── HTTP Client: Axios
│   ├── Request/Response interceptors
│   ├── JWT token handling
│   └── Error handling
│
├── Language: TypeScript
│   ├── Type safety
│   └── Interface definitions
│
└── Build Tool: Vite
    ├── Fast HMR
    └── Optimized build
```

### 2.2 API Gateway Stack (Spring Boot)

```
API Gateway Technology Stack:
├── Framework: Spring Boot 3.x
│   ├── Spring Security (JWT)
│   ├── Spring Web MVC
│   └── Spring Data JPA
│
├── Authentication: JWT
│   ├── Access tokens (24h)
│   ├── Refresh tokens (7d)
│   └── BCrypt password hashing
│
├── Database: PostgreSQL 15
│   ├── Users table
│   ├── CVs table
│   ├── Threads table
│   └── Messages table
│
├── Language: Java 17+
│   ├── Records for DTOs
│   └── Virtual threads (preview)
│
└── Build: Gradle/Maven
    └── Docker image build
```

### 2.3 Python Services Stack (FastAPI)

```
Python Services Technology Stack:
├── Framework: FastAPI
│   ├── Automatic OpenAPI docs
│   ├── Async support
│   ├── Dependency injection
│   └── Pydantic v2 validation
│
├── Server: Uvicorn
│   ├── ASGI server
│   └── Hot reload for dev
│
├── PDF Processing: pdfplumber
│   ├── Text extraction
│   ├── Layout preservation
│   └── Fallback: PyPDF2
│
├── Language: Python 3.10+
│   ├── Type hints
│   └── Async/await
│
└── Inter-service: httpx
    └── Async HTTP client
```

### 2.4 Chatbot & LLM Stack

```
Chatbot Technology Stack:
├── LLM Server: Ollama
│   ├── Model: Llama 3.2 (3B)
│   ├── CPU-only inference
│   ├── 16GB RAM requirement
│   └── REST API on :11434
│
├── Agent Framework: LlamaIndex
│   ├── ReAct agent pattern
│   ├── Tool calling
│   ├── Memory management
│   └── RAG pipeline
│
├── Vector Database: ChromaDB
│   ├── Document embeddings
│   ├── Conversation history
│   ├── Persistent storage
│   └── REST API on :8000
│
├── Embeddings: Sentence-BERT
│   ├── all-MiniLM-L6-v2
│   ├── 384-dim embeddings
│   └── Local inference
│
└── RAG Knowledge Sources:
    ├── O*NET Database
    ├── CV Writing Guides
    ├── Job Market Data
    └── User's CV (personalized)
```

### 2.5 ML/NER Stack

```
ML Technology Stack:
├── Deep Learning: PyTorch 2.0
│   ├── Eager execution
│   ├── CPU inference (production)
│   └── GPU training (Colab)
│
├── NLP: Hugging Face Transformers
│   ├── Pre-trained BERT
│   ├── Tokenizers
│   └── Trainer API
│
├── Embeddings: Sentence-BERT
│   ├── all-MiniLM-L6-v2
│   ├── 384-dim embeddings
│   └── Fast inference
│
├── Evaluation: seqeval
│   ├── NER metrics (F1, P, R)
│   └── BIO evaluation
│
└── Data: datasets library
    ├── Dataset management
    └── Data loading
```

---

## 3. API Design

### 3.1 API Gateway Endpoints (Spring Boot :8080)

```yaml
openapi: 3.0.0
info:
  title: CV Assistant API Gateway
  version: 2.0.0

paths:
  # Authentication
  /api/auth/register:
    post:
      summary: Register new user
      requestBody:
        content:
          application/json:
            schema:
              type: object
              properties:
                email: {type: string}
                password: {type: string}
                name: {type: string}
      responses:
        201:
          description: User created
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/AuthResponse'

  /api/auth/login:
    post:
      summary: User login
      requestBody:
        content:
          application/json:
            schema:
              type: object
              properties:
                email: {type: string}
                password: {type: string}
      responses:
        200:
          description: Login successful
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/AuthResponse'

  # Chat (Core Feature)
  /api/chat:
    post:
      summary: Send message to chatbot
      security:
        - bearerAuth: []
      requestBody:
        content:
          application/json:
            schema:
              type: object
              properties:
                message: {type: string}
                thread_id: {type: string, nullable: true}
      responses:
        200:
          description: Chatbot response
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ChatResponse'

  /api/threads:
    get:
      summary: Get user's conversation threads
      security:
        - bearerAuth: []
      responses:
        200:
          description: List of threads
          content:
            application/json:
              schema:
                type: array
                items:
                  $ref: '#/components/schemas/Thread'

  /api/threads/{thread_id}:
    get:
      summary: Get thread with messages
      security:
        - bearerAuth: []
      responses:
        200:
          description: Thread details
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ThreadDetail'

  # CV Management
  /api/cv/upload:
    post:
      summary: Upload CV PDF
      security:
        - bearerAuth: []
      requestBody:
        content:
          multipart/form-data:
            schema:
              type: object
              properties:
                file: {type: string, format: binary}
      responses:
        200:
          description: CV uploaded
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/CVUploadResponse'

  /api/health:
    get:
      summary: Health check
      responses:
        200:
          description: Service is healthy
```

### 3.2 Chatbot Service Endpoints (FastAPI :5004)

```yaml
paths:
  /chat:
    post:
      summary: Process chat message
      requestBody:
        content:
          application/json:
            schema:
              type: object
              properties:
                user_id: {type: string}
                message: {type: string}
                thread_id: {type: string}
                context: {type: object}
      responses:
        200:
          description: AI response
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/AIResponse'

  /rag/query:
    post:
      summary: RAG knowledge base query
      requestBody:
        content:
          application/json:
            schema:
              type: object
              properties:
                query: {type: string}
                top_k: {type: integer, default: 5}
      responses:
        200:
          description: Retrieved context

  /memory/{user_id}:
    get:
      summary: Get conversation history
    delete:
      summary: Clear conversation history
```

### 3.3 NER Service Endpoints (FastAPI :5001)

```yaml
paths:
  /extract:
    post:
      summary: Extract entities from text
      requestBody:
        content:
          application/json:
            schema:
              type: object
              properties:
                text: {type: string}
                cv_id: {type: string}
      responses:
        200:
          description: Extracted entities
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ExtractionResult'

  /parse-pdf:
    post:
      summary: Parse PDF and extract
      requestBody:
        content:
          multipart/form-data:
            schema:
              type: object
              properties:
                file: {type: string, format: binary}
      responses:
        200:
          description: Parsed and extracted

  /health:
    get:
      summary: Service health check
```

### 3.4 Skill Matching Service Endpoints (FastAPI :5002)

```yaml
paths:
  /match:
    post:
      summary: Match CV skills with JD
      requestBody:
        content:
          application/json:
            schema:
              type: object
              properties:
                cv_skills: {type: array, items: {type: string}}
                jd_text: {type: string}
      responses:
        200:
          description: Match results
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/MatchResult'

  /skills/normalize:
    post:
      summary: Normalize skill names

  /health:
    get:
      summary: Service health check
```

### 3.5 Career Recommendation Service Endpoints (FastAPI :5003)

```yaml
paths:
  /recommend:
    post:
      summary: Generate career paths
      requestBody:
        content:
          application/json:
            schema:
              type: object
              properties:
                current_role: {type: string}
                target_role: {type: string}
                current_skills: {type: array, items: {type: string}}
      responses:
        200:
          description: Career roadmap
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/CareerRoadmap'

  /roles:
    get:
      summary: Get available roles from O*NET

  /health:
    get:
      summary: Service health check
```

### 3.6 Data Models

```python
# === Authentication Models ===

class User(BaseModel):
    id: str
    email: str
    name: str
    created_at: datetime

class AuthResponse(BaseModel):
    user: User
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

# === Chat/Conversation Models ===

class Message(BaseModel):
    id: str
    role: str  # "user" | "assistant"
    content: str
    created_at: datetime
    metadata: Optional[dict]  # tool calls, sources, etc.

class Thread(BaseModel):
    id: str
    user_id: str
    title: str
    created_at: datetime
    updated_at: datetime

class ThreadDetail(BaseModel):
    thread: Thread
    messages: List[Message]

class ChatRequest(BaseModel):
    message: str
    thread_id: Optional[str]

class ChatResponse(BaseModel):
    response: str
    thread_id: str
    sources: Optional[List[str]]  # RAG sources
    tool_results: Optional[dict]  # Results from tool calls

# === NER Models ===

class Entity(BaseModel):
    text: str
    type: str  # PER, ORG, DATE, LOC, SKILL, DEGREE, MAJOR, JOB_TITLE, PROJECT, CERT
    start: int
    end: int
    confidence: float

class PersonalInfo(BaseModel):
    name: Optional[str]
    email: Optional[str]
    phone: Optional[str]
    location: Optional[str]

class WorkExperience(BaseModel):
    company: Optional[str]
    title: Optional[str]
    start_date: Optional[str]
    end_date: Optional[str]
    description: Optional[str]

class Education(BaseModel):
    institution: Optional[str]
    degree: Optional[str]
    major: Optional[str]
    graduation_year: Optional[str]

class Project(BaseModel):
    name: str
    description: Optional[str]
    technologies: List[str]

class Certification(BaseModel):
    name: str
    issuer: Optional[str]
    date: Optional[str]

class CVResult(BaseModel):
    cv_id: str
    user_id: str
    raw_text: str
    entities: List[Entity]
    personal_info: PersonalInfo
    work_experience: List[WorkExperience]
    education: List[Education]
    skills: List[str]
    projects: List[Project]
    certifications: List[Certification]
    processed_at: datetime

# === Skill Matching Models ===

class MatchRequest(BaseModel):
    cv_skills: List[str]
    jd_text: str

class SkillMatch(BaseModel):
    cv_skill: str
    jd_skill: str
    match_type: str  # exact, semantic
    similarity: float

class MatchResult(BaseModel):
    jd_skills: List[str]
    exact_matches: List[str]
    semantic_matches: List[SkillMatch]
    unmatched_jd: List[str]
    unmatched_cv: List[str]
    score: float
    matched_at: datetime

# === Career Recommendation Models ===

class CareerStep(BaseModel):
    step: int
    target_role: str
    timeframe: str
    skills_to_learn: List[str]
    certifications: List[str]
    experience_needed: str

class CareerPath(BaseModel):
    type: str  # conservative, moderate, ambitious
    total_time: str
    steps: List[CareerStep]

class CareerRoadmap(BaseModel):
    current_role: str
    target_role: str
    paths: List[CareerPath]
    generated_at: datetime
```

---

## 4. Data Flow

### 4.0 Chatbot Flow (Core Feature)

```
┌────────────────────────────────────────────────────────────────────────────┐
│                         Chatbot Conversation Flow                           │
├────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  [User sends message]                                                       │
│    │                                                                        │
│    │ 1. "How can I improve my CV for a Senior Developer role?"             │
│    ▼                                                                        │
│  [React Chat UI]                                                            │
│    │                                                                        │
│    │ 2. POST /api/chat { message, thread_id }                              │
│    ▼                                                                        │
│  [API Gateway (Spring Boot)]                                                │
│    │                                                                        │
│    │ 3. Validate JWT token                                                 │
│    │ 4. Forward to Chatbot Service                                         │
│    ▼                                                                        │
│  [Chatbot Service (LlamaIndex)]                                             │
│    │                                                                        │
│    │ 5. Load conversation history from ChromaDB                            │
│    │ 6. Build context with user's CV data                                  │
│    ▼                                                                        │
│  [ReAct Agent]                                                              │
│    │                                                                        │
│    │ 7. Analyze intent:                                                    │
│    │    - General Q&A → RAG retrieval                                      │
│    │    - CV extraction → Call NER Service                                 │
│    │    - Skill matching → Call Match Service                              │
│    │    - Career advice → Call Career Service                              │
│    ▼                                                                        │
│  [Tool Calling / RAG]                                                       │
│    │                                                                        │
│    │ 8. Execute tools or retrieve knowledge                                │
│    ▼                                                                        │
│  [LLM (Llama 3.2 via Ollama)]                                               │
│    │                                                                        │
│    │ 9. Generate response with context                                     │
│    │    (5-15 seconds, CPU-only)                                           │
│    ▼                                                                        │
│  [Conversation Memory]                                                      │
│    │                                                                        │
│    │ 10. Save to ChromaDB                                                  │
│    ▼                                                                        │
│  [Response]                                                                 │
│    │                                                                        │
│    │ 11. Return ChatResponse JSON                                          │
│    ▼                                                                        │
│  [React Chat UI]                                                            │
│    │                                                                        │
│    │ 12. Display AI response with typing effect                            │
│    │ 13. Show sources if RAG was used                                      │
│    ▼                                                                        │
│  [User sees response]                                                       │
│                                                                             │
└────────────────────────────────────────────────────────────────────────────┘
```

### 4.1 Upload & Extract Flow

```
┌────────────────────────────────────────────────────────────────────────────┐
│                         Upload & Extract Flow                               │
├────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  [User]                                                                     │
│    │                                                                        │
│    │ 1. Select PDF file                                                     │
│    ▼                                                                        │
│  [React Chat UI or Upload]                                                  │
│    │                                                                        │
│    │ 2. POST /api/cv/upload (multipart/form-data)                          │
│    ▼                                                                        │
│  [API Gateway (Spring Boot)]                                                │
│    │                                                                        │
│    │ 3. Validate JWT, file (PDF, size < 10MB)                              │
│    │ 4. Forward to NER Service                                             │
│    ▼                                                                        │
│  [NER Service (FastAPI :5001)]                                              │
│    │                                                                        │
│    │ 5. Extract text using pdfplumber                                      │
│    │ 6. Clean text (normalize whitespace, fix encoding)                    │
│    │ 7. Tokenize text (BertTokenizer)                                      │
│    │ 8. Run inference (BERT + NER head)                                    │
│    │ 9. Decode BIO labels to entities                                      │
│    ▼                                                                        │
│  [Post-processor]                                                           │
│    │                                                                        │
│    │ 10. Structure entities into sections                                  │
│    │ 11. Save to PostgreSQL + ChromaDB                                     │
│    ▼                                                                        │
│  [Response]                                                                 │
│    │                                                                        │
│    │ 12. Return CVResult JSON                                              │
│    ▼                                                                        │
│  [User can edit results via chat]                                           │
│                                                                             │
└────────────────────────────────────────────────────────────────────────────┘
```

### 4.2 Skill Matching Flow

```
┌────────────────────────────────────────────────────────────────────────────┐
│                         Skill Matching Flow                                 │
├────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  [User inputs JD]                                                           │
│    │                                                                        │
│    │ 1. Enter job description text                                         │
│    ▼                                                                        │
│  [React JD Input Component]                                                 │
│    │                                                                        │
│    │ 2. POST /api/match { cv_id, jd_text }                                 │
│    ▼                                                                        │
│  [FastAPI Router]                                                           │
│    │                                                                        │
│    │ 3. Retrieve CV result by cv_id                                        │
│    ▼                                                                        │
│  [JD Processor]                                                             │
│    │                                                                        │
│    │ 4. Extract skills from JD text                                        │
│    │    (NER or keyword extraction)                                        │
│    ▼                                                                        │
│  [Skill Normalizer]                                                         │
│    │                                                                        │
│    │ 5. Normalize skills (lowercase, synonyms)                             │
│    │    "JS" → "javascript", "ML" → "machine learning"                     │
│    ▼                                                                        │
│  [Skill Matcher]                                                            │
│    │                                                                        │
│    │ 6. Exact matching                                                     │
│    │    "python" in CV, "python" in JD → match                             │
│    │                                                                        │
│    │ 7. Semantic matching (remaining skills)                               │
│    │    Embed with Sentence-BERT                                           │
│    │    Compute cosine similarity                                          │
│    │    Match if similarity ≥ 0.7                                          │
│    ▼                                                                        │
│  [Scorer]                                                                   │
│    │                                                                        │
│    │ 8. Calculate match score                                              │
│    │    score = (exact × 1.0 + semantic × sim) / total_jd × 100           │
│    ▼                                                                        │
│  [Response]                                                                 │
│    │                                                                        │
│    │ 9. Return MatchResult JSON                                            │
│    ▼                                                                        │
│  [React Match Display]                                                      │
│    │                                                                        │
│    │ 10. Show match score                                                  │
│    │ 11. Show matched/unmatched skills                                     │
│    ▼                                                                        │
│  [User sees match results]                                                  │
│                                                                             │
└────────────────────────────────────────────────────────────────────────────┘
```

---

## 5. NER Model Architecture

### 5.1 Model Structure

```
┌────────────────────────────────────────────────────────────────────────────┐
│                         BERT NER Model Architecture                         │
├────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Input: "John works at Google as Software Engineer"                        │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                     BERT Tokenizer                                   │   │
│  │  [CLS] John works at Google as Software Engineer [SEP] [PAD] ...    │   │
│  │    0     1    2    3    4    5    6       7       8     9    ...    │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│                                    ▼                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                    BERT Embedding Layer                              │   │
│  │          Token Embeddings + Position Embeddings + Segment           │   │
│  │                         768 dimensions                               │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│                                    ▼                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                    BERT Encoder (12 Layers)                          │   │
│  │  ┌────────────────────────────────────────────────────────────┐     │   │
│  │  │  Layer 1: Multi-Head Attention + FFN                       │     │   │
│  │  ├────────────────────────────────────────────────────────────┤     │   │
│  │  │  Layer 2: Multi-Head Attention + FFN                       │     │   │
│  │  ├────────────────────────────────────────────────────────────┤     │   │
│  │  │  ...                                                       │     │   │
│  │  ├────────────────────────────────────────────────────────────┤     │   │
│  │  │  Layer 12: Multi-Head Attention + FFN                      │     │   │
│  │  └────────────────────────────────────────────────────────────┘     │   │
│  │                    Output: 768-dim per token                         │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│                                    ▼                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                    Classification Head                               │   │
│  │              Linear(768 → 17) + Softmax                              │   │
│  │                                                                      │   │
│  │  Token:  [CLS] John  works at  Google as   Software Engineer [SEP]  │   │
│  │  Label:   -   B-PER   O    O   B-ORG  O   B-JOB   I-JOB      -      │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  Output: List of (token, label) pairs                                      │
│                                                                             │
└────────────────────────────────────────────────────────────────────────────┘
```

### 5.2 Training Pipeline

```
┌────────────────────────────────────────────────────────────────────────────┐
│                         NER Training Pipeline                               │
├────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────┐                                                       │
│  │ Annotated Data  │  CoNLL format from Label Studio                       │
│  │ (200+ CVs)      │                                                       │
│  └────────┬────────┘                                                       │
│           │                                                                 │
│           ▼                                                                 │
│  ┌─────────────────┐                                                       │
│  │ Data Splitter   │  Train: 70%, Val: 15%, Test: 15%                      │
│  └────────┬────────┘                                                       │
│           │                                                                 │
│           ▼                                                                 │
│  ┌─────────────────┐                                                       │
│  │ Preprocessor    │  Tokenize + Align labels                              │
│  │                 │  Handle subword tokens                                │
│  └────────┬────────┘                                                       │
│           │                                                                 │
│           ▼                                                                 │
│  ┌─────────────────┐                                                       │
│  │ DataLoader      │  Batch size: 16, Shuffle: True                        │
│  └────────┬────────┘                                                       │
│           │                                                                 │
│           ▼                                                                 │
│  ┌─────────────────┐                                                       │
│  │ Training Loop   │  10 epochs                                            │
│  │ ┌─────────────┐ │                                                       │
│  │ │ Forward     │ │  model(inputs) → logits                               │
│  │ │ Loss        │ │  CrossEntropyLoss(logits, labels)                     │
│  │ │ Backward    │ │  loss.backward()                                      │
│  │ │ Optimize    │ │  optimizer.step()                                     │
│  │ └─────────────┘ │                                                       │
│  └────────┬────────┘                                                       │
│           │                                                                 │
│           ▼                                                                 │
│  ┌─────────────────┐                                                       │
│  │ Validation      │  After each epoch                                     │
│  │                 │  Compute F1, save if best                             │
│  └────────┬────────┘                                                       │
│           │                                                                 │
│           ▼                                                                 │
│  ┌─────────────────┐                                                       │
│  │ Final Test      │  Evaluate on held-out test set                        │
│  │                 │  Report metrics                                       │
│  └────────┬────────┘                                                       │
│           │                                                                 │
│           ▼                                                                 │
│  ┌─────────────────┐                                                       │
│  │ Save Model      │  Hugging Face format                                  │
│  │                 │  model.save_pretrained()                              │
│  └─────────────────┘                                                       │
│                                                                             │
└────────────────────────────────────────────────────────────────────────────┘
```

---

## 6. Directory Structure

### 6.1 Project Structure (Microservices)

```
cv-assistant/
├── frontend/                           # React 18 Frontend
│   ├── public/
│   ├── src/
│   │   ├── components/
│   │   │   ├── chat/
│   │   │   │   ├── ChatInput.tsx
│   │   │   │   ├── MessageList.tsx
│   │   │   │   └── MessageBubble.tsx
│   │   │   ├── sidebar/
│   │   │   │   ├── ThreadList.tsx
│   │   │   │   └── UserMenu.tsx
│   │   │   └── common/
│   │   │       ├── LoadingSpinner.tsx
│   │   │       └── Header.tsx
│   │   ├── pages/
│   │   │   ├── LoginPage.tsx
│   │   │   ├── ChatPage.tsx
│   │   │   └── ProfilePage.tsx
│   │   ├── services/
│   │   │   └── api.ts
│   │   ├── hooks/
│   │   │   ├── useAuth.ts
│   │   │   └── useChat.ts
│   │   ├── types/
│   │   │   └── index.ts
│   │   ├── App.tsx
│   │   └── main.tsx
│   ├── package.json
│   ├── Dockerfile
│   └── vite.config.ts
│
├── api-gateway/                        # Spring Boot API Gateway
│   ├── src/main/java/com/cvassistant/
│   │   ├── ApiGatewayApplication.java
│   │   ├── config/
│   │   │   ├── SecurityConfig.java
│   │   │   └── CorsConfig.java
│   │   ├── controller/
│   │   │   ├── AuthController.java
│   │   │   ├── ChatController.java
│   │   │   └── CVController.java
│   │   ├── service/
│   │   │   ├── AuthService.java
│   │   │   └── ProxyService.java
│   │   ├── model/
│   │   │   ├── User.java
│   │   │   └── Thread.java
│   │   ├── repository/
│   │   │   └── UserRepository.java
│   │   └── security/
│   │       ├── JwtUtil.java
│   │       └── JwtFilter.java
│   ├── src/main/resources/
│   │   └── application.yml
│   ├── pom.xml
│   └── Dockerfile
│
├── services/
│   ├── ner-service/                    # NER Service (FastAPI :5001)
│   │   ├── app/
│   │   │   ├── __init__.py
│   │   │   ├── main.py
│   │   │   ├── routers/
│   │   │   │   └── extraction.py
│   │   │   ├── services/
│   │   │   │   ├── pdf_service.py
│   │   │   │   └── ner_service.py
│   │   │   └── models/
│   │   │       └── schemas.py
│   │   ├── requirements.txt
│   │   └── Dockerfile
│   │
│   ├── skill-service/                  # Skill Matching (FastAPI :5002)
│   │   ├── app/
│   │   │   ├── __init__.py
│   │   │   ├── main.py
│   │   │   ├── services/
│   │   │   │   ├── taxonomy.py
│   │   │   │   └── matcher.py
│   │   │   └── data/
│   │   │       └── onet_skills.json
│   │   ├── requirements.txt
│   │   └── Dockerfile
│   │
│   ├── career-service/                 # Career Recommendation (FastAPI :5003)
│   │   ├── app/
│   │   │   ├── __init__.py
│   │   │   ├── main.py
│   │   │   ├── services/
│   │   │   │   └── career_path.py
│   │   │   └── data/
│   │   │       └── onet_careers.json
│   │   ├── requirements.txt
│   │   └── Dockerfile
│   │
│   └── chatbot-service/                # Chatbot (FastAPI + LlamaIndex :5004)
│       ├── app/
│       │   ├── __init__.py
│       │   ├── main.py
│       │   ├── agent/
│       │   │   ├── agent.py
│       │   │   └── tools.py
│       │   ├── rag/
│       │   │   ├── indexer.py
│       │   │   └── retriever.py
│       │   ├── memory/
│       │   │   └── conversation.py
│       │   └── prompts/
│       │       └── system_prompts.py
│       ├── requirements.txt
│       └── Dockerfile
│
├── ml/                            # ML training
│   ├── notebooks/
│   │   ├── 01_data_preprocessing.ipynb
│   │   ├── 02_model_training.ipynb
│   │   └── 03_evaluation.ipynb
│   ├── src/
│   │   ├── __init__.py
│   │   ├── data/
│   │   │   ├── __init__.py
│   │   │   ├── preprocessor.py
│   │   │   └── dataset.py
│   │   ├── model/
│   │   │   ├── __init__.py
│   │   │   ├── ner_model.py
│   │   │   └── trainer.py
│   │   └── evaluation/
│   │       ├── __init__.py
│   │       └── metrics.py
│   ├── config/
│   │   └── training_config.yaml
│   └── requirements.txt
│
├── data/                          # Data storage
│   ├── raw/                       # Raw PDFs
│   ├── processed/                 # Extracted text
│   ├── annotated/                 # Label Studio exports
│   └── splits/                    # Train/val/test
│
├── models/                        # Trained models
│   └── ner-bert-cv/
│       ├── config.json
│       ├── model.safetensors
│       └── tokenizer/
│
├── documents/                     # This documentation
│   ├── 01_requirements_intake.md
│   ├── ...
│   └── 14_feedback_improvement.md
│
├── docker-compose.yml
├── README.md
└── .gitignore
```

---

## 7. Deployment Architecture

### 7.1 Development Environment

```
┌────────────────────────────────────────────────────────────────────────────┐
│                    Development Environment (docker-compose)                 │
├────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Local Machine (Acer Aspire 7, 16GB RAM, CPU-only)                         │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                                                                       │  │
│  │  ┌─────────────┐    ┌─────────────┐    ┌─────────────────────────┐  │  │
│  │  │ Frontend    │    │ API Gateway │    │ Python Services         │  │  │
│  │  │ React :3000 │───▶│ Spring :8080│───▶│ NER:5001 Skill:5002    │  │  │
│  │  └─────────────┘    └─────────────┘    │ Career:5003 Chat:5004  │  │  │
│  │                                        └─────────────────────────┘  │  │
│  │                                                   │                  │  │
│  │         ┌─────────────────────────────────────────┤                  │  │
│  │         ▼                   ▼                     ▼                  │  │
│  │  ┌─────────────┐    ┌─────────────┐    ┌─────────────────────────┐  │  │
│  │  │ PostgreSQL  │    │ ChromaDB    │    │ Ollama                  │  │  │
│  │  │ :5432       │    │ :8000       │    │ Llama 3.2 (3B) :11434   │  │  │
│  │  └─────────────┘    └─────────────┘    └─────────────────────────┘  │  │
│  │                                                                       │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  Google Colab (NER Training only)                                           │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │  ┌─────────────┐    ┌─────────────┐                                  │  │
│  │  │ Training    │    │ T4 GPU      │                                  │  │
│  │  │ Notebook    │───▶│ (16GB VRAM) │                                  │  │
│  │  └─────────────┘    └─────────────┘                                  │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
└────────────────────────────────────────────────────────────────────────────┘
```

### 7.2 Demo Environment (Docker Compose)

```
┌────────────────────────────────────────────────────────────────────────────┐
│                    Demo Environment (docker-compose up)                     │
├────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                                                                       │  │
│  │  ┌─────────────┐                                                     │  │
│  │  │ frontend    │  React + Nginx                                      │  │
│  │  │ :3000       │  Static files served                                │  │
│  │  └──────┬──────┘                                                     │  │
│  │         │                                                            │  │
│  │         ▼                                                            │  │
│  │  ┌─────────────┐                                                     │  │
│  │  │ api-gateway │  Spring Boot + JWT Auth                             │  │
│  │  │ :8080       │  Routes to microservices                            │  │
│  │  └──────┬──────┘                                                     │  │
│  │         │                                                            │  │
│  │    ┌────┴────┬─────────┬─────────┐                                   │  │
│  │    ▼         ▼         ▼         ▼                                   │  │
│  │ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────────┐                             │  │
│  │ │ ner  │ │skill │ │career│ │ chatbot  │                             │  │
│  │ │:5001 │ │:5002 │ │:5003 │ │ :5004    │                             │  │
│  │ └──────┘ └──────┘ └──────┘ └────┬─────┘                             │  │
│  │                                  │                                   │  │
│  │         ┌────────────────────────┤                                   │  │
│  │         ▼                        ▼                                   │  │
│  │  ┌─────────────┐          ┌─────────────┐                           │  │
│  │  │ chromadb    │          │ ollama      │                           │  │
│  │  │ :8000       │          │ :11434      │                           │  │
│  │  │ (RAG+Memory)│          │ (Llama 3.2) │                           │  │
│  │  └─────────────┘          └─────────────┘                           │  │
│  │                                                                       │  │
│  │  ┌─────────────┐                                                     │  │
│  │  │ postgres    │  Users, CVs, Threads, Messages                      │  │
│  │  │ :5432       │                                                     │  │
│  │  └─────────────┘                                                     │  │
│  │                                                                       │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  Access: http://localhost                                                   │
│                                                                             │
└────────────────────────────────────────────────────────────────────────────┘
```

---

## 8. Security Considerations

### 8.1 Data Security

```
Data Security Measures:
├── Anonymization
│   ├── Remove PII before annotation
│   ├── Replace names with [NAME]
│   └── Mask emails, phones
│
├── Storage
│   ├── Local storage only
│   ├── No cloud uploads of raw data
│   └── .gitignore for data folders
│
└── Access Control
    ├── Team-only access to raw data
    └── No public sharing of CVs
```

### 8.2 API Security (Basic for Demo)

```
API Security:
├── CORS
│   ├── Allow localhost origins
│   └── Restrict in production
│
├── File Upload
│   ├── File type validation (PDF only)
│   ├── File size limit (10MB)
│   └── Virus scan (optional)
│
└── Rate Limiting (optional for demo)
    └── Basic throttling
```

---

*Document created as part of CV-NER Research Project documentation.*
