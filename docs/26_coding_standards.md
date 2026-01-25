# 26. Coding Standards & Best Practices

> **Document Version**: 2.0
> **Last Updated**: 2026-01-25
> **Status**: Approved
> **Product Name**: CV Assistant
> **Related Documents**: [09_system_architecture.md](./09_system_architecture.md), [11_adr_decisions.md](./11_adr_decisions.md)

---

## 1. Tổng Quan

### 1.1 Mục Tiêu

Tài liệu này định nghĩa **coding standards bắt buộc** cho toàn bộ dự án CV Assistant. Mọi thành viên **PHẢI** tuân thủ để đảm bảo:

| Mục tiêu | Mô tả |
|----------|-------|
| **Maintainability** | Code dễ đọc, dễ hiểu, dễ sửa sau 6 tháng |
| **Reusability** | Tái sử dụng code giữa các services |
| **Testability** | Dễ viết unit test, dễ mock dependencies |
| **Consistency** | Code trong toàn bộ project có style thống nhất |
| **Quality** | Giảm bugs, giảm technical debt |

### 1.2 Nguyên Tắc Cốt Lõi

```
╔══════════════════════════════════════════════════════════════════╗
║                    5 NGUYÊN TẮC BẮT BUỘC                         ║
╠══════════════════════════════════════════════════════════════════╣
║ 1. DRY - Don't Repeat Yourself                                   ║
║    → Không duplicate code, extract thành function/component      ║
║                                                                   ║
║ 2. KISS - Keep It Simple, Stupid                                 ║
║    → Code đơn giản, không over-engineering                       ║
║                                                                   ║
║ 3. Single Responsibility                                         ║
║    → Mỗi function/class chỉ làm MỘT việc                         ║
║                                                                   ║
║ 4. Explicit over Implicit                                        ║
║    → Code rõ ràng, không dựa vào side effects                    ║
║                                                                   ║
║ 5. Fail Fast                                                     ║
║    → Validate input sớm, throw error ngay khi phát hiện issue    ║
╚══════════════════════════════════════════════════════════════════╝
```

---

## 2. Kiến Trúc & Project Structure

### 2.1 Microservices Structure (Theo ADR-003, ADR-011)

Mỗi service **PHẢI** tuân theo cấu trúc sau:

```
services/<service-name>/
├── main.py                 # FastAPI entrypoint (chỉ routing, không logic)
├── requirements.txt        # Dependencies
├── Dockerfile              # Docker build
├── README.md               # Service documentation (BẮT BUỘC)
├── config.py               # Configuration management
├── models/                 # Pydantic models
│   ├── __init__.py
│   └── schemas.py
├── services/               # Business logic (core)
│   ├── __init__.py
│   └── <domain>_service.py
├── repositories/           # Data access layer
│   ├── __init__.py
│   └── <entity>_repository.py
├── utils/                  # Helper functions
│   ├── __init__.py
│   └── helpers.py
└── tests/                  # Unit tests
    ├── __init__.py
    └── test_<module>.py
```

### 2.2 Shared Code (Tái Sử Dụng)

Code dùng chung giữa services **PHẢI** đặt trong `shared/`:

```
shared/
├── __init__.py
├── db/
│   ├── __init__.py
│   ├── chroma_client.py    # ChromaDB connection (Singleton)
│   └── postgres_client.py  # PostgreSQL connection
├── models/
│   ├── __init__.py
│   └── base_models.py      # Common Pydantic models
├── utils/
│   ├── __init__.py
│   ├── text_utils.py       # Text processing
│   ├── logging_config.py   # Centralized logging
│   └── validators.py       # Common validators
└── constants.py            # Shared constants
```

### 2.3 Frontend Structure (Theo ADR-004)

```
frontend/src/
├── components/             # Reusable UI components
│   ├── common/             # Button, Input, Card, Modal
│   ├── chat/               # ChatMessage, ChatInput
│   └── layout/             # Header, Sidebar, Footer
├── pages/                  # Route-level components
├── hooks/                  # Custom React hooks
├── services/               # API calls
│   └── api.js              # Axios instance + endpoints
├── utils/                  # Helper functions
├── styles/                 # CSS/Tailwind
└── App.jsx
```

---

## 3. Python Coding Standards

### 3.1 Style Guide (PEP 8 + Additions)

| Rule | Mô tả | Ví dụ |
|------|-------|-------|
| **Line length** | Max 100 characters | - |
| **Imports** | Group: stdlib → 3rd party → local | ✅ |
| **Blank lines** | 2 giữa top-level, 1 trong class | ✅ |
| **Quotes** | Double quotes `"string"` | ✅ |
| **Trailing comma** | Trong multiline lists | `[a, b,]` |

### 3.2 Naming Conventions (BẮT BUỘC)

```python
# ✅ ĐÚNG
class SkillMatcherService:         # PascalCase cho class
    MAX_RESULTS = 10               # UPPER_SNAKE cho constants
    
    def calculate_score(self, cv_skills: List[str]) -> float:  # snake_case
        user_name = "John"         # snake_case cho variables
        _internal_cache = {}       # _ prefix cho private
        
# ❌ SAI
class skillMatcher:                # Phải PascalCase
    def CalculateScore(self):      # Phải snake_case
        UserName = "John"          # Phải lowercase
```

### 3.3 Type Hints (BẮT BUỘC 100%)

**Tất cả functions PHẢI có type hints cho parameters và return type.**

```python
from typing import List, Dict, Optional, Union, Tuple
from pydantic import BaseModel

# ✅ ĐÚNG: Có type hints
def extract_skills(text: str, min_confidence: float = 0.5) -> List[Dict[str, str]]:
    """Extract skills from text."""
    pass

def process_cv(file: UploadFile) -> Tuple[str, List[Entity]]:
    pass

# ❌ SAI: Thiếu type hints
def extract_skills(text, min_confidence=0.5):  # ← KHÔNG CHẤP NHẬN
    pass
```

### 3.4 Docstrings (Google Style - BẮT BUỘC)

**Mọi public function/class PHẢI có docstring.**

```python
def match_skills(cv_skills: List[str], jd_text: str) -> MatchResult:
    """
    Match CV skills against job description requirements.
    
    Sử dụng semantic search với Sentence-BERT để so khớp skills.
    
    Args:
        cv_skills: List of skills from candidate's CV.
        jd_text: Raw text from job description.
    
    Returns:
        MatchResult containing exact_matches, semantic_matches, and score.
    
    Raises:
        ValueError: If cv_skills is empty.
        ConnectionError: If ChromaDB is unavailable.
    
    Example:
        >>> result = match_skills(["Python", "SQL"], "Looking for Python dev")
        >>> print(result.score)
        85.5
    """
```

### 3.5 Error Handling

```python
import logging
from fastapi import HTTPException

logger = logging.getLogger(__name__)

# ✅ ĐÚNG: Specific exceptions, logging, proper HTTP status
def load_model(path: str):
    if not Path(path).exists():
        logger.error(f"Model path does not exist: {path}")
        raise FileNotFoundError(f"Model not found: {path}")
    
    try:
        model = SentenceTransformer(path)
        logger.info(f"Model loaded successfully from {path}")
        return model
    except Exception as e:
        logger.exception("Failed to load model")
        raise HTTPException(status_code=500, detail="Model loading failed")

# ❌ SAI: Bare except, silent failure
def load_model(path):
    try:
        return SentenceTransformer(path)
    except:            # ← KHÔNG BAO GIỜ dùng bare except
        pass           # ← KHÔNG BAO GIỜ silent failure
        return None    # ← Trả về None là bad practice
```

### 3.6 Configuration Management

**KHÔNG hardcode values. Dùng environment variables.**

```python
# config.py
import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """Service configuration from environment."""
    
    # Database
    chroma_path: str = "./knowledge_base/chroma_db"
    postgres_url: str = "postgresql://user:pass@localhost:5432/db"
    
    # Service
    service_port: int = 5002
    log_level: str = "INFO"
    
    # ML
    embedding_model: str = "all-MiniLM-L6-v2"
    similarity_threshold: float = 0.5
    
    class Config:
        env_file = ".env"

settings = Settings()

# Usage
from config import settings
client = chromadb.PersistentClient(path=settings.chroma_path)
```

---

## 4. Dependency Injection & Testability

### 4.1 Dependency Injection Pattern

**KHÔNG hardcode dependencies trong class. Inject từ bên ngoài.**

```python
# ✅ ĐÚNG: Dependency Injection
class SkillMatcherService:
    def __init__(
        self, 
        embedding_model: SentenceTransformer,
        collection: chromadb.Collection
    ):
        self.model = embedding_model
        self.collection = collection
    
    def match(self, cv_skills: List[str], jd_text: str) -> MatchResult:
        # Use injected dependencies
        embeddings = self.model.encode(cv_skills)
        results = self.collection.query(query_texts=[jd_text])
        return self._process_results(results)

# main.py - Wire dependencies
embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
collection = get_chroma_collection("onet_jobs")
skill_service = SkillMatcherService(embedding_model, collection)

# ❌ SAI: Hardcoded dependencies (KHÔNG THỂ TEST)
class SkillMatcherService:
    def __init__(self):
        self.model = SentenceTransformer("all-MiniLM-L6-v2")  # ← Hardcoded!
        self.collection = chromadb.get_collection("onet_jobs")  # ← Hardcoded!
```

### 4.2 FastAPI Dependency Injection

```python
from fastapi import Depends

# dependencies.py
def get_skill_service() -> SkillMatcherService:
    return SkillMatcherService(
        embedding_model=get_embedding_model(),
        collection=get_chroma_collection()
    )

# main.py
@app.post("/match")
def match_skills(
    request: SkillMatchRequest,
    service: SkillMatcherService = Depends(get_skill_service)
) -> MatchResult:
    return service.match(request.cv_skills, request.jd_text)
```

---

## 5. API Design Standards

### 5.1 RESTful Conventions

| Method | Path | Mô tả |
|--------|------|-------|
| `GET` | `/api/resources` | List resources |
| `GET` | `/api/resources/{id}` | Get single resource |
| `POST` | `/api/resources` | Create resource |
| `PUT` | `/api/resources/{id}` | Replace resource |
| `PATCH` | `/api/resources/{id}` | Update resource |
| `DELETE` | `/api/resources/{id}` | Delete resource |

### 5.2 Response Format

```python
# ✅ Consistent response structure
class SuccessResponse(BaseModel):
    success: bool = True
    data: Any
    message: Optional[str] = None

class ErrorResponse(BaseModel):
    success: bool = False
    error: Dict[str, Any]
    request_id: str

# Example
{
    "success": true,
    "data": {
        "score": 85.5,
        "matches": ["Python", "SQL"]
    },
    "message": "Matching completed"
}
```

### 5.3 Error Codes

```python
# Use standard HTTP status codes
class AppException(HTTPException):
    pass

class NotFoundError(AppException):
    def __init__(self, resource: str):
        super().__init__(status_code=404, detail=f"{resource} not found")

class ValidationError(AppException):
    def __init__(self, message: str):
        super().__init__(status_code=400, detail=message)

class ServiceUnavailableError(AppException):
    def __init__(self, service: str):
        super().__init__(status_code=503, detail=f"{service} unavailable")
```

---

## 6. React/Frontend Standards

### 6.1 Component Guidelines

```jsx
// ✅ ĐÚNG: Small, focused, props-based
function ChatMessage({ content, role, timestamp }) {
    const isUser = role === "user";
    
    return (
        <div className={`message ${isUser ? "user" : "assistant"}`}>
            <p>{content}</p>
            <span className="timestamp">{timestamp}</span>
        </div>
    );
}

// ✅ Extract logic into custom hooks
function useChat() {
    const [messages, setMessages] = useState([]);
    const [isLoading, setIsLoading] = useState(false);
    
    const sendMessage = async (text) => {
        setIsLoading(true);
        try {
            const response = await api.chat(text);
            setMessages(prev => [...prev, response]);
        } finally {
            setIsLoading(false);
        }
    };
    
    return { messages, isLoading, sendMessage };
}
```

### 6.2 State Management

```jsx
// ✅ Use React Context for global state
const ChatContext = createContext();

function ChatProvider({ children }) {
    const [threads, setThreads] = useState([]);
    const [activeThread, setActiveThread] = useState(null);
    
    return (
        <ChatContext.Provider value={{ threads, activeThread, setActiveThread }}>
            {children}
        </ChatContext.Provider>
    );
}

// ❌ KHÔNG prop drilling qua nhiều levels
<App>
    <Sidebar threads={threads}>
        <ThreadList threads={threads} onSelect={...}>
            <ThreadItem thread={thread} .../>  ← Too deep!
```

### 6.3 API Calls

```javascript
// services/api.js
import axios from "axios";

const api = axios.create({
    baseURL: import.meta.env.VITE_API_URL || "http://localhost:8080",
    timeout: 30000,
});

// Interceptors for auth
api.interceptors.request.use((config) => {
    const token = localStorage.getItem("accessToken");
    if (token) {
        config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
});

export const chatApi = {
    send: (message, threadId) => 
        api.post("/api/chat", { message, thread_id: threadId }),
    getThreads: () => 
        api.get("/api/threads"),
};
```

---

## 7. Testing Standards

### 7.1 Coverage Requirements

| Component | Minimum | Target |
|-----------|---------|--------|
| Business Logic | 80% | 90% |
| API Endpoints | 70% | 80% |
| Utilities | 90% | 95% |
| UI Components | 60% | 70% |

### 7.2 Test Structure

```python
# tests/test_skill_matcher.py
import pytest
from unittest.mock import Mock, patch

class TestSkillMatcher:
    
    @pytest.fixture
    def matcher(self):
        """Create matcher with mocked dependencies."""
        mock_model = Mock()
        mock_model.encode.return_value = [[0.1, 0.2, 0.3]]
        mock_collection = Mock()
        return SkillMatcherService(mock_model, mock_collection)
    
    def test_exact_match_found(self, matcher):
        """Test that exact matches are identified."""
        result = matcher.match(
            cv_skills=["Python", "SQL"],
            jd_text="Looking for Python developer"
        )
        assert "python" in result.exact_matches
    
    def test_empty_skills_returns_zero_score(self, matcher):
        """Test edge case with empty input."""
        result = matcher.match(cv_skills=[], jd_text="Any job")
        assert result.score == 0.0
    
    def test_chromadb_unavailable_raises_error(self, matcher):
        """Test graceful handling of DB failure."""
        matcher.collection.query.side_effect = ConnectionError()
        with pytest.raises(ServiceUnavailableError):
            matcher.match(["Python"], "Developer")
```

---

## 8. Git & Version Control

### 8.1 Commit Message Format

```
<type>(<scope>): <short description>

[optional body]

[optional footer]

Types:
├── feat      → New feature
├── fix       → Bug fix
├── docs      → Documentation
├── refactor  → Code refactoring (no new feature, no bug fix)
├── test      → Adding tests
├── chore     → Build, config, dependencies
└── style     → Formatting (no logic change)

Examples:
├── feat(skill-service): implement semantic search with SBERT
├── fix(chatbot): handle empty response from Ollama
├── refactor(shared): extract ChromaDB client to singleton
└── docs: add comprehensive coding standards
```

### 8.2 Branch Strategy

```
main                   ← Production-ready
├── develop            ← Integration branch
├── feature/*          ← New features
│   ├── feature/skill-matching
│   └── feature/chat-history
├── fix/*              ← Bug fixes
│   └── fix/chroma-connection
└── release/*          ← Release preparation
```

---

## 9. Code Review Checklist

Trước khi merge, reviewer **PHẢI** kiểm tra:

### 9.1 Code Quality

- [ ] Tuân thủ naming conventions
- [ ] Có type hints cho tất cả functions
- [ ] Có docstrings cho public functions
- [ ] Không có hardcoded values (dùng config)
- [ ] Error handling đầy đủ (không bare except)
- [ ] Không duplicate code (DRY)
- [ ] Logic đơn giản, dễ hiểu (KISS)

### 9.2 Architecture

- [ ] Đúng layer (service logic trong services/, không trong main.py)
- [ ] Dependency injection (không hardcode dependencies)
- [ ] Shared code trong shared/ nếu dùng chung

### 9.3 Testing & Docs

- [ ] Có unit tests cho business logic
- [ ] Tests pass (CI green)
- [ ] README updated nếu thay đổi API

### 9.4 Security

- [ ] Không sensitive data trong code (passwords, keys)
- [ ] Input validation đầy đủ
- [ ] Proper authentication checks

---

## 10. Linting & Formatting Tools

### 10.1 Python

```bash
# Install tools
pip install ruff black mypy

# ruff - Fast linter
ruff check .

# black - Formatter
black .

# mypy - Type checker
mypy --strict .
```

### 10.2 JavaScript/React

```bash
# ESLint + Prettier
npm install eslint prettier --save-dev

# Run
npx eslint src/
npx prettier --write src/
```

### 10.3 Pre-commit Hooks

```yaml
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: ruff
        name: ruff
        entry: ruff check --fix
        language: python
        types: [python]
      - id: black
        name: black
        entry: black
        language: python
        types: [python]
      - id: mypy
        name: mypy
        entry: mypy --strict
        language: python
        types: [python]
```

---

## 11. Documentation Requirements

### 11.1 README per Service

**Mỗi service PHẢI có README.md với format sau:**

```markdown
# <Service Name>

## Overview
Brief description of what this service does.

## Quick Start
1. Install: `pip install -r requirements.txt`
2. Run: `python main.py`
3. Docs: http://localhost:<port>/docs

## API Endpoints
| Method | Path | Description |
|--------|------|-------------|
| POST | /match | Match CV skills with JD |

## Environment Variables
| Variable | Default | Description |
|----------|---------|-------------|
| CHROMA_PATH | ./kb | ChromaDB path |

## Architecture
Brief description of internal structure.

## Testing
`pytest tests/`
```

---

## 12. Summary

```
╔══════════════════════════════════════════════════════════════════╗
║                    RULES TO REMEMBER                             ║
╠══════════════════════════════════════════════════════════════════╣
║ ✓ Type hints: 100% coverage                                      ║
║ ✓ Docstrings: All public functions                               ║
║ ✓ No hardcoded values: Use config                                ║
║ ✓ Dependency Injection: For testability                          ║
║ ✓ Single Responsibility: One function = one job                  ║
║ ✓ DRY: Extract to shared/ if used by 2+ services                 ║
║ ✓ Tests: 80%+ coverage for business logic                        ║
║ ✓ README: Every service must have one                            ║
╚══════════════════════════════════════════════════════════════════╝
```

---

*Document created as part of CV Assistant Research Project documentation.*
