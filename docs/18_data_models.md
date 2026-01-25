# 18. Data Models

> **Document Version**: 1.0
> **Last Updated**: 2026-01-23
> **Status**: Approved
> **Product Name**: CV Assistant
> **Related Documents**: [09_system_architecture.md](./09_system_architecture.md), [17_api_specifications.md](./17_api_specifications.md)

---

## 1. Overview

This document defines all data models used in CV Assistant, including database schemas, API models, and vector store structures.

---

## 2. PostgreSQL Database Schema

### 2.1 Users Table

```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    name VARCHAR(255) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_login_at TIMESTAMP WITH TIME ZONE,
    is_active BOOLEAN DEFAULT TRUE
);

CREATE INDEX idx_users_email ON users(email);
```

### 2.2 CVs Table

```sql
CREATE TABLE cvs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    filename VARCHAR(255) NOT NULL,
    raw_text TEXT,
    extraction_result JSONB,
    status VARCHAR(50) DEFAULT 'pending',  -- pending, processing, processed, failed
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_cvs_user_id ON cvs(user_id);
CREATE INDEX idx_cvs_status ON cvs(status);
```

### 2.3 Threads Table

```sql
CREATE TABLE threads (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(500),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_threads_user_id ON threads(user_id);
CREATE INDEX idx_threads_updated_at ON threads(updated_at DESC);
```

### 2.4 Messages Table

```sql
CREATE TABLE messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    thread_id UUID NOT NULL REFERENCES threads(id) ON DELETE CASCADE,
    role VARCHAR(20) NOT NULL,  -- 'user' or 'assistant'
    content TEXT NOT NULL,
    metadata JSONB,  -- sources, tool_results, etc.
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_messages_thread_id ON messages(thread_id);
CREATE INDEX idx_messages_created_at ON messages(created_at);
```

### 2.5 Refresh Tokens Table

```sql
CREATE TABLE refresh_tokens (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token_hash VARCHAR(255) NOT NULL,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    revoked_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_refresh_tokens_user_id ON refresh_tokens(user_id);
CREATE INDEX idx_refresh_tokens_expires ON refresh_tokens(expires_at);
```

---

## 3. API Data Models (Pydantic/Java Records)

### 3.1 Authentication Models

```python
# Python (FastAPI/Pydantic)

class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    name: str = Field(min_length=1, max_length=255)

class UserResponse(BaseModel):
    id: str
    email: str
    name: str
    created_at: datetime

class AuthResponse(BaseModel):
    user: UserResponse
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = 86400

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class RefreshRequest(BaseModel):
    refresh_token: str
```

```java
// Java (Spring Boot Records)

public record UserCreateRequest(
    @Email String email,
    @Size(min = 8) String password,
    @NotBlank String name
) {}

public record UserResponse(
    String id,
    String email,
    String name,
    Instant createdAt
) {}

public record AuthResponse(
    UserResponse user,
    String accessToken,
    String refreshToken,
    String tokenType,
    int expiresIn
) {}
```

### 3.2 Chat/Conversation Models

```python
class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=10000)
    thread_id: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    thread_id: str
    message_id: str
    sources: Optional[List[str]] = None
    tool_results: Optional[dict] = None
    created_at: datetime

class Message(BaseModel):
    id: str
    role: Literal["user", "assistant"]
    content: str
    created_at: datetime
    metadata: Optional[dict] = None

class Thread(BaseModel):
    id: str
    title: Optional[str]
    message_count: int
    created_at: datetime
    updated_at: datetime

class ThreadDetail(BaseModel):
    thread: Thread
    messages: List[Message]
```

### 3.3 NER/CV Models

```python
class Entity(BaseModel):
    text: str
    type: str  # PER, ORG, DATE, LOC, SKILL, DEGREE, MAJOR, JOB_TITLE, PROJECT, CERT
    start: int
    end: int
    confidence: float = Field(ge=0, le=1)

class PersonalInfo(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    location: Optional[str] = None

class WorkExperience(BaseModel):
    company: Optional[str] = None
    title: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    description: Optional[str] = None
    location: Optional[str] = None

class Education(BaseModel):
    institution: Optional[str] = None
    degree: Optional[str] = None
    major: Optional[str] = None
    graduation_year: Optional[str] = None
    gpa: Optional[str] = None

class Project(BaseModel):
    name: str
    description: Optional[str] = None
    technologies: List[str] = []
    url: Optional[str] = None

class Certification(BaseModel):
    name: str
    issuer: Optional[str] = None
    date: Optional[str] = None
    expiry: Optional[str] = None
    credential_id: Optional[str] = None

class CVExtractionResult(BaseModel):
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

class ExtractionRequest(BaseModel):
    text: str
    cv_id: Optional[str] = None
```

### 3.4 Skill Matching Models

```python
class MatchRequest(BaseModel):
    cv_skills: List[str]
    jd_text: str

class SemanticMatch(BaseModel):
    cv_skill: str
    jd_skill: str
    similarity: float = Field(ge=0, le=1)

class MatchResult(BaseModel):
    jd_skills: List[str]
    exact_matches: List[str]
    semantic_matches: List[SemanticMatch]
    unmatched_jd: List[str]
    unmatched_cv: List[str]
    score: float = Field(ge=0, le=100)
    breakdown: dict
    processing_time_ms: int
```

### 3.5 Career Recommendation Models

```python
class CareerStep(BaseModel):
    step: int
    target_role: str
    timeframe: str
    skills_to_learn: List[str]
    certifications: List[str]
    experience_needed: str

class CareerPath(BaseModel):
    type: Literal["conservative", "moderate", "ambitious"]
    total_time: str
    steps: List[CareerStep]

class SkillGap(BaseModel):
    missing: List[str]
    to_improve: List[str]

class CareerRecommendation(BaseModel):
    current_role: str
    target_role: str
    paths: List[CareerPath]
    skill_gap: SkillGap
    generated_at: datetime

class CareerRequest(BaseModel):
    current_role: str
    target_role: str
    current_skills: List[str] = []
```

---

## 4. ChromaDB Collections

### 4.1 Knowledge Base Collection

```python
# Collection for RAG knowledge base
collection_name = "cv_assistant_knowledge"

# Document structure
{
    "id": "doc_abc123",
    "document": "Software Engineers typically need skills in...",
    "metadata": {
        "source": "O*NET Database",
        "category": "career_guide",
        "topic": "software_engineering",
        "created_at": "2026-01-23T10:00:00Z"
    }
}

# Embedding model: all-MiniLM-L6-v2 (384 dimensions)
```

### 4.2 Conversation Memory Collection

```python
# Collection for conversation history (per user)
collection_name = f"conversations_{user_id}"

# Document structure
{
    "id": "msg_abc123",
    "document": "User asked about improving CV for Senior Developer role",
    "metadata": {
        "thread_id": "thr_xyz789",
        "role": "user",
        "timestamp": "2026-01-23T10:00:00Z",
        "user_id": "usr_abc123"
    }
}
```

### 4.3 CV Embeddings Collection

```python
# Collection for user CV data
collection_name = "cv_embeddings"

# Document structure
{
    "id": "cv_section_abc123",
    "document": "5 years of Python development experience at Google...",
    "metadata": {
        "cv_id": "cv_abc123",
        "user_id": "usr_abc123",
        "section": "work_experience",
        "created_at": "2026-01-23T10:00:00Z"
    }
}
```

---

## 5. NER Model Data Format

### 5.1 Training Data (CoNLL Format)

```
John    B-PER
Doe     I-PER
is      O
a       O
Software    B-JOB_TITLE
Engineer    I-JOB_TITLE
at      O
Google  B-ORG
.       O
```

### 5.2 Label Mapping

```python
LABEL2ID = {
    "O": 0,
    "B-PER": 1, "I-PER": 2,
    "B-ORG": 3, "I-ORG": 4,
    "B-DATE": 5, "I-DATE": 6,
    "B-LOC": 7, "I-LOC": 8,
    "B-SKILL": 9, "I-SKILL": 10,
    "B-DEGREE": 11, "I-DEGREE": 12,
    "B-MAJOR": 13, "I-MAJOR": 14,
    "B-JOB_TITLE": 15, "I-JOB_TITLE": 16,
    "B-PROJECT": 17, "I-PROJECT": 18,
    "B-CERT": 19, "I-CERT": 20
}

ID2LABEL = {v: k for k, v in LABEL2ID.items()}
```

### 5.3 Model Input/Output

```python
# Input
{
    "input_ids": [101, 2198, 2139, ...],      # Token IDs
    "attention_mask": [1, 1, 1, ...],         # Attention mask
    "token_type_ids": [0, 0, 0, ...]          # Segment IDs
}

# Output
{
    "logits": [[0.1, 0.8, 0.1, ...]],         # Shape: (batch, seq_len, 21)
    "predictions": [0, 1, 2, 0, ...]          # Argmax of logits
}
```

---

## 6. O*NET Data Structures

### 6.1 Skills Taxonomy

```json
{
  "skills": [
    {
      "id": "2.A.1.a",
      "name": "Reading Comprehension",
      "category": "Basic Skills",
      "description": "Understanding written sentences..."
    },
    {
      "id": "2.B.3.a",
      "name": "Programming",
      "category": "Technical Skills",
      "description": "Writing computer programs..."
    }
  ]
}
```

### 6.2 Occupations

```json
{
  "occupations": [
    {
      "code": "15-1252.00",
      "title": "Software Developers",
      "description": "Research, design, and develop...",
      "median_salary": 120730,
      "required_skills": ["2.B.3.a", "2.A.1.a"],
      "related_occupations": ["15-1253.00", "15-1254.00"]
    }
  ]
}
```

### 6.3 Career Transitions

```json
{
  "transitions": [
    {
      "from_occupation": "15-1252.00",
      "to_occupation": "11-3021.00",
      "typical_time_years": 5,
      "skill_overlap": 0.65,
      "common_path": true
    }
  ]
}
```

---

## 7. Error Models

```python
class ErrorDetail(BaseModel):
    field: Optional[str] = None
    value: Optional[Any] = None
    message: str

class ErrorResponse(BaseModel):
    error: dict  # {code, message, details}
    timestamp: datetime
    request_id: str

# Example
{
    "error": {
        "code": "VALIDATION_ERROR",
        "message": "Invalid request data",
        "details": [
            {"field": "email", "message": "Invalid email format"}
        ]
    },
    "timestamp": "2026-01-23T10:00:00Z",
    "request_id": "req_abc123"
}
```

---

## 8. Configuration Models

### 8.1 Service Configuration

```yaml
# config.yaml
database:
  host: postgres
  port: 5432
  name: cv_assistant
  user: ${DB_USER}
  password: ${DB_PASSWORD}

chromadb:
  host: chromadb
  port: 8000

ollama:
  host: ollama
  port: 11434
  model: llama3.2:3b

services:
  ner:
    url: http://ner-service:5001
    timeout: 30
  skill:
    url: http://skill-service:5002
    timeout: 10
  career:
    url: http://career-service:5003
    timeout: 15
  chatbot:
    url: http://chatbot-service:5004
    timeout: 60

jwt:
  secret: ${JWT_SECRET}
  access_token_expire_minutes: 1440
  refresh_token_expire_days: 7
```

---

*Document created as part of CV Assistant Research Project documentation.*
