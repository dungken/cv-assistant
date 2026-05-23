"""Dump key numbers from Market Intelligence dashboard insights để dùng
trong Chương 4.5 báo cáo. Chạy `get_dashboard()` thật trên snapshot DB
hiện tại, in summary của 33 insight (top-N items, counts, ratios).

Run từ repo root:
    PYTHONPATH=. python3 services/skill_service/scripts/dump_market_intel_stats.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from services.skill_service.services.db_session import SessionLocal  # noqa
from services.skill_service.services.market_intel import get_dashboard  # noqa

OUT = ROOT / "services/skill_service/data/market_intel_dump.json"


def main() -> int:
    db = SessionLocal()
    try:
        # Default view (all sources, no filter)
        d_all = get_dashboard(db, source="all")
        d_itviec = get_dashboard(db, source="itviec")
        d_topcv = get_dashboard(db, source="topcv")

        summary = {
            "kpis_all": d_all["kpis"],
            "kpis_itviec": d_itviec["kpis"],
            "kpis_topcv": d_topcv["kpis"],
            "source_breakdown": d_all["source_breakdown"],
            "top_5_skills": d_all["top_skills"][:5],
            "top_5_skills_count": len(d_all["top_skills"]),
            "role_distribution": d_all["role_distribution"],
            "seniority_distribution": d_all["seniority_distribution"],
            "work_mode_distribution": d_all["work_mode_distribution"],
            "salary_by_seniority_count": len(d_all["salary_by_seniority"]),
            "top_5_locations": d_all["top_locations"][:5],
            "top_5_companies": d_all["top_companies"][:5],
            "exp_buckets_count": len(d_all["exp_histogram"]),
            "degree_distribution": d_all["degree_distribution"],
            "skill_pairs_top_5": d_all["skill_pairs"][:5],
            "skill_premium_keys": list(d_all["skill_premium"].keys()) if isinstance(d_all.get("skill_premium"), dict) else None,
            "skill_premium_summary": {k: (v[:5] if isinstance(v, list) else v) for k, v in (d_all.get("skill_premium") or {}).items()},
            "skill_velocity_summary": {k: (v[:5] if isinstance(v, list) else v) for k, v in (d_all.get("skill_velocity") or {}).items()},
            "hidden_gems_count": len(d_all.get("hidden_gems", [])),
            "skill_clusters_count": len(d_all.get("skill_clusters", [])),
            "english_premium": d_all.get("english_premium"),
            "skill_network_nodes": len(d_all.get("skill_network", {}).get("nodes", [])),
            "skill_network_edges": len(d_all.get("skill_network", {}).get("edges", [])),
            "outdated_skills_count": len(d_all.get("outdated_skills", [])),
            "hot_companies_count": len(d_all.get("hot_companies", [])),
            "niche_champions_count": len(d_all.get("niche_champions", [])),
            "skill_specificity_top_5": d_all.get("skill_specificity", [])[:5],
            "all_keys": sorted(d_all.keys()),
            "insight_count": len([k for k in d_all.keys() if k not in {"filters_applied", "options"}]),
        }

        # Pretty print
        print(f"Total JDs:          {summary['kpis_all']['total_jds']}")
        print(f"  ITviec:           {summary['kpis_itviec']['total_jds']}")
        print(f"  TopCV:            {summary['kpis_topcv']['total_jds']}")
        print(f"Total companies:    {summary['kpis_all']['total_companies']}")
        print(f"Unique skills:      {summary['kpis_all']['unique_skills']}")
        print(f"Date range:         {summary['kpis_all']['earliest_post']} → {summary['kpis_all']['latest_post']}")
        print(f"Insight count:      {summary['insight_count']}")
        print(f"Skill network:      {summary['skill_network_nodes']} nodes / {summary['skill_network_edges']} edges")
        print(f"Skill clusters:     {summary['skill_clusters_count']}")
        print(f"Hidden gems:        {summary['hidden_gems_count']}")
        print()
        print("=== Top 5 skills (all sources) ===")
        for s in summary["top_5_skills"]:
            print(f"  {s['skill']:20s} {s['cnt']}")
        print()
        print("=== Role distribution ===")
        for r in summary["role_distribution"]:
            print(f"  {str(r.get('role_group') or 'unknown'):40s} {r['cnt']}")
        print()
        print("=== Seniority distribution ===")
        for r in summary["seniority_distribution"]:
            print(f"  {str(r.get('seniority') or 'unknown'):20s} {r['cnt']}")
        print()
        print("=== Top 5 locations ===")
        for r in summary["top_5_locations"]:
            print(f"  {r['location']:30s} {r['cnt']}")
        print()
        print("=== Top 5 companies ===")
        for r in summary["top_5_companies"]:
            print(f"  {r['company']:50s} {r['cnt']}")
        print()
        print("=== Source breakdown ===")
        for s in summary["source_breakdown"]:
            print(f"  {s['source']:20s} {s['cnt']}")
        print()
        print("=== English Premium ===")
        ep = summary["english_premium"]
        if ep:
            print(json.dumps(ep, indent=2, default=str))

        OUT.write_text(json.dumps(summary, indent=2, default=str, ensure_ascii=False))
        print(f"\nFull dump → {OUT}")
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    sys.exit(main())
