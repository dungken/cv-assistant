"""Seed a demo CV for the dashboard demo.

Usage:
    PYTHONPATH=. python3 services/skill_service/scripts/seed_demo_cv.py [user_id] [role]

Defaults: user_id = "dungdemo22@gmail.com", role = "backend".

After running:
    - skill_user_cv has a row → /health-score, /opportunity-window stop returning 404
    - skill_freshness_history gets the first snapshot → time-series chart has points
    - skill_freshness_alerts stays empty (no prior snapshot to diff against)
"""
from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from services.skill_service.services import cv_store
from services.skill_service.services.freshness_engine import (
    CVFreshnessEngine, CVSkillInput, record_history_and_alert,
)
from services.skill_service.services.ontology import SkillOntology
from services.skill_service.services.db_session import SessionLocal


DEMO_SKILLS = [
    {"name": "Python", "last_used_year": 2026},
    {"name": "FastAPI", "last_used_year": 2026},
    {"name": "PostgreSQL", "last_used_year": 2026},
    {"name": "Docker", "last_used_year": 2026},
    {"name": "Kubernetes", "last_used_year": 2025},
    {"name": "Redis", "last_used_year": 2025},
    {"name": "AWS", "last_used_year": 2026},
    {"name": "REST", "last_used_year": 2026},
    {"name": "Microservices", "last_used_year": 2025},
    {"name": "Git", "last_used_year": 2026},
    {"name": "PHP", "last_used_year": 2020},  # one legacy skill to demo trend impact
]


def main() -> int:
    user_id = sys.argv[1] if len(sys.argv) > 1 else "dungdemo22@gmail.com"
    role = sys.argv[2] if len(sys.argv) > 2 else "backend"

    db = SessionLocal()
    try:
        rec = cv_store.upsert_cv(db, user_id, role, DEMO_SKILLS)
        print(f"✓ Upserted CV for user_id={user_id} role={role} ({len(rec.skills_with_recency)} skills)")

        engine = CVFreshnessEngine(SkillOntology())
        cv_inputs = [CVSkillInput(name=s["name"], last_used_year=s["last_used_year"]) for s in DEMO_SKILLS]
        result = engine.compute(db, cv_inputs, role=role, snapshot_date=date.today())
        record_history_and_alert(db, user_id=user_id, result=result)
        print(f"✓ Initial Freshness Score = {result.score:.2f}  (cold_start={result.cold_start})")
        print(f"  Top contributions:")
        for c in result.contributions[:5]:
            print(f"    {c.skill:<20s}  contrib={c.contribution:6.2f}  trend={c.trend:.2f}  recency={c.recency:.1f}")
        if result.missing_ideal:
            print(f"  Missing-ideal (top 5): {', '.join(result.missing_ideal[:5])}")
    finally:
        db.close()

    print()
    print("Next: reload /cv-health in the browser — gauge + history chart should render.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
