import sys
from pathlib import Path

# Add core to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from datetime import datetime

from services.chatbot_service.config import settings
from services.chatbot_service.models.schemas import ChatRequest, ChatResponse, SessionHistory
from services.chatbot_service.services.agent import ChatService
from shared.db.chroma_client import get_collection
from shared.utils.logging_config import setup_logging
from shared.constants import COLLECTION_JOBS, COLLECTION_GUIDES

# Logger
logger = setup_logging(settings.service_name)

app = FastAPI(title="Chatbot Service", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global instance
_chat_service = None

def get_chat_service() -> ChatService:
    """DI for ChatService."""
    global _chat_service
    if _chat_service is None:
        try:
            collections = {
                "onet_jobs": get_collection(COLLECTION_JOBS),
                "cv_guides": get_collection(COLLECTION_GUIDES)
            }
            _chat_service = ChatService(
                ollama_url=settings.ollama_url,
                ner_url=settings.ner_url,
                model_name=settings.model_name,
                collections=collections
            )

        except Exception as e:
            logger.error(f"Init Error: {e}")
            raise HTTPException(status_code=500, detail="KB not available")
    return _chat_service

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest, service: ChatService = Depends(get_chat_service)):
    """API for chat interaction."""
    logger.info(f"Chat req: {request.session_id}")
    
    # 1. Update history
    service.add_msg(request.session_id, "user", request.message)
    
    # 2. RAG
    context, sources = service.retrieve_context(request.message)
    
    # 3. Prompt context
    hist_str = service.get_history_str(request.session_id)
    
    # 4. LLM
    response = service.generate_response(request.message, context, hist_str)
    
    # 5. Save assistant reply
    service.add_msg(request.session_id, "assistant", response)
    
    return ChatResponse(
        response=response,
        sources=sources,
        session_id=request.session_id,
        timestamp=datetime.now().isoformat()
    )

@app.get("/history/{session_id}", response_model=SessionHistory)
def get_history(session_id: str, service: ChatService = Depends(get_chat_service)):
    msgs = service.history.get(session_id, [])
    return SessionHistory(session_id=session_id, messages=msgs, count=len(msgs))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=settings.service_port)
