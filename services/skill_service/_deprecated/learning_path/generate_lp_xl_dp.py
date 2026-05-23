"""Sinh test case extra-large với |candidates| ∈ [21, 30] để buộc DPStrategy
chạy code DP table (n > 20 vượt qua brute_force_threshold).

Strategy: ghép 2 case từ group 'real' lại thành super-case có nhiều JD đa dạng
(skill pool gộp), điều chỉnh budget cho hợp lý. Oracle dùng Dijkstra exact
(hiện đã PASS 100% optimal trên 50 case cũ, không cần brute force).

Run từ repo root:
    PYTHONPATH=. python3 services/skill_service/scripts/generate_lp_xl_dp.py
"""
from __future__ import annotations

import json
import sys
from itertools import combinations
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from services.skill_service.services.learning_path import (  # noqa
    DijkstraStrategy, DPStrategy, GreedyStrategy,
)
from services.skill_service.services.lp_benchmark import (  # noqa
    TestCase, JD, ExpectedOptimal, candidates_for, load_cases, _cost,
)
from services.skill_service.services.ontology import SkillOntology  # noqa


CASES_PATH = ROOT / "services/skill_service/data/learning_path_benchmark/cases.json"
N_TARGET = 10               # số case xl_dp muốn giữ
MIN_CANDS = 21              # vượt brute_force_threshold của DP
MAX_CANDS = 30              # ≤ max_candidates của DP
DIJKSTRA_MAX_STATES = 200_000  # nâng cho dataset lớn


def merge_cases(a: TestCase, b: TestCase, new_id: str) -> TestCase:
    """Ghép 2 case: JD list union, S_user intersection (giữ baseline chung)."""
    s_user = sorted(set(a.S_user) & set(b.S_user))
    if not s_user:  # nếu rỗng, lấy cái nhỏ hơn để vẫn có baseline
        s_user = sorted(min((a.S_user, b.S_user), key=len))
    seen_jd_ids: set[str] = set()
    jds: list[JD] = []
    for src, prefix in [(a, "a"), (b, "b")]:
        for j in src.JDs:
            jid = f"{prefix}_{j.id}"
            if jid in seen_jd_ids:
                continue
            seen_jd_ids.add(jid)
            jds.append(JD(id=jid, required=list(j.required)))
    # Budget: tổng để có chỗ unlock vài JD nhưng vẫn tight
    return TestCase(
        test_id=new_id,
        description=f"XL merge of {a.test_id}+{b.test_id} ({len(jds)} JDs)",
        role=a.role if a.role == b.role else "mixed",
        group="xl_dp",
        S_user=s_user,
        JDs=jds,
        budget=max(a.budget, b.budget) + 4,
    )


def main() -> int:
    onto = SkillOntology()
    all_cases = load_cases(CASES_PATH)
    real = [c for c in all_cases if c.group == "real"]
    wide = [c for c in all_cases if c.group == "wide_budget"]
    pool = real + wide

    print(f"Pool: {len(real)} real + {len(wide)} wide_budget = {len(pool)} candidates")

    # Try all pair combinations, keep ones with |candidates| ∈ [MIN, MAX].
    found: list[TestCase] = []
    seen_signatures: set[tuple] = set()
    for a, b in combinations(pool, 2):
        if len(found) >= N_TARGET:
            break
        tc = merge_cases(a, b, new_id=f"xl_{len(found):02d}")
        n_cands = len(candidates_for(tc))
        if not (MIN_CANDS <= n_cands <= MAX_CANDS):
            continue
        sig = tuple(sorted(j.id for j in tc.JDs))
        if sig in seen_signatures:
            continue
        seen_signatures.add(sig)
        found.append(tc)
        print(f"  candidate {tc.test_id}: |cands|={n_cands}  |JDs|={len(tc.JDs)}  "
              f"budget={tc.budget}  S_user={len(tc.S_user)}")

    if len(found) < N_TARGET:
        print(f"⚠️  Only {len(found)} cases found (target {N_TARGET}). "
              f"Try widening cost gap or relaxing constraints.")
    if not found:
        return 1

    # Oracle pass: Dijkstra exact. Verify it doesn't hit max_states (else not exact).
    dij = DijkstraStrategy(max_states=DIJKSTRA_MAX_STATES)
    greedy = GreedyStrategy()
    enriched: list[dict] = []
    print("\nOracle (Dijkstra) pass:")
    for tc in found:
        d_sr = dij.solve(tc, onto)
        g_sr = greedy.solve(tc, onto)
        warning = ""
        # Dijkstra exact iff did not exhaust max_states. We can't directly read
        # counter from result, but we can sanity-check optimality by ensuring
        # Greedy ≤ Dijkstra; if Greedy > Dijkstra → Dijkstra incomplete.
        if g_sr.jd_unlocked > d_sr.jd_unlocked:
            warning = " ⚠️ Dijkstra likely truncated (Greedy > Dijkstra)"
        print(f"  {tc.test_id}: dijkstra={d_sr.jd_unlocked} JD  greedy={g_sr.jd_unlocked} JD"
              f"  budget_used={d_sr.total_cost}/{tc.budget}{warning}")
        enriched.append({
            "test_id": tc.test_id,
            "description": tc.description,
            "role": tc.role,
            "group": "xl_dp",
            "S_user": tc.S_user,
            "JDs": [{"id": j.id, "required": j.required} for j in tc.JDs],
            "budget": tc.budget,
            "expected_optimal": {
                "skills": list(d_sr.path),
                "jd_unlocked": d_sr.jd_unlocked,
                "total_cost": d_sr.total_cost,
            },
        })

    # Merge with existing cases.json (replace existing xl_dp group if present)
    existing = json.loads(CASES_PATH.read_text())
    existing = [c for c in existing if c.get("group") != "xl_dp"]
    existing.extend(enriched)
    CASES_PATH.write_text(json.dumps(existing, indent=2, ensure_ascii=False))
    print(f"\n→ Added {len(enriched)} xl_dp cases to {CASES_PATH}")
    print(f"  Total cases now: {len(existing)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
