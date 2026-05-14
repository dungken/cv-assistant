"""Skill extraction for JDs.

Strategy (in priority order):
1. Use skills_raw if non-empty (source already provided skill tags, e.g. ITviec).
2. Else, extract from description via NER service (when available).
3. Else fallback: ontology-based matching against title text
   (handles TopCV, where listing cards don't expose skill tags).

Step 3 uses the existing SkillOntology to find canonical skill names embedded
in the title — works well because Vietnamese IT job titles commonly contain
the tech stack in parentheses, e.g. "Backend Developer (.Net/ Java/ NodeJS)".
"""
import logging
import re
from functools import lru_cache

import requests

from services.crawler_service.config import settings

logger = logging.getLogger(__name__)


class SkillExtractor:
    def __init__(self, ner_url: str | None = None, skill_url: str | None = None) -> None:
        self.ner_url = (ner_url or settings.ner_service_url).rstrip("/")
        self.skill_url = (skill_url or settings.skill_service_url).rstrip("/")

    # ── public ──────────────────────────────────────────────────────

    def extract_from_jd(
        self,
        description: str,
        fallback_skills: list[str],
        title: str = "",
    ) -> list[str]:
        """Return canonical skill list, trying multiple sources."""
        # 1. source-provided tags win — they're already curated.
        if fallback_skills:
            return self._normalize(fallback_skills)
        # 2. NER on description (skipped if description empty or NER down).
        from_ner = self._extract_via_ner(description) if description else []
        if from_ner:
            return self._normalize(from_ner)
        # 3. Fallback: ontology pattern-match against title + description.
        text_blob = (title + "\n" + description).strip()
        return self._extract_from_text(text_blob)

    # ── internals ───────────────────────────────────────────────────

    def _extract_via_ner(self, text: str) -> list[str]:
        try:
            resp = requests.post(
                f"{self.ner_url}/parse-jd", json={"text": text}, timeout=20,
            )
            resp.raise_for_status()
            return list(resp.json().get("skills", []) or [])
        except Exception as e:
            logger.debug("NER unavailable: %s", e)
            return []

    def _normalize(self, skills: list[str]) -> list[str]:
        try:
            resp = requests.post(
                f"{self.skill_url}/skills/normalize",
                json={"skills": skills}, timeout=10,
            )
            resp.raise_for_status()
            return list(dict.fromkeys(resp.json().get("canonical", skills)))
        except Exception as e:
            logger.debug("Skill normalize unavailable, returning raw: %s", e)
            return list(dict.fromkeys(skills))

    def _extract_from_text(self, text: str) -> list[str]:
        """Match canonical skill names against arbitrary text via word-boundary regex."""
        if not text:
            return []
        text_lower = text.lower()
        found: list[str] = []
        for skill, pattern in _get_skill_patterns():
            if pattern.search(text_lower):
                found.append(skill)
        return list(dict.fromkeys(found))


@lru_cache(maxsize=1)
def _get_skill_patterns() -> list[tuple[str, "re.Pattern"]]:
    """Build (canonical_skill, regex) pairs once. Word-boundary matching."""
    # Import here to avoid circular cost when NER-only path is used.
    from services.skill_service.services.ontology import SkillOntology

    ont = SkillOntology()
    patterns: list[tuple[str, re.Pattern]] = []
    for skill in ont.all_skills:
        if len(skill) < 2:
            continue  # skip too-short skills that cause false positives
        patterns.append(
            (skill, re.compile(r"\b" + re.escape(skill.lower()) + r"\b"))
        )
    logger.info("Loaded %d skill patterns from ontology", len(patterns))
    return patterns
