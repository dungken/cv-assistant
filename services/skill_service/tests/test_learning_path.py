"""Smoke tests for Learning Path Optimizer — Tuần 12.

Verifies the Greedy + Dijkstra strategies on hand-checked group-1 cases.

Run:
    PYTHONPATH=. python3 services/skill_service/tests/test_learning_path.py
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from services.skill_service.services.learning_path import (
    DijkstraStrategy, DPStrategy, GreedyStrategy, LearningPathOptimizer,
)
from services.skill_service.services.lp_benchmark import (
    JD, TestCase, evaluate_path, expand_with_prereqs,
)
from services.skill_service.services.ontology import SkillOntology


ONT = SkillOntology()


def _tc_react_or_vue() -> TestCase:
    return TestCase(
        test_id="t01", group="small", role="frontend",
        description="FE junior with JS, two reachable React JDs",
        S_user=["HTML", "CSS", "JavaScript"],
        JDs=[
            JD("jd_a", ["JavaScript", "React"]),
            JD("jd_b", ["JavaScript", "React", "TypeScript"]),
            JD("jd_c", ["JavaScript", "Vue.js"]),
        ],
        budget=5,
    )


def test_greedy_picks_highest_roi_skill():
    """React alone unlocks jd_a (gain=1) → should be picked first."""
    tc = _tc_react_or_vue()
    g = GreedyStrategy()
    r = g.solve(tc, ONT)
    assert "React" in r.path, f"path={r.path}"
    assert r.jd_unlocked >= 1


def test_greedy_respects_budget():
    tc = _tc_react_or_vue()
    g = GreedyStrategy()
    r = g.solve(tc, ONT)
    assert r.total_cost <= tc.budget


def test_dijkstra_finds_at_least_as_many_jds_as_greedy():
    tc = _tc_react_or_vue()
    g = GreedyStrategy().solve(tc, ONT)
    d = DijkstraStrategy().solve(tc, ONT)
    assert d.jd_unlocked >= g.jd_unlocked


def test_prereq_compliance_via_expand():
    """Empty start needing Next.js should auto-include JavaScript and React."""
    tc = TestCase(
        test_id="t02", group="deep_prereq", role="frontend",
        description="empty start, JD asks Next.js",
        S_user=[], JDs=[JD("jd_a", ["Next.js"])], budget=12,
    )
    r = GreedyStrategy().solve(tc, ONT)
    rep = evaluate_path(tc, r, ONT, "greedy")
    assert rep.prereq_compliant, f"path violates REQUIRES: {r.path}"
    assert rep.within_budget


def test_expand_with_prereqs_handles_cycle_safety():
    """expand_with_prereqs must terminate on any input (defensive)."""
    out = expand_with_prereqs(["Next.js"], owned=set(), ontology=ONT)
    assert "Next.js" in out
    # All entries must be unique (no cycles, no duplicates).
    assert len(out) == len(set(out))


def test_optimizer_returns_explanation():
    tc = _tc_react_or_vue()
    opt = LearningPathOptimizer(ONT)
    result, exp = opt.optimize(tc, algorithm="greedy")
    assert exp.algorithm == "greedy"
    assert exp.jd_unlocked_count == result.jd_unlocked
    assert all(s.reason for s in exp.steps)


def test_no_jd_to_unlock_returns_empty_path():
    tc = TestCase(
        test_id="t03", group="small", role="backend",
        description="CV already covers the only JD",
        S_user=["Python"], JDs=[JD("jd_a", ["Python"])], budget=10,
    )
    r = GreedyStrategy().solve(tc, ONT)
    assert r.path == []
    assert r.jd_unlocked == 1


def test_dp_matches_brute_force_on_small_case():
    """DP is expected to be optimal — must match the brute-force oracle."""
    from services.skill_service.services.lp_benchmark import solve_brute_force
    tc = _tc_react_or_vue()
    dp = DPStrategy().solve(tc, ONT)
    bf = solve_brute_force(tc, ONT)
    assert dp.jd_unlocked == bf.jd_unlocked, f"DP={dp.jd_unlocked} BF={bf.jd_unlocked}"


def test_dp_dominates_greedy_when_they_disagree():
    """DP must always produce ≥ JD count of any other strategy."""
    tc = _tc_react_or_vue()
    g = GreedyStrategy().solve(tc, ONT)
    d = DijkstraStrategy().solve(tc, ONT)
    p = DPStrategy().solve(tc, ONT)
    assert p.jd_unlocked >= g.jd_unlocked
    assert p.jd_unlocked >= d.jd_unlocked


def test_dp_handles_prereq_chain():
    """Start with JS+React, JD asks Next.js → DP picks Next.js (cost 2)."""
    tc = TestCase(
        test_id="t05", group="deep_prereq", role="frontend",
        description="JS+React in hand, JD needs Next.js (which also requires Node.js)",
        S_user=["JavaScript", "React"],
        JDs=[JD("jd_a", ["Next.js"])],
        budget=6,  # Next.js (2) + Node.js prereq (3) = 5
    )
    p = DPStrategy().solve(tc, ONT)
    rep = evaluate_path(tc, p, ONT, "dp")
    assert rep.prereq_compliant
    assert rep.within_budget
    assert p.jd_unlocked == 1, f"path={p.path}"


def test_zero_budget_yields_empty_path():
    tc = TestCase(
        test_id="t04", group="small", role="frontend",
        description="Zero budget",
        S_user=["JavaScript"], JDs=[JD("jd_a", ["JavaScript", "React"])],
        budget=0,
    )
    r = GreedyStrategy().solve(tc, ONT)
    assert r.path == [] and r.total_cost == 0


if __name__ == "__main__":
    tests = [
        test_greedy_picks_highest_roi_skill,
        test_greedy_respects_budget,
        test_dijkstra_finds_at_least_as_many_jds_as_greedy,
        test_prereq_compliance_via_expand,
        test_expand_with_prereqs_handles_cycle_safety,
        test_optimizer_returns_explanation,
        test_no_jd_to_unlock_returns_empty_path,
        test_dp_matches_brute_force_on_small_case,
        test_dp_dominates_greedy_when_they_disagree,
        test_dp_handles_prereq_chain,
        test_zero_budget_yields_empty_path,
    ]
    failures = 0
    for t in tests:
        try:
            t()
            print(f"OK  {t.__name__}")
        except AssertionError as e:
            failures += 1
            print(f"FAIL {t.__name__}: {e}")
        except Exception as e:
            failures += 1
            print(f"ERR  {t.__name__}: {type(e).__name__}: {e}")
    if failures:
        sys.exit(1)
    print(f"\nAll {len(tests)} tests passed.")
