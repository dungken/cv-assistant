import logging
import json
from typing import List, Dict, Any, Optional
from collections import Counter, defaultdict
import numpy as np
from chromadb import Collection
from services.skill_service.models.schemas import (
    MarketOverviewResponse, SkillTrend, SkillCorrelation, SalaryStats
)

logger = logging.getLogger(__name__)

class MarketAnalyzer:
    """Service for cross-JD market data aggregation and analysis."""

    def __init__(self, collection: Collection):
        self.collection = collection

    def get_overview(self, industry: Optional[str] = None) -> MarketOverviewResponse:
        """Aggregate market data from all JDs or filtered by industry."""
        
        # 1. Fetch data from ChromaDB
        # We fetch all because 600-1000 records is light
        query_params = {}
        if industry:
            query_params["where"] = {"industry": industry}
            
        results = self.collection.get(**query_params)
        metadatas = results.get("metadatas", [])
        total_jds = len(metadatas)

        if total_jds == 0:
            return MarketOverviewResponse(
                top_skills=[], industry_distribution={}, 
                location_distribution={}, salary_overview=[], correlations=[]
            )

        # 2. Aggregations
        skill_counts = Counter()
        ind_dist = Counter()
        loc_dist = Counter()
        salary_by_cat = defaultdict(list)
        
        # Skill co-occurrence for correlations
        co_occurrence = defaultdict(Counter)

        for meta in metadatas:
            # Stats
            ind_dist[meta["industry"]] += 1
            loc_dist[meta["location"]] += 1
            
            # Skills
            skills = json.loads(meta["skills"])
            for s in skills:
                skill_counts[s] += 1
                # Correlations
                for other_s in skills:
                    if s != other_s:
                        co_occurrence[s][other_s] += 1
            
            # Salary
            salary_by_cat[meta["industry"]].append({
                "min": meta["min_salary"],
                "max": meta["max_salary"]
            })

        # 3. Format Top Skills
        top_skills = []
        for name, count in skill_counts.most_common(15):
            top_skills.append(SkillTrend(
                name=name,
                count=count,
                percentage=round((count / total_jds) * 100, 1),
                growth=round(np.random.uniform(-5, 15), 1) # Mock growth for UI
            ))

        # 4. Format Salary Stats
        salary_overview = []
        for cat, values in salary_by_cat.items():
            mins = [v["min"] for v in values]
            maxs = [v["max"] for v in values]
            salary_overview.append(SalaryStats(
                category=cat,
                min_salary=float(np.min(mins)),
                max_salary=float(np.max(maxs)),
                median_salary=float(np.median([(v["min"] + v["max"]) / 2 for v in values]))
            ))

        # 5. Format Correlations (Heatmap)
        correlations = []
        # Get top 10 skills to limit heatmap size
        top_10 = [s.name for s in top_skills[:10]]
        for i, s_a in enumerate(top_10):
            for s_b in top_10[i+1:]:
                weight = co_occurrence[s_a][s_b] / total_jds
                if weight > 0:
                    correlations.append(SkillCorrelation(
                        skill_a=s_a,
                        skill_b=s_b,
                        weight=round(weight * 10, 2) # Scale for UI
                    ))

        return MarketOverviewResponse(
            top_skills=top_skills,
            industry_distribution=dict(ind_dist),
            location_distribution=dict(loc_dist),
            salary_overview=salary_overview,
            correlations=correlations
        )
