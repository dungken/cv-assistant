import sys
from pathlib import Path

# Add core to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from services.career_service.config import settings
from services.career_service.models.schemas import CareerRequest, CareerRecommendation, RelatedRole
from services.career_service.services.career_advisor import CareerAdvisor
from shared.db.chroma_client import get_collection
from shared.utils.logging_config import setup_logging
from shared.constants import COLLECTION_JOBS

# Logger
logger = setup_logging(settings.service_name)

app = FastAPI(title="Career Service", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Cache advisor
_advisor = None

def get_advisor() -> CareerAdvisor:
    global _advisor
    if _advisor is None:
        try:
            coll = get_collection(COLLECTION_JOBS)
            _advisor = CareerAdvisor(settings.onet_path, coll)
        except Exception as e:
            logger.error(f"Failed to init advisor: {e}")
            raise HTTPException(status_code=503, detail="O*NET Service Error")
    return _advisor

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/recommend", response_model=CareerRecommendation)
def recommend(request: CareerRequest, advisor: CareerAdvisor = Depends(get_advisor)):
    logger.info(f"Career req: {request.current_role} -> {request.target_role}")

    current_occ = advisor.find_role(request.current_role)
    if not current_occ:
        raise HTTPException(status_code=404, detail="Current role not found in O*NET database")

    target_occ = advisor.find_role(request.target_role or "Senior " + request.current_role)
    if not target_occ:
        target_occ = current_occ

    gap = advisor.calculate_gap(request.current_skills, target_occ["code"])
    level = advisor.estimate_experience_level(request.current_skills)
    paths = advisor.generate_paths(current_occ, target_occ, gap, request.current_skills)

    # Find related roles for exploration
    related = advisor.find_related_it_roles(current_occ["code"])
    related_roles = [
        RelatedRole(
            title=r["title"],
            code=r["code"],
            description=r.get("description", ""),
            timeframe=r.get("timeframe", ""),
        )
        for r in related
    ]

    return CareerRecommendation(
        current_role=current_occ["title"],
        target_role=target_occ["title"],
        experience_level=level,
        skill_gap=gap,
        paths=paths,
        related_roles=related_roles,
    )

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=settings.service_port)
