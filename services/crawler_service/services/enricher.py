"""Tuần 16 — call NER service /parse-jd-text to enrich raw JDs with
structured signal: min_exp, seniority, required vs preferred skills, etc.

Designed to fail soft: if NER is unreachable or slow, the JD is still stored
with whatever signal the crawler already extracted. A nightly backfill script
re-tries unparsed rows.
"""
from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from typing import Optional

import requests

logger = logging.getLogger(__name__)

PARSE_VERSION = "v1"
# NER takes 5-20s on long JDs (mBERT inference + LLM refiner). Original 15s
# timeout would drop most JD-detail-page-sized payloads. 60s comfortably
# covers 99th percentile while still bounding crawler runtime.
TIMEOUT_S = 60


@dataclass
class EnrichedJD:
    min_exp: Optional[int]
    max_exp: Optional[int]
    seniority: Optional[str]
    skills_required: list[str]
    skills_preferred: list[str]
    degree_required: Optional[str]
    work_mode: Optional[str]
    description_summary: Optional[str]
    parse_version: str = PARSE_VERSION


_WORK_MODE_PATTERNS = [
    ("remote", re.compile(r"\b(100% remote|fully remote|remote (only|first))\b", re.I)),
    ("hybrid", re.compile(r"\b(hybrid|hybrid model|hybrid working|kết hợp văn phòng)\b", re.I)),
    ("onsite", re.compile(r"\b(on[- ]?site|onsite|tại văn phòng|làm việc tại văn phòng)\b", re.I)),
]


def detect_work_mode(text: str) -> Optional[str]:
    if not text:
        return None
    for mode, pat in _WORK_MODE_PATTERNS:
        if pat.search(text):
            return mode
    return None


def summarize_description(text: str, max_chars: int = 320) -> Optional[str]:
    """Cheap deterministic summary: first 2-3 sentences of description.
    Replace with LLM later if needed — current approach has no external cost
    and stays useful for displaying a preview blurb under the JD title.
    """
    if not text:
        return None
    # Split on sentence-ish punctuation. Vietnamese also uses '。' rarely; cover both.
    sentences = re.split(r"(?<=[.!?。])\s+", text.strip())
    out = ""
    for s in sentences:
        if not s:
            continue
        candidate = (out + " " + s).strip()
        if len(candidate) > max_chars:
            break
        out = candidate
    return out or text[:max_chars]


class JDEnricher:
    """Wraps an HTTP call to NER service /parse-jd-text and normalizes the
    response into our column shape.
    """

    def __init__(self, ner_url: str, timeout_s: float = TIMEOUT_S):
        # ner_url is the service base, e.g. "http://localhost:5005"
        self.ner_url = ner_url.rstrip("/")
        self.timeout_s = timeout_s

    def enrich(self, *, title: str, company: str, description: str) -> Optional[EnrichedJD]:
        if not description or len(description) < 50:
            # Too short — skip to avoid noisy NER output.
            return None
        try:
            resp = requests.post(
                f"{self.ner_url}/parse-jd-text",
                json={"text": description, "title": title or "", "company": company or ""},
                timeout=self.timeout_s,
            )
        except requests.RequestException as e:
            logger.warning("JDEnricher: NER call failed: %s", e)
            return None
        if resp.status_code != 200:
            logger.warning("JDEnricher: NER returned %d: %s", resp.status_code, resp.text[:200])
            return None
        try:
            data = resp.json()
        except ValueError:
            logger.warning("JDEnricher: NER returned non-JSON")
            return None

        skills = data.get("extracted_skills") or {}
        req = list(skills.get("required") or [])
        pref = list(skills.get("preferred") or [])

        # Deduplicate, normalize case via lower-key.
        seen: set[str] = set()
        req_clean: list[str] = []
        for s in req:
            if isinstance(s, str) and s.strip() and s.lower() not in seen:
                seen.add(s.lower())
                req_clean.append(s.strip())
        pref_clean: list[str] = []
        for s in pref:
            if isinstance(s, str) and s.strip() and s.lower() not in seen:
                seen.add(s.lower())
                pref_clean.append(s.strip())

        min_exp = _coerce_int(data.get("min_exp"))
        max_exp = _coerce_int(data.get("max_exp"))
        seniority = _coerce_seniority(data.get("level"))
        degree = _coerce_degree(data.get("analysis", {}).get("degree_required") or data.get("degree_required"))

        work_mode = detect_work_mode(description)
        summary = summarize_description(description)

        return EnrichedJD(
            min_exp=min_exp,
            max_exp=max_exp,
            seniority=seniority,
            skills_required=req_clean,
            skills_preferred=pref_clean,
            degree_required=degree,
            work_mode=work_mode,
            description_summary=summary,
        )


def _coerce_int(v) -> Optional[int]:
    if v is None:
        return None
    try:
        i = int(v)
        if i < 0 or i > 30:
            return None
        return i
    except (TypeError, ValueError):
        return None


def _coerce_seniority(v) -> Optional[str]:
    if not v:
        return None
    val = str(v).strip().lower()
    if val in {"intern", "fresher"}:
        return "junior"
    if val in {"junior", "mid", "middle", "senior", "lead", "principal"}:
        return "mid" if val == "middle" else val
    return None


def _coerce_degree(v) -> Optional[str]:
    if not v:
        return None
    val = str(v).strip()
    if not val or val.lower() in {"none", "null", "n/a"}:
        return None
    # Truncate to col size (VARCHAR(64)).
    return val[:64]
