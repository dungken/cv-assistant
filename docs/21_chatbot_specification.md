# 21. Chatbot Specification

> **Document Version**: 1.0
> **Last Updated**: 2026-01-23
> **Status**: Approved
> **Product Name**: CV Assistant
> **Related Documents**: [09_system_architecture.md](./09_system_architecture.md), [17_api_specifications.md](./17_api_specifications.md), [18_data_models.md](./18_data_models.md)

---

## 1. Overview

This document provides comprehensive specifications for the Chatbot Service - the core feature of CV Assistant. The chatbot serves as a conversational AI assistant for career guidance, CV analysis, and job market insights.

### 1.1 Chatbot Role

| Aspect | Description |
|--------|-------------|
| **Primary Function** | General Q&A about CV, career, job market |
| **Availability** | Always available, independent of other flows |
| **Interaction Style** | ChatGPT/Gemini-like conversational interface |
| **Context Awareness** | Maintains conversation + user CV context |

### 1.2 Core Capabilities

```
┌─────────────────────────────────────────────────────────────────┐
│                    CHATBOT CAPABILITIES                          │
├─────────────────────────────────────────────────────────────────┤
│  1. General Career Q&A                                          │
│     • Answer questions about career paths                       │
│     • Provide industry insights                                 │
│     • Offer CV writing tips                                     │
│                                                                 │
│  2. CV Analysis (via NER Service)                               │
│     • Extract information from uploaded CVs                     │
│     • Identify skills and experience                            │
│     • Suggest improvements                                      │
│                                                                 │
│  3. Skill Matching (via Skill Service)                          │
│     • Compare CV skills with job descriptions                   │
│     • Identify skill gaps                                       │
│     • Recommend skills to learn                                 │
│                                                                 │
│  4. Career Recommendations (via Career Service)                 │
│     • Generate career roadmaps                                  │
│     • Suggest certifications                                    │
│     • Provide timeline estimates                                │
│                                                                 │
│  5. Personalized Advice                                         │
│     • Use user's CV data for context                            │
│     • Remember conversation history                             │
│     • Provide tailored recommendations                          │
└─────────────────────────────────────────────────────────────────┘
```

---

## 2. Technical Architecture

### 2.1 Technology Stack

| Component | Technology | Purpose |
|-----------|------------|---------|
| **LLM** | Llama 3.2 (3B) | Language understanding & generation |
| **LLM Server** | Ollama | Local LLM serving |
| **Agent Framework** | LlamaIndex | ReAct agent orchestration |
| **Vector Database** | ChromaDB | RAG knowledge base & memory |
| **Embedding Model** | all-MiniLM-L6-v2 | Text embeddings (384 dim) |
| **API Framework** | FastAPI | REST API server |

### 2.2 Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                    CHATBOT SERVICE                               │
│                    Port: 5004                                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐         │
│  │   FastAPI   │───▶│  LlamaIndex │───▶│   Ollama    │         │
│  │   Router    │    │    Agent    │    │  Llama 3.2  │         │
│  └─────────────┘    └──────┬──────┘    └─────────────┘         │
│                            │                                    │
│            ┌───────────────┼───────────────┐                   │
│            ▼               ▼               ▼                   │
│     ┌───────────┐   ┌───────────┐   ┌───────────┐              │
│     │    RAG    │   │   Tool    │   │  Memory   │              │
│     │  Pipeline │   │  Calling  │   │  Manager  │              │
│     └─────┬─────┘   └─────┬─────┘   └─────┬─────┘              │
│           │               │               │                    │
│           ▼               ▼               ▼                    │
│     ┌───────────┐   ┌───────────┐   ┌───────────┐              │
│     │ ChromaDB  │   │  External │   │ ChromaDB  │              │
│     │ Knowledge │   │  Services │   │  Memory   │              │
│     └───────────┘   └───────────┘   └───────────┘              │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
                              │
              ┌───────────────┼───────────────┐
              ▼               ▼               ▼
      ┌───────────┐   ┌───────────┐   ┌───────────┐
      │    NER    │   │   Skill   │   │  Career   │
      │  Service  │   │  Service  │   │  Service  │
      │   :5001   │   │   :5002   │   │   :5003   │
      └───────────┘   └───────────┘   └───────────┘
```

### 2.3 Response Time Targets

| Operation | Target | Notes |
|-----------|--------|-------|
| Simple Q&A | 5-8 seconds | No tool calling |
| With RAG retrieval | 8-12 seconds | Knowledge base lookup |
| With tool calling | 10-15 seconds | External service calls |
| Maximum | 30 seconds | Timeout with retry |

---

## 3. LlamaIndex Agent Implementation

### 3.1 Agent Configuration

```python
# chatbot_service/agent/config.py
from dataclasses import dataclass
from typing import Optional

@dataclass
class AgentConfig:
    # LLM Settings
    ollama_host: str = "ollama"
    ollama_port: int = 11434
    model_name: str = "llama3.2:3b"
    temperature: float = 0.7
    max_tokens: int = 2048
    request_timeout: float = 60.0

    # RAG Settings
    chroma_host: str = "chromadb"
    chroma_port: int = 8000
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    top_k: int = 5
    similarity_threshold: float = 0.7

    # Memory Settings
    max_history_tokens: int = 4096
    conversation_window: int = 10

    # Tool Settings
    tool_timeout: float = 30.0
    max_retries: int = 2
```

### 3.2 Agent Implementation

```python
# chatbot_service/agent/cv_assistant_agent.py
from llama_index.core import VectorStoreIndex, Settings
from llama_index.core.agent import ReActAgent
from llama_index.core.tools import FunctionTool, QueryEngineTool
from llama_index.llms.ollama import Ollama
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.vector_stores.chroma import ChromaVectorStore
import chromadb
from typing import List, Optional
import httpx

from .config import AgentConfig
from .tools import CVTools
from .memory import ConversationMemory
from .prompts import SYSTEM_PROMPT, REACT_PROMPT

class CVAssistantAgent:
    def __init__(self, config: AgentConfig):
        self.config = config
        self._setup_llm()
        self._setup_embeddings()
        self._setup_vector_store()
        self._setup_tools()
        self._setup_agent()
        self.memory = ConversationMemory(config)

    def _setup_llm(self):
        """Initialize Ollama LLM"""
        self.llm = Ollama(
            model=self.config.model_name,
            base_url=f"http://{self.config.ollama_host}:{self.config.ollama_port}",
            temperature=self.config.temperature,
            request_timeout=self.config.request_timeout,
            additional_kwargs={
                "num_predict": self.config.max_tokens,
            }
        )
        Settings.llm = self.llm

    def _setup_embeddings(self):
        """Initialize embedding model"""
        self.embed_model = HuggingFaceEmbedding(
            model_name=self.config.embedding_model
        )
        Settings.embed_model = self.embed_model

    def _setup_vector_store(self):
        """Initialize ChromaDB vector store"""
        self.chroma_client = chromadb.HttpClient(
            host=self.config.chroma_host,
            port=self.config.chroma_port
        )

        # Knowledge base collection
        self.knowledge_collection = self.chroma_client.get_or_create_collection(
            name="cv_assistant_knowledge"
        )
        self.knowledge_store = ChromaVectorStore(
            chroma_collection=self.knowledge_collection
        )
        self.knowledge_index = VectorStoreIndex.from_vector_store(
            self.knowledge_store,
            embed_model=self.embed_model
        )

    def _setup_tools(self):
        """Setup agent tools"""
        self.cv_tools = CVTools(self.config)

        # RAG Query Tool
        self.query_engine = self.knowledge_index.as_query_engine(
            similarity_top_k=self.config.top_k
        )

        self.tools = [
            # Knowledge Base Tool
            QueryEngineTool.from_defaults(
                query_engine=self.query_engine,
                name="knowledge_base",
                description=(
                    "Use this tool to search the knowledge base for information about "
                    "careers, skills, job market, CV writing tips, and industry insights. "
                    "Input should be a search query."
                )
            ),

            # NER Extraction Tool
            FunctionTool.from_defaults(
                fn=self.cv_tools.extract_cv_info,
                name="extract_cv_info",
                description=(
                    "Use this tool to extract structured information from CV text. "
                    "Input should be the raw CV text. Returns extracted entities like "
                    "name, skills, experience, education, etc."
                )
            ),

            # Skill Matching Tool
            FunctionTool.from_defaults(
                fn=self.cv_tools.match_skills,
                name="match_skills",
                description=(
                    "Use this tool to compare CV skills with job description requirements. "
                    "Input should be a dict with 'cv_skills' (list) and 'jd_text' (string). "
                    "Returns matching score and skill gaps."
                )
            ),

            # Career Path Tool
            FunctionTool.from_defaults(
                fn=self.cv_tools.generate_career_path,
                name="generate_career_path",
                description=(
                    "Use this tool to generate career roadmap from current role to target role. "
                    "Input should be a dict with 'current_role', 'target_role', and optionally "
                    "'current_skills'. Returns three career paths (conservative, moderate, ambitious)."
                )
            ),

            # User CV Context Tool
            FunctionTool.from_defaults(
                fn=self.cv_tools.get_user_cv_context,
                name="get_user_cv",
                description=(
                    "Use this tool to retrieve the user's uploaded CV information for context. "
                    "Input should be the user_id. Returns structured CV data if available."
                )
            )
        ]

    def _setup_agent(self):
        """Initialize ReAct agent"""
        self.agent = ReActAgent.from_tools(
            tools=self.tools,
            llm=self.llm,
            verbose=True,
            max_iterations=5,
            system_prompt=SYSTEM_PROMPT,
            react_chat_formatter=REACT_PROMPT
        )

    async def chat(
        self,
        message: str,
        user_id: str,
        thread_id: Optional[str] = None
    ) -> dict:
        """
        Process a chat message and return response.

        Args:
            message: User's message
            user_id: User identifier
            thread_id: Optional thread ID for conversation continuity

        Returns:
            dict with response, thread_id, sources, etc.
        """
        # Get or create thread
        if not thread_id:
            thread_id = self.memory.create_thread(user_id)

        # Get conversation history
        history = self.memory.get_history(thread_id, self.config.conversation_window)

        # Get user's CV context if available
        cv_context = await self._get_cv_context(user_id)

        # Build context-aware prompt
        context_prompt = self._build_context_prompt(message, history, cv_context)

        # Store user message
        self.memory.add_message(thread_id, "user", message)

        try:
            # Run agent
            response = await self._run_agent(context_prompt)

            # Store assistant response
            self.memory.add_message(
                thread_id,
                "assistant",
                response.response,
                metadata={"sources": response.source_nodes if hasattr(response, 'source_nodes') else None}
            )

            return {
                "response": response.response,
                "thread_id": thread_id,
                "message_id": self.memory.get_last_message_id(thread_id),
                "sources": self._extract_sources(response),
                "tool_results": self._extract_tool_results(response)
            }

        except Exception as e:
            error_response = f"I apologize, but I encountered an error: {str(e)}. Please try again."
            self.memory.add_message(thread_id, "assistant", error_response)
            return {
                "response": error_response,
                "thread_id": thread_id,
                "message_id": self.memory.get_last_message_id(thread_id),
                "error": str(e)
            }

    async def _run_agent(self, prompt: str):
        """Run the ReAct agent with the given prompt"""
        return await self.agent.achat(prompt)

    async def _get_cv_context(self, user_id: str) -> Optional[dict]:
        """Retrieve user's CV data for context"""
        try:
            return await self.cv_tools.get_user_cv_context(user_id)
        except Exception:
            return None

    def _build_context_prompt(
        self,
        message: str,
        history: List[dict],
        cv_context: Optional[dict]
    ) -> str:
        """Build a context-aware prompt"""
        prompt_parts = []

        # Add CV context if available
        if cv_context:
            prompt_parts.append(f"[User's CV Context]\n{self._format_cv_context(cv_context)}\n")

        # Add conversation history
        if history:
            prompt_parts.append("[Conversation History]")
            for msg in history[-5:]:  # Last 5 messages
                role = "User" if msg["role"] == "user" else "Assistant"
                prompt_parts.append(f"{role}: {msg['content']}")
            prompt_parts.append("")

        # Add current message
        prompt_parts.append(f"User: {message}")

        return "\n".join(prompt_parts)

    def _format_cv_context(self, cv_context: dict) -> str:
        """Format CV context for prompt"""
        parts = []
        if cv_context.get("name"):
            parts.append(f"Name: {cv_context['name']}")
        if cv_context.get("current_role"):
            parts.append(f"Current Role: {cv_context['current_role']}")
        if cv_context.get("skills"):
            parts.append(f"Skills: {', '.join(cv_context['skills'][:10])}")
        if cv_context.get("experience_years"):
            parts.append(f"Experience: {cv_context['experience_years']} years")
        return "\n".join(parts)

    def _extract_sources(self, response) -> List[str]:
        """Extract source references from response"""
        sources = []
        if hasattr(response, 'source_nodes'):
            for node in response.source_nodes:
                if hasattr(node, 'metadata') and 'source' in node.metadata:
                    sources.append(node.metadata['source'])
        return sources

    def _extract_tool_results(self, response) -> Optional[dict]:
        """Extract tool call results from response"""
        if hasattr(response, 'sources'):
            return {
                "tools_used": [s.tool_name for s in response.sources if hasattr(s, 'tool_name')]
            }
        return None
```

### 3.3 Tool Implementations

```python
# chatbot_service/agent/tools.py
import httpx
from typing import List, Optional, Dict, Any

class CVTools:
    def __init__(self, config):
        self.config = config
        self.ner_url = f"http://ner-service:5001"
        self.skill_url = f"http://skill-service:5002"
        self.career_url = f"http://career-service:5003"
        self.timeout = config.tool_timeout

    async def extract_cv_info(self, cv_text: str) -> Dict[str, Any]:
        """
        Extract structured information from CV text using NER service.

        Args:
            cv_text: Raw CV text content

        Returns:
            Extracted CV information including entities
        """
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.ner_url}/api/v1/extract",
                json={"text": cv_text}
            )
            response.raise_for_status()
            return response.json()

    async def match_skills(self, match_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Compare CV skills with job description requirements.

        Args:
            match_data: Dict with 'cv_skills' and 'jd_text'

        Returns:
            Skill matching results including score and gaps
        """
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.skill_url}/api/v1/match",
                json={
                    "cv_skills": match_data.get("cv_skills", []),
                    "jd_text": match_data.get("jd_text", "")
                }
            )
            response.raise_for_status()
            return response.json()

    async def generate_career_path(self, path_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate career roadmap from current to target role.

        Args:
            path_data: Dict with 'current_role', 'target_role', 'current_skills'

        Returns:
            Three career paths (conservative, moderate, ambitious)
        """
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.career_url}/api/v1/recommend",
                json={
                    "current_role": path_data.get("current_role"),
                    "target_role": path_data.get("target_role"),
                    "current_skills": path_data.get("current_skills", [])
                }
            )
            response.raise_for_status()
            return response.json()

    async def get_user_cv_context(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve user's uploaded CV information.

        Args:
            user_id: User identifier

        Returns:
            Structured CV data if available
        """
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(
                f"http://api-gateway:8080/internal/users/{user_id}/cv"
            )
            if response.status_code == 404:
                return None
            response.raise_for_status()
            return response.json()
```

---

## 4. RAG (Retrieval-Augmented Generation)

### 4.1 Knowledge Base Structure

```python
# Knowledge base collections in ChromaDB
COLLECTIONS = {
    "cv_assistant_knowledge": {
        "description": "Main knowledge base for career information",
        "sources": [
            "O*NET Database",
            "CV Writing Guides",
            "Job Market Reports",
            "Industry Standards"
        ]
    },
    "cv_embeddings": {
        "description": "User CV embeddings for personalized context",
        "per_user": True
    },
    "conversation_memory": {
        "description": "Conversation history embeddings",
        "per_user": True
    }
}
```

### 4.2 Knowledge Base Data Sources

| Source | Data Type | Update Frequency |
|--------|-----------|-----------------|
| **O*NET Database** | Jobs, skills, career transitions | Quarterly |
| **CV Writing Guides** | Best practices, tips, examples | Static |
| **Job Market Data** | Trends, salary info, demand | Monthly |
| **Industry Standards** | Tech stacks, methodologies | As needed |

### 4.3 Document Ingestion Pipeline

```python
# chatbot_service/rag/ingestion.py
from llama_index.core import Document
from llama_index.core.node_parser import SentenceSplitter
from llama_index.vector_stores.chroma import ChromaVectorStore
import json
from pathlib import Path

class KnowledgeIngestion:
    def __init__(self, chroma_client, embed_model):
        self.chroma_client = chroma_client
        self.embed_model = embed_model
        self.splitter = SentenceSplitter(
            chunk_size=512,
            chunk_overlap=50
        )

    async def ingest_onet_data(self, onet_path: Path):
        """Ingest O*NET occupations and skills data"""
        documents = []

        # Load occupations
        with open(onet_path / "occupations.json") as f:
            occupations = json.load(f)

        for occ in occupations["occupations"]:
            doc_text = f"""
            Occupation: {occ['title']}
            Code: {occ['code']}
            Description: {occ['description']}
            Median Salary: ${occ.get('median_salary', 'N/A')}
            Required Skills: {', '.join(occ.get('required_skills', []))}
            Related Occupations: {', '.join(occ.get('related_occupations', []))}
            """

            documents.append(Document(
                text=doc_text,
                metadata={
                    "source": "O*NET Database",
                    "category": "occupation",
                    "occupation_code": occ['code'],
                    "occupation_title": occ['title']
                }
            ))

        await self._store_documents(documents, "cv_assistant_knowledge")

    async def ingest_cv_guides(self, guides_path: Path):
        """Ingest CV writing guides and tips"""
        documents = []

        for guide_file in guides_path.glob("*.md"):
            content = guide_file.read_text()
            documents.append(Document(
                text=content,
                metadata={
                    "source": "CV Writing Guide",
                    "category": "cv_guide",
                    "file": guide_file.name
                }
            ))

        await self._store_documents(documents, "cv_assistant_knowledge")

    async def ingest_user_cv(self, user_id: str, cv_data: dict):
        """Store user CV embeddings for personalized context"""
        documents = []

        # Create documents for each CV section
        if cv_data.get("work_experience"):
            for exp in cv_data["work_experience"]:
                doc_text = f"""
                Experience at {exp.get('company', 'Unknown')}
                Role: {exp.get('title', 'Unknown')}
                Period: {exp.get('start_date', '')} - {exp.get('end_date', 'Present')}
                Description: {exp.get('description', '')}
                """
                documents.append(Document(
                    text=doc_text,
                    metadata={
                        "user_id": user_id,
                        "section": "work_experience",
                        "cv_id": cv_data.get("cv_id")
                    }
                ))

        if cv_data.get("skills"):
            doc_text = f"Skills: {', '.join(cv_data['skills'])}"
            documents.append(Document(
                text=doc_text,
                metadata={
                    "user_id": user_id,
                    "section": "skills",
                    "cv_id": cv_data.get("cv_id")
                }
            ))

        collection_name = f"cv_embeddings_{user_id}"
        await self._store_documents(documents, collection_name)

    async def _store_documents(self, documents: list, collection_name: str):
        """Store documents in ChromaDB collection"""
        collection = self.chroma_client.get_or_create_collection(collection_name)
        vector_store = ChromaVectorStore(chroma_collection=collection)

        # Split documents into nodes
        nodes = self.splitter.get_nodes_from_documents(documents)

        # Generate embeddings and store
        for i, node in enumerate(nodes):
            embedding = self.embed_model.get_text_embedding(node.text)
            collection.add(
                ids=[f"{collection_name}_{i}"],
                embeddings=[embedding],
                documents=[node.text],
                metadatas=[node.metadata]
            )
```

### 4.4 RAG Query Pipeline

```python
# chatbot_service/rag/retriever.py
from llama_index.core import VectorStoreIndex
from llama_index.core.retrievers import VectorIndexRetriever
from typing import List, Optional

class RAGRetriever:
    def __init__(self, chroma_client, embed_model, config):
        self.chroma_client = chroma_client
        self.embed_model = embed_model
        self.config = config

    async def retrieve(
        self,
        query: str,
        user_id: Optional[str] = None,
        top_k: int = 5,
        include_user_cv: bool = True
    ) -> List[dict]:
        """
        Retrieve relevant context for a query.

        Args:
            query: User query
            user_id: Optional user ID for personalized retrieval
            top_k: Number of results to return
            include_user_cv: Whether to include user's CV context

        Returns:
            List of relevant document chunks with metadata
        """
        results = []

        # Query main knowledge base
        knowledge_results = await self._query_collection(
            "cv_assistant_knowledge",
            query,
            top_k
        )
        results.extend(knowledge_results)

        # Query user's CV if available
        if user_id and include_user_cv:
            cv_results = await self._query_collection(
                f"cv_embeddings_{user_id}",
                query,
                top_k=3
            )
            results.extend(cv_results)

        # Sort by relevance and deduplicate
        results = self._deduplicate_and_rank(results, top_k)

        return results

    async def _query_collection(
        self,
        collection_name: str,
        query: str,
        top_k: int
    ) -> List[dict]:
        """Query a specific ChromaDB collection"""
        try:
            collection = self.chroma_client.get_collection(collection_name)
        except Exception:
            return []

        # Generate query embedding
        query_embedding = self.embed_model.get_text_embedding(query)

        # Query ChromaDB
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            include=["documents", "metadatas", "distances"]
        )

        formatted_results = []
        for i, doc in enumerate(results["documents"][0]):
            formatted_results.append({
                "text": doc,
                "metadata": results["metadatas"][0][i],
                "score": 1 - results["distances"][0][i],  # Convert distance to similarity
                "collection": collection_name
            })

        return formatted_results

    def _deduplicate_and_rank(
        self,
        results: List[dict],
        top_k: int
    ) -> List[dict]:
        """Deduplicate and rank results by relevance"""
        # Remove near-duplicates
        seen_texts = set()
        unique_results = []

        for result in results:
            text_hash = hash(result["text"][:100])
            if text_hash not in seen_texts:
                seen_texts.add(text_hash)
                unique_results.append(result)

        # Sort by score
        unique_results.sort(key=lambda x: x["score"], reverse=True)

        return unique_results[:top_k]
```

---

## 5. Conversation Memory

### 5.1 Memory Architecture

```python
# chatbot_service/memory/conversation_memory.py
from datetime import datetime
from typing import List, Optional, Dict
import chromadb
from uuid import uuid4

class ConversationMemory:
    def __init__(self, config):
        self.config = config
        self.chroma_client = chromadb.HttpClient(
            host=config.chroma_host,
            port=config.chroma_port
        )

    def create_thread(self, user_id: str, title: Optional[str] = None) -> str:
        """Create a new conversation thread"""
        thread_id = str(uuid4())
        collection = self._get_thread_collection(user_id)

        # Store thread metadata
        collection.add(
            ids=[f"thread_{thread_id}_meta"],
            documents=[title or "New Conversation"],
            metadatas=[{
                "type": "thread_meta",
                "thread_id": thread_id,
                "user_id": user_id,
                "created_at": datetime.utcnow().isoformat()
            }]
        )

        return thread_id

    def add_message(
        self,
        thread_id: str,
        role: str,
        content: str,
        metadata: Optional[dict] = None
    ) -> str:
        """Add a message to conversation history"""
        message_id = str(uuid4())
        # Get user_id from thread
        user_id = self._get_user_from_thread(thread_id)
        collection = self._get_thread_collection(user_id)

        msg_metadata = {
            "type": "message",
            "thread_id": thread_id,
            "message_id": message_id,
            "role": role,
            "created_at": datetime.utcnow().isoformat()
        }
        if metadata:
            msg_metadata.update(metadata)

        collection.add(
            ids=[f"msg_{message_id}"],
            documents=[content],
            metadatas=[msg_metadata]
        )

        return message_id

    def get_history(
        self,
        thread_id: str,
        limit: int = 10
    ) -> List[Dict]:
        """Get conversation history for a thread"""
        user_id = self._get_user_from_thread(thread_id)
        collection = self._get_thread_collection(user_id)

        results = collection.get(
            where={"thread_id": thread_id, "type": "message"},
            include=["documents", "metadatas"]
        )

        messages = []
        for i, doc in enumerate(results["documents"]):
            messages.append({
                "id": results["metadatas"][i]["message_id"],
                "role": results["metadatas"][i]["role"],
                "content": doc,
                "created_at": results["metadatas"][i]["created_at"]
            })

        # Sort by timestamp and limit
        messages.sort(key=lambda x: x["created_at"])
        return messages[-limit:]

    def get_relevant_context(
        self,
        user_id: str,
        query: str,
        top_k: int = 3
    ) -> List[str]:
        """Get relevant past conversation context using semantic search"""
        collection = self._get_thread_collection(user_id)

        # Query for semantically similar past messages
        results = collection.query(
            query_texts=[query],
            n_results=top_k,
            where={"type": "message"}
        )

        return results["documents"][0] if results["documents"] else []

    def get_last_message_id(self, thread_id: str) -> str:
        """Get the ID of the last message in a thread"""
        user_id = self._get_user_from_thread(thread_id)
        collection = self._get_thread_collection(user_id)

        results = collection.get(
            where={"thread_id": thread_id, "type": "message"},
            include=["metadatas"]
        )

        if not results["metadatas"]:
            return ""

        # Get latest message
        latest = max(results["metadatas"], key=lambda x: x["created_at"])
        return latest["message_id"]

    def _get_thread_collection(self, user_id: str):
        """Get or create user's conversation collection"""
        collection_name = f"conversations_{user_id}"
        return self.chroma_client.get_or_create_collection(collection_name)

    def _get_user_from_thread(self, thread_id: str) -> str:
        """Get user_id from thread_id (stored in PostgreSQL, cached)"""
        # In production, this would query the database
        # For now, we assume thread_id contains user info or is cached
        return thread_id.split("_")[0] if "_" in thread_id else "default_user"
```

---

## 6. Prompts and Templates

### 6.1 System Prompt

```python
# chatbot_service/agent/prompts.py

SYSTEM_PROMPT = """You are CV Assistant, an AI-powered career advisor and CV expert.

Your role is to help users with:
1. **CV Analysis**: Extract and analyze information from CVs
2. **Career Guidance**: Provide advice on career paths and transitions
3. **Skill Development**: Identify skill gaps and recommend learning paths
4. **Job Matching**: Compare skills with job requirements
5. **General Career Q&A**: Answer questions about careers, industries, and job market

Guidelines:
- Be helpful, professional, and encouraging
- Provide specific, actionable advice when possible
- Use the user's CV context when available for personalized recommendations
- If you don't know something, say so honestly
- For technical questions about specific companies or roles, use the knowledge base
- When analyzing CVs, be constructive in feedback

Available Tools:
- knowledge_base: Search career information, job market data, CV tips
- extract_cv_info: Extract structured information from CV text
- match_skills: Compare CV skills with job requirements
- generate_career_path: Create career roadmaps
- get_user_cv: Retrieve user's CV for context

Always think step-by-step when handling complex queries.
"""
```

### 6.2 ReAct Prompt Template

```python
REACT_PROMPT = """You are an AI assistant that can use tools to help answer questions.

Available Tools:
{tool_descriptions}

Use the following format:

Question: the input question you must answer
Thought: you should always think about what to do
Action: the action to take, should be one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action
... (this Thought/Action/Action Input/Observation can repeat N times)
Thought: I now know the final answer
Final Answer: the final answer to the original input question

Important:
- Only use tools when necessary
- For simple questions, answer directly without tools
- When using user's CV context, personalize your response
- Be concise but thorough

Begin!

{history}

Question: {input}
{agent_scratchpad}
"""
```

### 6.3 Response Templates

```python
TEMPLATES = {
    "cv_analysis": """
Based on your CV analysis:

**Summary**
{summary}

**Key Strengths**
{strengths}

**Areas for Improvement**
{improvements}

**Recommendations**
{recommendations}
""",

    "skill_match": """
**Skill Matching Results**

Match Score: {score}/100

**Matching Skills** ({match_count})
{matching_skills}

**Missing Skills** ({missing_count})
{missing_skills}

**Recommendations**
{recommendations}
""",

    "career_path": """
**Career Roadmap: {current_role} → {target_role}**

{paths}

**Skill Gap Analysis**
- Missing Skills: {missing_skills}
- Skills to Improve: {improve_skills}

Would you like more details on any specific path?
""",

    "error_response": """
I apologize, but I encountered an issue while processing your request.

Error: {error_message}

Please try:
1. Rephrasing your question
2. Providing more specific details
3. Breaking down complex requests into smaller parts

If the issue persists, please try again later.
"""
}
```

---

## 7. API Endpoints

### 7.1 Chat API

```python
# chatbot_service/api/routes.py
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

router = APIRouter(prefix="/api/v1", tags=["chat"])

class ChatRequest(BaseModel):
    message: str
    user_id: str
    thread_id: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    thread_id: str
    message_id: str
    sources: Optional[List[str]] = None
    tool_results: Optional[dict] = None
    created_at: datetime

@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest, agent: CVAssistantAgent = Depends(get_agent)):
    """
    Send a message to the CV Assistant chatbot.

    - **message**: The user's message
    - **user_id**: User identifier for personalization
    - **thread_id**: Optional thread ID to continue a conversation
    """
    result = await agent.chat(
        message=request.message,
        user_id=request.user_id,
        thread_id=request.thread_id
    )

    return ChatResponse(
        response=result["response"],
        thread_id=result["thread_id"],
        message_id=result["message_id"],
        sources=result.get("sources"),
        tool_results=result.get("tool_results"),
        created_at=datetime.utcnow()
    )

@router.get("/threads/{user_id}")
async def get_threads(user_id: str, limit: int = 20):
    """Get user's conversation threads"""
    # Implementation
    pass

@router.get("/threads/{thread_id}/messages")
async def get_messages(thread_id: str, limit: int = 50):
    """Get messages in a conversation thread"""
    # Implementation
    pass

@router.delete("/threads/{thread_id}")
async def delete_thread(thread_id: str):
    """Delete a conversation thread"""
    # Implementation
    pass

@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "chatbot-service"}
```

---

## 8. Error Handling

### 8.1 Error Types

```python
# chatbot_service/errors.py
from enum import Enum

class ChatbotErrorCode(Enum):
    LLM_TIMEOUT = "LLM_TIMEOUT"
    LLM_ERROR = "LLM_ERROR"
    TOOL_ERROR = "TOOL_ERROR"
    RAG_ERROR = "RAG_ERROR"
    MEMORY_ERROR = "MEMORY_ERROR"
    INVALID_INPUT = "INVALID_INPUT"
    SERVICE_UNAVAILABLE = "SERVICE_UNAVAILABLE"

class ChatbotError(Exception):
    def __init__(self, code: ChatbotErrorCode, message: str, details: dict = None):
        self.code = code
        self.message = message
        self.details = details or {}
        super().__init__(message)
```

### 8.2 Retry and Fallback Strategy

```python
# chatbot_service/resilience.py
import asyncio
from functools import wraps
from typing import Callable, Any

def with_retry(max_retries: int = 2, delay: float = 1.0):
    """Decorator for retry logic"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            last_error = None
            for attempt in range(max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_error = e
                    if attempt < max_retries:
                        await asyncio.sleep(delay * (attempt + 1))
            raise last_error
        return wrapper
    return decorator

def with_fallback(fallback_func: Callable):
    """Decorator for fallback on failure"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            try:
                return await func(*args, **kwargs)
            except Exception:
                return await fallback_func(*args, **kwargs)
        return wrapper
    return decorator

# Usage example
@with_retry(max_retries=2)
@with_fallback(fallback_response)
async def process_chat(message: str, user_id: str):
    return await agent.chat(message, user_id)
```

---

## 9. Performance Optimization

### 9.1 CPU-Only Optimizations

```python
# Ollama configuration for CPU-only systems
OLLAMA_CONFIG = {
    "num_ctx": 2048,        # Context window size
    "num_batch": 256,       # Batch size for prompt processing
    "num_thread": 4,        # Number of threads (match CPU cores)
    "num_gpu": 0,           # Disable GPU
    "num_predict": 512,     # Max tokens to generate
    "repeat_penalty": 1.1,  # Reduce repetition
    "temperature": 0.7,     # Balance creativity/consistency
}
```

### 9.2 Response Caching

```python
# chatbot_service/cache.py
from functools import lru_cache
from typing import Optional
import hashlib

class ResponseCache:
    def __init__(self, max_size: int = 1000):
        self.cache = {}
        self.max_size = max_size

    def get_cache_key(self, query: str, user_id: str) -> str:
        """Generate cache key for a query"""
        # Only cache non-personalized queries
        content = f"{query.lower().strip()}"
        return hashlib.md5(content.encode()).hexdigest()

    def get(self, key: str) -> Optional[dict]:
        """Get cached response"""
        return self.cache.get(key)

    def set(self, key: str, response: dict, ttl: int = 3600):
        """Cache a response"""
        if len(self.cache) >= self.max_size:
            # Remove oldest entries
            oldest_keys = list(self.cache.keys())[:100]
            for k in oldest_keys:
                del self.cache[k]

        self.cache[key] = {
            "response": response,
            "cached_at": datetime.utcnow(),
            "ttl": ttl
        }
```

### 9.3 Async Processing

```python
# chatbot_service/async_utils.py
import asyncio
from concurrent.futures import ThreadPoolExecutor

executor = ThreadPoolExecutor(max_workers=4)

async def run_in_executor(func, *args):
    """Run CPU-bound operations in thread pool"""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(executor, func, *args)

async def parallel_retrieve(queries: list, retriever):
    """Run multiple retrievals in parallel"""
    tasks = [retriever.retrieve(q) for q in queries]
    return await asyncio.gather(*tasks)
```

---

## 10. Monitoring and Logging

### 10.1 Metrics

```python
# chatbot_service/metrics.py
from prometheus_client import Counter, Histogram, Gauge

# Request metrics
CHAT_REQUESTS = Counter(
    'chatbot_requests_total',
    'Total chat requests',
    ['status']
)

CHAT_LATENCY = Histogram(
    'chatbot_request_latency_seconds',
    'Chat request latency',
    buckets=[1, 5, 10, 15, 30, 60]
)

TOOL_CALLS = Counter(
    'chatbot_tool_calls_total',
    'Total tool calls',
    ['tool_name', 'status']
)

# Resource metrics
ACTIVE_THREADS = Gauge(
    'chatbot_active_threads',
    'Number of active conversation threads'
)

LLM_QUEUE_SIZE = Gauge(
    'chatbot_llm_queue_size',
    'Number of requests waiting for LLM'
)
```

### 10.2 Structured Logging

```python
# chatbot_service/logging_config.py
import logging
import json
from datetime import datetime

class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "service": "chatbot-service",
            "module": record.module,
            "function": record.funcName
        }

        if hasattr(record, 'user_id'):
            log_data["user_id"] = record.user_id
        if hasattr(record, 'thread_id'):
            log_data["thread_id"] = record.thread_id
        if hasattr(record, 'latency_ms'):
            log_data["latency_ms"] = record.latency_ms

        return json.dumps(log_data)

# Usage
logger = logging.getLogger("chatbot")
logger.info("Chat request processed", extra={
    "user_id": user_id,
    "thread_id": thread_id,
    "latency_ms": latency_ms
})
```

---

## 11. Security Considerations

### 11.1 Input Validation

```python
# chatbot_service/security.py
import re
from typing import Optional

MAX_MESSAGE_LENGTH = 10000
MAX_CONTEXT_LENGTH = 50000

def validate_message(message: str) -> tuple[bool, Optional[str]]:
    """Validate user message input"""
    if not message or not message.strip():
        return False, "Message cannot be empty"

    if len(message) > MAX_MESSAGE_LENGTH:
        return False, f"Message exceeds maximum length of {MAX_MESSAGE_LENGTH}"

    # Check for potential injection patterns
    injection_patterns = [
        r"(?i)ignore\s+(previous|all)\s+instructions",
        r"(?i)system\s*:\s*",
        r"(?i)assistant\s*:\s*",
    ]

    for pattern in injection_patterns:
        if re.search(pattern, message):
            return False, "Invalid message content"

    return True, None

def sanitize_output(response: str) -> str:
    """Sanitize LLM output before returning to user"""
    # Remove any accidentally leaked system prompts
    response = re.sub(r"(?i)<\|system\|>.*?<\|end\|>", "", response)
    return response.strip()
```

### 11.2 Rate Limiting

```python
# chatbot_service/rate_limit.py
from collections import defaultdict
from datetime import datetime, timedelta

class RateLimiter:
    def __init__(self, requests_per_minute: int = 10):
        self.requests_per_minute = requests_per_minute
        self.user_requests = defaultdict(list)

    def is_allowed(self, user_id: str) -> bool:
        """Check if user can make another request"""
        now = datetime.utcnow()
        minute_ago = now - timedelta(minutes=1)

        # Clean old requests
        self.user_requests[user_id] = [
            t for t in self.user_requests[user_id]
            if t > minute_ago
        ]

        # Check limit
        if len(self.user_requests[user_id]) >= self.requests_per_minute:
            return False

        self.user_requests[user_id].append(now)
        return True
```

---

## 12. Testing

### 12.1 Unit Tests

```python
# tests/test_agent.py
import pytest
from unittest.mock import Mock, patch, AsyncMock
from chatbot_service.agent import CVAssistantAgent, AgentConfig

@pytest.fixture
def mock_config():
    return AgentConfig(
        ollama_host="localhost",
        ollama_port=11434,
        chroma_host="localhost",
        chroma_port=8000
    )

@pytest.fixture
def agent(mock_config):
    with patch('chatbot_service.agent.Ollama'):
        with patch('chatbot_service.agent.chromadb.HttpClient'):
            return CVAssistantAgent(mock_config)

@pytest.mark.asyncio
async def test_chat_returns_response(agent):
    """Test that chat returns a valid response"""
    with patch.object(agent, '_run_agent') as mock_run:
        mock_run.return_value = Mock(response="Hello! How can I help?")

        result = await agent.chat("Hello", "user_123")

        assert "response" in result
        assert result["thread_id"] is not None

@pytest.mark.asyncio
async def test_chat_with_existing_thread(agent):
    """Test continuing conversation in existing thread"""
    thread_id = "existing_thread_123"

    with patch.object(agent, '_run_agent') as mock_run:
        mock_run.return_value = Mock(response="Sure, I remember!")

        result = await agent.chat("Remember me?", "user_123", thread_id)

        assert result["thread_id"] == thread_id
```

---

*Document created as part of CV Assistant Research Project documentation.*
