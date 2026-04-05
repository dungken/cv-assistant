import re
import logging
import uuid
import time
from typing import Dict, Any, List, Optional
from pathlib import Path

from shared.utils.cv_parser import SmartCVParser
from services.ner_service.services.refiner import JDRefiner

logger = logging.getLogger(__name__)


class JDParser:
    """
    Parses Job Descriptions (JDs) using a hybrid approach:
    1. Fine-tuned BERT for high-precision entity extraction.
    2. Section-aware logic to distinguish Requirements vs Benefits.
    3. Heuristics for seniority and experience normalization.
    """

    JD_SECTION_KEYWORDS = {
        "REQUIREMENTS": [
            "requirements", "required", "qualifications", "yêu cầu",
            "minimum qualifications", "must have", "must-have", "điều kiện",
            "what we're looking for", "what we are looking for",
            "your profile", "essential skills", "essential requirements",
            "your skills and experience", "skills and experience",
            "skills & experience", "skills required", "required skills",
            "technical requirements", "technical skills",
            "yêu cầu công việc", "yêu cầu ứng viên", "yêu cầu tuyển dụng",
            "kỹ năng yêu cầu", "năng lực cần có", "yêu cầu chuyên môn",
            "what you'll need", "what you need", "what you bring",
            "who you are", "about you", "ideal candidate",
            "key qualifications", "basic qualifications",
        ],
        "RESPONSIBILITIES": [
            "responsibilities", "duties", "what you'll do", "what you will do",
            "mô tả công việc", "trách nhiệm", "job description",
            "key responsibilities", "nhiệm vụ", "role description",
            "the role", "your role", "vai trò", "công việc chính",
            "nội dung công việc", "phạm vi công việc",
            "what you'll be doing", "day to day", "day-to-day",
            "scope of work", "your responsibilities",
        ],
        "BENEFITS": [
            "benefits", "perks", "what we offer", "quyền lợi", "chế độ",
            "compensation", "why join us", "phúc lợi", "đãi ngộ",
            "why you'll love working here", "why you will love", "love working here",
            "you'll love", "what's in it for you",
            "we offer", "our offer", "chế độ đãi ngộ", "chế độ phúc lợi",
            "quyền lợi được hưởng", "compensation and benefits",
            "salary and benefits", "lương thưởng", "total rewards",
        ],
        "ABOUT": [
            "about us", "company overview", "giới thiệu", "về chúng tôi",
            "about the company", "company description", "who we are",
            "giới thiệu công ty", "tổng quan công ty", "our company",
            "about the team", "về đội ngũ",
        ],
        "PREFERRED": [
            "preferred", "nice to have", "nice-to-have", "bonus", "ưu tiên", "điểm cộng",
            "plus", "additional skills", "advantage", "preferably",
            "preferred qualifications", "preferred skills",
            "bonus points", "extra points", "good to have",
            "lợi thế", "ưu tiên nếu có", "sẽ là lợi thế",
            "it's a plus", "would be a plus", "a plus if",
            "desirable", "desired skills", "desired qualifications",
            "not required but", "optional skills",
        ],
    }

    # Common technical skill patterns for fallback (Defensive Extraction)
    TECH_SKILLS = [
        # Frontend
        "Angular", "React", "Vue", "Vue.js", "JavaScript", "TypeScript", "ES6",
        "RxJS", "Signal", "HTML", "CSS", "SASS", "SCSS", "LESS", "Bootstrap",
        "Tailwind", "Webpack", "Vite", "Next.js", "Nuxt", "Nuxt.js",
        "jQuery", "Svelte", "Ember", "Backbone", "Material UI", "Ant Design",
        "Storybook", "Redux", "MobX", "Zustand", "Pinia", "Vuex",
        "Styled Components", "Emotion", "Chakra UI", "Figma",
        # Backend
        "Python", "Java", "Node.js", "Express", "Django", "Flask", "FastAPI",
        "Spring", "Spring Boot", "Laravel", "Go", "Golang", "Rust", "C#", ".NET",
        "ASP.NET", "Ruby", "Ruby on Rails", "PHP", "Symfony", "NestJS",
        "Koa", "Hapi", "Fastify", "Gin", "Echo", "Fiber",
        "Scala", "Kotlin", "Elixir", "Phoenix", "Clojure",
        "C++", "C", "Perl", "R", "MATLAB", "Lua", "Dart",
        "Hibernate", "MyBatis", "Entity Framework", "Prisma", "Sequelize",
        "TypeORM", "SQLAlchemy", "Dapper",
        # Mobile
        "Flutter", "React Native", "iOS", "Android", "Swift", "Objective-C",
        "Kotlin", "Xamarin", "Ionic", "Cordova", "SwiftUI", "Jetpack Compose",
        # DevOps / Cloud / Infra
        "Docker", "Kubernetes", "AWS", "Azure", "GCP", "Terraform",
        "CI/CD", "Jenkins", "Git", "Git-flow", "GitLab", "GitHub Actions",
        "CircleCI", "Travis CI", "ArgoCD", "Ansible", "Puppet", "Chef",
        "Helm", "Istio", "Prometheus", "Grafana", "ELK", "Datadog",
        "New Relic", "CloudWatch", "Nginx", "Apache", "HAProxy",
        "Linux", "Ubuntu", "CentOS", "Shell", "Bash",
        "VMware", "Vagrant", "Consul", "Vault",
        "CloudFormation", "Pulumi", "Serverless",
        # Databases
        "PostgreSQL", "MySQL", "MongoDB", "Redis", "Elasticsearch", "SQLite",
        "Oracle", "SQL Server", "MariaDB", "Cassandra", "DynamoDB",
        "Neo4j", "CouchDB", "InfluxDB", "TimescaleDB", "Memcached",
        "Firebase", "Supabase", "Firestore",
        # Message Queue / Streaming
        "Kafka", "RabbitMQ", "SQS", "Redis Pub/Sub", "NATS", "ZeroMQ",
        "Apache Pulsar", "Celery",
        # ML/AI
        "Machine Learning", "Deep Learning", "TensorFlow", "PyTorch", "NLP",
        "AI", "Scikit-learn", "Keras", "OpenCV", "Pandas", "NumPy",
        "Hugging Face", "LangChain", "LLM", "GPT", "BERT", "Transformer",
        "MLflow", "Kubeflow", "SageMaker", "Computer Vision",
        "Data Science", "Data Engineering", "Apache Spark", "Hadoop",
        "Airflow", "dbt", "Snowflake", "BigQuery", "Databricks",
        "Power BI", "Tableau", "Looker", "Metabase",
        # Methodology / Tools
        "Scrum", "Agile", "Kanban", "JIRA", "Confluence", "Trello",
        "Notion", "Slack", "Microsoft Teams",
        # API / Communication
        "RESTful API", "REST", "GraphQL", "gRPC", "WebSocket", "SOAP",
        "OpenAPI", "Swagger", "Postman", "API Gateway",
        # Security
        "OAuth", "OAuth2", "JWT", "Web Security", "OWASP",
        "SSL/TLS", "HTTPS", "IAM", "RBAC", "SAML", "SSO",
        "Penetration Testing", "Encryption", "Firewall",
        # Testing
        "Jest", "Mocha", "Cypress", "Selenium", "Playwright",
        "JUnit", "PyTest", "TestNG", "Cucumber", "Postman",
        "Unit Testing", "Integration Testing", "E2E Testing",
        "TDD", "BDD", "SonarQube", "Load Testing", "JMeter",
        # Architecture / Patterns
        "Microservices", "Monolith", "Event-Driven", "CQRS",
        "Domain-Driven Design", "Clean Architecture",
        "Design Patterns", "SOLID Principles", "OOP", "Functional Programming",
        # Other
        "Blockchain", "Web3", "Solidity", "Ethereum",
        "IoT", "Embedded", "RTOS",
        "SAP", "Salesforce", "ServiceNow",
        "Unity", "Unreal Engine",
    ]

    # Patterns that indicate company boilerplate (not real section content)
    _BOILERPLATE_PATTERNS = [
        re.compile(r"^company\s+(type|industry|size|overview)\s*$", re.I),
        re.compile(r"^(it\s+outsourcing|software\s+development\s+outsourcing)\s*$", re.I),
        re.compile(r"^\d+\s*-\s*\d+\s*$"),            # size like "1-150"
        re.compile(r"^(monday|tuesday|friday)\s*-", re.I),
        re.compile(r"^(no\s+ot|overtime\s+policy)\s*$", re.I),
        re.compile(r"^country\s*$", re.I),
        re.compile(r"^working\s+days?\s*$", re.I),
        re.compile(r"^(finland|vietnam|thailand|singapore|usa|uk)\s*$", re.I),
    ]

    # Noise words to strip from company names
    _COMPANY_NOISE = re.compile(
        r"\b(big\s+logo|logo|icon|banner|image|photo|picture|thumbnail)\b", re.I
    )

    def __init__(self, extractor=None):
        self.parser = SmartCVParser()
        self.extractor = extractor
        self.refiner = JDRefiner()

    def parse_text(self, text: str, title: str = "", company: str = "") -> Dict[str, Any]:
        """Deep parse of JD text."""
        start_time = time.time()

        # 1. Title/Company Auto-detection
        if not title or not company:
            auto_title, auto_company = self._detect_title_company(text)
            title = title or auto_title
            company = company or auto_company

        # 2. Section Segmentation
        section_ranges = self._detect_section_ranges(text)

        # 3. NER Entity Extraction (The "Brain")
        entities = []
        if self.extractor:
            try:
                entities = self.extractor.extract(text)
            except Exception as e:
                logger.error(f"JD NER extraction failed: {e}")

        # 4. Contextual Skill Classification
        skills = self._extract_skills_contextual(text, entities, section_ranges)

        # 5. Experience & Seniority Analysis
        level, exp_years, min_exp, max_exp = self._analyze_experience(text, title, entities)

        # 6. Location & Education
        location = self._extract_location(text, entities)
        degree = self._extract_degree(text)
        certs = self._extract_certs(entities)

        parse_time = int((time.time() - start_time) * 1000)

        # Structural Output (Analysis Object)
        analysis = {
            "title": title,
            "company": company,
            "min_exp": min_exp,
            "max_exp": max_exp,
            "seniority": level,
            "skills_required": skills["required"],
            "skills_preferred": skills["preferred"],
            "degree_required": degree,
            "certifications": certs,
            "location": location
        }

        # 7. LLM Refinement (Elite Phase)
        refined_analysis = self.refiner.refine(text, analysis)
        
        # Sync local variables with refined data (for return dict)
        title = refined_analysis.get("title", title)
        company = self._clean_company_name(refined_analysis.get("company", company))
        level = refined_analysis.get("seniority", level)
        min_exp = refined_analysis.get("min_exp", min_exp)
        max_exp = refined_analysis.get("max_exp", max_exp)
        location = refined_analysis.get("location", location)

        # Build final skill lists: merge BERT + LLM, deduplicate, normalize casing
        final_required = refined_analysis.get("skills_required", skills["required"])
        final_preferred = refined_analysis.get("skills_preferred", skills["preferred"])

        # Clean + normalize casing + deduplicate
        def _normalize_and_dedup(skill_list):
            seen = set()
            result = []
            for s in skill_list:
                cleaned = self._clean_skill(s)
                if not cleaned:
                    continue
                normalized = self._normalize_skill_casing(cleaned)
                key = normalized.lower()
                if key in seen:
                    continue
                seen.add(key)
                result.append(normalized)
            return sorted(result)

        final_required = _normalize_and_dedup(final_required)
        req_lower = {s.lower() for s in final_required}
        final_preferred = _normalize_and_dedup(
            [s for s in final_preferred if self._normalize_skill_casing(self._clean_skill(s)).lower() not in req_lower]
        )

        return {
            "jd_id": f"jd-{uuid.uuid4().hex[:8]}",
            "title": title,
            "company": company,
            "location": location,
            "level": level,
            "experience_years": exp_years,
            "min_exp": min_exp,
            "max_exp": max_exp,
            "sections": self._get_sections_content(text, section_ranges),
            "extracted_skills": {
                "required": final_required,
                "preferred": final_preferred,
            },
            "analysis": refined_analysis,
            "entities": [e.dict() for e in entities],
            "metadata": {
                "language": "vi" if re.search(r'[àáảãạăằắẳẵặâầấẩẫậèéẻẽẹêềếểễệìíỉĩịòóỏõọôồốổỗộơờớởỡợùúủũụưừứửữựỳýỷỹỵđ]', text, re.I) else "en",
                "input_method": "text",
                "parse_time_ms": parse_time,
                "model_version": "jd-bert-v1-hybrid"
            },
            "status": "success",
        }

    def _is_boilerplate_line(self, line: str) -> bool:
        """Return True if the line is company/metadata boilerplate, not real content."""
        return any(p.match(line) for p in self._BOILERPLATE_PATTERNS)

    def _get_sections_content(self, text: str, section_ranges: List[Dict]) -> Dict[str, List[str]]:
        """Extract line-by-line items for each section to satisfy UI requirements."""
        sections = {
            "requirements": [], "responsibilities": [], "benefits": [],
            "about": [], "preferred": []
        }

        for r in section_ranges:
            section_text = text[r["start"]:r["end"]].strip()
            # Split into lines and clean
            lines = [l.strip() for l in section_text.split("\n") if l.strip()]
            # Skip the first line if it's just the header we already matched (< 5 words)
            if lines and len(lines[0].split()) < 5:
                lines = lines[1:]

            key = r["type"].lower()
            if key not in sections:
                continue

            # Clean bullet characters and filter boilerplate
            clean_lines = []
            for l in lines:
                l = re.sub(r"^[-•\*◦▪►→✓✔☑\d\.\)]\s*", "", l).strip()
                if l and not self._is_boilerplate_line(l):
                    clean_lines.append(l)

            sections[key].extend(clean_lines)

        return sections

    def _clean_company_name(self, name: str) -> str:
        """Strip UI/image noise from company names."""
        name = self._COMPANY_NOISE.sub("", name).strip()
        # Collapse multiple spaces
        name = re.sub(r"\s{2,}", " ", name).strip()
        return name

    def _detect_title_company(self, text: str) -> tuple:
        """Detect title and company using multiple strategies."""
        lines = [l.strip() for l in text.strip().split("\n") if l.strip()][:20]
        if not lines:
            return "", ""

        # Address keywords to filter out
        address_kws = ["số ", "phường ", "quận ", "tp.", "thành phố", "hà nội", "hcm",
                       "tòa nhà", "đường ", "floor", "building", "street", "district"]
        # Job title keywords to prioritize
        job_kws = [
            "developer", "designer", "engineer", "kỹ sư", "nhân viên", "chuyên viên",
            "thực tập", "intern", "lead", "manager", "architect", "analyst", "consultant",
            "specialist", "administrator", "devops", "qa", "tester", "scientist",
            "director", "coordinator", "officer", "executive", "lập trình viên",
            "trưởng nhóm", "phó phòng", "giám đốc", "phụ trách",
        ]
        # Section header keywords to skip
        section_kws = ["mô tả", "yêu cầu", "quyền lợi", "trách nhiệm",
                       "requirements", "responsibilities", "benefits", "about us",
                       "nice to have", "preferred", "description"]

        title = ""
        company = ""

        # Strategy 1: Explicit labels "Position:", "Title:", "Company:", "Vị trí:"
        for l in lines:
            if not title:
                m = re.match(r"(?:position|title|vị\s*trí|chức\s*(?:danh|vụ)|job\s*title)\s*:\s*(.+)", l, re.I)
                if m:
                    title = m.group(1).strip()[:120]
            if not company:
                m = re.match(r"(?:company|công\s*ty|employer|nhà\s*tuyển\s*dụng)\s*:\s*(.+)", l, re.I)
                if m:
                    company = self._clean_company_name(m.group(1).strip()[:100])

        # Strategy 2: "X at Y" / "X - Y" / "X | Y" pattern in first few lines
        if not title:
            for l in lines[:5]:
                # "Senior Developer at FPT Software"
                m = re.match(r"(.+?)\s+(?:at|tại|@)\s+(.+)", l, re.I)
                if m and any(kw in m.group(1).lower() for kw in job_kws):
                    title = m.group(1).strip()[:120]
                    if not company:
                        company = self._clean_company_name(m.group(2).strip()[:100])
                    break
                # "Senior Developer - FPT Software" or "Senior Developer | FPT"
                m = re.match(r"(.+?)\s*[-|–—]\s*(.+)", l)
                if m and any(kw in m.group(1).lower() for kw in job_kws):
                    title = m.group(1).strip()[:120]
                    if not company:
                        company = self._clean_company_name(m.group(2).strip()[:100])
                    break

        # Strategy 3: Filter lines and find title by job keywords
        candidate_lines = []
        for l in lines:
            if any(kw in l.lower() for kw in address_kws) and len(re.findall(r"\d+", l)) > 1:
                continue
            if any(kw in l.lower() for kw in section_kws):
                continue
            candidate_lines.append(l)

        if candidate_lines and not title:
            for l in candidate_lines:
                if any(kw in l.lower() for kw in job_kws):
                    title = l[:120]
                    break
            if not title:
                title = candidate_lines[0][:120]

        # Strategy 4: Find company from remaining candidate lines
        if not company and candidate_lines:
            for l in candidate_lines:
                if l == title:
                    continue
                l_lower = l.lower()
                # Skip lines that are section headers or too long
                if any(kw in l_lower for kw in section_kws):
                    continue
                if len(l.split()) > 10:
                    continue
                # Company names are typically short, capitalized, and not job keywords
                if len(l.split()) < 8 and not any(kw in l_lower for kw in job_kws):
                    company = self._clean_company_name(l[:100])
                    break

        # Strategy 5: Use NER entities if available
        if self.extractor and (not title or not company):
            try:
                header_text = "\n".join(lines[:8])
                header_entities = self.extractor.extract(header_text)
                for ent in header_entities:
                    if ent.type == "JOB_TITLE" and not title:
                        title = ent.text.strip()
                    elif ent.type == "ORG" and not company:
                        company = self._clean_company_name(ent.text.strip())
            except Exception:
                pass

        return title, company

    def _detect_section_ranges(self, text: str) -> List[Dict]:
        """Find character ranges for each section to map entities later."""
        ranges = []
        text_upper = text.upper()
        
        # Collect all potential matches
        matches = []
        for sec_type, keywords in self.JD_SECTION_KEYWORDS.items():
            for kw in keywords:
                regex = re.compile(rf"\n?#*\s*{re.escape(kw.upper())}[:\s\n]", re.I)
                for m in regex.finditer(text_upper):
                    matches.append({"type": sec_type, "start": m.start(), "end": m.end()})
        
        # Sort matches by start position
        matches = sorted(matches, key=lambda x: x["start"])
        
        # Create continuous ranges
        for i, m in enumerate(matches):
            section_end = matches[i+1]["start"] if i + 1 < len(matches) else len(text)
            ranges.append({"type": m["type"], "start": m["start"], "end": section_end})
            
        return ranges

    # Known acronyms/special-cased skills that should NOT be .title()'d
    _SKILL_CASING = {
        "rxjs": "RxJS", "ngrx": "NgRx", "css3": "CSS3", "html5": "HTML5",
        "css": "CSS", "html": "HTML", "ci/cd": "CI/CD", "ci": "CI", "cd": "CD",
        "aws": "AWS", "gcp": "GCP", "sql": "SQL", "nosql": "NoSQL",
        "graphql": "GraphQL", "grpc": "gRPC", "jwt": "JWT", "oauth": "OAuth",
        "rest": "REST", "restful": "RESTful", "restful api": "RESTful API",
        "api": "API", "sdk": "SDK", "cli": "CLI", "ui": "UI", "ux": "UX",
        "oop": "OOP", "tdd": "TDD", "bdd": "BDD", "sso": "SSO",
        "saml": "SAML", "rbac": "RBAC", "iam": "IAM", "ssl": "SSL",
        "tls": "TLS", "ssl/tls": "SSL/TLS", "https": "HTTPS",
        "owasp": "OWASP", "mqtt": "MQTT", "amqp": "AMQP",
        "xml": "XML", "json": "JSON", "yaml": "YAML", "csv": "CSV",
        "crud": "CRUD", "cqrs": "CQRS", "ddd": "DDD", "solid": "SOLID",
        "dry": "DRY", "mvvm": "MVVM", "mvc": "MVC", "mvp": "MVP",
        "nginx": "Nginx", "mysql": "MySQL", "postgresql": "PostgreSQL",
        "mongodb": "MongoDB", "redis": "Redis", "elasticsearch": "Elasticsearch",
        "sqlite": "SQLite", "mariadb": "MariaDB", "dynamodb": "DynamoDB",
        "rabbitmq": "RabbitMQ", "kafka": "Kafka", "sqs": "SQS",
        "docker": "Docker", "kubernetes": "Kubernetes", "terraform": "Terraform",
        "jenkins": "Jenkins", "gitlab": "GitLab", "github": "GitHub",
        "circleci": "CircleCI", "argocd": "ArgoCD",
        "nestjs": "NestJS", "nuxt.js": "Nuxt.js", "next.js": "Next.js",
        "vue.js": "Vue.js", "node.js": "Node.js", "react.js": "React",
        "express.js": "Express.js", "angular": "Angular",
        "typescript": "TypeScript", "javascript": "JavaScript",
        ".net": ".NET", "asp.net": "ASP.NET", "c#": "C#", "c++": "C++",
        "fastapi": "FastAPI", "flask": "Flask", "django": "Django",
        "spring boot": "Spring Boot", "spring": "Spring",
        "react native": "React Native", "flutter": "Flutter",
        "ios": "iOS", "android": "Android", "swiftui": "SwiftUI",
        "pytorch": "PyTorch", "tensorflow": "TensorFlow",
        "scikit-learn": "Scikit-learn", "pandas": "Pandas", "numpy": "NumPy",
        "nlp": "NLP", "llm": "LLM", "bert": "BERT", "gpt": "GPT",
        "power bi": "Power BI", "tableau": "Tableau",
        "sonarqube": "SonarQube", "jmeter": "JMeter",
        "jest": "Jest", "cypress": "Cypress", "selenium": "Selenium",
        "playwright": "Playwright", "junit": "JUnit", "pytest": "Pytest",
        "webpack": "Webpack", "vite": "Vite", "babel": "Babel",
        "redux": "Redux", "mobx": "MobX", "vuex": "Vuex", "pinia": "Pinia",
        "zustand": "Zustand", "storybook": "Storybook",
        "tailwind": "Tailwind CSS", "bootstrap": "Bootstrap", "sass": "Sass",
        "microservices": "Microservices", "devops": "DevOps",
        "linux": "Linux", "bash": "Bash", "git": "Git", "git-flow": "Git-flow",
        "jira": "Jira", "agile": "Agile", "scrum": "Scrum", "kanban": "Kanban",
    }

    def _normalize_skill_casing(self, skill: str) -> str:
        """Apply correct casing for known skills, fallback to title case."""
        key = skill.lower().strip()
        if key in self._SKILL_CASING:
            return self._SKILL_CASING[key]
        # For unknown skills, use title case
        return skill.title() if skill == skill.lower() or skill == skill.upper() else skill

    def _clean_skill(self, raw: str) -> str:
        """Strip leading/trailing punctuation and whitespace from a skill name."""
        cleaned = re.sub(r'^[\W_]+|[\W_]+$', '', raw.strip())
        return cleaned.strip()

    # Inline context patterns near a skill that indicate preferred/nice-to-have
    _PREFERRED_CONTEXT_PATTERNS = re.compile(
        r"(?:nice\s+to\s+have|nice-to-have|bonus|preferred|preferably|"
        r"a\s+plus|is\s+a\s+plus|would\s+be\s+a\s+plus|"
        r"good\s+to\s+have|not\s+required|optional|advantage|"
        r"ưu\s*tiên|điểm\s*cộng|lợi\s*thế|sẽ\s+là\s+lợi\s+thế|"
        r"không\s+bắt\s+buộc|có\s+thì\s+tốt)", re.I
    )

    # Inline context patterns near a skill that indicate required/must-have
    _REQUIRED_CONTEXT_PATTERNS = re.compile(
        r"(?:must\s+have|must-have|required|mandatory|essential|"
        r"bắt\s*buộc|yêu\s*cầu\s*bắt\s*buộc|cần\s+có|phải\s+có|"
        r"minimum|tối\s*thiểu)", re.I
    )

    def _get_line_context(self, text: str, pos: int) -> str:
        """Get the line containing the position + adjacent lines for context."""
        # Find line boundaries
        line_start = text.rfind("\n", 0, pos)
        line_start = line_start + 1 if line_start >= 0 else 0
        # Also include the previous line for header context
        prev_line_start = text.rfind("\n", 0, max(0, line_start - 1))
        prev_line_start = prev_line_start + 1 if prev_line_start >= 0 else 0

        line_end = text.find("\n", pos)
        if line_end < 0:
            line_end = len(text)

        return text[prev_line_start:line_end]

    def _classify_skill_context(self, text: str, pos: int, section_type: str) -> str:
        """Classify a skill as required or preferred using multi-signal approach.

        Priority: Section-based first (most reliable), then inline context
        only overrides when the inline pattern is on the SAME LINE as the skill.
        """
        # Signal 1: Section-based classification (most reliable)
        if section_type == "PREFERRED":
            return "PREFERRED"
        if section_type in ("BENEFITS", "ABOUT"):
            return "IGNORED"

        # Signal 2: Inline context on the same line/adjacent line only
        # (prevents "Nice to have" from next section bleeding into current)
        line_context = self._get_line_context(text, pos)
        if self._PREFERRED_CONTEXT_PATTERNS.search(line_context):
            return "PREFERRED"
        if self._REQUIRED_CONTEXT_PATTERNS.search(line_context):
            return "REQUIREMENTS"

        # Signal 3: Default to required (if in REQUIREMENTS, RESPONSIBILITIES, or unclassified)
        return "REQUIREMENTS"

    def _extract_skills_contextual(self, text: str, entities: List, section_ranges: List) -> Dict:
        required = set()
        preferred = set()

        # Build a case-insensitive lookup to avoid duplicates
        seen_skills_lower = set()

        def _canonical_key(name: str) -> set:
            """Generate all canonical forms for deduplication."""
            k = name.lower().strip()
            forms = {k}
            # "Vue.js" ↔ "Vue" ↔ "Vuejs"
            forms.add(k.replace(".js", ""))
            forms.add(k.replace(".", ""))
            forms.add(k.replace(" ", ""))
            forms.add(k.replace("-", ""))
            # "Angular 2+" → "Angular", "Angular 2" → "Angular"
            base = re.sub(r"\s+\d[\d+.*]*$", "", k)
            forms.add(base)
            # "Microservices architecture" → "Microservices"
            if " " in k:
                forms.add(k.split()[0])
            # "CI/CD" covers "CI" and "CD"
            if "/" in k:
                for part in k.split("/"):
                    forms.add(part.strip())
            return forms

        def _add_skill(skill_name: str, classification: str):
            """Add skill to the correct set, avoiding duplicates."""
            key = skill_name.lower().strip()
            if key in seen_skills_lower or len(key) < 2:
                return

            # Check if any canonical form already exists
            forms = _canonical_key(skill_name)
            if any(f in seen_skills_lower for f in forms):
                return

            # Skip if this is a sub-part of an already-added compound skill
            # e.g. skip "CI" if "CI/CD" already added
            for existing in list(seen_skills_lower):
                if "/" in existing and key in existing.split("/"):
                    return

            seen_skills_lower.add(key)
            # Also register canonical forms for future checks
            seen_skills_lower.update(forms)

            if classification == "PREFERRED":
                preferred.add(skill_name)
            elif classification == "REQUIREMENTS":
                required.add(skill_name)
            # IGNORED skills are dropped

        # 1. AI-Driven Extraction (BERT)
        for ent in entities:
            if ent.type == "SKILL":
                skill = self._clean_skill(ent.text)
                if not skill or len(skill) < 2:
                    continue
                skill = self._normalize_skill_casing(skill)

                # Find which section this entity falls into
                section_type = "REQUIREMENTS"
                for r in section_ranges:
                    if r["start"] <= ent.start < r["end"]:
                        section_type = r["type"]
                        break

                classification = self._classify_skill_context(text, ent.start, section_type)
                _add_skill(skill, classification)

        # 2. Defensive Fallback (Regex for common tech skills)
        text_lower = text.lower()
        for skill_kw in self.TECH_SKILLS:
            pattern = rf"\b{re.escape(skill_kw.lower())}\b"
            match = re.search(pattern, text_lower)
            if match:
                skill_display = skill_kw
                if skill_display.lower() in seen_skills_lower:
                    continue

                section_type = "REQUIREMENTS"
                for r in section_ranges:
                    if r["start"] <= match.start() < r["end"]:
                        section_type = r["type"]
                        break

                classification = self._classify_skill_context(text, match.start(), section_type)
                _add_skill(skill_display, classification)

        # 3. Deduplicate: if a skill appears in both sets, keep in required only
        preferred -= required

        return {
            "required": sorted(list(required)),
            "preferred": sorted(list(preferred))
        }

    def _analyze_experience(self, text: str, title: str, entities: List) -> tuple:
        """Extract level and normalize years using multi-signal approach."""
        text_lower = text.lower()
        title_lower = title.lower()

        level = "mid"
        min_years = 0
        max_years = None
        years_str = ""

        # 1. Seniority from title (High weight)
        senior_kws = ["senior", "sr.", "sr ", "lead", "principal", "staff",
                      "architect", "trưởng nhóm", "trưởng phòng", "quản lý"]
        junior_kws = ["junior", "jr.", "jr ", "fresher", "entry level", "entry-level",
                      "mới ra trường", "sinh viên mới"]
        intern_kws = ["intern", "internship", "thực tập", "apprentice"]

        if any(kw in title_lower for kw in senior_kws):
            level = "senior"
            min_years = 5
        elif any(kw in title_lower for kw in intern_kws):
            level = "intern"
            min_years = 0
        elif any(kw in title_lower for kw in junior_kws):
            level = "junior"
            min_years = 0

        # 2. Extract years from text (Regex) — ordered from most specific to least
        exp_patterns = [
            # "4-6 years" / "4–6 years" / "4 to 6 years"
            (r"(\d+)\s*[-–~]\s*(\d+)\s*(?:years?|năm)\b", True),
            (r"(\d+)\s+(?:to|đến)\s+(\d+)\s*(?:years?|năm)\b", True),
            # "4+ years" / "4+ năm"
            (r"(\d+)\+\s*(?:years?|năm)\b", False),
            # "at least 4 years" / "minimum 4 years" / "ít nhất 4 năm"
            (r"(?:ít nhất|tối thiểu|at least|minimum|from)\s*(\d+)\s*(?:years?|năm)\b", False),
            # "4 years of experience" / "4 năm kinh nghiệm"
            (r"(\d+)\s*(?:years?|năm)\s+(?:of\s+)?(?:experience|kinh\s*nghiệm)\b", False),
            # "over 4 years" / "trên 4 năm"
            (r"(?:over|above|trên|hơn)\s*(\d+)\s*(?:years?|năm)\b", False),
            # "experienced 4 years" or just "4 years" near experience context
            (r"(\d+)\s*(?:years?|năm)\s+(?:working|relevant|professional|hands-on|practical)", False),
            # Vietnamese patterns: "kinh nghiệm 4 năm" / "kinh nghiệm từ 4 năm"
            (r"kinh\s*nghiệm\s+(?:từ\s+)?(\d+)\s*(?:years?|năm)", False),
        ]

        for p, has_max in exp_patterns:
            m = re.search(p, text_lower)
            if m:
                years_str = m.group(0)
                try:
                    vals = [int(v) for v in m.groups() if v and v.isdigit()]
                    if vals:
                        min_years = max(min_years, vals[0])
                        if has_max and len(vals) > 1:
                            max_years = vals[1]
                except Exception:
                    pass
                break

        # 3. Also scan the full text for seniority keywords (not just title)
        if level == "mid":
            # Check if text mentions senior/lead level explicitly
            if re.search(r"\b(?:senior|lead|principal|staff)\s+(?:level|position|role)\b", text_lower):
                level = "senior"
            elif re.search(r"\b(?:junior|entry[\s-]level|fresher)\s+(?:level|position|role)\b", text_lower):
                level = "junior"

        # 4. Infer level from years if still default "mid"
        if level == "mid":
            if min_years >= 7:
                level = "senior"
            elif min_years >= 4:
                level = "mid"
            elif min_years <= 1:
                level = "junior"

        return level, years_str, min_years, max_years

    def _extract_degree(self, text: str) -> Optional[str]:
        # Use precise patterns: require "degree/of/in" after master to avoid "Scrum Master" FP
        patterns = {
            "PhD":      r"\b(?:tiến\s*sĩ|phd|ph\.d)\b",
            "Master":   r"\b(?:thạc\s*sĩ|master(?:'?s)?\s+(?:degree|of|in))\b",
            "Bachelor": r"\b(?:đại\s*học|cử\s*nhân|bachelor(?:'?s)?(?:\s+(?:degree|of|in))?|degree\s+in)\b",
        }
        for label, p in patterns.items():
            if re.search(p, text, re.I):
                return label
        return None

    def _extract_certs(self, entities: List) -> List[str]:
        return sorted(list(set([e.text.strip() for e in entities if e.type == "CERT"])))

    def _extract_location(self, text: str, entities: List = None) -> str:
        # 1. Explicit label (require colon to avoid false matches)
        for p in [r"(?:^|\n)\s*(?:địa\s*điểm|location)\s*:\s*(.+)",
                  r"\blocation\s*:\s*(.+)"]:
            m = re.search(p, text, re.I)
            if m:
                loc = m.group(1).split("\n")[0].strip()
                if loc:
                    return loc

        # 2. NER-based: use the first LOC entity that appears in the early part of text
        #    (title area, roughly first 300 chars) — skip common office city lists
        SKIP_LOCS = {"helsinki", "finland", "thailand", "khon kaen", "bangkok",
                     "abu dhabi", "uae", "ksa", "riyadh", "saudi arabia"}
        if entities:
            for ent in entities:
                if ent.type == "LOC" and ent.start < 400:
                    if ent.text.lower() not in SKIP_LOCS:
                        return ent.text.strip()

        return ""

    def parse_file(self, file_path: str) -> Dict[str, Any]:
        """Extract text and parse."""
        text = self.parser.get_markdown(file_path)
        if not text: return {"status": "error", "error": "No text extracted"}
        return self.parse_text(text)
