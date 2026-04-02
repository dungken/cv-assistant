import logging
import requests
from datetime import datetime
from typing import List, Dict, Tuple
import chromadb
from fastapi import HTTPException

from services.chatbot_service.models.schemas import Source
from shared.models.base_models import Source as SharedSource

logger = logging.getLogger(__name__)

from services.chatbot_service.services.normalizer import SkillNormalizer

class ChatService:
    """Orchestrates RAG, conversation history, and LLM generation.
    Enhanced with skill matching and career path context integration."""

    SYSTEM_PROMPT = """You are CV Assistant, an AI-powered career guidance chatbot for IT professionals.

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
                 skill_service_url: str = None, career_service_url: str = None):
        self.ollama_url = ollama_url
        self.ner_url = ner_url
        self.model_name = model_name
        self.collections = collections
        self.skill_service_url = skill_service_url
        self.career_service_url = career_service_url
        self.history: Dict[str, List[Dict[str, str]]] = {}

        # Initialize Normalizer
        skill_coll = collections.get("onet_skills")
        self.normalizer = SkillNormalizer(skill_coll) if skill_coll else None



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

    def generate_response(self, message: str, context: str, history: str) -> str:
        """Call Ollama for completion."""
        # 0. Basic Greeting Detection for Mock Mode
        greetings = ["hi", "hello", "xin chào", "chào", "hey", "greetings"]
        is_greeting = any(g in message.lower() for g in greetings) and len(message.split()) < 4

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
            if is_greeting:
                return "Chào bạn! Tôi là CV Assistant. Tôi có thể giúp gì cho bạn về định hướng nghề nghiệp hoặc chỉnh sửa CV hôm nay?"
            
            fallback_response = f"[Chatbot running in mock mode. LLM currently unavailable.]\n\nI found the following contexts in my Knowledge Base based on your query:\n\n{context}"
            return fallback_response
