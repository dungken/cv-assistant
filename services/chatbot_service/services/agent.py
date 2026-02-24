import logging
import requests
from datetime import datetime
from typing import List, Dict, Tuple
import chromadb
from fastapi import HTTPException

from services.chatbot_service.models.schemas import Source
from shared.models.base_models import Source as SharedSource

logger = logging.getLogger(__name__)

class ChatService:
    """Orchestrates RAG, conversation history, and LLM generation."""
    
    SYSTEM_PROMPT = """You are CV Assistant, an AI-powered career guidance chatbot.

Your capabilities:
1. Answer questions about CV writing, job applications, and career development
2. Provide advice based on O*NET occupational data
3. Help users understand skill requirements for different jobs
4. Give actionable tips for improving CVs

Guidelines:
- Be concise and helpful
- Use bullet points for lists
- If you don't know something, admit it
- Always be encouraging and professional
- When referencing job data, mention the source

Current context from knowledge base:
{context}

Conversation history:
{history}
"""

    def __init__(self, ollama_url: str, model_name: str, collections: Dict[str, chromadb.Collection]):
        self.ollama_url = ollama_url
        self.model_name = model_name
        self.collections = collections
        self.history: Dict[str, List[Dict]] = {}

    def get_history_str(self, session_id: str, max_msgs: int = 10) -> str:
        """Format history for prompt."""
        msgs = self.history.get(session_id, [])
        if not msgs:
            return "[No previous conversation]"
        
        formatted = []
        for msg in msgs[-max_msgs:]:
            role = "User" if msg["role"] == "user" else "Assistant"
            formatted.append(f"{role}: {msg['content'][:200]}")
        return "\n".join(formatted)

    def add_msg(self, session_id: str, role: str, content: str):
        """Save message to local history."""
        if session_id not in self.history:
            self.history[session_id] = []
        self.history[session_id].append({
            "role": role, 
            "content": content, 
            "timestamp": datetime.now().isoformat()
        })

    def retrieve_context(self, query: str) -> Tuple[str, List[SharedSource]]:
        """Query ChromaDB for relevant info."""
        parts = []
        sources = []
        
        # Job search
        coll_jobs = self.collections.get("onet_jobs")
        if coll_jobs:
            res = coll_jobs.query(query_texts=[query], n_results=2)
            if res["documents"] and res["documents"][0]:
                parts.append("## Jobs Found:")
                for i, doc in enumerate(res["documents"][0]):
                    title = res["metadatas"][0][i].get("title", "Unknown")
                    parts.append(f"- {title}: {doc[:200]}...")
                    sources.append(SharedSource(title=title, type="job", relevance=0.8))
        
        return "\n".join(parts) if parts else "[No info found]", sources

    def generate_response(self, message: str, context: str, history: str) -> str:
        """Call Ollama for completion."""
        system = self.SYSTEM_PROMPT.format(context=context, history=history)
        try:
            payload = {
                "model": self.model_name,
                "prompt": message,
                "system": system,
                "stream": False
            }
            r = requests.post(f"{self.ollama_url}/api/generate", json=payload, timeout=60)
            r.raise_for_status()
            return r.json().get("response", "")
        except Exception as e:
            logger.error(f"LLM Error: {e}")
            raise HTTPException(status_code=500, detail="AI Service Error")
