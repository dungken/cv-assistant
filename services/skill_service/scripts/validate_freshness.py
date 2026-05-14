"""Tuần 11 — Freshness Score validation.

Runs CVFreshnessEngine on 10 hand-crafted "fresh" CVs and 10 "stale" CVs against
a synthetic market snapshot (since real crawler history is still accumulating).

Reports:
- Per-CV score
- Group means (fresh vs stale) and the gap
- Sanity check: every fresh CV > every stale CV of the same role
- Spearman rank correlation between expected ordering (label) and score

Run from repo root:
    PYTHONPATH=. python3 services/skill_service/scripts/validate_freshness.py
"""
from __future__ import annotations

import json
import sys
import statistics
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from services.skill_service.services.freshness_engine import (
    CVFreshnessEngine, CVSkillInput, FreshnessResult,
)
from services.skill_service.services.ontology import SkillOntology

DATA = ROOT / "services" / "skill_service" / "data" / "freshness_validation"


# ─── Fake DB that serves the synthetic market snapshot ────────────────────────


class FakeResult:
    def __init__(self, rows):
        self._rows = rows

    def fetchall(self):
        return list(self._rows)

    def scalar(self):
        if not self._rows:
            return None
        first = self._rows[0]
        return first[0] if isinstance(first, tuple) else first


class SyntheticMarketDB:
    """Routes the engine's SQL probes against an in-memory snapshot."""

    def __init__(self, market: dict):
        self.market = market
        self.history_weeks = market.get("history_weeks", 8)
        self._current_role: str | None = None

    def for_role(self, role: str) -> "SyntheticMarketDB":
        self._current_role = role
        return self

    def execute(self, stmt, params=None):
        sql = str(stmt)
        params = params or {}
        role = params.get("role") or self._current_role
        bucket = self.market["roles"].get(role, {})
        current = bucket.get("current", {})
        ma = bucket.get("ma", {})

        if "FROM skill_trends" in sql and "MAX(snapshot_date)" in sql:
            return FakeResult([(sk, cnt) for sk, cnt in current.items()])
        if "COUNT(DISTINCT snapshot_date)" in sql:
            return FakeResult([(self.history_weeks,)])
        if "AVG(demand_count)" in sql:
            sk = params.get("sk")
            return FakeResult([(ma.get(sk),)] if sk in ma else [])
        return FakeResult([])


# ─── Helpers ──────────────────────────────────────────────────────────────────


def load_cvs(path: Path) -> list[dict]:
    return json.loads(path.read_text())


def to_inputs(cv: dict) -> list[CVSkillInput]:
    return [CVSkillInput(name=s["name"], last_used_year=s.get("last_used_year")) for s in cv["skills"]]


def spearman(scores: list[tuple[int, float]]) -> float:
    """Spearman ρ between a list of (rank_expected, score) tuples."""
    n = len(scores)
    if n < 2:
        return 1.0
    by_score = sorted(scores, key=lambda x: -x[1])
    rank_observed = {id(p): r + 1 for r, p in enumerate(by_score)}
    d2 = 0.0
    for p in scores:
        d2 += (p[0] - rank_observed[id(p)]) ** 2
    return 1 - (6 * d2) / (n * (n * n - 1))


# ─── Main ─────────────────────────────────────────────────────────────────────


def main() -> int:
    market = json.loads((DATA / "market_snapshot.json").read_text())
    snapshot_date = date.fromisoformat(market["snapshot_date"])
    fresh_cvs = load_cvs(DATA / "cvs_fresh.json")
    stale_cvs = load_cvs(DATA / "cvs_stale.json")

    engine = CVFreshnessEngine(SkillOntology())
    db = SyntheticMarketDB(market)

    print(f"Snapshot: {snapshot_date}  |  history weeks: {market.get('history_weeks')}\n")

    rows: list[dict] = []
    for cv in fresh_cvs + stale_cvs:
        role = cv["role"]
        db.for_role(role)
        res: FreshnessResult = engine.compute(
            db=db,
            cv_skills=to_inputs(cv),
            role=role,
            snapshot_date=snapshot_date,
        )
        rows.append({"cv": cv, "score": res.score, "missing": res.missing_ideal, "ideal": res.ideal_skills})

    # ── per-CV report
    print(f"{'CV ID':<18}{'Role':<14}{'Label':<8}{'Score':>8}    Missing-ideal (top)")
    print("-" * 100)
    for r in rows:
        cv = r["cv"]
        missing = ", ".join(r["missing"][:5])
        print(f"{cv['cv_id']:<18}{cv['role']:<14}{cv['label']:<8}{r['score']:>7.2f}    {missing}")

    fresh_scores = [r["score"] for r in rows if r["cv"]["label"] == "fresh"]
    stale_scores = [r["score"] for r in rows if r["cv"]["label"] == "stale"]

    print("\n── Group statistics ────────────────────────────")
    print(f"  fresh  n={len(fresh_scores):2d}  mean={statistics.mean(fresh_scores):6.2f}  "
          f"stdev={statistics.pstdev(fresh_scores):5.2f}  min={min(fresh_scores):.2f}  max={max(fresh_scores):.2f}")
    print(f"  stale  n={len(stale_scores):2d}  mean={statistics.mean(stale_scores):6.2f}  "
          f"stdev={statistics.pstdev(stale_scores):5.2f}  min={min(stale_scores):.2f}  max={max(stale_scores):.2f}")
    gap = statistics.mean(fresh_scores) - statistics.mean(stale_scores)
    print(f"  Δ(fresh − stale) = {gap:+.2f}")

    # ── sanity check per role
    print("\n── Per-role sanity (all fresh > all stale of the same role?) ──")
    by_role: dict[str, dict[str, list[float]]] = {}
    for r in rows:
        by_role.setdefault(r["cv"]["role"], {}).setdefault(r["cv"]["label"], []).append(r["score"])
    ok = True
    for role, groups in sorted(by_role.items()):
        fresh = groups.get("fresh", [])
        stale = groups.get("stale", [])
        if not fresh or not stale:
            continue
        passes = min(fresh) > max(stale)
        ok = ok and passes
        print(f"  {role:<14} min(fresh)={min(fresh):5.2f}  max(stale)={max(stale):5.2f}  {'PASS' if passes else 'FAIL'}")

    # ── Spearman ρ between expected label-rank and score
    labelled = [(0 if r["cv"]["label"] == "fresh" else 1, r["score"]) for r in rows]
    # Expected: fresh (rank 0) should have higher score than stale (rank 1) → negative ρ desired
    rho = spearman(labelled)
    print(f"\nSpearman ρ(rank_expected, score) = {rho:+.3f}  "
          f"(negative is good: 'fresh' label sorts above 'stale' by score)")

    if ok and statistics.mean(fresh_scores) > statistics.mean(stale_scores):
        print("\nResult: VALIDATION PASSED")
        return 0
    print("\nResult: VALIDATION FAILED")
    return 1


if __name__ == "__main__":
    sys.exit(main())
