"""Groq-backed LLM JD structured-field extractor.

This is the smart-overlay companion to `structured_extractor.py`. The regex
extractor handles deterministic / cheap fields (location, posted_date,
work_mode badges, simple year mentions). The LLM fills in fields where regex
is brittle:

  - seniority    — when title is ambiguous (e.g. "IT Security & Network
                  Engineer" reads senior but the title has no level keyword)
  - min/max exp  — handles "3-5 years", "at least 4", phrasing variants
  - degree       — avoids false positives like "Bachelor of Banking is a plus"
  - skills_required vs skills_preferred — semantic Must-Have vs Nice-to-Have
                  split that regex bucketing misses

Backend: Groq Cloud (OpenAI-compatible chat-completions). Configured from
environment:
    CHAT_GROQ_API_KEY  (required)
    CHAT_GROQ_MODEL    (optional, default openai/gpt-oss-120b)

Cost discipline: prompt + description capped at MAX_DESC_CHARS; output capped
at 800 tokens with temperature=0 and JSON response_format for determinism.
"""
from __future__ import annotations

import json
import logging
import os
import re
from dataclasses import dataclass, field
from typing import Optional

import requests

logger = logging.getLogger(__name__)


DEFAULT_GROQ_URL = "https://api.groq.com/openai/v1"
DEFAULT_GROQ_MODEL = "openai/gpt-oss-120b"
DEFAULT_TIMEOUT_S = 30
MAX_DESC_CHARS = 3500


@dataclass
class LLMResult:
    # Semantic fields (LLM is the primary source — HTML regex is fragile here)
    seniority: Optional[str] = None
    min_exp: Optional[int] = None
    max_exp: Optional[int] = None
    degree_required: Optional[str] = None
    skills_required: list[str] = field(default_factory=list)
    skills_preferred: list[str] = field(default_factory=list)
    # Cross-validation fields (HTML usually wins, LLM provides fallback when
    # JSON-LD is missing or placeholder e.g. "You'll love it" for salary)
    salary_min: Optional[int] = None
    salary_max: Optional[int] = None
    salary_currency: Optional[str] = None
    work_mode: Optional[str] = None


class LLMJDExtractor:
    """Groq-backed JD field extractor. Optional overlay on top of regex."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        timeout_s: int = DEFAULT_TIMEOUT_S,
    ):
        self.api_key = api_key or os.environ.get("CHAT_GROQ_API_KEY")
        if not self.api_key:
            raise ValueError("CHAT_GROQ_API_KEY is missing — set it in env or pass api_key=")
        self.base_url = (base_url or DEFAULT_GROQ_URL).rstrip("/")
        self.model = model or os.environ.get("CHAT_GROQ_MODEL") or DEFAULT_GROQ_MODEL
        self.timeout_s = timeout_s

    def extract(
        self,
        *,
        title: str,
        description: str,
        candidate_skills: list[str],
    ) -> Optional[LLMResult]:
        """Return LLMResult or None on failure. Candidate_skills are the
        chip skills from the listing — the LLM picks from this set and never
        invents new entries (validated downstream)."""
        if not description or len(description) < 80:
            return None

        prompt = _build_prompt(title, description[:MAX_DESC_CHARS], candidate_skills)
        text = self._call(prompt)
        if not text:
            return None

        parsed = _parse_response_json(text)
        if parsed is None:
            return None
        return _coerce(parsed, candidate_skills)

    def _call(self, prompt: str, max_retries: int = 2) -> Optional[str]:
        """Groq exposes an OpenAI-compatible chat-completions endpoint.

        Retries on 429 (rate limit) using the `retry-after` hint from the body
        when available. Returns None on permanent failure.
        """
        import re as _re
        import time as _time
        for attempt in range(max_retries + 1):
            try:
                resp = requests.post(
                    f"{self.base_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": self.model,
                        "messages": [
                            {
                                "role": "system",
                                "content": (
                                    "You are a strict JSON-only extraction assistant. "
                                    "Output exactly ONE valid JSON object. No prose, "
                                    "no markdown, no code fences."
                                ),
                            },
                            {"role": "user", "content": prompt},
                        ],
                        "temperature": 0.0,
                        "max_tokens": 800,
                    },
                    timeout=self.timeout_s,
                )
            except requests.RequestException as e:
                logger.warning("Groq call failed (attempt %d): %s", attempt + 1, e)
                return None

            if resp.status_code == 200:
                try:
                    return resp.json()["choices"][0]["message"]["content"]
                except (ValueError, KeyError, IndexError) as e:
                    logger.warning("Groq response parse failed: %s", e)
                    return None

            if resp.status_code == 429 and attempt < max_retries:
                # Extract suggested wait time from error message
                body = resp.text[:400]
                m = _re.search(r"try again in ([\d.]+)s", body)
                wait_s = float(m.group(1)) + 0.5 if m else 16.0
                wait_s = min(wait_s, 30.0)  # cap to avoid blocking forever
                logger.info("Groq 429 — sleeping %.1fs before retry %d/%d", wait_s, attempt + 2, max_retries + 1)
                _time.sleep(wait_s)
                continue

            logger.warning("Groq returned %d: %s", resp.status_code, resp.text[:300])
            return None

        return None


# ─── Prompt + parsing ─────────────────────────────────────────────────────────


def _build_prompt(title: str, description: str, candidate_skills: list[str]) -> str:
    skill_list = ", ".join(candidate_skills[:40]) or "(none)"
    return f"""You are a STRICT extraction assistant. Read the JOB DESCRIPTION and copy facts that are LITERALLY written there. You MUST NOT guess, infer, generalize, or fill gaps from your knowledge.

JOB TITLE: {title}

CANDIDATE SKILLS (these are the only valid string values for skills_required and skills_preferred — copy exactly as listed):
{skill_list}

JOB DESCRIPTION (this is your ONLY source of truth):
\"\"\"
{description}
\"\"\"

Return ONE JSON object with exactly these keys, no others:

{{
  "seniority": "junior" | "mid" | "senior" | "lead" | null,
  "min_exp": <integer> | null,
  "max_exp": <integer> | null,
  "degree_required": "Bachelor" | "Master" | "PhD" | null,
  "skills_required": [<strings from CANDIDATE SKILLS>],
  "skills_preferred": [<strings from CANDIDATE SKILLS>],
  "salary_min": <integer> | null,
  "salary_max": <integer> | null,
  "salary_currency": "USD" | "VND" | null,
  "work_mode": "onsite" | "hybrid" | "remote" | null
}}

==================== ABSOLUTE RULES ====================

If you violate ANY of these rules, the extraction fails. When in doubt, return null. Empty/null is ALWAYS better than guessed.

──── RULE 1: SENIORITY ────

The ONLY valid signal for `seniority` is one of these words appearing in the JOB TITLE or as a literal section heading in the description:
  "Senior" / "Sr." / "Senior-level" → "senior"
  "Junior" / "Jr." / "Fresher" / "Intern" → "junior"
  "Mid" / "Middle" / "Mid-level" → "mid"
  "Lead" / "Principal" / "Head of" / "Chief" → "lead"

If NONE of these literal words appear → seniority = null. DO NOT infer from years of experience. DO NOT infer from job complexity. DO NOT use your training knowledge.

EXAMPLES:
  Title "Senior Backend Developer" → "senior" ✓
  Title "Python Developer" + "3+ years" → null  (NOT "junior", NOT "mid")
  Title "IT Security Engineer" + "5+ years" → null  (NOT "senior")
  Title "Lead Architect" → "lead" ✓

──── RULE 2: min_exp / max_exp ────

Only extract numbers from phrases that literally state YEARS OF CANDIDATE EXPERIENCE.

  Pattern "N+ years" / "N+ năm" → min_exp = N, max_exp = null
  Pattern "N-M years" / "N to M years" → min_exp = N, max_exp = M
  Pattern "at least N years" / "minimum N years" → min_exp = N, max_exp = null
  No years mentioned → both null

DO NOT invent max_exp if only min_exp is stated. "3+ years" means min_exp=3, max_exp=null. NEVER write max_exp=5 unless the text says "3-5 years" or "3 to 5 years" explicitly.

IGNORE years that don't refer to candidate experience:
  "60 years of heritage" → IGNORE
  "founded in 2010" → IGNORE
  "13th month salary" → IGNORE

──── RULE 3: degree_required ────

Only fill when the text REQUIRES a specific degree as a hard requirement.

  "Bachelor's degree in CS required" → "Bachelor" ✓
  "Bachelor's degree is mandatory" → "Bachelor" ✓
  "Bachelor of Banking is a plus" → null (it's preferred, not required)
  "We graduate top universities" → null (about company, not requirement)
  Just mentions university name → null

──── RULE 4: skills_required vs skills_preferred (READ CAREFULLY) ────

**THIS IS THE MOST COMMON FAILURE POINT. PAY EXTRA ATTENTION.**

Step 1 — Scan the JOB DESCRIPTION for these EXACT section markers (case-insensitive):
  PREFERRED markers: "Nice-to-Have", "Nice to Have", "Preferred", "Bonus", "Plus", "Optional", "Highly Valued", "Ưu tiên", "Lợi thế", "Sẽ là lợi thế", "Điểm cộng"
  REQUIRED markers: "Must-Have", "Must Have", "Required", "Requirements", "Your Skills", "Skills and Experience", "Qualifications", "Yêu cầu", "Kỹ năng yêu cầu"

Step 2 — Bucket each CANDIDATE SKILL by where it appears in the description:

  CASE A: Skill appears AFTER a PREFERRED marker → put in skills_preferred.
  CASE B: Skill appears AFTER a REQUIRED marker (and not in a PREFERRED section) → put in skills_required.
  CASE C: Skill appears anywhere else but NOT in any preferred section → put in skills_required.
  CASE D: Skill is in CANDIDATE SKILLS but does NOT appear anywhere in description → put in skills_required (default).

Step 3 — CRITICAL: If the description has NO PREFERRED MARKER at all, then `skills_preferred = []` (empty array). DO NOT redistribute candidate skills into preferred. DO NOT invent a preferred section.

Step 4 — A skill must NEVER appear in both buckets. If conflict, REQUIRED wins.

Step 5 — Use the EXACT casing/spelling from CANDIDATE SKILLS. Never invent a skill not in that list.

EXAMPLES:
  Description has "Nice-to-Have: CISSP, CCNP, ISO 27001" → skills_preferred = (skills from that section that match CANDIDATE SKILLS)
  Description has only "Requirements: ..." with no Nice-to-Have section → skills_preferred = []  (EMPTY!)
  Description has "Must-Have: Python" and "Highly Valued: Docker" → skills_required = [Python], skills_preferred = [Docker]

──── RULE 5: salary ────

Only fill when a NUMERIC range or value is stated:
  "1,000 - 1,800 USD" → min=1000, max=1800, currency="USD"
  "20.000.000 – 30.000.000 VND" → min=20000000, max=30000000, currency="VND"
  "Up to $2000" → min=null, max=2000, currency="USD"
  "Negotiable" / "You'll love it" / "Sign in to view" / "Competitive" / "DOE" → ALL null

──── RULE 6: work_mode ────

  "At office" / "Tại văn phòng" / "On-site" → "onsite"
  "Hybrid" / "Kết hợp" → "hybrid"
  "Fully remote" / "100% remote" / "Work from home" → "remote"
  Not mentioned → null

==================== FINAL CHECK ====================

Before responding, audit your JSON:
  □ Did I look for the LITERAL words for seniority? If no literal word, did I write null?
  □ Did I avoid inferring max_exp from a "+years" pattern?
  □ For preferred skills: does the description ACTUALLY have a "Nice-to-Have" / "Preferred" section? If no, is skills_preferred = []?
  □ Did I copy skill names EXACTLY from CANDIDATE SKILLS without modification?

Output ONLY the JSON. No prose, no markdown, no code fences."""


_JSON_OBJ = re.compile(r"\{[\s\S]*\}", re.M)
_FENCE = re.compile(r"```(?:json)?\s*([\s\S]+?)```", re.I)


def _parse_response_json(text: str) -> Optional[dict]:
    """Be defensive — even with response_format=json_object, an occasional
    response slips through as code-fenced or prose-wrapped."""
    if not text:
        return None
    m = _FENCE.search(text)
    if m:
        text = m.group(1)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    m = _JSON_OBJ.search(text)
    if not m:
        return None
    try:
        return json.loads(m.group(0))
    except json.JSONDecodeError as e:
        logger.warning("LLM JSON parse failed: %s; raw: %.200s", e, text)
        return None


def _coerce(parsed: dict, candidate_skills: list[str]) -> LLMResult:
    """Validate + clean LLM output. Returns LLMResult with safe defaults
    and drops any skill the LLM hallucinated outside CANDIDATE SKILLS."""
    out = LLMResult()

    sen = parsed.get("seniority")
    if isinstance(sen, str) and sen.strip().lower() in {"junior", "mid", "senior", "lead"}:
        out.seniority = sen.strip().lower()

    for key in ("min_exp", "max_exp"):
        v = parsed.get(key)
        if isinstance(v, (int, float)) and 0 <= v <= 30:
            setattr(out, key, int(v))
        elif isinstance(v, str) and v.strip().isdigit():
            n = int(v)
            if 0 <= n <= 30:
                setattr(out, key, n)

    deg = parsed.get("degree_required")
    if isinstance(deg, str) and deg.strip() in {"Bachelor", "Master", "PhD"}:
        out.degree_required = deg.strip()

    cand_lower = {s.lower(): s for s in candidate_skills}
    seen: set[str] = set()
    for key in ("skills_required", "skills_preferred"):
        raw = parsed.get(key) or []
        if not isinstance(raw, list):
            continue
        cleaned: list[str] = []
        for item in raw:
            if not isinstance(item, str):
                continue
            canonical = cand_lower.get(item.strip().lower())
            if canonical and canonical.lower() not in seen:
                cleaned.append(canonical)
                seen.add(canonical.lower())
        setattr(out, key, cleaned)

    # Salary
    for key in ("salary_min", "salary_max"):
        v = parsed.get(key)
        if isinstance(v, (int, float)) and v > 0:
            setattr(out, key, int(v))
    cur = parsed.get("salary_currency")
    if isinstance(cur, str) and cur.strip().upper() in {"USD", "VND"}:
        out.salary_currency = cur.strip().upper()

    # Work mode
    wm = parsed.get("work_mode")
    if isinstance(wm, str) and wm.strip().lower() in {"onsite", "hybrid", "remote"}:
        out.work_mode = wm.strip().lower()

    return out
