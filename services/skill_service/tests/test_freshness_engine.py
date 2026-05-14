"""Smoke tests for CVFreshnessEngine — Tuần 10.

Uses a fake DB session that returns canned skill_trends data. We're checking
formula correctness and the A1–A5 properties from chuong3/3.2.1, not Postgres.

Run from repo root:
    PYTHONPATH=. python -m pytest services/skill_service/tests/test_freshness_engine.py -v
or:
    PYTHONPATH=. python services/skill_service/tests/test_freshness_engine.py
"""
import sys
from datetime import date
from pathlib import Path

# Allow running directly without installing the package.
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from services.skill_service.services.freshness_engine import (
    CVFreshnessEngine,
    CVSkillInput,
)
from services.skill_service.services.ontology import SkillOntology


# ─── Fake DB ───────────────────────────────────────────────────────────────────

class FakeResult:
    def __init__(self, rows):
        self._rows = rows

    def fetchall(self):
        return list(self._rows)

    def scalar(self):
        if not self._rows:
            return None
        first = self._rows[0]
        if isinstance(first, tuple):
            return first[0]
        return first


class FakeDB:
    """Minimal stand-in for a SQLAlchemy Session for the queries the engine runs."""

    def __init__(self, current_demand: dict[str, int], ma_lookup: dict[str, float], n_history: int = 10):
        self.current_demand = current_demand
        self.ma_lookup = ma_lookup
        self.n_history = n_history

    def execute(self, stmt, params=None):
        sql = str(stmt)
        params = params or {}
        if "FROM skill_trends" in sql and "MAX(snapshot_date)" in sql:
            # current snapshot rows
            return FakeResult([(sk, cnt) for sk, cnt in self.current_demand.items()])
        if "COUNT(DISTINCT snapshot_date)" in sql:
            return FakeResult([(self.n_history,)])
        if "AVG(demand_count)" in sql:
            sk = params.get("sk")
            ma = self.ma_lookup.get(sk)
            return FakeResult([(ma,)] if ma is not None else [])
        return FakeResult([])


# ─── Tests ─────────────────────────────────────────────────────────────────────

def _engine() -> CVFreshnessEngine:
    return CVFreshnessEngine(SkillOntology())


def test_score_in_bounds_a1():
    """A1 — Score must be in [0, 100]."""
    eng = _engine()
    db = FakeDB(
        current_demand={"Python": 100, "Django": 80, "PostgreSQL": 70, "Docker": 60, "FastAPI": 50},
        ma_lookup={"Python": 90, "Django": 80, "PostgreSQL": 65, "Docker": 50, "FastAPI": 45},
    )
    cv = [CVSkillInput(name="Python", last_used_year=2026), CVSkillInput(name="Django", last_used_year=2026)]
    res = eng.compute(db, cv, role="backend", snapshot_date=date(2026, 5, 10))
    assert 0.0 <= res.score <= 100.0


def test_monotonic_add_trending_skill_a2():
    """A2 — Adding a trending skill should not decrease the score."""
    eng = _engine()
    db = FakeDB(
        current_demand={"Python": 100, "Django": 80, "Docker": 90, "PostgreSQL": 70, "FastAPI": 60},
        ma_lookup={"Python": 90, "Django": 80, "Docker": 60, "PostgreSQL": 65, "FastAPI": 50},  # Docker trending up
    )
    base_cv = [CVSkillInput(name="Python", last_used_year=2026)]
    plus_cv = base_cv + [CVSkillInput(name="Docker", last_used_year=2026)]
    base = eng.compute(db, base_cv, role="backend", snapshot_date=date(2026, 5, 10))
    plus = eng.compute(db, plus_cv, role="backend", snapshot_date=date(2026, 5, 10))
    assert plus.score >= base.score, f"A2 violated: {plus.score} < {base.score}"


def test_recency_a5():
    """A5 — Same skill, more recent use → higher score."""
    eng = _engine()
    db = FakeDB(
        current_demand={"Python": 100, "Django": 80, "PostgreSQL": 70},
        ma_lookup={"Python": 90, "Django": 80, "PostgreSQL": 65},
    )
    recent = [CVSkillInput(name="Python", last_used_year=2026)]
    old = [CVSkillInput(name="Python", last_used_year=2018)]  # > 5 years
    r_recent = eng.compute(db, recent, role="backend", snapshot_date=date(2026, 5, 10))
    r_old = eng.compute(db, old, role="backend", snapshot_date=date(2026, 5, 10))
    assert r_recent.score > r_old.score


def test_role_sensitivity_a4():
    """A4 — Same CV, different role → different scores."""
    eng = _engine()
    db_backend = FakeDB(
        current_demand={"Python": 100, "Django": 80, "PostgreSQL": 70, "Docker": 60, "FastAPI": 55},
        ma_lookup={},
    )
    db_frontend = FakeDB(
        current_demand={"React": 100, "TypeScript": 90, "Next.js": 80, "Tailwind CSS": 70, "Vue.js": 60},
        ma_lookup={},
    )
    cv = [CVSkillInput(name="Python", last_used_year=2026), CVSkillInput(name="Django", last_used_year=2026)]
    backend = eng.compute(db_backend, cv, role="backend", snapshot_date=date(2026, 5, 10))
    frontend = eng.compute(db_frontend, cv, role="frontend", snapshot_date=date(2026, 5, 10))
    # Backend CV scoring against backend market should beat its frontend score.
    assert backend.score > frontend.score


def test_cold_start_flag():
    """Cold start when < 4 historical snapshots available."""
    eng = _engine()
    db = FakeDB(
        current_demand={"Python": 100},
        ma_lookup={},
        n_history=2,
    )
    res = eng.compute(db, [CVSkillInput(name="Python", last_used_year=2026)], role="backend", snapshot_date=date(2026, 5, 10))
    assert res.cold_start is True


def test_decomposability_a6():
    """A6 — sum of contributions ≈ total score (modulo cap at 100)."""
    eng = _engine()
    db = FakeDB(
        current_demand={"Python": 100, "Django": 80, "PostgreSQL": 70, "Docker": 60, "FastAPI": 50},
        ma_lookup={"Python": 90, "Django": 80, "PostgreSQL": 65, "Docker": 50, "FastAPI": 45},
    )
    cv = [
        CVSkillInput(name="Python", last_used_year=2026),
        CVSkillInput(name="Django", last_used_year=2025),
        CVSkillInput(name="PostgreSQL", last_used_year=2024),
    ]
    res = eng.compute(db, cv, role="backend", snapshot_date=date(2026, 5, 10))
    total = sum(c.contribution for c in res.contributions)
    # Score is min(total, 100). Allow small float drift.
    assert abs(min(total, 100.0) - res.score) < 0.05


def test_empty_trends_returns_zero_cold_start():
    eng = _engine()
    db = FakeDB(current_demand={}, ma_lookup={}, n_history=0)
    res = eng.compute(db, [CVSkillInput(name="Python")], role="backend", snapshot_date=date(2026, 5, 10))
    assert res.score == 0.0 and res.cold_start is True


if __name__ == "__main__":
    tests = [
        test_score_in_bounds_a1,
        test_monotonic_add_trending_skill_a2,
        test_recency_a5,
        test_role_sensitivity_a4,
        test_cold_start_flag,
        test_decomposability_a6,
        test_empty_trends_returns_zero_cold_start,
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
