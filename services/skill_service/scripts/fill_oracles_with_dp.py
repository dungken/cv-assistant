"""Tuần 13 — fill `expected_optimal` slots that brute-force couldn't (group3
wide_budget cases) using DPStrategy as the canonical optimal oracle.

Run after generate_lp_benchmark.py so the brute-forced cases are already in.

    PYTHONPATH=. python3 services/skill_service/scripts/fill_oracles_with_dp.py
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from services.skill_service.services.learning_path import DPStrategy
from services.skill_service.services.lp_benchmark import (
    ExpectedOptimal, candidates_for, dump_cases, load_cases,
)
from services.skill_service.services.ontology import SkillOntology


CASES = ROOT / "services" / "skill_service" / "data" / "learning_path_benchmark" / "cases.json"


def main() -> int:
    cases = load_cases(CASES)
    ontology = SkillOntology()
    dp = DPStrategy(max_candidates=30)

    filled = 0
    skipped = 0
    for tc in cases:
        if tc.expected_optimal is not None:
            continue
        n_cand = len(candidates_for(tc))
        if n_cand > dp.max_candidates:
            print(f"  skip {tc.test_id}: {n_cand} candidates > DP cap {dp.max_candidates}")
            skipped += 1
            continue
        r = dp.solve(tc, ontology)
        tc.expected_optimal = ExpectedOptimal(
            skills=r.path, jd_unlocked=r.jd_unlocked, total_cost=r.total_cost,
        )
        print(f"  {tc.test_id} ({tc.group:<12}) JD={r.jd_unlocked} cost={r.total_cost} "
              f"path[0:5]={r.path[:5]}  ({r.runtime_s*1000:.1f} ms)")
        filled += 1

    dump_cases(cases, CASES)
    total_with_oracle = sum(1 for c in cases if c.expected_optimal is not None)
    print(f"\nFilled {filled} oracles with DP. Skipped {skipped}.")
    print(f"Cases with expected_optimal now: {total_with_oracle} / {len(cases)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
