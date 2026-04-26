import logging
import pandas as pd
from pathlib import Path
from typing import List, Dict, Optional
import chromadb
from services.career_service.models.schemas import CareerStep, CareerPath, SkillGap

logger = logging.getLogger(__name__)

# IT career progression paths (role code -> possible next roles)
IT_CAREER_GRAPH: Dict[str, List[Dict[str, str]]] = {
    # Developer tracks
    "junior_developer": [
        {"role": "Software Developer", "code": "15-1252.00", "timeframe": "1-2 years"},
    ],
    "15-1252.00": [  # Software Developers
        {"role": "Senior Software Developer", "code": "15-1252.00", "timeframe": "2-3 years"},
        {"role": "Software Quality Assurance", "code": "15-1253.00", "timeframe": "1-2 years"},
        {"role": "Computer Systems Analyst", "code": "15-1211.00", "timeframe": "2-3 years"},
    ],
    "15-1254.00": [  # Web Developers
        {"role": "Software Developer", "code": "15-1252.00", "timeframe": "1-2 years"},
        {"role": "Web and Digital Interface Designer", "code": "15-1255.00", "timeframe": "1-2 years"},
    ],
    "15-1211.00": [  # Computer Systems Analysts
        {"role": "Computer and Information Systems Manager", "code": "11-3021.00", "timeframe": "3-5 years"},
        {"role": "Computer Network Architect", "code": "15-1241.00", "timeframe": "2-3 years"},
    ],
    "15-1212.00": [  # Information Security Analysts
        {"role": "Information Security Engineer", "code": "15-1299.05", "timeframe": "2-3 years"},
        {"role": "Computer and Information Systems Manager", "code": "11-3021.00", "timeframe": "3-5 years"},
    ],
    "15-1242.00": [  # Database Administrators
        {"role": "Database Architect", "code": "15-1243.00", "timeframe": "2-3 years"},
        {"role": "Data Warehousing Specialist", "code": "15-1243.01", "timeframe": "1-2 years"},
    ],
    "15-1253.00": [  # Software QA
        {"role": "Software Developer", "code": "15-1252.00", "timeframe": "1-2 years"},
        {"role": "IT Project Manager", "code": "15-1299.09", "timeframe": "2-3 years"},
    ],
    "15-1244.00": [  # Network/Systems Admins
        {"role": "Computer Network Architect", "code": "15-1241.00", "timeframe": "2-3 years"},
        {"role": "Information Security Analyst", "code": "15-1212.00", "timeframe": "1-2 years"},
    ],
    "15-1221.00": [  # Computer/Info Research Scientists
        {"role": "Computer and Information Systems Manager", "code": "11-3021.00", "timeframe": "3-5 years"},
    ],
    "15-1241.00": [  # Computer Network Architects
        {"role": "Computer and Information Systems Manager", "code": "11-3021.00", "timeframe": "3-5 years"},
    ],
    "15-1299.09": [  # IT Project Managers
        {"role": "Computer and Information Systems Manager", "code": "11-3021.00", "timeframe": "2-3 years"},
    ],
    "11-3021.00": [  # Computer and Information Systems Managers
        {"role": "Chief Technology Officer", "code": "11-1011.00", "timeframe": "5-10 years"},
    ],
    "17-2061.00": [  # Computer Hardware Engineers / IoT Engineers
        {"role": "Computer Network Architects", "code": "15-1241.00", "timeframe": "2-3 years"},
        {"role": "Computer Systems Engineers/Architects", "code": "15-1299.08", "timeframe": "2-3 years"},
        {"role": "Information Security Analysts", "code": "15-1212.00", "timeframe": "2-4 years"},
    ],
    "15-1299.08": [  # Computer Systems Engineers/Architects
        {"role": "Computer and Information Systems Manager", "code": "11-3021.00", "timeframe": "3-5 years"},
        {"role": "Computer Network Architects", "code": "15-1241.00", "timeframe": "2-3 years"},
    ],
    "15-2051.01": [  # Data/Business Intelligence Analysts
        {"role": "Database Architects", "code": "15-1243.00", "timeframe": "2-3 years"},
        {"role": "Computer/Info Research Scientists", "code": "15-1221.00", "timeframe": "2-4 years"},
        {"role": "Computer Systems Analysts", "code": "15-1211.00", "timeframe": "1-2 years"},
    ],
}

# Common role aliases → O*NET code (for roles not in O*NET by exact name)
ROLE_ALIASES: Dict[str, str] = {
    # Backend
    "backend": "15-1252.00",
    "backend developer": "15-1252.00",
    "backend engineer": "15-1252.00",
    "server-side developer": "15-1252.00",
    "software engineer": "15-1252.00",
    "junior developer": "15-1252.00",
    "junior software engineer": "15-1252.00",
    "senior software engineer": "15-1252.00",
    "senior developer": "15-1252.00",
    # Frontend / Web
    "frontend": "15-1254.00",
    "frontend developer": "15-1254.00",
    "frontend engineer": "15-1254.00",
    "front-end developer": "15-1254.00",
    "web developer": "15-1254.00",
    "ui developer": "15-1254.00",
    # Full-stack
    "fullstack": "15-1252.00",
    "full-stack": "15-1252.00",
    "full stack developer": "15-1252.00",
    "full-stack developer": "15-1252.00",
    "full stack engineer": "15-1252.00",
    # Mobile
    "mobile developer": "15-1252.00",
    "android developer": "15-1252.00",
    "ios developer": "15-1252.00",
    # DevOps / SRE / Infra
    "devops": "15-1244.00",
    "devops engineer": "15-1244.00",
    "sre": "15-1244.00",
    "site reliability engineer": "15-1244.00",
    "infrastructure engineer": "15-1244.00",
    "cloud engineer": "15-1244.00",
    "systems administrator": "15-1244.00",
    "sysadmin": "15-1244.00",
    # Data
    "data analyst": "15-2051.01",
    "data engineer": "15-1243.00",
    "data scientist": "15-1221.00",
    "machine learning engineer": "15-1221.00",
    "ml engineer": "15-1221.00",
    "ai engineer": "15-1221.00",
    "database administrator": "15-1242.00",
    "dba": "15-1242.00",
    # Security
    "security engineer": "15-1299.05",
    "cybersecurity engineer": "15-1299.05",
    "security analyst": "15-1212.00",
    "cybersecurity analyst": "15-1212.00",
    "penetration tester": "15-1299.05",
    "pentester": "15-1299.05",
    # QA / Test
    "qa engineer": "15-1253.00",
    "test engineer": "15-1253.00",
    "software tester": "15-1253.00",
    "quality assurance": "15-1253.00",
    # Network
    "network engineer": "15-1241.00",
    "network architect": "15-1241.00",
    "network administrator": "15-1244.00",
    # IoT / Embedded / Hardware
    "iot": "17-2061.00",
    "iot engineer": "17-2061.00",
    "iot developer": "17-2061.00",
    "internet of things": "17-2061.00",
    "embedded engineer": "17-2061.00",
    "embedded developer": "17-2061.00",
    "embedded systems engineer": "17-2061.00",
    "firmware engineer": "17-2061.00",
    "hardware engineer": "17-2061.00",
    # Management
    "tech lead": "15-1299.09",
    "technical lead": "15-1299.09",
    "it project manager": "15-1299.09",
    "project manager": "15-1299.09",
    "engineering manager": "11-3021.00",
    "it manager": "11-3021.00",
    "cto": "11-1011.00",
    "chief technology officer": "11-1011.00",
    # Systems
    "systems analyst": "15-1211.00",
    "systems engineer": "15-1299.08",
    "solutions architect": "15-1299.08",
    "software architect": "15-1299.08",
    "blockchain engineer": "15-1299.07",
}

# Technology skills associated with IT roles (mapped from O*NET Technology Skills)
ROLE_TECH_SKILLS: Dict[str, List[str]] = {
    "15-1252.00": ["Python", "Java", "JavaScript", "Git", "SQL", "Docker", "REST API", "Agile", "CI/CD"],
    "15-1254.00": ["HTML", "CSS", "JavaScript", "React", "Node.js", "Git", "REST API"],
    "15-1253.00": ["Selenium", "Jest", "Python", "Jira", "CI/CD", "SQL", "Postman", "ISTQB"],
    "15-1212.00": ["OWASP", "Nmap", "Wireshark", "Python", "Linux", "SIEM", "AWS", "Burp Suite"],
    "15-1242.00": ["SQL", "PostgreSQL", "MySQL", "Oracle", "MongoDB", "Redis", "Python", "Linux"],
    "15-1243.00": ["SQL", "PostgreSQL", "Snowflake", "BigQuery", "Python", "Spark", "Airflow", "dbt"],
    "15-1244.00": ["Linux", "Nginx", "Docker", "Kubernetes", "AWS", "Terraform", "Ansible", "Prometheus"],
    "15-1241.00": ["Cisco", "AWS", "Azure", "Kubernetes", "Terraform", "Linux", "Docker", "Networking"],
    "15-1211.00": ["Python", "SQL", "UML", "Jira", "Agile", "REST API", "Microservices", "Docker"],
    "15-1299.09": ["Jira", "Agile", "Scrum", "MS Project", "Risk Management", "Confluence", "Git"],
    "11-3021.00": ["Leadership", "Strategic Planning", "Agile", "Cloud", "DevOps", "Architecture", "Budget"],
    "15-1221.00": ["Python", "TensorFlow", "PyTorch", "Machine Learning", "AI", "Research", "NLP"],
    "15-1299.05": ["OWASP", "Penetration Testing", "SIEM", "Python", "Cloud Security", "IAM", "PKI"],
    "15-1299.08": ["Python", "Java", "Microservices", "Docker", "Kubernetes", "AWS", "UML", "REST API"],
    "15-1299.07": ["Solidity", "Ethereum", "Hyperledger", "Python", "Go", "Cryptography", "Smart Contracts"],
    "17-2061.00": ["C", "C++", "Embedded C", "MQTT", "Linux", "RTOS", "Arduino", "Raspberry Pi", "IoT protocols", "Firmware"],
    "15-2051.01": ["SQL", "Python", "Excel", "Tableau", "Power BI", "Statistics", "R", "Data Visualization"],
    "15-1243.01": ["SQL", "ETL", "Python", "Hadoop", "Spark", "Data Modeling", "Airflow", "BigQuery"],
}


class CareerAdvisor:
    """Enhanced career path advisor with multi-step progression and experience-based logic."""

    def __init__(self, onet_path: str, collection: chromadb.Collection):
        self.onet_path = Path(onet_path)
        self.collection = collection
        self.occupations: Dict[str, dict] = {}
        self.skills_map: Dict[str, List[str]] = {}
        self.tech_skills: Dict[str, List[str]] = {}
        self.load_data()

    def load_data(self):
        """Load O*NET flat files and tech skills."""
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
            for code in self.occupations.keys():
                occ_skills = df[df["O*NET-SOC Code"] == code]
                if not occ_skills.empty:
                    self.skills_map[code] = occ_skills["Element Name"].tolist()[:8]

        # Load tech skills (O*NET Technology Skills + curated)
        tech_file = self.onet_path / "Technology Skills.txt"
        if tech_file.exists():
            df = pd.read_csv(tech_file, sep="\t")
            for code in self.occupations.keys():
                if code.startswith("15-") or code.startswith("11-3021"):
                    occ_tech = df[df["O*NET-SOC Code"] == code]
                    if not occ_tech.empty:
                        # Get hot technologies first, then others
                        hot = occ_tech[occ_tech.get("Hot Technology", "") == "Y"]
                        skills = hot["Example"].tolist()[:5]
                        skills += occ_tech["Example"].tolist()[:10]
                        self.tech_skills[code] = list(dict.fromkeys(skills))[:10]

        # Merge with curated tech skills
        for code, skills in ROLE_TECH_SKILLS.items():
            if code not in self.tech_skills:
                self.tech_skills[code] = skills
            else:
                existing = set(s.lower() for s in self.tech_skills[code])
                for s in skills:
                    if s.lower() not in existing:
                        self.tech_skills[code].append(s)

        logger.info(f"Loaded {len(self.occupations)} occupations, {len(self.tech_skills)} with tech skills")

    def find_role(self, query: str) -> Optional[dict]:
        """Find role by alias → exact → substring → semantic."""
        query_lower = query.lower().strip()

        # 1. Alias lookup (common shorthand names not in O*NET)
        if query_lower in ROLE_ALIASES:
            code = ROLE_ALIASES[query_lower]
            occ = self.occupations.get(code)
            if occ:
                return occ
            # Code not in loaded occupations — build synthetic entry
            return {"code": code, "title": query.title(), "description": ""}

        # 2. Exact match against O*NET titles
        for code, occ in self.occupations.items():
            if occ["title"].lower() == query_lower:
                return occ

        # 3. Plural/singular variants
        variants = {query_lower, query_lower.rstrip('s'), query_lower + 's'}
        for code, occ in self.occupations.items():
            if occ["title"].lower() in variants:
                return occ

        # 4. Substring match (query inside title)
        for code, occ in self.occupations.items():
            if query_lower in occ["title"].lower():
                return occ

        # 5. Substring match (title inside query)
        for code, occ in self.occupations.items():
            if occ["title"].lower() in query_lower:
                return occ

        # 6. Semantic search via ChromaDB
        if self.collection:
            res = self.collection.query(query_texts=[query], n_results=1)
            if res["metadatas"] and res["metadatas"][0]:
                code = res["metadatas"][0][0].get("code")
                return self.occupations.get(code)
        return None

    def find_related_it_roles(self, code: str) -> List[dict]:
        """Find related IT roles from career graph and O*NET."""
        related = []

        # From career graph
        next_roles = IT_CAREER_GRAPH.get(code, [])
        for nr in next_roles:
            occ = self.occupations.get(nr["code"])
            if occ:
                related.append({**occ, "timeframe": nr["timeframe"]})

        # From O*NET semantic search if few results
        if len(related) < 3 and self.collection:
            current = self.occupations.get(code, {})
            if current:
                res = self.collection.query(
                    query_texts=[current.get("title", "")],
                    n_results=5
                )
                if res["metadatas"] and res["metadatas"][0]:
                    for meta in res["metadatas"][0]:
                        rcode = meta.get("code", "")
                        if rcode != code and rcode not in [r["code"] for r in related]:
                            occ = self.occupations.get(rcode)
                            if occ:
                                related.append({**occ, "timeframe": "2-4 years"})

        return related[:5]

    def calculate_gap(self, current_skills: List[str], target_code: str) -> SkillGap:
        """Analyze skill gap using technology skills only (excludes O*NET soft skills)."""
        tech = self.tech_skills.get(target_code, [])
        # Fallback to O*NET skills only when no tech skills exist for this role
        required = tech if tech else self.skills_map.get(target_code, [])

        curr_lower = {s.lower() for s in current_skills}
        missing = [s for s in required if s.lower() not in curr_lower]
        overlap = [s for s in required if s.lower() in curr_lower]

        return SkillGap(
            current=current_skills,
            required=required,
            missing=missing,
            overlap=overlap,
            readiness_score=round(len(overlap) / max(1, len(required)) * 100, 1),
        )

    def estimate_experience_level(self, skills: List[str]) -> str:
        """Estimate seniority based on breadth and depth of skills."""
        n = len(skills)
        if n <= 3:
            return "junior"
        elif n <= 8:
            return "mid"
        elif n <= 15:
            return "senior"
        else:
            return "lead"

    def generate_paths(self, current: dict, target: dict, gap: SkillGap,
                       current_skills: List[str] = None) -> List[CareerPath]:
        """
        Generate multi-step career paths based on experience and skill gap.
        Returns conservative, moderate, and ambitious paths.
        """
        level = self.estimate_experience_level(current_skills or gap.current)
        readiness = gap.readiness_score if hasattr(gap, 'readiness_score') else 50

        # Find intermediate roles
        intermediate_roles = self.find_related_it_roles(current["code"])
        intermediate_roles = [
            r for r in intermediate_roles
            if r["code"] != target["code"]
        ]

        paths = []

        # ─── Conservative Path (step-by-step, with intermediate roles) ───
        if intermediate_roles and readiness < 60:
            steps = []
            for i, ir in enumerate(intermediate_roles[:2]):
                ir_gap = self.calculate_gap(current_skills or gap.current, ir["code"])
                steps.append(CareerStep(
                    step=i + 1,
                    role=ir["title"],
                    role_code=ir["code"],
                    timeframe=ir.get("timeframe", "1-2 years"),
                    skills_to_learn=ir_gap.missing[:4],
                    description=f"Build experience as {ir['title']} to develop foundational skills.",
                ))

            steps.append(CareerStep(
                step=len(steps) + 1,
                role=target["title"],
                role_code=target["code"],
                timeframe="1-2 years",
                skills_to_learn=gap.missing[:5],
                description=f"Transition to target role after building prerequisite experience.",
            ))

            total_years = len(steps) + 1
            paths.append(CareerPath(
                path_type="conservative",
                total_time=f"{total_years}-{total_years + 2} years",
                steps=steps,
            ))

        # ─── Moderate Path (1-2 steps, focused upskilling) ───
        moderate_steps = []
        if readiness < 70 and gap.missing:
            # Split missing skills into two phases
            phase1 = gap.missing[:len(gap.missing) // 2 + 1]
            phase2 = gap.missing[len(gap.missing) // 2 + 1:]

            moderate_steps.append(CareerStep(
                step=1,
                role=f"{current['title']} (Upskilling Phase)",
                role_code=current["code"],
                timeframe="6-12 months",
                skills_to_learn=phase1[:5],
                description="Focus on acquiring core missing skills while in current role.",
            ))

            if phase2:
                moderate_steps.append(CareerStep(
                    step=2,
                    role=target["title"],
                    role_code=target["code"],
                    timeframe="6-12 months",
                    skills_to_learn=phase2[:5],
                    description="Apply for target role and continue learning remaining skills on the job.",
                ))
            else:
                moderate_steps.append(CareerStep(
                    step=2,
                    role=target["title"],
                    role_code=target["code"],
                    timeframe="3-6 months",
                    skills_to_learn=[],
                    description="Transition to target role with newly acquired skills.",
                ))
        else:
            moderate_steps.append(CareerStep(
                step=1,
                role=target["title"],
                role_code=target["code"],
                timeframe="3-6 months",
                skills_to_learn=gap.missing[:5],
                description="Direct transition with minor upskilling.",
            ))

        paths.append(CareerPath(
            path_type="moderate",
            total_time="1-2 years" if readiness < 70 else "3-6 months",
            steps=moderate_steps,
        ))

        # ─── Ambitious Path (fast-track, direct jump) ───
        ambitious_time = "3-6 months" if readiness >= 50 else "6-12 months"
        paths.append(CareerPath(
            path_type="ambitious",
            total_time=ambitious_time,
            steps=[CareerStep(
                step=1,
                role=target["title"],
                role_code=target["code"],
                timeframe=ambitious_time,
                skills_to_learn=gap.missing[:3],
                description=(
                    f"Fast-track: Focus on top 3 critical skills and leverage your "
                    f"{len(gap.overlap)} existing relevant skills to secure the role quickly."
                    if hasattr(gap, 'overlap') else "Fast-track transition."
                ),
            )],
        ))

        return paths
