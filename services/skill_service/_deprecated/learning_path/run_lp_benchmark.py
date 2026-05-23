"""Tuần 12 — run Greedy + Dijkstra on the 50 benchmark cases and report metrics.

Metrics (§3.3.4):
- Optimality ratio = jd_unlocked / expected_optimal.jd_unlocked
  (only computed where expected_optimal exists; group3 wide_budget mostly skipped — DP in Tuần 13 fills)
- Runtime wall-clock (mean over N_REPEAT runs per case)
- Prerequisite compliance (must be 100%)
- Within-budget compliance (must be 100%)

Run from repo root:
    PYTHONPATH=. python3 services/skill_service/scripts/run_lp_benchmark.py
"""
from __future__ import annotations

import csv
import json
import statistics
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from services.skill_service.services.learning_path import (
    DijkstraStrategy, DPStrategy, GreedyStrategy,
)
from services.skill_service.services.lp_benchmark import (
    EvalReport, evaluate_path, load_cases,
)
from services.skill_service.services.ontology import SkillOntology


CASES = ROOT / "services" / "skill_service" / "data" / "learning_path_benchmark" / "cases.json"
OUT_DIR = ROOT / "services" / "skill_service" / "data" / "learning_path_benchmark"

N_REPEAT = 5  # average runtime over N runs per (case, solver) — §3.3.4


def main() -> int:
    cases = load_cases(CASES)
    ontology = SkillOntology()

    solvers = [
        GreedyStrategy(),
        DijkstraStrategy(max_states=80_000),
        DPStrategy(max_candidates=30),
    ]
    rows: list[EvalReport] = []
    runtime_runs: dict[tuple[str, str], list[float]] = defaultdict(list)

    for tc in cases:
        for solver in solvers:
            best_report: EvalReport | None = None
            for _ in range(N_REPEAT):
                sr = solver.solve(tc, ontology)
                runtime_runs[(tc.test_id, solver.name)].append(sr.runtime_s)
                rep = evaluate_path(tc, sr, ontology, solver.name)
                if best_report is None or rep.jd_unlocked > best_report.jd_unlocked:
                    best_report = rep
            rows.append(best_report)  # type: ignore[arg-type]

    # ── Aggregate
    by_solver_group: dict[tuple[str, str], dict[str, list]] = defaultdict(lambda: defaultdict(list))
    case_group = {tc.test_id: tc.group for tc in cases}
    has_optimal = {tc.test_id for tc in cases if tc.expected_optimal is not None}

    for r in rows:
        g = case_group[r.test_id]
        key = (r.solver, g)
        if r.test_id in has_optimal:
            by_solver_group[key]["opt"].append(r.optimality_ratio)
        rt_mean = statistics.mean(runtime_runs[(r.test_id, r.solver)])
        by_solver_group[key]["runtime"].append(rt_mean)
        by_solver_group[key]["prereq"].append(1 if r.prereq_compliant else 0)
        by_solver_group[key]["budget"].append(1 if r.within_budget else 0)
        by_solver_group[key]["jd"].append(r.jd_unlocked)

    # ── Print summary
    print(f"Cases: {len(cases)}  |  N_REPEAT runtime samples: {N_REPEAT}  |  "
          f"with expected_optimal: {len(has_optimal)}\n")
    header = f"{'Solver':<10}{'Group':<14}{'n':>4}{'opt_mean':>10}{'opt_min':>10}{'rt_mean_ms':>12}{'rt_max_ms':>12}{'prereq%':>10}{'budget%':>10}{'JD_mean':>10}"
    print(header)
    print("-" * len(header))

    summary_rows: list[dict] = []
    for (solver, group) in sorted(by_solver_group):
        data = by_solver_group[(solver, group)]
        n = len(data["runtime"])
        opt_mean = round(statistics.mean(data["opt"]), 3) if data["opt"] else float("nan")
        opt_min = round(min(data["opt"]), 3) if data["opt"] else float("nan")
        rt_mean_ms = round(1000 * statistics.mean(data["runtime"]), 2)
        rt_max_ms = round(1000 * max(data["runtime"]), 2)
        prereq_pct = round(100 * statistics.mean(data["prereq"]), 1)
        budget_pct = round(100 * statistics.mean(data["budget"]), 1)
        jd_mean = round(statistics.mean(data["jd"]), 2)
        print(f"{solver:<10}{group:<14}{n:>4}"
              f"{opt_mean:>10}{opt_min:>10}{rt_mean_ms:>12}{rt_max_ms:>12}"
              f"{prereq_pct:>10}{budget_pct:>10}{jd_mean:>10}")
        summary_rows.append({
            "solver": solver, "group": group, "n": n,
            "optimality_mean": opt_mean, "optimality_min": opt_min,
            "runtime_ms_mean": rt_mean_ms, "runtime_ms_max": rt_max_ms,
            "prereq_compliance_pct": prereq_pct,
            "within_budget_pct": budget_pct,
            "jd_unlocked_mean": jd_mean,
        })

    # ── Per-solver overall row
    print()
    by_solver: dict[str, dict[str, list]] = defaultdict(lambda: defaultdict(list))
    for (solver, group), data in by_solver_group.items():
        for k, v in data.items():
            by_solver[solver][k].extend(v)
    for solver, data in sorted(by_solver.items()):
        opt_mean = round(statistics.mean(data["opt"]), 3) if data["opt"] else float("nan")
        opt_min = round(min(data["opt"]), 3) if data["opt"] else float("nan")
        rt_mean_ms = round(1000 * statistics.mean(data["runtime"]), 2)
        rt_max_ms = round(1000 * max(data["runtime"]), 2)
        prereq_pct = round(100 * statistics.mean(data["prereq"]), 1)
        budget_pct = round(100 * statistics.mean(data["budget"]), 1)
        print(f"OVERALL {solver:<10}  opt_mean={opt_mean}  opt_min={opt_min}  "
              f"rt_mean={rt_mean_ms}ms  rt_max={rt_max_ms}ms  "
              f"prereq={prereq_pct}%  budget={budget_pct}%")

    # ── Persist artifacts
    detail_path = OUT_DIR / "benchmark_results.csv"
    summary_path = OUT_DIR / "benchmark_summary.json"
    with detail_path.open("w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["test_id", "group", "solver", "jd_unlocked", "total_cost",
                    "optimality_ratio", "runtime_s_mean", "prereq_compliant",
                    "within_budget", "path"])
        for r in rows:
            g = case_group[r.test_id]
            rt_mean = statistics.mean(runtime_runs[(r.test_id, r.solver)])
            has_opt = r.test_id in has_optimal
            w.writerow([
                r.test_id, g, r.solver, r.jd_unlocked, r.total_cost,
                r.optimality_ratio if has_opt else "",
                round(rt_mean, 6),
                int(r.prereq_compliant), int(r.within_budget),
                ";".join(r.path),
            ])
    summary_path.write_text(json.dumps(summary_rows, indent=2))
    print(f"\nDetails:  {detail_path.relative_to(ROOT)}")
    print(f"Summary:  {summary_path.relative_to(ROOT)}")

    # ── Stability metric (§3.3.4 metric 3): Greedy under shuffled candidate orders
    print("\n── Greedy stability (5 random seeds, JD-count variance) ──")
    import random
    stability_failures = 0
    stability_outputs: dict[str, set[int]] = {}
    for tc in cases:
        outputs = []
        for seed in range(5):
            rng = random.Random(seed)
            tc_shuffled = _shuffle_jds(tc, rng)
            r = GreedyStrategy().solve(tc_shuffled, ontology)
            outputs.append(r.jd_unlocked)
        if len(set(outputs)) > 1:
            stability_failures += 1
            stability_outputs[tc.test_id] = set(outputs)
    if stability_failures == 0:
        print(f"  Greedy stable across 5 seeds on all {len(cases)} cases.")
    else:
        print(f"  WARNING: {stability_failures}/{len(cases)} cases vary by seed:")
        for tid, vals in stability_outputs.items():
            print(f"    {tid}: JD counts seen = {sorted(vals)}")

    # ── Tuần 13 acceptance checks
    overall_greedy_opt = (
        statistics.mean(by_solver["greedy"]["opt"]) if by_solver["greedy"]["opt"] else 0
    )
    overall_dp_opt = (
        statistics.mean(by_solver["dp"]["opt"]) if by_solver["dp"]["opt"] else 0
    )
    all_prereq = all(r.prereq_compliant for r in rows)
    all_budget = all(r.within_budget for r in rows)
    greedy_runtime_max_ms = 1000 * max(by_solver["greedy"]["runtime"])
    dijkstra_runtime_max_ms = 1000 * max(by_solver["dijkstra"]["runtime"])
    dp_runtime_max_ms = 1000 * max(by_solver["dp"]["runtime"])

    print("\n── Tuần 13 acceptance checks (per §3.3.4) ──")
    print(f"  Greedy mean optimality ≥ 0.8 ?       {overall_greedy_opt:.3f} "
          f"{'PASS' if overall_greedy_opt >= 0.8 else 'FAIL'}")
    print(f"  DP mean optimality = 1.0 (oracle)?   {overall_dp_opt:.3f} "
          f"{'PASS' if overall_dp_opt >= 0.999 else 'FAIL'}")
    print(f"  All paths prereq-compliant ?         {'PASS' if all_prereq else 'FAIL'}")
    print(f"  All paths within budget ?            {'PASS' if all_budget else 'FAIL'}")
    print(f"  Greedy runtime < 1000 ms (max) ?     {greedy_runtime_max_ms:.2f} ms "
          f"{'PASS' if greedy_runtime_max_ms < 1000 else 'FAIL'}")
    print(f"  Dijkstra runtime < 10000 ms (max) ?  {dijkstra_runtime_max_ms:.2f} ms "
          f"{'PASS' if dijkstra_runtime_max_ms < 10000 else 'FAIL'}")
    print(f"  DP runtime < 60000 ms (max) ?        {dp_runtime_max_ms:.2f} ms "
          f"{'PASS' if dp_runtime_max_ms < 60000 else 'FAIL'}")
    print(f"  Greedy stable across seeds ?         "
          f"{'PASS' if stability_failures == 0 else f'WARN ({stability_failures} cases differ)'}")

    all_pass = (
        overall_greedy_opt >= 0.8 and overall_dp_opt >= 0.999
        and all_prereq and all_budget
        and greedy_runtime_max_ms < 1000
        and dijkstra_runtime_max_ms < 10000
        and dp_runtime_max_ms < 60000
    )
    if all_pass:
        print("\nResult: BENCHMARK PASSED")
        return 0
    print("\nResult: BENCHMARK NEEDS REVIEW")
    return 1


def _shuffle_jds(tc, rng):
    """Return a shallow copy of `tc` with JDs and S_user shuffled — exercises
    Greedy tie-break under a different input order."""
    from services.skill_service.services.lp_benchmark import TestCase
    jds = list(tc.JDs)
    rng.shuffle(jds)
    s_user = list(tc.S_user)
    rng.shuffle(s_user)
    return TestCase(
        test_id=tc.test_id, description=tc.description, role=tc.role,
        S_user=s_user, JDs=jds, budget=tc.budget,
        expected_optimal=tc.expected_optimal, group=tc.group,
    )


if __name__ == "__main__":
    sys.exit(main())
