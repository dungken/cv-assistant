# 04. Requirements Classification - Phân Loại Yêu Cầu

> **Document Version**: 2.0
> **Last Updated**: 2026-01-23
> **Status**: Approved
> **Product Name**: CV Assistant
> **Related Documents**: [03_feasibility_analysis.md](./03_feasibility_analysis.md), [05_problem_decomposition.md](./05_problem_decomposition.md)

---

## Feature Priority Matrix

| # | Feature | Priority | Status |
|---|---------|----------|--------|
| 1 | **Chatbot (Core)** | **P0 - MUST** | Planned |
| 2 | NER Extraction | P0 - MUST | Planned |
| 3 | Skill Matching | P1 - Should | Planned |
| 4 | Career Roadmap | P1 - Should | Planned |
| 5 | User Auth | P1 - Should | Planned |
| 6 | CV Score (basic) | P2 - Nice | Planned |
| 7 | Visual Roadmap | P2 - Nice | Planned |

---

## 1. Functional Requirements (FR)

### 1.0 Chatbot Requirements (P0 - CORE)

| ID | Requirement | Priority | Status |
|----|-------------|----------|--------|
| **FR-CHAT-01** | Hệ thống phải cung cấp Conversational AI Assistant cho career/CV guidance | Critical | Planned |
| **FR-CHAT-02** | Chatbot phải tích hợp với các AI services: NER, Skill Matching, Career Recommendation | Critical | Planned |
| **FR-CHAT-03** | User có thể edit tất cả extracted results từ chatbot | High | Planned |
| **FR-CHAT-04** | Conversation memory phải persistent per user | High | Planned |

#### FR-CHAT-01: Conversational AI Core
```
Role: General Q&A về CV, career, job market
UI Style: ChatGPT/Gemini - Conversation-first
Availability: Luôn available, không phụ thuộc flow

Technical Stack:
├── LLM: Llama 3.2 (3B) - CPU-only, 16GB RAM
├── Agent Framework: LlamaIndex (ReAct agent style)
├── Vector DB: ChromaDB
└── Tool Calling: Auto-detect intent (LLM tự hiểu và gọi services)

Acceptance Criteria:
├── Response time: 5-15 seconds (CPU-only acceptable)
├── Có loading indicator khi đang xử lý
├── Context-aware responses dựa trên user's CV
└── Proper error handling với user-friendly messages
```

#### FR-CHAT-02: RAG Knowledge Base
```
Data Sources:
├── O*NET Database - Jobs, careers, skills
├── CV Writing Guides - Tips, best practices
├── Job Market Info - Trends, salary data
└── User's Own CV - Personalized context

Output: Context-enhanced LLM responses
Storage: ChromaDB vector database

Acceptance Criteria:
├── Relevant context retrieval ≥ 70% accuracy
├── Response includes source attribution when applicable
└── Knowledge base updateable without redeployment
```

#### FR-CHAT-03: Service Integration
```
Integrated Services:
├── NER Service - Extract CV information on request
├── Skill Matching - Compare skills with JD
└── Career Recommendation - Generate career paths

Workflow:
1. User asks question
2. LLM determines intent
3. LLM calls appropriate service(s) via tools
4. LLM synthesizes response

Acceptance Criteria:
├── Correct service routing ≥ 85%
├── Graceful fallback when service unavailable
└── Clear explanation of actions taken
```

### 1.1 Data Processing Requirements

| ID | Requirement | Priority | Status |
|----|-------------|----------|--------|
| **FR-01** | Hệ thống phải trích xuất thông tin cá nhân từ CV (name, email, phone, address) | Critical | Planned |
| **FR-02** | Hệ thống phải trích xuất kinh nghiệm làm việc (company, title, duration, description) | Critical | Planned |
| **FR-03** | Hệ thống phải trích xuất học vấn (institution, degree, major, graduation year) | Critical | Planned |
| **FR-04** | Hệ thống phải trích xuất kỹ năng (technical skills, soft skills, languages) | Critical | Planned |

#### FR-01: Personal Information Extraction
```
Input:  Raw CV text
Output: Structured JSON
{
  "personal_info": {
    "name": "John Doe",
    "email": "john@example.com",
    "phone": "+84 123 456 789",
    "address": "Ho Chi Minh City, Vietnam"
  }
}

Acceptance Criteria:
├── Extract name with ≥ 80% accuracy
├── Extract email with ≥ 95% accuracy (regex + NER)
├── Extract phone with ≥ 90% accuracy
└── Extract address with ≥ 70% accuracy
```

#### FR-02: Work Experience Extraction
```
Input:  Raw CV text
Output: Structured JSON
{
  "work_experience": [
    {
      "company": "ABC Corp",
      "title": "Software Engineer",
      "start_date": "2020-01",
      "end_date": "2022-12",
      "description": "Developed web applications..."
    }
  ]
}

Acceptance Criteria:
├── Extract company names with ≥ 75% accuracy
├── Extract job titles with ≥ 75% accuracy
├── Extract dates with ≥ 80% accuracy
└── Handle multiple experiences
```

#### FR-03: Education Extraction
```
Input:  Raw CV text
Output: Structured JSON
{
  "education": [
    {
      "institution": "MIT",
      "degree": "Bachelor",
      "major": "Computer Science",
      "year": "2020"
    }
  ]
}

Acceptance Criteria:
├── Extract institution with ≥ 75% accuracy
├── Extract degree with ≥ 80% accuracy
├── Extract major with ≥ 70% accuracy
└── Handle multiple degrees
```

#### FR-04: Skills Extraction
```
Input:  Raw CV text
Output: Structured JSON
{
  "skills": {
    "technical": ["Python", "Java", "SQL"],
    "soft": ["Leadership", "Communication"],
    "languages": ["English", "Vietnamese"]
  }
}

Acceptance Criteria:
├── Extract technical skills with ≥ 70% recall
├── Categorize skills correctly
└── Handle skill variations (JS = JavaScript)
```

### 1.2 Skill Matching Requirements

| ID | Requirement | Priority | Status |
|----|-------------|----------|--------|
| **FR-05** | Hệ thống phải so khớp kỹ năng từ CV với yêu cầu từ JD | High | Planned |
| **FR-06** | Hệ thống phải tính điểm matching (0-100%) | High | Planned |
| **FR-07** | Skill taxonomy dựa trên O*NET Skills | High | Planned |

#### FR-05: Skill Matching
```
Input:
├── CV skills: ["Python", "Machine Learning", "SQL"]
└── JD requirements: ["Python", "Deep Learning", "Database"]

Output: Match results
{
  "matches": {
    "exact": ["Python"],
    "semantic": [
      {"cv_skill": "Machine Learning", "jd_skill": "Deep Learning", "similarity": 0.85},
      {"cv_skill": "SQL", "jd_skill": "Database", "similarity": 0.75}
    ],
    "missing": []
  }
}

Acceptance Criteria:
├── Exact match: 100% precision
├── Semantic match: ≥ 70% accuracy
└── Response time: < 1s
```

#### FR-06: Match Scoring
```
Scoring formula:
score = (exact_matches × 1.0 + semantic_matches × similarity) / total_required × 100

Example:
├── JD requires: 5 skills
├── Exact matches: 2 (score: 2.0)
├── Semantic matches: 2 (avg similarity 0.8, score: 1.6)
├── Missing: 1
└── Final score: (2.0 + 1.6) / 5 × 100 = 72%

Acceptance Criteria:
├── Score range: 0-100%
├── Calculation transparent
└── Breakdown provided
```

### 1.3 Career Path Recommendation Requirements

| ID | Requirement | Priority | Status |
|----|-------------|----------|--------|
| **FR-CAREER-01** | User có thể chọn target role để system tạo career path | High | Planned |
| **FR-CAREER-02** | System tạo 3 lộ trình: conservative, moderate, ambitious | High | Planned |
| **FR-CAREER-03** | Career data dựa trên O*NET Database | High | Planned |

#### FR-CAREER-01: Career Path Generation
```
Input: User chọn target role
Process: System tạo path từ current → target
Output: 3 lộ trình khác nhau với timeline và skills required

Roadmap Structure:
{
  "current_role": "Junior Developer",
  "target_role": "Tech Lead",
  "paths": [
    {
      "type": "conservative",
      "steps": [
        {
          "step": 1,
          "target_role": "Mid-level Developer",
          "timeframe": "2-3 years",
          "skills_to_learn": ["System Design", "CI/CD"],
          "certifications": ["AWS Solutions Architect"]
        }
      ]
    },
    {"type": "moderate", "steps": [...]},
    {"type": "ambitious", "steps": [...]}
  ]
}

Display: Text + Visual timeline

Acceptance Criteria:
├── Paths based on O*NET job relationships
├── Skills aligned with target roles
└── Realistic timeframes based on industry data
```

### 1.4 CV Score Requirements

| ID | Requirement | Priority | Status |
|----|-------------|----------|--------|
| **FR-SCORE-01** | System check CV completeness và quality | Medium | Planned |
| **FR-SCORE-02** | Output % score + checklist + suggestions | Medium | Planned |

### 1.5 Web Application Requirements

| ID | Requirement | Priority | Status |
|----|-------------|----------|--------|
| **FR-WEB-01** | Web UI ChatGPT-style với conversation-first design | High | Planned |
| **FR-WEB-02** | Upload CV và xem kết quả | Medium | Planned |
| **FR-WEB-03** | Export kết quả ra JSON/PDF | Medium | Planned |

#### FR-07: Web Interface
```
Features:
├── Upload CV (PDF)
├── View extracted information
├── Input JD for matching
├── View match score
└── Download results

Pages:
├── Home/Upload page
├── Results page
├── JD Input page
└── Match results page
```

#### FR-WEB-03: Export Functionality
```
Export formats:
├── JSON: Full structured data
└── PDF: Formatted report

JSON export example:
{
  "cv_id": "cv_001",
  "extracted_at": "2026-01-23T10:00:00Z",
  "personal_info": {...},
  "work_experience": [...],
  "education": [...],
  "skills": {...},
  "match_result": {...}
}
```

### 1.6 Authentication Requirements

| ID | Requirement | Priority | Status |
|----|-------------|----------|--------|
| **FR-AUTH-01** | Basic Authentication (Login/Register) | High | Planned |
| **FR-AUTH-02** | JWT token-based authentication | High | Planned |
| **FR-AUTH-03** | Save CV and chat history per user | High | Planned |

#### FR-AUTH-01: User Authentication
```
Features:
├── Registration (email, password)
├── Login with JWT tokens
├── Session management
└── Password reset (optional for v1)

Implementation:
├── API Gateway: Java Spring Boot + Spring Security
├── Token: JWT with 24h expiry
└── Storage: PostgreSQL users table

Acceptance Criteria:
├── Secure password hashing (bcrypt)
├── JWT validation on all protected routes
└── User data isolation
```

---

## 2. Non-Functional Requirements (NFR)

### 2.1 Performance Requirements

| ID | Requirement | Target | Priority |
|----|-------------|--------|----------|
| **NFR-01** | F1-Score của NER model | ≥ 75% | Critical |
| **NFR-02** | Processing time per CV | ≤ 5 seconds | High |
| **NFR-03** | API response time (non-chatbot) | ≤ 2 seconds | Medium |
| **NFR-04** | Concurrent users support | ≥ 5 users | Low |
| **NFR-05** | Chatbot response time | 5-15 seconds | High |
| **NFR-06** | RAG context retrieval | ≤ 2 seconds | Medium |

#### NFR-01: Model Accuracy
```
Metrics definition:
├── Precision = TP / (TP + FP)
├── Recall = TP / (TP + FN)
└── F1 = 2 × (Precision × Recall) / (Precision + Recall)

Target breakdown by entity (10 types):
├── PER (Person): F1 ≥ 80%
├── ORG (Organization): F1 ≥ 75%
├── DATE: F1 ≥ 80%
├── LOC (Location): F1 ≥ 70%
├── SKILL: F1 ≥ 70%
├── DEGREE: F1 ≥ 75%
├── MAJOR: F1 ≥ 70%
├── JOB_TITLE: F1 ≥ 75%
├── PROJECT: F1 ≥ 70%
├── CERT (Certification): F1 ≥ 75%
└── Overall: F1 ≥ 75%
```

#### NFR-05: Chatbot Response Time
```
Target: 5-15 seconds (CPU-only Llama 3.2 3B)

Time breakdown:
├── Intent detection: ≤ 1s
├── RAG retrieval: ≤ 2s
├── LLM inference: 5-10s
├── Tool calling (if needed): ≤ 2s
└── Response formatting: ≤ 0.5s

Measurement:
├── Tool: Python time module + logging
├── Sample: 100 random queries
└── Report: Avg, P50, P95, P99
```

#### NFR-02: Processing Time
```
Time breakdown (target):
├── PDF parsing: ≤ 1s
├── Text preprocessing: ≤ 0.5s
├── NER inference: ≤ 2s
├── Post-processing: ≤ 0.5s
└── Total: ≤ 4s (with 1s buffer → ≤ 5s)

Measurement:
├── Tool: Python time module
├── Sample: 50 random CVs
└── Report: Avg, P50, P95, P99
```

### 2.2 Quality Requirements

| ID | Requirement | Target | Priority |
|----|-------------|--------|----------|
| **NFR-05** | Code coverage | ≥ 60% | Medium |
| **NFR-06** | Documentation completeness | 100% | High |
| **NFR-07** | Inter-annotator agreement | ≥ 80% | High |

### 2.3 Usability Requirements

| ID | Requirement | Target | Priority |
|----|-------------|--------|----------|
| **NFR-08** | Web App responsive design | Mobile + Desktop | Medium |
| **NFR-09** | Upload file size limit | ≤ 10MB | Medium |
| **NFR-10** | Supported file formats | PDF only (v1) | Medium |

### 2.4 Compatibility Requirements

| ID | Requirement | Target | Priority |
|----|-------------|--------|----------|
| **NFR-11** | Browser support | Chrome, Firefox, Safari | Medium |
| **NFR-12** | Python version | 3.10+ | High |
| **NFR-13** | PyTorch version | 2.0+ | High |

---

## 3. Constraints

### 3.1 Project Constraints

| Constraint | Details | Impact |
|------------|---------|--------|
| **Budget** | $0 (Free tier only) | Must use free tools |
| **Timeline** | 12 weeks | Limited iterations |
| **Team** | 5 members (1 dev + 4 annotators) | Single technical POC |
| **Infrastructure** | Google Colab | Session limits |

### 3.2 Technical Constraints

```
GPU Constraints:
├── Provider: Google Colab Free
├── GPU: NVIDIA T4 (16GB VRAM)
├── Session limit: ~12 hours
├── Queue: May need to wait
└── Mitigation: Checkpoint frequently

Model Constraints:
├── Base model: bert-base-uncased (fixed)
├── Batch size: ≤ 16 (memory limit)
├── Max sequence length: 512 tokens
└── Mitigation: Truncate long CVs
```

### 3.3 Data Constraints

```
Privacy Constraints:
├── MUST anonymize all PII
├── MUST NOT publish raw CVs
├── MUST NOT share outside team
└── MUST document anonymization process

Format Constraints:
├── PDF only (no Word, no images)
├── Text-extractable (no scanned docs)
├── English language (v1)
└── Mitigation: Filter incompatible CVs
```

---

## 4. Assumptions

### 4.1 Data Assumptions

| ID | Assumption | Confidence | Validation |
|----|------------|------------|------------|
| **A-01** | CVs chủ yếu tiếng Anh | High | Sample 50 CVs |
| **A-02** | PDF có thể extract text | High | Test PyPDF2 |
| **A-03** | CV format reasonably structured | Medium | Visual review |
| **A-04** | 200 annotated CVs đủ cho fine-tuning | Medium | Literature review |

### 4.2 Technical Assumptions

| ID | Assumption | Confidence | Validation |
|----|------------|------------|------------|
| **A-05** | Google Colab always available | Medium | Monitor availability |
| **A-06** | BERT fine-tuning will converge | High | Early experiments |
| **A-07** | Sentence-BERT works for skill matching | High | Quick POC |
| **A-08** | FastAPI + React can be learned quickly | Medium | Simple demo first |

### 4.3 Resource Assumptions

| ID | Assumption | Confidence | Validation |
|----|------------|------------|------------|
| **A-09** | Annotators available 10-15 hrs/week | Medium | Weekly check-in |
| **A-10** | Leader can handle all technical tasks | Medium | Backup plan needed |
| **A-11** | No major scope changes | Low | Change control process |

---

## 5. Dependencies

### 5.1 External Dependencies

```
Library Dependencies:
├── transformers >= 4.30.0
│   └── Source: Hugging Face
├── torch >= 2.0.0
│   └── Source: PyTorch
├── sentence-transformers >= 2.2.0
│   └── Source: Hugging Face
├── fastapi >= 0.100.0
│   └── Source: PyPI
├── pdfplumber >= 0.9.0
│   └── Source: PyPI
└── react >= 18.0.0
    └── Source: npm

Service Dependencies:
├── Google Colab
│   └── Status: Free tier, reliable
├── Hugging Face Hub
│   └── Status: Free, reliable
├── Label Studio
│   └── Status: Self-hosted, reliable
└── GitHub
    └── Status: Free, reliable
```

### 5.2 Internal Dependencies

```
Module Dependencies:
┌───────────────┐
│  Annotation   │
└───────┬───────┘
        │
        ▼
┌───────────────┐
│   Training    │
└───────┬───────┘
        │
        ├───────────────┐
        ▼               ▼
┌───────────────┐ ┌───────────────┐
│  Evaluation   │ │   Web App     │
└───────┬───────┘ └───────┬───────┘
        │                 │
        └────────┬────────┘
                 ▼
        ┌───────────────┐
        │    Report     │
        └───────────────┘

Critical Path:
Annotation → Training → Evaluation → Report
```

### 5.3 Dependency Risk Matrix

| Dependency | Risk Level | Mitigation |
|------------|------------|------------|
| Google Colab | Medium | Kaggle backup |
| Hugging Face | Low | Local cache |
| PyPDF2 | Medium | pdfplumber fallback |
| Label Studio | Low | Export backups |

---

## 6. Requirements Traceability Matrix

| Req ID | Source | Priority | Module | Test Case |
|--------|--------|----------|--------|-----------|
| FR-01 | Problem Statement | Critical | NER | TC-01 |
| FR-02 | Problem Statement | Critical | NER | TC-02 |
| FR-03 | Problem Statement | Critical | NER | TC-03 |
| FR-04 | Problem Statement | Critical | NER | TC-04 |
| FR-05 | Problem Statement | High | Matching | TC-05 |
| FR-06 | Problem Statement | High | Matching | TC-06 |
| FR-07 | Stakeholder | Medium | Web App | TC-07 |
| FR-08 | Stakeholder | Medium | Web App | TC-08 |
| NFR-01 | KPI | Critical | NER | TC-09 |
| NFR-02 | KPI | High | System | TC-10 |

---

## 7. Requirements Change Control

### 7.1 Change Request Process

```
1. Submit change request (CR)
   └── Include: Reason, Impact, Priority

2. Impact analysis
   └── Assess: Timeline, Resources, Quality

3. Approval (by Leader + GVHD if major)
   └── Criteria: Scope, Feasibility

4. Implementation
   └── Update docs, code, tests

5. Verification
   └── Review changes
```

### 7.2 Change Categories

| Category | Approval | Example |
|----------|----------|---------|
| Minor | Leader | Fix typo in spec |
| Moderate | Leader + Team | Add new entity type |
| Major | Leader + GVHD | Change scope |

---

## 8. Appendix: Entity Type Definitions (10 Types)

### 8.1 BIO Tagging Schema

| # | Entity | B-tag | I-tag | Example |
|---|--------|-------|-------|---------|
| 1 | Person | B-PER | I-PER | `[John]B-PER [Doe]I-PER` |
| 2 | Organization | B-ORG | I-ORG | `[Google]B-ORG [Inc]I-ORG` |
| 3 | Date | B-DATE | I-DATE | `[January]B-DATE [2020]I-DATE` |
| 4 | Location | B-LOC | I-LOC | `[Ho Chi Minh]B-LOC [City]I-LOC` |
| 5 | Skill | B-SKILL | I-SKILL | `[Machine]B-SKILL [Learning]I-SKILL` |
| 6 | Degree | B-DEGREE | I-DEGREE | `[Bachelor]B-DEGREE [of Science]I-DEGREE` |
| 7 | Major | B-MAJOR | I-MAJOR | `[Computer]B-MAJOR [Science]I-MAJOR` |
| 8 | Job Title | B-JOB_TITLE | I-JOB_TITLE | `[Software]B-JOB_TITLE [Engineer]I-JOB_TITLE` |
| 9 | Project | B-PROJECT | I-PROJECT | `[E-commerce]B-PROJECT [Platform]I-PROJECT` |
| 10 | Certification | B-CERT | I-CERT | `[AWS]B-CERT [Solutions Architect]I-CERT` |

### 8.2 Entity Examples by Section

```
Personal Information:
├── "John Smith" → PER
├── "john@email.com" → (regex, not NER)
├── "+84 123 456 789" → (regex, not NER)
└── "Ho Chi Minh City, Vietnam" → LOC

Work Experience:
├── "Google" → ORG
├── "Software Engineer" → JOB_TITLE
├── "2020 - 2022" → DATE
└── "Python, Java" → SKILL

Education:
├── "MIT" → ORG
├── "Bachelor of Science" → DEGREE
├── "Computer Science" → MAJOR
└── "2016 - 2020" → DATE

Skills:
├── "Python" → SKILL
├── "Machine Learning" → SKILL
├── "Leadership" → SKILL
└── "English" → SKILL (language)

Projects:
├── "E-commerce Platform" → PROJECT
├── "Mobile Banking App" → PROJECT
└── "AI Chatbot System" → PROJECT

Certifications:
├── "AWS Solutions Architect" → CERT
├── "Google Cloud Professional" → CERT
├── "PMP" → CERT
└── "CCNA" → CERT
```

---

*Document created as part of CV-NER Research Project documentation.*
