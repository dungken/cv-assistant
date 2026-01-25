# 17. API Specifications

> **Document Version**: 1.0
> **Last Updated**: 2026-01-23
> **Status**: Approved
> **Product Name**: CV Assistant
> **Related Documents**: [09_system_architecture.md](./09_system_architecture.md), [18_data_models.md](./18_data_models.md)

---

## 1. API Overview

CV Assistant uses a microservices architecture with the following services:

| Service | Port | Base URL | Description |
|---------|------|----------|-------------|
| API Gateway | 8080 | `/api` | Auth + Routing (Spring Boot) |
| NER Service | 5001 | `/` | CV extraction (FastAPI) |
| Skill Service | 5002 | `/` | Skill matching (FastAPI) |
| Career Service | 5003 | `/` | Career paths (FastAPI) |
| Chatbot Service | 5004 | `/` | Conversational AI (FastAPI) |

---

## 2. API Gateway (Spring Boot - Port 8080)

### 2.1 Authentication Endpoints

#### POST /api/auth/register

Register a new user account.

**Request**:
```json
{
  "email": "user@example.com",
  "password": "securePassword123",
  "name": "John Doe"
}
```

**Response** (201 Created):
```json
{
  "user": {
    "id": "usr_abc123",
    "email": "user@example.com",
    "name": "John Doe",
    "created_at": "2026-01-23T10:00:00Z"
  },
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "expires_in": 86400
}
```

**Errors**:
- `400`: Invalid email format or weak password
- `409`: Email already registered

---

#### POST /api/auth/login

Authenticate user and get tokens.

**Request**:
```json
{
  "email": "user@example.com",
  "password": "securePassword123"
}
```

**Response** (200 OK):
```json
{
  "user": {
    "id": "usr_abc123",
    "email": "user@example.com",
    "name": "John Doe",
    "created_at": "2026-01-23T10:00:00Z"
  },
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "expires_in": 86400
}
```

**Errors**:
- `401`: Invalid credentials

---

#### POST /api/auth/refresh

Refresh access token.

**Request**:
```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIs..."
}
```

**Response** (200 OK):
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "expires_in": 86400
}
```

---

### 2.2 Chat Endpoints

All chat endpoints require `Authorization: Bearer <token>` header.

#### POST /api/chat

Send a message to the chatbot.

**Request**:
```json
{
  "message": "How can I improve my CV for a Senior Developer role?",
  "thread_id": "thr_xyz789"  // optional, creates new thread if null
}
```

**Response** (200 OK):
```json
{
  "response": "To improve your CV for a Senior Developer role, I recommend focusing on...",
  "thread_id": "thr_xyz789",
  "message_id": "msg_abc123",
  "sources": [
    "O*NET: Software Developer Career Guide",
    "CV Writing Best Practices"
  ],
  "tool_results": {
    "ner_extraction": null,
    "skill_matching": null,
    "career_recommendation": null
  },
  "created_at": "2026-01-23T10:05:00Z"
}
```

**Response Time**: 5-15 seconds (CPU-only LLM)

---

#### GET /api/threads

Get user's conversation threads.

**Response** (200 OK):
```json
{
  "threads": [
    {
      "id": "thr_xyz789",
      "title": "CV Improvement for Senior Developer",
      "message_count": 5,
      "created_at": "2026-01-23T10:00:00Z",
      "updated_at": "2026-01-23T10:30:00Z"
    },
    {
      "id": "thr_abc456",
      "title": "Skill Gap Analysis",
      "message_count": 3,
      "created_at": "2026-01-22T15:00:00Z",
      "updated_at": "2026-01-22T15:45:00Z"
    }
  ],
  "total": 2
}
```

---

#### GET /api/threads/{thread_id}

Get a specific thread with all messages.

**Response** (200 OK):
```json
{
  "thread": {
    "id": "thr_xyz789",
    "title": "CV Improvement for Senior Developer",
    "created_at": "2026-01-23T10:00:00Z",
    "updated_at": "2026-01-23T10:30:00Z"
  },
  "messages": [
    {
      "id": "msg_001",
      "role": "user",
      "content": "How can I improve my CV?",
      "created_at": "2026-01-23T10:00:00Z"
    },
    {
      "id": "msg_002",
      "role": "assistant",
      "content": "I'd be happy to help! First, could you...",
      "created_at": "2026-01-23T10:00:15Z",
      "metadata": {
        "sources": ["CV Writing Guide"]
      }
    }
  ]
}
```

---

#### DELETE /api/threads/{thread_id}

Delete a conversation thread.

**Response** (204 No Content)

---

### 2.3 CV Management Endpoints

#### POST /api/cv/upload

Upload a CV PDF for extraction.

**Request**: `multipart/form-data`
- `file`: PDF file (max 10MB)

**Response** (200 OK):
```json
{
  "cv_id": "cv_abc123",
  "status": "processed",
  "extraction_result": {
    "personal_info": {
      "name": "John Doe",
      "email": "john@example.com",
      "phone": "+1234567890",
      "location": "Ho Chi Minh City"
    },
    "work_experience": [...],
    "education": [...],
    "skills": ["Python", "Java", "Machine Learning"],
    "projects": [...],
    "certifications": [...]
  },
  "entities": [
    {"text": "John Doe", "type": "PER", "start": 0, "end": 8, "confidence": 0.95}
  ],
  "processed_at": "2026-01-23T10:00:00Z"
}
```

**Errors**:
- `400`: Invalid file format (not PDF)
- `413`: File too large (>10MB)
- `422`: Cannot extract text (scanned PDF)

---

#### GET /api/cv

Get user's uploaded CVs.

**Response** (200 OK):
```json
{
  "cvs": [
    {
      "id": "cv_abc123",
      "filename": "john_doe_cv.pdf",
      "uploaded_at": "2026-01-23T10:00:00Z",
      "skills_count": 15
    }
  ],
  "total": 1
}
```

---

#### GET /api/cv/{cv_id}

Get a specific CV's extraction result.

**Response** (200 OK): Same as upload response

---

#### PUT /api/cv/{cv_id}

Update/edit extracted CV data.

**Request**:
```json
{
  "personal_info": {
    "name": "John Doe Updated"
  },
  "skills": ["Python", "Java", "Machine Learning", "Docker"]
}
```

**Response** (200 OK): Updated CV data

---

### 2.4 Health Check

#### GET /api/health

**Response** (200 OK):
```json
{
  "status": "healthy",
  "services": {
    "api_gateway": "up",
    "ner_service": "up",
    "skill_service": "up",
    "career_service": "up",
    "chatbot_service": "up",
    "database": "up"
  },
  "timestamp": "2026-01-23T10:00:00Z"
}
```

---

## 3. NER Service (FastAPI - Port 5001)

Internal service called by API Gateway and Chatbot Service.

### 3.1 POST /extract

Extract entities from text.

**Request**:
```json
{
  "text": "John Doe is a Software Engineer at Google with 5 years of Python experience.",
  "cv_id": "cv_abc123"
}
```

**Response** (200 OK):
```json
{
  "entities": [
    {"text": "John Doe", "type": "PER", "start": 0, "end": 8, "confidence": 0.95},
    {"text": "Software Engineer", "type": "JOB_TITLE", "start": 14, "end": 31, "confidence": 0.92},
    {"text": "Google", "type": "ORG", "start": 35, "end": 41, "confidence": 0.98},
    {"text": "5 years", "type": "DATE", "start": 47, "end": 54, "confidence": 0.88},
    {"text": "Python", "type": "SKILL", "start": 58, "end": 64, "confidence": 0.96}
  ],
  "structured_data": {
    "personal_info": {"name": "John Doe"},
    "work_experience": [{"company": "Google", "title": "Software Engineer"}],
    "skills": ["Python"]
  },
  "processing_time_ms": 245
}
```

---

### 3.2 POST /parse-pdf

Parse PDF and extract entities.

**Request**: `multipart/form-data`
- `file`: PDF file

**Response** (200 OK):
```json
{
  "raw_text": "John Doe\nSoftware Engineer...",
  "entities": [...],
  "structured_data": {...},
  "page_count": 2,
  "processing_time_ms": 1250
}
```

---

### 3.3 GET /health

**Response** (200 OK):
```json
{
  "status": "healthy",
  "model_loaded": true,
  "model_name": "bert-base-uncased-cv-ner"
}
```

---

## 4. Skill Matching Service (FastAPI - Port 5002)

### 4.1 POST /match

Match CV skills with job description.

**Request**:
```json
{
  "cv_skills": ["Python", "Machine Learning", "SQL", "TensorFlow"],
  "jd_text": "We are looking for a Data Scientist with Python, Deep Learning, and SQL experience."
}
```

**Response** (200 OK):
```json
{
  "jd_skills": ["Python", "Deep Learning", "SQL"],
  "exact_matches": ["Python", "SQL"],
  "semantic_matches": [
    {
      "cv_skill": "Machine Learning",
      "jd_skill": "Deep Learning",
      "similarity": 0.85
    }
  ],
  "unmatched_jd": [],
  "unmatched_cv": ["TensorFlow"],
  "score": 95.0,
  "breakdown": {
    "exact_count": 2,
    "semantic_count": 1,
    "total_jd_skills": 3
  },
  "processing_time_ms": 120
}
```

---

### 4.2 POST /skills/extract

Extract skills from text (JD or CV).

**Request**:
```json
{
  "text": "Requirements: Python, SQL, Machine Learning, 3+ years experience"
}
```

**Response** (200 OK):
```json
{
  "skills": ["Python", "SQL", "Machine Learning"],
  "normalized_skills": ["python", "sql", "machine learning"]
}
```

---

### 4.3 GET /skills/taxonomy

Get skill taxonomy from O*NET.

**Response** (200 OK):
```json
{
  "categories": [
    {
      "name": "Programming Languages",
      "skills": ["Python", "Java", "JavaScript", "C++", "Go"]
    },
    {
      "name": "Frameworks",
      "skills": ["React", "Angular", "Django", "Spring", "FastAPI"]
    }
  ],
  "total_skills": 500
}
```

---

## 5. Career Recommendation Service (FastAPI - Port 5003)

### 5.1 POST /recommend

Generate career path recommendations.

**Request**:
```json
{
  "current_role": "Junior Developer",
  "target_role": "Tech Lead",
  "current_skills": ["Python", "Git", "SQL"]
}
```

**Response** (200 OK):
```json
{
  "current_role": "Junior Developer",
  "target_role": "Tech Lead",
  "paths": [
    {
      "type": "conservative",
      "total_time": "6-8 years",
      "steps": [
        {
          "step": 1,
          "target_role": "Mid-level Developer",
          "timeframe": "2-3 years",
          "skills_to_learn": ["System Design", "CI/CD", "Docker"],
          "certifications": ["AWS Solutions Architect"],
          "experience_needed": "Lead small features"
        },
        {
          "step": 2,
          "target_role": "Senior Developer",
          "timeframe": "2-3 years",
          "skills_to_learn": ["Architecture", "Mentoring", "Code Review"],
          "certifications": [],
          "experience_needed": "Lead team of 3-5"
        },
        {
          "step": 3,
          "target_role": "Tech Lead",
          "timeframe": "1-2 years",
          "skills_to_learn": ["Strategic Planning", "Stakeholder Management"],
          "certifications": [],
          "experience_needed": "Lead cross-functional projects"
        }
      ]
    },
    {
      "type": "moderate",
      "total_time": "4-6 years",
      "steps": [...]
    },
    {
      "type": "ambitious",
      "total_time": "3-4 years",
      "steps": [...]
    }
  ],
  "skill_gap": {
    "missing": ["System Design", "Architecture", "Leadership"],
    "to_improve": ["CI/CD", "Docker"]
  },
  "generated_at": "2026-01-23T10:00:00Z"
}
```

---

### 5.2 GET /roles

Get available roles from O*NET.

**Query Parameters**:
- `search`: Filter by keyword
- `category`: Filter by category

**Response** (200 OK):
```json
{
  "roles": [
    {
      "id": "15-1252.00",
      "title": "Software Developer",
      "category": "Computer and Mathematical",
      "median_salary": "$120,000"
    },
    {
      "id": "15-2051.00",
      "title": "Data Scientist",
      "category": "Computer and Mathematical",
      "median_salary": "$130,000"
    }
  ],
  "total": 50
}
```

---

## 6. Chatbot Service (FastAPI - Port 5004)

### 6.1 POST /chat

Process chat message with LlamaIndex agent.

**Request**:
```json
{
  "user_id": "usr_abc123",
  "message": "Analyze my CV and tell me what skills I'm missing for a Data Scientist role",
  "thread_id": "thr_xyz789",
  "context": {
    "cv_id": "cv_abc123",
    "cv_skills": ["Python", "SQL", "Machine Learning"]
  }
}
```

**Response** (200 OK):
```json
{
  "response": "Based on your CV, you have a strong foundation with Python, SQL, and Machine Learning. For a Data Scientist role, I recommend developing these additional skills:\n\n1. **Deep Learning** - TensorFlow or PyTorch\n2. **Statistical Analysis** - R or advanced Python stats\n3. **Data Visualization** - Tableau or Power BI\n\nWould you like me to create a detailed career roadmap?",
  "thread_id": "thr_xyz789",
  "message_id": "msg_def456",
  "tools_used": ["skill_matching", "career_recommendation"],
  "tool_results": {
    "skill_matching": {
      "score": 72,
      "missing_skills": ["Deep Learning", "Statistics", "Visualization"]
    }
  },
  "sources": [
    "O*NET: Data Scientist Requirements",
    "Career Guide: Data Science Path"
  ],
  "response_time_ms": 8500
}
```

---

### 6.2 POST /rag/query

Query RAG knowledge base directly.

**Request**:
```json
{
  "query": "What are the key skills for a Data Scientist?",
  "top_k": 5
}
```

**Response** (200 OK):
```json
{
  "results": [
    {
      "content": "Data Scientists typically need: Python, R, SQL, Machine Learning...",
      "source": "O*NET Database",
      "score": 0.92
    }
  ],
  "query_time_ms": 150
}
```

---

### 6.3 GET /memory/{user_id}

Get conversation history for a user.

**Response** (200 OK):
```json
{
  "conversations": [
    {
      "thread_id": "thr_xyz789",
      "messages": [...]
    }
  ],
  "total_messages": 25
}
```

---

### 6.4 DELETE /memory/{user_id}

Clear conversation history.

**Response** (204 No Content)

---

## 7. Error Response Format

All services use consistent error format:

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid email format",
    "details": {
      "field": "email",
      "value": "invalid-email"
    }
  },
  "timestamp": "2026-01-23T10:00:00Z",
  "request_id": "req_abc123"
}
```

### Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `VALIDATION_ERROR` | 400 | Invalid request data |
| `UNAUTHORIZED` | 401 | Missing or invalid token |
| `FORBIDDEN` | 403 | Insufficient permissions |
| `NOT_FOUND` | 404 | Resource not found |
| `CONFLICT` | 409 | Resource conflict (e.g., duplicate) |
| `UNPROCESSABLE` | 422 | Cannot process (e.g., scanned PDF) |
| `RATE_LIMITED` | 429 | Too many requests |
| `SERVER_ERROR` | 500 | Internal server error |
| `SERVICE_UNAVAILABLE` | 503 | Service temporarily unavailable |

---

## 8. Rate Limiting

| Endpoint Type | Rate Limit |
|---------------|------------|
| Auth endpoints | 10 req/min |
| Chat endpoints | 20 req/min |
| CV upload | 5 req/min |
| Other endpoints | 60 req/min |

---

*Document created as part of CV Assistant Research Project documentation.*
