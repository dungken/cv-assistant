"""
Task 2.1: IT Skills Ontology - Knowledge Graph of skill relationships.
Maps O*NET data into a hierarchical structure that understands:
- Skill categories (Frontend, Backend, DevOps, etc.)
- Parent-child relationships (React -> Frontend -> Web Development)
- Skill similarity/substitutability (React <-> Vue.js)
- Proficiency progression (Junior -> Senior skill expectations)
"""

import logging
from typing import Optional
from collections import defaultdict

logger = logging.getLogger(__name__)


# ─── IT Skills Hierarchy (Ontology) ─────────────────────────────────────────

# Each category maps to: subcategories -> specific skills
# This is the "knowledge graph" that powers context-aware matching

SKILL_ONTOLOGY: dict[str, dict[str, list[str]]] = {
    "Programming Languages": {
        "Systems Languages": ["C", "C++", "Rust", "Go", "Golang", "Assembly"],
        "Application Languages": ["Java", "C#", "Kotlin", "Swift", "Scala", "Dart"],
        "Scripting Languages": ["Python", "JavaScript", "TypeScript", "Ruby", "PHP", "Perl", "Lua"],
        "Functional Languages": ["Haskell", "Elixir", "Clojure", "Erlang", "F#", "OCaml"],
        "Data/ML Languages": ["R", "MATLAB", "Julia", "SQL", "SAS"],
        "Shell/Scripting": ["Bash", "PowerShell", "Shell", "Zsh"],
    },
    "Frontend Development": {
        "Core Web": ["HTML", "HTML5", "CSS", "CSS3", "JavaScript", "TypeScript"],
        "CSS Frameworks": ["Tailwind CSS", "Tailwind", "Bootstrap", "Material UI", "MUI", "Bulma", "SASS", "SCSS", "Less", "Styled Components"],
        "JavaScript Frameworks": ["React", "React.js", "ReactJS", "Angular", "AngularJS", "Vue.js", "Vue", "VueJS", "Svelte", "SolidJS"],
        "Meta-Frameworks": ["Next.js", "NextJS", "Nuxt.js", "Gatsby", "Remix", "Astro"],
        "State Management": ["Redux", "Vuex", "Pinia", "MobX", "Zustand", "Recoil", "NgRx"],
        "Build Tools": ["Webpack", "Vite", "Babel", "ESBuild", "Rollup", "Parcel", "Turbopack"],
        "Testing": ["Jest", "Cypress", "Playwright", "Testing Library", "Storybook", "Vitest"],
    },
    "Backend Development": {
        "Node.js Ecosystem": ["Node.js", "NodeJS", "Express.js", "Express", "NestJS", "Fastify", "Koa"],
        "Python Frameworks": ["Django", "Flask", "FastAPI", "Tornado", "Sanic", "aiohttp"],
        "Java/JVM Frameworks": ["Spring Boot", "Spring", "Quarkus", "Micronaut", "Vert.x"],
        ".NET Ecosystem": ["ASP.NET", "ASP.NET Core", ".NET", ".NET Core", "Entity Framework", "Blazor"],
        "Go Frameworks": ["Gin", "Fiber", "Echo", "Chi", "Gorilla"],
        "Ruby Ecosystem": ["Ruby on Rails", "Rails", "Sinatra", "Hanami"],
        "PHP Frameworks": ["Laravel", "Symfony", "CodeIgniter", "CakePHP"],
        "API Technologies": ["REST", "REST API", "RESTful", "GraphQL", "gRPC", "WebSocket", "tRPC", "OpenAPI", "Swagger"],
        "Message Queues": ["RabbitMQ", "Apache Kafka", "Kafka", "ActiveMQ", "Redis Pub/Sub", "Amazon SQS", "NATS"],
    },
    "Database": {
        "Relational": ["PostgreSQL", "Postgres", "MySQL", "MariaDB", "SQL Server", "MSSQL", "Oracle", "SQLite", "CockroachDB"],
        "NoSQL Document": ["MongoDB", "CouchDB", "Couchbase", "Amazon DocumentDB", "Firebase Firestore", "Firestore"],
        "Key-Value": ["Redis", "Memcached", "DynamoDB", "Etcd", "Amazon ElastiCache"],
        "Search Engines": ["Elasticsearch", "OpenSearch", "Solr", "Meilisearch", "Algolia"],
        "Graph Databases": ["Neo4j", "ArangoDB", "Amazon Neptune", "JanusGraph"],
        "Time-Series": ["InfluxDB", "TimescaleDB", "Prometheus", "QuestDB"],
        "Cloud Databases": ["Amazon RDS", "Cloud SQL", "Supabase", "PlanetScale", "Neon", "Firebase"],
    },
    "DevOps & Infrastructure": {
        "Containerization": ["Docker", "Podman", "containerd", "LXC"],
        "Orchestration": ["Kubernetes", "K8s", "Docker Swarm", "Nomad", "Amazon ECS", "Amazon EKS"],
        "CI/CD": ["Jenkins", "GitHub Actions", "GitLab CI/CD", "GitLab CI", "CircleCI", "Travis CI", "ArgoCD", "Drone", "Tekton"],
        "Infrastructure as Code": ["Terraform", "Pulumi", "CloudFormation", "AWS CDK", "Ansible", "Puppet", "Chef", "SaltStack"],
        "Cloud Platforms": ["AWS", "Amazon Web Services", "Azure", "Microsoft Azure", "GCP", "Google Cloud", "Google Cloud Platform", "DigitalOcean", "Heroku", "Vercel", "Netlify"],
        "Monitoring & Observability": ["Prometheus", "Grafana", "Datadog", "New Relic", "Splunk", "ELK Stack", "Jaeger", "OpenTelemetry", "PagerDuty"],
        "Service Mesh": ["Istio", "Envoy", "Linkerd", "Consul"],
        "Web Servers": ["Nginx", "Apache", "Caddy", "HAProxy", "Traefik"],
        "OS & Platforms": ["Linux", "Ubuntu", "CentOS", "RHEL", "Debian", "Alpine", "Windows Server"],
        "Package Management": ["Helm", "Kustomize", "Vagrant"],
    },
    "Data Engineering": {
        "Big Data Processing": ["Apache Spark", "Spark", "PySpark", "Hadoop", "MapReduce", "Flink", "Apache Flink", "Apache Beam"],
        "Data Orchestration": ["Apache Airflow", "Airflow", "Prefect", "Dagster", "Luigi"],
        "Streaming": ["Apache Kafka", "Kafka", "Kafka Streams", "Apache Pulsar", "Amazon Kinesis"],
        "Data Warehouses": ["Snowflake", "BigQuery", "Redshift", "Databricks", "Azure Synapse"],
        "ETL/ELT": ["dbt", "Fivetran", "Airbyte", "Talend", "Informatica"],
        "BI & Visualization": ["Tableau", "Power BI", "Looker", "Metabase", "Superset", "Grafana"],
    },
    "Machine Learning & AI": {
        "ML Frameworks": ["TensorFlow", "PyTorch", "Keras", "JAX", "MXNet"],
        "ML Libraries": ["Scikit-learn", "Sklearn", "XGBoost", "LightGBM", "CatBoost", "Pandas", "NumPy", "Scipy"],
        "NLP": ["Hugging Face", "HuggingFace", "Transformers", "BERT", "GPT", "spaCy", "NLTK", "LangChain", "LlamaIndex"],
        "Computer Vision": ["OpenCV", "YOLO", "Detectron2", "MediaPipe"],
        "MLOps": ["MLflow", "Kubeflow", "SageMaker", "Vertex AI", "Weights & Biases", "DVC"],
        "Data Science": ["Jupyter", "Matplotlib", "Seaborn", "Plotly"],
    },
    "Mobile Development": {
        "Cross-Platform": ["React Native", "Flutter", "Xamarin", "Ionic", "Cordova", "MAUI"],
        "Android": ["Android", "Kotlin", "Jetpack Compose", "Android Studio"],
        "iOS": ["iOS", "Swift", "SwiftUI", "Objective-C", "Xcode"],
    },
    "Security": {
        "Security Frameworks": ["OWASP", "NIST", "ISO 27001", "SOC 2"],
        "Security Tools": ["Burp Suite", "Metasploit", "Wireshark", "Nmap", "Nessus", "Qualys", "Snort", "Splunk"],
        "Authentication": ["OAuth", "OAuth 2.0", "JWT", "SAML", "OpenID Connect", "OIDC", "SSO", "MFA"],
        "Encryption": ["SSL", "TLS", "SSL/TLS", "PKI", "AES", "RSA"],
        "Cloud Security": ["IAM", "WAF", "VPC", "Security Groups", "KMS"],
    },
    "Version Control & Collaboration": {
        "VCS": ["Git", "GitHub", "GitLab", "Bitbucket", "SVN", "Mercurial"],
        "Project Management": ["Jira", "Confluence", "Trello", "Asana", "Linear", "Notion", "Monday.com"],
        "Communication": ["Slack", "Microsoft Teams", "Discord"],
    },
    "Testing & QA": {
        "Unit Testing": ["Jest", "Mocha", "JUnit", "pytest", "TestNG", "xUnit", "NUnit", "Vitest"],
        "E2E Testing": ["Selenium", "Cypress", "Playwright", "Puppeteer", "Appium"],
        "Performance Testing": ["JMeter", "Gatling", "k6", "Locust", "Artillery"],
        "API Testing": ["Postman", "Insomnia", "REST Assured", "Supertest"],
    },
    "Architecture & Methodologies": {
        "Architecture Patterns": ["Microservices", "Monolith", "Serverless", "Event-Driven", "CQRS", "DDD", "Hexagonal"],
        "Development Practices": ["Agile", "Scrum", "Kanban", "SAFe", "Lean", "XP"],
        "Engineering Practices": ["CI/CD", "TDD", "BDD", "DevOps", "SRE", "GitOps", "Infrastructure as Code"],
        "Design Principles": ["Design Patterns", "SOLID", "Clean Architecture", "Clean Code", "DRY", "KISS"],
    },
    "Game Development": {
        "Game Engines": ["Unity", "Unreal Engine", "Godot", "CryEngine", "Cocos2d"],
        "Graphics": ["OpenGL", "DirectX", "Vulkan", "WebGL", "Metal"],
    },
    "Blockchain": {
        "Smart Contracts": ["Solidity", "Vyper", "Rust (Solana)"],
        "Platforms": ["Ethereum", "Solana", "Polygon", "Avalanche", "Cardano"],
        "Tools": ["Web3", "Web3.js", "Ethers.js", "Hardhat", "Truffle", "Foundry"],
    },
    "Embedded & IoT": {
        "Platforms": ["Arduino", "Raspberry Pi", "ESP32", "STM32"],
        "RTOS": ["FreeRTOS", "RTOS", "Zephyr"],
        "Protocols": ["MQTT", "CoAP", "Zigbee", "BLE", "LoRa"],
    },
}


class SkillOntology:
    """IT Skills Knowledge Graph for context-aware matching."""

    def __init__(self):
        # skill -> category
        self.skill_to_category: dict[str, str] = {}
        # skill -> subcategory
        self.skill_to_subcategory: dict[str, str] = {}
        # category -> [skills]
        self.category_skills: dict[str, list[str]] = defaultdict(list)
        # subcategory -> [skills]
        self.subcategory_skills: dict[str, list[str]] = defaultdict(list)
        # skill -> [related skills in same subcategory]
        self.related_skills: dict[str, list[str]] = defaultdict(list)

        self._build_index()

    def _build_index(self):
        """Build reverse indexes from the ontology tree."""
        for category, subcategories in SKILL_ONTOLOGY.items():
            for subcategory, skills in subcategories.items():
                for skill in skills:
                    skill_lower = skill.lower()
                    self.skill_to_category[skill_lower] = category
                    self.skill_to_subcategory[skill_lower] = subcategory
                    self.category_skills[category].append(skill)
                    self.subcategory_skills[subcategory].append(skill)

                # Build related skills (same subcategory = substitutable)
                for skill in skills:
                    skill_lower = skill.lower()
                    self.related_skills[skill_lower] = [
                        s for s in skills if s.lower() != skill_lower
                    ]

        logger.info(
            f"Ontology loaded: {len(self.skill_to_category)} skills, "
            f"{len(SKILL_ONTOLOGY)} categories"
        )

    def get_category(self, skill: str) -> Optional[str]:
        """Get the top-level category of a skill."""
        return self.skill_to_category.get(skill.lower())

    def get_subcategory(self, skill: str) -> Optional[str]:
        """Get the subcategory of a skill."""
        return self.skill_to_subcategory.get(skill.lower())

    def get_related(self, skill: str) -> list[str]:
        """Get skills that are substitutable (same subcategory)."""
        return self.related_skills.get(skill.lower(), [])

    def get_category_skills(self, category: str) -> list[str]:
        """Get all skills in a category."""
        return self.category_skills.get(category, [])

    def get_hierarchy(self, skill: str) -> Optional[dict]:
        """Get full hierarchy path: skill -> subcategory -> category."""
        skill_lower = skill.lower()
        cat = self.skill_to_category.get(skill_lower)
        subcat = self.skill_to_subcategory.get(skill_lower)
        if cat:
            return {
                "skill": skill,
                "subcategory": subcat,
                "category": cat,
                "related": self.related_skills.get(skill_lower, [])[:5],
            }
        return None

    def skill_distance(self, skill_a: str, skill_b: str) -> float:
        """
        Calculate ontological distance between two skills.
        Returns 0.0 (identical) to 1.0 (unrelated).

        Distance levels:
        - 0.0: Same skill
        - 0.2: Same subcategory (e.g., React <-> Vue.js)
        - 0.5: Same category (e.g., React <-> Webpack)
        - 0.8: Different category but tech-related
        - 1.0: Unknown/no relation
        """
        a_lower = skill_a.lower()
        b_lower = skill_b.lower()

        if a_lower == b_lower:
            return 0.0

        subcat_a = self.skill_to_subcategory.get(a_lower)
        subcat_b = self.skill_to_subcategory.get(b_lower)

        if subcat_a and subcat_b and subcat_a == subcat_b:
            return 0.2

        cat_a = self.skill_to_category.get(a_lower)
        cat_b = self.skill_to_category.get(b_lower)

        if cat_a and cat_b and cat_a == cat_b:
            return 0.5

        if cat_a and cat_b:
            return 0.8

        return 1.0

    def explain_relationship(self, skill_a: str, skill_b: str) -> str:
        """Generate human-readable explanation of skill relationship."""
        distance = self.skill_distance(skill_a, skill_b)

        if distance == 0.0:
            return f"'{skill_a}' and '{skill_b}' are the same skill."
        elif distance == 0.2:
            subcat = self.skill_to_subcategory.get(skill_a.lower(), "")
            return (
                f"'{skill_a}' and '{skill_b}' are closely related "
                f"(both are {subcat} technologies). They are often substitutable."
            )
        elif distance == 0.5:
            cat = self.skill_to_category.get(skill_a.lower(), "")
            return (
                f"'{skill_a}' and '{skill_b}' belong to the same domain "
                f"({cat}), but serve different purposes."
            )
        elif distance == 0.8:
            cat_a = self.skill_to_category.get(skill_a.lower(), "Unknown")
            cat_b = self.skill_to_category.get(skill_b.lower(), "Unknown")
            return (
                f"'{skill_a}' ({cat_a}) and '{skill_b}' ({cat_b}) "
                f"are from different domains."
            )
        else:
            return f"No known relationship between '{skill_a}' and '{skill_b}'."

    def categorize_skills(self, skills: list[str]) -> dict[str, list[str]]:
        """Group a list of skills by their top-level category."""
        result: dict[str, list[str]] = defaultdict(list)
        for skill in skills:
            cat = self.get_category(skill)
            if cat:
                result[cat].append(skill)
            else:
                result["Other"].append(skill)
        return dict(result)

    def get_all_categories(self) -> list[str]:
        """Return all top-level categories."""
        return list(SKILL_ONTOLOGY.keys())

    def get_subcategories(self, category: str) -> list[str]:
        """Return all subcategories under a category."""
        return list(SKILL_ONTOLOGY.get(category, {}).keys())
