"""Learning Path Optimizer benchmark scaffold (Tuần 11).

Provides:
- TestCase dataclass mirroring the JSON schema from §3.3.4.
- A reference brute-force solver (`solve_brute_force`) usable as ground truth
  for small test cases (|candidates| ≤ ~12). The Tuần 13 DP implementation
  will replace this as the canonical "optimal" oracle for larger cases.
- `evaluate_path` — given a candidate path and a test case, computes the four
  benchmark metrics from §3.3.4 (optimality, runtime, stability, prereq-compliance).

The actual Greedy/Dijkstra/DP strategies arrive in Tuần 12-13; this module is
strategy-agnostic so each one can plug in via the `Solver` protocol below.
"""
from __future__ import annotations

import itertools
import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Iterable, Optional, Protocol

from services.skill_service.services.ontology import (
    REQUIRES, SkillOntology, get_skill_cost,
)


# ─── Schema ───────────────────────────────────────────────────────────────────


@dataclass
class JD:
    id: str
    required: list[str]  # canonical skill names


@dataclass
class ExpectedOptimal:
    skills: list[str]
    jd_unlocked: int
    total_cost: int


@dataclass
class TestCase:
    test_id: str
    description: str
    role: str
    S_user: list[str]
    JDs: list[JD]
    budget: int
    expected_optimal: Optional[ExpectedOptimal] = None
    group: str = "unknown"  # one of: small, tight_budget, wide_budget, deep_prereq, real

    @staticmethod
    def from_dict(d: dict) -> "TestCase":
        eo = d.get("expected_optimal")
        return TestCase(
            test_id=d["test_id"],
            description=d.get("description", ""),
            role=d.get("role", "backend"),
            S_user=list(d["S_user"]),
            JDs=[JD(id=j["id"], required=list(j["required"])) for j in d["JDs"]],
            budget=int(d["budget"]),
            expected_optimal=ExpectedOptimal(**eo) if eo else None,
            group=d.get("group", "unknown"),
        )

    def to_dict(self) -> dict:
        return {
            "test_id": self.test_id,
            "description": self.description,
            "role": self.role,
            "group": self.group,
            "S_user": self.S_user,
            "JDs": [j.__dict__ for j in self.JDs],
            "budget": self.budget,
            "expected_optimal": (
                self.expected_optimal.__dict__ if self.expected_optimal else None
            ),
        }


# ─── Solver protocol ──────────────────────────────────────────────────────────


@dataclass
class SolverResult:
    path: list[str]
    total_cost: int
    jd_unlocked: int
    runtime_s: float


class Solver(Protocol):
    name: str
    def solve(self, tc: TestCase, ontology: SkillOntology) -> SolverResult: ...


# ─── Helpers ──────────────────────────────────────────────────────────────────


def _cost(skill: str, ontology: SkillOntology) -> int:
    cat = ontology.skill_to_category.get(skill.lower())
    return get_skill_cost(skill, cat)


def _prereqs(skill: str, ontology: SkillOntology) -> list[str]:
    """Direct REQUIRES prerequisites (one hop) of `skill`."""
    return list(ontology.graph_out.get(skill.lower(), {}).get(REQUIRES, []))


def expand_with_prereqs(skills: Iterable[str], owned: set[str], ontology: SkillOntology) -> list[str]:
    """Return `skills` augmented with their transitive REQUIRES that aren't in `owned`,
    in topo order (prereqs first). Used by every strategy per §3.3.1.
    """
    seen: set[str] = set()
    out: list[str] = []

    def visit(sk: str):
        if sk in seen or sk in owned:
            return
        seen.add(sk)
        for p in _prereqs(sk, ontology):
            visit(p)
        out.append(sk)

    for s in skills:
        visit(s)
    return out


def jd_unlocked(path_owned: set[str], jds: list[JD]) -> int:
    """A JD is unlocked iff every required skill is in `path_owned`."""
    return sum(1 for j in jds if set(j.required).issubset(path_owned))


def candidates_for(tc: TestCase) -> list[str]:
    """Skills appearing in any JD but not already owned."""
    owned = set(tc.S_user)
    seen: set[str] = set()
    out: list[str] = []
    for jd in tc.JDs:
        for s in jd.required:
            if s not in owned and s not in seen:
                seen.add(s)
                out.append(s)
    return out


# ─── Brute force (oracle for small cases) ─────────────────────────────────────


def solve_brute_force(tc: TestCase, ontology: SkillOntology, max_candidates: int = 14) -> SolverResult:
    """Exhaustively search subsets of `candidates`. O(2^n) — use only for tiny
    cases. Auto-expands each chosen skill with its REQUIRES prereqs.
    Returns the subset maximizing (jd_unlocked desc, total_cost asc).
    """
    start = time.perf_counter()
    owned0 = set(tc.S_user)
    cands = candidates_for(tc)
    if len(cands) > max_candidates:
        raise ValueError(
            f"brute-force refuses {len(cands)} candidates (max={max_candidates}); "
            f"use DP as oracle instead."
        )

    best: tuple[int, int, list[str]] = (0, 0, [])  # (jd_unlocked, -cost, path)
    for size in range(0, len(cands) + 1):
        for combo in itertools.combinations(cands, size):
            expanded = expand_with_prereqs(combo, owned0, ontology)
            cost = sum(_cost(s, ontology) for s in expanded)
            if cost > tc.budget:
                continue
            owned = owned0 | set(expanded)
            unlocked = jd_unlocked(owned, tc.JDs)
            key = (unlocked, -cost)
            best_key = (best[0], -best[1])
            if key > best_key:
                best = (unlocked, cost, expanded)
    return SolverResult(
        path=best[2], total_cost=best[1], jd_unlocked=best[0],
        runtime_s=time.perf_counter() - start,
    )


# ─── Evaluation ───────────────────────────────────────────────────────────────


@dataclass
class EvalReport:
    test_id: str
    solver: str
    jd_unlocked: int
    total_cost: int
    optimality_ratio: float  # vs expected_optimal.jd_unlocked
    runtime_s: float
    prereq_compliant: bool
    within_budget: bool
    path: list[str] = field(default_factory=list)


def evaluate_path(tc: TestCase, sr: SolverResult, ontology: SkillOntology, solver_name: str) -> EvalReport:
    owned = set(tc.S_user) | set(sr.path)
    within_budget = sr.total_cost <= tc.budget

    # Prereq compliance: every skill in path has all its REQUIRES either earlier in path or already in S_user.
    prereq_ok = True
    seen: set[str] = set(tc.S_user)
    for sk in sr.path:
        needed = _prereqs(sk, ontology)
        for p in needed:
            if p not in seen:
                prereq_ok = False
                break
        if not prereq_ok:
            break
        seen.add(sk)

    opt_ratio = 1.0
    if tc.expected_optimal and tc.expected_optimal.jd_unlocked > 0:
        opt_ratio = sr.jd_unlocked / tc.expected_optimal.jd_unlocked

    return EvalReport(
        test_id=tc.test_id, solver=solver_name,
        jd_unlocked=sr.jd_unlocked, total_cost=sr.total_cost,
        optimality_ratio=round(opt_ratio, 3),
        runtime_s=round(sr.runtime_s, 4),
        prereq_compliant=prereq_ok,
        within_budget=within_budget,
        path=list(sr.path),
    )


# ─── IO ───────────────────────────────────────────────────────────────────────


def load_cases(path: Path) -> list[TestCase]:
    data = json.loads(path.read_text())
    return [TestCase.from_dict(d) for d in data]


def dump_cases(cases: list[TestCase], path: Path) -> None:
    path.write_text(json.dumps([c.to_dict() for c in cases], indent=2))


# ─── Oracle-fill helper used by the case-generation script ────────────────────


def fill_expected_optimal(tc: TestCase, ontology: SkillOntology) -> TestCase:
    """Run brute-force and stamp the result into `expected_optimal`.
    Raises ValueError if the case is too big for brute force; callers should
    leave `expected_optimal=None` in that situation (DP from Tuần 13 fills later).
    """
    r = solve_brute_force(tc, ontology)
    tc.expected_optimal = ExpectedOptimal(
        skills=r.path, jd_unlocked=r.jd_unlocked, total_cost=r.total_cost,
    )
    return tc
