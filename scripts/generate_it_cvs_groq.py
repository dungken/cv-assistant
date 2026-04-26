"""
Generate synthetic IT CVs using Groq API (llama-3.3-70b-versatile).
Drop-in replacement for generate_it_cvs.py — same data, Groq backend instead of Ollama.

Usage:
    python scripts/generate_it_cvs_groq.py --count 1000 --workers 4
    python scripts/generate_it_cvs_groq.py --count 1000 --resume   # resume interrupted run

Groq free tier: ~30 req/min, 14,400 req/day — enough for 1000 CVs in ~35 min.
"""

import os
import re
import json
import time
import random
import hashlib
import argparse
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from groq import Groq

# ─── Configuration ────────────────────────────────────────────────────────────

GROQ_API_KEY = os.getenv("CHAT_GROQ_API_KEY") or os.getenv("GROQ_API_KEY", "")
GROQ_MODEL   = os.getenv("GROQ_MODEL", os.getenv("CHAT_GROQ_MODEL", "llama-3.3-70b-versatile"))

OUTPUT_DIR   = Path("data/raw/synthetic_it")
TARGET_COUNT = 1000
MAX_WORKERS  = 4   # Groq can handle concurrent requests; free tier ~30 req/min total

# Rate limiting: stay under 30 req/min on free tier
# With 4 workers: 1 req per worker per ~8 sec → ~30 req/min total
DELAY_BETWEEN_REQUESTS = 0.5   # seconds between requests per worker

# ─── IT Roles ─────────────────────────────────────────────────────────────────

IT_ROLES = [
    "Software Developer", "Frontend Developer", "Backend Developer",
    "Full Stack Developer", "Mobile Developer", "DevOps Engineer",
    "Cloud Engineer", "Data Engineer", "Data Scientist",
    "Machine Learning Engineer", "AI Engineer", "QA Engineer",
    "Software Tester", "Database Administrator", "System Administrator",
    "Network Engineer", "Information Security Analyst", "Cybersecurity Engineer",
    "Penetration Tester", "Web Developer", "UI/UX Designer",
    "IT Project Manager", "Scrum Master", "Business Analyst",
    "Solutions Architect", "Site Reliability Engineer", "Platform Engineer",
    "Embedded Systems Engineer", "Blockchain Developer", "Game Developer",
    "Technical Lead", "Engineering Manager", "Computer Vision Engineer",
    "NLP Engineer", "IoT Developer",
]

SKILL_POOLS = {
    "programming": [
        "Python", "Java", "JavaScript", "TypeScript", "C#", "C++", "Go", "Rust",
        "Ruby", "PHP", "Kotlin", "Swift", "Scala", "R", "Dart", "Shell Scripting",
    ],
    "frontend": [
        "React", "Angular", "Vue.js", "Next.js", "Nuxt.js", "Svelte",
        "HTML5", "CSS3", "SASS", "Tailwind CSS", "Bootstrap", "Material UI",
        "Redux", "Webpack", "Vite", "jQuery", "D3.js",
    ],
    "backend": [
        "Node.js", "Django", "Flask", "FastAPI", "Spring Boot", "ASP.NET Core",
        "Express.js", "NestJS", "Ruby on Rails", "Laravel", "Gin",
        "GraphQL", "gRPC", "REST API", "Microservices",
    ],
    "database": [
        "PostgreSQL", "MySQL", "MongoDB", "Redis", "Elasticsearch", "Cassandra",
        "Oracle", "SQL Server", "DynamoDB", "Firebase", "Neo4j",
        "SQLite", "MariaDB",
    ],
    "devops": [
        "Docker", "Kubernetes", "Jenkins", "GitHub Actions", "GitLab CI/CD",
        "Terraform", "Ansible", "AWS", "Azure", "GCP", "Prometheus", "Grafana",
        "Nginx", "Linux", "Helm", "ArgoCD",
    ],
    "data_ml": [
        "TensorFlow", "PyTorch", "Scikit-learn", "Pandas", "NumPy", "Spark",
        "Hadoop", "Airflow", "Kafka", "Tableau", "Power BI",
        "MLflow", "OpenCV", "Hugging Face", "LangChain",
    ],
    "tools": [
        "Git", "Jira", "Confluence", "Postman", "Swagger", "Figma",
        "VS Code", "IntelliJ IDEA", "Slack", "Notion",
    ],
    "security": [
        "OWASP", "Burp Suite", "Metasploit", "Wireshark", "Nmap", "Nessus",
        "PKI", "OAuth 2.0", "JWT", "SAML", "SSL/TLS",
    ],
}

VN_COMPANIES = [
    "FPT Software", "Viettel Solutions", "VNG Corporation", "Tiki",
    "Shopee Vietnam", "MoMo", "VNPay", "KMS Technology", "TMA Solutions",
    "NashTech", "Axon Active", "CMC Corporation", "VNPT IT",
    "ZaloPay", "Grab Vietnam", "One Mount Group",
    "Samsung Vietnam R&D", "LG Development Center Vietnam", "Bosch Vietnam",
    "Fujitsu Vietnam", "Rikkeisoft", "Sun Asterisk", "CO-WELL Asia",
    "Savvycom", "Niteco Vietnam", "NFQ Asia",
    "TechVify Software", "Orient Software", "Golden Owl Consulting",
    "Enlab Software", "Amanotes", "Gameloft Vietnam", "Sky Mavis",
]

VN_UNIVERSITIES = [
    "Vietnam National University (VNU)", "Ho Chi Minh City University of Technology (HCMUT)",
    "University of Information Technology (UIT)", "Posts and Telecommunications Institute (PTIT)",
    "Hanoi University of Science and Technology (HUST)", "FPT University",
    "Ton Duc Thang University", "University of Science (HCMUS)",
    "Da Nang University of Science and Technology", "Le Quy Don Technical University",
    "HUTECH University", "University of Transport and Communications (UTC2)",
    "Thai Nguyen University of Information and Communication Technology",
    "Can Tho University",
]

VN_NAMES = [
    "Nguyen Van An", "Tran Thi Binh", "Le Hoang Cuong", "Pham Minh Duc",
    "Vo Thanh Em", "Hoang Thi Phuong", "Bui Quoc Gia", "Dang Van Hai",
    "Do Thi Huong", "Ngo Quang Khai", "Ly Van Lam", "Duong Thi Mai",
    "Truong Hoang Nam", "Ha Thi Oanh", "Luu Van Phuc", "Mai Thi Quynh",
    "Dinh Van Rang", "Vu Thi Son", "Cao Van Tai", "Huynh Thi Uyen",
    "Phan Van Vinh", "Trinh Thi Xuan", "Tang Van Yen", "Lam Thi Zung",
    "Nguyen Duc Anh", "Tran Quoc Bao", "Le Van Chien", "Pham Thi Dao",
    "Vo Minh Hieu", "Hoang Van Khoa", "Bui Thi Linh", "Dang Quoc Minh",
    "Do Van Nghia", "Ngo Thi Phuong", "Ly Hoang Quan", "Duong Van Sang",
    "Truong Thi Thao", "Ha Van Tuan", "Luu Thi Van", "Mai Hoang Vu",
    "Nguyen Thi Thu", "Tran Van Kiet", "Le Thi Hoa", "Pham Hoang Long",
    "Vo Thi Kim Anh", "Hoang Minh Tri", "Bui Van Thanh", "Dang Thi Lan",
]

CERTIFICATIONS = [
    "AWS Certified Solutions Architect", "AWS Certified Developer",
    "Azure Administrator Associate", "Azure Solutions Architect",
    "Google Cloud Professional Cloud Architect",
    "Certified Kubernetes Administrator (CKA)", "Docker Certified Associate",
    "Certified Scrum Master (CSM)", "PMP (Project Management Professional)",
    "CompTIA Security+", "CISSP", "CEH (Certified Ethical Hacker)",
    "CCNA (Cisco Certified Network Associate)", "Oracle Certified Professional",
    "Red Hat Certified System Administrator (RHCSA)", "Terraform Associate",
    "MongoDB Certified Developer", "TensorFlow Developer Certificate",
    "ISTQB Certified Tester", "TOGAF Certified", "ITIL Foundation",
    "Agile Certified Practitioner (PMI-ACP)",
]

EXPERIENCE_LEVELS = ["junior", "mid", "senior", "lead", "principal"]

# Edge types control CV diversity
EDGE_TYPES = {
    "normal":       "Write a standard full CV (300-500 words).",
    "short":        "Write a brief CV under 200 words (fresher / entry-level style).",
    "verbose":      "Write a detailed CV over 500 words with rich project descriptions.",
    "mixed_vi_en":  "Mix Vietnamese sentences naturally with English technical terms.",
}
EDGE_TYPE_WEIGHTS = [0.5, 0.15, 0.2, 0.15]   # 50% normal, 15% short, 20% verbose, 15% mixed


# ─── Skill selection ──────────────────────────────────────────────────────────

def get_role_skills(role: str) -> list[str]:
    role_lower = role.lower()
    skills = list(SKILL_POOLS["tools"])

    if any(k in role_lower for k in ["frontend", "ui", "ux", "web"]):
        skills += random.sample(SKILL_POOLS["frontend"], min(6, len(SKILL_POOLS["frontend"])))
        skills += random.sample(SKILL_POOLS["programming"], 3)
    elif any(k in role_lower for k in ["backend", "api"]):
        skills += random.sample(SKILL_POOLS["backend"], min(5, len(SKILL_POOLS["backend"])))
        skills += random.sample(SKILL_POOLS["database"], 3)
        skills += random.sample(SKILL_POOLS["programming"], 4)
    elif "full stack" in role_lower:
        skills += random.sample(SKILL_POOLS["frontend"], 4)
        skills += random.sample(SKILL_POOLS["backend"], 4)
        skills += random.sample(SKILL_POOLS["database"], 3)
        skills += random.sample(SKILL_POOLS["programming"], 3)
    elif any(k in role_lower for k in ["devops", "sre", "cloud", "platform"]):
        skills += random.sample(SKILL_POOLS["devops"], min(8, len(SKILL_POOLS["devops"])))
        skills += random.sample(SKILL_POOLS["programming"], 2)
    elif any(k in role_lower for k in ["data", "ml", "ai", "machine learning", "nlp", "vision"]):
        skills += random.sample(SKILL_POOLS["data_ml"], min(7, len(SKILL_POOLS["data_ml"])))
        skills += random.sample(SKILL_POOLS["programming"], 3)
        skills += random.sample(SKILL_POOLS["database"], 2)
    elif any(k in role_lower for k in ["security", "penetration", "cyber"]):
        skills += random.sample(SKILL_POOLS["security"], min(6, len(SKILL_POOLS["security"])))
        skills += random.sample(SKILL_POOLS["programming"], 2)
    elif "mobile" in role_lower:
        skills += random.sample(SKILL_POOLS["programming"], 3)
        skills += ["React Native", "Flutter", "Swift", "Kotlin"]
        skills += random.sample(SKILL_POOLS["backend"], 2)
    elif "database" in role_lower or "dba" in role_lower:
        skills += random.sample(SKILL_POOLS["database"], min(6, len(SKILL_POOLS["database"])))
        skills += random.sample(SKILL_POOLS["programming"], 2)
    elif "game" in role_lower:
        skills += ["Unity", "Unreal Engine", "C#", "C++", "OpenGL"]
        skills += random.sample(SKILL_POOLS["programming"], 2)
    else:
        skills += random.sample(SKILL_POOLS["programming"], 4)
        skills += random.sample(SKILL_POOLS["backend"], 3)
        skills += random.sample(SKILL_POOLS["database"], 2)
        skills += random.sample(SKILL_POOLS["devops"], 2)

    return list(set(skills))


# ─── Prompt builder ───────────────────────────────────────────────────────────

def build_prompt(role: str, level: str, name: str, skills: list[str],
                 edge_type: str = "normal") -> str:
    years_map = {
        "junior": "1-2", "mid": "3-5", "senior": "5-8",
        "lead": "8-12", "principal": "10-15",
    }
    years        = years_map[level]
    companies    = random.sample(VN_COMPANIES, min(3, len(VN_COMPANIES)))
    uni          = random.choice(VN_UNIVERSITIES)
    certs        = random.sample(CERTIFICATIONS, random.randint(0, 2))
    skill_str    = ", ".join(random.sample(skills, min(12, len(skills))))
    edge_hint    = EDGE_TYPES[edge_type]

    return f"""Generate a realistic IT professional CV for:

Name: {name}
Role: {level.capitalize()} {role}
Experience: {years} years
Location: Vietnam
Skills: {skill_str}
Companies: {", ".join(companies)}
University: {uni}
Certifications: {", ".join(certs) if certs else "None"}

{edge_hint}

Format (plain text only — NO markdown, NO asterisks, NO #):
1. Full name + contact (email, phone, location)
2. Professional Summary (2-3 sentences)
3. Experience (2-3 positions: company, dates, achievements with metrics)
4. Education (degree, university, graduation year)
5. Technical Skills (list)
6. Certifications (if any)

Rules:
- Use realistic Vietnamese names and companies
- Include specific metrics in achievements (e.g. "reduced latency by 30%")
- English only (unless mixed_vi_en style requested)
- Use plain dash (-) for bullet points"""


# ─── CV generation via Groq ───────────────────────────────────────────────────

def generate_cv(client: Groq, prompt: str, model: str,
                max_retries: int = 3) -> str | None:
    for attempt in range(max_retries):
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1024,
                temperature=0.85,
                top_p=0.95,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            err = str(e)
            if "rate_limit" in err.lower() or "429" in err:
                wait = 60 * (attempt + 1)
                print(f"  [RATE LIMIT] waiting {wait}s before retry {attempt+1}...")
                time.sleep(wait)
            else:
                print(f"  [ERROR] attempt {attempt+1}: {e}")
                time.sleep(2 * (attempt + 1))
    return None


def clean_cv_text(text: str) -> str:
    text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)
    text = re.sub(r'\*([^*]+)\*', r'\1', text)
    text = re.sub(r'^#{1,3}\s+', '', text, flags=re.MULTILINE)
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()


def compute_quality_score(text: str, skills: list[str]) -> float:
    score = 0.0
    words = text.split()
    text_upper = text.upper()
    text_lower = text.lower()

    # Criteria 1: valid length (100–1000 words)
    if 100 <= len(words) <= 1000:
        score += 0.3

    # Criteria 2: required sections present
    sections = sum(1 for s in ["EXPERIENCE", "EDUCATION", "SKILLS", "SUMMARY"]
                   if s in text_upper)
    score += 0.4 * (sections / 4)

    # Criteria 3: ≥60% of metadata skills appear in text
    matched = sum(1 for sk in skills if sk.lower() in text_lower)
    if skills and matched / len(skills) >= 0.6:
        score += 0.3

    return round(score, 2)


def generate_filename(role: str, name: str) -> str:
    role_slug = role.lower().replace(" ", "_").replace("/", "_")
    name_slug = name.lower().replace(" ", "_")
    uid = hashlib.md5(f"{name}{role}{time.time()}{random.random()}".encode()).hexdigest()[:8]
    return f"{role_slug}_{name_slug}_{uid}.txt"


def get_existing_count(output_dir: Path) -> int:
    return len(list(output_dir.glob("*.txt"))) if output_dir.exists() else 0


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Generate synthetic IT CVs using Groq API")
    parser.add_argument("--count",   type=int, default=TARGET_COUNT, help="Total CVs to generate")
    parser.add_argument("--output",  type=str, default=str(OUTPUT_DIR), help="Output directory")
    parser.add_argument("--model",   type=str, default=GROQ_MODEL,  help="Groq model name")
    parser.add_argument("--workers", type=int, default=MAX_WORKERS, help="Parallel workers")
    parser.add_argument("--resume",  action="store_true", help="Resume — skip existing count")
    parser.add_argument("--min-quality", type=float, default=0.5, help="Min quality_score to keep")
    args = parser.parse_args()

    # Validate API key
    api_key = GROQ_API_KEY
    if not api_key:
        print("ERROR: GROQ_API_KEY / CHAT_GROQ_API_KEY not set.")
        print("  Set it in .env or: export GROQ_API_KEY=gsk_...")
        return

    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    existing = get_existing_count(output_dir)
    remaining = max(0, args.count - existing) if args.resume else args.count

    if remaining == 0:
        print(f"Already have {existing} CVs — target reached!")
        return

    print(f"{'='*60}")
    print(f"Groq CV Generator")
    print(f"  Model   : {args.model}")
    print(f"  Target  : {args.count}  (existing: {existing}, need: {remaining})")
    print(f"  Workers : {args.workers}")
    print(f"  Output  : {output_dir.resolve()}")
    print(f"{'='*60}\n")

    # Build task list
    tasks = []
    for _ in range(remaining):
        role      = random.choice(IT_ROLES)
        level     = random.choice(EXPERIENCE_LEVELS)
        name      = random.choice(VN_NAMES)
        skills    = get_role_skills(role)
        edge_type = random.choices(list(EDGE_TYPES), weights=EDGE_TYPE_WEIGHTS)[0]
        prompt    = build_prompt(role, level, name, skills, edge_type)
        tasks.append((role, level, name, skills, edge_type, prompt))

    client = Groq(api_key=api_key)

    success, failed, skipped = 0, 0, 0
    start_time = time.time()

    def process_task(task):
        role, level, name, skills, edge_type, prompt = task
        time.sleep(DELAY_BETWEEN_REQUESTS)   # gentle rate limiting
        cv_text = generate_cv(client, prompt, args.model)
        if not cv_text or len(cv_text.split()) < 80:
            return False, None, 0.0
        cv_text = clean_cv_text(cv_text)
        q_score = compute_quality_score(cv_text, skills)
        if q_score < args.min_quality:
            return False, None, q_score
        # Add metadata header for traceability
        header = (f"# META role={role} level={level} name={name} "
                  f"edge={edge_type} quality={q_score}\n\n")
        filename = generate_filename(role, name)
        (output_dir / filename).write_text(header + cv_text, encoding="utf-8")
        return True, filename, q_score

    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        futures = {executor.submit(process_task, t): i for i, t in enumerate(tasks)}
        for future in as_completed(futures):
            idx = futures[future]
            try:
                ok, filename, q = future.result()
                if ok:
                    success += 1
                    total   = existing + success
                    elapsed = time.time() - start_time
                    rate    = success / (elapsed / 60) if elapsed > 0 else 0
                    eta_min = (remaining - success - failed) / rate if rate > 0 else 0
                    print(f"  [{total:4d}/{args.count}] ✓ {filename}  "
                          f"q={q:.2f}  {rate:.1f} CV/min  ETA={eta_min:.0f}m")
                else:
                    failed += 1
                    print(f"  [{existing+success:4d}/{args.count}] ✗ task {idx}  q={q:.2f}")
            except Exception as e:
                failed += 1
                print(f"  [EXCEPTION] task {idx}: {e}")

    elapsed = time.time() - start_time
    total   = existing + success
    print(f"\n{'='*60}")
    print(f"Done!")
    print(f"  Generated : {success} new CVs (quality ≥ {args.min_quality})")
    print(f"  Skipped   : {failed}  (low quality or API error)")
    print(f"  Total     : {total}/{args.count}")
    print(f"  Time      : {elapsed/60:.1f} minutes")
    print(f"  Speed     : {success/(elapsed/60):.1f} CVs/min")
    print(f"  Output    : {output_dir.resolve()}")


if __name__ == "__main__":
    main()
