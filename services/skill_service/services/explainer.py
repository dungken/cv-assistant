"""
Task 2.3: Explainable Skill Gap Analysis.
Provides human-readable explanations for why skills are missing,
how to bridge gaps, and learning priority recommendations.
"""

import logging
from typing import Optional
from services.skill_service.services.ontology import SkillOntology

logger = logging.getLogger(__name__)


# Priority weight for different skill categories
CATEGORY_PRIORITY = {
    "Programming Languages": 0.9,
    "Backend Development": 0.85,
    "Frontend Development": 0.85,
    "Database": 0.8,
    "DevOps & Infrastructure": 0.75,
    "Machine Learning & AI": 0.8,
    "Data Engineering": 0.75,
    "Security": 0.7,
    "Testing & QA": 0.65,
    "Architecture & Methodologies": 0.6,
    "Mobile Development": 0.8,
    "Version Control & Collaboration": 0.5,
    "Game Development": 0.7,
    "Blockchain": 0.7,
    "Embedded & IoT": 0.7,
}

# Estimated learning time (weeks) by subcategory
LEARNING_TIME_WEEKS = {
    "Core Web": 2,
    "CSS Frameworks": 1,
    "JavaScript Frameworks": 4,
    "Meta-Frameworks": 3,
    "State Management": 2,
    "Build Tools": 1,
    "Node.js Ecosystem": 3,
    "Python Frameworks": 3,
    "Java/JVM Frameworks": 4,
    ".NET Ecosystem": 4,
    "Go Frameworks": 3,
    "API Technologies": 2,
    "Message Queues": 2,
    "Relational": 3,
    "NoSQL Document": 2,
    "Key-Value": 1,
    "Containerization": 2,
    "Orchestration": 4,
    "CI/CD": 2,
    "Infrastructure as Code": 3,
    "Cloud Platforms": 4,
    "Monitoring & Observability": 2,
    "ML Frameworks": 6,
    "ML Libraries": 3,
    "NLP": 6,
    "Computer Vision": 6,
    "MLOps": 3,
    "Systems Languages": 8,
    "Application Languages": 6,
    "Scripting Languages": 3,
    "Cross-Platform": 4,
    "Android": 6,
    "iOS": 6,
    "Security Frameworks": 2,
    "Security Tools": 3,
    "Authentication": 2,
    "Development Practices": 1,
    "Engineering Practices": 2,
    "Design Principles": 2,
}


class SkillGapExplainer:
    """Generates explainable, actionable skill gap analysis."""

    def __init__(self, ontology: SkillOntology):
        self.ontology = ontology

    def analyze_gap(
        self,
        cv_skills: list[str],
        jd_skills: list[str],
        missing_skills: list[str],
        match_score: float,
    ) -> dict:
        """
        Produce a full explainable skill gap report.

        Returns:
            {
                "summary": str,
                "score_interpretation": str,
                "gap_by_category": {...},
                "priority_skills": [...],
                "learning_plan": [...],
                "transferable_strengths": [...],
                "total_estimated_weeks": int,
            }
        """
        # 1. Score interpretation
        score_interp = self._interpret_score(match_score)

        # 2. Categorize missing skills
        gap_categories = self.ontology.categorize_skills(missing_skills)

        # 3. Build gap explanations per category
        gap_explanations = {}
        for category, skills in gap_categories.items():
            gap_explanations[category] = {
                "skills": skills,
                "count": len(skills),
                "priority": CATEGORY_PRIORITY.get(category, 0.5),
                "explanation": self._explain_category_gap(category, skills, cv_skills),
            }

        # 4. Priority ranking
        priority_skills = self._rank_by_priority(missing_skills, cv_skills)

        # 5. Learning plan
        learning_plan = self._build_learning_plan(priority_skills)

        # 6. Transferable strengths
        strengths = self._find_transferable_strengths(cv_skills, missing_skills)

        # 7. Total estimated time
        total_weeks = sum(item["estimated_weeks"] for item in learning_plan)

        # 8. Summary
        summary = self._generate_summary(
            cv_skills, missing_skills, match_score, gap_categories, total_weeks
        )

        return {
            "summary": summary,
            "score_interpretation": score_interp,
            "gap_by_category": gap_explanations,
            "priority_skills": priority_skills,
            "learning_plan": learning_plan,
            "transferable_strengths": strengths,
            "total_estimated_weeks": total_weeks,
        }

    def _interpret_score(self, score: float) -> str:
        if score >= 85:
            return "Excellent match! You meet most requirements. Focus on the few remaining gaps."
        elif score >= 70:
            return "Good match. You have a strong foundation. A few targeted improvements will make you competitive."
        elif score >= 50:
            return "Moderate match. You have relevant experience but need to develop several key skills."
        elif score >= 30:
            return "Below average match. Significant upskilling needed, but your existing skills provide a starting point."
        else:
            return "Low match. This role requires substantial new skill development. Consider intermediate roles first."

    def _explain_category_gap(self, category: str, missing: list[str], cv_skills: list[str]) -> str:
        """Explain why a category gap matters and how existing skills help."""
        cv_in_category = [
            s for s in cv_skills
            if self.ontology.get_category(s) == category
        ]

        if cv_in_category:
            return (
                f"You have {len(cv_in_category)} skills in {category} "
                f"({', '.join(cv_in_category[:3])}), but need to add "
                f"{', '.join(missing[:3])}. Your existing knowledge will accelerate learning."
            )
        else:
            return (
                f"You currently lack skills in {category}. "
                f"Skills needed: {', '.join(missing[:3])}. "
                f"This is a new domain that will require dedicated study."
            )

    def _rank_by_priority(self, missing_skills: list[str], cv_skills: list[str]) -> list[dict]:
        """Rank missing skills by learning priority."""
        ranked = []
        for skill in missing_skills:
            cat = self.ontology.get_category(skill) or "Other"
            subcat = self.ontology.get_subcategory(skill)
            base_priority = CATEGORY_PRIORITY.get(cat, 0.5)

            # Boost priority if candidate has related skills (faster to learn)
            has_related = any(
                self.ontology.skill_distance(skill, cv_s) <= 0.5
                for cv_s in cv_skills
            )
            if has_related:
                base_priority *= 1.15  # 15% boost for transferable skills

            related = self.ontology.get_related(skill)
            cv_related = [r for r in related if r.lower() in [s.lower() for s in cv_skills]]

            ranked.append({
                "skill": skill,
                "category": cat,
                "subcategory": subcat or "General",
                "priority_score": round(min(1.0, base_priority), 2),
                "has_related_skills": bool(cv_related),
                "related_cv_skills": cv_related[:3],
                "reason": (
                    f"High priority for {cat}."
                    + (f" You already know {', '.join(cv_related[:2])}, which helps." if cv_related else "")
                ),
            })

        ranked.sort(key=lambda x: -x["priority_score"])
        return ranked

    def _build_learning_plan(self, priority_skills: list[dict]) -> list[dict]:
        """Build a phased learning plan with time estimates."""
        plan = []
        for i, item in enumerate(priority_skills):
            subcat = item.get("subcategory", "General")
            est_weeks = LEARNING_TIME_WEEKS.get(subcat, 3)

            # Reduce time if candidate has related skills
            if item.get("has_related_skills"):
                est_weeks = max(1, int(est_weeks * 0.6))

            if i < 3:
                phase = "Phase 1 (Immediate)"
            elif i < 6:
                phase = "Phase 2 (Short-term)"
            else:
                phase = "Phase 3 (Long-term)"

            plan.append({
                "skill": item["skill"],
                "phase": phase,
                "estimated_weeks": est_weeks,
                "approach": self._suggest_approach(item["skill"], item.get("related_cv_skills", [])),
            })

        return plan

    def _suggest_approach(self, skill: str, related_cv_skills: list[str]) -> str:
        """Suggest learning approach based on skill type and existing knowledge."""
        cat = self.ontology.get_category(skill)

        if related_cv_skills:
            return (
                f"Leverage your {', '.join(related_cv_skills[:2])} experience. "
                f"Focus on differences and unique features of {skill}."
            )

        approaches = {
            "Programming Languages": f"Start with official tutorials and build 2-3 small projects with {skill}.",
            "Frontend Development": f"Build a portfolio project using {skill}. Focus on component architecture.",
            "Backend Development": f"Build a REST API with {skill}. Practice with database integration.",
            "Database": f"Set up {skill} locally, practice CRUD operations and query optimization.",
            "DevOps & Infrastructure": f"Set up {skill} in a personal project. Practice with Docker/CI pipeline.",
            "Machine Learning & AI": f"Complete a Kaggle competition or course using {skill}.",
            "Security": f"Study {skill} through CTF challenges and OWASP resources.",
        }
        return approaches.get(cat, f"Study {skill} through documentation and hands-on projects.")

    def _find_transferable_strengths(self, cv_skills: list[str], missing_skills: list[str]) -> list[dict]:
        """Identify CV skills that transfer well to missing requirements."""
        strengths = []
        seen = set()

        for cv_skill in cv_skills:
            for missing in missing_skills:
                dist = self.ontology.skill_distance(cv_skill, missing)
                key = f"{cv_skill.lower()}-{missing.lower()}"
                if dist <= 0.5 and key not in seen:
                    seen.add(key)
                    strengths.append({
                        "existing_skill": cv_skill,
                        "helps_with": missing,
                        "relationship": self.ontology.explain_relationship(cv_skill, missing),
                        "transfer_strength": round(1.0 - dist, 2),
                    })

        strengths.sort(key=lambda x: -x["transfer_strength"])
        return strengths[:10]

    def _generate_summary(
        self, cv_skills, missing_skills, score, gap_categories, total_weeks
    ) -> str:
        """Generate a concise executive summary."""
        n_cv = len(cv_skills)
        n_missing = len(missing_skills)
        n_cats = len([c for c in gap_categories if c != "Other"])

        if score >= 85:
            tone = "You are an excellent fit"
        elif score >= 70:
            tone = "You are a good fit"
        elif score >= 50:
            tone = "You are a moderate fit"
        else:
            tone = "There is a significant gap"

        return (
            f"{tone} for this position (match score: {score}%). "
            f"You bring {n_cv} relevant skills. "
            f"To fully qualify, you need to develop {n_missing} additional "
            f"skill{'s' if n_missing != 1 else ''} across {n_cats} "
            f"categor{'ies' if n_cats != 1 else 'y'}. "
            f"Estimated preparation time: {total_weeks} weeks with focused study."
        )
