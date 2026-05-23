"""Search for Learning-Path adversarial test cases — instances where the Greedy
ROI heuristic falls short of the DP oracle. Goal: 10+ cases với Greedy < DP
to sharpen the trade-off picture in Chương 4.5.

Strategy: enumerate parameterized templates of Budgeted Max Coverage hard
instances. For each candidate, run Greedy + DP; keep when DP > Greedy.

Run từ repo root:
    PYTHONPATH=. python3 services/skill_service/scripts/generate_lp_adversarial.py
"""
from __future__ import annotations

import json
import sys
from itertools import product
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from services.skill_service.services.learning_path import GreedyStrategy, DPStrategy  # noqa
from services.skill_service.services.lp_benchmark import TestCase, JD, ExpectedOptimal  # noqa
from services.skill_service.services.ontology import SkillOntology, get_skill_cost  # noqa


CASES_PATH = ROOT / "services/skill_service/data/learning_path_benchmark/cases.json"
OUT_PATH = ROOT / "services/skill_service/data/learning_path_benchmark/adversarial_candidates.json"


def make_tc(tid, desc, role, S_user, jds, budget) -> TestCase:
    return TestCase(
        test_id=tid, description=desc, role=role, group="adversarial",
        S_user=list(S_user),
        JDs=[JD(id=jid, required=list(req)) for jid, req in jds],
        budget=budget,
    )


# ─── Template 1 — "Bait single-skill JD": a tiny cheap JD lures Greedy into a
# choice that prevents finishing a costlier multi-skill JD cluster.
# Owned: {Python}.
# JDs: jd_bait needs {cheap}, jd_cluster_N each needs {Python, skill_i}.
# Budget = sum of `cheap` + N·cost(skill_i) but leaves no room for bait when
# we also need cluster.

def gen_bait_cases():
    onto = SkillOntology()
    cheap_baits = [("Tailwind CSS", 1), ("HTML", 1), ("CSS", 2)]
    cluster_skills = [("Docker", 2), ("Redis", 2), ("FastAPI", 2), ("Express.js", 2),
                      ("REST", 2), ("GraphQL", 2), ("dbt", 2), ("Pandas", 2)]
    cases = []
    n = 0
    for bait, bcost in cheap_baits:
        for cluster_n in (3, 4):
            cluster = cluster_skills[:cluster_n]
            cluster_cost = sum(c for _, c in cluster)
            # Budget: bait + (cluster_n-1) cluster items → Greedy picks bait + few cluster
            # Optimal: skip bait → cluster_n cluster items + 1 JD missed
            for delta in (0, 1):
                budget = bcost + cluster_cost - (cluster[0][1] + delta)
                if budget <= bcost:
                    continue
                S_user = ["Python"]
                jds = [("jd_bait", [bait])]
                for i, (sk, _) in enumerate(cluster):
                    jds.append((f"jd_c{i}", ["Python", sk]))
                tc = make_tc(
                    f"adv_bait_{n:02d}",
                    f"Cheap bait {bait} + {cluster_n} cluster JDs, B={budget}",
                    "backend", S_user, jds, budget,
                )
                cases.append(tc)
                n += 1
    return cases


# ─── Template 2 — "Diminishing chain": a skill with prereq chain looks tempting
# (one big chain unlocks 1 JD), but optimal splits budget across several cheap
# single-skill JDs.

def gen_chain_cases():
    cases = []
    n = 0
    # Owned: empty. Build cases where one chain (Python→Django→PostgreSQL, cost ~11)
    # unlocks 1 JD but optimal picks N cheaper single-skill JDs.
    chain_targets = ["Spring Boot", "PyTorch", "Kubernetes"]
    cheap_singles = [("Tailwind CSS", 1), ("HTML", 1), ("CSS", 2), ("Redis", 2),
                     ("Express.js", 2), ("REST", 2), ("dbt", 2)]
    for chain_skill in chain_targets:
        for k in (3, 4, 5):
            singles = cheap_singles[:k]
            cheap_cost = sum(c for _, c in singles)
            # Make budget tight: chain_cost == cheap_cost
            for budget in (cheap_cost, cheap_cost + 1):
                S_user = ["Python"]  # gives some baseline
                jds = [("jd_big", ["Python", chain_skill])]
                for i, (sk, _) in enumerate(singles):
                    jds.append((f"jd_s{i}", [sk]))
                tc = make_tc(
                    f"adv_chain_{n:02d}",
                    f"Big chain {chain_skill} vs {k} cheap singles, B={budget}",
                    "backend", S_user, jds, budget,
                )
                cases.append(tc)
                n += 1
    return cases


# ─── Template 3 — "Shared prereq trap": two JDs share a costly prereq but
# only one of them has additional unique skills that fit budget.

def gen_shared_prereq_cases():
    cases = []
    n = 0
    # Two clusters share a common skill X. Greedy picks X + small extras,
    # but optimal swaps to a different base that unlocks more JDs.
    bases = [
        ("Kubernetes", 6, [("Docker", 2)]),
        ("Spring Boot", 5, [("Java", 5)]),
        ("PyTorch", 5, [("Python", 4)]),
    ]
    for base, _base_cost, prereqs in bases:
        for n_jds in (3, 4):
            S_user: list[str] = []
            jds = []
            jds.append(("jd_base1", [base]))
            jds.append(("jd_base2", [base, "Redis"]))
            # Add cheap competing JDs
            cheap = [("Tailwind CSS", 1), ("HTML", 1), ("CSS", 2),
                     ("Express.js", 2)][:n_jds]
            for i, (sk, _) in enumerate(cheap):
                jds.append((f"jd_alt{i}", [sk]))
            cheap_cost = sum(c for _, c in cheap)
            # Budget covers base+1 alt OR all cheap
            for budget in (cheap_cost + 1, cheap_cost + 2):
                tc = make_tc(
                    f"adv_shared_{n:02d}",
                    f"Shared prereq {base} vs {n_jds} cheap, B={budget}",
                    "backend", S_user, jds, budget,
                )
                cases.append(tc)
                n += 1
    return cases


# ─── Template 4 — "Multi-skill coverage maze": every JD needs ≥2 skills, with
# overlapping requirements. Greedy's fractional fallback may pick wrong skill.

def gen_maze_cases():
    cases = []
    n = 0
    # 4 skills, 4 JDs each requiring 2 skills (a complete K2,4-style design)
    skill_pools = [
        ["Docker", "Redis", "FastAPI", "PostgreSQL"],
        ["TypeScript", "React", "Next.js", "Redux"],
        ["dbt", "Snowflake", "Airflow", "Pandas"],
    ]
    for pool in skill_pools:
        s = pool
        jds = [
            ("jd_ab", [s[0], s[1]]),
            ("jd_cd", [s[2], s[3]]),
            ("jd_ac", [s[0], s[2]]),
            ("jd_bd", [s[1], s[3]]),
        ]
        # Skills cost roughly 2-3 each → budget tight at ~6-8
        for budget in (6, 7, 8, 9):
            tc = make_tc(
                f"adv_maze_{n:02d}",
                f"Maze with pool {pool[0]}/{pool[2]}, B={budget}",
                "backend", [], jds, budget,
            )
            cases.append(tc)
            n += 1
    return cases


def run_greedy_vs_dp(tc, onto, greedy, dp):
    g = greedy.solve(tc, onto)
    d = dp.solve(tc, onto)
    return g.jd_unlocked, d.jd_unlocked, g.total_cost, d.total_cost


def main() -> int:
    onto = SkillOntology()
    greedy = GreedyStrategy()
    dp = DPStrategy(max_candidates=30)

    candidates = []
    for gen in (gen_bait_cases, gen_chain_cases, gen_shared_prereq_cases, gen_maze_cases):
        candidates.extend(gen())

    print(f"Generated {len(candidates)} candidate cases. Testing Greedy vs DP...\n")
    kept: list[tuple[TestCase, int, int]] = []
    for tc in candidates:
        try:
            g_jd, d_jd, g_c, d_c = run_greedy_vs_dp(tc, onto, greedy, dp)
        except Exception as e:
            print(f"  [skip] {tc.test_id}: {e}")
            continue
        marker = "GAP" if d_jd > g_jd else "  -"
        print(f"  {marker} {tc.test_id:<22} budget={tc.budget:>2}  greedy={g_jd}  dp={d_jd}")
        if d_jd > g_jd:
            kept.append((tc, g_jd, d_jd))

    print(f"\n→ {len(kept)} cases where DP > Greedy.")

    if not kept:
        print("No adversarial cases found. Need to tweak templates.")
        return 1

    # Emit as JSON in the same schema as cases.json
    out = []
    for tc, g_jd, d_jd in kept:
        out.append({
            "test_id": tc.test_id,
            "description": tc.description,
            "role": tc.role,
            "group": "adversarial",
            "S_user": tc.S_user,
            "JDs": [{"id": j.id, "required": j.required} for j in tc.JDs],
            "budget": tc.budget,
            "expected_optimal": {
                "skills": [],  # DP fills exact path during benchmark
                "jd_unlocked": d_jd,
                "total_cost": 0,
            },
            "_greedy_jd_when_generated": g_jd,
        })
    OUT_PATH.write_text(json.dumps(out, indent=2, ensure_ascii=False))
    print(f"Wrote → {OUT_PATH}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
