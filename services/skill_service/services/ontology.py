"""
US-04: Skill Ontology & Knowledge Graph.
Full knowledge graph with 500+ IT skill nodes and 4 relationship types:
- REQUIRES: prerequisite skills (React REQUIRES JavaScript)
- RELATED_TO: substitutable / similar skills (React RELATED_TO Vue.js)
- PART_OF: belongs to a domain (React PART_OF Frontend Development)
- LEADS_TO: career/skill progression (React LEADS_TO Next.js)
"""

import logging
from typing import Optional
from collections import defaultdict

logger = logging.getLogger(__name__)


# ─── Relationship Types ────────────────────────────────────────────────────────

REQUIRES = "REQUIRES"
RELATED_TO = "RELATED_TO"
PART_OF = "PART_OF"
LEADS_TO = "LEADS_TO"


# ─── Skill Level Definitions ──────────────────────────────────────────────────

LEVELS = {
    "beginner": 1,
    "intermediate": 2,
    "advanced": 3,
    "expert": 4,
}


# ─── IT Skills Hierarchy (Ontology) ───────────────────────────────────────────

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


# ─── Explicit Relationship Edges ──────────────────────────────────────────────
# Format: (source_skill, relationship_type, target_skill)
# These are directional: "React REQUIRES JavaScript" means React needs JavaScript

SKILL_RELATIONSHIPS: list[tuple[str, str, str]] = [
    # ── Frontend REQUIRES ──
    ("React", REQUIRES, "JavaScript"),
    ("React", REQUIRES, "HTML"),
    ("React", REQUIRES, "CSS"),
    ("Angular", REQUIRES, "TypeScript"),
    ("Angular", REQUIRES, "HTML"),
    ("Angular", REQUIRES, "CSS"),
    ("Vue.js", REQUIRES, "JavaScript"),
    ("Vue.js", REQUIRES, "HTML"),
    ("Vue.js", REQUIRES, "CSS"),
    ("Svelte", REQUIRES, "JavaScript"),
    ("Svelte", REQUIRES, "HTML"),
    ("SolidJS", REQUIRES, "JavaScript"),
    ("Next.js", REQUIRES, "React"),
    ("Next.js", REQUIRES, "Node.js"),
    ("Nuxt.js", REQUIRES, "Vue.js"),
    ("Nuxt.js", REQUIRES, "Node.js"),
    ("Gatsby", REQUIRES, "React"),
    ("Remix", REQUIRES, "React"),
    ("Astro", REQUIRES, "JavaScript"),
    ("Redux", REQUIRES, "React"),
    ("Vuex", REQUIRES, "Vue.js"),
    ("Pinia", REQUIRES, "Vue.js"),
    ("NgRx", REQUIRES, "Angular"),
    ("MobX", REQUIRES, "JavaScript"),
    ("Zustand", REQUIRES, "React"),
    ("Recoil", REQUIRES, "React"),
    ("TypeScript", REQUIRES, "JavaScript"),
    ("Tailwind CSS", REQUIRES, "CSS"),
    ("SASS", REQUIRES, "CSS"),
    ("SCSS", REQUIRES, "CSS"),
    ("Less", REQUIRES, "CSS"),
    ("Bootstrap", REQUIRES, "CSS"),
    ("Material UI", REQUIRES, "React"),
    ("Styled Components", REQUIRES, "React"),
    ("Styled Components", REQUIRES, "CSS"),
    ("Webpack", REQUIRES, "JavaScript"),
    ("Vite", REQUIRES, "JavaScript"),
    ("Babel", REQUIRES, "JavaScript"),
    ("Jest", REQUIRES, "JavaScript"),
    ("Cypress", REQUIRES, "JavaScript"),
    ("Playwright", REQUIRES, "JavaScript"),
    ("Storybook", REQUIRES, "React"),
    ("Vitest", REQUIRES, "JavaScript"),

    # ── Backend REQUIRES ──
    ("Node.js", REQUIRES, "JavaScript"),
    ("Express.js", REQUIRES, "Node.js"),
    ("NestJS", REQUIRES, "Node.js"),
    ("NestJS", REQUIRES, "TypeScript"),
    ("Fastify", REQUIRES, "Node.js"),
    ("Koa", REQUIRES, "Node.js"),
    ("Django", REQUIRES, "Python"),
    ("Flask", REQUIRES, "Python"),
    ("FastAPI", REQUIRES, "Python"),
    ("Tornado", REQUIRES, "Python"),
    ("Sanic", REQUIRES, "Python"),
    ("aiohttp", REQUIRES, "Python"),
    ("Spring Boot", REQUIRES, "Java"),
    ("Spring", REQUIRES, "Java"),
    ("Quarkus", REQUIRES, "Java"),
    ("Micronaut", REQUIRES, "Java"),
    ("ASP.NET", REQUIRES, "C#"),
    ("ASP.NET Core", REQUIRES, "C#"),
    (".NET", REQUIRES, "C#"),
    ("Entity Framework", REQUIRES, "C#"),
    ("Blazor", REQUIRES, "C#"),
    ("Gin", REQUIRES, "Go"),
    ("Fiber", REQUIRES, "Go"),
    ("Echo", REQUIRES, "Go"),
    ("Chi", REQUIRES, "Go"),
    ("Ruby on Rails", REQUIRES, "Ruby"),
    ("Sinatra", REQUIRES, "Ruby"),
    ("Laravel", REQUIRES, "PHP"),
    ("Symfony", REQUIRES, "PHP"),
    ("CodeIgniter", REQUIRES, "PHP"),
    ("GraphQL", REQUIRES, "REST"),
    ("gRPC", REQUIRES, "REST"),
    ("tRPC", REQUIRES, "TypeScript"),

    # ── Database REQUIRES ──
    ("PostgreSQL", REQUIRES, "SQL"),
    ("MySQL", REQUIRES, "SQL"),
    ("MariaDB", REQUIRES, "SQL"),
    ("SQL Server", REQUIRES, "SQL"),
    ("Oracle", REQUIRES, "SQL"),
    ("SQLite", REQUIRES, "SQL"),
    ("CockroachDB", REQUIRES, "SQL"),

    # ── DevOps REQUIRES ──
    ("Kubernetes", REQUIRES, "Docker"),
    ("Docker Swarm", REQUIRES, "Docker"),
    ("Helm", REQUIRES, "Kubernetes"),
    ("Kustomize", REQUIRES, "Kubernetes"),
    ("Istio", REQUIRES, "Kubernetes"),
    ("Linkerd", REQUIRES, "Kubernetes"),
    ("Amazon ECS", REQUIRES, "Docker"),
    ("Amazon EKS", REQUIRES, "Kubernetes"),
    ("ArgoCD", REQUIRES, "Kubernetes"),
    ("ArgoCD", REQUIRES, "Git"),
    ("Terraform", REQUIRES, "Cloud Platforms"),
    ("Pulumi", REQUIRES, "Cloud Platforms"),
    ("AWS CDK", REQUIRES, "AWS"),
    ("CloudFormation", REQUIRES, "AWS"),
    ("Ansible", REQUIRES, "Linux"),
    ("GitHub Actions", REQUIRES, "Git"),
    ("GitLab CI/CD", REQUIRES, "Git"),

    # ── Data Engineering REQUIRES ──
    ("PySpark", REQUIRES, "Python"),
    ("PySpark", REQUIRES, "Apache Spark"),
    ("Apache Spark", REQUIRES, "SQL"),
    ("Apache Airflow", REQUIRES, "Python"),
    ("dbt", REQUIRES, "SQL"),
    ("Kafka Streams", REQUIRES, "Apache Kafka"),

    # ── ML/AI REQUIRES ──
    ("TensorFlow", REQUIRES, "Python"),
    ("PyTorch", REQUIRES, "Python"),
    ("Keras", REQUIRES, "Python"),
    ("Keras", REQUIRES, "TensorFlow"),
    ("JAX", REQUIRES, "Python"),
    ("Scikit-learn", REQUIRES, "Python"),
    ("Scikit-learn", REQUIRES, "NumPy"),
    ("Pandas", REQUIRES, "Python"),
    ("NumPy", REQUIRES, "Python"),
    ("Hugging Face", REQUIRES, "Python"),
    ("Hugging Face", REQUIRES, "PyTorch"),
    ("spaCy", REQUIRES, "Python"),
    ("NLTK", REQUIRES, "Python"),
    ("LangChain", REQUIRES, "Python"),
    ("OpenCV", REQUIRES, "Python"),
    ("MLflow", REQUIRES, "Python"),
    ("Kubeflow", REQUIRES, "Kubernetes"),
    ("XGBoost", REQUIRES, "Python"),
    ("LightGBM", REQUIRES, "Python"),
    ("Matplotlib", REQUIRES, "Python"),
    ("Seaborn", REQUIRES, "Python"),
    ("Seaborn", REQUIRES, "Matplotlib"),

    # ── Mobile REQUIRES ──
    ("React Native", REQUIRES, "React"),
    ("React Native", REQUIRES, "JavaScript"),
    ("Flutter", REQUIRES, "Dart"),
    ("Xamarin", REQUIRES, "C#"),
    ("Jetpack Compose", REQUIRES, "Kotlin"),
    ("SwiftUI", REQUIRES, "Swift"),
    ("MAUI", REQUIRES, "C#"),

    # ── Blockchain REQUIRES ──
    ("Solidity", REQUIRES, "JavaScript"),
    ("Web3.js", REQUIRES, "JavaScript"),
    ("Ethers.js", REQUIRES, "JavaScript"),
    ("Hardhat", REQUIRES, "JavaScript"),
    ("Truffle", REQUIRES, "JavaScript"),

    # ── Embedded REQUIRES ──
    ("Arduino", REQUIRES, "C"),
    ("ESP32", REQUIRES, "C"),
    ("FreeRTOS", REQUIRES, "C"),

    # ── RELATED_TO (substitutable/similar) ──
    ("React", RELATED_TO, "Vue.js"),
    ("React", RELATED_TO, "Angular"),
    ("React", RELATED_TO, "Svelte"),
    ("Vue.js", RELATED_TO, "Angular"),
    ("Vue.js", RELATED_TO, "Svelte"),
    ("Angular", RELATED_TO, "Svelte"),
    ("Next.js", RELATED_TO, "Nuxt.js"),
    ("Next.js", RELATED_TO, "Gatsby"),
    ("Next.js", RELATED_TO, "Remix"),
    ("Redux", RELATED_TO, "Zustand"),
    ("Redux", RELATED_TO, "MobX"),
    ("Vuex", RELATED_TO, "Pinia"),
    ("Webpack", RELATED_TO, "Vite"),
    ("Webpack", RELATED_TO, "Rollup"),
    ("Vite", RELATED_TO, "ESBuild"),
    ("Tailwind CSS", RELATED_TO, "Bootstrap"),
    ("SASS", RELATED_TO, "Less"),
    ("Express.js", RELATED_TO, "Fastify"),
    ("Express.js", RELATED_TO, "Koa"),
    ("NestJS", RELATED_TO, "Express.js"),
    ("Django", RELATED_TO, "Flask"),
    ("Django", RELATED_TO, "FastAPI"),
    ("Flask", RELATED_TO, "FastAPI"),
    ("Spring Boot", RELATED_TO, "Quarkus"),
    ("Spring Boot", RELATED_TO, "Micronaut"),
    ("ASP.NET Core", RELATED_TO, "Spring Boot"),
    ("Gin", RELATED_TO, "Fiber"),
    ("Gin", RELATED_TO, "Echo"),
    ("Ruby on Rails", RELATED_TO, "Django"),
    ("Laravel", RELATED_TO, "Symfony"),
    ("Laravel", RELATED_TO, "Ruby on Rails"),
    ("REST", RELATED_TO, "GraphQL"),
    ("REST", RELATED_TO, "gRPC"),
    ("GraphQL", RELATED_TO, "gRPC"),
    ("RabbitMQ", RELATED_TO, "Apache Kafka"),
    ("RabbitMQ", RELATED_TO, "Amazon SQS"),
    ("Apache Kafka", RELATED_TO, "Amazon SQS"),
    ("PostgreSQL", RELATED_TO, "MySQL"),
    ("PostgreSQL", RELATED_TO, "MariaDB"),
    ("MySQL", RELATED_TO, "MariaDB"),
    ("SQL Server", RELATED_TO, "Oracle"),
    ("MongoDB", RELATED_TO, "CouchDB"),
    ("MongoDB", RELATED_TO, "Firebase Firestore"),
    ("Redis", RELATED_TO, "Memcached"),
    ("Redis", RELATED_TO, "DynamoDB"),
    ("Elasticsearch", RELATED_TO, "OpenSearch"),
    ("Elasticsearch", RELATED_TO, "Solr"),
    ("Neo4j", RELATED_TO, "ArangoDB"),
    ("Docker", RELATED_TO, "Podman"),
    ("Kubernetes", RELATED_TO, "Docker Swarm"),
    ("Kubernetes", RELATED_TO, "Nomad"),
    ("Terraform", RELATED_TO, "Pulumi"),
    ("Terraform", RELATED_TO, "CloudFormation"),
    ("Ansible", RELATED_TO, "Puppet"),
    ("Ansible", RELATED_TO, "Chef"),
    ("AWS", RELATED_TO, "Azure"),
    ("AWS", RELATED_TO, "GCP"),
    ("Azure", RELATED_TO, "GCP"),
    ("Jenkins", RELATED_TO, "GitHub Actions"),
    ("Jenkins", RELATED_TO, "GitLab CI/CD"),
    ("GitHub Actions", RELATED_TO, "GitLab CI/CD"),
    ("CircleCI", RELATED_TO, "Travis CI"),
    ("Prometheus", RELATED_TO, "Datadog"),
    ("Grafana", RELATED_TO, "Datadog"),
    ("Prometheus", RELATED_TO, "New Relic"),
    ("Nginx", RELATED_TO, "Apache"),
    ("Nginx", RELATED_TO, "Caddy"),
    ("HAProxy", RELATED_TO, "Traefik"),
    ("TensorFlow", RELATED_TO, "PyTorch"),
    ("TensorFlow", RELATED_TO, "JAX"),
    ("PyTorch", RELATED_TO, "JAX"),
    ("Scikit-learn", RELATED_TO, "XGBoost"),
    ("XGBoost", RELATED_TO, "LightGBM"),
    ("XGBoost", RELATED_TO, "CatBoost"),
    ("spaCy", RELATED_TO, "NLTK"),
    ("Hugging Face", RELATED_TO, "LangChain"),
    ("MLflow", RELATED_TO, "Kubeflow"),
    ("SageMaker", RELATED_TO, "Vertex AI"),
    ("Apache Spark", RELATED_TO, "Apache Flink"),
    ("Apache Airflow", RELATED_TO, "Prefect"),
    ("Apache Airflow", RELATED_TO, "Dagster"),
    ("Snowflake", RELATED_TO, "BigQuery"),
    ("Snowflake", RELATED_TO, "Redshift"),
    ("BigQuery", RELATED_TO, "Redshift"),
    ("Tableau", RELATED_TO, "Power BI"),
    ("Tableau", RELATED_TO, "Looker"),
    ("dbt", RELATED_TO, "Fivetran"),
    ("React Native", RELATED_TO, "Flutter"),
    ("React Native", RELATED_TO, "Xamarin"),
    ("Flutter", RELATED_TO, "MAUI"),
    ("Jetpack Compose", RELATED_TO, "SwiftUI"),
    ("Android", RELATED_TO, "iOS"),
    ("Unity", RELATED_TO, "Unreal Engine"),
    ("Unity", RELATED_TO, "Godot"),
    ("OpenGL", RELATED_TO, "Vulkan"),
    ("OpenGL", RELATED_TO, "DirectX"),
    ("Ethereum", RELATED_TO, "Solana"),
    ("Ethereum", RELATED_TO, "Polygon"),
    ("Web3.js", RELATED_TO, "Ethers.js"),
    ("Hardhat", RELATED_TO, "Truffle"),
    ("Hardhat", RELATED_TO, "Foundry"),
    ("Jest", RELATED_TO, "Mocha"),
    ("Jest", RELATED_TO, "Vitest"),
    ("JUnit", RELATED_TO, "TestNG"),
    ("pytest", RELATED_TO, "JUnit"),
    ("Selenium", RELATED_TO, "Cypress"),
    ("Selenium", RELATED_TO, "Playwright"),
    ("Cypress", RELATED_TO, "Playwright"),
    ("JMeter", RELATED_TO, "Gatling"),
    ("JMeter", RELATED_TO, "k6"),
    ("Postman", RELATED_TO, "Insomnia"),
    ("Python", RELATED_TO, "Ruby"),
    ("Java", RELATED_TO, "C#"),
    ("Java", RELATED_TO, "Kotlin"),
    ("C", RELATED_TO, "C++"),
    ("Go", RELATED_TO, "Rust"),
    ("JavaScript", RELATED_TO, "TypeScript"),
    ("Git", RELATED_TO, "SVN"),
    ("GitHub", RELATED_TO, "GitLab"),
    ("GitHub", RELATED_TO, "Bitbucket"),
    ("Jira", RELATED_TO, "Linear"),
    ("Jira", RELATED_TO, "Asana"),
    ("OAuth", RELATED_TO, "SAML"),
    ("OAuth 2.0", RELATED_TO, "OpenID Connect"),
    ("JWT", RELATED_TO, "OAuth 2.0"),
    ("Arduino", RELATED_TO, "Raspberry Pi"),
    ("Arduino", RELATED_TO, "ESP32"),
    ("MQTT", RELATED_TO, "CoAP"),
    ("FreeRTOS", RELATED_TO, "Zephyr"),
    ("Agile", RELATED_TO, "Scrum"),
    ("Scrum", RELATED_TO, "Kanban"),
    ("TDD", RELATED_TO, "BDD"),
    ("Microservices", RELATED_TO, "Monolith"),
    ("CQRS", RELATED_TO, "Event-Driven"),
    ("DDD", RELATED_TO, "Hexagonal"),

    # ── PART_OF (domain membership) ──
    ("React", PART_OF, "Frontend Development"),
    ("Angular", PART_OF, "Frontend Development"),
    ("Vue.js", PART_OF, "Frontend Development"),
    ("Svelte", PART_OF, "Frontend Development"),
    ("Next.js", PART_OF, "Frontend Development"),
    ("HTML", PART_OF, "Frontend Development"),
    ("CSS", PART_OF, "Frontend Development"),
    ("JavaScript", PART_OF, "Web Development"),
    ("TypeScript", PART_OF, "Web Development"),
    ("Node.js", PART_OF, "Backend Development"),
    ("Django", PART_OF, "Backend Development"),
    ("Flask", PART_OF, "Backend Development"),
    ("FastAPI", PART_OF, "Backend Development"),
    ("Spring Boot", PART_OF, "Backend Development"),
    ("ASP.NET Core", PART_OF, "Backend Development"),
    ("Express.js", PART_OF, "Backend Development"),
    ("NestJS", PART_OF, "Backend Development"),
    ("PostgreSQL", PART_OF, "Data Management"),
    ("MongoDB", PART_OF, "Data Management"),
    ("Redis", PART_OF, "Data Management"),
    ("Docker", PART_OF, "DevOps"),
    ("Kubernetes", PART_OF, "DevOps"),
    ("Terraform", PART_OF, "DevOps"),
    ("AWS", PART_OF, "Cloud Computing"),
    ("Azure", PART_OF, "Cloud Computing"),
    ("GCP", PART_OF, "Cloud Computing"),
    ("TensorFlow", PART_OF, "Machine Learning"),
    ("PyTorch", PART_OF, "Machine Learning"),
    ("Scikit-learn", PART_OF, "Machine Learning"),
    ("Hugging Face", PART_OF, "NLP"),
    ("spaCy", PART_OF, "NLP"),
    ("BERT", PART_OF, "NLP"),
    ("GPT", PART_OF, "NLP"),
    ("OpenCV", PART_OF, "Computer Vision"),
    ("YOLO", PART_OF, "Computer Vision"),
    ("React Native", PART_OF, "Mobile Development"),
    ("Flutter", PART_OF, "Mobile Development"),
    ("Swift", PART_OF, "iOS Development"),
    ("Kotlin", PART_OF, "Android Development"),
    ("Apache Spark", PART_OF, "Data Engineering"),
    ("Apache Airflow", PART_OF, "Data Engineering"),
    ("Apache Kafka", PART_OF, "Data Streaming"),
    ("Solidity", PART_OF, "Blockchain Development"),
    ("Ethereum", PART_OF, "Blockchain Development"),
    ("Unity", PART_OF, "Game Development"),
    ("Unreal Engine", PART_OF, "Game Development"),
    ("Arduino", PART_OF, "Embedded Systems"),
    ("MQTT", PART_OF, "IoT"),
    ("Git", PART_OF, "Version Control"),
    ("Agile", PART_OF, "Project Management"),
    ("Scrum", PART_OF, "Project Management"),
    ("Microservices", PART_OF, "Software Architecture"),
    ("CI/CD", PART_OF, "DevOps"),
    ("Jenkins", PART_OF, "DevOps"),
    ("GitHub Actions", PART_OF, "DevOps"),

    # ── LEADS_TO (progression/career path) ──
    ("HTML", LEADS_TO, "CSS"),
    ("CSS", LEADS_TO, "JavaScript"),
    ("JavaScript", LEADS_TO, "TypeScript"),
    ("JavaScript", LEADS_TO, "React"),
    ("JavaScript", LEADS_TO, "Vue.js"),
    ("JavaScript", LEADS_TO, "Angular"),
    ("JavaScript", LEADS_TO, "Node.js"),
    ("React", LEADS_TO, "Next.js"),
    ("React", LEADS_TO, "React Native"),
    ("React", LEADS_TO, "Redux"),
    ("Vue.js", LEADS_TO, "Nuxt.js"),
    ("Angular", LEADS_TO, "NgRx"),
    ("TypeScript", LEADS_TO, "NestJS"),
    ("Node.js", LEADS_TO, "Express.js"),
    ("Node.js", LEADS_TO, "NestJS"),
    ("Python", LEADS_TO, "Django"),
    ("Python", LEADS_TO, "Flask"),
    ("Python", LEADS_TO, "FastAPI"),
    ("Python", LEADS_TO, "TensorFlow"),
    ("Python", LEADS_TO, "PyTorch"),
    ("Python", LEADS_TO, "Pandas"),
    ("Python", LEADS_TO, "Apache Airflow"),
    ("Java", LEADS_TO, "Spring Boot"),
    ("Java", LEADS_TO, "Kotlin"),
    ("C#", LEADS_TO, "ASP.NET Core"),
    ("C#", LEADS_TO, ".NET"),
    ("Go", LEADS_TO, "Gin"),
    ("Go", LEADS_TO, "Kubernetes"),
    ("Ruby", LEADS_TO, "Ruby on Rails"),
    ("PHP", LEADS_TO, "Laravel"),
    ("SQL", LEADS_TO, "PostgreSQL"),
    ("SQL", LEADS_TO, "MySQL"),
    ("SQL", LEADS_TO, "dbt"),
    ("Docker", LEADS_TO, "Kubernetes"),
    ("Docker", LEADS_TO, "Docker Swarm"),
    ("Kubernetes", LEADS_TO, "Helm"),
    ("Kubernetes", LEADS_TO, "Istio"),
    ("Kubernetes", LEADS_TO, "ArgoCD"),
    ("Linux", LEADS_TO, "Docker"),
    ("Linux", LEADS_TO, "Ansible"),
    ("Linux", LEADS_TO, "Bash"),
    ("Git", LEADS_TO, "GitHub Actions"),
    ("Git", LEADS_TO, "GitLab CI/CD"),
    ("AWS", LEADS_TO, "Terraform"),
    ("AWS", LEADS_TO, "CloudFormation"),
    ("AWS", LEADS_TO, "Amazon EKS"),
    ("Terraform", LEADS_TO, "Pulumi"),
    ("REST", LEADS_TO, "GraphQL"),
    ("REST", LEADS_TO, "gRPC"),
    ("NumPy", LEADS_TO, "Pandas"),
    ("Pandas", LEADS_TO, "Scikit-learn"),
    ("Scikit-learn", LEADS_TO, "TensorFlow"),
    ("Scikit-learn", LEADS_TO, "PyTorch"),
    ("Scikit-learn", LEADS_TO, "XGBoost"),
    ("TensorFlow", LEADS_TO, "Keras"),
    ("PyTorch", LEADS_TO, "Hugging Face"),
    ("PyTorch", LEADS_TO, "YOLO"),
    ("Hugging Face", LEADS_TO, "LangChain"),
    ("Apache Spark", LEADS_TO, "PySpark"),
    ("Apache Kafka", LEADS_TO, "Kafka Streams"),
    ("Snowflake", LEADS_TO, "dbt"),
    ("Dart", LEADS_TO, "Flutter"),
    ("Swift", LEADS_TO, "SwiftUI"),
    ("Kotlin", LEADS_TO, "Jetpack Compose"),
    ("C", LEADS_TO, "C++"),
    ("C", LEADS_TO, "Rust"),
    ("C++", LEADS_TO, "Rust"),
    ("Solidity", LEADS_TO, "Hardhat"),
    ("Ethereum", LEADS_TO, "Polygon"),
    ("C", LEADS_TO, "Arduino"),
    ("Arduino", LEADS_TO, "ESP32"),
    ("MQTT", LEADS_TO, "BLE"),

    # ── Career path LEADS_TO ──
    ("React", LEADS_TO, "Full-Stack Development"),
    ("Node.js", LEADS_TO, "Full-Stack Development"),
    ("Django", LEADS_TO, "Full-Stack Development"),
    ("Docker", LEADS_TO, "DevOps Engineering"),
    ("Kubernetes", LEADS_TO, "DevOps Engineering"),
    ("AWS", LEADS_TO, "Cloud Architecture"),
    ("TensorFlow", LEADS_TO, "ML Engineering"),
    ("PyTorch", LEADS_TO, "ML Engineering"),
    ("Apache Spark", LEADS_TO, "Data Engineering"),
    ("React Native", LEADS_TO, "Mobile Engineering"),
    ("Flutter", LEADS_TO, "Mobile Engineering"),
    ("Solidity", LEADS_TO, "Blockchain Engineering"),
    ("Microservices", LEADS_TO, "Software Architecture"),
]


# ─── Skill Metadata (level range, description, demand) ────────────────────────
# Key skills with additional metadata. Skills not listed default to intermediate.

SKILL_METADATA: dict[str, dict] = {
    "Python": {"levels": ["beginner", "expert"], "demand": 0.95, "trending": True, "description": "General-purpose programming language, widely used in web, data science, and AI"},
    "JavaScript": {"levels": ["beginner", "expert"], "demand": 0.96, "trending": True, "description": "The language of the web, runs in browsers and on servers via Node.js"},
    "TypeScript": {"levels": ["intermediate", "expert"], "demand": 0.90, "trending": True, "description": "Typed superset of JavaScript for large-scale applications"},
    "Java": {"levels": ["beginner", "expert"], "demand": 0.85, "trending": False, "description": "Enterprise-grade language for backend and Android development"},
    "C#": {"levels": ["beginner", "expert"], "demand": 0.80, "trending": False, "description": "Microsoft's language for .NET, Unity, and enterprise applications"},
    "Go": {"levels": ["intermediate", "advanced"], "demand": 0.78, "trending": True, "description": "Fast, simple language for cloud-native and systems programming"},
    "Rust": {"levels": ["intermediate", "expert"], "demand": 0.72, "trending": True, "description": "Memory-safe systems language for performance-critical applications"},
    "C": {"levels": ["beginner", "expert"], "demand": 0.60, "trending": False, "description": "Low-level language for systems programming and embedded systems"},
    "C++": {"levels": ["intermediate", "expert"], "demand": 0.65, "trending": False, "description": "High-performance language for games, systems, and HPC"},
    "Kotlin": {"levels": ["intermediate", "advanced"], "demand": 0.75, "trending": True, "description": "Modern JVM language, primary for Android development"},
    "Swift": {"levels": ["intermediate", "advanced"], "demand": 0.70, "trending": False, "description": "Apple's language for iOS, macOS, and other Apple platforms"},
    "Ruby": {"levels": ["beginner", "advanced"], "demand": 0.55, "trending": False, "description": "Elegant language known for Ruby on Rails web framework"},
    "PHP": {"levels": ["beginner", "advanced"], "demand": 0.60, "trending": False, "description": "Server-side scripting language powering much of the web"},
    "SQL": {"levels": ["beginner", "advanced"], "demand": 0.90, "trending": False, "description": "Standard language for relational database queries"},
    "R": {"levels": ["intermediate", "advanced"], "demand": 0.55, "trending": False, "description": "Statistical computing language for data analysis"},
    "Dart": {"levels": ["intermediate", "advanced"], "demand": 0.65, "trending": True, "description": "Language optimized for building UIs, used with Flutter"},
    "Scala": {"levels": ["advanced", "expert"], "demand": 0.50, "trending": False, "description": "JVM language combining OOP and functional programming"},

    # Frontend
    "React": {"levels": ["intermediate", "expert"], "demand": 0.94, "trending": True, "description": "JavaScript library for building component-based user interfaces"},
    "Angular": {"levels": ["intermediate", "advanced"], "demand": 0.72, "trending": False, "description": "Full-featured framework for enterprise web applications"},
    "Vue.js": {"levels": ["intermediate", "advanced"], "demand": 0.75, "trending": True, "description": "Progressive JavaScript framework for building UIs"},
    "Svelte": {"levels": ["intermediate", "advanced"], "demand": 0.60, "trending": True, "description": "Compile-time framework with minimal runtime overhead"},
    "Next.js": {"levels": ["intermediate", "advanced"], "demand": 0.88, "trending": True, "description": "React meta-framework for SSR, SSG, and full-stack apps"},
    "Nuxt.js": {"levels": ["intermediate", "advanced"], "demand": 0.60, "trending": True, "description": "Vue.js meta-framework for SSR and static sites"},
    "Tailwind CSS": {"levels": ["beginner", "intermediate"], "demand": 0.85, "trending": True, "description": "Utility-first CSS framework for rapid UI development"},
    "Redux": {"levels": ["intermediate", "advanced"], "demand": 0.70, "trending": False, "description": "Predictable state container for JavaScript apps"},
    "HTML": {"levels": ["beginner", "intermediate"], "demand": 0.90, "trending": False, "description": "Standard markup language for web pages"},
    "CSS": {"levels": ["beginner", "advanced"], "demand": 0.90, "trending": False, "description": "Style sheet language for web page presentation"},

    # Backend
    "Node.js": {"levels": ["intermediate", "advanced"], "demand": 0.88, "trending": True, "description": "JavaScript runtime for server-side development"},
    "Express.js": {"levels": ["intermediate", "advanced"], "demand": 0.80, "trending": False, "description": "Minimalist web framework for Node.js"},
    "NestJS": {"levels": ["intermediate", "advanced"], "demand": 0.75, "trending": True, "description": "Progressive Node.js framework with TypeScript support"},
    "Django": {"levels": ["intermediate", "advanced"], "demand": 0.78, "trending": False, "description": "Batteries-included Python web framework"},
    "Flask": {"levels": ["beginner", "advanced"], "demand": 0.72, "trending": False, "description": "Lightweight Python web microframework"},
    "FastAPI": {"levels": ["intermediate", "advanced"], "demand": 0.82, "trending": True, "description": "Modern, fast Python web framework for building APIs"},
    "Spring Boot": {"levels": ["intermediate", "expert"], "demand": 0.82, "trending": False, "description": "Java framework for production-ready applications"},
    "ASP.NET Core": {"levels": ["intermediate", "expert"], "demand": 0.75, "trending": False, "description": "Cross-platform .NET framework for web APIs"},
    "GraphQL": {"levels": ["intermediate", "advanced"], "demand": 0.72, "trending": True, "description": "Query language for APIs with flexible data fetching"},
    "REST": {"levels": ["beginner", "advanced"], "demand": 0.92, "trending": False, "description": "Architectural style for distributed systems APIs"},
    "gRPC": {"levels": ["advanced", "expert"], "demand": 0.65, "trending": True, "description": "High-performance RPC framework by Google"},

    # Database
    "PostgreSQL": {"levels": ["intermediate", "expert"], "demand": 0.88, "trending": True, "description": "Advanced open-source relational database"},
    "MySQL": {"levels": ["beginner", "advanced"], "demand": 0.80, "trending": False, "description": "Popular open-source relational database"},
    "MongoDB": {"levels": ["intermediate", "advanced"], "demand": 0.75, "trending": False, "description": "Document-oriented NoSQL database"},
    "Redis": {"levels": ["intermediate", "advanced"], "demand": 0.82, "trending": True, "description": "In-memory data store for caching and messaging"},
    "Elasticsearch": {"levels": ["intermediate", "expert"], "demand": 0.70, "trending": False, "description": "Distributed search and analytics engine"},
    "Neo4j": {"levels": ["intermediate", "advanced"], "demand": 0.50, "trending": True, "description": "Graph database for connected data"},

    # DevOps
    "Docker": {"levels": ["intermediate", "advanced"], "demand": 0.92, "trending": True, "description": "Container platform for consistent deployment"},
    "Kubernetes": {"levels": ["advanced", "expert"], "demand": 0.88, "trending": True, "description": "Container orchestration platform"},
    "Terraform": {"levels": ["intermediate", "expert"], "demand": 0.82, "trending": True, "description": "Infrastructure as Code tool for cloud provisioning"},
    "AWS": {"levels": ["intermediate", "expert"], "demand": 0.92, "trending": True, "description": "Amazon's comprehensive cloud computing platform"},
    "Azure": {"levels": ["intermediate", "expert"], "demand": 0.80, "trending": True, "description": "Microsoft's cloud computing platform"},
    "GCP": {"levels": ["intermediate", "expert"], "demand": 0.72, "trending": True, "description": "Google's cloud computing platform"},
    "Jenkins": {"levels": ["intermediate", "advanced"], "demand": 0.65, "trending": False, "description": "Open-source CI/CD automation server"},
    "GitHub Actions": {"levels": ["beginner", "advanced"], "demand": 0.80, "trending": True, "description": "CI/CD automation integrated with GitHub"},
    "Linux": {"levels": ["beginner", "expert"], "demand": 0.88, "trending": False, "description": "Open-source operating system family"},
    "Nginx": {"levels": ["intermediate", "advanced"], "demand": 0.75, "trending": False, "description": "High-performance web server and reverse proxy"},
    "Ansible": {"levels": ["intermediate", "advanced"], "demand": 0.70, "trending": False, "description": "Agentless IT automation tool"},
    "Prometheus": {"levels": ["intermediate", "advanced"], "demand": 0.72, "trending": True, "description": "Open-source monitoring and alerting toolkit"},
    "Grafana": {"levels": ["intermediate", "advanced"], "demand": 0.70, "trending": True, "description": "Open-source analytics and monitoring platform"},
    "ArgoCD": {"levels": ["advanced", "expert"], "demand": 0.65, "trending": True, "description": "Declarative GitOps continuous delivery for Kubernetes"},
    "Helm": {"levels": ["intermediate", "advanced"], "demand": 0.70, "trending": True, "description": "Package manager for Kubernetes"},

    # ML/AI
    "TensorFlow": {"levels": ["intermediate", "expert"], "demand": 0.80, "trending": False, "description": "Google's end-to-end ML platform"},
    "PyTorch": {"levels": ["intermediate", "expert"], "demand": 0.85, "trending": True, "description": "Facebook's deep learning framework, popular in research"},
    "Scikit-learn": {"levels": ["intermediate", "advanced"], "demand": 0.78, "trending": False, "description": "Python library for classical machine learning"},
    "Pandas": {"levels": ["beginner", "advanced"], "demand": 0.85, "trending": False, "description": "Data manipulation and analysis library for Python"},
    "NumPy": {"levels": ["beginner", "advanced"], "demand": 0.82, "trending": False, "description": "Fundamental package for numerical computing in Python"},
    "Hugging Face": {"levels": ["intermediate", "expert"], "demand": 0.80, "trending": True, "description": "Platform and library for state-of-the-art NLP models"},
    "LangChain": {"levels": ["intermediate", "advanced"], "demand": 0.78, "trending": True, "description": "Framework for building LLM-powered applications"},
    "OpenCV": {"levels": ["intermediate", "expert"], "demand": 0.65, "trending": False, "description": "Computer vision and image processing library"},
    "MLflow": {"levels": ["intermediate", "advanced"], "demand": 0.68, "trending": True, "description": "Platform for ML experiment tracking and deployment"},

    # Data Engineering
    "Apache Spark": {"levels": ["advanced", "expert"], "demand": 0.75, "trending": False, "description": "Unified analytics engine for big data processing"},
    "Apache Kafka": {"levels": ["advanced", "expert"], "demand": 0.78, "trending": True, "description": "Distributed event streaming platform"},
    "Apache Airflow": {"levels": ["intermediate", "advanced"], "demand": 0.72, "trending": True, "description": "Platform to programmatically author, schedule workflows"},
    "Snowflake": {"levels": ["intermediate", "advanced"], "demand": 0.78, "trending": True, "description": "Cloud-native data warehouse platform"},
    "dbt": {"levels": ["intermediate", "advanced"], "demand": 0.75, "trending": True, "description": "Data transformation tool for analytics engineering"},
    "Tableau": {"levels": ["beginner", "advanced"], "demand": 0.70, "trending": False, "description": "Business intelligence and data visualization platform"},

    # Mobile
    "React Native": {"levels": ["intermediate", "advanced"], "demand": 0.78, "trending": True, "description": "Cross-platform mobile framework using React"},
    "Flutter": {"levels": ["intermediate", "advanced"], "demand": 0.80, "trending": True, "description": "Google's cross-platform UI toolkit"},

    # Misc
    "Git": {"levels": ["beginner", "advanced"], "demand": 0.95, "trending": False, "description": "Distributed version control system"},
    "Agile": {"levels": ["beginner", "advanced"], "demand": 0.80, "trending": False, "description": "Iterative approach to project management and software development"},
    "Microservices": {"levels": ["advanced", "expert"], "demand": 0.78, "trending": True, "description": "Architectural style that structures an app as a collection of services"},
    "CI/CD": {"levels": ["intermediate", "advanced"], "demand": 0.85, "trending": True, "description": "Continuous Integration and Continuous Delivery practices"},
}


class SkillOntology:
    """IT Skills Knowledge Graph for context-aware matching and exploration."""

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

        # Knowledge Graph edges: skill -> {rel_type: [target_skills]}
        self.graph_out: dict[str, dict[str, list[str]]] = defaultdict(lambda: defaultdict(list))
        # Reverse edges: skill -> {rel_type: [source_skills]}
        self.graph_in: dict[str, dict[str, list[str]]] = defaultdict(lambda: defaultdict(list))

        # All unique skill names (canonical form)
        self.all_skills: set[str] = set()
        # Lowercase -> canonical name mapping
        self.canonical: dict[str, str] = {}

        self._build_index()
        self._build_graph()

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
                    self.all_skills.add(skill)
                    self.canonical[skill_lower] = skill

                # Build related skills (same subcategory = substitutable)
                for skill in skills:
                    skill_lower = skill.lower()
                    self.related_skills[skill_lower] = [
                        s for s in skills if s.lower() != skill_lower
                    ]

        logger.info(
            f"Ontology loaded: {len(self.all_skills)} skills, "
            f"{len(SKILL_ONTOLOGY)} categories"
        )

    def _build_graph(self):
        """Build knowledge graph from explicit relationship edges."""
        for source, rel_type, target in SKILL_RELATIONSHIPS:
            src_lower = source.lower()
            tgt_lower = target.lower()
            self.graph_out[src_lower][rel_type].append(target)
            self.graph_in[tgt_lower][rel_type].append(source)
            # Ensure both nodes are tracked
            self.all_skills.add(source)
            self.all_skills.add(target)
            if src_lower not in self.canonical:
                self.canonical[src_lower] = source
            if tgt_lower not in self.canonical:
                self.canonical[tgt_lower] = target

        total_edges = sum(
            len(targets)
            for rels in self.graph_out.values()
            for targets in rels.values()
        )
        logger.info(f"Knowledge graph built: {len(self.all_skills)} nodes, {total_edges} edges")

    # ─── Basic Lookups ─────────────────────────────────────────────────

    def get_category(self, skill: str) -> Optional[str]:
        return self.skill_to_category.get(skill.lower())

    def get_subcategory(self, skill: str) -> Optional[str]:
        return self.skill_to_subcategory.get(skill.lower())

    def get_related(self, skill: str) -> list[str]:
        return self.related_skills.get(skill.lower(), [])

    def get_category_skills(self, category: str) -> list[str]:
        return self.category_skills.get(category, [])

    def get_all_categories(self) -> list[str]:
        return list(SKILL_ONTOLOGY.keys())

    def get_subcategories(self, category: str) -> list[str]:
        return list(SKILL_ONTOLOGY.get(category, {}).keys())

    # ─── Knowledge Graph Queries ───────────────────────────────────────

    def get_skill_node(self, skill: str) -> Optional[dict]:
        """Get full skill node with all relationships and metadata."""
        skill_lower = skill.lower()
        canonical_name = self.canonical.get(skill_lower)
        if not canonical_name and skill_lower not in self.skill_to_category:
            return None

        name = canonical_name or skill
        cat = self.skill_to_category.get(skill_lower)
        subcat = self.skill_to_subcategory.get(skill_lower)
        meta = SKILL_METADATA.get(name, {})

        # Collect outgoing relationships
        relationships = {}
        for rel_type in [REQUIRES, RELATED_TO, PART_OF, LEADS_TO]:
            targets = self.graph_out.get(skill_lower, {}).get(rel_type, [])
            if targets:
                relationships[rel_type] = targets

        # Add implicit RELATED_TO from same subcategory
        implicit_related = self.related_skills.get(skill_lower, [])
        existing_related = set(r.lower() for r in relationships.get(RELATED_TO, []))
        for r in implicit_related:
            if r.lower() not in existing_related:
                relationships.setdefault(RELATED_TO, []).append(r)
                existing_related.add(r.lower())

        # Incoming relationships (who requires this skill, etc.)
        prerequisites_of = self.graph_in.get(skill_lower, {}).get(REQUIRES, [])
        leads_from = self.graph_in.get(skill_lower, {}).get(LEADS_TO, [])

        return {
            "skill_id": f"skill_{name.lower().replace(' ', '_').replace('.', '_')}",
            "name": name,
            "category": cat,
            "subcategory": subcat,
            "level_range": meta.get("levels", ["intermediate", "advanced"]),
            "description": meta.get("description", ""),
            "demand_score": meta.get("demand", 0.5),
            "trending": meta.get("trending", False),
            "relationships": relationships,
            "required_by": prerequisites_of[:10],
            "leads_from": leads_from[:10],
        }

    def get_graph_data(self, center_skill: Optional[str] = None, depth: int = 1, max_nodes: int = 80) -> dict:
        """
        Get graph data (nodes + edges) for visualization.
        If center_skill is provided, returns the neighborhood subgraph.
        Otherwise returns a sample of the full graph.
        """
        nodes = []
        edges = []
        seen_nodes: set[str] = set()
        seen_edges: set[str] = set()

        def add_node(skill_name: str, distance: int = 0):
            lower = skill_name.lower()
            if lower in seen_nodes or len(seen_nodes) >= max_nodes:
                return
            seen_nodes.add(lower)
            cat = self.skill_to_category.get(lower, "Other")
            meta = SKILL_METADATA.get(self.canonical.get(lower, skill_name), {})
            nodes.append({
                "id": lower,
                "label": self.canonical.get(lower, skill_name),
                "category": cat,
                "demand": meta.get("demand", 0.5),
                "trending": meta.get("trending", False),
                "distance": distance,
            })

        def add_edge(source: str, rel_type: str, target: str):
            edge_key = f"{source.lower()}|{rel_type}|{target.lower()}"
            if edge_key in seen_edges:
                return
            if source.lower() not in seen_nodes or target.lower() not in seen_nodes:
                return
            seen_edges.add(edge_key)
            edges.append({
                "source": source.lower(),
                "target": target.lower(),
                "type": rel_type,
            })

        if center_skill:
            # BFS from center skill
            skill_lower = center_skill.lower()
            if skill_lower not in self.canonical and skill_lower not in self.skill_to_category:
                return {"nodes": [], "edges": []}

            queue = [(skill_lower, 0)]
            visited = {skill_lower}
            add_node(self.canonical.get(skill_lower, center_skill), 0)

            while queue and len(seen_nodes) < max_nodes:
                current, dist = queue.pop(0)
                if dist >= depth:
                    continue

                # Outgoing edges
                for rel_type, targets in self.graph_out.get(current, {}).items():
                    for t in targets:
                        t_lower = t.lower()
                        add_node(t, dist + 1)
                        add_edge(self.canonical.get(current, current), rel_type, t)
                        if t_lower not in visited:
                            visited.add(t_lower)
                            queue.append((t_lower, dist + 1))

                # Incoming edges
                for rel_type, sources in self.graph_in.get(current, {}).items():
                    for s in sources:
                        s_lower = s.lower()
                        add_node(s, dist + 1)
                        add_edge(s, rel_type, self.canonical.get(current, current))
                        if s_lower not in visited:
                            visited.add(s_lower)
                            queue.append((s_lower, dist + 1))

                # Also add implicit related skills from same subcategory
                for r in self.related_skills.get(current, [])[:5]:
                    r_lower = r.lower()
                    add_node(r, dist + 1)
                    add_edge(self.canonical.get(current, current), RELATED_TO, r)
                    if r_lower not in visited:
                        visited.add(r_lower)
                        queue.append((r_lower, dist + 1))
        else:
            # Return top skills by demand
            sorted_skills = sorted(
                SKILL_METADATA.items(),
                key=lambda x: x[1].get("demand", 0),
                reverse=True,
            )
            for name, _ in sorted_skills[:max_nodes]:
                add_node(name, 0)

            # Add edges between visible nodes
            for source, rels in self.graph_out.items():
                if source in seen_nodes:
                    for rel_type, targets in rels.items():
                        for t in targets:
                            if t.lower() in seen_nodes:
                                add_edge(
                                    self.canonical.get(source, source),
                                    rel_type,
                                    t,
                                )

        return {"nodes": nodes, "edges": edges}

    def search_skills(self, query: str, limit: int = 20) -> list[dict]:
        """Search skills by name prefix or substring."""
        query_lower = query.lower().strip()
        if not query_lower:
            return []

        results = []
        for skill_name in self.all_skills:
            name_lower = skill_name.lower()
            if query_lower in name_lower:
                cat = self.skill_to_category.get(name_lower, "Other")
                meta = SKILL_METADATA.get(skill_name, {})
                # Score: exact match > prefix > contains
                if name_lower == query_lower:
                    score = 3.0
                elif name_lower.startswith(query_lower):
                    score = 2.0
                else:
                    score = 1.0
                score += meta.get("demand", 0)

                results.append({
                    "name": skill_name,
                    "category": cat,
                    "subcategory": self.skill_to_subcategory.get(name_lower, ""),
                    "demand": meta.get("demand", 0.5),
                    "trending": meta.get("trending", False),
                    "score": round(score, 2),
                })

        results.sort(key=lambda x: -x["score"])
        return results[:limit]

    def get_stats(self) -> dict:
        """Get ontology statistics."""
        total_edges = sum(
            len(targets)
            for rels in self.graph_out.values()
            for targets in rels.values()
        )

        # Count by relationship type
        edge_counts = defaultdict(int)
        for rels in self.graph_out.values():
            for rel_type, targets in rels.items():
                edge_counts[rel_type] += len(targets)

        # Count by category
        category_counts = {}
        for cat, skills in self.category_skills.items():
            category_counts[cat] = len(skills)

        # Connectivity
        nodes_with_edges = set()
        for src in self.graph_out:
            nodes_with_edges.add(src)
        for tgt in self.graph_in:
            nodes_with_edges.add(tgt)

        total_nodes = len(self.all_skills)
        connected = len(nodes_with_edges)

        return {
            "total_nodes": total_nodes,
            "total_edges": total_edges,
            "edge_counts": dict(edge_counts),
            "category_counts": category_counts,
            "connectivity": round(connected / max(1, total_nodes) * 100, 1),
            "categories": len(SKILL_ONTOLOGY),
        }

    # ─── Distance & Explanation (backward compatible) ──────────────────

    def skill_distance(self, skill_a: str, skill_b: str) -> float:
        """
        Calculate ontological distance between two skills.
        0.0 = identical, 0.2 = same subcategory, 0.5 = same category, 0.8 = different, 1.0 = unknown.
        """
        a_lower = skill_a.lower()
        b_lower = skill_b.lower()

        if a_lower == b_lower:
            return 0.0

        # Check explicit REQUIRES or RELATED_TO edge
        a_out = self.graph_out.get(a_lower, {})
        b_out = self.graph_out.get(b_lower, {})
        if b_lower in [t.lower() for t in a_out.get(RELATED_TO, [])]:
            return 0.15
        if a_lower in [t.lower() for t in b_out.get(RELATED_TO, [])]:
            return 0.15

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
        elif distance <= 0.2:
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
