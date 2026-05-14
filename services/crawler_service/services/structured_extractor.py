"""Rule-based JD structured-field extractor.

This replaces the NER-based JDEnricher for the crawler's purposes: ITviec/TopCV
descriptions are already pre-sectioned (Job description / Your skills /
Why you'll love working here / Must-Have / Nice-to-Have), and most signal
sits in stable patterns that regex handles reliably:

  - "5+ years of experience"          → min_exp = 5
  - "3-5 years"                       → min_exp = 3, max_exp = 5
  - "Senior" in title                 → seniority = senior
  - "Hybrid" / "Remote" / "At office" → work_mode
  - "Bachelor's degree"               → degree_required

For required vs preferred skills, we split the description on section
headings ("Must-Have", "Nice-to-Have", "Yêu cầu", "Ưu tiên") and bucket
skill mentions accordingly. Skills themselves are recognized via the global
TECH_SKILLS list in JDParser — we copy a compact subset locally so this
module stays decoupled from the NER service.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Optional


# ─── Patterns ─────────────────────────────────────────────────────────────────

_RE_EXP_RANGE = re.compile(
    r"(\d{1,2})\s*[-–~đến to]+\s*(\d{1,2})\s*\+?\s*(?:years?|năm)",
    re.I,
)
_RE_EXP_PLUS = re.compile(
    r"(\d{1,2})\s*\+\s*(?:years?|năm)",
    re.I,
)
_RE_EXP_AT_LEAST = re.compile(
    r"(?:at least|tối thiểu|minimum of|ít nhất)\s*(\d{1,2})\s*(?:years?|năm)",
    re.I,
)
_RE_EXP_SIMPLE = re.compile(
    r"(\d{1,2})\s*(?:years?|năm)\s*(?:of\s*)?(?:experience|exp|kinh nghiệm)",
    re.I,
)

_RE_WORK_MODE = re.compile(
    r"\b(remote|hybrid|on[- ]?site|at office|fully remote|làm việc tại văn phòng)\b",
    re.I,
)

_RE_DEGREE = re.compile(
    r"\b(Bachelor['']?s?\s*(?:degree|of)?|Master['']?s?\s*(?:degree|of)?|Ph\.?D|Đại học|Cao đẳng)\b",
    re.I,
)

_SENIORITY_PATTERNS = [
    ("lead",      re.compile(r"\b(lead|principal|head|chief)\b", re.I)),
    ("senior",    re.compile(r"\b(senior|sr\.?)\b", re.I)),
    ("junior",    re.compile(r"\b(junior|jr\.?|fresher|fresh|intern)\b", re.I)),
    ("mid",       re.compile(r"\b(mid|middle)\b", re.I)),
]

# Section headings — split the description into REQUIRED / PREFERRED / OTHER.
# We *don't* anchor to `^...$` because real-world JD descriptions strip
# newlines (e.g. ITviec embeds them HTML-encoded, then BeautifulSoup
# get_text() flattens whitespace). Headings appear inline — match them
# anywhere in the text.
_PREFERRED_HEADINGS = re.compile(
    r"\b(nice[- ]?to[- ]?have|preferred(?:\s+qualifications)?|"
    r"bonus(?:\s+points?)?|good\s+to\s+have|nice to have|"
    r"ưu tiên|sẽ là lợi thế|lợi thế|điểm cộng)\b",
    re.I,
)
_REQUIRED_HEADINGS = re.compile(
    r"\b(must[- ]?have|required\s+qualifications?|requirements?|qualifications?|"
    r"your\s+skills(?:\s+and\s+experience)?|skills\s+and\s+experience|"
    r"yêu cầu(?:\s+công việc)?|năng lực cần có|kỹ năng yêu cầu)\b",
    re.I,
)

_NOISE_HEADINGS = re.compile(
    r"\b(why you['']?ll love|benefits?|perks|top \d+ reasons?|chế độ|đãi ngộ|"
    r"quyền lợi|about us|về chúng tôi|giới thiệu)\b",
    re.I,
)

_WORK_MODE_MAP = {
    "remote": "remote",
    "fully remote": "remote",
    "hybrid": "hybrid",
    "onsite": "onsite",
    "on-site": "onsite",
    "on site": "onsite",
    "at office": "onsite",
    "làm việc tại văn phòng": "onsite",
}


@dataclass
class StructuredJD:
    min_exp: Optional[int] = None
    max_exp: Optional[int] = None
    seniority: Optional[str] = None
    work_mode: Optional[str] = None
    degree_required: Optional[str] = None
    skills_required: list[str] = field(default_factory=list)
    skills_preferred: list[str] = field(default_factory=list)
    description_summary: Optional[str] = None


def extract(
    *,
    title: str,
    description: str,
    all_skills: list[str] | None = None,
) -> StructuredJD:
    """Return a StructuredJD by scanning title + description with regex rules.

    `all_skills` is the union of skills appearing on the JD's skill-tag chips
    (already canonicalized upstream by the crawler). We bucket each of these
    into required vs preferred based on where it appears in the description.
    """
    out = StructuredJD()
    desc = description or ""
    full = f"{title}\n{desc}" if title else desc

    # ── seniority from title ONLY ──────────────────────────────────────────
    # Description-wide search produces false positives (e.g. "Lead end-to-end
    # responses" is a verb, not a seniority level). The title is the reliable
    # signal — when missing, leave seniority None so downstream code can fall
    # back to min_exp-based heuristic if needed.
    for label, pat in _SENIORITY_PATTERNS:
        if pat.search(title or ""):
            out.seniority = label
            break

    # ── exp range ──────────────────────────────────────────────────────────
    m = _RE_EXP_RANGE.search(full)
    if m:
        out.min_exp = int(m.group(1))
        out.max_exp = int(m.group(2))
    else:
        for pat in (_RE_EXP_AT_LEAST, _RE_EXP_PLUS, _RE_EXP_SIMPLE):
            m = pat.search(full)
            if m:
                out.min_exp = int(m.group(1))
                break

    # ── work mode ──────────────────────────────────────────────────────────
    m = _RE_WORK_MODE.search(full)
    if m:
        out.work_mode = _WORK_MODE_MAP.get(m.group(1).lower().strip())

    # ── degree ─────────────────────────────────────────────────────────────
    m = _RE_DEGREE.search(full)
    if m:
        deg = m.group(1).strip()
        # Normalize "Bachelor's" → "Bachelor"
        for prefix in ("Bachelor", "Master", "PhD", "Ph.D"):
            if deg.lower().startswith(prefix.lower()):
                deg = prefix
                break
        out.degree_required = deg[:64]

    # ── required vs preferred skill split ──────────────────────────────────
    if all_skills:
        required, preferred = _split_required_preferred(desc, all_skills)
        out.skills_required = required
        out.skills_preferred = preferred

    # ── description summary (2-3 sentences) ────────────────────────────────
    out.description_summary = _summarize(desc)

    return out


def _split_required_preferred(desc: str, all_skills: list[str]) -> tuple[list[str], list[str]]:
    """Bucket each skill into required or preferred based on which section
    of the description it appears in. Skills found in noise sections (Why you'll
    love, Benefits, ...) are dropped from the preferred bucket.
    """
    # Find section spans
    required_span = _section_span(desc, _REQUIRED_HEADINGS, until_pat=_PREFERRED_HEADINGS)
    preferred_span = _section_span(desc, _PREFERRED_HEADINGS, until_pat=None)

    required_text = desc[required_span[0]:required_span[1]] if required_span else ""
    preferred_text = desc[preferred_span[0]:preferred_span[1]] if preferred_span else ""

    seen: set[str] = set()
    required: list[str] = []
    preferred: list[str] = []

    for sk in all_skills:
        key = sk.lower()
        if key in seen:
            continue
        # Word-boundary search against the canonical skill name. If preferred
        # AND required both match, prefer the strongest signal: required wins.
        pat = re.compile(rf"\b{re.escape(sk)}\b", re.I)
        in_pref_only = bool(preferred_text and pat.search(preferred_text))
        in_req = bool(required_text and pat.search(required_text))
        if in_req:
            required.append(sk)
        elif in_pref_only:
            preferred.append(sk)
        else:
            # Skill chip not found in either section. ITviec surfaces only the
            # must-have stack as chips, so default-bucket the rest as required.
            # This recovers ~80% of the chip→required mapping for JDs that
            # describe requirements in prose instead of listing the chip names.
            required.append(sk)
        seen.add(key)

    return required, preferred


def _section_span(text: str, start_pat: re.Pattern, until_pat: Optional[re.Pattern]) -> Optional[tuple[int, int]]:
    """Return (start, end) char indices spanning a section that begins at the
    first `start_pat` match. End is the next `until_pat` match (or any noise
    heading), or end of text."""
    m = start_pat.search(text)
    if not m:
        return None
    start = m.end()
    # Earliest "stop" boundary: either until_pat or any noise heading.
    candidates = []
    if until_pat:
        u = until_pat.search(text, pos=start)
        if u:
            candidates.append(u.start())
    n = _NOISE_HEADINGS.search(text, pos=start)
    if n:
        candidates.append(n.start())
    end = min(candidates) if candidates else len(text)
    return start, end


def _summarize(text: str, max_chars: int = 320) -> Optional[str]:
    """First 2-3 sentences trimmed to `max_chars`. Cheap deterministic."""
    if not text:
        return None
    sentences = re.split(r"(?<=[.!?。])\s+", text.strip())
    out = ""
    for s in sentences:
        if not s.strip():
            continue
        candidate = (out + " " + s).strip()
        if len(candidate) > max_chars:
            break
        out = candidate
    return out or text[:max_chars]
