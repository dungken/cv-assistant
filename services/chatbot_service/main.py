import warnings
warnings.filterwarnings("ignore", category=UserWarning, module="pydantic")
import sys
import re
import json
from pathlib import Path
import requests as req
from typing import List, Optional, Dict
from datetime import datetime
import uvicorn

# Add core to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from fastapi import FastAPI, Depends, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware

from services.chatbot_service.config import settings
from services.chatbot_service.models.schemas import (
    ChatRequest, ChatResponse, SessionHistory, CollectorResponse,
    CVRewriteRequest, CVRewriteResponse, CVGenerateRequest, CVOptimizeResponse,
    OptimizationSuggestion, OptimizationResponse,
    UserMemory, MemoryUpdateRequest, TitleRequest, TitleResponse,
    CVSuggestRequest, CVSuggestResponse, BulletSuggestion,
    CVValidateRequest, CVValidateResponse, CVDraftData
)
from services.chatbot_service.services.agent import ChatService
from services.chatbot_service.services.optimization import OptimizationService
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
_opt_service = None

def get_chat_service() -> ChatService:
    """DI for ChatService."""
    global _chat_service
    if _chat_service is None:
        try:
            logger.info(f"Initializing ChatService. Groq Enabled: {settings.use_groq}, Model: {settings.groq_model}")
            collections = {
                "onet_jobs": get_collection(COLLECTION_JOBS),
                "cv_guides": get_collection(COLLECTION_GUIDES),
                "onet_skills": get_collection("onet_skills")
            }

            _chat_service = ChatService(
                ollama_url=settings.ollama_url,
                ner_url=settings.ner_url,
                model_name=settings.model_name,
                collections=collections,
                skill_service_url=settings.skill_service_url,
                career_service_url=settings.career_service_url,
                groq_api_key=settings.groq_api_key,
                groq_model=settings.groq_model,
                use_groq=settings.use_groq,
                memory_dir=settings.memory_dir,
            )

        except Exception as e:
            logger.error(f"Init Error: {e}")
            raise HTTPException(status_code=500, detail="KB not available")
    return _chat_service

def get_optimization_service(chat_service: ChatService = Depends(get_chat_service)) -> OptimizationService:
    """DI for OptimizationService."""
    global _opt_service
    if _opt_service is None:
        _opt_service = OptimizationService(chat_service.get_llm_handler())
    return _opt_service

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest, service: ChatService = Depends(get_chat_service)):
    """API for chat interaction with skill/career-aware context."""
    logger.info(f"Chat req: {request.session_id}, active_tool: {request.active_tool}")

    # 1. Update history
    service.add_msg(request.session_id, "user", request.message)

    # 2. RAG context retrieval
    context, sources = service.retrieve_context(request.message)

    # 3. Enrich with skill/career service intelligence
    entities = []
    try:
        r = req.post(f"{settings.ner_url}/extract",
                     json={"text": request.message, "cv_id": "chat-query"}, timeout=5)
        if r.status_code == 200:
            entities = r.json().get("entities", [])
    except Exception:
        pass

    service_context = service.enrich_with_services(request.message, entities)
    if service_context:
        context = context + "\n" + service_context

    # 4. Build history context
    hist_str = service.get_history_str(request.session_id)

    # 5. LLM generation (US-26: active_tool, US-27: user_id for memory)
    response = service.generate_response(
        request.message,
        context,
        hist_str,
        active_tool=request.active_tool,
        user_id=request.user_id,
        tool_context=request.tool_context
    )

    # 6. Save assistant reply
    service.add_msg(request.session_id, "assistant", response)

    return ChatResponse(
        response=response,
        sources=sources,
        session_id=request.session_id,
        timestamp=datetime.now().isoformat()
    )
    
@app.post("/chat/stream")
def chat_stream(request: ChatRequest, service: ChatService = Depends(get_chat_service)):
    """Streaming API for chat interaction. US-26: supports active_tool context."""
    logger.info(f"Chat stream req: {request.session_id}, active_tool: {request.active_tool}")
    context, _ = service.retrieve_context(request.message)
    entities = []
    service_context = service.enrich_with_services(request.message, entities)
    if service_context:
        context = context + "\n" + service_context
    hist_str = service.get_history_str(request.session_id)
    return StreamingResponse(
        service.generate_chat_stream(
            request.message,
            context,
            hist_str,
            active_tool=request.active_tool,
            user_id=request.user_id,
            tool_context=request.tool_context
        ),
        media_type="text/event-stream"
    )

@app.post("/chat/title", response_model=TitleResponse)
def generate_chat_title(request: TitleRequest, service: ChatService = Depends(get_chat_service)):
    """Generate a concise title for a chat session from first-turn context."""
    title = service.generate_chat_title(
        user_message=request.user_message,
        assistant_message=request.assistant_message,
        active_tool=request.active_tool,
        user_id=request.user_id,
        tool_context=request.tool_context
    )
    return TitleResponse(title=title)

@app.post("/chat/collector/stream")
def chat_collector_stream(request: ChatRequest, service: ChatService = Depends(get_chat_service)):
    """Streaming API for specialized CV information collection flow."""
    return StreamingResponse(
        service.generate_collector_stream(
            request.session_id,
            request.message,
            request.current_step or 1,
            request.cv_data,
            request.user_id
        ),
        media_type="text/event-stream"
    )

@app.post("/chat/collector", response_model=CollectorResponse)
def chat_collector(request: ChatRequest, service: ChatService = Depends(get_chat_service)):
    """API for specialized CV information collection flow."""
    logger.info(f"Collector req: {request.session_id}")
    response, step, cv_data = service.collect_cv_info(
        request.session_id,
        request.message,
        request.current_step or 1,
        request.cv_data
    )
    return CollectorResponse(
        response=response,
        current_step=step,
        cv_data=cv_data,
        session_id=request.session_id,
        timestamp=datetime.now().isoformat()
    )

@app.get("/history/{session_id}", response_model=SessionHistory)
def get_history(session_id: str, service: ChatService = Depends(get_chat_service)):
    msgs = service.history.get(session_id, [])
    return SessionHistory(session_id=session_id, messages=msgs, count=len(msgs))

@app.post("/cv/rewrite", response_model=CVRewriteResponse)
def rewrite_section(request: CVRewriteRequest, service: ChatService = Depends(get_chat_service)):
    """AI Rewrite of bullet points into STAR format."""
    rewritten = service.cv_generator.rewrite_bullet_points(
        request.title, request.context, request.raw_points
    )
    return CVRewriteResponse(rewritten_points=rewritten)

@app.post("/cv/generate", response_model=CVOptimizeResponse)
def generate_cv(request: CVGenerateRequest, service: ChatService = Depends(get_chat_service)):
    """Full CV optimization: section ordering + ATS analysis (legacy)."""
    new_order = service.cv_generator.suggest_section_order(request.cv_data)
    request.cv_data.section_order = new_order
    ats_result = None
    if request.jd_text:
        ats_result_obj = service.cv_generator.optimize_ats(request.cv_data, request.jd_text)
        ats_result = ats_result_obj.dict()
    return CVOptimizeResponse(
        optimized_cv=request.cv_data,
        ats_result=ats_result
    )

@app.post("/cv/optimize-suggestions", response_model=OptimizationResponse)
def get_optimization_suggestions(
    request: CVGenerateRequest,
    service: OptimizationService = Depends(get_optimization_service)
):
    """US-17: Get explainable AI suggestions for CV improvement."""
    try:
        logger.info(f"Generating optimization suggestions for CV. JD length: {len(request.jd_text) if request.jd_text else 0}")
        
        # 1. Get ATS score from skill_service
        skill_svc_url = settings.skill_service_url
        logger.info(f"Calling skill service at: {skill_svc_url}/cv/ats-score")
        
        try:
            ats_resp = req.post(f"{skill_svc_url}/cv/ats-score", json={
                "cv_data": request.cv_data.dict(),
                "jd_text": request.jd_text
            }, timeout=15)
            
            if ats_resp.status_code != 200:
                logger.error(f"Skill service returned error {ats_resp.status_code}: {ats_resp.text}")
                raise HTTPException(status_code=ats_resp.status_code, detail=f"Skill service error: {ats_resp.text}")
            
            ats_result = ats_resp.json()
            logger.info("Successfully received ATS score from skill service")
            
        except req.exceptions.RequestException as e:
            logger.error(f"Connection error to skill service: {e}")
            raise HTTPException(status_code=503, detail="Skill service connection failed")
        
        # 2. Generate suggestions using LLM
        logger.info("Generating LLM suggestions...")
        suggestions = service.get_suggestions(request.cv_data, ats_result, request.jd_text)
        logger.info(f"Generated {len(suggestions)} suggestions")
        
        return OptimizationResponse(
            suggestions=suggestions,
            ats_score=ats_result.get("total_score", 0),
            breakdown=ats_result.get("breakdown", {})
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Critical error in optimization: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal Optimization Error: {str(e)}")


# ─── US-27: User Memory CRUD ─────────────────────────────────────────────────

@app.get("/memory/{user_id}", response_model=UserMemory)
def get_memory(user_id: str, service: ChatService = Depends(get_chat_service)):
    """Get user memory profile."""
    if not service.memory_service:
        raise HTTPException(status_code=503, detail="Memory service not available")
    return service.memory_service.load(user_id)

@app.put("/memory/{user_id}", response_model=UserMemory)
def update_memory(user_id: str, body: MemoryUpdateRequest, service: ChatService = Depends(get_chat_service)):
    """Update user memory fields."""
    if not service.memory_service:
        raise HTTPException(status_code=503, detail="Memory service not available")
    updates = body.dict(exclude_none=True)
    return service.memory_service.update_fields(user_id, updates)

@app.delete("/memory/{user_id}/{field}")
def delete_memory_field(user_id: str, field: str, service: ChatService = Depends(get_chat_service)):
    """Delete a specific memory field."""
    if not service.memory_service:
        raise HTTPException(status_code=503, detail="Memory service not available")
    memory = service.memory_service.delete_field(user_id, field)
    return {"status": "ok", "memory": memory.dict()}

@app.delete("/memory/{user_id}")
def delete_all_memory(user_id: str, service: ChatService = Depends(get_chat_service)):
    """Delete all memory for a user."""
    if not service.memory_service:
        raise HTTPException(status_code=503, detail="Memory service not available")
    service.memory_service.delete_all(user_id)
    return {"status": "ok"}


# ─── US-29: CV Builder Optimization ──────────────────────────────────────────

# In-memory draft store (keyed by user_id). Survives restarts if memory_dir used.
_draft_store: Dict[str, dict] = {}

@app.post("/cv-builder/suggest", response_model=CVSuggestResponse)
def suggest_cv_content(request: CVSuggestRequest, service: ChatService = Depends(get_chat_service)):
    """T2: Generate 3-5 AI bullet point suggestions in STAR format."""
    logger.info(f"CV suggest req: job={request.job_title}, section={request.section}")

    section_instruction = {
        "experience": "experience bullet points for a CV experience section",
        "summary": "a professional summary paragraph",
        "projects": "project description bullet points",
    }.get(request.section, "bullet points")

    system_prompt = f"""You are a professional CV writing expert specializing in ATS-optimized resumes.
Generate exactly 3 STAR-format {section_instruction} based on the user's raw description.

Rules:
- Use strong action verbs (Developed, Optimized, Led, Implemented, Reduced...)
- Include specific metrics/numbers where plausible (e.g. 10K+ requests/min, 40% faster)
- Each bullet should be 1-2 sentences, under 20 words
- Make bullets ATS-friendly with relevant technical keywords
- Write in English

Return ONLY a valid JSON array, no markdown, no extra text:
[
  {{
    "id": 1,
    "bullet": "...",
    "star_format": {{"situation": "...", "task": "...", "action": "...", "result": "..."}},
    "confidence": 0.85
  }}
]"""

    user_msg = f"Job Title: {request.job_title}\nCompany: {request.company or 'N/A'}\nDuration: {request.duration or 'N/A'}\nRaw description: {request.raw_input}"

    try:
        raw = service._call_llm([{"role": "user", "content": user_msg}], system_prompt=system_prompt)
        # Strip markdown code fences if present
        raw = raw.strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        parsed = json.loads(raw.strip())
        suggestions = [BulletSuggestion(**item) for item in parsed[:5]]
    except Exception as e:
        logger.error(f"CV suggest LLM error: {e}")
        suggestions = [
            BulletSuggestion(
                id=1,
                bullet=f"Contributed to key {request.section} responsibilities at {request.company or 'the company'} as {request.job_title}",
                star_format={"situation": "Team needed results", "task": "Deliver assigned work", "action": "Executed tasks", "result": "Positive outcome"},
                confidence=0.5
            )
        ]

    return CVSuggestResponse(
        job_title=request.job_title,
        company=request.company,
        duration=request.duration,
        raw_input=request.raw_input,
        suggestions=suggestions
    )


@app.post("/cv-builder/validate", response_model=CVValidateResponse)
def validate_cv_field(request: CVValidateRequest):
    """T4: Validate a single CV field and return error/warning if invalid."""
    value = request.value.strip()
    error = None
    warning = None

    if request.field_type == "email":
        if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", value):
            error = "Email không hợp lệ. Ví dụ: name@email.com"
    elif request.field_type == "phone":
        digits = re.sub(r"[\s\-\(\)\+]", "", value)
        if not re.match(r"^[0-9]{9,12}$", digits):
            error = "Số điện thoại không hợp lệ. Ví dụ: 0901234567"
    elif request.field_type == "date":
        if not re.match(r"^(19|20)\d{2}(-(0[1-9]|1[0-2])(-([0-2]\d|3[01]))?)?$", value):
            error = "Ngày không hợp lệ. Dùng định dạng YYYY hoặc YYYY-MM"
    elif request.field_type == "url":
        if value and not re.match(r"^https?://", value):
            warning = "URL nên bắt đầu bằng http:// hoặc https://"
    elif request.field_type == "text":
        if len(value) < 2:
            error = f"Trường '{request.field}' quá ngắn"
        elif len(value) > 500:
            warning = f"Trường '{request.field}' quá dài (>{500} ký tự)"

    return CVValidateResponse(
        field=request.field,
        is_valid=error is None,
        error=error,
        warning=warning
    )


@app.put("/cv-builder/draft/{user_id}", response_model=CVDraftData)
def save_draft(user_id: str, draft: CVDraftData):
    """T5: Auto-save CV builder draft for a user."""
    _draft_store[user_id] = draft.dict()
    # Also persist to disk if memory_dir is available
    try:
        draft_path = Path(settings.memory_dir) / f"cv_draft_{user_id}.json"
        draft_path.write_text(json.dumps(_draft_store[user_id], ensure_ascii=False))
    except Exception:
        pass
    logger.info(f"Draft saved for user: {user_id}, step={draft.current_step}")
    return draft


@app.get("/cv-builder/draft/{user_id}", response_model=CVDraftData)
def get_draft(user_id: str):
    """T5: Get CV builder draft for a user."""
    if user_id in _draft_store:
        return CVDraftData(**_draft_store[user_id])
    # Try loading from disk
    try:
        draft_path = Path(settings.memory_dir) / f"cv_draft_{user_id}.json"
        if draft_path.exists():
            data = json.loads(draft_path.read_text())
            _draft_store[user_id] = data
            return CVDraftData(**data)
    except Exception:
        pass
    from fastapi import HTTPException
    raise HTTPException(status_code=404, detail="No draft found")


@app.delete("/cv-builder/draft/{user_id}")
def delete_draft(user_id: str):
    """T5: Delete CV builder draft for a user."""
    _draft_store.pop(user_id, None)
    try:
        draft_path = Path(settings.memory_dir) / f"cv_draft_{user_id}.json"
        draft_path.unlink(missing_ok=True)
    except Exception:
        pass
    return {"status": "ok"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=settings.service_port)
