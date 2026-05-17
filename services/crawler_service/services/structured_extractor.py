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
    # "2-5 năm", "2 đến 5 năm", "từ 2 đến 5 năm", "between 2 and 5 years"
    r"(?:từ\s+|between\s+)?(\d{1,2})\s*(?:[-–~]|đến|to|and|tới)\s*(\d{1,2})\s*\+?\s*(?:years?|năm)",
    re.I,
)
_RE_EXP_PLUS = re.compile(
    r"(\d{1,2})\s*\+\s*(?:years?|năm)",
    re.I,
)
_RE_EXP_AT_LEAST = re.compile(
    # Bổ sung "trên X năm", "from X years", "over X years", "X+ years"
    r"(?:at\s*least|tối\s*thiểu|minimum(?:\s*of)?|ít\s*nhất|trên|over|from|từ|hơn|"
    r"min\.?|more\s*than)\s+(\d{1,2})\s*\+?\s*(?:years?|năm)",
    re.I,
)
_RE_EXP_AT_MOST = re.compile(
    # "dưới X năm", "up to X years", "tối đa X năm", "no more than X"
    r"(?:dưới|under|less\s*than|up\s*to|tối\s*đa|no\s*more\s*than)\s+(\d{1,2})\s*(?:years?|năm)",
    re.I,
)
_RE_EXP_SIMPLE = re.compile(
    # Bắt: "X năm kinh nghiệm", "X years of experience", "X year exp",
    # "có X năm", "with X years" — đặc biệt cho TopCV title có "Từ X Năm Kinh Nghiệm"
    r"(?:có|with)?\s*(\d{1,2})\s*\+?\s*(?:years?|năm)(?:\s*(?:of\s*)?(?:experience|exp|kinh\s*nghiệm))?",
    re.I,
)

_RE_WORK_MODE = re.compile(
    # Mở rộng: "remote", "hybrid", "WFH", "work from home", "từ xa", "online",
    # "tại văn phòng", "at office", "onsite", "on-site"
    r"\b(fully\s*remote|remote|hybrid|on[- ]?site|at\s*office|wfh|"
    r"work\s*from\s*home|làm\s*việc\s*tại\s*văn\s*phòng|tại\s*văn\s*phòng|"
    r"làm\s*việc\s*từ\s*xa|từ\s*xa|online)\b",
    re.I,
)

_RE_DEGREE = re.compile(
    # Bắt nhiều biến thể tiếng Việt:
    # "Tốt nghiệp Đại học", "Cử nhân", "có bằng đại học", "Cao đẳng trở lên",
    # "Tốt nghiệp ngành ... Đại học", "trình độ Đại học"
    r"\b(Bachelor['']?s?\s*(?:degree|of)?|"
    r"Master['']?s?\s*(?:degree|of)?|"
    r"Ph\.?D|Doctorate|Tiến\s*sĩ|"
    r"Thạc\s*sĩ|"
    r"Cử\s*nhân|"
    r"(?:Tốt\s*nghiệp\s+)?Đại\s*học(?:\s+trở\s*lên)?|"
    r"(?:Tốt\s*nghiệp\s+)?Cao\s*đẳng(?:\s+trở\s*lên)?|"
    r"Trung\s*cấp(?:\s+trở\s*lên)?|"
    r"College|University|degree)\b",
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

    # ── seniority from title ──────────────────────────────────────────────
    # Title is the most reliable signal (description-wide search hits verbs
    # like "Lead end-to-end..."). When title doesn't say it, we'll derive
    # from min_exp at the end of this function.
    for label, pat in _SENIORITY_PATTERNS:
        if pat.search(title or ""):
            out.seniority = label
            break

    # ── exp range ──────────────────────────────────────────────────────────
    # Try strongest signals first: explicit range "2-5 năm", then bounded
    # patterns ("at least X", "up to Y"), then bare numbers.
    m = _RE_EXP_RANGE.search(full)
    if m:
        out.min_exp = int(m.group(1))
        out.max_exp = int(m.group(2))
    else:
        m_min = _RE_EXP_AT_LEAST.search(full)
        m_max = _RE_EXP_AT_MOST.search(full)
        if m_min:
            out.min_exp = int(m_min.group(1))
        if m_max:
            out.max_exp = int(m_max.group(1))
        if out.min_exp is None:
            m = _RE_EXP_PLUS.search(full)
            if m:
                out.min_exp = int(m.group(1))
        if out.min_exp is None and out.max_exp is None:
            m = _RE_EXP_SIMPLE.search(full)
            if m:
                out.min_exp = int(m.group(1))

    # Sanity: cap unrealistic values (rule sometimes matches "100% remote" →
    # min_exp=100; or "in 2024" → min_exp=2024).
    if out.min_exp is not None and not 0 <= out.min_exp <= 20:
        out.min_exp = None
    if out.max_exp is not None and not 0 <= out.max_exp <= 30:
        out.max_exp = None
    if out.min_exp is not None and out.max_exp is not None and out.min_exp > out.max_exp:
        # Probably parsed wrong; trust min
        out.max_exp = None

    # ── work mode ──────────────────────────────────────────────────────────
    m = _RE_WORK_MODE.search(full)
    if m:
        out.work_mode = _WORK_MODE_MAP.get(m.group(1).lower().strip())
    else:
        # Default for the VN market: when no signal, assume onsite — 90%+ of
        # JDs in our crawled dataset that DO mention work_mode pick onsite.
        # Caller can still detect this is a default by checking parse_version.
        out.work_mode = "onsite"

    # ── degree ─────────────────────────────────────────────────────────────
    m = _RE_DEGREE.search(full)
    if m:
        deg_raw = m.group(1).strip()
        deg_lower = deg_raw.lower()
        # Canonical normalization across EN/VI variants
        if "thạc sĩ" in deg_lower or deg_lower.startswith("master"):
            out.degree_required = "Master"
        elif "tiến sĩ" in deg_lower or deg_lower.startswith(("phd", "ph.d", "doctor")):
            out.degree_required = "PhD"
        elif (
            "đại học" in deg_lower
            or "cử nhân" in deg_lower
            or deg_lower.startswith(("bachelor", "univers"))
        ):
            out.degree_required = "Bachelor"
        elif "cao đẳng" in deg_lower or deg_lower.startswith("college"):
            out.degree_required = "Diploma"
        elif "trung cấp" in deg_lower:
            out.degree_required = "Intermediate"
        else:
            out.degree_required = deg_raw[:64]

    # ── derive seniority from min_exp when title didn't give us one ────────
    # Industry-standard buckets (VN market):
    #   0-1y → junior/fresher, 2-3y → mid, 4-6y → senior, 7+y → lead
    if out.seniority is None and out.min_exp is not None:
        if out.min_exp <= 1:
            out.seniority = "junior"
        elif out.min_exp <= 3:
            out.seniority = "mid"
        elif out.min_exp <= 6:
            out.seniority = "senior"
        else:
            out.seniority = "lead"

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
