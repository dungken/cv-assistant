"""
Task 4.1: Evaluate Skill Matcher accuracy.
Tests ontology-based matching, semantic matching, and overall scoring
on predefined test cases with known ground truth.
"""

import sys
import json
import argparse
from pathlib import Path
from collections import defaultdict

sys.path.insert(0, str(Path(__file__).parent.parent))

from services.skill_service.services.ontology import SkillOntology


# ─── Test Cases ──────────────────────────────────────────────────────────────

TEST_CASES = [
    {
        "id": "TC001",
        "description": "Frontend Developer - exact skills",
        "cv_skills": ["React", "JavaScript", "CSS3", "HTML5", "Git", "Redux"],
        "jd_skills": ["React", "JavaScript", "CSS", "HTML", "Git", "State Management"],
        "expected_score_min": 70,
        "expected_exact_min": 3,
    },
    {
        "id": "TC002",
        "description": "Frontend Developer - framework substitution",
        "cv_skills": ["Vue.js", "JavaScript", "TypeScript", "Nuxt.js", "Tailwind CSS"],
        "jd_skills": ["React", "JavaScript", "TypeScript", "Next.js", "CSS Framework"],
        "expected_score_min": 40,
        "expected_ontology_min": 2,  # Vue->React, Nuxt->Next should match via ontology
    },
    {
        "id": "TC003",
        "description": "Backend Developer - database equivalence",
        "cv_skills": ["Python", "Django", "PostgreSQL", "Redis", "Docker"],
        "jd_skills": ["Python", "Flask", "MySQL", "Memcached", "Docker"],
        "expected_score_min": 50,
        "expected_ontology_min": 2,  # Django-Flask, PostgreSQL-MySQL
    },
    {
        "id": "TC004",
        "description": "DevOps Engineer - cloud platform substitution",
        "cv_skills": ["AWS", "Terraform", "Docker", "Kubernetes", "Jenkins", "Linux"],
        "jd_skills": ["Azure", "Terraform", "Docker", "Kubernetes", "GitHub Actions", "Linux"],
        "expected_score_min": 60,
        "expected_ontology_min": 1,  # AWS-Azure
    },
    {
        "id": "TC005",
        "description": "Data Scientist - ML framework equivalence",
        "cv_skills": ["Python", "TensorFlow", "Pandas", "Scikit-learn", "SQL"],
        "jd_skills": ["Python", "PyTorch", "Pandas", "XGBoost", "SQL"],
        "expected_score_min": 50,
        "expected_ontology_min": 1,  # TensorFlow-PyTorch
    },
    {
        "id": "TC006",
        "description": "Full Stack - broad skill mismatch",
        "cv_skills": ["Python", "Django", "PostgreSQL"],
        "jd_skills": ["React", "Node.js", "MongoDB", "TypeScript", "GraphQL", "Docker", "AWS"],
        "expected_score_min": 0,
        "expected_score_max": 30,
    },
    {
        "id": "TC007",
        "description": "Perfect match",
        "cv_skills": ["Python", "FastAPI", "PostgreSQL", "Docker", "Git"],
        "jd_skills": ["Python", "FastAPI", "PostgreSQL", "Docker", "Git"],
        "expected_score_min": 95,
        "expected_exact_min": 5,
    },
    {
        "id": "TC008",
        "description": "Mobile cross-platform substitution",
        "cv_skills": ["Flutter", "Dart", "Firebase", "Git", "REST API"],
        "jd_skills": ["React Native", "JavaScript", "Firebase", "Git", "REST API"],
        "expected_score_min": 40,
        "expected_ontology_min": 1,  # Flutter-React Native
    },
    {
        "id": "TC009",
        "description": "Security role - tool substitution",
        "cv_skills": ["Burp Suite", "OWASP", "Python", "Nmap", "Linux"],
        "jd_skills": ["Metasploit", "OWASP", "Python", "Nessus", "Linux"],
        "expected_score_min": 50,
        "expected_ontology_min": 1,  # Burp-Metasploit, Nmap-Nessus
    },
    {
        "id": "TC010",
        "description": "CI/CD tool equivalence",
        "cv_skills": ["Jenkins", "Docker", "Terraform", "AWS", "Git"],
        "jd_skills": ["GitHub Actions", "Docker", "Terraform", "AWS", "Git"],
        "expected_score_min": 70,
        "expected_ontology_min": 1,  # Jenkins-GitHub Actions
    },
]


def evaluate_ontology_matching(ontology: SkillOntology, test_cases: list[dict]) -> dict:
    """Evaluate ontology matching accuracy on test cases."""
    results = []
    passed = 0
    failed = 0

    for tc in test_cases:
        cv_lower = [s.lower() for s in tc["cv_skills"]]
        jd_lower = [s.lower() for s in tc["jd_skills"]]

        # Exact matches
        exact = list(set(cv_lower) & set(jd_lower))

        # Ontology matches
        ontology_matches = []
        matched_jd = set(exact)
        remaining_jd = [s for s in jd_lower if s not in matched_jd]

        for jd_skill in remaining_jd:
            best_dist = 1.0
            best_cv = None
            for cv_skill in cv_lower:
                dist = ontology.skill_distance(cv_skill, jd_skill)
                if dist < best_dist:
                    best_dist = dist
                    best_cv = cv_skill
            if best_dist <= 0.2 and best_cv:
                ontology_matches.append({
                    "cv": best_cv, "jd": jd_skill,
                    "distance": best_dist,
                    "explanation": ontology.explain_relationship(best_cv, jd_skill)
                })
                matched_jd.add(jd_skill)

        # Score
        total_jd = max(1, len(jd_lower))
        score = min(100, round(
            (len(exact) * 1.0 + len(ontology_matches) * 0.85) / total_jd * 100, 1
        ))

        # Check assertions
        test_passed = True
        issues = []

        if "expected_score_min" in tc and score < tc["expected_score_min"]:
            test_passed = False
            issues.append(f"Score {score} < expected min {tc['expected_score_min']}")
        if "expected_score_max" in tc and score > tc["expected_score_max"]:
            test_passed = False
            issues.append(f"Score {score} > expected max {tc['expected_score_max']}")
        if "expected_exact_min" in tc and len(exact) < tc["expected_exact_min"]:
            test_passed = False
            issues.append(f"Exact matches {len(exact)} < expected min {tc['expected_exact_min']}")
        if "expected_ontology_min" in tc and len(ontology_matches) < tc["expected_ontology_min"]:
            test_passed = False
            issues.append(f"Ontology matches {len(ontology_matches)} < expected min {tc['expected_ontology_min']}")

        if test_passed:
            passed += 1
        else:
            failed += 1

        results.append({
            "id": tc["id"],
            "description": tc["description"],
            "score": score,
            "exact_matches": len(exact),
            "ontology_matches": len(ontology_matches),
            "ontology_details": ontology_matches,
            "passed": test_passed,
            "issues": issues,
        })

    return {
        "total": len(test_cases),
        "passed": passed,
        "failed": failed,
        "accuracy": round(passed / max(1, len(test_cases)) * 100, 1),
        "results": results,
    }


def print_report(evaluation: dict, output_file: str = None):
    """Print and optionally save evaluation report."""
    lines = []
    lines.append("=" * 70)
    lines.append("  Skill Matcher Evaluation Report")
    lines.append("=" * 70)
    lines.append(f"\nTotal test cases: {evaluation['total']}")
    lines.append(f"Passed: {evaluation['passed']}")
    lines.append(f"Failed: {evaluation['failed']}")
    lines.append(f"Accuracy: {evaluation['accuracy']}%")
    lines.append("")

    for r in evaluation["results"]:
        status = "PASS" if r["passed"] else "FAIL"
        lines.append(f"[{status}] {r['id']}: {r['description']}")
        lines.append(f"       Score: {r['score']}% | Exact: {r['exact_matches']} | Ontology: {r['ontology_matches']}")
        if r["ontology_details"]:
            for om in r["ontology_details"]:
                lines.append(f"         -> {om['cv']} ~ {om['jd']} (dist={om['distance']})")
        if r["issues"]:
            for issue in r["issues"]:
                lines.append(f"       ISSUE: {issue}")
        lines.append("")

    text = "\n".join(lines)
    print(text)

    if output_file:
        Path(output_file).parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, "w") as f:
            f.write(text)
        print(f"Report saved to {output_file}")


def main():
    parser = argparse.ArgumentParser(description="Evaluate Skill Matcher accuracy")
    parser.add_argument("--output", type=str, default="reports/matcher_evaluation.txt")
    args = parser.parse_args()

    print("Initializing Skill Ontology...")
    ontology = SkillOntology()

    print(f"Running {len(TEST_CASES)} test cases...\n")
    evaluation = evaluate_ontology_matching(ontology, TEST_CASES)

    print_report(evaluation, args.output)


if __name__ == "__main__":
    main()
