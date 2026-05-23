"""Validate Multi-criteria CV Freshness Framework — 8 chiều (chuong3/3.2.5).

Chạy MultiCriteriaFreshnessEngine trên 10 CV "fresh" + 10 CV "stale" với cùng
một synthetic market snapshot (vì lịch sử crawler thực còn đang tích luỹ), thực
hiện đủ 3 phương pháp validate của §3.2.5:

  Phương pháp 1 — Fresh vs Stale: trung bình nhóm fresh phải > stale ≥ 20 điểm,
                  và mọi fresh > mọi stale cùng role.
  Phương pháp 2 — Baseline comparison: so với (A) Random score và (B) Single
                  Skill-dimension-only, đo bằng độ phân tách (separation) fresh/stale.
  Phương pháp 3 — Self-consistency (T2 monotonic): thêm dần thành phần vào 1 CV
                  gốc → Freshness không bao giờ giảm.

Xuất bảng số + ghi report Markdown cho Chương 4.

Run từ repo root:
    PYTHONPATH=. python3 services/skill_service/scripts/validate_multi_freshness.py
"""
from __future__ import annotations

import json
import random
import statistics
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from services.skill_service.services.freshness_engine import (  # noqa: E402
    MultiCriteriaFreshnessEngine, CVProfileInput, CVSkillInput, DIMENSION_ORDER,
)
from services.skill_service.services.ontology import SkillOntology  # noqa: E402
from services.skill_service.scripts.validate_freshness import (  # noqa: E402
    SyntheticMarketDB, DATA,
)

REPORT = DATA / "multi_freshness_report.md"


# ─── Build CVProfileInput from a CV dict ──────────────────────────────────────


def to_profile(cv: dict) -> CVProfileInput:
    return CVProfileInput(
        skills=[CVSkillInput(name=s["name"], last_used_year=s.get("last_used_year"))
                for s in cv["skills"]],
        role=cv["role"],
        seniority=cv.get("seniority", "junior"),
        years_experience=cv.get("years_experience"),
        past_job_titles=cv.get("past_job_titles", []),
        num_projects=cv.get("num_projects", 0),
        project_skill_counts=cv.get("project_skill_counts", []),
        degree=cv.get("degree"),
        major=cv.get("major"),
        achievement_text=cv.get("achievement_text", ""),
        language_text=cv.get("language_text", ""),
        has_contact=cv.get("has_contact", False),
        has_summary=cv.get("has_summary", False),
        has_education=cv.get("has_education", False),
        has_experience=cv.get("has_experience", False),
        has_skills=cv.get("has_skills", False),
        has_projects=cv.get("has_projects", False),
    )


def separation(fresh: list[float], stale: list[float]) -> float:
    """Cohen's d — độ phân tách chuẩn hoá giữa 2 nhóm (lớn = phân biệt tốt)."""
    if len(fresh) < 2 or len(stale) < 2:
        return 0.0
    pooled = ((statistics.pstdev(fresh) ** 2 + statistics.pstdev(stale) ** 2) / 2) ** 0.5
    if pooled == 0:
        return float("inf")
    return (statistics.mean(fresh) - statistics.mean(stale)) / pooled


# ─── Phương pháp 3 — monotonic build-up ───────────────────────────────────────


def monotonic_check(engine, db, snapshot_date) -> tuple[bool, list[tuple[str, float]]]:
    """Bắt đầu từ CV tối thiểu, thêm dần thành phần 8 chiều → score không giảm."""
    db.for_role("backend")
    steps: list[tuple[str, CVProfileInput]] = []

    base = CVProfileInput(role="backend", seniority="junior",
                          skills=[CVSkillInput("Python", 2026)],
                          has_skills=True)
    steps.append(("CV gốc (1 skill)", base))

    def clone(p: CVProfileInput, **kw) -> CVProfileInput:
        d = dict(p.__dict__)
        d.update(kw)
        return CVProfileInput(**d)

    p = clone(base, skills=base.skills + [CVSkillInput("Docker", 2026),
                                          CVSkillInput("Kubernetes", 2026),
                                          CVSkillInput("PostgreSQL", 2026)])
    steps.append(("+3 skill hot", p))
    p = clone(p, has_contact=True, has_summary=True, has_education=True,
              has_experience=True, has_projects=True)
    steps.append(("+ đủ section (Completeness)", p))
    p = clone(p, num_projects=3, project_skill_counts=[5, 4, 5])
    steps.append(("+3 project", p))
    p = clone(p, degree="Bachelor", major="Computer Science")
    steps.append(("+ Education (Bachelor CS)", p))
    p = clone(p, years_experience=2.0, past_job_titles=["Backend Developer"])
    steps.append(("+ Experience (2 năm)", p))
    p = clone(p, language_text="IELTS 7.0")
    steps.append(("+ Language (IELTS 7.0)", p))
    p = clone(p, achievement_text="AWS certified; hackathon winner 2025")
    steps.append(("+ Achievement", p))

    results: list[tuple[str, float]] = []
    prev = -1.0
    ok = True
    for name, profile in steps:
        r = engine.compute(db, profile, snapshot_date=snapshot_date)
        if r.score < prev - 1e-6:
            ok = False
        results.append((name, r.score))
        prev = r.score
    return ok, results


# ─── Main ─────────────────────────────────────────────────────────────────────


def main() -> int:
    market = json.loads((DATA / "market_snapshot.json").read_text())
    snapshot_date = date.fromisoformat(market["snapshot_date"])
    fresh_cvs = json.loads((DATA / "cvs_fresh.json").read_text())
    stale_cvs = json.loads((DATA / "cvs_stale.json").read_text())

    engine = MultiCriteriaFreshnessEngine(SkillOntology())
    db = SyntheticMarketDB(market)

    rows: list[dict] = []
    dim_means_fresh: dict[str, list[float]] = {d: [] for d in DIMENSION_ORDER}
    dim_means_stale: dict[str, list[float]] = {d: [] for d in DIMENSION_ORDER}

    for cv in fresh_cvs + stale_cvs:
        db.for_role(cv["role"])
        profile = to_profile(cv)
        res = engine.compute(db, profile, snapshot_date=snapshot_date)
        dims = {d.name: d.score for d in res.dimensions}
        rows.append({"cv": cv, "score": res.score, "dims": dims,
                     "skill_only": dims["skill"]})
        tgt = dim_means_fresh if cv["label"] == "fresh" else dim_means_stale
        for d in DIMENSION_ORDER:
            tgt[d].append(dims[d])

    fresh = [r["score"] for r in rows if r["cv"]["label"] == "fresh"]
    stale = [r["score"] for r in rows if r["cv"]["label"] == "stale"]
    gap = statistics.mean(fresh) - statistics.mean(stale)

    # ── Phương pháp 1
    by_role: dict[str, dict[str, list[float]]] = {}
    for r in rows:
        by_role.setdefault(r["cv"]["role"], {}).setdefault(r["cv"]["label"], []).append(r["score"])
    per_role_pass = True
    role_lines = []
    for role, g in sorted(by_role.items()):
        f, s = g.get("fresh", []), g.get("stale", [])
        if not f or not s:
            continue
        ok = min(f) > max(s)
        per_role_pass = per_role_pass and ok
        role_lines.append((role, min(f), max(s), ok))

    # ── Phương pháp 2 — baselines
    random.seed(42)
    rand_fresh = [random.uniform(0, 100) for _ in fresh]
    rand_stale = [random.uniform(0, 100) for _ in stale]
    skill_fresh = [r["skill_only"] for r in rows if r["cv"]["label"] == "fresh"]
    skill_stale = [r["skill_only"] for r in rows if r["cv"]["label"] == "stale"]

    sep_multi = separation(fresh, stale)
    sep_skill = separation(skill_fresh, skill_stale)
    sep_rand = separation(rand_fresh, rand_stale)

    # ── Phương pháp 3
    mono_ok, mono_steps = monotonic_check(engine, db, snapshot_date)

    # ── Console
    print(f"Snapshot: {snapshot_date}\n")
    print(f"{'CV':<18}{'Role':<13}{'Lbl':<7}{'Total':>7}  " +
          "  ".join(f"{d[:4]:>5}" for d in DIMENSION_ORDER))
    print("-" * 120)
    for r in rows:
        cv = r["cv"]
        dimstr = "  ".join(f"{r['dims'][d]:5.0f}" for d in DIMENSION_ORDER)
        print(f"{cv['cv_id']:<18}{cv['role']:<13}{cv['label']:<7}{r['score']:7.2f}  {dimstr}")

    print("\n── PP1: Fresh vs Stale ─────────────")
    print(f"  fresh mean={statistics.mean(fresh):.2f}  stale mean={statistics.mean(stale):.2f}  "
          f"Δ={gap:+.2f}  (yêu cầu ≥ 20)")
    for role, mf, ms, ok in role_lines:
        print(f"  {role:<13} min(fresh)={mf:6.2f}  max(stale)={ms:6.2f}  {'PASS' if ok else 'FAIL'}")

    print("\n── PP2: Baseline (Cohen's d separation) ──")
    print(f"  Multi-criteria 8 chiều : d = {sep_multi:.2f}")
    print(f"  Single Skill-only      : d = {sep_skill:.2f}")
    print(f"  Random                 : d = {sep_rand:.2f}")

    print("\n── PP3: Monotonic build-up ──")
    for name, sc in mono_steps:
        print(f"  {name:<32} → {sc:6.2f}")
    print(f"  Monotonic: {'PASS' if mono_ok else 'FAIL'}")

    pp1 = gap >= 20 and per_role_pass
    pp2 = sep_multi >= sep_skill and sep_multi > sep_rand
    overall = pp1 and pp2 and mono_ok
    print(f"\nKết quả: PP1={'PASS' if pp1 else 'FAIL'}  "
          f"PP2={'PASS' if pp2 else 'FAIL'}  PP3={'PASS' if mono_ok else 'FAIL'}  "
          f"→ {'VALIDATION PASSED' if overall else 'VALIDATION FAILED'}")

    # ── Markdown report
    _write_report(snapshot_date, rows, fresh, stale, gap, role_lines,
                  sep_multi, sep_skill, sep_rand, mono_steps, mono_ok,
                  dim_means_fresh, dim_means_stale, pp1, pp2, overall)
    print(f"\nReport → {REPORT}")
    return 0 if overall else 1


def _write_report(snap, rows, fresh, stale, gap, role_lines,
                  sep_multi, sep_skill, sep_rand, mono_steps, mono_ok,
                  dmf, dms, pp1, pp2, overall):
    L: list[str] = []
    L.append("# Kết quả validate Multi-criteria CV Freshness Framework (8 chiều)\n")
    L.append(f"Snapshot thị trường: `{snap}` · N = {len(fresh)} fresh + {len(stale)} stale CV "
             "(role: backend, frontend, data, devops, ai_engineer).\n")
    L.append("> Sinh từ `services/skill_service/scripts/validate_multi_freshness.py`. "
             "Phương pháp theo chuong3/3.2.5.\n")

    L.append("## Bảng A — Điểm tổng và 8 chiều từng CV\n")
    L.append("| CV | Role | Label | Total | " +
             " | ".join(d.capitalize()[:6] for d in DIMENSION_ORDER) + " |")
    L.append("|---|---|---|---|" + "---|" * len(DIMENSION_ORDER))
    for r in rows:
        cv = r["cv"]
        dimstr = " | ".join(f"{r['dims'][d]:.0f}" for d in DIMENSION_ORDER)
        L.append(f"| {cv['cv_id']} | {cv['role']} | {cv['label']} | "
                 f"**{r['score']:.1f}** | {dimstr} |")

    L.append("\n## Bảng B — Trung bình từng chiều (fresh vs stale)\n")
    L.append("| Chiều | Fresh mean | Stale mean | Δ |")
    L.append("|---|---|---|---|")
    for d in DIMENSION_ORDER:
        mf, ms = statistics.mean(dmf[d]), statistics.mean(dms[d])
        L.append(f"| {d.capitalize()} | {mf:.1f} | {ms:.1f} | {mf - ms:+.1f} |")

    L.append("\n## Phương pháp 1 — Fresh vs Stale\n")
    L.append(f"- Trung bình **fresh = {statistics.mean(fresh):.2f}**, "
             f"**stale = {statistics.mean(stale):.2f}**, "
             f"khoảng cách **Δ = {gap:+.2f}** điểm (yêu cầu ≥ 20 → "
             f"{'**ĐẠT**' if gap >= 20 else '**KHÔNG ĐẠT**'}).")
    L.append("- Kiểm tra per-role (mọi fresh > mọi stale cùng role):\n")
    L.append("| Role | min(fresh) | max(stale) | Kết quả |")
    L.append("|---|---|---|---|")
    for role, mf, ms, ok in role_lines:
        L.append(f"| {role} | {mf:.2f} | {ms:.2f} | {'PASS' if ok else 'FAIL'} |")

    L.append("\n## Phương pháp 2 — So sánh baseline (Cohen's d separation)\n")
    L.append("Độ phân tách chuẩn hoá fresh/stale (d càng lớn càng phân biệt tốt):\n")
    L.append("| Phương án | Cohen's d |")
    L.append("|---|---|")
    L.append(f"| **Multi-criteria 8 chiều** | **{sep_multi:.2f}** |")
    L.append(f"| Single Skill-dimension only | {sep_skill:.2f} |")
    L.append(f"| Random | {sep_rand:.2f} |")
    L.append(f"\nMulti-criteria phân biệt tốt hơn baseline Skill-only "
             f"({sep_multi:.2f} ≥ {sep_skill:.2f}) và vượt xa Random "
             f"({sep_rand:.2f}) → {'**ĐẠT**' if pp2 else '**KHÔNG ĐẠT**'}.")

    L.append("\n## Phương pháp 3 — Self-consistency (T2 monotonic)\n")
    L.append("Thêm dần thành phần vào 1 CV gốc → Freshness không bao giờ giảm:\n")
    L.append("| Bước | Freshness |")
    L.append("|---|---|")
    for name, sc in mono_steps:
        L.append(f"| {name} | {sc:.2f} |")
    L.append(f"\nMonotonic qua mọi bước → {'**ĐẠT**' if mono_ok else '**KHÔNG ĐẠT**'}.")

    L.append(f"\n## Tổng kết\n")
    L.append(f"- PP1 (phân biệt fresh/stale): {'PASS' if pp1 else 'FAIL'}")
    L.append(f"- PP2 (vượt baseline): {'PASS' if pp2 else 'FAIL'}")
    L.append(f"- PP3 (monotonic): {'PASS' if mono_ok else 'FAIL'}")
    L.append(f"\n**Kết luận: {'VALIDATION PASSED' if overall else 'VALIDATION FAILED'}**")

    REPORT.write_text("\n".join(L) + "\n", encoding="utf-8")


if __name__ == "__main__":
    sys.exit(main())
