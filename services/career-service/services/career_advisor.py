import logging
import pandas as pd
from pathlib import Path
from typing import List, Dict, Optional
import chromadb
from services.career_service.models.schemas import CareerStep, CareerPath, SkillGap

logger = logging.getLogger(__name__)

class CareerAdvisor:
    """Core logic for career paths and O*NET data analysis."""
    
    def __init__(self, onet_path: str, collection: chromadb.Collection):
        self.onet_path = Path(onet_path)
        self.collection = collection
        self.occupations: Dict[str, dict] = {}
        self.skills_map: Dict[str, List[str]] = {}
        self.load_data()

    def load_data(self):
        """Load O*NET flat files."""
        occ_file = self.onet_path / "Occupation Data.txt"
        if occ_file.exists():
            df = pd.read_csv(occ_file, sep="\t")
            for _, row in df.iterrows():
                code = row["O*NET-SOC Code"]
                self.occupations[code] = {
                    "code": code,
                    "title": row["Title"],
                    "description": row.get("Description", "")
                }
        
        skills_file = self.onet_path / "Skills.txt"
        if skills_file.exists():
            df = pd.read_csv(skills_file, sep="\t")
            # Group by code and get top skills
            for code in self.occupations.keys():
                occ_skills = df[df["O*NET-SOC Code"] == code]
                if not occ_skills.empty:
                    self.skills_map[code] = occ_skills["Element Name"].tolist()[:8]

    def find_role(self, query: str) -> Optional[dict]:
        """Find role by title or semantic search."""
        query_lower = query.lower()
        for code, occ in self.occupations.items():
            if query_lower in occ["title"].lower():
                return occ
        
        if self.collection:
            res = self.collection.query(query_texts=[query], n_results=1)
            if res["metadatas"] and res["metadatas"][0]:
                code = res["metadatas"][0][0].get("code")
                return self.occupations.get(code)
        return None

    def calculate_gap(self, current_skills: List[str], target_code: str) -> SkillGap:
        """Analyze difference between current skills and target role requirements."""
        req = self.skills_map.get(target_code, [])
        curr_lower = [s.lower() for s in current_skills]
        missing = [s for s in req if s.lower() not in curr_lower]
        return SkillGap(current=current_skills, required=req, missing=missing)

    def generate_paths(self, current: dict, target: dict, gap: SkillGap) -> List[CareerPath]:
        """Simple path generation logic."""
        # Ambitious (Fast)
        ambitious = CareerPath(
            path_type="ambitious",
            total_time="6-12 months",
            steps=[CareerStep(
                step=1, role=target["title"], role_code=target["code"],
                timeframe="6-12 months", skills_to_learn=gap.missing[:3],
                description="Fast-track transition."
            )]
        )
        
        # Moderate
        moderate = CareerPath(
            path_type="moderate",
            total_time="1-2 years",
            steps=[CareerStep(
                step=1, role=target["title"], role_code=target["code"],
                timeframe="1-2 years", skills_to_learn=gap.missing,
                description="Balanced transition."
            )]
        )
        
        return [moderate, ambitious]
