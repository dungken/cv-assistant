import logging
import requests
import json
import time
from datetime import datetime
from typing import List, Dict, Tuple, Iterator, Optional
import chromadb
from fastapi import HTTPException

from services.chatbot_service.models.schemas import Source
from shared.models.base_models import Source as SharedSource

logger = logging.getLogger(__name__)

from services.chatbot_service.services.normalizer import SkillNormalizer
from services.chatbot_service.services.collector_manager import CollectorManager, CollectorStep
from services.chatbot_service.services.cv_generator import CVGeneratorService
from services.chatbot_service.services.memory_service import MemoryService
from shared.models.cv_models import CVData

class ChatService:
    """Orchestrates RAG, conversation history, and LLM generation.
    Enhanced with skill matching and career path context integration."""

    # US-26: Context prompts injected when a specific tool is active
    TOOL_CONTEXT_PROMPTS = {
        "match": """## Active Tool: Skill Match (Ma trận kỹ năng)
The user currently has the Skill Match tool open on the right panel.
This tool compares CV skills against a Job Description to find gaps.
It needs: (1) the user's current skills/tech stack, (2) a target job title, (3) a Job Description text.
Your job: Proactively ask what position they're targeting and what technologies they currently use.
If they already shared some info, confirm it and guide them to fill in the remaining fields in the tool.
Suggest relevant skills for their target role. Keep responses focused on skill matching.""",

        "career": """## Active Tool: Career Path (Lộ trình sự nghiệp)
The user currently has the Career Path tool open on the right panel.
This tool predicts career trajectories based on current role, target role, and skills.
It needs: (1) current job title/role, (2) desired target role, (3) current skill set.
Your job: Ask about their current position, where they want to be in 3-5 years, and their key skills.
Provide encouraging guidance about career transitions. Keep responses focused on career planning.""",

        "upload": """## Active Tool: CV Upload (Tải CV lên)
The user currently has the CV Upload/Data Ingestion tool open on the right panel.
This tool parses uploaded CV files (PDF/DOCX) and extracts structured data using NER.
Your job: Ask what they intend to do after uploading — apply for a specific job? improve their CV? compare with a JD?
If they've already uploaded, suggest next steps: run Skill Match against a JD, check ATS score, or use the CV Builder to enhance it.
Keep responses focused on CV analysis and improvement.""",

        "ats": """## Active Tool: ATS Score (Chấm điểm ATS)
The user currently has the ATS scoring tool open.
This tool compares CV content against a target Job Description.
It needs: (1) CV data, (2) JD text or job posting link.
Your job: Ask for JD text/link if missing, then guide user to run scoring.
After scoring, explain high-priority gaps and suggest next action.
Keep responses focused on ATS optimization and keyword relevance.""",

        "jd": """## Active Tool: JD Analysis (Phân tích mô tả công việc)
The user currently has the JD Analysis tool open on the right panel.
This tool parses Job Descriptions to extract requirements, skills, and qualifications.
It supports: file upload, paste text, or URL input.
Your job: Ask if they have a specific job posting they want to analyze.
After parsing, suggest comparing the JD results with their CV using Skill Match.
Keep responses focused on understanding job requirements.""",

        "graph": """## Active Tool: Knowledge Graph (Biểu đồ kỹ năng)
The user currently has the Skill Knowledge Graph visualization open on the right panel.
This tool shows relationships between IT skills (requires, related_to, leads_to).
Your job: Ask what skill area they want to explore or what technology they're curious about.
Help them understand skill relationships and learning paths between technologies.
Keep responses focused on skill ecosystems and learning roadmaps.""",

        "market": """## Active Tool: Market Dashboard (Thị trường việc làm)
The user currently has the Market Intelligence dashboard open on the right panel.
This tool shows job market trends: top skills, salary data, industry distribution.
Your job: Ask what industry or role they're interested in for market insights.
Help interpret trends and connect market data to their career decisions.
Keep responses focused on market analysis and actionable insights.""",
    }

    SYSTEM_PROMPT = """You are Resume Assistant, an AI-powered career guidance chatbot for IT professionals.

Your capabilities:
1. Answer questions about CV writing, job applications, and career development
2. Provide advice based on O*NET occupational data and IT industry knowledge
3. Help users understand skill requirements for different IT jobs
4. Analyze skill gaps and suggest learning paths
5. Recommend career trajectories based on current skills
6. Give actionable tips for improving CVs for ATS (Applicant Tracking Systems)

Guidelines:
- Be concise and helpful
- Use bullet points for lists
- If you don't know something, admit it
- Always be encouraging and professional
- When referencing job data, mention it comes from O*NET
- For skill-related questions, explain relationships between technologies
- For career path questions, consider both ambitious and conservative options

Current context from knowledge base:
{context}

Conversation history:
{history}
"""

    def __init__(self, ollama_url: str, ner_url: str, model_name: str,
                 collections: Dict[str, chromadb.Collection],
                 skill_service_url: str = None, career_service_url: str = None,
                 groq_api_key: str = None, groq_model: str = None, use_groq: bool = False,
                 memory_dir: str = None):
        self.ollama_url = ollama_url
        self.ner_url = ner_url
        self.ollama_model = model_name
        self.collections = collections
        self.skill_service_url = skill_service_url
        self.career_service_url = career_service_url

        # Groq Config
        self.groq_api_key = groq_api_key
        self.groq_model = groq_model
        self.use_groq = use_groq and bool(groq_api_key)

        self.history: Dict[str, List[Dict[str, str]]] = {}

        # Initialize Normalizer
        skill_coll = collections.get("onet_skills")
        self.normalizer = SkillNormalizer(skill_coll) if skill_coll else None
        self.collector_manager = CollectorManager()
        self.cv_generator = CVGeneratorService(self._call_llm)

        # US-27: Memory service
        self.memory_service = MemoryService(memory_dir) if memory_dir else None

    def get_llm_handler(self):
        """Expose the internal LLM caller for specialized services."""
        return self._call_llm




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
        """Query ChromaDB for relevant info, enriched by NER."""
        # 0. Fast path for greetings
        greetings = ["hi", "hello", "xin chào", "chào", "hey", "greetings"]
        if any(g in query.lower() for g in greetings) and len(query.split()) < 4:
            return "[Greeting detected, no context needed]", []

        parts = []
        sources = []
        
        # 1. Extract Entities from Query
        entities = []
        try:
            r = requests.post(f"{self.ner_url}/extract", json={"text": query, "cv_id": "user-query"}, timeout=5)
            if r.status_code == 200:
                entities = r.json().get("entities", [])
                logger.info(f"Extracted entities from query: {entities}")
        except Exception as e:
            logger.warning(f"NER Service unavailable for query enrichment: {e}")

            # 2. Query Job Collection
        coll_jobs = self.collections.get("onet_jobs")
        if coll_jobs:
            # Enriched query if skills or job titles are found
            search_query = query
            skills = [e.get('text') for e in entities if e.get('type') == 'SKILL']
            job_titles = [e.get('text') for e in entities if e.get('type') == 'JOB_TITLE']
            
            # Prioritize JOB_TITLE in searching
            if job_titles:
                search_query = " ".join(job_titles) + " " + query
                logger.info(f"Enriched search query (job titles): {search_query}")
                
            if skills and self.normalizer:
                normalized_skills = self.normalizer.normalize_list(skills)
                canonical_names = [n['canonical'] for n in normalized_skills]
                if canonical_names:
                    search_query += " " + " ".join(canonical_names)
                logger.info(f"Enriched search query (normalized skills): {search_query}")
            elif skills:
                search_query += " " + " ".join(skills)
                logger.info(f"Enriched search query (raw skills): {search_query}")

            res = coll_jobs.query(query_texts=[search_query], n_results=2)
            if res["documents"] and res["documents"][0]:
                relevant_found = False
                for i, doc in enumerate(res["documents"][0]):
                    distance = res["distances"][0][i]
                    # Simple similarity score: higher is better
                    similarity = 1 - distance 
                    
                    if similarity > 0.3: # Threshold for job relevance
                        if not relevant_found:
                            parts.append("## Relevant Occupations & Skills:")
                            relevant_found = True
                        title = res["metadatas"][0][i].get("title", "Unknown")
                        parts.append(f"- {title}: {doc[:300]}...")
                        sources.append(SharedSource(title=title, type="job", relevance=float(similarity)))
        
        # 3. Query Advice Collection
        coll_advice = self.collections.get("cv_guides")

        if coll_advice:
            res = coll_advice.query(query_texts=[query], n_results=1)
            if res["documents"] and res["documents"][0]:
                distance = res["distances"][0][0]
                similarity = 1 - distance
                
                if similarity > 0.3: # Threshold for advice relevance
                    parts.append("\n## Writing Advice:")
                    parts.append(res["documents"][0][0][:400] + "...")
                    title = res["metadatas"][0][0].get("title", "Advice")
                    sources.append(SharedSource(title=title, type="guide", relevance=float(similarity)))

        return "\n".join(parts) if parts else "[No specific info found in KB, using general knowledge]", sources


    def enrich_with_services(self, query: str, entities: list) -> str:
        """Call skill/career services to enrich context for skill or career questions."""
        enrichments = []

        # Detect if query is about skills/matching
        skills = [e.get("text") for e in entities if e.get("type") == "SKILL"]
        job_titles = [e.get("text") for e in entities if e.get("type") == "JOB_TITLE"]

        skill_keywords = ["skill", "match", "require", "need", "learn", "gap", "kỹ năng"]
        career_keywords = ["career", "path", "transition", "grow", "promotion", "lộ trình", "nghề"]

        query_lower = query.lower()
        is_skill_query = any(k in query_lower for k in skill_keywords)
        is_career_query = any(k in query_lower for k in career_keywords)

        # Call Skill Service for skill-related queries
        if is_skill_query and skills and self.skill_service_url:
            try:
                resp = requests.post(
                    f"{self.skill_service_url}/match",
                    json={"cv_skills": skills, "jd_text": query},
                    timeout=10
                )
                if resp.status_code == 200:
                    data = resp.json()
                    score = data.get("overall_score", 0)
                    missing = data.get("missing_skills", [])
                    gap_info = data.get("skill_gap_explanation", {})

                    enrichments.append(f"\n## Skill Analysis (from Matcher):")
                    enrichments.append(f"- Match score: {score}%")
                    if missing:
                        enrichments.append(f"- Missing skills: {', '.join(missing[:5])}")
                    if gap_info.get("summary"):
                        enrichments.append(f"- {gap_info['summary']}")
            except Exception as e:
                logger.warning(f"Skill service unavailable: {e}")

        # Call Career Service for career-related queries
        if is_career_query and (job_titles or skills) and self.career_service_url:
            try:
                current_role = job_titles[0] if job_titles else "Software Developer"
                resp = requests.post(
                    f"{self.career_service_url}/recommend",
                    json={
                        "current_role": current_role,
                        "target_role": None,
                        "current_skills": skills[:10]
                    },
                    timeout=10
                )
                if resp.status_code == 200:
                    data = resp.json()
                    target = data.get("target_role", "")
                    level = data.get("experience_level", "")
                    gap = data.get("skill_gap", {})

                    enrichments.append(f"\n## Career Intelligence:")
                    enrichments.append(f"- Current level: {level}")
                    enrichments.append(f"- Suggested target: {target}")
                    if gap.get("missing"):
                        enrichments.append(f"- Skills to develop: {', '.join(gap['missing'][:5])}")
                    if gap.get("readiness_score"):
                        enrichments.append(f"- Readiness: {gap['readiness_score']}%")
            except Exception as e:
                logger.warning(f"Career service unavailable: {e}")

        return "\n".join(enrichments) if enrichments else ""

    def _call_llm(self, messages: List[Dict[str, str]], system_prompt: str = None) -> str:
        """Unified method to call LLM (Groq or Ollama)."""
        
        # 1. Try Groq if enabled
        if self.use_groq and self.groq_api_key:
            try:
                logger.info(f"Calling Groq API with model: {self.groq_model}")
                # Format for OpenAI-compatible Groq API
                groq_messages = []
                if system_prompt:
                    groq_messages.append({"role": "system", "content": system_prompt})
                groq_messages.extend(messages)
                
                payload = {
                    "model": self.groq_model,
                    "messages": groq_messages,
                    "temperature": 0.2, # Conservative for CV data
                    "stream": False
                }
                headers = {
                    "Authorization": f"Bearer {self.groq_api_key}",
                    "Content-Type": "application/json"
                }
                
                r = requests.post("https://api.groq.com/openai/v1/chat/completions", 
                                 json=payload, headers=headers, timeout=30)
                r.raise_for_status()
                return r.json().get("choices", [{}])[0].get("message", {}).get("content", "")
            except Exception as e:
                logger.error(f"Groq API Error: {e}. Falling back to Ollama.")
        
        # 2. Fallback to Ollama
        try:
            # Check if messages have roles or it's a raw prompt (legacy/generate)
            # /api/chat expects messages with roles
            if any("role" in m for m in messages):
                ollama_messages = []
                if system_prompt:
                    ollama_messages.append({"role": "system", "content": system_prompt})
                ollama_messages.extend(messages)
                
                payload = {
                    "model": self.ollama_model,
                    "messages": ollama_messages,
                    "stream": False
                }
                endpoint = f"{self.ollama_url}/api/chat"
                r = requests.post(endpoint, json=payload, timeout=60)
                r.raise_for_status()
                return r.json().get("message", {}).get("content", "")
            else:
                # Legacy /api/generate
                prompt = messages[0]["content"] if messages else ""
                payload = {
                    "model": self.ollama_model,
                    "prompt": prompt,
                    "system": system_prompt,
                    "stream": False
                }
                endpoint = f"{self.ollama_url}/api/generate"
                r = requests.post(endpoint, json=payload, timeout=60)
                r.raise_for_status()
                return r.json().get("response", "")
                
        except Exception as e:
            logger.error(f"Ollama Error: {e}")
            raise e

    def _call_llm_stream(self, messages: List[Dict[str, str]], system_prompt: str = None) -> Iterator[str]:
        """Unified method to call LLM with streaming enabled."""
        
        # 1. Try Groq if enabled
        if self.use_groq and self.groq_api_key:
            try:
                groq_messages = []
                if system_prompt:
                    groq_messages.append({"role": "system", "content": system_prompt})
                groq_messages.extend(messages)
                
                payload = {
                    "model": self.groq_model,
                    "messages": groq_messages,
                    "temperature": 0.2,
                    "stream": True
                }
                headers = {
                    "Authorization": f"Bearer {self.groq_api_key}",
                    "Content-Type": "application/json"
                }
                
                r = requests.post("https://api.groq.com/openai/v1/chat/completions", 
                                 json=payload, headers=headers, stream=True, timeout=30)
                r.raise_for_status()
                
                for line in r.iter_lines():
                    if not line: continue
                    line_str = line.decode('utf-8')
                    if line_str.startswith("data: "):
                        if line_str.strip() == "data: [DONE]": break
                        try:
                            chunk = json.loads(line_str[6:])
                            content = chunk.get("choices", [{}])[0].get("delta", {}).get("content", "")
                            if content: yield content
                        except: continue
                return
            except Exception as e:
                logger.error(f"Groq Stream Error: {e}. Falling back to Ollama.")
        
        # 2. Fallback to Ollama
        try:
            ollama_messages = []
            if system_prompt:
                ollama_messages.append({"role": "system", "content": system_prompt})
            ollama_messages.extend(messages)
            
            payload = {
                "model": self.ollama_model,
                "messages": ollama_messages,
                "stream": True
            }
            endpoint = f"{self.ollama_url}/api/chat"
            r = requests.post(endpoint, json=payload, stream=True, timeout=60)
            r.raise_for_status()
            
            for line in r.iter_lines():
                if not line: continue
                try:
                    chunk = json.loads(line.decode('utf-8'))
                    content = chunk.get("message", {}).get("content", "")
                    if content: yield content
                except: continue
                
        except Exception as e:
            logger.error(f"Ollama Stream Error: {e}")
            raise e

    def _build_system_prompt(
        self,
        context: str,
        history: str,
        active_tool: str = None,
        user_id: str = None,
        tool_context: str = None
    ) -> str:
        """Build system prompt with optional tool context (US-26) and user memory (US-27)."""
        system = self.SYSTEM_PROMPT.format(context=context, history=history)
        # US-26: tool context
        tool_ctx = self.TOOL_CONTEXT_PROMPTS.get(active_tool, "") if active_tool else ""
        if tool_ctx:
            system += f"\n\n{tool_ctx}"
        if tool_context:
            system += (
                "\n\n## Active Tool Data Snapshot (from UI)\n"
                f"{tool_context}\n"
                "Use this as high-priority grounding when answering questions about the active tool."
            )
        # US-27: user memory context
        if user_id and self.memory_service:
            try:
                memory = self.memory_service.load(user_id)
                memory_ctx = self.memory_service.format_for_prompt(memory)
                if memory_ctx:
                    system += f"\n\n{memory_ctx}"
                if active_tool:
                    system += (
                        "\n\nIf required info for the active tool already exists in user memory, "
                        "confirm it briefly and avoid re-asking. Ask only missing fields."
                    )
            except Exception as e:
                logger.warning(f"Failed to load memory for prompt: {e}")
        return system

    def _detect_tool_recommendation(self, message: str) -> Optional[Dict]:
        """US-28: lightweight intent detection for proactive tool routing."""
        m = message.lower()
        mapping = [
            (["thiếu kỹ năng", "skill gap", "match kỹ năng", "khớp kỹ năng"], "match", "🎯 Mở Skill Match ngay",
             [
                 "Upload CV của bạn",
                 "Nhập vị trí mục tiêu",
                 "Paste Job Description",
                 "Nhấn Phân tích"
             ]),
            (["chưa biết sau này làm gì", "career path", "lộ trình", "định hướng nghề nghiệp"], "career", "🗺️ Mở Career Path ngay",
             [
                 "Nhập vai trò hiện tại",
                 "Nhập vai trò mục tiêu",
                 "Thêm kỹ năng hiện có",
                 "Xem lộ trình đề xuất"
             ]),
            (["muốn tạo cv", "tạo cv", "viết cv", "làm cv"], "builder", "🛠️ Mở CV Builder ngay",
             [
                 "Chọn tạo CV mới hoặc upload CV có sẵn",
                 "Điền thông tin từng mục",
                 "Xem preview và chỉnh sửa",
                 "Xuất CV"
             ]),
            (["upload cv", "tải cv", "cv sẵn"], "upload", "📄 Mở CV Upload ngay",
             [
                 "Upload file CV (PDF/DOCX)",
                 "Chờ hệ thống trích xuất dữ liệu",
                 "Kiểm tra dữ liệu đã parse",
                 "Chuyển sang Skill Match hoặc Builder"
             ]),
            (["ats", "chấm điểm cv", "điểm ats", "optimize ats"], "ats", "📊 Mở ATS Score ngay",
             [
                 "Chuẩn bị CV hiện tại",
                 "Dán Job Description hoặc link tin tuyển dụng",
                 "Chạy chấm điểm ATS",
                 "Ưu tiên sửa các mục điểm thấp"
             ]),
        ]
        for keywords, tool, cta, checklist in mapping:
            if any(k in m for k in keywords):
                return {"tool": tool, "cta": cta, "checklist": checklist}
        return None

    def _render_structured_guidance(self, rec: Dict) -> str:
        """Structured directives parsed by frontend for CTA/checklist rendering."""
        checklist = " ; ".join(rec["checklist"])
        return (
            f"\n[TOOL_CTA:{rec['tool']}|{rec['cta']}]\n"
            f"[TOOL_CHECKLIST:{rec['tool']}|{checklist}]\n"
        )

    def _sync_memory_from_cv_data(self, user_id: Optional[str], cv_data: CVData) -> None:
        """US-27: hydrate user memory from extracted CV data in collector flow."""
        if not user_id or not self.memory_service:
            return
        try:
            updates = {
                "display_name": (cv_data.personal_info.full_name or None) if cv_data.personal_info else None,
                "career_profile": {
                    "current_role": (cv_data.personal_info.title or None) if cv_data.personal_info else None,
                    "current_skills": cv_data.skills or [],
                }
            }
            self.memory_service.update_fields(user_id, updates)
        except Exception as e:
            logger.warning(f"Failed syncing memory from CV data: {e}")

    def _remember_response_suggestions(self, user_id: Optional[str], text: str) -> None:
        """US-27: persist lightweight suggestion history for deduplication."""
        if not user_id or not self.memory_service or not text:
            return
        try:
            lines = []
            for raw in text.splitlines():
                line = raw.strip().lstrip("-•*").strip()
                if 12 <= len(line) <= 180 and not line.startswith("[TOOL_"):
                    lines.append(line)
            # Keep only first 3 non-empty lines as suggestion candidates
            for line in lines[:3]:
                self.memory_service.add_suggestion(user_id, "advice", line)
        except Exception as e:
            logger.warning(f"Failed saving suggestion history: {e}")

    def generate_chat_title(
        self,
        user_message: str,
        assistant_message: str,
        active_tool: str = None,
        user_id: str = None,
        tool_context: str = None
    ) -> str:
        """Generate a concise, context-aware chat title from the first exchange."""
        fallback = (user_message or "").strip() or "New Conversation"
        fallback = " ".join(fallback.split())[:52].rstrip() or "New Conversation"

        prompt = (
            "Create ONE concise chat title (max 8 words) for this conversation.\n"
            "Rules:\n"
            "- Keep the user's intent/topic, not greetings.\n"
            "- No quotes, no markdown, no trailing punctuation.\n"
            "- Return title only.\n\n"
            f"Active tool: {active_tool or 'none'}\n"
            f"Tool context: {tool_context or 'none'}\n"
            f"User: {user_message}\n"
            f"Assistant: {assistant_message[:800]}"
        )

        try:
            raw = self._call_llm([{"role": "user", "content": prompt}], None).strip()
            title = raw.splitlines()[0].strip().strip('"').strip("'")
            title = " ".join(title.split())
            if not title:
                return fallback
            if len(title.split()) > 8:
                title = " ".join(title.split()[:8])
            return title[:64].rstrip(" .,!?:;") or fallback
        except Exception as e:
            logger.warning(f"Failed to generate chat title via LLM: {e}")
            return fallback

    def generate_chat_stream(
        self,
        message: str,
        context: str,
        history: str,
        active_tool: str = None,
        user_id: str = None,
        tool_context: str = None
    ) -> Iterator[str]:
        """Generator for general chat streaming. US-26: tool context, US-27: user memory."""
        system = self._build_system_prompt(context, history, active_tool, user_id, tool_context)
        rec = self._detect_tool_recommendation(message) if not active_tool else None

        def stream_with_guidance() -> Iterator[str]:
            full = ""
            for chunk in self._call_llm_stream([{"role": "user", "content": message}], system):
                full += chunk
                yield chunk
            if rec:
                # Render guidance after the answer so CTA/checklist appears naturally at the end.
                yield self._render_structured_guidance(rec)
            self._remember_response_suggestions(user_id, full)

        return stream_with_guidance()

    def generate_collector_stream(self, session_id: str, message: str, current_step: int = 1, cv_data_in: CVData = None, user_id: str = None) -> Iterator[str]:
        """Generator for CV collection streaming. Returns text chunks, then a final metadata chunk."""
        step = current_step
        cv_data = cv_data_in or CVData()
        # Save user msg to history
        self.add_msg(session_id, "user", message)
        
        system_prompt = self.collector_manager.get_system_prompt(step, cv_data)
        
        messages = []
        history = self.history.get(session_id, [])
        for msg in history[-10:]:
            messages.append({"role": msg["role"], "content": msg["content"]})

        full_response = ""
        stream_buffer = ""
        open_tag = "<extracted_data>"
        close_tag = "</extracted_data>"

        def flush_safe_text(buf: str) -> tuple[str, str]:
            """Return (safe_to_emit, remaining_buffer), removing extracted_data blocks safely across chunk boundaries."""
            out = []
            while True:
                start = buf.find(open_tag)
                if start == -1:
                    # Keep possible partial open tag suffix to wait for next chunk
                    keep = 0
                    max_prefix = min(len(buf), len(open_tag) - 1)
                    for k in range(max_prefix, 0, -1):
                        if open_tag.startswith(buf[-k:]):
                            keep = k
                            break
                    if keep:
                        out.append(buf[:-keep])
                        return "".join(out), buf[-keep:]
                    out.append(buf)
                    return "".join(out), ""

                # Emit plain text before tag
                if start > 0:
                    out.append(buf[:start])

                end = buf.find(close_tag, start + len(open_tag))
                if end == -1:
                    # Incomplete tag block, keep from start for next chunk
                    return "".join(out), buf[start:]

                # Remove one complete extracted_data block and continue
                buf = buf[end + len(close_tag):]
        # 1. Stream text chunks
        for chunk in self._call_llm_stream(messages, system_prompt):
            full_response += chunk
            stream_buffer += chunk
            safe, stream_buffer = flush_safe_text(stream_buffer)
            if safe:
                yield safe

        # Flush any remaining non-tag text after stream ends
        if stream_buffer and open_tag not in stream_buffer:
            yield stream_buffer
        
        # 2. After stream ends, perform extraction and return metadata
        extracted = self.collector_manager.extract_json_from_response(full_response)
        if extracted:
            cv_data = self.collector_manager.update_cv_data(cv_data, extracted)
            step = self.collector_manager.get_next_incomplete_step(step, cv_data)
            if extracted.get("step") == 7: step = 7
            self._sync_memory_from_cv_data(user_id, cv_data)

        # Save assistant msg to history (cleaned)
        import re
        clean_history_msg = re.sub(r'<extracted_data>.*?</extracted_data>', '', full_response, flags=re.DOTALL).strip()
        self.add_msg(session_id, "assistant", clean_history_msg)

        # 3. Final chunk: Signal end of text and send metadata in a formatted way
        # Prefix with [METADATA] for frontend detection
        yield f"\n[METADATA]{json.dumps({'step': step, 'cv_data': cv_data.dict()})}"

    def generate_response(
        self,
        message: str,
        context: str,
        history: str,
        active_tool: str = None,
        user_id: str = None,
        tool_context: str = None
    ) -> str:
        """Enhanced response generation. US-26: tool context, US-27: user memory."""
        # 0. Basic Greeting Detection for Mock Mode
        greetings = ["hi", "hello", "xin chào", "chào", "hey", "greetings"]
        is_greeting = any(g in message.lower() for g in greetings) and len(message.split()) < 4

        system = self._build_system_prompt(context, history, active_tool, user_id, tool_context)
        rec = self._detect_tool_recommendation(message) if not active_tool else None
        try:
            # For general chat, we pass as a single user message for now
            # but _call_llm will wrap it with system prompt
            base = self._call_llm([{"role": "user", "content": message}], system)
            self._remember_response_suggestions(user_id, base)
            if rec:
                return base + "\n" + self._render_structured_guidance(rec)
            return base
        except Exception as e:
            if is_greeting:
                return "Chào bạn! Tôi là Resume Assistant. Tôi có thể giúp gì cho bạn về định hướng nghề nghiệp hoặc chỉnh sửa CV hôm nay?"
            
            fallback_response = f"[Chatbot running in mock mode. LLM currently unavailable.]\n\nI found the following contexts in my Knowledge Base based on your query:\n\n{context}"
            return fallback_response

    # --- Collector Mode Methods ---


    def collect_cv_info(self, session_id: str, message: str, current_step: int = 1, cv_data_in: CVData = None) -> Tuple[str, int, CVData]:
        """Main flow for CV Builder mode. State is passed from frontend to avoid auth issues."""
        # 1. Use provided state (frontend passes current state)
        step = current_step
        cv_data = cv_data_in or CVData()

        # 2. Add message to local history
        self.add_msg(session_id, "user", message)

        # 3. Build specialized system prompt
        system_prompt = self.collector_manager.get_system_prompt(step, cv_data)

        # 4. Build messages array from conversation history
        messages = []
        history = self.history.get(session_id, [])
        for msg in history[-10:]:  # Last 10 messages for context
            messages.append({"role": msg["role"], "content": msg["content"]})

        # 5. Call Unified LLM handler
        try:
            ai_response = self._call_llm(messages, system_prompt)

            # 6. Clean response: remove JSON blocks and tags before extraction
            # We assume text is BEFORE the tags usually, but we handle it safely
            response_for_display = ai_response
            
            # Use regex or simple split to get the text portion
            if "<extracted_data>" in response_for_display:
                parts = response_for_display.split("<extracted_data>")
                # Take the longest part that doesn't contain </extracted_data>
                # Or simply take the first part if it's not empty
                text_part = parts[0].strip()
                if not text_part and len(parts) > 1:
                    # If first part is empty, text might be AFTER the closing tag
                    post_tag = parts[1].split("</extracted_data>")
                    if len(post_tag) > 1:
                        text_part = post_tag[1].strip()
                response_for_display = text_part
            
            # Final fallback for other potential markdown tags
            for tag in ["```json", "```"]:
                if tag in response_for_display:
                    response_for_display = response_for_display.split(tag)[0].strip()

            if not response_for_display:
                # If everything failed and it's empty, use the original without tags as fallback
                import re
                response_for_display = re.sub(r'<extracted_data>.*?</extracted_data>', '', ai_response, flags=re.DOTALL).strip()

            # 7. Extract structured data from original response (before cleaning)
            extracted = self.collector_manager.extract_json_from_response(ai_response)

            # Use cleaned response for display
            ai_response = response_for_display

            if extracted:
                # Update CV data with extracted information (Global update)
                cv_data = self.collector_manager.update_cv_data(cv_data, extracted)
                logger.info(f"Data extracted successfully for session {session_id}")

                # Intelligent Step Jumping: Calculate the best next step based on data density
                new_step = self.collector_manager.get_next_incomplete_step(step, cv_data)
                
                # If LLM specifically signaled completion (step 7), honor it
                if extracted.get("step") == 7:
                    step = 7
                else:
                    step = new_step
                    
                logger.info(f"Next intelligent step determined: {step}")
            else:
                # Extraction failed - log for debugging
                logger.warning(f"Failed to extract data at step {step} for session {session_id}")
                logger.debug(f"Raw LLM response was: {ai_response[:200]}...")

            # 8. Save assistant message
            self.add_msg(session_id, "assistant", ai_response)

            return ai_response, step, cv_data

        except Exception as e:
            logger.error(f"Collector LLM Error: {e}", exc_info=True)
            logger.debug(f"Raw ai_response that caused error: {ai_response}")
            return "Đã có lỗi xảy ra khi xử lý thông tin. Vui lòng thử lại sau.", step, cv_data
