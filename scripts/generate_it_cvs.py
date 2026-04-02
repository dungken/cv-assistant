"""
Task 1.1: Generate 1000 synthetic IT CVs using Ollama (Llama 3.2).
Produces diverse CVs covering multiple IT roles, skill sets, and experience levels.
"""

import os
import json
import time
import random
import hashlib
import argparse
import requests
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

# ─── Configuration ───────────────────────────────────────────────────────────

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
MODEL = os.getenv("OLLAMA_MODEL", "llama3.2:1b")
OUTPUT_DIR = Path("data/raw/synthetic_it")
TARGET_COUNT = 1000
MAX_WORKERS = 2  # Parallel requests to Ollama (keep low for 1b model)

# ─── IT Role Templates ──────────────────────────────────────────────────────

IT_ROLES = [
    "Software Developer",
    "Frontend Developer",
    "Backend Developer",
    "Full Stack Developer",
    "Mobile Developer",
    "DevOps Engineer",
    "Cloud Engineer",
    "Data Engineer",
    "Data Scientist",
    "Machine Learning Engineer",
    "AI Engineer",
    "QA Engineer",
    "Software Tester",
    "Database Administrator",
    "System Administrator",
    "Network Engineer",
    "Information Security Analyst",
    "Cybersecurity Engineer",
    "Penetration Tester",
    "Web Developer",
    "UI/UX Designer",
    "IT Project Manager",
    "Scrum Master",
    "Business Analyst",
    "Solutions Architect",
    "Enterprise Architect",
    "Site Reliability Engineer",
    "Platform Engineer",
    "Embedded Systems Engineer",
    "Blockchain Developer",
    "Game Developer",
    "Technical Lead",
    "Engineering Manager",
    "CTO",
    "Computer Vision Engineer",
    "NLP Engineer",
    "IoT Developer",
    "Firmware Engineer",
    "ERP Consultant",
    "Salesforce Developer",
]

SKILL_POOLS = {
    "programming": [
        "Python", "Java", "JavaScript", "TypeScript", "C#", "C++", "Go", "Rust",
        "Ruby", "PHP", "Kotlin", "Swift", "Scala", "R", "Dart", "Lua",
        "Perl", "Haskell", "Elixir", "Clojure", "MATLAB", "Shell Scripting",
    ],
    "frontend": [
        "React", "Angular", "Vue.js", "Next.js", "Nuxt.js", "Svelte",
        "HTML5", "CSS3", "SASS", "Tailwind CSS", "Bootstrap", "Material UI",
        "Redux", "Vuex", "Webpack", "Vite", "jQuery", "D3.js",
    ],
    "backend": [
        "Node.js", "Django", "Flask", "FastAPI", "Spring Boot", "ASP.NET Core",
        "Express.js", "NestJS", "Ruby on Rails", "Laravel", "Gin", "Fiber",
        "GraphQL", "gRPC", "REST API", "Microservices",
    ],
    "database": [
        "PostgreSQL", "MySQL", "MongoDB", "Redis", "Elasticsearch", "Cassandra",
        "Oracle", "SQL Server", "DynamoDB", "Firebase", "Neo4j", "InfluxDB",
        "SQLite", "CouchDB", "MariaDB", "Supabase",
    ],
    "devops": [
        "Docker", "Kubernetes", "Jenkins", "GitHub Actions", "GitLab CI/CD",
        "Terraform", "Ansible", "AWS", "Azure", "GCP", "Prometheus", "Grafana",
        "Nginx", "Apache", "Linux", "Helm", "ArgoCD", "Datadog",
    ],
    "data_ml": [
        "TensorFlow", "PyTorch", "Scikit-learn", "Pandas", "NumPy", "Spark",
        "Hadoop", "Airflow", "Kafka", "Flink", "Tableau", "Power BI",
        "MLflow", "Kubeflow", "OpenCV", "Hugging Face", "LangChain",
    ],
    "tools": [
        "Git", "Jira", "Confluence", "Slack", "VS Code", "IntelliJ IDEA",
        "Postman", "Swagger", "Figma", "Notion", "Trello", "Bitbucket",
    ],
    "security": [
        "OWASP", "Burp Suite", "Metasploit", "Wireshark", "Nmap", "Nessus",
        "SIEM", "IDS/IPS", "PKI", "OAuth 2.0", "JWT", "SAML", "SSL/TLS",
    ],
}

VN_COMPANIES = [
    "FPT Software", "Viettel Solutions", "VNG Corporation", "Tiki",
    "Shopee Vietnam", "MoMo", "VNPay", "KMS Technology", "TMA Solutions",
    "NashTech", "Axon Active", "Ến Global", "CMC Corporation", "VNPT IT",
    "Sendo", "ZaloPay", "Grab Vietnam", "One Mount Group", "Yeah1 Group",
    "Samsung Vietnam R&D", "LG Development Center Vietnam", "Bosch Vietnam",
    "Fujitsu Vietnam", "Rikkeisoft", "Sun Asterisk", "CO-WELL Asia",
    "Savvycom", "Designveloper", "Niteco Vietnam", "NFQ Asia",
    "TechVify Software", "Orient Software", "Ến Data", "Golden Owl Consulting",
    "Supremetech", "Enlab Software", "Amanotes", "Gameloft Vietnam",
    "Unity Vietnam", "Sky Mavis",
]

VN_UNIVERSITIES = [
    "Vietnam National University (VNU)", "University of Technology (HCMUT)",
    "University of Information Technology (UIT)", "Posts and Telecommunications Institute (PTIT)",
    "Hanoi University of Science and Technology (HUST)", "FPT University",
    "Ton Duc Thang University", "Can Tho University", "University of Science (HCMUS)",
    "Da Nang University of Science and Technology", "Le Quy Don Technical University",
    "Ho Chi Minh City University of Technology (HUTECH)",
    "University of Economics Ho Chi Minh City (UEH)",
    "Hanoi University", "University of Transport and Communications (UTC)",
    "Academy of Cryptography Techniques", "Military Technical Academy",
    "Vietnam-Korea University of Information and Communication Technology",
    "Thai Nguyen University of Information and Communication Technology",
    "Lac Hong University",
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
]

CERTIFICATIONS = [
    "AWS Certified Solutions Architect", "AWS Certified Developer",
    "Azure Administrator Associate", "Azure Solutions Architect",
    "Google Cloud Professional Cloud Architect", "Google Cloud Professional Data Engineer",
    "Certified Kubernetes Administrator (CKA)", "Docker Certified Associate",
    "Certified Scrum Master (CSM)", "PMP (Project Management Professional)",
    "CompTIA Security+", "CISSP", "CEH (Certified Ethical Hacker)",
    "CCNA (Cisco Certified Network Associate)", "Oracle Certified Professional",
    "Red Hat Certified System Administrator (RHCSA)", "Terraform Associate",
    "MongoDB Certified Developer", "Apache Kafka Certification",
    "TensorFlow Developer Certificate", "ISTQB Certified Tester",
    "TOGAF Certified", "ITIL Foundation", "Agile Certified Practitioner (PMI-ACP)",
]

EXPERIENCE_LEVELS = ["junior", "mid", "senior", "lead", "principal"]


def get_role_skills(role: str) -> list[str]:
    """Select relevant skill categories based on role."""
    role_lower = role.lower()
    skills = list(SKILL_POOLS["tools"])

    if any(k in role_lower for k in ["frontend", "ui", "ux", "web"]):
        skills += random.sample(SKILL_POOLS["frontend"], min(6, len(SKILL_POOLS["frontend"])))
        skills += random.sample(SKILL_POOLS["programming"], 3)
    elif any(k in role_lower for k in ["backend", "api"]):
        skills += random.sample(SKILL_POOLS["backend"], min(5, len(SKILL_POOLS["backend"])))
        skills += random.sample(SKILL_POOLS["database"], 3)
        skills += random.sample(SKILL_POOLS["programming"], 4)
    elif any(k in role_lower for k in ["full stack"]):
        skills += random.sample(SKILL_POOLS["frontend"], 4)
        skills += random.sample(SKILL_POOLS["backend"], 4)
        skills += random.sample(SKILL_POOLS["database"], 3)
        skills += random.sample(SKILL_POOLS["programming"], 4)
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
    elif any(k in role_lower for k in ["mobile"]):
        skills += random.sample(SKILL_POOLS["programming"], 3)
        skills += ["React Native", "Flutter", "Swift", "Kotlin"]
        skills += random.sample(SKILL_POOLS["backend"], 2)
    elif any(k in role_lower for k in ["database", "dba"]):
        skills += random.sample(SKILL_POOLS["database"], min(6, len(SKILL_POOLS["database"])))
        skills += random.sample(SKILL_POOLS["programming"], 2)
    elif any(k in role_lower for k in ["game"]):
        skills += ["Unity", "Unreal Engine", "C#", "C++", "OpenGL", "DirectX"]
        skills += random.sample(SKILL_POOLS["programming"], 2)
    else:
        # Generic software/IT role
        skills += random.sample(SKILL_POOLS["programming"], 4)
        skills += random.sample(SKILL_POOLS["backend"], 3)
        skills += random.sample(SKILL_POOLS["database"], 2)
        skills += random.sample(SKILL_POOLS["devops"], 2)

    return list(set(skills))


def build_prompt(role: str, level: str, name: str, skills: list[str]) -> str:
    """Build a prompt for Ollama to generate a realistic IT CV."""
    years_map = {
        "junior": "1-2", "mid": "3-5", "senior": "5-8",
        "lead": "8-12", "principal": "10-15"
    }
    years = years_map[level]
    company_sample = random.sample(VN_COMPANIES, min(3, len(VN_COMPANIES)))
    uni = random.choice(VN_UNIVERSITIES)
    cert_sample = random.sample(CERTIFICATIONS, random.randint(0, 3))
    skill_str = ", ".join(random.sample(skills, min(12, len(skills))))

    prompt = f"""Generate a realistic IT professional CV/resume in plain text format for:

Name: {name}
Role: {level.capitalize()} {role}
Years of experience: {years} years
Location: Vietnam
Skills: {skill_str}
Companies worked at: {', '.join(company_sample)}
University: {uni}
Certifications: {', '.join(cert_sample) if cert_sample else 'None'}

Format the CV with these sections (use plain text, no markdown):
1. Full name and contact info (email, phone, location)
2. Professional Summary (2-3 sentences)
3. Experience (2-3 positions with company name, dates, and bullet points of achievements)
4. Education (degree, university, year)
5. Technical Skills (list of technologies)
6. Certifications (if any)

Important rules:
- Use realistic Vietnamese company names and dates
- Include specific technical achievements with metrics where possible
- Keep it to about 300-500 words
- Write in English
- Do NOT use markdown formatting, asterisks, or special symbols
- Use plain dashes (-) for bullet points"""

    return prompt


def generate_cv(ollama_url: str, model: str, prompt: str, timeout: int = 120) -> str | None:
    """Call Ollama API to generate a CV."""
    try:
        resp = requests.post(
            f"{ollama_url}/api/generate",
            json={
                "model": model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.8,
                    "top_p": 0.9,
                    "num_predict": 1024,
                }
            },
            timeout=timeout,
        )
        resp.raise_for_status()
        return resp.json().get("response", "").strip()
    except Exception as e:
        print(f"  [ERROR] Ollama call failed: {e}")
        return None


def clean_cv_text(text: str) -> str:
    """Clean up generated CV text - remove markdown artifacts."""
    import re
    # Remove markdown bold/italic
    text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)
    text = re.sub(r'\*([^*]+)\*', r'\1', text)
    # Remove markdown headers
    text = re.sub(r'^#{1,3}\s+', '', text, flags=re.MULTILINE)
    # Clean up excessive whitespace
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()


def get_existing_count(output_dir: Path) -> int:
    """Count existing CV files."""
    if not output_dir.exists():
        return 0
    return len(list(output_dir.glob("*.txt")))


def generate_filename(role: str, name: str) -> str:
    """Generate a unique filename for a CV."""
    role_slug = role.lower().replace(" ", "_").replace("/", "_")
    name_slug = name.lower().replace(" ", "_")
    uid = hashlib.md5(f"{name}{role}{time.time()}{random.random()}".encode()).hexdigest()[:8]
    return f"{role_slug}_{name_slug}_{uid}.txt"


def main():
    parser = argparse.ArgumentParser(description="Generate synthetic IT CVs using Ollama")
    parser.add_argument("--count", type=int, default=TARGET_COUNT, help="Number of CVs to generate")
    parser.add_argument("--output", type=str, default=str(OUTPUT_DIR), help="Output directory")
    parser.add_argument("--model", type=str, default=MODEL, help="Ollama model name")
    parser.add_argument("--workers", type=int, default=MAX_WORKERS, help="Parallel workers")
    parser.add_argument("--resume", action="store_true", help="Resume from existing files")
    args = parser.parse_args()

    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    existing = get_existing_count(output_dir)
    if args.resume and existing > 0:
        remaining = max(0, args.count - existing)
        print(f"Found {existing} existing CVs. Need {remaining} more.")
    else:
        remaining = args.count

    if remaining == 0:
        print(f"Already have {existing} CVs. Target of {args.count} reached!")
        return

    # Verify Ollama is reachable
    try:
        resp = requests.get(f"{OLLAMA_URL}/api/tags", timeout=5)
        resp.raise_for_status()
        models = [m["name"] for m in resp.json().get("models", [])]
        if args.model not in models:
            print(f"WARNING: Model '{args.model}' not found. Available: {models}")
            return
        print(f"Ollama OK. Using model: {args.model}")
    except Exception as e:
        print(f"ERROR: Cannot connect to Ollama at {OLLAMA_URL}: {e}")
        return

    # Build generation tasks
    tasks = []
    for i in range(remaining):
        role = random.choice(IT_ROLES)
        level = random.choice(EXPERIENCE_LEVELS)
        name = random.choice(VN_NAMES)
        skills = get_role_skills(role)
        prompt = build_prompt(role, level, name, skills)
        tasks.append((role, level, name, prompt))

    print(f"\nGenerating {remaining} CVs with {args.workers} workers...")
    print(f"Output: {output_dir.resolve()}\n")

    success = 0
    failed = 0
    start_time = time.time()

    def process_task(idx, task):
        role, level, name, prompt = task
        cv_text = generate_cv(OLLAMA_URL, args.model, prompt)
        if cv_text and len(cv_text) > 100:
            cv_text = clean_cv_text(cv_text)
            filename = generate_filename(role, name)
            filepath = output_dir / filename
            filepath.write_text(cv_text, encoding="utf-8")
            return True, filename
        return False, None

    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        futures = {
            executor.submit(process_task, i, task): i
            for i, task in enumerate(tasks)
        }
        for future in as_completed(futures):
            idx = futures[future]
            try:
                ok, filename = future.result()
                if ok:
                    success += 1
                    total = existing + success
                    elapsed = time.time() - start_time
                    rate = success / elapsed if elapsed > 0 else 0
                    eta = (remaining - success - failed) / rate if rate > 0 else 0
                    print(
                        f"  [{total}/{args.count}] Generated: {filename} "
                        f"({rate:.1f} CVs/min, ETA: {eta/60:.0f}min)"
                    )
                else:
                    failed += 1
                    print(f"  [{existing + success}/{args.count}] FAILED (attempt {idx + 1})")
            except Exception as e:
                failed += 1
                print(f"  [ERROR] Task {idx}: {e}")

    elapsed = time.time() - start_time
    total = existing + success
    print(f"\n{'='*60}")
    print(f"Generation complete!")
    print(f"  Generated: {success} new CVs")
    print(f"  Failed:    {failed}")
    print(f"  Total:     {total}/{args.count}")
    print(f"  Time:      {elapsed/60:.1f} minutes")
    print(f"  Output:    {output_dir.resolve()}")


if __name__ == "__main__":
    main()
