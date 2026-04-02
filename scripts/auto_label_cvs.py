"""
Task 1.2: Auto-labeling script for synthetic IT CVs.
Uses O*NET skills dictionary + rule-based patterns to create BIO-tagged training data.

Output: JSONL files compatible with HuggingFace datasets for NER training.
Each line: {"tokens": [...], "ner_tags": [...]}
"""

import os
import re
import json
import argparse
from pathlib import Path
from typing import Optional


# ─── Configuration ───────────────────────────────────────────────────────────

INPUT_DIR = Path("data/raw/synthetic_it")
OUTPUT_DIR = Path("data/processed/annotated_hf")
ONET_DIR = Path("knowledge_base/onet/db_28_1_text")

LABEL_LIST = [
    "O", "B-PER", "I-PER", "B-ORG", "I-ORG", "B-DATE", "I-DATE",
    "B-LOC", "I-LOC", "B-SKILL", "I-SKILL", "B-DEGREE", "I-DEGREE",
    "B-MAJOR", "I-MAJOR", "B-JOB_TITLE", "I-JOB_TITLE", "B-PROJECT",
    "I-PROJECT", "B-CERT", "I-CERT"
]


# ─── Knowledge Base Loaders ─────────────────────────────────────────────────

def load_onet_skills(onet_dir: Path) -> set[str]:
    """Load IT-relevant technology skills from O*NET."""
    skills = set()

    # Load from Technology Skills file
    tech_skills_file = onet_dir / "Technology Skills.txt"
    if tech_skills_file.exists():
        with open(tech_skills_file, "r", encoding="utf-8") as f:
            for line in f:
                parts = line.strip().split("\t")
                if len(parts) >= 2 and not line.startswith("O*NET"):
                    skill_name = parts[1].strip()
                    if len(skill_name) > 1:
                        skills.add(skill_name)

    # Load custom IT skills dictionary
    it_dict_file = onet_dir / "it_skills_dict.txt"
    if it_dict_file.exists():
        with open(it_dict_file, "r", encoding="utf-8") as f:
            for line in f:
                skill = line.strip()
                if skill and len(skill) > 1:
                    skills.add(skill)

    return skills


def build_skill_lookup() -> set[str]:
    """Build comprehensive IT skills set from O*NET + curated list."""
    skills = set()

    # Load O*NET skills
    onet_skills = load_onet_skills(ONET_DIR)
    skills.update(onet_skills)

    # Add curated IT skills (common ones that might not be in O*NET)
    curated = [
        # Programming Languages
        "Python", "Java", "JavaScript", "TypeScript", "C#", "C++", "C",
        "Go", "Golang", "Rust", "Ruby", "PHP", "Kotlin", "Swift", "Scala",
        "R", "Dart", "Lua", "Perl", "Haskell", "Elixir", "Clojure",
        "MATLAB", "Shell", "Bash", "PowerShell", "SQL", "NoSQL",
        # Frontend
        "React", "React.js", "ReactJS", "Angular", "AngularJS", "Vue.js",
        "Vue", "VueJS", "Next.js", "NextJS", "Nuxt.js", "Svelte",
        "HTML", "HTML5", "CSS", "CSS3", "SASS", "SCSS", "Less",
        "Tailwind CSS", "Tailwind", "Bootstrap", "Material UI", "MUI",
        "Redux", "Vuex", "Pinia", "Webpack", "Vite", "Babel",
        "jQuery", "D3.js", "Three.js", "Gatsby", "Remix",
        # Backend
        "Node.js", "NodeJS", "Django", "Flask", "FastAPI", "Spring Boot",
        "Spring", "ASP.NET", "ASP.NET Core", ".NET", ".NET Core",
        "Express.js", "Express", "NestJS", "Ruby on Rails", "Rails",
        "Laravel", "Gin", "Fiber", "Echo", "Actix", "Rocket",
        "GraphQL", "gRPC", "REST", "REST API", "RESTful",
        "Microservices", "WebSocket", "RabbitMQ", "ActiveMQ",
        # Databases
        "PostgreSQL", "Postgres", "MySQL", "MongoDB", "Redis",
        "Elasticsearch", "Cassandra", "Oracle", "SQL Server", "MSSQL",
        "DynamoDB", "Firebase", "Firestore", "Neo4j", "InfluxDB",
        "SQLite", "CouchDB", "MariaDB", "Supabase", "Couchbase",
        "Memcached", "Amazon RDS", "Cloud SQL",
        # DevOps / Cloud
        "Docker", "Kubernetes", "K8s", "Jenkins", "GitHub Actions",
        "GitLab CI/CD", "GitLab CI", "CircleCI", "Travis CI",
        "Terraform", "Ansible", "Puppet", "Chef",
        "AWS", "Amazon Web Services", "Azure", "Microsoft Azure",
        "GCP", "Google Cloud", "Google Cloud Platform",
        "Prometheus", "Grafana", "Datadog", "New Relic", "ELK Stack",
        "Nginx", "Apache", "Linux", "Ubuntu", "CentOS", "RHEL",
        "Helm", "ArgoCD", "Istio", "Envoy", "Consul",
        "CloudFormation", "Pulumi", "Vagrant",
        # Data / ML
        "TensorFlow", "PyTorch", "Scikit-learn", "Sklearn",
        "Pandas", "NumPy", "Scipy", "Matplotlib",
        "Spark", "Apache Spark", "PySpark", "Hadoop", "MapReduce",
        "Airflow", "Apache Airflow", "Kafka", "Apache Kafka",
        "Flink", "Apache Flink", "Beam", "Apache Beam",
        "Tableau", "Power BI", "Looker", "Metabase",
        "MLflow", "Kubeflow", "SageMaker", "Vertex AI",
        "OpenCV", "Hugging Face", "HuggingFace", "LangChain",
        "BERT", "GPT", "Transformers", "NLTK", "spaCy",
        "Keras", "XGBoost", "LightGBM", "CatBoost",
        "dbt", "Snowflake", "BigQuery", "Redshift", "Databricks",
        # Mobile
        "React Native", "Flutter", "SwiftUI", "Jetpack Compose",
        "Android", "iOS", "Xamarin", "Ionic", "Cordova",
        # Tools
        "Git", "GitHub", "GitLab", "Bitbucket", "SVN",
        "Jira", "Confluence", "Slack", "Notion", "Trello",
        "VS Code", "Visual Studio Code", "IntelliJ IDEA", "IntelliJ",
        "PyCharm", "WebStorm", "Eclipse", "Vim", "Neovim",
        "Postman", "Swagger", "OpenAPI", "Figma", "Sketch",
        "SonarQube", "ESLint", "Prettier", "Black",
        # Security
        "OWASP", "Burp Suite", "Metasploit", "Wireshark", "Nmap",
        "Nessus", "Qualys", "Snort", "Splunk",
        "OAuth", "OAuth 2.0", "JWT", "SAML", "OpenID Connect",
        "SSL", "TLS", "SSL/TLS", "PKI", "IAM",
        # Methodologies
        "Agile", "Scrum", "Kanban", "SAFe", "Lean",
        "CI/CD", "TDD", "BDD", "DDD",
        "Design Patterns", "SOLID", "Clean Architecture",
        "DevOps", "SRE", "GitOps", "Infrastructure as Code",
        # Testing
        "Selenium", "Cypress", "Playwright", "Jest", "Mocha",
        "JUnit", "pytest", "TestNG", "Appium",
        "Load Testing", "JMeter", "Gatling", "k6",
        # Game / Embedded
        "Unity", "Unreal Engine", "Godot", "OpenGL", "DirectX", "Vulkan",
        "Arduino", "Raspberry Pi", "RTOS", "FreeRTOS",
        # Blockchain
        "Solidity", "Ethereum", "Web3", "Web3.js", "Hardhat", "Truffle",
        # Other
        "ERP", "SAP", "Salesforce", "ServiceNow", "Dynamics 365",
        "Power Automate", "Power Apps", "SharePoint",
    ]
    skills.update(curated)

    return skills


# ─── Pattern Matchers ────────────────────────────────────────────────────────

# Vietnamese and international location patterns
LOCATIONS = [
    "Ho Chi Minh City", "Ho Chi Minh", "HCMC", "HCM", "Hanoi", "Ha Noi",
    "Da Nang", "Danang", "Can Tho", "Hai Phong", "Hue", "Nha Trang",
    "Bien Hoa", "Vung Tau", "Binh Duong", "Dong Nai", "Long An",
    "Vietnam", "Viet Nam", "Singapore", "Japan", "Korea", "Thailand",
    "District 1", "District 2", "District 3", "District 7", "District 9",
    "Thu Duc", "Binh Thanh", "Go Vap", "Tan Binh", "Phu Nhuan",
    "Cau Giay", "Dong Da", "Hai Ba Trung", "Hoang Mai", "Thanh Xuan",
]

# Degree patterns
DEGREES = [
    "Bachelor of Science", "Bachelor of Engineering", "Bachelor of Arts",
    "Master of Science", "Master of Engineering", "Master of Business Administration",
    "Doctor of Philosophy", "Ph.D.", "PhD", "MBA",
    "B.Sc.", "B.Eng.", "M.Sc.", "M.Eng.", "B.S.", "M.S.",
    "Bachelor", "Master", "Associate Degree",
    "Kỹ sư", "Cử nhân", "Thạc sĩ", "Tiến sĩ",
]

# Major/field of study
MAJORS = [
    "Computer Science", "Software Engineering", "Information Technology",
    "Information Systems", "Computer Engineering", "Data Science",
    "Artificial Intelligence", "Cybersecurity", "Network Engineering",
    "Electrical Engineering", "Electronics Engineering",
    "Mathematics", "Applied Mathematics", "Statistics",
    "Khoa học Máy tính", "Công nghệ Thông tin", "Kỹ thuật Phần mềm",
]

# IT Job titles
JOB_TITLES = [
    "Software Developer", "Software Engineer", "Senior Software Engineer",
    "Junior Software Developer", "Lead Software Engineer", "Principal Engineer",
    "Frontend Developer", "Frontend Engineer", "Backend Developer",
    "Backend Engineer", "Full Stack Developer", "Full Stack Engineer",
    "DevOps Engineer", "Senior DevOps Engineer", "Cloud Engineer",
    "Cloud Architect", "Solutions Architect", "Enterprise Architect",
    "Data Engineer", "Senior Data Engineer", "Data Scientist",
    "Senior Data Scientist", "Machine Learning Engineer", "ML Engineer",
    "AI Engineer", "AI Researcher", "NLP Engineer",
    "QA Engineer", "QA Lead", "Test Engineer", "SDET",
    "Software Tester", "Automation Tester", "Manual Tester",
    "Database Administrator", "DBA", "System Administrator",
    "Systems Engineer", "Network Engineer", "Network Administrator",
    "Security Analyst", "Security Engineer", "Cybersecurity Analyst",
    "Penetration Tester", "SOC Analyst",
    "Web Developer", "UI Developer", "UX Designer", "UI/UX Designer",
    "Mobile Developer", "iOS Developer", "Android Developer",
    "IT Project Manager", "Project Manager", "Technical Project Manager",
    "Scrum Master", "Agile Coach", "Product Owner",
    "Business Analyst", "IT Business Analyst", "Systems Analyst",
    "Technical Lead", "Tech Lead", "Team Lead",
    "Engineering Manager", "VP of Engineering", "CTO",
    "Chief Technology Officer", "IT Manager", "IT Director",
    "Site Reliability Engineer", "SRE", "Platform Engineer",
    "Embedded Systems Engineer", "Firmware Engineer",
    "Blockchain Developer", "Smart Contract Developer",
    "Game Developer", "Game Programmer", "Game Designer",
    "Computer Vision Engineer", "Robotics Engineer",
    "ERP Consultant", "SAP Consultant", "Salesforce Developer",
    "Technical Writer", "Developer Advocate",
    "Intern", "Software Intern", "IT Intern",
]

# Vietnamese company names
VN_COMPANIES = [
    "FPT Software", "FPT Information System", "FPT Telecom",
    "Viettel", "Viettel Solutions", "Viettel Cyber Security",
    "VNG Corporation", "VNG", "Zalo", "ZaloPay",
    "Tiki", "Tiki Corporation",
    "Shopee", "Shopee Vietnam",
    "MoMo", "M_Service",
    "VNPay", "VNPT", "VNPT IT",
    "KMS Technology", "KMS Solutions", "KMS Software Solutions",
    "TMA Solutions", "TMA Technology",
    "NashTech", "NashTech Vietnam",
    "Axon Active", "Axon Active Vietnam",
    "CMC Corporation", "CMC Global", "CMC Telecom",
    "Sendo", "Sendo Technology",
    "Grab Vietnam", "Grab",
    "One Mount Group",
    "Samsung Vietnam", "Samsung Vietnam R&D", "Samsung SDS Vietnam",
    "LG Development Center Vietnam", "LG CNS Vietnam",
    "Bosch Vietnam", "Robert Bosch Engineering",
    "Fujitsu Vietnam",
    "Rikkeisoft", "Rikkei Soft",
    "Sun Asterisk", "Sun*",
    "CO-WELL Asia",
    "Savvycom",
    "Designveloper",
    "Niteco Vietnam",
    "NFQ Asia",
    "TechVify Software",
    "Orient Software",
    "Golden Owl Consulting",
    "Supremetech",
    "Enlab Software",
    "Amanotes",
    "Gameloft Vietnam", "Gameloft",
    "Unity Vietnam",
    "Sky Mavis",
    "KardiaChain",
    "Ến Global",
    "Yeah1 Group",
    "Masan Group",
    "Techcombank", "VPBank", "MB Bank",
    "Vingroup", "VinAI", "VinBigData",
    "Vietcombank", "BIDV", "Agribank",
    "ACB", "Sacombank", "TPBank",
    "Google", "Microsoft", "Amazon", "Meta", "Apple",
    "IBM", "Oracle", "SAP", "Accenture", "Deloitte",
]

# Vietnamese university names
VN_UNIVERSITIES = [
    "Vietnam National University", "VNU",
    "University of Technology", "HCMUT", "Bach Khoa University",
    "University of Information Technology", "UIT",
    "Posts and Telecommunications Institute", "PTIT",
    "Hanoi University of Science and Technology", "HUST",
    "FPT University",
    "Ton Duc Thang University", "TDTU",
    "Can Tho University", "CTU",
    "University of Science", "HCMUS",
    "Da Nang University of Science and Technology", "DUT",
    "Le Quy Don Technical University",
    "Ho Chi Minh City University of Technology", "HUTECH",
    "University of Economics Ho Chi Minh City", "UEH",
    "Hanoi University",
    "University of Transport and Communications", "UTC",
    "Academy of Cryptography Techniques",
    "Military Technical Academy", "MTA",
    "Lac Hong University",
    "Thai Nguyen University",
    "RMIT University", "RMIT Vietnam",
    "Phenikaa University",
    "Vietnam-Korea University",
]

# Certification patterns
CERTIFICATIONS = [
    "AWS Certified Solutions Architect",
    "AWS Certified Developer",
    "AWS Certified Cloud Practitioner",
    "AWS Certified DevOps Engineer",
    "AWS Certified SysOps Administrator",
    "Azure Administrator Associate",
    "Azure Solutions Architect",
    "Azure Developer Associate",
    "Azure DevOps Engineer Expert",
    "Google Cloud Professional Cloud Architect",
    "Google Cloud Professional Data Engineer",
    "Google Cloud Associate Cloud Engineer",
    "Certified Kubernetes Administrator",
    "CKA",
    "Certified Kubernetes Application Developer",
    "CKAD",
    "Docker Certified Associate",
    "Certified Scrum Master",
    "CSM",
    "PMP",
    "Project Management Professional",
    "CompTIA Security+",
    "CompTIA Network+",
    "CompTIA A+",
    "CISSP",
    "CEH",
    "Certified Ethical Hacker",
    "CCNA",
    "Cisco Certified Network Associate",
    "CCNP",
    "Oracle Certified Professional",
    "OCP",
    "Red Hat Certified System Administrator",
    "RHCSA",
    "Red Hat Certified Engineer",
    "RHCE",
    "Terraform Associate",
    "HashiCorp Certified Terraform Associate",
    "MongoDB Certified Developer",
    "Apache Kafka Certification",
    "TensorFlow Developer Certificate",
    "ISTQB Certified Tester",
    "ISTQB Foundation Level",
    "TOGAF Certified",
    "ITIL Foundation",
    "ITIL 4 Foundation",
    "Agile Certified Practitioner",
    "PMI-ACP",
    "Professional Scrum Master",
    "PSM I",
    "PSM II",
    "Certified Information Security Manager",
    "CISM",
    "Certified ScrumMaster",
    "SAFe Agilist",
    "SAFe Practitioner",
    "IELTS", "TOEIC", "TOEFL",
]


# ─── Date Patterns ───────────────────────────────────────────────────────────

DATE_PATTERNS = [
    # Year ranges: 2018 - 2020, 2018-2020, 2018 – 2020
    r'\b((?:19|20)\d{2})\s*[-–—]\s*((?:19|20)\d{2}|[Pp]resent|[Cc]urrent|[Nn]ow)\b',
    # Month/Year: January 2020, Jan 2020, 01/2020
    r'\b((?:January|February|March|April|May|June|July|August|September|October|November|December|'
    r'Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\.?\s+(?:19|20)\d{2})\b',
    r'\b(\d{1,2}/(?:19|20)\d{2})\b',
    # Standalone year in context
    r'\((\d{4})\)',
]


# ─── Tokenizer ───────────────────────────────────────────────────────────────

def tokenize(text: str) -> list[dict]:
    """Tokenize text preserving offsets."""
    tokens = []
    for match in re.finditer(r'\S+', text):
        tokens.append({
            "text": match.group(),
            "start": match.start(),
            "end": match.end(),
        })
    return tokens


# ─── Entity Annotation Engine ────────────────────────────────────────────────

class CVAnnotator:
    def __init__(self, skills: set[str]):
        self.skills = skills
        # Build sorted lists for efficient matching (longest first)
        self.skill_list = sorted(skills, key=len, reverse=True)
        self.job_title_list = sorted(JOB_TITLES, key=len, reverse=True)
        self.org_list = sorted(VN_COMPANIES, key=len, reverse=True)
        self.uni_list = sorted(VN_UNIVERSITIES, key=len, reverse=True)
        self.loc_list = sorted(LOCATIONS, key=len, reverse=True)
        self.degree_list = sorted(DEGREES, key=len, reverse=True)
        self.major_list = sorted(MAJORS, key=len, reverse=True)
        self.cert_list = sorted(CERTIFICATIONS, key=len, reverse=True)

    def find_spans(self, text: str) -> list[tuple[int, int, str]]:
        """Find all entity spans in text. Returns (start, end, label)."""
        spans = []

        # Helper: case-insensitive phrase search
        def find_phrases(text: str, phrases: list[str], label: str):
            text_lower = text.lower()
            for phrase in phrases:
                phrase_lower = phrase.lower()
                start = 0
                while True:
                    idx = text_lower.find(phrase_lower, start)
                    if idx == -1:
                        break
                    end = idx + len(phrase)
                    # Word boundary check
                    if (idx == 0 or not text[idx - 1].isalnum()) and \
                       (end == len(text) or not text[end].isalnum()):
                        spans.append((idx, end, label))
                    start = idx + 1

        # 1. Skills (highest priority for IT CVs)
        find_phrases(text, self.skill_list, "SKILL")

        # 2. Job titles
        find_phrases(text, self.job_title_list, "JOB_TITLE")

        # 3. Organizations
        find_phrases(text, self.org_list, "ORG")

        # 4. Universities (also ORG in some schemes, but we tag as ORG)
        for uni in self.uni_list:
            uni_lower = uni.lower()
            text_lower = text.lower()
            idx = 0
            while True:
                pos = text_lower.find(uni_lower, idx)
                if pos == -1:
                    break
                end = pos + len(uni)
                if (pos == 0 or not text[pos - 1].isalnum()) and \
                   (end == len(text) or not text[end].isalnum()):
                    spans.append((pos, end, "ORG"))
                idx = pos + 1

        # 5. Locations
        find_phrases(text, self.loc_list, "LOC")

        # 6. Degrees
        find_phrases(text, self.degree_list, "DEGREE")

        # 7. Majors
        find_phrases(text, self.major_list, "MAJOR")

        # 8. Certifications
        find_phrases(text, self.cert_list, "CERT")

        # 9. Dates (regex-based)
        for pattern in DATE_PATTERNS:
            for m in re.finditer(pattern, text):
                spans.append((m.start(), m.end(), "DATE"))

        # 10. Person names - first line heuristic (CV name is usually first line)
        lines = text.strip().split("\n")
        if lines:
            first_line = lines[0].strip()
            # If first line looks like a name (2-4 words, no special chars)
            if re.match(r'^[A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,3}$', first_line):
                spans.append((0, len(first_line), "PER"))

        # Remove overlapping spans (prefer longer spans)
        return self._resolve_overlaps(spans)

    def _resolve_overlaps(self, spans: list[tuple[int, int, str]]) -> list[tuple[int, int, str]]:
        """Remove overlapping spans, preferring longer ones."""
        if not spans:
            return []

        # Sort by length (descending), then by start position
        spans.sort(key=lambda s: (-(s[1] - s[0]), s[0]))
        result = []
        occupied = set()

        for start, end, label in spans:
            char_range = set(range(start, end))
            if not char_range & occupied:
                result.append((start, end, label))
                occupied |= char_range

        result.sort(key=lambda s: s[0])
        return result

    def annotate(self, text: str) -> dict:
        """Annotate a CV text and return tokens + BIO tags."""
        tokens_info = tokenize(text)
        tokens = [t["text"] for t in tokens_info]
        tags = ["O"] * len(tokens_info)

        # Find entity spans
        spans = self.find_spans(text)

        # Map spans to tokens
        for span_start, span_end, label in spans:
            first_token = True
            for i, t in enumerate(tokens_info):
                # Token overlaps with span
                if t["start"] < span_end and t["end"] > span_start:
                    if tags[i] == "O":  # Don't overwrite existing tags
                        if first_token:
                            tags[i] = f"B-{label}"
                            first_token = False
                        else:
                            tags[i] = f"I-{label}"

        return {"tokens": tokens, "ner_tags": tags}


# ─── Main Pipeline ───────────────────────────────────────────────────────────

def process_cv_file(filepath: Path, annotator: CVAnnotator) -> Optional[dict]:
    """Process a single CV file and return annotated data."""
    try:
        text = filepath.read_text(encoding="utf-8").strip()
        if not text or len(text) < 50:
            return None

        result = annotator.annotate(text)

        # Quality check: must have at least some non-O tags
        non_o_count = sum(1 for t in result["ner_tags"] if t != "O")
        if non_o_count < 3:
            return None

        result["id"] = filepath.stem
        return result
    except Exception as e:
        print(f"  [ERROR] Processing {filepath.name}: {e}")
        return None


def print_annotation_stats(dataset: list[dict]):
    """Print statistics about the annotated dataset."""
    from collections import Counter
    tag_counts = Counter()
    for item in dataset:
        for tag in item["ner_tags"]:
            tag_counts[tag] += 1

    total = sum(tag_counts.values())
    print(f"\n{'='*50}")
    print(f"Annotation Statistics")
    print(f"{'='*50}")
    print(f"Total samples: {len(dataset)}")
    print(f"Total tokens:  {total}")
    print(f"\nEntity distribution:")
    for tag, count in sorted(tag_counts.items(), key=lambda x: -x[1]):
        if tag != "O":
            pct = count / total * 100
            print(f"  {tag:15s}: {count:6d} ({pct:.2f}%)")
    print(f"  {'O':15s}: {tag_counts['O']:6d} ({tag_counts['O']/total*100:.2f}%)")


def main():
    parser = argparse.ArgumentParser(description="Auto-label synthetic IT CVs with BIO tags")
    parser.add_argument("--input", type=str, default=str(INPUT_DIR), help="Input directory with CV .txt files")
    parser.add_argument("--output", type=str, default=str(OUTPUT_DIR), help="Output directory for JSONL files")
    parser.add_argument("--output-file", type=str, default="synthetic_it.jsonl", help="Output filename")
    parser.add_argument("--sample", type=int, default=0, help="Process only N files (0=all)")
    parser.add_argument("--show-examples", type=int, default=3, help="Show N annotated examples")
    args = parser.parse_args()

    input_dir = Path(args.input)
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    if not input_dir.exists():
        print(f"ERROR: Input directory not found: {input_dir}")
        return

    # Load skills dictionary
    print("Loading O*NET skills dictionary...")
    skills = build_skill_lookup()
    print(f"  Loaded {len(skills)} skills")

    # Initialize annotator
    annotator = CVAnnotator(skills)

    # Find CV files
    cv_files = sorted(input_dir.glob("*.txt"))
    if args.sample > 0:
        cv_files = cv_files[:args.sample]

    print(f"\nProcessing {len(cv_files)} CV files from {input_dir}...")

    dataset = []
    for i, filepath in enumerate(cv_files):
        result = process_cv_file(filepath, annotator)
        if result:
            dataset.append(result)
        if (i + 1) % 100 == 0:
            print(f"  Processed {i + 1}/{len(cv_files)} files ({len(dataset)} valid)")

    if not dataset:
        print("ERROR: No valid annotated samples produced.")
        return

    # Show examples
    if args.show_examples > 0:
        print(f"\n{'='*50}")
        print(f"Example Annotations (first {args.show_examples}):")
        print(f"{'='*50}")
        for sample in dataset[:args.show_examples]:
            print(f"\nID: {sample['id']}")
            for token, tag in zip(sample["tokens"], sample["ner_tags"]):
                if tag != "O":
                    print(f"  {token:30s} -> {tag}")
            print(f"  ... ({len(sample['tokens'])} tokens total)")

    # Print stats
    print_annotation_stats(dataset)

    # Save output
    output_file = output_dir / args.output_file
    with open(output_file, "w", encoding="utf-8") as f:
        for item in dataset:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")

    print(f"\nSaved {len(dataset)} annotated samples to {output_file}")

    # Also save a train/test split
    import random
    random.seed(42)
    indices = list(range(len(dataset)))
    random.shuffle(indices)
    split = int(len(dataset) * 0.8)
    train_indices = indices[:split]
    test_indices = indices[split:]

    train_file = output_dir / "synthetic_it_train.jsonl"
    test_file = output_dir / "synthetic_it_test.jsonl"

    with open(train_file, "w", encoding="utf-8") as f:
        for idx in train_indices:
            f.write(json.dumps(dataset[idx], ensure_ascii=False) + "\n")

    with open(test_file, "w", encoding="utf-8") as f:
        for idx in test_indices:
            f.write(json.dumps(dataset[idx], ensure_ascii=False) + "\n")

    print(f"  Train split: {len(train_indices)} samples -> {train_file}")
    print(f"  Test split:  {len(test_indices)} samples -> {test_file}")


if __name__ == "__main__":
    main()
