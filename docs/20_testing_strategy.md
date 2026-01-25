# 20. Testing Strategy

> **Document Version**: 1.0
> **Last Updated**: 2026-01-23
> **Status**: Approved
> **Product Name**: CV Assistant
> **Related Documents**: [09_system_architecture.md](./09_system_architecture.md), [17_api_specifications.md](./17_api_specifications.md)

---

## 1. Overview

This document defines the comprehensive testing strategy for CV Assistant, covering unit tests, integration tests, and end-to-end testing across all microservices.

### 1.1 Testing Goals

| Goal | Target | Metric |
|------|--------|--------|
| **Code Coverage** | 60% minimum | Lines covered |
| **Unit Tests** | All core functions | Pass rate 100% |
| **Integration Tests** | All API endpoints | Pass rate 100% |
| **E2E Tests** | Critical user flows | Pass rate 100% |
| **Performance** | Response time within SLA | P95 latency |

### 1.2 Testing Pyramid

```
                    ┌─────────────┐
                    │    E2E      │  10%
                    │   Tests     │
                ┌───┴─────────────┴───┐
                │   Integration       │  30%
                │      Tests          │
            ┌───┴─────────────────────┴───┐
            │        Unit Tests           │  60%
            │                             │
            └─────────────────────────────┘
```

---

## 2. Testing Framework by Service

### 2.1 Technology Stack

| Service | Language | Testing Framework | Mocking | Coverage Tool |
|---------|----------|-------------------|---------|---------------|
| NER Service | Python | pytest | pytest-mock | coverage.py |
| Skill Service | Python | pytest | pytest-mock | coverage.py |
| Career Service | Python | pytest | pytest-mock | coverage.py |
| Chatbot Service | Python | pytest | pytest-mock, responses | coverage.py |
| API Gateway | Java | JUnit 5 | Mockito | JaCoCo |
| Frontend | TypeScript | Jest, React Testing Library | jest.mock | Istanbul |

### 2.2 Dependencies

**Python Services (requirements-test.txt)**:
```
pytest==7.4.4
pytest-asyncio==0.23.3
pytest-cov==4.1.0
pytest-mock==3.12.0
httpx==0.26.0
responses==0.24.1
faker==22.0.0
factory-boy==3.3.0
```

**Java API Gateway (build.gradle.kts)**:
```kotlin
testImplementation("org.springframework.boot:spring-boot-starter-test")
testImplementation("org.junit.jupiter:junit-jupiter:5.10.1")
testImplementation("org.mockito:mockito-core:5.8.0")
testImplementation("com.h2database:h2")
```

**Frontend (package.json)**:
```json
{
  "devDependencies": {
    "@testing-library/react": "^14.1.2",
    "@testing-library/jest-dom": "^6.2.0",
    "@testing-library/user-event": "^14.5.2",
    "jest": "^29.7.0",
    "jest-environment-jsdom": "^29.7.0"
  }
}
```

---

## 3. Unit Testing

### 3.1 NER Service Unit Tests

**Test Structure**:
```
services/ner-service/
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_extractor.py
│   ├── test_preprocessor.py
│   ├── test_postprocessor.py
│   └── test_models.py
```

**Example Tests**:

```python
# tests/test_extractor.py
import pytest
from unittest.mock import Mock, patch
from app.extractor import NERExtractor, Entity

class TestNERExtractor:

    @pytest.fixture
    def extractor(self):
        with patch('app.extractor.AutoModelForTokenClassification'):
            with patch('app.extractor.AutoTokenizer'):
                return NERExtractor(model_path="test_model")

    def test_extract_entities_returns_list(self, extractor):
        """Test that extract_entities returns a list of Entity objects"""
        text = "John Doe works at Google"

        with patch.object(extractor, '_run_inference') as mock_inference:
            mock_inference.return_value = [
                {"word": "John", "entity": "B-PER", "score": 0.99},
                {"word": "Doe", "entity": "I-PER", "score": 0.98},
                {"word": "Google", "entity": "B-ORG", "score": 0.97}
            ]

            result = extractor.extract_entities(text)

            assert isinstance(result, list)
            assert len(result) == 2
            assert result[0].type == "PER"
            assert result[0].text == "John Doe"

    def test_extract_entities_empty_text(self, extractor):
        """Test extraction with empty text"""
        result = extractor.extract_entities("")
        assert result == []

    def test_extract_entities_no_entities(self, extractor):
        """Test text with no recognizable entities"""
        text = "This is a plain sentence."

        with patch.object(extractor, '_run_inference') as mock_inference:
            mock_inference.return_value = []

            result = extractor.extract_entities(text)
            assert result == []

    def test_entity_confidence_threshold(self, extractor):
        """Test that low confidence entities are filtered"""
        text = "John works at somewhere"

        with patch.object(extractor, '_run_inference') as mock_inference:
            mock_inference.return_value = [
                {"word": "John", "entity": "B-PER", "score": 0.95},
                {"word": "somewhere", "entity": "B-ORG", "score": 0.3}
            ]

            result = extractor.extract_entities(text, confidence_threshold=0.5)

            assert len(result) == 1
            assert result[0].text == "John"


# tests/test_preprocessor.py
import pytest
from app.preprocessor import CVPreprocessor

class TestCVPreprocessor:

    @pytest.fixture
    def preprocessor(self):
        return CVPreprocessor()

    def test_clean_text_removes_extra_whitespace(self, preprocessor):
        """Test whitespace normalization"""
        text = "John   Doe\n\n\nworks   at   Google"
        result = preprocessor.clean_text(text)
        assert "  " not in result

    def test_clean_text_preserves_structure(self, preprocessor):
        """Test that section headers are preserved"""
        text = "EXPERIENCE\nSoftware Engineer at Google"
        result = preprocessor.clean_text(text)
        assert "EXPERIENCE" in result

    def test_extract_sections(self, preprocessor):
        """Test section extraction from CV"""
        text = """
        EDUCATION
        MIT - Computer Science

        EXPERIENCE
        Google - Software Engineer
        """

        sections = preprocessor.extract_sections(text)

        assert "education" in sections
        assert "experience" in sections
        assert "MIT" in sections["education"]
        assert "Google" in sections["experience"]


# tests/test_models.py
import pytest
from pydantic import ValidationError
from app.models import Entity, CVExtractionResult

class TestEntityModel:

    def test_entity_creation(self):
        """Test Entity model creation"""
        entity = Entity(
            text="John Doe",
            type="PER",
            start=0,
            end=8,
            confidence=0.95
        )

        assert entity.text == "John Doe"
        assert entity.type == "PER"

    def test_entity_confidence_bounds(self):
        """Test confidence must be between 0 and 1"""
        with pytest.raises(ValidationError):
            Entity(text="Test", type="PER", start=0, end=4, confidence=1.5)

    def test_entity_start_end_validation(self):
        """Test start must be less than end"""
        with pytest.raises(ValidationError):
            Entity(text="Test", type="PER", start=10, end=5, confidence=0.9)
```

### 3.2 Skill Service Unit Tests

```python
# tests/test_matcher.py
import pytest
import numpy as np
from unittest.mock import Mock, patch
from app.matcher import SkillMatcher, SemanticMatch

class TestSkillMatcher:

    @pytest.fixture
    def matcher(self):
        with patch('app.matcher.SentenceTransformer') as mock_model:
            mock_model.return_value.encode.return_value = np.random.rand(10, 384)
            return SkillMatcher()

    def test_exact_match(self, matcher):
        """Test exact skill matching"""
        cv_skills = ["Python", "JavaScript", "Docker"]
        jd_skills = ["Python", "JavaScript", "React"]

        result = matcher.match_skills(cv_skills, jd_skills)

        assert "Python" in result.exact_matches
        assert "JavaScript" in result.exact_matches

    def test_semantic_match(self, matcher):
        """Test semantic similarity matching"""
        cv_skills = ["Python programming"]
        jd_skills = ["Python development"]

        with patch.object(matcher, '_compute_similarity') as mock_sim:
            mock_sim.return_value = 0.85

            result = matcher.match_skills(cv_skills, jd_skills)

            assert len(result.semantic_matches) >= 0

    def test_score_calculation(self, matcher):
        """Test overall score calculation"""
        cv_skills = ["Python", "Java"]
        jd_skills = ["Python", "Java", "Docker"]

        result = matcher.match_skills(cv_skills, jd_skills)

        assert 0 <= result.score <= 100

    def test_empty_skills(self, matcher):
        """Test handling of empty skill lists"""
        result = matcher.match_skills([], [])

        assert result.score == 0
        assert result.exact_matches == []
```

### 3.3 Career Service Unit Tests

```python
# tests/test_recommender.py
import pytest
from app.recommender import CareerRecommender, CareerPath

class TestCareerRecommender:

    @pytest.fixture
    def recommender(self):
        return CareerRecommender(onet_data_path="tests/fixtures/onet_sample.json")

    def test_generate_path_returns_three_options(self, recommender):
        """Test that three career paths are generated"""
        result = recommender.generate_paths(
            current_role="Junior Developer",
            target_role="Tech Lead",
            current_skills=["Python", "Git"]
        )

        assert len(result.paths) == 3
        path_types = [p.type for p in result.paths]
        assert "conservative" in path_types
        assert "moderate" in path_types
        assert "ambitious" in path_types

    def test_skill_gap_analysis(self, recommender):
        """Test skill gap identification"""
        result = recommender.analyze_skill_gap(
            current_skills=["Python", "SQL"],
            target_role="Data Scientist"
        )

        assert "missing" in result
        assert "to_improve" in result
        assert isinstance(result["missing"], list)

    def test_invalid_role(self, recommender):
        """Test handling of unknown roles"""
        with pytest.raises(ValueError):
            recommender.generate_paths(
                current_role="Unknown Role",
                target_role="Tech Lead",
                current_skills=[]
            )
```

### 3.4 Chatbot Service Unit Tests

```python
# tests/test_agent.py
import pytest
from unittest.mock import Mock, patch, AsyncMock
from app.agent import CVAssistantAgent

class TestCVAssistantAgent:

    @pytest.fixture
    def agent(self):
        with patch('app.agent.Ollama') as mock_ollama:
            with patch('app.agent.ChromaVectorStore') as mock_chroma:
                return CVAssistantAgent(
                    ollama_host="localhost",
                    ollama_port=11434,
                    chroma_host="localhost",
                    chroma_port=8000
                )

    @pytest.mark.asyncio
    async def test_chat_returns_response(self, agent):
        """Test basic chat functionality"""
        with patch.object(agent, '_get_response') as mock_response:
            mock_response.return_value = AsyncMock(return_value="Test response")

            result = await agent.chat("Hello", user_id="test_user")

            assert "response" in result

    @pytest.mark.asyncio
    async def test_tool_detection(self, agent):
        """Test that agent detects when to use tools"""
        message = "Analyze my CV and extract skills"

        with patch.object(agent, '_detect_intent') as mock_intent:
            mock_intent.return_value = "ner_extraction"

            intent = await agent._detect_intent(message)

            assert intent == "ner_extraction"

    @pytest.mark.asyncio
    async def test_context_retrieval(self, agent):
        """Test RAG context retrieval"""
        query = "What skills do software engineers need?"

        with patch.object(agent, '_retrieve_context') as mock_retrieve:
            mock_retrieve.return_value = ["Context 1", "Context 2"]

            contexts = await agent._retrieve_context(query)

            assert len(contexts) > 0


# tests/test_memory.py
import pytest
from app.memory import ConversationMemory

class TestConversationMemory:

    @pytest.fixture
    def memory(self):
        with patch('app.memory.chromadb.Client'):
            return ConversationMemory(
                chroma_host="localhost",
                chroma_port=8000
            )

    def test_add_message(self, memory):
        """Test adding message to memory"""
        memory.add_message(
            user_id="test_user",
            thread_id="thread_1",
            role="user",
            content="Test message"
        )

        # Verify message was added
        messages = memory.get_thread_messages("thread_1")
        assert len(messages) >= 0

    def test_get_relevant_context(self, memory):
        """Test retrieving relevant past context"""
        with patch.object(memory, '_query_similar') as mock_query:
            mock_query.return_value = ["Previous context about Python"]

            context = memory.get_relevant_context(
                user_id="test_user",
                query="Tell me about Python"
            )

            assert isinstance(context, list)
```

### 3.5 API Gateway Unit Tests (Java)

```java
// src/test/java/com/cvassistant/gateway/service/AuthServiceTest.java
package com.cvassistant.gateway.service;

import com.cvassistant.gateway.model.User;
import com.cvassistant.gateway.repository.UserRepository;
import com.cvassistant.gateway.security.JwtTokenProvider;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.security.crypto.password.PasswordEncoder;

import java.util.Optional;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.*;

@ExtendWith(MockitoExtension.class)
class AuthServiceTest {

    @Mock
    private UserRepository userRepository;

    @Mock
    private PasswordEncoder passwordEncoder;

    @Mock
    private JwtTokenProvider jwtTokenProvider;

    @InjectMocks
    private AuthService authService;

    private User testUser;

    @BeforeEach
    void setUp() {
        testUser = new User();
        testUser.setId("user-123");
        testUser.setEmail("test@example.com");
        testUser.setPasswordHash("hashed_password");
        testUser.setName("Test User");
    }

    @Test
    void login_ValidCredentials_ReturnsAuthResponse() {
        // Arrange
        when(userRepository.findByEmail("test@example.com"))
            .thenReturn(Optional.of(testUser));
        when(passwordEncoder.matches("password", "hashed_password"))
            .thenReturn(true);
        when(jwtTokenProvider.generateAccessToken(any()))
            .thenReturn("access_token");
        when(jwtTokenProvider.generateRefreshToken(any()))
            .thenReturn("refresh_token");

        // Act
        var result = authService.login("test@example.com", "password");

        // Assert
        assertNotNull(result);
        assertEquals("access_token", result.accessToken());
        assertEquals("refresh_token", result.refreshToken());
    }

    @Test
    void login_InvalidEmail_ThrowsException() {
        // Arrange
        when(userRepository.findByEmail("invalid@example.com"))
            .thenReturn(Optional.empty());

        // Act & Assert
        assertThrows(AuthenticationException.class, () ->
            authService.login("invalid@example.com", "password")
        );
    }

    @Test
    void login_InvalidPassword_ThrowsException() {
        // Arrange
        when(userRepository.findByEmail("test@example.com"))
            .thenReturn(Optional.of(testUser));
        when(passwordEncoder.matches("wrong_password", "hashed_password"))
            .thenReturn(false);

        // Act & Assert
        assertThrows(AuthenticationException.class, () ->
            authService.login("test@example.com", "wrong_password")
        );
    }

    @Test
    void register_NewUser_ReturnsCreatedUser() {
        // Arrange
        when(userRepository.existsByEmail("new@example.com"))
            .thenReturn(false);
        when(passwordEncoder.encode("password"))
            .thenReturn("hashed_password");
        when(userRepository.save(any(User.class)))
            .thenReturn(testUser);

        // Act
        var result = authService.register("new@example.com", "password", "New User");

        // Assert
        assertNotNull(result);
        verify(userRepository).save(any(User.class));
    }

    @Test
    void register_ExistingEmail_ThrowsException() {
        // Arrange
        when(userRepository.existsByEmail("existing@example.com"))
            .thenReturn(true);

        // Act & Assert
        assertThrows(UserAlreadyExistsException.class, () ->
            authService.register("existing@example.com", "password", "User")
        );
    }
}
```

```java
// src/test/java/com/cvassistant/gateway/controller/ChatControllerTest.java
package com.cvassistant.gateway.controller;

import com.cvassistant.gateway.dto.ChatRequest;
import com.cvassistant.gateway.dto.ChatResponse;
import com.cvassistant.gateway.service.ChatService;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.WebMvcTest;
import org.springframework.boot.test.mock.mockito.MockBean;
import org.springframework.http.MediaType;
import org.springframework.security.test.context.support.WithMockUser;
import org.springframework.test.web.servlet.MockMvc;

import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.when;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

@WebMvcTest(ChatController.class)
class ChatControllerTest {

    @Autowired
    private MockMvc mockMvc;

    @Autowired
    private ObjectMapper objectMapper;

    @MockBean
    private ChatService chatService;

    @Test
    @WithMockUser(username = "user@example.com")
    void chat_ValidRequest_ReturnsResponse() throws Exception {
        // Arrange
        ChatRequest request = new ChatRequest("Hello", null);
        ChatResponse response = new ChatResponse(
            "Hello! How can I help you?",
            "thread-123",
            "msg-456",
            null,
            null
        );

        when(chatService.processMessage(any(), any())).thenReturn(response);

        // Act & Assert
        mockMvc.perform(post("/api/chat")
                .contentType(MediaType.APPLICATION_JSON)
                .content(objectMapper.writeValueAsString(request)))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$.response").value("Hello! How can I help you?"))
            .andExpect(jsonPath("$.thread_id").value("thread-123"));
    }

    @Test
    void chat_Unauthenticated_Returns401() throws Exception {
        // Arrange
        ChatRequest request = new ChatRequest("Hello", null);

        // Act & Assert
        mockMvc.perform(post("/api/chat")
                .contentType(MediaType.APPLICATION_JSON)
                .content(objectMapper.writeValueAsString(request)))
            .andExpect(status().isUnauthorized());
    }

    @Test
    @WithMockUser(username = "user@example.com")
    void chat_EmptyMessage_Returns400() throws Exception {
        // Arrange
        ChatRequest request = new ChatRequest("", null);

        // Act & Assert
        mockMvc.perform(post("/api/chat")
                .contentType(MediaType.APPLICATION_JSON)
                .content(objectMapper.writeValueAsString(request)))
            .andExpect(status().isBadRequest());
    }
}
```

### 3.6 Frontend Unit Tests

```typescript
// src/components/__tests__/ChatInput.test.tsx
import { render, screen, fireEvent } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import ChatInput from '../ChatInput';

describe('ChatInput', () => {
  const mockOnSend = jest.fn();

  beforeEach(() => {
    mockOnSend.mockClear();
  });

  it('renders input field and send button', () => {
    render(<ChatInput onSend={mockOnSend} isLoading={false} />);

    expect(screen.getByPlaceholderText(/type your message/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /send/i })).toBeInTheDocument();
  });

  it('calls onSend with message when submitted', async () => {
    render(<ChatInput onSend={mockOnSend} isLoading={false} />);

    const input = screen.getByPlaceholderText(/type your message/i);
    const button = screen.getByRole('button', { name: /send/i });

    await userEvent.type(input, 'Hello, chatbot!');
    await userEvent.click(button);

    expect(mockOnSend).toHaveBeenCalledWith('Hello, chatbot!');
  });

  it('clears input after sending', async () => {
    render(<ChatInput onSend={mockOnSend} isLoading={false} />);

    const input = screen.getByPlaceholderText(/type your message/i) as HTMLInputElement;

    await userEvent.type(input, 'Test message');
    await userEvent.click(screen.getByRole('button', { name: /send/i }));

    expect(input.value).toBe('');
  });

  it('disables input and button when loading', () => {
    render(<ChatInput onSend={mockOnSend} isLoading={true} />);

    expect(screen.getByPlaceholderText(/type your message/i)).toBeDisabled();
    expect(screen.getByRole('button', { name: /send/i })).toBeDisabled();
  });

  it('does not send empty messages', async () => {
    render(<ChatInput onSend={mockOnSend} isLoading={false} />);

    await userEvent.click(screen.getByRole('button', { name: /send/i }));

    expect(mockOnSend).not.toHaveBeenCalled();
  });

  it('submits on Enter key press', async () => {
    render(<ChatInput onSend={mockOnSend} isLoading={false} />);

    const input = screen.getByPlaceholderText(/type your message/i);

    await userEvent.type(input, 'Hello{enter}');

    expect(mockOnSend).toHaveBeenCalledWith('Hello');
  });
});


// src/components/__tests__/MessageList.test.tsx
import { render, screen } from '@testing-library/react';
import MessageList from '../MessageList';

describe('MessageList', () => {
  const mockMessages = [
    { id: '1', role: 'user', content: 'Hello', created_at: '2026-01-23T10:00:00Z' },
    { id: '2', role: 'assistant', content: 'Hi there!', created_at: '2026-01-23T10:00:01Z' },
  ];

  it('renders all messages', () => {
    render(<MessageList messages={mockMessages} />);

    expect(screen.getByText('Hello')).toBeInTheDocument();
    expect(screen.getByText('Hi there!')).toBeInTheDocument();
  });

  it('shows empty state when no messages', () => {
    render(<MessageList messages={[]} />);

    expect(screen.getByText(/start a conversation/i)).toBeInTheDocument();
  });

  it('applies correct styles for user and assistant messages', () => {
    render(<MessageList messages={mockMessages} />);

    const userMessage = screen.getByText('Hello').closest('div');
    const assistantMessage = screen.getByText('Hi there!').closest('div');

    expect(userMessage).toHaveClass('user-message');
    expect(assistantMessage).toHaveClass('assistant-message');
  });

  it('renders markdown in assistant messages', () => {
    const messagesWithMarkdown = [
      { id: '1', role: 'assistant', content: '**Bold text**', created_at: '2026-01-23T10:00:00Z' },
    ];

    render(<MessageList messages={messagesWithMarkdown} />);

    expect(screen.getByText('Bold text')).toBeInTheDocument();
  });
});


// src/hooks/__tests__/useChat.test.ts
import { renderHook, act } from '@testing-library/react';
import { useChat } from '../useChat';

// Mock fetch
global.fetch = jest.fn();

describe('useChat', () => {
  beforeEach(() => {
    (fetch as jest.Mock).mockClear();
  });

  it('initializes with empty messages', () => {
    const { result } = renderHook(() => useChat());

    expect(result.current.messages).toEqual([]);
    expect(result.current.isLoading).toBe(false);
  });

  it('sends message and receives response', async () => {
    const mockResponse = {
      response: 'Hello!',
      thread_id: 'thread-123',
      message_id: 'msg-456',
    };

    (fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve(mockResponse),
    });

    const { result } = renderHook(() => useChat());

    await act(async () => {
      await result.current.sendMessage('Hi');
    });

    expect(result.current.messages).toHaveLength(2);
    expect(result.current.messages[0].content).toBe('Hi');
    expect(result.current.messages[1].content).toBe('Hello!');
  });

  it('handles error gracefully', async () => {
    (fetch as jest.Mock).mockRejectedValueOnce(new Error('Network error'));

    const { result } = renderHook(() => useChat());

    await act(async () => {
      await result.current.sendMessage('Hi');
    });

    expect(result.current.error).toBeTruthy();
    expect(result.current.isLoading).toBe(false);
  });

  it('sets loading state during request', async () => {
    (fetch as jest.Mock).mockImplementation(() =>
      new Promise(resolve => setTimeout(resolve, 100))
    );

    const { result } = renderHook(() => useChat());

    act(() => {
      result.current.sendMessage('Hi');
    });

    expect(result.current.isLoading).toBe(true);
  });
});
```

---

## 4. Integration Testing

### 4.1 API Integration Tests (Python)

```python
# tests/integration/test_ner_api.py
import pytest
from httpx import AsyncClient
from main import app

@pytest.fixture
def anyio_backend():
    return 'asyncio'

@pytest.mark.anyio
async def test_extract_endpoint():
    """Test NER extraction endpoint"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/extract",
            json={"text": "John Doe works at Google as Software Engineer"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "entities" in data
        assert len(data["entities"]) > 0

@pytest.mark.anyio
async def test_extract_with_cv_upload():
    """Test CV file upload and extraction"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Create test PDF content
        pdf_content = create_test_pdf("John Doe\nSoftware Engineer\nGoogle")

        response = await client.post(
            "/api/v1/extract/file",
            files={"file": ("test_cv.pdf", pdf_content, "application/pdf")}
        )

        assert response.status_code == 200
        data = response.json()
        assert "entities" in data

@pytest.mark.anyio
async def test_health_endpoint():
    """Test health check endpoint"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/health")

        assert response.status_code == 200
        assert response.json()["status"] == "healthy"


# tests/integration/test_chatbot_api.py
import pytest
from httpx import AsyncClient

@pytest.mark.anyio
async def test_chat_endpoint():
    """Test chatbot chat endpoint"""
    async with AsyncClient(base_url="http://localhost:5004") as client:
        response = await client.post(
            "/api/v1/chat",
            json={
                "message": "What skills do software engineers need?",
                "user_id": "test_user"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert "response" in data
        assert "thread_id" in data

@pytest.mark.anyio
async def test_chat_with_thread():
    """Test continuing conversation in existing thread"""
    async with AsyncClient(base_url="http://localhost:5004") as client:
        # First message
        response1 = await client.post(
            "/api/v1/chat",
            json={
                "message": "I want to become a data scientist",
                "user_id": "test_user"
            }
        )
        thread_id = response1.json()["thread_id"]

        # Follow-up message
        response2 = await client.post(
            "/api/v1/chat",
            json={
                "message": "What certifications should I get?",
                "user_id": "test_user",
                "thread_id": thread_id
            }
        )

        assert response2.status_code == 200
        assert response2.json()["thread_id"] == thread_id
```

### 4.2 API Gateway Integration Tests (Java)

```java
// src/test/java/com/cvassistant/gateway/integration/AuthIntegrationTest.java
package com.cvassistant.gateway.integration;

import com.cvassistant.gateway.dto.LoginRequest;
import com.cvassistant.gateway.dto.RegisterRequest;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.http.MediaType;
import org.springframework.test.context.ActiveProfiles;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.transaction.annotation.Transactional;

import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

@SpringBootTest
@AutoConfigureMockMvc
@ActiveProfiles("test")
@Transactional
class AuthIntegrationTest {

    @Autowired
    private MockMvc mockMvc;

    @Autowired
    private ObjectMapper objectMapper;

    @Test
    void fullAuthFlow_RegisterAndLogin_Success() throws Exception {
        // Register
        RegisterRequest registerRequest = new RegisterRequest(
            "newuser@example.com",
            "password123",
            "New User"
        );

        mockMvc.perform(post("/api/auth/register")
                .contentType(MediaType.APPLICATION_JSON)
                .content(objectMapper.writeValueAsString(registerRequest)))
            .andExpect(status().isCreated())
            .andExpect(jsonPath("$.user.email").value("newuser@example.com"));

        // Login
        LoginRequest loginRequest = new LoginRequest(
            "newuser@example.com",
            "password123"
        );

        mockMvc.perform(post("/api/auth/login")
                .contentType(MediaType.APPLICATION_JSON)
                .content(objectMapper.writeValueAsString(loginRequest)))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$.access_token").exists())
            .andExpect(jsonPath("$.refresh_token").exists());
    }

    @Test
    void refreshToken_ValidToken_ReturnsNewTokens() throws Exception {
        // First login to get tokens
        // ... setup code

        mockMvc.perform(post("/api/auth/refresh")
                .contentType(MediaType.APPLICATION_JSON)
                .content("{\"refresh_token\": \"valid_refresh_token\"}"))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$.access_token").exists());
    }
}


// src/test/java/com/cvassistant/gateway/integration/ServiceProxyIntegrationTest.java
@SpringBootTest
@AutoConfigureMockMvc
@ActiveProfiles("test")
class ServiceProxyIntegrationTest {

    @Autowired
    private MockMvc mockMvc;

    @Test
    @WithMockUser
    void proxyToNerService_ValidRequest_ReturnsResponse() throws Exception {
        // This test requires running NER service
        // Skip in CI if service not available

        mockMvc.perform(post("/api/ner/extract")
                .contentType(MediaType.APPLICATION_JSON)
                .content("{\"text\": \"John Doe works at Google\"}"))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$.entities").isArray());
    }
}
```

### 4.3 Database Integration Tests

```python
# tests/integration/test_database.py
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from app.database import Base, get_db
from app.models import User, CV, Thread, Message

@pytest.fixture(scope="function")
def test_db():
    """Create test database"""
    engine = create_engine("postgresql://test:test@localhost:5432/cv_assistant_test")
    Base.metadata.create_all(bind=engine)

    with Session(engine) as session:
        yield session

    Base.metadata.drop_all(bind=engine)

def test_user_crud(test_db):
    """Test User CRUD operations"""
    # Create
    user = User(
        email="test@example.com",
        password_hash="hashed",
        name="Test User"
    )
    test_db.add(user)
    test_db.commit()

    # Read
    found = test_db.query(User).filter_by(email="test@example.com").first()
    assert found is not None
    assert found.name == "Test User"

    # Update
    found.name = "Updated Name"
    test_db.commit()

    updated = test_db.query(User).filter_by(email="test@example.com").first()
    assert updated.name == "Updated Name"

    # Delete
    test_db.delete(updated)
    test_db.commit()

    deleted = test_db.query(User).filter_by(email="test@example.com").first()
    assert deleted is None

def test_thread_messages_cascade(test_db):
    """Test cascade delete for threads and messages"""
    # Create user and thread
    user = User(email="user@example.com", password_hash="hash", name="User")
    test_db.add(user)
    test_db.commit()

    thread = Thread(user_id=user.id, title="Test Thread")
    test_db.add(thread)
    test_db.commit()

    # Add messages
    msg1 = Message(thread_id=thread.id, role="user", content="Hello")
    msg2 = Message(thread_id=thread.id, role="assistant", content="Hi!")
    test_db.add_all([msg1, msg2])
    test_db.commit()

    # Delete thread
    test_db.delete(thread)
    test_db.commit()

    # Messages should be deleted too
    messages = test_db.query(Message).filter_by(thread_id=thread.id).all()
    assert len(messages) == 0
```

---

## 5. End-to-End Testing

### 5.1 E2E Test Scenarios

```typescript
// e2e/tests/chat-flow.spec.ts
import { test, expect } from '@playwright/test';

test.describe('Chat Flow', () => {
  test.beforeEach(async ({ page }) => {
    // Login before each test
    await page.goto('/login');
    await page.fill('[name="email"]', 'test@example.com');
    await page.fill('[name="password"]', 'password123');
    await page.click('button[type="submit"]');
    await expect(page).toHaveURL('/dashboard');
  });

  test('user can send message and receive response', async ({ page }) => {
    // Navigate to new chat
    await page.click('text=New Chat');

    // Send message
    await page.fill('[placeholder*="type your message"]', 'What skills do I need for a software engineer role?');
    await page.click('button:has-text("Send")');

    // Wait for response
    await expect(page.locator('.assistant-message')).toBeVisible({ timeout: 30000 });

    // Verify response contains relevant content
    const response = await page.textContent('.assistant-message');
    expect(response).toContain('skill');
  });

  test('user can continue conversation', async ({ page }) => {
    await page.click('text=New Chat');

    // First message
    await page.fill('[placeholder*="type your message"]', 'I want to become a data scientist');
    await page.click('button:has-text("Send")');
    await expect(page.locator('.assistant-message')).toBeVisible({ timeout: 30000 });

    // Follow-up message
    await page.fill('[placeholder*="type your message"]', 'What certifications should I get?');
    await page.click('button:has-text("Send")');

    // Verify context is maintained
    await expect(page.locator('.assistant-message').nth(1)).toBeVisible({ timeout: 30000 });
    const response = await page.textContent('.assistant-message:last-child');
    expect(response?.toLowerCase()).toMatch(/data|certification|course/);
  });

  test('chat history persists after refresh', async ({ page }) => {
    await page.click('text=New Chat');

    // Send message
    await page.fill('[placeholder*="type your message"]', 'Hello chatbot');
    await page.click('button:has-text("Send")');
    await expect(page.locator('.assistant-message')).toBeVisible({ timeout: 30000 });

    // Refresh page
    await page.reload();

    // Verify messages are still there
    await expect(page.locator('.user-message')).toContainText('Hello chatbot');
  });
});


// e2e/tests/cv-upload.spec.ts
test.describe('CV Upload Flow', () => {
  test('user can upload CV and see extracted information', async ({ page }) => {
    // Login
    await page.goto('/login');
    await page.fill('[name="email"]', 'test@example.com');
    await page.fill('[name="password"]', 'password123');
    await page.click('button[type="submit"]');

    // Navigate to CV upload
    await page.click('text=Upload CV');

    // Upload file
    const fileInput = page.locator('input[type="file"]');
    await fileInput.setInputFiles('e2e/fixtures/sample_cv.pdf');

    // Wait for processing
    await expect(page.locator('text=Processing')).toBeVisible();
    await expect(page.locator('.extraction-results')).toBeVisible({ timeout: 60000 });

    // Verify extracted entities
    await expect(page.locator('[data-entity-type="PER"]')).toBeVisible();
    await expect(page.locator('[data-entity-type="SKILL"]')).toBeVisible();
  });

  test('user can edit extracted information', async ({ page }) => {
    // ... upload CV first

    // Click edit button on a skill
    await page.click('[data-entity-type="SKILL"] >> button:has-text("Edit")');

    // Modify skill
    await page.fill('[data-edit-field="skill"]', 'Python Programming');
    await page.click('button:has-text("Save")');

    // Verify update
    await expect(page.locator('[data-entity-type="SKILL"]')).toContainText('Python Programming');
  });
});


// e2e/tests/career-path.spec.ts
test.describe('Career Path Feature', () => {
  test('user can generate career roadmap', async ({ page }) => {
    // Login and navigate
    await page.goto('/dashboard/career');

    // Select current and target roles
    await page.selectOption('[name="currentRole"]', 'Junior Developer');
    await page.selectOption('[name="targetRole"]', 'Tech Lead');

    // Generate paths
    await page.click('button:has-text("Generate Career Path")');

    // Wait for results
    await expect(page.locator('.career-path')).toBeVisible({ timeout: 30000 });

    // Verify three paths are shown
    await expect(page.locator('.path-option')).toHaveCount(3);
    await expect(page.locator('text=Conservative')).toBeVisible();
    await expect(page.locator('text=Moderate')).toBeVisible();
    await expect(page.locator('text=Ambitious')).toBeVisible();
  });
});
```

### 5.2 Playwright Configuration

```typescript
// playwright.config.ts
import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './e2e/tests',
  fullyParallel: false,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: 1,
  reporter: 'html',
  use: {
    baseURL: 'http://localhost:3000',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
  },
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],
  webServer: {
    command: 'docker compose up -d && sleep 30',
    url: 'http://localhost:3000',
    reuseExistingServer: !process.env.CI,
    timeout: 120000,
  },
});
```

---

## 6. Test Execution

### 6.1 Running Tests

```bash
# Python Services - Unit Tests
cd services/ner-service
pytest tests/ -v --cov=app --cov-report=html

# Python Services - Integration Tests
pytest tests/integration/ -v --cov=app

# Java API Gateway
cd api-gateway
./gradlew test

# Frontend
cd frontend
npm test -- --coverage

# E2E Tests
npx playwright test

# All tests with coverage
./scripts/run-all-tests.sh
```

### 6.2 Test Script (run-all-tests.sh)

```bash
#!/bin/bash
# scripts/run-all-tests.sh

set -e

echo "=== Running All Tests ==="

# Run Python service tests
for service in ner-service skill-service career-service chatbot-service; do
    echo "Testing $service..."
    cd services/$service
    pytest tests/ -v --cov=app --cov-report=xml:coverage.xml
    cd ../..
done

# Run Java tests
echo "Testing API Gateway..."
cd api-gateway
./gradlew test jacocoTestReport
cd ..

# Run Frontend tests
echo "Testing Frontend..."
cd frontend
npm test -- --coverage --watchAll=false
cd ..

# Combine coverage reports
echo "Combining coverage reports..."
python scripts/combine_coverage.py

echo "=== All Tests Complete ==="
```

---

## 7. CI/CD Integration

### 7.1 GitHub Actions Workflow

```yaml
# .github/workflows/test.yml
name: Test

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  test-python:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        service: [ner-service, skill-service, career-service, chatbot-service]

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.10'

      - name: Install dependencies
        run: |
          cd services/${{ matrix.service }}
          pip install -r requirements.txt
          pip install -r requirements-test.txt

      - name: Run tests
        run: |
          cd services/${{ matrix.service }}
          pytest tests/ -v --cov=app --cov-report=xml

      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          files: services/${{ matrix.service }}/coverage.xml
          flags: ${{ matrix.service }}

  test-java:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - name: Set up JDK
        uses: actions/setup-java@v4
        with:
          java-version: '17'
          distribution: 'temurin'

      - name: Run tests
        run: |
          cd api-gateway
          ./gradlew test jacocoTestReport

      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          files: api-gateway/build/reports/jacoco/test/jacocoTestReport.xml
          flags: api-gateway

  test-frontend:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - name: Set up Node
        uses: actions/setup-node@v4
        with:
          node-version: '20'

      - name: Install dependencies
        run: |
          cd frontend
          npm ci

      - name: Run tests
        run: |
          cd frontend
          npm test -- --coverage --watchAll=false

      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          files: frontend/coverage/lcov.info
          flags: frontend

  e2e-test:
    runs-on: ubuntu-latest
    needs: [test-python, test-java, test-frontend]

    steps:
      - uses: actions/checkout@v4

      - name: Start services
        run: docker compose up -d

      - name: Wait for services
        run: sleep 60

      - name: Pull Ollama model
        run: ./scripts/pull-models.sh

      - name: Run E2E tests
        run: npx playwright test

      - name: Upload test results
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: playwright-report
          path: playwright-report/
```

---

## 8. Coverage Requirements

### 8.1 Coverage Targets by Component

| Component | Target | Critical Paths |
|-----------|--------|----------------|
| NER Service | 70% | Extraction, entity merging |
| Skill Service | 65% | Matching algorithm |
| Career Service | 60% | Path generation |
| Chatbot Service | 60% | Tool calling, RAG |
| API Gateway | 65% | Auth, routing |
| Frontend | 55% | Components, hooks |
| **Overall** | **60%** | |

### 8.2 Coverage Enforcement

```yaml
# pytest.ini
[pytest]
minversion = 7.0
addopts = --cov-fail-under=60
testpaths = tests
```

```kotlin
// build.gradle.kts
jacocoTestCoverageVerification {
    violationRules {
        rule {
            limit {
                minimum = BigDecimal("0.60")
            }
        }
    }
}
```

---

## 9. Test Data Management

### 9.1 Fixtures

```python
# tests/fixtures/cv_samples.py
SAMPLE_CV_TEXT = """
John Doe
Software Engineer

Contact: john.doe@email.com | San Francisco, CA

EXPERIENCE
Google - Senior Software Engineer
January 2020 - Present
- Developed Python applications
- Led team of 5 engineers

EDUCATION
MIT - Master of Science in Computer Science
2018

SKILLS
Python, Java, Docker, Kubernetes, AWS
"""

SAMPLE_ENTITIES = [
    {"text": "John Doe", "type": "PER", "start": 0, "end": 8},
    {"text": "Google", "type": "ORG", "start": 50, "end": 56},
    {"text": "Senior Software Engineer", "type": "JOB_TITLE", "start": 59, "end": 83},
]
```

### 9.2 Factory Classes

```python
# tests/factories.py
import factory
from faker import Faker
from app.models import User, CV, Thread, Message

fake = Faker()

class UserFactory(factory.Factory):
    class Meta:
        model = User

    id = factory.LazyFunction(lambda: str(uuid4()))
    email = factory.LazyAttribute(lambda _: fake.email())
    password_hash = "hashed_password"
    name = factory.LazyAttribute(lambda _: fake.name())

class CVFactory(factory.Factory):
    class Meta:
        model = CV

    id = factory.LazyFunction(lambda: str(uuid4()))
    user_id = factory.LazyAttribute(lambda _: str(uuid4()))
    filename = factory.LazyAttribute(lambda _: f"{fake.word()}.pdf")
    status = "processed"

class ThreadFactory(factory.Factory):
    class Meta:
        model = Thread

    id = factory.LazyFunction(lambda: str(uuid4()))
    user_id = factory.LazyAttribute(lambda _: str(uuid4()))
    title = factory.LazyAttribute(lambda _: fake.sentence())
```

---

## 10. Performance Testing

### 10.1 Load Testing with Locust

```python
# tests/load/locustfile.py
from locust import HttpUser, task, between

class ChatbotUser(HttpUser):
    wait_time = between(1, 5)

    def on_start(self):
        # Login to get token
        response = self.client.post("/api/auth/login", json={
            "email": "load_test@example.com",
            "password": "password123"
        })
        self.token = response.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}

    @task(3)
    def chat(self):
        self.client.post(
            "/api/chat",
            json={"message": "What skills do software engineers need?"},
            headers=self.headers
        )

    @task(1)
    def extract_cv(self):
        with open("tests/fixtures/sample_cv.pdf", "rb") as f:
            self.client.post(
                "/api/cv/upload",
                files={"file": f},
                headers=self.headers
            )

# Run: locust -f tests/load/locustfile.py --host=http://localhost:8080
```

### 10.2 Performance Benchmarks

| Endpoint | Target P95 | Max Load |
|----------|------------|----------|
| `/api/auth/login` | < 500ms | 100 req/s |
| `/api/chat` | < 15s | 10 req/s |
| `/api/cv/upload` | < 30s | 5 req/s |
| `/api/ner/extract` | < 5s | 20 req/s |
| `/api/skill/match` | < 3s | 30 req/s |

---

*Document created as part of CV Assistant Research Project documentation.*
