"""US-27: Persistent user memory service.

File-based JSON storage for user profile, career goals, skill gaps,
suggestion history, and tone preferences. Injected into LLM prompts
for personalized chatbot responses.
"""
import json
import logging
import os
from datetime import datetime, timedelta
from typing import List, Optional

from services.chatbot_service.models.schemas import (
    CareerProfile, SuggestionRecord, UserMemory
)

logger = logging.getLogger(__name__)

STALENESS_DAYS = 30


class MemoryService:
    def __init__(self, memory_dir: str):
        self.memory_dir = memory_dir
        os.makedirs(memory_dir, exist_ok=True)

    def _path(self, user_id: str) -> str:
        safe_id = user_id.replace("/", "_").replace("\\", "_").replace("..", "_")
        return os.path.join(self.memory_dir, f"{safe_id}.json")

    # ── CRUD ────────────────────────────────────────────────────────────

    def load(self, user_id: str) -> UserMemory:
        path = self._path(user_id)
        if not os.path.exists(path):
            return UserMemory(
                user_id=user_id,
                created_at=datetime.now().isoformat(),
                updated_at=datetime.now().isoformat(),
            )
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return UserMemory(**data)
        except Exception as e:
            logger.error(f"Failed to load memory for {user_id}: {e}")
            return UserMemory(user_id=user_id, created_at=datetime.now().isoformat(), updated_at=datetime.now().isoformat())

    def save(self, memory: UserMemory) -> None:
        memory.updated_at = datetime.now().isoformat()
        path = self._path(memory.user_id)
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(memory.dict(), f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Failed to save memory for {memory.user_id}: {e}")

    def update_fields(self, user_id: str, updates: dict) -> UserMemory:
        memory = self.load(user_id)
        now = datetime.now().isoformat()

        if "display_name" in updates and updates["display_name"] is not None:
            memory.display_name = updates["display_name"]
            memory.field_timestamps["display_name"] = now

        if "tone_preference" in updates and updates["tone_preference"] is not None:
            memory.tone_preference = updates["tone_preference"]
            memory.field_timestamps["tone_preference"] = now

        if "language" in updates and updates["language"] is not None:
            memory.language = updates["language"]
            memory.field_timestamps["language"] = now

        if "career_profile" in updates and updates["career_profile"] is not None:
            cp = updates["career_profile"]
            if isinstance(cp, dict):
                for k, v in cp.items():
                    if v is not None:
                        setattr(memory.career_profile, k, v)
                        memory.field_timestamps[f"career_profile.{k}"] = now

        if "skill_gaps" in updates and updates["skill_gaps"] is not None:
            memory.skill_gaps = updates["skill_gaps"]
            memory.field_timestamps["skill_gaps"] = now

        self.save(memory)
        return memory

    def delete_field(self, user_id: str, field: str) -> UserMemory:
        memory = self.load(user_id)
        now = datetime.now().isoformat()

        if field == "display_name":
            memory.display_name = None
        elif field == "tone_preference":
            memory.tone_preference = "professional"
        elif field == "language":
            memory.language = "vi"
        elif field == "career_profile":
            memory.career_profile = CareerProfile()
        elif field.startswith("career_profile."):
            sub = field.split(".", 1)[1]
            if sub == "current_skills":
                memory.career_profile.current_skills = []
            elif sub == "timeline_months":
                memory.career_profile.timeline_months = None
            else:
                setattr(memory.career_profile, sub, None)
        elif field == "skill_gaps":
            memory.skill_gaps = []
        elif field == "suggestion_history":
            memory.suggestion_history = []
        else:
            logger.warning(f"Unknown field to delete: {field}")
            return memory

        memory.field_timestamps.pop(field, None)
        memory.updated_at = now
        self.save(memory)
        return memory

    def delete_all(self, user_id: str) -> None:
        path = self._path(user_id)
        if os.path.exists(path):
            os.remove(path)
            logger.info(f"Deleted all memory for {user_id}")

    # ── Suggestion History ──────────────────────────────────────────────

    def add_suggestion(self, user_id: str, suggestion_type: str, content: str) -> None:
        memory = self.load(user_id)
        # Skip duplicates within the recent 7-day window
        recent_cutoff = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
        normalized = content.strip().lower()
        if any((s.content or "").strip().lower() == normalized and s.given_at >= recent_cutoff for s in memory.suggestion_history):
            return

        memory.suggestion_history.append(SuggestionRecord(
            type=suggestion_type,
            content=content,
            given_at=datetime.now().strftime("%Y-%m-%d"),
        ))
        # Keep only last 20 suggestions
        if len(memory.suggestion_history) > 20:
            memory.suggestion_history = memory.suggestion_history[-20:]
        self.save(memory)

    # ── Staleness Check ─────────────────────────────────────────────────

    def get_stale_fields(self, memory: UserMemory, days: int = STALENESS_DAYS) -> List[str]:
        stale = []
        cutoff = (datetime.now() - timedelta(days=days)).isoformat()
        for field, ts in memory.field_timestamps.items():
            if ts < cutoff:
                stale.append(field)
        return stale

    # ── Prompt Formatting ───────────────────────────────────────────────

    def format_for_prompt(self, memory: UserMemory) -> str:
        parts = ["## User Profile Memory (US-27)"]

        # Name & tone
        name = memory.display_name or "Unknown"
        parts.append(f"User: {name} (tone: {memory.tone_preference}, language: {memory.language})")

        # Career profile
        cp = memory.career_profile
        if cp.current_role:
            parts.append(f"Current role: {cp.current_role}")
        if cp.current_skills:
            parts.append(f"Skills: {', '.join(cp.current_skills)}")
        if cp.target_role:
            target = f"Target: {cp.target_role}"
            if cp.timeline_months:
                target += f" (within {cp.timeline_months} months)"
            parts.append(target)

        # Skill gaps
        if memory.skill_gaps:
            parts.append(f"Skill gaps identified: {', '.join(memory.skill_gaps)}")

        # Staleness warnings
        stale = self.get_stale_fields(memory)
        if stale:
            parts.append(f"\n⚠️ Stale fields (>{STALENESS_DAYS} days old): {', '.join(stale)}")
            parts.append("Consider asking the user to confirm if this information is still accurate.")

        # Recent suggestions (deduplication)
        recent_cutoff = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
        recent = [s for s in memory.suggestion_history if s.given_at >= recent_cutoff]
        if recent:
            parts.append("\nRecent suggestions (do NOT repeat within 7 days):")
            for s in recent:
                parts.append(f"- {s.content} ({s.given_at})")

        # Instructions
        if memory.display_name:
            parts.append(f"\nAddress the user as \"{memory.display_name}\". Adapt your tone to be {memory.tone_preference}.")
        if memory.tone_preference == "casual":
            parts.append("Use informal, friendly language. Use 'bạn/mình' in Vietnamese.")
        else:
            parts.append("Use professional, polite language.")
        if memory.language == "en":
            parts.append("Prefer English unless the user explicitly writes in Vietnamese.")
        else:
            parts.append("Prefer Vietnamese unless the user explicitly asks for English.")

        # Only return if we have meaningful data beyond defaults
        has_data = (
            memory.display_name
            or cp.current_role
            or cp.current_skills
            or cp.target_role
            or memory.skill_gaps
        )
        return "\n".join(parts) if has_data else ""
