"""CV Freshness Engine — Tuần 10.

Implements the formula from chuong3/3.2:

    Freshness(CV, r, t) = 100 * sum_{s in S}  w_r(s) * trend(s, t) * recency(s)
                                / sum_{s in S_r_ideal}  w_r(s)

Components:
- importance w_r(s) = α1·1[PART_OF(s, r)] + α2·indegree_REQUIRES(s) + α3·freq_r(s)
- trend(s, t)       = clip(d_t / MA_4(s, t-1), 0.5, 1.5)
- recency(s)        = step function on years since last use {1.0, 0.7, 0.4, 0.1}
- S_r_ideal         = top-15 skills in JD role r over the last 4 weeks

Reads `skill_trends` written by the crawler aggregator (per-week buckets via
`window_days=7`). Falls back gracefully when there's not enough history
(cold-start: first 4 weeks of crawling).
"""
from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Optional

from sqlalchemy import text
from sqlalchemy.orm import Session

from services.skill_service.services.ontology import (
    PART_OF,
    REQUIRES,
    SkillOntology,
)

logger = logging.getLogger(__name__)


# ─── Tunables (defaults match chuong3/3.2) ────────────────────────────────────

ALPHA_PART_OF = 0.3
ALPHA_REQUIRES_INDEGREE = 0.2
ALPHA_FREQUENCY = 0.5

TREND_CLIP_LOW = 0.5
TREND_CLIP_HIGH = 1.5

IDEAL_TOP_K = 15
TREND_WINDOW_DAYS = 7
TREND_LOOKBACK_WEEKS = 4

DEFAULT_RECENCY = 0.7  # used when CV experience date info is missing

ALERT_DROP_THRESHOLD = 5.0  # §3.2.5 — fire alert when score drops more than this


# Role alias mapping — frontend gửi role ngắn (vd 'backend'), `skill_trends`
# lưu canonical từ crawler (vd 'backend-developer'). Mapping cho phép engine
# query đúng row, tránh cold_start giả do role mismatch.
ROLE_ALIASES_FOR_TRENDS: dict[str, list[str]] = {
    "backend": ["backend-developer", "backend"],
    "frontend": ["frontend-developer", "frontend"],
    "fullstack": ["fullstack-developer", "fullstack", "backend-developer", "frontend-developer"],
    "data": ["data-engineer", "data-scientist", "data-analyst", "data-architect", "data"],
    "data_engineer": ["data-engineer", "data-architect", "dataops-mlops-engineer", "data"],
    "data_scientist": ["data-scientist", "data-analyst", "data"],
    "devops": ["devops", "devops-engineer", "devsecops-engineer", "sysops-engineer",
               "site-reliability-engineer-sre", "cloud-engineer"],
    "ai_engineer": ["ai-machine-learning-engineer", "ai-architect", "ai_engineer",
                    "computer-vision-engineer", "dataops-mlops-engineer"],
    "ml_engineer": ["ai-machine-learning-engineer", "dataops-mlops-engineer"],
    "mobile": ["mobile-application-developer", "mobile"],
}


def _role_alias_list(role: str | None) -> list[str]:
    """Return all role aliases used in skill_trends table for a given short role."""
    if not role:
        return []
    return ROLE_ALIASES_FOR_TRENDS.get(role.lower(), [role])


# ─── CV input + output dataclasses ────────────────────────────────────────────

@dataclass
class CVSkillInput:
    """One CV skill, optionally with the most-recent year of use from NER."""
    name: str
    last_used_year: Optional[int] = None  # e.g. 2025

    def recency(self, today_year: int) -> float:
        if self.last_used_year is None:
            return 0.7  # average — see chuong3/3.2.6 (NER fallback)
        years = today_year - self.last_used_year
        if years <= 1:
            return 1.0
        if years <= 2:
            return 0.7
        if years <= 5:
            return 0.4
        return 0.1


@dataclass
class SkillContribution:
    skill: str
    importance: float
    trend: float
    recency: float
    contribution: float  # 100 * w·trend·recency / denominator


@dataclass
class FreshnessResult:
    score: float
    role: str
    snapshot_date: date
    contributions: list[SkillContribution] = field(default_factory=list)
    ideal_skills: list[str] = field(default_factory=list)
    missing_ideal: list[str] = field(default_factory=list)  # ideal skills not in CV
    cold_start: bool = False  # True if trend data is too thin


# ─── Engine ───────────────────────────────────────────────────────────────────


class CVFreshnessEngine:
    """Compute Freshness Score from skill_trends + ontology."""

    def __init__(self, ontology: SkillOntology):
        self.ontology = ontology
        self._requires_indegree_max = self._compute_requires_indegree_max()

    # ── importance components ──

    def _compute_requires_indegree_max(self) -> int:
        """Max in-degree of REQUIRES across the graph — used to normalize to [0,1]."""
        max_deg = 1
        for skill_lower, by_rel in self.ontology.graph_in.items():
            deg = len(by_rel.get(REQUIRES, []))
            if deg > max_deg:
                max_deg = deg
        return max_deg

    def _is_part_of_role(self, skill: str, role: str) -> bool:
        """True if skill PART_OF a domain that maps to this role."""
        skill_lower = skill.lower()
        # Map our role name to ontology domains.
        role_domains = _ROLE_TO_DOMAINS.get(role.lower(), set())
        targets = self.ontology.graph_out.get(skill_lower, {}).get(PART_OF, [])
        for tgt in targets:
            if tgt in role_domains:
                return True
        # Fallback: skill's category matches one of the role's preferred categories.
        cat = self.ontology.skill_to_category.get(skill_lower)
        return cat in role_domains

    def _requires_indegree(self, skill: str) -> float:
        deg = len(self.ontology.graph_in.get(skill.lower(), {}).get(REQUIRES, []))
        return deg / self._requires_indegree_max

    def _importance(self, skill: str, role: str, freq_norm: float) -> float:
        """w_r(s) ∈ [0, 1]."""
        return (
            ALPHA_PART_OF * (1.0 if self._is_part_of_role(skill, role) else 0.0)
            + ALPHA_REQUIRES_INDEGREE * self._requires_indegree(skill)
            + ALPHA_FREQUENCY * freq_norm
        )

    # ── trend & frequency from skill_trends ──

    def _load_trend_data(
        self, db: Session, role: str, snapshot_date: date
    ) -> tuple[dict[str, int], dict[str, float], bool]:
        """Returns (current_demand_by_skill, freq_norm_by_skill, cold_start).

        Aggregates across all role aliases (vd `backend` → `backend-developer`)
        và SUM demand_count nếu skill xuất hiện ở nhiều alias.
        """
        aliases = _role_alias_list(role)
        if not aliases:
            return {}, {}, True

        # Current week demand: aggregate qua tất cả role aliases ở snapshot mới nhất.
        sql_current = text(
            """
            SELECT skill_canonical, SUM(demand_count) AS cnt
            FROM skill_trends
            WHERE window_days = :window
              AND snapshot_date = (
                  SELECT MAX(snapshot_date) FROM skill_trends
                  WHERE window_days = :window
                    AND snapshot_date <= :snap
                    AND role = ANY(:roles)
              )
              AND role = ANY(:roles)
            GROUP BY skill_canonical
            """
        )
        rows = db.execute(
            sql_current,
            {"window": TREND_WINDOW_DAYS, "snap": snapshot_date, "roles": aliases},
        ).fetchall()
        current: dict[str, int] = {r[0]: int(r[1]) for r in rows}

        if not current:
            logger.warning(
                "freshness: no skill_trends for role=%s aliases=%s snap=%s",
                role, aliases, snapshot_date,
            )
            return {}, {}, True

        # Normalize freq to [0, 1] using max demand in the snapshot.
        max_demand = max(current.values()) or 1
        freq_norm = {sk: cnt / max_demand for sk, cnt in current.items()}

        # Cold-start detection: < 4 distinct snapshots historically.
        sql_history_count = text(
            """
            SELECT COUNT(DISTINCT snapshot_date) FROM skill_trends
            WHERE window_days = :window
              AND role = ANY(:roles)
              AND snapshot_date <= :snap
            """
        )
        n_snaps = db.execute(
            sql_history_count,
            {"window": TREND_WINDOW_DAYS, "snap": snapshot_date, "roles": aliases},
        ).scalar() or 0
        cold_start = n_snaps < TREND_LOOKBACK_WEEKS

        return current, freq_norm, cold_start

    def _trend_for_skill(
        self, db: Session, skill: str, role: str, snapshot_date: date, current: dict[str, int]
    ) -> float:
        """trend(s, t) = clip(d_t / MA_4_prev, 0.5, 1.5)."""
        d_t = current.get(skill, 0)
        if d_t == 0:
            return TREND_CLIP_LOW

        # MA over the 4 previous weekly snapshots strictly before snapshot_date.
        # Use role aliases (vd `backend` → `backend-developer`) — sum demand
        # across aliases per snapshot, then average.
        aliases = _role_alias_list(role)
        sql = text(
            """
            SELECT AVG(snap_total) FROM (
                SELECT SUM(demand_count) AS snap_total FROM skill_trends
                WHERE skill_canonical = :sk
                  AND window_days = :window
                  AND role = ANY(:roles)
                  AND snapshot_date < :snap
                GROUP BY snapshot_date
                ORDER BY snapshot_date DESC
                LIMIT :k
            ) sub
            """
        )
        ma = db.execute(
            sql,
            {
                "sk": skill,
                "window": TREND_WINDOW_DAYS,
                "roles": aliases,
                "snap": snapshot_date,
                "k": TREND_LOOKBACK_WEEKS,
            },
        ).scalar()
        if ma is None or ma == 0:
            return 1.0  # no history → neutral
        ratio = d_t / float(ma)
        return max(TREND_CLIP_LOW, min(TREND_CLIP_HIGH, ratio))

    # ── ideal skill set ──

    def _ideal_skills(self, current: dict[str, int]) -> list[str]:
        """Top-K most-demanded canonical skills in the current snapshot."""
        return [
            sk for sk, _ in sorted(current.items(), key=lambda kv: -kv[1])[:IDEAL_TOP_K]
        ]

    # ── public ──

    def compute(
        self,
        db: Session,
        cv_skills: list[CVSkillInput],
        role: str,
        snapshot_date: Optional[date] = None,
        today_year: Optional[int] = None,
    ) -> FreshnessResult:
        snapshot_date = snapshot_date or date.today()
        today_year = today_year or snapshot_date.year

        current, freq_norm, cold_start = self._load_trend_data(db, role, snapshot_date)
        if not current:
            return FreshnessResult(
                score=0.0,
                role=role,
                snapshot_date=snapshot_date,
                cold_start=True,
            )

        ideal = self._ideal_skills(current)
        # Denominator = sum of importance over ideal set.
        denom = 0.0
        for sk in ideal:
            denom += self._importance(sk, role, freq_norm.get(sk, 0.0))
        if denom <= 0:
            denom = 1e-6

        # Canonicalize CV skill names against the ontology.
        contributions: list[SkillContribution] = []
        numerator = 0.0
        cv_skill_set: set[str] = set()
        for cv in cv_skills:
            canon = self.ontology.canonical.get(cv.name.lower(), cv.name)
            cv_skill_set.add(canon)
            w = self._importance(canon, role, freq_norm.get(canon, 0.0))
            tr = self._trend_for_skill(db, canon, role, snapshot_date, current)
            rec = cv.recency(today_year)
            term = w * tr * rec
            numerator += term
            contributions.append(
                SkillContribution(
                    skill=canon,
                    importance=round(w, 4),
                    trend=round(tr, 4),
                    recency=round(rec, 4),
                    contribution=round(100.0 * term / denom, 3),
                )
            )

        score = 100.0 * numerator / denom
        # The formula is unbounded above only if a CV piles up many high-trend skills
        # outside the ideal set. Cap at 100 for UX (per A1 in §3.2.1).
        score = max(0.0, min(100.0, score))

        missing_ideal = [s for s in ideal if s not in cv_skill_set]
        contributions.sort(key=lambda c: -c.contribution)

        return FreshnessResult(
            score=round(score, 2),
            role=role,
            snapshot_date=snapshot_date,
            contributions=contributions,
            ideal_skills=ideal,
            missing_ideal=missing_ideal,
            cold_start=cold_start,
        )


# ─── Persistence helpers (Tuần 11) ────────────────────────────────────────────


def record_history_and_alert(
    db: Session,
    user_id: str,
    result: FreshnessResult,
) -> Optional[dict]:
    """Append result to skill_freshness_history and fire an alert if score
    dropped more than ALERT_DROP_THRESHOLD from the previous snapshot.

    Returns the alert dict if fired, else None. Imports are local so the
    pure-formula `compute()` path stays import-light for unit tests.
    """
    from services.skill_service.models.database import (
        FreshnessHistoryDB, FreshnessAlertDB,
    )

    # Find the most recent prior score for (user, role).
    prev = (
        db.query(FreshnessHistoryDB)
        .filter(
            FreshnessHistoryDB.user_id == user_id,
            FreshnessHistoryDB.role == result.role,
        )
        .order_by(FreshnessHistoryDB.snapshot_date.desc())
        .first()
    )

    db.add(
        FreshnessHistoryDB(
            user_id=user_id,
            role=result.role,
            score=result.score,
            contributions=[c.__dict__ for c in result.contributions],
            cold_start=1 if result.cold_start else 0,
        )
    )

    alert_payload = None
    if prev is not None:
        delta = prev.score - result.score
        if delta > ALERT_DROP_THRESHOLD:
            reason = _summarize_alert_reason(result, prev_score=prev.score)
            alert = FreshnessAlertDB(
                user_id=user_id,
                role=result.role,
                prev_score=prev.score,
                new_score=result.score,
                delta=delta,
                reason=reason,
            )
            db.add(alert)
            alert_payload = {
                "user_id": user_id,
                "role": result.role,
                "prev_score": prev.score,
                "new_score": result.score,
                "delta": delta,
                "reason": reason,
            }
            logger.info(
                "Freshness alert fired user=%s role=%s drop=%.2f -> %.2f",
                user_id, result.role, delta, result.score,
            )
    db.commit()
    return alert_payload


def _summarize_alert_reason(result: FreshnessResult, prev_score: float) -> str:
    """Pick the largest-trend-drop skill in the contribution list as the headline."""
    if not result.contributions:
        return f"Freshness dropped from {prev_score:.1f} to {result.score:.1f}."
    worst = min(result.contributions, key=lambda c: c.trend)
    return (
        f"Freshness dropped from {prev_score:.1f} to {result.score:.1f}. "
        f"Likely cause: '{worst.skill}' trend={worst.trend:.2f} (cooling)."
    )


# ─── Role → ontology PART_OF domain mapping ───────────────────────────────────
# Maps the 5 study roles (Backend, Frontend, Data, DevOps, AI Engineer) to the
# domain names used by PART_OF edges and to category names from SKILL_ONTOLOGY.

_ROLE_TO_DOMAINS: dict[str, set[str]] = {
    "backend": {"Backend Development", "Web Development", "Database"},
    "frontend": {"Frontend Development", "Web Development"},
    "data": {"Data Science", "Data Engineering", "Database"},
    "data_engineer": {"Data Engineering", "Database"},
    "data_scientist": {"Data Science", "ML/AI"},
    "devops": {"DevOps & Infrastructure", "Cloud Platforms"},
    "ai_engineer": {"ML/AI", "Data Science"},
    "ml_engineer": {"ML/AI", "Data Engineering"},
    "fullstack": {"Frontend Development", "Backend Development", "Web Development"},
    "mobile": {"Mobile"},
}


# ══════════════════════════════════════════════════════════════════════════════
#  Multi-criteria CV Freshness Framework — 8 chiều (chuong3/3.2)
# ══════════════════════════════════════════════════════════════════════════════
#
# Freshness = Σ_d ω_d · s_d   với   Σ ω_d = 1   (Weighted Sum Model — §3.2.3)
#
# Tám chiều (mỗi s_d ∈ [0, 100]):
#   1. Skill           — tái dùng CVFreshnessEngine.compute() (skill_trends + ontology)
#   2. Experience      — years_exp / years_target · relevance
#   3. Project         — num_projects / N* · skill_density
#   4. Education        — DEGREE base ± MAJOR
#   5. Achievement     — regex/keyword count
#   6. Language        — regex TOEIC/IELTS/level
#   7. Completeness    — đếm section bắt buộc
#   8. Market Alignment — |S_CV ∩ top-K JD| / K

# ─── Dimension constants (defaults match chuong3/3.2) ─────────────────────────

PROJECT_TARGET = 3            # N* — chuẩn portfolio fresher (§3.2.2 chiều 3)
PROJECT_SKILL_BENCHMARK = 5  # skill/project để skill_density = 1.0

MARKET_ALIGN_TOP_K = 10      # K — top-K skill role (§3.2.2 chiều 8)

# Chiều 4 — Education base score theo DEGREE (§3.2.2)
DEGREE_BASE_SCORE: dict[str, float] = {
    "phd": 100.0,
    "doctor": 100.0,
    "master": 90.0,
    "bachelor": 80.0,
    "engineer": 80.0,      # Kỹ sư ≈ Bachelor
    "diploma": 60.0,
    "associate": 60.0,     # Cao đẳng
    "college": 60.0,
}
DEGREE_DEFAULT_SCORE = 40.0  # "Khác"
MAJOR_ADJUST = 10.0          # ±10 theo MAJOR liên quan domain IT

# Major liên quan IT (boost +10); ngoài danh sách & không rõ → -10/0
_IT_MAJOR_KEYWORDS = (
    "computer", "software", "information", "công nghệ thông tin", "khoa học máy tính",
    "kỹ thuật phần mềm", "hệ thống thông tin", "data", "artificial intelligence",
    "trí tuệ nhân tạo", "an toàn thông tin", "cyber", "it", "cntt", "điện tử",
    "automation", "tự động hóa", "toán tin",
)

# Chiều 5 — Achievement: keyword → điểm/item (cap 100)
ACHIEVEMENT_PATTERNS: list[tuple[str, float]] = [
    (r"\b(olympiad|olympic)\b", 20.0),
    (r"\bhackathon\b", 15.0),
    (r"\b(award|giải nhất|giải nhì|giải ba|giải thưởng|prize|winner|champion)\b", 15.0),
    (r"\b(scholarship|học bổng)\b", 15.0),
    (r"\b(aws|azure|gcp|google cloud)\s*(certified|certification|certificate)?\b", 15.0),
    (r"\b(certified|certification|certificate|chứng chỉ)\b", 10.0),
    (r"\b(publication|paper|báo khoa học|patent|sáng chế)\b", 20.0),
    (r"\b(open[- ]?source|contributor|maintainer)\b", 10.0),
    (r"\b(jlpt|n1|n2|n3|toeic|ielts|toefl)\b", 10.0),
    (r"\b(leetcode|hackerrank|codeforces)\b", 10.0),
]

# Chiều 6 — Language scoring (§3.2.2 chiều 6)
LANG_NATIVE = 100.0
LANG_ADVANCED = 80.0
LANG_INTERMEDIATE = 60.0
LANG_BASIC = 40.0
LANG_NONE = 30.0

# Chiều 7 — Completeness section weights (§3.2.2 chiều 7) — Σ = 100
COMPLETENESS_WEIGHTS: dict[str, float] = {
    "contact": 20.0,
    "summary": 10.0,
    "education": 15.0,
    "experience": 25.0,
    "skills": 20.0,
    "projects": 10.0,
}

# Số năm kinh nghiệm mục tiêu theo seniority (years_target — chiều 2)
SENIORITY_TARGET_YEARS: dict[str, float] = {
    "fresher": 0.0,    # fresher = không yêu cầu kinh nghiệm chuyên môn
    "intern": 0.0,
    "junior": 1.0,
    "mid": 3.0,
    "middle": 3.0,
    "senior": 5.0,
    "lead": 8.0,
    "principal": 10.0,
    "manager": 8.0,
}
DEFAULT_TARGET_YEARS = 3.0
# Điểm tối thiểu cho Experience khi seniority yêu cầu 0 năm (fresher) —
# tránh kéo tổng điểm xuống 0 chỉ vì user là sinh viên mới ra trường.
FRESHER_BASELINE_EXP = 70.0
# Achievement: scale theo số hit (không cộng dồn điểm cố định để tránh
# JLPT match cả "jlpt"+"n3"+"certificate" thành 3 hit).
ACHIEVEMENT_PER_HIT = 18.0  # 4 hit phân biệt → ~72/100
ACHIEVEMENT_CAP = 100.0

# Top skill noise — kỹ năng này thường xuất hiện top JD nhưng không phải
# skill cụ thể (architecture concepts) → bỏ khỏi market alignment.
MARKET_ALIGN_NOISE = {
    "microservices", "agile", "scrum", "rest", "restful", "api",
    "soa", "saas", "ci/cd", "cicd", "tdd", "bdd", "oop",
}


# ─── Trọng số ω_d theo (role, seniority) — Bảng 3.2 ───────────────────────────
# Key = seniority. Tổng mỗi profile = 1.00. Bảng 3.2 nêu 3 cột tiêu biểu
# (Backend junior / Frontend mid / Data Engineer senior); ở đây tổng quát hoá
# theo seniority vì pattern trọng số chủ yếu phụ thuộc seniority.

DIMENSION_ORDER = (
    "skill", "experience", "project", "education",
    "achievement", "language", "completeness", "market_alignment",
)

WEIGHT_PROFILES: dict[str, dict[str, float]] = {
    # junior/fresher — nhấn Project (portfolio bù kinh nghiệm), Experience thấp
    "junior": {
        "skill": 0.25, "experience": 0.10, "project": 0.20, "education": 0.10,
        "achievement": 0.05, "language": 0.05, "completeness": 0.10,
        "market_alignment": 0.15,
    },
    # mid — Experience nhích lên, Education giảm
    "mid": {
        "skill": 0.25, "experience": 0.15, "project": 0.20, "education": 0.05,
        "achievement": 0.05, "language": 0.05, "completeness": 0.10,
        "market_alignment": 0.15,
    },
    # senior/lead — Experience cao nhất, Project + Completeness giảm
    "senior": {
        "skill": 0.25, "experience": 0.25, "project": 0.10, "education": 0.10,
        "achievement": 0.05, "language": 0.05, "completeness": 0.05,
        "market_alignment": 0.15,
    },
}
# Alias seniority → profile
_SENIORITY_TO_PROFILE = {
    "fresher": "junior", "junior": "junior", "intern": "junior",
    "mid": "mid", "middle": "mid", "intermediate": "mid",
    "senior": "senior", "lead": "senior", "principal": "senior", "staff": "senior",
}


def weights_for(seniority: Optional[str]) -> dict[str, float]:
    """Trả về dict trọng số ω_d cho seniority (mặc định junior)."""
    profile = _SENIORITY_TO_PROFILE.get((seniority or "junior").lower(), "junior")
    return dict(WEIGHT_PROFILES[profile])


# ─── Input / output ───────────────────────────────────────────────────────────


@dataclass
class CVProfileInput:
    """Toàn bộ thông tin CV cần cho 8 chiều. Các trường ngoài `skills` đều
    optional — chiều nào thiếu input sẽ rơi về baseline thay vì lỗi."""
    skills: list[CVSkillInput] = field(default_factory=list)
    role: str = "backend"
    seniority: str = "junior"

    # Chiều 2 — Experience
    years_experience: Optional[float] = None
    past_job_titles: list[str] = field(default_factory=list)

    # Chiều 3 — Project
    num_projects: int = 0
    project_skill_counts: list[int] = field(default_factory=list)  # #skill mỗi project

    # Chiều 4 — Education
    degree: Optional[str] = None     # "Bachelor" / "Master" / "Cao đẳng" / ...
    major: Optional[str] = None

    # Chiều 5 / 6 — Achievement / Language (raw text scan)
    achievement_text: str = ""
    language_text: str = ""

    # Chiều 7 — Completeness (section nào có mặt)
    has_contact: bool = False
    has_summary: bool = False
    has_education: bool = False
    has_experience: bool = False
    has_skills: bool = False
    has_projects: bool = False


@dataclass
class DimensionDetail:
    """Structured breakdown for a dimension — feeds the (i) popup on dashboard.

    `summary` is the 1-line headline shown inline next to the bar.
    The remaining fields are shown in a Dialog when user clicks the info icon.
    All fields are optional so simpler dimensions don't need to fill everything.
    """
    summary: str = ""                       # 1-line headline
    formula: str = ""                       # vd "100 × 0.13 × 1.00 = 13.0"
    inputs: list[dict] = field(default_factory=list)        # [{label, value, hint?}]
    breakdown: list[str] = field(default_factory=list)      # bullets giải thích vì sao
    tips: list[str] = field(default_factory=list)           # action items


@dataclass
class DimensionScore:
    name: str
    score: float          # s_d ∈ [0, 100]
    weight: float         # ω_d
    weighted: float       # ω_d · s_d
    detail: DimensionDetail = field(default_factory=DimensionDetail)


@dataclass
class MultiCriteriaResult:
    score: float                       # Freshness tổng ∈ [0, 100]
    role: str
    seniority: str
    snapshot_date: date
    dimensions: list[DimensionScore] = field(default_factory=list)
    skill_result: Optional[FreshnessResult] = None  # chi tiết chiều Skill
    cold_start: bool = False


# ─── Engine ────────────────────────────────────────────────────────────────────


class MultiCriteriaFreshnessEngine:
    """8-chiều Weighted Sum Model. Compose CVFreshnessEngine cho chiều Skill +
    Market Alignment (cần skill_trends), tự tính 6 chiều còn lại."""

    def __init__(self, ontology: SkillOntology, skill_engine: Optional[CVFreshnessEngine] = None):
        self.ontology = ontology
        self.skill_engine = skill_engine or CVFreshnessEngine(ontology)

    # ── chiều 1: Skill ──
    def _dim_skill(
        self, db: Session, profile: CVProfileInput, snapshot_date: date, today_year: int
    ) -> tuple[float, FreshnessResult]:
        res = self.skill_engine.compute(
            db=db, cv_skills=profile.skills, role=profile.role,
            snapshot_date=snapshot_date, today_year=today_year,
        )
        return res.score, res

    # ── chiều 2: Experience ──
    def _dim_experience(self, profile: CVProfileInput) -> tuple[float, DimensionDetail]:
        if profile.years_experience is None:
            return 50.0, DimensionDetail(
                summary="Chưa quét được số năm KN — tạm chấm 50/100.",
                formula=r"\text{baseline (no data)} = 50",
                inputs=[{"label": "years_experience", "value": "null"}],
                breakdown=["⚠ Hệ thống không đọc được số năm KN từ CV (thiếu DATE entity).",
                           "ℹ Có thể do CV không ghi rõ mốc tháng/năm ở mỗi job."],
                tips=["Ghi rõ format 'Jan 2024 - Present' hoặc '01/2024 - hiện tại' ở mỗi job.",
                      "Tránh viết chung chung như '2 năm tại công ty A'."],
            )

        seniority_l = (profile.seniority or "").lower()
        target = SENIORITY_TARGET_YEARS.get(seniority_l, DEFAULT_TARGET_YEARS)
        relevance = self._relevance_factor(profile)
        seniority_label = (profile.seniority or "mục tiêu").upper()
        yrs = profile.years_experience

        if target <= 0:
            bonus = min(30.0, yrs * 30.0)
            base_score = FRESHER_BASELINE_EXP + bonus
            score = max(0.0, min(100.0, base_score * relevance))
            return score, DimensionDetail(
                summary=f"Fresher (target 0 năm) — nền {FRESHER_BASELINE_EXP:.0f} + {bonus:.0f} bonus × relevance {relevance:.2f}",
                formula=(rf"\text{{score}} = (\underbrace{{{FRESHER_BASELINE_EXP:.0f}}}_{{\text{{baseline}}}} + "
                         rf"\underbrace{{{bonus:.1f}}}_{{\text{{bonus}}}}) \cdot "
                         rf"\underbrace{{{relevance:.2f}}}_{{\text{{relevance}}}} = {score:.1f}"),
                inputs=[
                    {"label": "Cấp bậc mục tiêu", "value": seniority_label, "hint": "không yêu cầu năm KN"},
                    {"label": "Số năm KN thực có", "value": f"{yrs:.1f} năm"},
                    {"label": "Độ liên quan job title", "value": f"{relevance*100:.0f}%"},
                ],
                breakdown=[
                    f"ℹ Cấp {seniority_label} không yêu cầu năm KN — nền tảng {FRESHER_BASELINE_EXP:.0f}đ.",
                    (f"✓ Bonus +{bonus:.1f}đ cho {yrs:.1f} năm KN intern/part-time bạn đang có."
                     if yrs > 0 else f"ℹ Chưa có KN intern/part-time → không có bonus."),
                    (f"✓ Job title cũ ({', '.join(profile.past_job_titles[:2])}) khớp role {profile.role} (×{relevance:.2f})."
                     if relevance >= 0.8 and profile.past_job_titles else
                     f"⚠ Job title cũ chưa khớp role {profile.role} → relevance chỉ {relevance:.2f} (kéo điểm xuống)."
                     if profile.past_job_titles else
                     f"ℹ Không phát hiện JOB_TITLE entity → relevance = {relevance:.2f} (trung tính)."),
                ],
                tips=([] if relevance >= 0.8 else
                      [f"Đổi chức danh job cũ cho khớp role '{profile.role}' (vd 'Backend Intern' thay vì 'Software Intern')."]) +
                     (["Liệt kê thêm các project/freelance để bonus tăng lên 30đ."] if yrs < 1.0 else []),
            )

        coverage = min(1.0, yrs / target)
        score = 100.0 * coverage * relevance
        return score, DimensionDetail(
            summary=f"{yrs:.1f}/{target:.0f} năm KN ({coverage*100:.0f}% target) × relevance {relevance:.2f}",
            formula=(rf"\text{{score}} = 100 \cdot \min\!\left(1,\ \dfrac{{{yrs:.1f}}}{{{target:.0f}}}\right) "
                     rf"\cdot {relevance:.2f} = 100 \cdot {coverage:.2f} \cdot {relevance:.2f} = {score:.1f}"),
            inputs=[
                {"label": "Số năm KN", "value": f"{yrs:.1f} năm"},
                {"label": "Target cho {seniority_label}".format(seniority_label=seniority_label), "value": f"{target:.0f} năm"},
                {"label": "Coverage", "value": f"{coverage*100:.0f}%"},
                {"label": "Relevance job title", "value": f"{relevance*100:.0f}%"},
            ],
            breakdown=[
                (f"✓ Đạt đủ kỳ vọng KN cho cấp {seniority_label} ({yrs:.1f}/{target:.0f} năm)." if coverage >= 1.0 else
                 f"⚠ Mới đạt {coverage*100:.0f}% kỳ vọng — còn thiếu {(target - yrs):.1f} năm cho cấp {seniority_label}." if coverage < 0.5 else
                 f"ℹ Đạt {coverage*100:.0f}% kỳ vọng KN ({yrs:.1f}/{target:.0f} năm) — gần đủ."),
                (f"✓ Chức danh cũ ({', '.join(profile.past_job_titles[:2])}) khớp role {profile.role}."
                 if relevance >= 0.8 and profile.past_job_titles else
                 f"⚠ Chức danh cũ chưa thật khớp role {profile.role} (relevance {relevance:.0%})."
                 if profile.past_job_titles else
                 "ℹ Không tìm thấy JOB_TITLE trong CV → relevance trung tính (75%)."),
            ],
            tips=([f"Cần thêm {(target - yrs):.1f} năm KN nữa để đạt 100% coverage."] if coverage < 1.0 else []) +
                 ([f"Đổi tên chức danh job cũ cho khớp role '{profile.role}' để nâng relevance."] if relevance < 0.8 else []),
        )

    def _relevance_factor(self, profile: CVProfileInput) -> float:
        """∈ [0.5, 1.0] — 1.0 nếu job title cũ khớp role mục tiêu, 0.5 nếu không."""
        if not profile.past_job_titles:
            return 0.75  # không có title → trung tính
        role_tokens = set(re.split(r"[\s_/]+", profile.role.lower()))
        domains = {d.lower() for d in _ROLE_TO_DOMAINS.get(profile.role.lower(), set())}
        domain_tokens = set()
        for d in domains:
            domain_tokens.update(d.split())
        keys = role_tokens | domain_tokens
        for title in profile.past_job_titles:
            t = title.lower()
            if any(k and k in t for k in keys):
                return 1.0
        return 0.5

    # ── chiều 3: Project ──
    def _dim_project(self, profile: CVProfileInput) -> tuple[float, DimensionDetail]:
        seniority_l = (profile.seniority or "junior").lower()
        if seniority_l in ("fresher", "intern", "junior"):
            target = PROJECT_TARGET
        else:
            target = max(2, PROJECT_TARGET - 1)

        if profile.num_projects <= 0:
            return 0.0, DimensionDetail(
                summary=f"0 dự án — cần ít nhất {target} để đạt chuẩn.",
                formula=r"\text{score} = 0 \quad \text{(no projects)}",
                inputs=[{"label": "Số dự án", "value": "0"}, {"label": "Target", "value": str(target)}],
                breakdown=["✗ Không tìm thấy dự án nào trong CV.",
                           "ℹ Dự án là bằng chứng năng lực mạnh nhất, đặc biệt cho fresher/junior."],
                tips=[f"Thêm tối thiểu {target} dự án (cá nhân/freelance/open source).",
                      "Mỗi dự án nên có: tên, stack 3-5 công nghệ, mô tả vai trò + kết quả đo lường."],
            )

        count_factor = min(1.0, profile.num_projects / target)
        if profile.project_skill_counts:
            avg_skills = sum(profile.project_skill_counts) / len(profile.project_skill_counts)
        else:
            avg_skills = PROJECT_SKILL_BENCHMARK * 0.6
        density_raw = avg_skills / PROJECT_SKILL_BENCHMARK
        density = max(0.4, min(1.0, density_raw))
        score = 100.0 * count_factor * density

        bullets = [
            (f"✓ Đủ số dự án chuẩn ({profile.num_projects}/{target})." if profile.num_projects >= target else
             f"⚠ Mới có {profile.num_projects}/{target} dự án — cần thêm {target - profile.num_projects} cho đủ chuẩn."),
            (f"✓ Stack dày ({avg_skills:.1f} tech/dự án — chuẩn {PROJECT_SKILL_BENCHMARK})." if density >= 0.8 else
             f"⚠ Stack thưa ({avg_skills:.1f} tech/dự án — chuẩn {PROJECT_SKILL_BENCHMARK}) — chưa thể hiện hết tech đã dùng."),
        ]
        tips: list[str] = []
        if profile.num_projects < target:
            tips.append(f"Thêm {target - profile.num_projects} dự án nữa để đạt count_factor = 1.0.")
        if density < 0.8:
            tips.append("Liệt kê chi tiết Stack (Database, Message Queue, CI/CD, monitoring…) trong từng dự án.")
        if not tips:
            tips.append("Đã đạt chuẩn — tiếp tục thêm metric kết quả (vd 'giảm latency 40%') để gây ấn tượng mạnh hơn.")

        return score, DimensionDetail(
            summary=f"{profile.num_projects} dự án × {avg_skills:.1f} tech/dự án = {score:.1f}/100",
            formula=(rf"\text{{score}} = 100 \cdot \underbrace{{{count_factor:.2f}}}_{{\text{{count\_factor}}}} \cdot "
                     rf"\underbrace{{{density:.2f}}}_{{\text{{density}}}} = {score:.1f}"),
            inputs=[
                {"label": "Số dự án", "value": str(profile.num_projects), "hint": f"target {target}"},
                {"label": "Avg công nghệ/dự án", "value": f"{avg_skills:.1f}", "hint": f"benchmark {PROJECT_SKILL_BENCHMARK}"},
                {"label": "count_factor", "value": f"{count_factor:.2f}"},
                {"label": "density", "value": f"{density:.2f}", "hint": "floor 0.4"},
            ],
            breakdown=bullets,
            tips=tips,
        )

    # ── chiều 4: Education ──
    def _dim_education(self, profile: CVProfileInput) -> tuple[float, DimensionDetail]:
        if not profile.degree:
            return 40.0, DimensionDetail(
                summary="Không tìm thấy DEGREE trong CV — tạm chấm 40/100 (baseline 'Khác').",
                formula=rf"\text{{score}} = \text{{DEGREE\_DEFAULT}} = {DEGREE_DEFAULT_SCORE:.0f}",
                inputs=[{"label": "Degree", "value": "(không có)"}],
                breakdown=["✗ Không tìm thấy bằng cấp trong CV.",
                           "⚠ ATS doanh nghiệp lọc theo từ khoá bằng cấp — thiếu sẽ bị loại."],
                tips=["Ghi rõ 'Bachelor of Science', 'Cử nhân CNTT', 'Master of Engineering'…",
                      "Format: <bằng cấp>, <chuyên ngành>, <trường>, <năm tốt nghiệp>."],
            )
        base = DEGREE_DEFAULT_SCORE
        matched_key = "khác"
        deg_l = profile.degree.lower()
        for key, val in DEGREE_BASE_SCORE.items():
            if key in deg_l:
                base = val
                matched_key = key
                break
        adjust = 0.0
        major_status = "không có thông tin chuyên ngành"
        if profile.major:
            major_l = profile.major.lower()
            if any(k in major_l for k in _IT_MAJOR_KEYWORDS):
                adjust = MAJOR_ADJUST
                major_status = f"khớp khối CNTT ('{profile.major}') → +{MAJOR_ADJUST:.0f}"
            else:
                adjust = -MAJOR_ADJUST
                major_status = f"không khớp khối CNTT ('{profile.major}') → -{MAJOR_ADJUST:.0f}"
        score = max(0.0, min(100.0, base + adjust))
        tips: list[str] = []
        if not profile.major:
            tips.append("Bổ sung chuyên ngành ('in Computer Science', 'ngành CNTT') để nhận +10đ.")
        if base < 80:
            tips.append("Bằng cấp cao hơn (Bachelor/Master) sẽ nâng baseline lên 80-90đ.")
        return score, DimensionDetail(
            summary=f"{profile.degree} ({base:.0f}) {('+ ' + str(int(adjust))) if adjust > 0 else (str(int(adjust))) if adjust < 0 else ''} = {score:.0f}/100",
            formula=(rf"\text{{score}} = \underbrace{{{base:.0f}}}_{{\text{{DEGREE\_BASE[{matched_key}]}}}} "
                     rf"{'+' if adjust >= 0 else '-'} \underbrace{{{abs(adjust):.0f}}}_{{\text{{major\_adjust}}}} = {score:.0f}"),
            inputs=[
                {"label": "Bằng cấp", "value": profile.degree, "hint": f"baseline {base:.0f}"},
                {"label": "Chuyên ngành", "value": profile.major or "—", "hint": major_status},
            ],
            breakdown=[
                f"✓ Bằng '{profile.degree}' (tier {matched_key}) → nền {base:.0f}/100.",
                (f"✓ {major_status}." if adjust > 0 else
                 f"⚠ {major_status}." if adjust < 0 else
                 f"ℹ {major_status}."),
            ],
            tips=tips,
        )

    # ── chiều 5: Achievement ──
    def _dim_achievement(self, profile: CVProfileInput) -> tuple[float, DimensionDetail]:
        text_l = (profile.achievement_text or "").lower()
        if not text_l.strip():
            return 0.0, DimensionDetail(
                summary="Không có thành tích/chứng chỉ nào.",
                formula=r"\text{score} = 0 \quad \text{(no achievement text)}",
                inputs=[{"label": "achievement_text", "value": "(rỗng)"}],
                breakdown=["✗ Chưa có chứng chỉ/giải thưởng/đóng góp open source nào.",
                           "ℹ Hệ thống quét section Certifications, Awards, Achievements + summary."],
                tips=["Bổ sung chứng chỉ (AWS Certified, JLPT, IELTS) nếu có.",
                      "List Hackathon, đóng góp Open Source, LeetCode/Codeforces rating.",
                      "Học bổng, giải thưởng cấp trường/quốc gia cũng được tính."],
            )
        distinct_hits = 0
        labels: list[str] = []
        for pat, _pts in ACHIEVEMENT_PATTERNS:
            if re.search(pat, text_l):
                distinct_hits += 1
                first = re.sub(r"\\b|\(|\)|\?|\:|\.|\*|\+", "", pat).split("|")[0].strip()
                if first:
                    labels.append(first)
        score = min(ACHIEVEMENT_CAP, distinct_hits * ACHIEVEMENT_PER_HIT)
        return score, DimensionDetail(
            summary=f"{distinct_hits} loại thành tích × {ACHIEVEMENT_PER_HIT:.0f}đ = {score:.0f}/100",
            formula=(rf"\text{{score}} = \min\!\left({ACHIEVEMENT_CAP:.0f},\ "
                     rf"\underbrace{{{distinct_hits}}}_{{\text{{distinct hits}}}} \cdot "
                     rf"\underbrace{{{ACHIEVEMENT_PER_HIT:.0f}}}_{{\text{{pts/hit}}}}\right) = {score:.0f}"),
            inputs=[
                {"label": "Số loại distinct", "value": str(distinct_hits)},
                {"label": "Điểm/loại", "value": f"{ACHIEVEMENT_PER_HIT:.0f}"},
                {"label": "Mẫu phát hiện", "value": ", ".join(labels[:5]) or "—"},
            ],
            breakdown=[
                f"✓ Phát hiện {distinct_hits} LOẠI thành tích khác nhau: {', '.join(labels[:5])}.",
                f"ℹ Mỗi loại chỉ tính 1 lần — tránh phồng điểm khi 1 chứng chỉ match nhiều keyword.",
                (f"⚠ Cần thêm {int((ACHIEVEMENT_CAP - score) // ACHIEVEMENT_PER_HIT) + 1} loại nữa để đạt trần {ACHIEVEMENT_CAP:.0f}/100."
                 if score < ACHIEVEMENT_CAP else f"✓ Đã đạt trần điểm {ACHIEVEMENT_CAP:.0f}/100."),
            ],
            tips=([] if score >= ACHIEVEMENT_CAP else [
                f"Thêm {int((ACHIEVEMENT_CAP - score) // ACHIEVEMENT_PER_HIT) + 1} loại thành tích khác để đạt trần.",
                "Categories thiếu: paper/patent, scholarship, hackathon, cloud cert (AWS/Azure/GCP), open source."
            ]),
        )

    # ── chiều 6: Language ──
    def _dim_language(self, profile: CVProfileInput) -> tuple[float, DimensionDetail]:
        text_l = (profile.language_text or "").lower()
        tier_table = (
            f"Bảng quy đổi: Native={LANG_NATIVE:.0f} | Advanced={LANG_ADVANCED:.0f} | "
            f"Intermediate={LANG_INTERMEDIATE:.0f} | Basic={LANG_BASIC:.0f} | None={LANG_NONE:.0f}."
        )
        if not text_l.strip():
            return LANG_NONE, DimensionDetail(
                summary=f"Không đề cập ngoại ngữ → mặc định {LANG_NONE:.0f}/100.",
                formula=rf"\text{{score}} = \text{{LANG\_NONE}} = {LANG_NONE:.0f}",
                inputs=[{"label": "language_text", "value": "(rỗng)"}],
                breakdown=["✗ CV không có section Languages.",
                           f"ℹ {tier_table}"],
                tips=["Thêm: 'English: Professional Working Proficiency', 'JLPT N3', 'TOEIC 750'…"],
            )

        def build(score: float, tier: str, evidence: str, tips: list[str]) -> DimensionDetail:
            return DimensionDetail(
                summary=f"{evidence} → tier {tier} ({score:.0f}/100)",
                formula=rf"\text{{score}} = \text{{tier}}(\text{{{tier}}}) = {score:.0f}",
                inputs=[{"label": "Evidence trong CV", "value": evidence}, {"label": "Tier", "value": tier}],
                breakdown=[f"✓ CV match: {evidence} → tier {tier}.",
                           f"ℹ {tier_table}"],
                tips=tips,
            )

        # IELTS
        m = re.search(r"ielts\s*[:\-]?\s*(\d(?:\.\d)?)", text_l)
        if m:
            band = float(m.group(1))
            if band >= 7.0:
                return LANG_NATIVE, build(LANG_NATIVE, "Native", f"IELTS {band}",
                    ["Đã ở tier cao nhất."])
            if band >= 6.0:
                return LANG_ADVANCED, build(LANG_ADVANCED, "Advanced", f"IELTS {band}",
                    [f"Cần IELTS ≥ 7.0 để lên Native (+{LANG_NATIVE - LANG_ADVANCED:.0f}đ)."])
            return LANG_INTERMEDIATE, build(LANG_INTERMEDIATE, "Intermediate", f"IELTS {band}",
                [f"Cần IELTS ≥ 6.0 để lên Advanced (+{LANG_ADVANCED - LANG_INTERMEDIATE:.0f}đ)."])
        # TOEIC
        m = re.search(r"toeic\s*[:\-]?\s*(\d{3,4})", text_l)
        if m:
            sc = int(m.group(1))
            if sc >= 800:
                return LANG_NATIVE, build(LANG_NATIVE, "Native", f"TOEIC {sc}", ["Đã ở tier cao nhất."])
            if sc >= 600:
                return LANG_ADVANCED, build(LANG_ADVANCED, "Advanced", f"TOEIC {sc}",
                    [f"Cần TOEIC ≥ 800 để lên Native."])
            if sc >= 450:
                return LANG_INTERMEDIATE, build(LANG_INTERMEDIATE, "Intermediate", f"TOEIC {sc}",
                    [f"Cần TOEIC ≥ 600 để lên Advanced."])
            return LANG_BASIC, build(LANG_BASIC, "Basic", f"TOEIC {sc}",
                [f"Cần TOEIC ≥ 450 để lên Intermediate."])
        # JLPT
        m = re.search(r"jlpt\s*[:\-]?\s*(n[1-5])|\bn[1-5]\b", text_l)
        if m:
            level = (m.group(1) or m.group(0)).lower()
            if level in ("n1", "n2"):
                return LANG_NATIVE, build(LANG_NATIVE, "Native", f"JLPT {level.upper()}", ["Đã ở tier cao nhất."])
            if level == "n3":
                return LANG_ADVANCED, build(LANG_ADVANCED, "Advanced", "JLPT N3",
                    [f"Cần JLPT N2 để lên Native (+{LANG_NATIVE - LANG_ADVANCED:.0f}đ)."])
            if level in ("n4", "n5"):
                return LANG_INTERMEDIATE, build(LANG_INTERMEDIATE, "Intermediate", f"JLPT {level.upper()}",
                    [f"Cần JLPT N3 để lên Advanced."])
        # Keyword tier
        if re.search(r"\b(native|fluent|bản ngữ|thành thạo|bilingual|full professional proficiency)\b", text_l):
            return LANG_NATIVE, build(LANG_NATIVE, "Native", "keyword Native/Fluent/Bilingual", ["Đã ở tier cao nhất."])
        if re.search(r"\b(advanced|nâng cao|professional working proficiency)\b", text_l):
            return LANG_ADVANCED, build(LANG_ADVANCED, "Advanced", "keyword Advanced/Professional",
                ["Bổ sung điểm thi cụ thể (IELTS/TOEIC) để củng cố đánh giá."])
        if re.search(r"\b(intermediate|trung cấp|khá|limited working proficiency)\b", text_l):
            return LANG_INTERMEDIATE, build(LANG_INTERMEDIATE, "Intermediate", "keyword Intermediate/Khá", [])
        if re.search(r"\b(basic|cơ bản|beginner|elementary)\b", text_l):
            return LANG_BASIC, build(LANG_BASIC, "Basic", "keyword Basic/Cơ bản",
                ["Đầu tư học để lên Intermediate — phổ biến nhất trong tin tuyển dụng."])

        return LANG_NONE, DimensionDetail(
            summary=f"CV có mention ngoại ngữ nhưng không xác định được tier → {LANG_NONE:.0f}/100.",
            formula=rf"\text{{score}} = \text{{LANG\_NONE}} = {LANG_NONE:.0f}",
            inputs=[{"label": "language_text", "value": (profile.language_text or "")[:80]}],
            breakdown=["⚠ Có mention ngoại ngữ nhưng không match được tier (IELTS/TOEIC/JLPT/keyword chuẩn).",
                       f"ℹ {tier_table}"],
            tips=["Bổ sung dạng chuẩn: 'IELTS 6.5', 'TOEIC 750', 'JLPT N3', 'Professional Working Proficiency'."],
        )

    # ── chiều 7: Completeness ──
    def _dim_completeness(self, profile: CVProfileInput) -> tuple[float, DimensionDetail]:
        present = {
            "Contact": profile.has_contact,
            "Summary": profile.has_summary,
            "Education": profile.has_education,
            "Experience": profile.has_experience,
            "Skills": profile.has_skills,
            "Projects": profile.has_projects,
        }
        weight_map = {k: COMPLETENESS_WEIGHTS[k.lower()] for k in present}
        score = min(100.0, sum(weight_map[k] for k, ok in present.items() if ok))
        missing = [k for k, ok in present.items() if not ok]
        section_bullets = [f"{'✓' if ok else '✗'} {k} (+{weight_map[k]:.0f}đ)" for k, ok in present.items()]
        return score, DimensionDetail(
            summary=(f"Đủ 6/6 section ({score:.0f}/100)" if not missing
                     else f"Có {6 - len(missing)}/6 section, thiếu: {', '.join(missing)} → {score:.0f}/100"),
            formula=(rf"\text{{score}} = \sum_{{s \in \text{{sections}}}} w_s \cdot \mathbb{{1}}[s \in \text{{CV}}] "
                     rf"= {score:.0f}"),
            inputs=[{"label": k, "value": "✓" if ok else "✗", "hint": f"+{weight_map[k]:.0f}đ nếu có"}
                    for k, ok in present.items()],
            breakdown=section_bullets,
            tips=([f"Bổ sung section '{m}' để +{weight_map[m]:.0f}đ." for m in missing]
                  if missing else ["Đã đủ — duy trì khi update CV mới."]),
        )

    # ── chiều 8: Market Alignment ──
    def _dim_market_alignment(
        self, db: Session, profile: CVProfileInput, snapshot_date: date
    ) -> tuple[float, DimensionDetail]:
        current, _freq, _cold = self.skill_engine._load_trend_data(
            db, profile.role, snapshot_date
        )
        if not current:
            return 0.0, DimensionDetail(
                summary="Chưa đủ dữ liệu thị trường để đánh giá.",
                formula=r"\text{N/A} \quad \text{(no skill\_trends data)}",
                inputs=[{"label": "snapshot_date", "value": snapshot_date.isoformat()}],
                breakdown=["⚠ Chưa có dữ liệu thị trường cho role này.",
                           "ℹ Cần chạy crawler aggregator để build top-K skills."],
                tips=["Chờ batch crawler tiếp theo (chạy weekly)."],
            )
        filtered = [(sk, cnt) for sk, cnt in current.items() if sk.lower() not in MARKET_ALIGN_NOISE]
        top_k = [sk for sk, _ in sorted(filtered, key=lambda kv: -kv[1])[:MARKET_ALIGN_TOP_K]]
        top_set = {s.lower() for s in top_k}
        cv_canon = {self.ontology.canonical.get(s.name.lower(), s.name).lower() for s in profile.skills}
        matched = sorted(cv_canon & top_set)
        missing = [s for s in top_k if s.lower() not in cv_canon]
        hit = len(matched)
        score = 100.0 * hit / MARKET_ALIGN_TOP_K
        return score, DimensionDetail(
            summary=f"Khớp {hit}/{MARKET_ALIGN_TOP_K} top skill thị trường cho role {profile.role}.",
            formula=(rf"\text{{score}} = 100 \cdot \dfrac{{|\,S_{{\text{{CV}}}} \cap S_{{\text{{top-K}}}}|}}"
                     rf"{{|\,S_{{\text{{top-K}}}}|}} = 100 \cdot \dfrac{{{hit}}}{{{MARKET_ALIGN_TOP_K}}} = {score:.0f}"),
            inputs=[
                {"label": "Role", "value": profile.role},
                {"label": "Top-K skills thị trường", "value": ", ".join(top_k) or "—"},
                {"label": "Skill khớp trong CV", "value": ", ".join(matched) or "(không có)"},
                {"label": "Skill còn thiếu", "value": ", ".join(missing[:5]) or "—"},
            ],
            breakdown=[
                (f"✓ Khớp {hit}/{MARKET_ALIGN_TOP_K} top skill thị trường ({', '.join(matched[:3])}…)."
                 if matched else f"✗ Chưa khớp skill nào trong top {MARKET_ALIGN_TOP_K} thị trường."),
                (f"⚠ Còn {len(missing)} top skill chưa có: {', '.join(missing[:5])}{'…' if len(missing) > 5 else ''}."
                 if missing else "✓ CV đã cover trọn top thị trường — vô cùng tốt."),
                f"ℹ Top-K dựa trên demand_count từ JD crawl mới nhất ({snapshot_date.isoformat()}).",
            ],
            tips=([f"Học/bổ sung skill thiếu: {', '.join(missing[:3])}" + ("..." if len(missing) > 3 else "")]
                  if missing else ["Đã khớp toàn bộ top market — giữ vững!"]),
        )

    # ── public ──
    def compute(
        self,
        db: Session,
        profile: CVProfileInput,
        snapshot_date: Optional[date] = None,
        today_year: Optional[int] = None,
        weights: Optional[dict[str, float]] = None,
    ) -> MultiCriteriaResult:
        snapshot_date = snapshot_date or date.today()
        today_year = today_year or snapshot_date.year
        w = weights or weights_for(profile.seniority)

        s1, skill_res = self._dim_skill(db, profile, snapshot_date, today_year)
        s2, d2 = self._dim_experience(profile)
        s3, d3 = self._dim_project(profile)
        s4, d4 = self._dim_education(profile)
        s5, d5 = self._dim_achievement(profile)
        s6, d6 = self._dim_language(profile)
        s7, d7 = self._dim_completeness(profile)
        s8, d8 = self._dim_market_alignment(db, profile, snapshot_date)

        top_skills = sorted(skill_res.contributions, key=lambda c: c.contribution, reverse=True)
        top3 = top_skills[:3]
        top3_str = ", ".join(f"{c.skill} ({c.contribution:.1f}đ)" for c in top3) if top3 else "—"
        sum_terms = sum(c.contribution for c in skill_res.contributions)
        ideal_str = ", ".join(skill_res.ideal_skills[:5]) + ("…" if len(skill_res.ideal_skills) > 5 else "")
        missing_top = skill_res.missing_ideal[:3]
        # Insight-driven breakdown — nói VỀ CV CỦA USER, không giải thích công thức
        n_recent = sum(1 for c in skill_res.contributions if c.recency >= 0.7)
        n_old = sum(1 for c in skill_res.contributions if c.recency < 0.4)
        n_trending_up = sum(1 for c in skill_res.contributions if c.trend > 1.1)
        n_trending_down = sum(1 for c in skill_res.contributions if c.trend < 0.9)
        ideal_overlap = len(set(c.skill.lower() for c in skill_res.contributions)
                            & set(s.lower() for s in skill_res.ideal_skills))
        bk: list[str] = []
        if top3:
            bk.append(f"✓ Top 3 skill đóng góp điểm cao nhất: {top3_str} (chiếm {sum(c.contribution for c in top3):.0f}đ).")
        if ideal_overlap > 0:
            kind = "✓" if ideal_overlap >= len(skill_res.ideal_skills) * 0.5 else "ℹ"
            bk.append(f"{kind} CV có {ideal_overlap}/{len(skill_res.ideal_skills)} skill thuộc top thị trường hiện tại.")
        if n_trending_up > 0:
            bk.append(f"✓ {n_trending_up} skill đang TRENDING UP (demand tăng so với 4 tuần trước) → kéo điểm lên.")
        if n_trending_down > 0:
            bk.append(f"⚠ {n_trending_down} skill đang COOLING (demand giảm) → kéo điểm xuống.")
        if n_old > 0:
            bk.append(f"⚠ {n_old} skill chưa update last_used_year >5 năm → recency = 0.1 (penalty mạnh).")
        elif n_recent < len(skill_res.contributions) * 0.6:
            bk.append(f"ℹ Chỉ {n_recent}/{len(skill_res.contributions)} skill được dùng trong 2 năm gần nhất.")
        if missing_top:
            bk.append(f"✗ Skill HOT chưa có: {', '.join(missing_top)}{'…' if len(skill_res.missing_ideal) > 3 else ''}.")
        else:
            bk.append("✓ CV đã cover đủ top skill thị trường — duy trì!")
        if skill_res.cold_start:
            bk.append("ℹ Dữ liệu thị trường <4 tuần → điểm có thể biến động khi data đủ.")
        d1 = DimensionDetail(
            summary=(f"{len(profile.skills)} skill × Demand × Recency = {s1:.1f}/100"
                     + (f". Top: {top3[0].skill}" if top3 else "")),
            formula=(r"\text{score} = 100 \cdot \dfrac{\displaystyle\sum_{s \in S_{\text{CV}}} "
                     r"w_r(s) \cdot \text{trend}(s) \cdot \text{recency}(s)}"
                     r"{\displaystyle\sum_{s \in S_{\text{ideal}}} w_r(s)}"
                     rf" = {sum_terms:.1f}"
                     + (r"\quad \text{(capped to 100)}" if s1 >= 100 else "")),
            inputs=[
                {"label": "Số skill trong CV", "value": str(len(profile.skills))},
                {"label": "Top-15 ideal skills (role)", "value": ideal_str or "—"},
                {"label": "Top đóng góp",
                 "value": top3_str,
                 "hint": "skill (điểm) — sort theo contribution"},
                {"label": "Cold-start?", "value": "Có" if skill_res.cold_start else "Không",
                 "hint": "Cold-start = chưa đủ 4 tuần data → trend=1.0 trung tính"},
            ],
            breakdown=bk,
            tips=([f"Bổ sung skill thiếu: {', '.join(missing_top)}." for missing_top in [missing_top] if missing_top] +
                  (["Update last_used_year cho skill cũ để recency tăng (1.0 nếu dùng trong 1 năm)."]
                   if any(c.recency < 0.7 for c in skill_res.contributions) else [])
                  + (["Dữ liệu thị trường còn cold-start — điểm có thể thay đổi sau vài tuần."]
                     if skill_res.cold_start else [])),
        )

        raw = {
            "skill": (s1, d1),
            "experience": (s2, d2),
            "project": (s3, d3),
            "education": (s4, d4),
            "achievement": (s5, d5),
            "language": (s6, d6),
            "completeness": (s7, d7),
            "market_alignment": (s8, d8),
        }

        dims: list[DimensionScore] = []
        total = 0.0
        for name in DIMENSION_ORDER:
            score, detail = raw[name]
            score = max(0.0, min(100.0, score))
            omega = w.get(name, 0.0)
            weighted = omega * score
            total += weighted
            dims.append(DimensionScore(
                name=name, score=round(score, 2), weight=round(omega, 4),
                weighted=round(weighted, 3), detail=detail,
            ))

        return MultiCriteriaResult(
            score=round(max(0.0, min(100.0, total)), 2),
            role=profile.role,
            seniority=profile.seniority,
            snapshot_date=snapshot_date,
            dimensions=dims,
            skill_result=skill_res,
            cold_start=skill_res.cold_start,
        )
