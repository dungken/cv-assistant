"""LLM-powered advisor cho Multi-criteria CV Freshness.

Tách khỏi `freshness_engine.py` vì:
- engine phải deterministic + nhanh + test-able (rule-based).
- advisor optional, có mạng → gọi Groq, không → giữ tips cũ.

Workflow:
1. Engine compute() → tạo `MultiCriteriaResult` với rule-based tips (fallback).
2. Cải thiện bằng `enrich_with_llm_tips(result, profile)` → replace
   tips trong each `DimensionDetail` nếu LLM trả về OK.

Free tier Groq: ~30 req/min, lớn hơn nhu cầu (user bấm health-score
mỗi vài phút). Cache TTL 1h theo (user_id, role, snapshot_date, score_hash).
"""
from __future__ import annotations

import hashlib
import json
import logging
import os
import re
import time
from typing import Optional

import requests

logger = logging.getLogger(__name__)

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_TIMEOUT_SEC = 8.0
CACHE_TTL_SEC = 3600  # 1h
MAX_CACHE_ENTRIES = 500

# Quality guardrails — drop tips chứa banned phrase, hoặc match nguyên text
# từ few-shot example (model nhỏ hay copy).
BANNED_SUBSTRINGS = [
    "tham gia khóa học",
    "tăng cường kỹ năng",
    "cải thiện kỹ năng",
    "tìm kiếm cơ hội",
    "xây dựng mạng lưới",
    "cần cv cụ thể hơn",
    "công ty công nghệ",
    "công ty quốc tế",
    "cải thiện kỹ năng mềm",
    "tăng cường kỹ năng mềm",
    "kỹ năng mềm để",
]
# Tips từ few-shot example mà model 8B hay copy nguyên — loại để tránh fake-personalize
FEWSHOT_FRAGMENTS = [
    "url shortener: fastapi + redis + postgres + docker compose",
    "kafka qua confluent developer (free, ~20h)",
    "lấy ckad trong 3 tháng",
    "contribute fix 1-2 issue vào repo open source",
]


_PLACEHOLDER_RE = re.compile(r"<[^>]{1,40}>")


def _filter_tips(tips: list[str]) -> list[str]:
    """Drop generic/fake-personalized tips. Trả về list sạch."""
    out: list[str] = []
    for t in tips:
        t_clean = t.strip()
        if not t_clean or len(t_clean) < 15:
            continue
        # Reject tip chứa unfilled placeholder <foo> hoặc {bar}
        if _PLACEHOLDER_RE.search(t_clean) or "{" in t_clean or "}" in t_clean:
            continue
        low = t_clean.lower()
        if any(b in low for b in BANNED_SUBSTRINGS):
            continue
        if any(f in low for f in FEWSHOT_FRAGMENTS):
            continue
        out.append(t_clean)
    return out

# In-memory cache: {cache_key: (timestamp, tips_dict)}
_CACHE: dict[str, tuple[float, dict[str, list[str]]]] = {}


def _is_enabled() -> bool:
    return (
        os.getenv("CHAT_USE_GROQ", "False").lower() in ("true", "1", "yes")
        and bool(os.getenv("CHAT_GROQ_API_KEY"))
    )


def _cache_key(user_id: str, role: str, snapshot_date: str, dims_summary: list[tuple[str, float]]) -> str:
    """Hash theo (user, role, snap, score_per_dim) — nếu score thay đổi thì re-call."""
    payload = json.dumps([user_id, role, snapshot_date, sorted(dims_summary)], sort_keys=True)
    return hashlib.md5(payload.encode()).hexdigest()


def _cache_get(key: str) -> Optional[dict[str, list[str]]]:
    entry = _CACHE.get(key)
    if not entry:
        return None
    ts, tips = entry
    if time.time() - ts > CACHE_TTL_SEC:
        _CACHE.pop(key, None)
        return None
    return tips


def _cache_put(key: str, tips: dict[str, list[str]]) -> None:
    # Naive LRU-ish: drop oldest when overflow
    if len(_CACHE) >= MAX_CACHE_ENTRIES:
        oldest = min(_CACHE.items(), key=lambda kv: kv[1][0])[0]
        _CACHE.pop(oldest, None)
    _CACHE[key] = (time.time(), tips)


SYSTEM_PROMPT = """Bạn là senior tech recruiter người Việt, đã review 1000+ CV IT.
Sinh gợi ý CỰC KỲ CỤ THỂ để cải thiện CV theo 8 chiều scoring.

=== RULES ABSOLUTE ===
1. Mỗi tip ≤ 140 ký tự (cho phép link), viết tiếng Việt.
2. PHẢI có ÍT NHẤT MỘT artifact cụ thể:
   - Tên cert/exam (vd "AWS SAA-C03", "JLPT N2", "TOEIC ≥ 700").
   - Tên course/platform (vd "Frontend Masters: Advanced React").
   - Tên project pattern (vd "build URL shortener với Redis + JWT").
   - Số liệu (vd "thêm 2 dự án trong 8 tuần").
   - Tên skill/tool (vd "Kafka", "k8s HPA", "Prisma ORM").
3. NÊN kèm 1 link tham khảo cuối tip, format markdown `[text](https://url)`.
   - CHỈ dùng URL của các domain CHÍNH THỐNG, ổn định lâu dài:
     * developer.mozilla.org, docs.python.org, kubernetes.io, kafka.apache.org
     * aws.amazon.com/certification, learn.microsoft.com, cloud.google.com/learn
     * coursera.org, udemy.com, frontendmasters.com, freecodecamp.org, roadmap.sh
     * github.com/<org>/<repo> cho repo nổi tiếng
     * leetcode.com, hackerrank.com
   - TUYỆT ĐỐI KHÔNG fabricate URL. Nếu không chắc URL tồn tại → bỏ link.
   - 1 link/tip là đủ. Không cần mọi tip có link.
4. Tips KHÁC NHAU giữa các chiều. KHÔNG lặp ý.
5. Cân nhắc cross-dim: Skill cao + Experience thấp → đề xuất hackathon/open source.
6. Ưu tiên 1-2 tip impact cao nhất. Mỗi chiều 2-3 tip là đủ.

=== BANNED PHRASES (sai trả lỗi) ===
- "tham gia khóa học" (không nói khóa nào)
- "tăng cường kỹ năng" / "cải thiện kỹ năng" (mơ hồ)
- "tìm kiếm cơ hội" (mơ hồ)
- "xây dựng mạng lưới" (sáo rỗng)
- "kỹ năng mềm" / "soft skill" chung chung
- "công ty công nghệ" / "công ty quốc tế" (mơ hồ)
- Bất kỳ câu nào không kèm artifact cụ thể theo rule #2.

=== STRUCTURE TEMPLATE ===
Mỗi tip: [VERB] + [SPECIFIC ARTIFACT] + [METRIC/TIMELINE/MOTIVATION]
TUYỆT ĐỐI KHÔNG dùng placeholder <foo> hoặc {bar} trong output. Luôn viết tên thật.

=== HAI EXAMPLE CHO ROLE KHÁC (đừng copy — phải adapt theo role của user) ===

Example A — frontend mid-level, skill=60, missing top: tailwind, vite, next.js:
{
  "skill": [
    "Học Next.js App Router (18h) — top JD frontend Q2/2026. Tham khảo [docs Next.js](https://nextjs.org/learn)",
    "Refactor 1 dự án React cũ sang Vite + TailwindCSS. Guide: [Vite migration](https://vite.dev/guide/)"
  ],
  "project": [
    "Build dashboard analytics dùng Next.js + shadcn/ui + Recharts trong 4 tuần. [shadcn/ui](https://ui.shadcn.com)",
    "Open source 1 component library nhỏ (5-10 components) trên npm"
  ]
}

Example B — data engineer junior, skill=55, missing: airflow, dbt, spark:
{
  "skill": [
    "Học dbt qua [dbt Learn](https://learn.getdbt.com) (free, ~15h) + làm Jaffle Shop tutorial",
    "Lấy Airflow Fundamentals cert ([Astronomer](https://academy.astronomer.io), free) trong 1 tháng"
  ],
  "project": [
    "Build ELT pipeline: Airflow → BigQuery → dbt → Metabase. Inspiration: [data-engineering-zoomcamp](https://github.com/DataTalksClub/data-engineering-zoomcamp)",
    "Contribute 1 PR vào [dbt-utils](https://github.com/dbt-labs/dbt-utils) hoặc Great Expectations"
  ]
}

NOTICE: Link là URL THẬT của resource — không bịa. Tên cụ thể adapt theo user.

=== OUTPUT FORMAT (JSON only, no markdown fence) ===
{
  "skill": [...],
  "experience": [...],
  "project": [...],
  "education": [...],
  "achievement": [...],
  "language": [...],
  "completeness": [...],
  "market_alignment": [...]
}

Nếu chiều nào điểm ≥ 90 → tips ngắn 1 item ("Đã ổn, duy trì khi update CV") để focus chiều yếu."""


def _build_user_prompt(
    role: str,
    seniority: str,
    cv_skills: list[str],
    dimensions: list[dict],
    extras: Optional[dict] = None,
) -> str:
    skills_str = ", ".join(cv_skills[:30]) + (f" (+{len(cv_skills)-30} kỹ năng khác)" if len(cv_skills) > 30 else "")
    extras = extras or {}
    lines = [
        f"# CV Snapshot",
        f"- Role: **{role}** | Seniority: **{seniority}**",
        f"- Skills CV có ({len(cv_skills)}): {skills_str}",
    ]
    if extras.get("missing_top_market"):
        lines.append(f"- TOP skills thị trường CV ĐANG THIẾU: {', '.join(extras['missing_top_market'][:8])}")
    if extras.get("top_contributors"):
        lines.append(f"- Top skill đóng góp điểm cao nhất: {', '.join(extras['top_contributors'][:5])}")
    lines += [
        "",
        "# 8-Dimension Scores (sort yếu → mạnh — ưu tiên chiều đầu)",
    ]
    for d in dimensions:
        warning = ""
        if d["score"] < 30:
            warning = " 🔴 CRITICAL"
        elif d["score"] < 60:
            warning = " 🟡 WEAK"
        elif d["score"] >= 90:
            warning = " ✓ STRONG"
        lines.append(
            f"- **{d['name']}**: {d['score']:.0f}/100 (ω={d['weight']:.2f}){warning}\n"
            f"    {d.get('summary', '')[:200]}"
        )
    lines += [
        "",
        "Yêu cầu: sinh tips theo SYSTEM RULES. Output JSON only.",
        "Nếu thông tin về một chiều quá ít → tip 'cần CV cụ thể hơn để gợi ý'.",
    ]
    return "\n".join(lines)


def _call_groq(system: str, user: str) -> Optional[dict]:
    api_key = os.getenv("CHAT_GROQ_API_KEY")
    model = os.getenv("CHAT_GROQ_MODEL", "llama-3.1-8b-instant")
    if not api_key:
        return None
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "temperature": 0.3,
        "response_format": {"type": "json_object"},
        "stream": False,
    }
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    try:
        r = requests.post(GROQ_URL, json=payload, headers=headers, timeout=GROQ_TIMEOUT_SEC)
        r.raise_for_status()
        content = r.json().get("choices", [{}])[0].get("message", {}).get("content", "")
        if not content:
            return None
        return json.loads(content)
    except (requests.RequestException, json.JSONDecodeError, ValueError) as e:
        logger.warning("freshness_advisor: Groq call failed: %s", e)
        return None


def enrich_tips(
    user_id: str,
    role: str,
    seniority: str,
    snapshot_date: str,
    cv_skills: list[str],
    dimensions: list,  # list[DimensionScore] — to avoid circular import
    missing_top_market: Optional[list[str]] = None,
    top_contributors: Optional[list[str]] = None,
) -> dict[str, list[str]]:
    """Trả về dict {dim_name: tips[]}. Không raise nếu Groq fail — caller
    sẽ giữ tips cũ.
    Returns empty dict nếu disabled / fail.
    """
    if not _is_enabled():
        return {}

    dims_summary = [(d.name, round(d.score, 1)) for d in dimensions]
    key = _cache_key(user_id, role, snapshot_date, dims_summary)
    cached = _cache_get(key)
    if cached is not None:
        logger.info("freshness_advisor: cache HIT user=%s", user_id)
        return cached

    # Sort yếu → mạnh để LLM ưu tiên chiều cần improve nhất
    sorted_dims = sorted(dimensions, key=lambda d: d.score)
    dim_payload = [
        {
            "name": d.name,
            "score": d.score,
            "weight": d.weight,
            "summary": getattr(d.detail, "summary", "") if d.detail else "",
        }
        for d in sorted_dims
    ]
    system = SYSTEM_PROMPT
    user = _build_user_prompt(
        role, seniority, cv_skills, dim_payload,
        extras={
            "missing_top_market": missing_top_market or [],
            "top_contributors": top_contributors or [],
        },
    )

    t0 = time.time()
    raw = _call_groq(system, user)
    dt = time.time() - t0
    if not raw or not isinstance(raw, dict):
        logger.info("freshness_advisor: empty/invalid LLM response (%.2fs)", dt)
        return {}

    # Coerce + filter generic tips
    tips_by_dim: dict[str, list[str]] = {}
    dropped_total = 0
    for k, v in raw.items():
        raw_tips: list[str] = []
        if isinstance(v, list):
            raw_tips = [str(x) for x in v]
        elif isinstance(v, str) and v.strip():
            raw_tips = [v]
        filtered = _filter_tips(raw_tips)[:4]
        dropped_total += len(raw_tips) - len(filtered)
        # Chỉ giữ dim nếu còn ít nhất 1 tip sau filter — không thì fallback rule
        if filtered:
            tips_by_dim[k] = filtered
    logger.info(
        "freshness_advisor: LLM OK %d/%d dims kept (%d tips dropped as generic, %.2fs)",
        len(tips_by_dim), len(raw), dropped_total, dt,
    )
    _cache_put(key, tips_by_dim)
    return tips_by_dim
