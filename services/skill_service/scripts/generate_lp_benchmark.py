"""Tuần 11 — generate the 50-test-case benchmark for Learning Path Optimizer.

Distribution per §3.3.4:
- Group 1 (small,        n=10): ≤3 skills user, ≤5 JDs, budget ≤5 — correctness
- Group 2 (tight budget, n=10): budget only fits 2-3 skills — priority test
- Group 3 (wide budget,  n=10): budget fits 8-10 skills, many varied JDs
- Group 4 (deep prereq,  n=10): REQUIRES chains of depth 3-4
- Group 5 (real,         n=10): scenarios drawn from real CV/JD shapes

Cases small enough for brute force get `expected_optimal` stamped from the
oracle. Larger cases leave it `None`; DP from Tuần 13 will fill them.

Run:
    PYTHONPATH=. python3 services/skill_service/scripts/generate_lp_benchmark.py
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from services.skill_service.services.lp_benchmark import (
    JD, TestCase, candidates_for, dump_cases, fill_expected_optimal,
)
from services.skill_service.services.ontology import SkillOntology


OUT = ROOT / "services" / "skill_service" / "data" / "learning_path_benchmark" / "cases.json"


# ─── Group 1 — small, correctness ─────────────────────────────────────────────

def group1_small() -> list[TestCase]:
    cases: list[TestCase] = []

    cases.append(TestCase(
        test_id="g1_001", group="small", role="frontend",
        description="Junior FE, two clear React JDs, budget 5",
        S_user=["HTML", "CSS", "JavaScript"],
        JDs=[
            JD("jd_a", ["JavaScript", "React"]),
            JD("jd_b", ["JavaScript", "React", "TypeScript"]),
            JD("jd_c", ["JavaScript", "Vue.js"]),
        ],
        budget=5,
    ))
    cases.append(TestCase(
        test_id="g1_002", group="small", role="backend",
        description="Pythonista vs Django/Flask JDs",
        S_user=["Python", "SQL"],
        JDs=[
            JD("jd_a", ["Python", "Django"]),
            JD("jd_b", ["Python", "Flask", "PostgreSQL"]),
            JD("jd_c", ["Python", "FastAPI"]),
        ],
        budget=6,
    ))
    cases.append(TestCase(
        test_id="g1_003", group="small", role="data",
        description="SQL analyst → modern analytics",
        S_user=["SQL"],
        JDs=[
            JD("jd_a", ["SQL", "Python", "Pandas"]),
            JD("jd_b", ["SQL", "Tableau"]),
        ],
        budget=6,
    ))
    cases.append(TestCase(
        test_id="g1_004", group="small", role="devops",
        description="Linux admin → Docker",
        S_user=["Linux", "Bash"],
        JDs=[
            JD("jd_a", ["Linux", "Docker"]),
            JD("jd_b", ["Linux", "Docker", "Kubernetes"]),
        ],
        budget=5,
    ))
    cases.append(TestCase(
        test_id="g1_005", group="small", role="frontend",
        description="Already covers one JD, decide if to grow further",
        S_user=["HTML", "CSS", "JavaScript", "React"],
        JDs=[
            JD("jd_a", ["JavaScript", "React"]),
            JD("jd_b", ["JavaScript", "React", "Next.js"]),
            JD("jd_c", ["JavaScript", "TypeScript", "React"]),
        ],
        budget=4,
    ))
    cases.append(TestCase(
        test_id="g1_006", group="small", role="ai_engineer",
        description="Pythonista → ML basics",
        S_user=["Python"],
        JDs=[
            JD("jd_a", ["Python", "Pandas", "NumPy"]),
            JD("jd_b", ["Python", "Scikit-learn"]),
        ],
        budget=5,
    ))
    cases.append(TestCase(
        test_id="g1_007", group="small", role="backend",
        description="Java/Spring path",
        S_user=["Java"],
        JDs=[
            JD("jd_a", ["Java", "Spring Boot"]),
            JD("jd_b", ["Java", "Spring Boot", "PostgreSQL"]),
        ],
        budget=5,
    ))
    cases.append(TestCase(
        test_id="g1_008", group="small", role="frontend",
        description="Tight: only one JD reachable",
        S_user=["HTML", "CSS"],
        JDs=[
            JD("jd_a", ["JavaScript"]),
            JD("jd_b", ["JavaScript", "React"]),
            JD("jd_c", ["TypeScript", "Angular"]),
        ],
        budget=4,
    ))
    cases.append(TestCase(
        test_id="g1_009", group="small", role="data",
        description="Big-data ETL",
        S_user=["Python", "SQL"],
        JDs=[
            JD("jd_a", ["Python", "SQL", "Apache Airflow"]),
            JD("jd_b", ["Python", "Apache Spark"]),
        ],
        budget=5,
    ))
    cases.append(TestCase(
        test_id="g1_010", group="small", role="devops",
        description="Docker → orchestration",
        S_user=["Docker", "Linux"],
        JDs=[
            JD("jd_a", ["Docker", "Kubernetes"]),
            JD("jd_b", ["Docker", "Kubernetes", "Helm"]),
        ],
        budget=5,
    ))

    return cases


# ─── Group 2 — tight budget ───────────────────────────────────────────────────

def group2_tight_budget() -> list[TestCase]:
    cases: list[TestCase] = []
    base_jds_be = [
        JD("jd_a", ["Python", "FastAPI", "PostgreSQL"]),
        JD("jd_b", ["Python", "Django", "PostgreSQL"]),
        JD("jd_c", ["Python", "FastAPI", "Redis"]),
        JD("jd_d", ["Python", "Flask", "MongoDB"]),
        JD("jd_e", ["Python", "Django", "MySQL"]),
    ]
    for i, b in enumerate([2, 3, 3, 4, 4], start=1):
        cases.append(TestCase(
            test_id=f"g2_{i:03d}", group="tight_budget", role="backend",
            description=f"Backend candidate, very tight budget={b}",
            S_user=["Python"],
            JDs=base_jds_be,
            budget=b,
        ))

    base_jds_fe = [
        JD("jd_a", ["JavaScript", "React", "TypeScript"]),
        JD("jd_b", ["JavaScript", "Vue.js"]),
        JD("jd_c", ["JavaScript", "React", "Next.js"]),
        JD("jd_d", ["JavaScript", "Angular"]),
        JD("jd_e", ["JavaScript", "Svelte"]),
    ]
    for i, b in enumerate([2, 3, 4, 4, 5], start=6):
        cases.append(TestCase(
            test_id=f"g2_{i:03d}", group="tight_budget", role="frontend",
            description=f"Frontend candidate, tight budget={b}",
            S_user=["HTML", "CSS", "JavaScript"],
            JDs=base_jds_fe,
            budget=b,
        ))

    return cases


# ─── Group 3 — wide budget (DP needed for ground truth) ───────────────────────

def group3_wide_budget() -> list[TestCase]:
    cases: list[TestCase] = []
    big_be_jds = [
        JD(f"jd_{i:02d}", req) for i, req in enumerate([
            ["Python", "FastAPI", "PostgreSQL", "Docker"],
            ["Python", "Django", "PostgreSQL", "Redis"],
            ["Python", "Flask", "MongoDB"],
            ["Java", "Spring Boot", "PostgreSQL"],
            ["Node.js", "Express.js", "MongoDB"],
            ["Go", "PostgreSQL", "Docker"],
            ["Python", "FastAPI", "Apache Kafka"],
            ["Python", "Django", "AWS"],
            ["Java", "Spring Boot", "Kafka", "Kubernetes"],
            ["Python", "FastAPI", "Redis", "Docker"],
            ["Node.js", "NestJS", "PostgreSQL"],
            ["Python", "FastAPI", "Microservices"],
        ], start=1)
    ]
    for i, b in enumerate([12, 14, 16, 18, 20], start=1):
        cases.append(TestCase(
            test_id=f"g3_{i:03d}", group="wide_budget", role="backend",
            description=f"Backend, wide budget={b}, 12 diverse JDs",
            S_user=["Python", "Git"],
            JDs=big_be_jds,
            budget=b,
        ))

    big_fe_jds = [
        JD(f"jd_{i:02d}", req) for i, req in enumerate([
            ["JavaScript", "React", "TypeScript"],
            ["JavaScript", "React", "Next.js"],
            ["JavaScript", "Vue.js", "Pinia"],
            ["JavaScript", "Vue.js", "Nuxt.js"],
            ["JavaScript", "Angular", "TypeScript"],
            ["JavaScript", "Svelte"],
            ["JavaScript", "React", "Tailwind CSS"],
            ["JavaScript", "React", "Redux"],
            ["JavaScript", "TypeScript", "Vite"],
            ["JavaScript", "React", "Jest"],
            ["JavaScript", "React", "Storybook"],
            ["JavaScript", "Vue.js", "Tailwind CSS"],
        ], start=1)
    ]
    for i, b in enumerate([12, 14, 16, 18, 20], start=6):
        cases.append(TestCase(
            test_id=f"g3_{i:03d}", group="wide_budget", role="frontend",
            description=f"Frontend, wide budget={b}, 12 diverse JDs",
            S_user=["HTML", "CSS", "JavaScript", "Git"],
            JDs=big_fe_jds,
            budget=b,
        ))

    return cases


# ─── Group 4 — deep prereqs ───────────────────────────────────────────────────

def group4_deep_prereq() -> list[TestCase]:
    cases: list[TestCase] = []

    # FE chain: JavaScript → React → Next.js  (3 levels via REQUIRES in ontology)
    cases.append(TestCase(
        test_id="g4_001", group="deep_prereq", role="frontend",
        description="Empty start; JD requires Next.js — chain 3 levels deep",
        S_user=[],
        JDs=[JD("jd_a", ["Next.js"])],
        budget=10,
    ))
    cases.append(TestCase(
        test_id="g4_002", group="deep_prereq", role="frontend",
        description="HTML/CSS only; JD requires Redux + Next.js",
        S_user=["HTML", "CSS"],
        JDs=[JD("jd_a", ["Next.js", "Redux"])],
        budget=12,
    ))
    cases.append(TestCase(
        test_id="g4_003", group="deep_prereq", role="frontend",
        description="JS only; two JDs sharing React prereq",
        S_user=["JavaScript"],
        JDs=[
            JD("jd_a", ["React", "Next.js"]),
            JD("jd_b", ["React", "Redux"]),
        ],
        budget=8,
    ))
    # BE chain: Python → Django  (Spring Boot REQUIRES Java)
    cases.append(TestCase(
        test_id="g4_004", group="deep_prereq", role="backend",
        description="Empty start; chain Java → Spring Boot",
        S_user=[],
        JDs=[JD("jd_a", ["Spring Boot"])],
        budget=10,
    ))
    cases.append(TestCase(
        test_id="g4_005", group="deep_prereq", role="backend",
        description="Empty; FastAPI chain (Python → FastAPI)",
        S_user=[],
        JDs=[JD("jd_a", ["FastAPI", "PostgreSQL"])],
        budget=10,
    ))
    # DevOps chain: Docker → Kubernetes → Helm
    cases.append(TestCase(
        test_id="g4_006", group="deep_prereq", role="devops",
        description="Linux only; reach Helm (3-level chain)",
        S_user=["Linux"],
        JDs=[JD("jd_a", ["Helm"])],
        budget=10,
    ))
    cases.append(TestCase(
        test_id="g4_007", group="deep_prereq", role="devops",
        description="Linux only; reach ArgoCD (Docker→Kubernetes→ArgoCD)",
        S_user=["Linux"],
        JDs=[JD("jd_a", ["ArgoCD"])],
        budget=12,
    ))
    # Data chain: Python → Pandas → ML
    cases.append(TestCase(
        test_id="g4_008", group="deep_prereq", role="data",
        description="Empty; chain Python → Pandas → Scikit-learn",
        S_user=[],
        JDs=[JD("jd_a", ["Scikit-learn"])],
        budget=8,
    ))
    cases.append(TestCase(
        test_id="g4_009", group="deep_prereq", role="ai_engineer",
        description="Empty; chain to PyTorch + Hugging Face",
        S_user=[],
        JDs=[JD("jd_a", ["PyTorch", "Hugging Face"])],
        budget=14,
    ))
    cases.append(TestCase(
        test_id="g4_010", group="deep_prereq", role="frontend",
        description="HTML/CSS; two long chains compete (React→Next vs Vue→Nuxt)",
        S_user=["HTML", "CSS"],
        JDs=[
            JD("jd_a", ["Next.js"]),
            JD("jd_b", ["Nuxt.js"]),
        ],
        budget=8,
    ))

    return cases


# ─── Group 5 — realistic shape (DP/manual will fill optimal in Tuần 13) ───────

def group5_real() -> list[TestCase]:
    real_be_jds = [
        JD("jd_r01", ["Python", "FastAPI", "PostgreSQL", "Docker", "AWS"]),
        JD("jd_r02", ["Python", "Django", "PostgreSQL", "Redis", "Docker"]),
        JD("jd_r03", ["Java", "Spring Boot", "PostgreSQL", "Docker", "Kubernetes"]),
        JD("jd_r04", ["Python", "Flask", "MongoDB", "Docker"]),
        JD("jd_r05", ["Node.js", "NestJS", "PostgreSQL", "Docker"]),
    ]
    real_fe_jds = [
        JD("jd_r01", ["JavaScript", "TypeScript", "React", "Next.js", "Tailwind CSS"]),
        JD("jd_r02", ["JavaScript", "TypeScript", "React", "Redux", "Jest"]),
        JD("jd_r03", ["JavaScript", "Vue.js", "Pinia", "Nuxt.js", "Tailwind CSS"]),
        JD("jd_r04", ["JavaScript", "TypeScript", "Angular"]),
        JD("jd_r05", ["JavaScript", "React", "TypeScript", "GraphQL"]),
    ]
    real_data_jds = [
        JD("jd_r01", ["Python", "SQL", "Pandas", "Apache Airflow", "Snowflake"]),
        JD("jd_r02", ["Python", "SQL", "dbt", "Snowflake"]),
        JD("jd_r03", ["Python", "Apache Spark", "Apache Kafka", "AWS"]),
        JD("jd_r04", ["SQL", "Tableau", "Python"]),
    ]
    real_devops_jds = [
        JD("jd_r01", ["Linux", "Docker", "Kubernetes", "Terraform", "AWS"]),
        JD("jd_r02", ["Linux", "Docker", "Kubernetes", "Helm", "ArgoCD"]),
        JD("jd_r03", ["Linux", "Docker", "Azure", "GitHub Actions"]),
        JD("jd_r04", ["Linux", "Docker", "Kubernetes", "Prometheus", "Grafana"]),
    ]
    real_ai_jds = [
        JD("jd_r01", ["Python", "PyTorch", "Hugging Face", "FastAPI", "Docker"]),
        JD("jd_r02", ["Python", "TensorFlow", "Scikit-learn", "Pandas", "NumPy"]),
        JD("jd_r03", ["Python", "PyTorch", "LangChain", "FastAPI"]),
    ]

    cases: list[TestCase] = []
    cases.append(TestCase(
        test_id="g5_001", group="real", role="backend",
        description="BE candidate w/ Python+SQL chooses among 5 real-shape JDs",
        S_user=["Python", "SQL", "Git"],
        JDs=real_be_jds, budget=12,
    ))
    cases.append(TestCase(
        test_id="g5_002", group="real", role="backend",
        description="BE candidate w/ Java only",
        S_user=["Java", "Git"], JDs=real_be_jds, budget=14,
    ))
    cases.append(TestCase(
        test_id="g5_003", group="real", role="frontend",
        description="FE candidate w/ HTML+CSS+JS",
        S_user=["HTML", "CSS", "JavaScript", "Git"],
        JDs=real_fe_jds, budget=12,
    ))
    cases.append(TestCase(
        test_id="g5_004", group="real", role="frontend",
        description="FE candidate already has React",
        S_user=["HTML", "CSS", "JavaScript", "React", "Git"],
        JDs=real_fe_jds, budget=10,
    ))
    cases.append(TestCase(
        test_id="g5_005", group="real", role="data",
        description="Data candidate w/ Python only",
        S_user=["Python", "Git"], JDs=real_data_jds, budget=10,
    ))
    cases.append(TestCase(
        test_id="g5_006", group="real", role="data",
        description="Data candidate w/ SQL only — needs to pick up Python first",
        S_user=["SQL", "Git"], JDs=real_data_jds, budget=12,
    ))
    cases.append(TestCase(
        test_id="g5_007", group="real", role="devops",
        description="DevOps candidate w/ Linux + Docker",
        S_user=["Linux", "Docker", "Git"],
        JDs=real_devops_jds, budget=14,
    ))
    cases.append(TestCase(
        test_id="g5_008", group="real", role="devops",
        description="Sysadmin migrating to cloud-native",
        S_user=["Linux", "Bash", "Git"],
        JDs=real_devops_jds, budget=18,
    ))
    cases.append(TestCase(
        test_id="g5_009", group="real", role="ai_engineer",
        description="AI candidate w/ Python+Pandas",
        S_user=["Python", "Pandas", "NumPy", "Git"],
        JDs=real_ai_jds, budget=14,
    ))
    cases.append(TestCase(
        test_id="g5_010", group="real", role="ai_engineer",
        description="AI candidate empty start",
        S_user=["Git"], JDs=real_ai_jds, budget=18,
    ))
    return cases


# ─── Main ─────────────────────────────────────────────────────────────────────


def main() -> int:
    ontology = SkillOntology()
    cases: list[TestCase] = []
    cases.extend(group1_small())
    cases.extend(group2_tight_budget())
    cases.extend(group3_wide_budget())
    cases.extend(group4_deep_prereq())
    cases.extend(group5_real())

    # Stamp expected_optimal where brute force can handle it.
    filled, skipped = 0, 0
    for tc in cases:
        n_cand = len(candidates_for(tc))
        if n_cand <= 12:
            try:
                fill_expected_optimal(tc, ontology)
                filled += 1
            except ValueError:
                skipped += 1
        else:
            skipped += 1

    OUT.parent.mkdir(parents=True, exist_ok=True)
    dump_cases(cases, OUT)

    by_group: dict[str, int] = {}
    for tc in cases:
        by_group[tc.group] = by_group.get(tc.group, 0) + 1
    print(f"Wrote {len(cases)} test cases → {OUT.relative_to(ROOT)}")
    print("By group:", ", ".join(f"{k}={v}" for k, v in sorted(by_group.items())))
    print(f"expected_optimal filled by brute force: {filled} / {len(cases)} "
          f"(skipped {skipped} — DP oracle in Tuần 13 will fill the rest)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
