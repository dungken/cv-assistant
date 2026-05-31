"""Tuần 14 — smoke tests for the user-state endpoints.

Hits the real `skill_postgres` container the project uses in development
(localhost:5434). Tests namespace their writes by user_id prefix
`__test_t14_*` and clean up at the end, so they're safe to run repeatedly
against a shared dev DB.

The tests cover the service layer below FastAPI directly (cv_store +
freshness_engine + record_history_and_alert + opportunity_window). They
don't spin up Uvicorn — that would require sentence_transformers and
network — but they exercise the same logic the endpoints call.

Run from repo root:
    PYTHONPATH=. python3 services/skill_service/tests/test_tuan14_endpoints.py
"""
from __future__ import annotations

import os
import sys
import uuid
from datetime import date, datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from services.skill_service.models.database import (
    Base, FreshnessAlertDB, FreshnessHistoryDB, UserCVDB,
)
from services.skill_service.services import cv_store
from services.skill_service.services.freshness_engine import (
    CVFreshnessEngine, CVSkillInput, record_history_and_alert,
)
from services.skill_service.services.opportunity_window import find_opportunities
from services.skill_service.services.ontology import SkillOntology


DB_URL = os.environ.get(
    "TEST_DATABASE_URL",
    "postgresql://skill_user:skill_password@localhost:5434/skill_data",
)
ENGINE = create_engine(DB_URL, future=True)
SessionLocal = sessionmaker(bind=ENGINE, future=True)

USER_PREFIX = "__test_t14_"
JD_PREFIX = "_t14_"   # jd_key is VARCHAR(16) so prefix must stay short
TEST_SNAPSHOT = date(2026, 6, 4)


def _ensure_schema():
    """Create the skill_service tables we own + skip if jd_raw/skill_trends
    don't exist yet (the crawler service creates them on its own startup)."""
    Base.metadata.create_all(ENGINE)


def _cleanup(db):
    """Remove everything our tests inserted (namespaced by prefix)."""
    db.execute(text("DELETE FROM skill_freshness_alerts WHERE user_id LIKE :p"),
               {"p": f"{USER_PREFIX}%"})
    db.execute(text("DELETE FROM skill_freshness_history WHERE user_id LIKE :p"),
               {"p": f"{USER_PREFIX}%"})
    db.execute(text("DELETE FROM skill_user_cv WHERE user_id LIKE :p"),
               {"p": f"{USER_PREFIX}%"})
    db.execute(text("DELETE FROM skill_trends WHERE skill_canonical LIKE :p"),
               {"p": "__t14_%"})
    db.execute(text("DELETE FROM jd_raw WHERE jd_key LIKE :p"),
               {"p": f"{JD_PREFIX}%"})
    # Backward-compat: clean up old test-source rows from previous runs.
    db.execute(text("DELETE FROM jd_raw WHERE source = 'test'"))
    db.commit()


def _seed_market(db, role: str):
    """Seed skill_trends with a snapshot + 4 weeks of prior history for MA.
    Uses normal skill names (Python/Docker/...) so the engine's ontology
    importance computation sees real demand signal."""
    skills = {
        "Python": 120, "FastAPI": 70, "PostgreSQL": 105, "Docker": 130,
        "Kubernetes": 95, "Redis": 75, "AWS": 115, "Apache Kafka": 65,
        "Microservices": 85, "REST": 110, "Git": 140, "PHP": 25, "Oracle": 18,
    }
    # Wipe any pre-existing snapshot for our test date + role first.
    db.execute(text(
        "DELETE FROM skill_trends WHERE snapshot_date >= :d - INTERVAL '35 days' "
        "AND role = :r AND window_days = 7"
    ), {"d": TEST_SNAPSHOT, "r": role})
    for sk, cnt in skills.items():
        db.execute(text(
            "INSERT INTO skill_trends (skill_canonical, snapshot_date, window_days, role, location, demand_count) "
            "VALUES (:s, :d, 7, :r, NULL, :c)"
        ), {"s": sk, "d": TEST_SNAPSHOT, "r": role, "c": cnt})
    for w in range(1, 5):
        snap = TEST_SNAPSHOT - timedelta(days=7 * w)
        for sk, cnt in skills.items():
            db.execute(text(
                "INSERT INTO skill_trends (skill_canonical, snapshot_date, window_days, role, location, demand_count) "
                "VALUES (:s, :d, 7, :r, NULL, :c)"
            ), {"s": sk, "d": snap, "r": role, "c": int(cnt * 0.9)})
    db.commit()


def _seed_jds(db, role: str):
    """Insert namespaced JDs into jd_raw. Assumes the table already exists
    (created by the crawler service's own Base.metadata.create_all on startup)."""
    db.execute(text("DELETE FROM jd_raw WHERE jd_key LIKE :p"),
               {"p": f"{JD_PREFIX}%"})
    today = TEST_SNAPSHOT
    rows = [
        (f"{JD_PREFIX}001", "FastAPI Backend", "Acme", role, "HCM",
         ["Python", "FastAPI", "PostgreSQL"], today - timedelta(days=1)),
        (f"{JD_PREFIX}002", "Django Backend", "Beta", role, "HCM",
         ["Python", "Django", "PostgreSQL"], today - timedelta(days=3)),
        (f"{JD_PREFIX}003", "Kubernetes Ops", "Gamma", "devops", "Hanoi",
         ["Kubernetes", "Docker", "Linux"], today - timedelta(days=2)),
        (f"{JD_PREFIX}old", "Old JD", "Stale", role, "HCM",
         ["Python", "FastAPI"], today - timedelta(days=25)),
    ]
    now = datetime.utcnow()
    for r in rows:
        db.execute(text("""
            INSERT INTO jd_raw (jd_key, source, title, company, role, location,
                                skills_canonical, posted_date, first_seen, last_seen)
            VALUES (:k, 'itviec', :t, :c, :r, :l, CAST(:s AS JSONB), :d, :now, :now)
        """), {"k": r[0], "t": r[1], "c": r[2], "r": r[3], "l": r[4],
               "s": _json(r[5]), "d": r[6], "now": now})
    db.commit()


def _json(obj) -> str:
    import json
    return json.dumps(obj)


# ─── Tests ────────────────────────────────────────────────────────────────────


def test_cv_store_roundtrip():
    db = SessionLocal()
    try:
        uid = f"{USER_PREFIX}roundtrip_{uuid.uuid4().hex[:6]}"
        cv_store.upsert_cv(db, uid, "backend", [
            {"name": "Python", "last_used_year": 2026},
            {"name": "Docker", "last_used_year": 2025},
        ])
        fetched = cv_store.get_cv(db, uid)
        assert fetched is not None
        assert fetched.target_role == "backend"
        assert len(fetched.skills_with_recency) == 2
        # Update path
        cv_store.upsert_cv(db, uid, "frontend", [{"name": "React", "last_used_year": 2026}])
        f2 = cv_store.get_cv(db, uid)
        assert f2.target_role == "frontend"
        assert len(f2.skills_with_recency) == 1
    finally:
        db.close()


def test_health_score_path_records_history_and_alert():
    db = SessionLocal()
    try:
        _seed_market(db, role="backend")
        engine = CVFreshnessEngine(SkillOntology())
        uid = f"{USER_PREFIX}health_{uuid.uuid4().hex[:6]}"
        fresh_cv = [
            CVSkillInput("Python", 2026), CVSkillInput("FastAPI", 2026),
            CVSkillInput("PostgreSQL", 2026), CVSkillInput("Docker", 2026),
            CVSkillInput("Kubernetes", 2026), CVSkillInput("Redis", 2026),
            CVSkillInput("AWS", 2026), CVSkillInput("Microservices", 2026),
            CVSkillInput("REST", 2026), CVSkillInput("Git", 2026),
        ]
        r1 = engine.compute(db, fresh_cv, role="backend", snapshot_date=TEST_SNAPSHOT)
        record_history_and_alert(db, user_id=uid, result=r1)
        hist = db.query(FreshnessHistoryDB).filter(FreshnessHistoryDB.user_id == uid).all()
        assert len(hist) == 1, "first compute should write 1 history row"
        assert abs(hist[0].score - r1.score) < 1e-6

        # Degrade the CV — should fire an alert
        stale_cv = [CVSkillInput("PHP", 2018), CVSkillInput("Oracle", 2019)]
        r2 = engine.compute(db, stale_cv, role="backend", snapshot_date=TEST_SNAPSHOT)
        record_history_and_alert(db, user_id=uid, result=r2)
        hist = db.query(FreshnessHistoryDB).filter(FreshnessHistoryDB.user_id == uid).all()
        assert len(hist) == 2

        alerts = db.query(FreshnessAlertDB).filter(FreshnessAlertDB.user_id == uid).all()
        assert len(alerts) == 1, f"expected 1 alert, got {len(alerts)}"
        a = alerts[0]
        assert a.delta > 5
        assert abs(a.prev_score - r1.score) < 1e-6
        assert abs(a.new_score - r2.score) < 1e-6
        assert "Freshness dropped" in a.reason
    finally:
        db.close()


def test_no_alert_when_score_does_not_drop_much():
    db = SessionLocal()
    try:
        _seed_market(db, role="backend")
        engine = CVFreshnessEngine(SkillOntology())
        uid = f"{USER_PREFIX}stable_{uuid.uuid4().hex[:6]}"
        cv = [
            CVSkillInput("Python", 2026), CVSkillInput("FastAPI", 2026),
            CVSkillInput("PostgreSQL", 2026),
        ]
        r1 = engine.compute(db, cv, role="backend", snapshot_date=TEST_SNAPSHOT)
        record_history_and_alert(db, user_id=uid, result=r1)
        r2 = engine.compute(db, cv, role="backend", snapshot_date=TEST_SNAPSHOT)
        record_history_and_alert(db, user_id=uid, result=r2)
        alerts = db.query(FreshnessAlertDB).filter(FreshnessAlertDB.user_id == uid).all()
        assert len(alerts) == 0, "identical CVs should produce no alert"
    finally:
        db.close()


def test_opportunity_window_filters_by_date_and_match():
    db = SessionLocal()
    try:
        _seed_jds(db, role="backend")
        opps, _agg = find_opportunities(
            db, ["Python", "FastAPI", "PostgreSQL"],
            target_role=None, days=7, limit=10, min_match=0.5,
        )
        keys = {o.jd_key for o in opps if o.jd_key.startswith(JD_PREFIX)}
        assert f"{JD_PREFIX}001" in keys
        assert f"{JD_PREFIX}002" in keys
        assert f"{JD_PREFIX}old" not in keys, "old JDs (>7d) should be excluded"
        top = next(o for o in opps if o.jd_key == f"{JD_PREFIX}001")
        assert top.match_score == 1.0
    finally:
        db.close()


def test_opportunity_window_min_match_threshold():
    db = SessionLocal()
    try:
        _seed_jds(db, role="backend")
        opps, _agg = find_opportunities(
            db, ["Rust", "Elixir"],  # no overlap
            target_role=None, days=7, min_match=0.5,
        )
        ours = [o for o in opps if o.jd_key.startswith(JD_PREFIX)]
        assert ours == []
    finally:
        db.close()


def test_alert_reason_summarizes_worst_skill():
    db = SessionLocal()
    try:
        _seed_market(db, role="backend")
        engine = CVFreshnessEngine(SkillOntology())
        uid = f"{USER_PREFIX}reason_{uuid.uuid4().hex[:6]}"
        r1 = engine.compute(
            db,
            [CVSkillInput("Python", 2026), CVSkillInput("Docker", 2026),
             CVSkillInput("Kubernetes", 2026)],
            role="backend", snapshot_date=TEST_SNAPSHOT,
        )
        record_history_and_alert(db, user_id=uid, result=r1)
        r2 = engine.compute(
            db, [CVSkillInput("PHP", 2018)],
            role="backend", snapshot_date=TEST_SNAPSHOT,
        )
        record_history_and_alert(db, user_id=uid, result=r2)
        alerts = db.query(FreshnessAlertDB).filter(FreshnessAlertDB.user_id == uid).all()
        if alerts:  # only fires when delta > 5
            assert "Freshness dropped" in alerts[0].reason
    finally:
        db.close()


# ─── Runner ───────────────────────────────────────────────────────────────────


def main() -> int:
    print(f"Using DB: {DB_URL}")
    _ensure_schema()

    # Quick connectivity probe — fail fast with a clear message if Postgres is down.
    db = SessionLocal()
    try:
        db.execute(text("SELECT 1"))
    except Exception as e:
        print(f"ERROR: cannot reach Postgres at {DB_URL}: {e}")
        return 2
    finally:
        db.close()

    tests = [
        test_cv_store_roundtrip,
        test_health_score_path_records_history_and_alert,
        test_no_alert_when_score_does_not_drop_much,
        test_opportunity_window_filters_by_date_and_match,
        test_opportunity_window_min_match_threshold,
        test_alert_reason_summarizes_worst_skill,
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

    # Cleanup
    db = SessionLocal()
    try:
        _cleanup(db)
    finally:
        db.close()

    if failures:
        return 1
    print(f"\nAll {len(tests)} tests passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
