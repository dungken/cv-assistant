"""
Span-level NER evaluation on Groq-generated CVs.

Compares model-predicted entity spans with rule-based reference spans
using exact span match (entity type + text content), which avoids
WordPiece tokenization alignment issues.

Usage:
    python scripts/evaluate_ner_spans.py --count 100
    python scripts/evaluate_ner_spans.py --count 100 --show-errors 20
"""

import re
import json
import argparse
from pathlib import Path
from collections import Counter, defaultdict

import torch
from transformers import pipeline as hf_pipeline

# ── Label set ────────────────────────────────────────────────────────────────
ENTITY_TYPES = [
    "PER", "ORG", "DATE", "LOC", "SKILL",
    "DEGREE", "MAJOR", "JOB_TITLE", "PROJECT", "CERT",
]

# ── Rule-based reference annotator (span-level) ──────────────────────────────

SKILL_SET = {
    # Languages
    "Python", "Java", "JavaScript", "TypeScript", "Go", "Golang", "Rust",
    "C++", "C#", "C", "Swift", "Kotlin", "PHP", "Ruby", "Scala", "Dart",
    "Bash", "Shell", "Perl", "R", "MATLAB", "Lua", "Haskell", "Elixir",
    "Clojure", "Groovy", "PowerShell", "SQL", "NoSQL",
    # Frontend
    "React", "Vue", "Angular", "Svelte", "HTML", "CSS", "HTML5", "CSS3",
    "Tailwind", "Bootstrap", "Webpack", "Vite", "Babel", "Redux", "Pinia",
    "Vuex", "jQuery", "Sass", "SCSS", "Less",
    # Backend
    "Django", "Flask", "FastAPI", "Spring", "Express", "Laravel",
    "NestJS", ".NET", "Gin", "Echo", "Rails", "Fiber", "Actix",
    "Sinatra", "Phoenix", "Ktor", "Quarkus", "Micronaut",
    # Data / AI / ML
    "PyTorch", "TensorFlow", "Keras", "scikit-learn", "Sklearn",
    "MLflow", "LangChain", "Transformers", "Pandas", "NumPy", "SciPy",
    "Spark", "Kafka", "Airflow", "HuggingFace", "CUDA", "ONNX", "dbt",
    "XGBoost", "LightGBM", "CatBoost", "OpenCV", "spaCy", "NLTK",
    "Flink", "Beam", "Hadoop", "Hive", "Pig",
    # DevOps / Cloud
    "Docker", "Kubernetes", "Terraform", "Ansible", "Helm", "ArgoCD",
    "AWS", "GCP", "Azure", "Jenkins", "GitLab", "CircleCI",
    "Prometheus", "Grafana", "Datadog", "Nginx", "Linux",
    "Vagrant", "Pulumi", "Consul", "Istio", "Envoy",
    # Databases
    "PostgreSQL", "MySQL", "MongoDB", "Redis", "Elasticsearch",
    "Cassandra", "SQLite", "DynamoDB", "BigQuery", "Snowflake",
    "ClickHouse", "Neo4j", "InfluxDB", "MariaDB", "Oracle",
    "Supabase", "Firebase", "Firestore", "CouchDB",
    # Mobile
    "Flutter", "SwiftUI", "Xamarin", "Ionic", "Cordova",
    "Android", "iOS",
    # Testing
    "Selenium", "Cypress", "Jest", "Pytest", "JUnit", "Postman",
    "Playwright", "Mocha", "Jasmine", "TestNG", "Appium",
    "JMeter", "Gatling", "k6",
    # Tools
    "Git", "GitHub", "Jira", "Confluence", "Figma", "Postman",
    "Swagger", "SonarQube", "Kibana", "Logstash", "Splunk",
    # Misc
    "K8s", "k8s", "CI/CD", "REST", "GraphQL", "gRPC",
    "Agile", "Scrum", "Kanban", "DevOps",
    # Normalised lowercase variants (for matching)
    "numpy", "pandas", "pytorch", "tensorflow", "sklearn",
    "docker", "kubernetes", "postgresql", "mongodb", "redis",
    "azure", "aws", "gcp", "nginx", "linux",
    # BI / Analytics
    "Tableau", "Power BI", "Looker", "Metabase",
    # IntelliJ / IDEs as skills
    "IntelliJ IDEA", "IntelliJ", "VS Code", "PyCharm", "WebStorm",
    # Security
    "OWASP", "JWT", "OAuth",
    # Other common
    "Notion", "Trello", "Slack", "Confluence",
    "SQL Server", "MSSQL",
}

SKILL_PHRASES = {
    "React Native", "Node.js", "Next.js", "Nuxt.js", "GitHub Actions",
    "scikit-learn", "Apache Kafka", "Apache Spark", "Spring Boot",
    "Spring Framework", "ASP.NET Core", "ASP.NET", "Vue.js",
    "React.js", "Tailwind CSS", "Material UI", "Jetpack Compose",
    "Deep Learning", "Machine Learning", "Natural Language Processing",
    "Computer Vision", "Data Science", "Microservices",
    "RESTful API", "REST API", "Web Services",
    "Docker Compose", "GitLab CI/CD", "GitHub Actions",
    "Google Cloud", "Amazon Web Services", "Microsoft Azure",
    "Elastic Stack", "ELK Stack", "Apache Flink",
    "Ruby on Rails", "Unreal Engine", "React.js", "Vue.js",
    "Socket.IO", "WebSocket", "gRPC",
    "IntelliJ IDEA", "VS Code", "Power BI",
    "SQL Server", "Tailwind CSS",
}

MAJOR_PHRASES = [
    "Computer Science", "Software Engineering", "Information Technology",
    "Data Science", "Artificial Intelligence", "Electrical Engineering",
    "Computer Engineering", "Information Systems", "Cybersecurity",
    "Information Security", "Network Engineering", "Computer Networks",
]

DEGREE_RE = re.compile(
    r"\b(B\.?S\.?|M\.?S\.?|Ph\.?D\.?|MBA|BEng|MEng|"
    r"Bachelor(?:'?s)?(?:\s+of\s+\w+)?|Master(?:'?s)?(?:\s+of\s+\w+)?|"
    r"Doctorate|B\.?Sc\.?|M\.?Sc\.?|B\.?Eng\.?|M\.?Eng\.?)\b", re.I
)

JOB_TITLE_RE = re.compile(
    r"\b(?:(?:Senior|Mid-?level|Junior|Lead|Principal|Staff|Sr\.|Jr\.)\s+)?"
    r"(?:Software|Backend|Frontend|Full[- ]?[Ss]tack|Data|DevOps|QA|"
    r"Platform|Cloud|ML|AI|Mobile|iOS|Android|Security|Embedded|"
    r"Blockchain|Game|Web|NLP)\s+"
    r"(?:Engineer|Developer|Architect|Scientist|Analyst|Specialist|Researcher)\b"
    r"|\bTech(?:nical)?\s+Lead\b|\bTeam\s+Lead\b|\bEngineering\s+Manager\b"
    r"|\bSite\s+Reliability\s+Engineer\b|\bSRE\b|\bScrum\s+Master\b"
    r"|\bProduct\s+Manager\b|\bProject\s+Manager\b",
    re.I
)

DATE_RE = re.compile(
    r"\b(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?"
    r"|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?"
    r"|Dec(?:ember)?)[,.]?\s+\d{4}"
    r"|\b\d{4}\s*[-–—]\s*(?:\d{4}|Present|Now|Current|present)\b",
    re.I
)

LOC_RE = re.compile(
    r"\b(?:Ho\s+Chi\s+Minh\s+(?:City)?|Hanoi|Ha\s+Noi|Da\s+Nang|"
    r"Hai\s+Phong|Can\s+Tho|HCMC|HCM|TP\.?HCM|Vietnam|Viet\s+Nam|"
    r"Singapore|Tokyo|Seoul|Remote|Hybrid)\b", re.I
)

ORG_NAMES = {
    # VN tech companies
    "VNG Corporation", "VNG", "FPT Software", "FPT Information System",
    "FPT Telecom", "FPT", "Viettel Solutions", "Viettel Group", "Viettel",
    "VNPT", "MoMo", "M_Service", "Tiki", "Zalo", "ZaloPay", "VinAI",
    "VinBigData", "Shopee", "Shopee Vietnam", "Grab", "Grab Vietnam",
    "Lazada", "Lazada Vietnam", "One Mount Group", "Sendo",
    "KMS Technology", "KMS Solutions", "KMS", "NashTech", "NashTech Vietnam",
    "Axon Active", "Axon Active Vietnam", "TMA Solutions", "TMA Technology",
    "Sun Asterisk", "Sun*", "Rikkeisoft", "Rikkei Soft",
    "CO-WELL Asia", "Savvycom", "Niteco Vietnam", "Orient Software",
    "NFQ Asia", "TechVify Software", "Enlab Software", "Amanotes",
    "Gameloft Vietnam", "Gameloft", "Sky Mavis",
    "GHTK", "VPBank", "Techcombank", "MB Bank", "ACB", "Sacombank",
    "TPBank", "Vietcombank", "BIDV", "Agribank",
    "Masan Group", "Vingroup", "Yeah1 Group",
    # International
    "Samsung Electronics", "Samsung Vietnam", "Samsung SDS", "Samsung",
    "LG Electronics", "LG CNS", "Bosch Vietnam", "Bosch", "Fujitsu Vietnam",
    "Intel", "Microsoft", "Google", "Amazon", "Meta", "Apple",
    "IBM", "Oracle", "SAP", "Accenture", "Deloitte", "PwC", "KPMG",
    "Sea Limited", "ByteDance", "Stripe", "Atlassian", "Thoughtworks",
    # Universities (often appear as ORG in CVs)
    "FPT University", "RMIT University", "RMIT Vietnam",
    "Vietnam National University", "VNU",
    "Bach Khoa University", "HCMUT",
    "University of Information Technology", "UIT",
    "Posts and Telecommunications Institute", "PTIT",
    "Hanoi University of Science and Technology", "HUST",
    "Ton Duc Thang University", "TDTU",
    "University of Science", "HCMUS",
    "University of Transport and Communications", "UTC",
    "Phenikaa University",
}

CERT_RE = re.compile(
    r"\b(?:AWS\s+Certified[\w\s]{3,50}"
    r"|Google\s+(?:Professional|Associate|Cloud)[\w\s]{3,50}"
    r"|Microsoft\s+Certified[\w\s]{3,50}"
    r"|Azure\s+(?:Administrator|Developer|Solutions\s+Architect|DevOps)[\w\s]{0,30}"
    r"|CKA|CKAD|CKS"
    r"|PMP|CISSP|CISM|CEH|CCNA|CCNP|CCIE"
    r"|Oracle\s+Certified[\w\s]{3,40}"
    r"|ITIL[\w\s]{0,25}"
    r"|CompTIA[\w\s+]{3,30}"
    r"|Certified\s+Kubernetes[\w\s]{3,30}"
    r"|Docker\s+Certified[\w\s]{3,30}"
    r"|Terraform\s+Associate"
    r"|HashiCorp\s+Certified[\w\s]{3,30}"
    r"|Certified\s+Scrum\s+Master|CSM"
    r"|Professional\s+Scrum\s+Master|PSM"
    r"|PMI-ACP|TOGAF|ISTQB[\w\s]{0,20}"
    r"|TensorFlow\s+Developer\s+Certificate"
    r"|MongoDB\s+Certified[\w\s]{3,30}"
    r"|Salesforce\s+Certified[\w\s]{3,40})\b",
    re.I
)

NAME_RE = re.compile(
    r"^([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,3})(?:\s*[-,|]|\s*$)", re.MULTILINE
)


def get_reference_spans(text: str) -> list[tuple[int, int, str]]:
    """Extract entity spans using rule-based patterns. Returns (start, end, type)."""
    spans = []

    def add(m, etype):
        spans.append((m.start(), m.end(), etype))

    # CERT
    for m in CERT_RE.finditer(text):
        add(m, "CERT")

    # Known ORGs
    for name in sorted(ORG_NAMES, key=len, reverse=True):
        for m in re.finditer(r"\b" + re.escape(name) + r"\b", text, re.I):
            if not re.search(r"[@/\.]", text[max(0, m.start()-1):m.end()+1]):
                add(m, "ORG")

    # JOB_TITLE
    for m in JOB_TITLE_RE.finditer(text):
        add(m, "JOB_TITLE")

    # MAJOR (only if near Education section)
    edu_idx = max(
        (text.lower().find(kw) for kw in ["education", "academic", "university", "degree"]
         if text.lower().find(kw) != -1),
        default=-1
    )
    for phrase in sorted(MAJOR_PHRASES, key=len, reverse=True):
        for m in re.finditer(r"\b" + re.escape(phrase) + r"\b", text, re.I):
            if edu_idx != -1 and abs(m.start() - edu_idx) < 500:
                add(m, "MAJOR")

    # Multi-word SKILL phrases
    for phrase in sorted(SKILL_PHRASES, key=len, reverse=True):
        for m in re.finditer(r"\b" + re.escape(phrase) + r"\b", text):
            add(m, "SKILL")

    # Single-token SKILLs
    for skill in sorted(SKILL_SET, key=len, reverse=True):
        pattern = r"(?<![A-Za-z])" + re.escape(skill) + r"(?![A-Za-z])"
        for m in re.finditer(pattern, text):
            add(m, "SKILL")

    # DATE
    for m in DATE_RE.finditer(text):
        add(m, "DATE")

    # LOC
    for m in LOC_RE.finditer(text):
        add(m, "LOC")

    # DEGREE
    for m in DEGREE_RE.finditer(text):
        add(m, "DEGREE")

    # PER — only first non-empty line (CV header name) and lines starting with "Name:"
    per_found = False
    for line in text.strip().split("\n")[:5]:
        line_s = line.strip("- ,\t*#")
        # "Name: Nguyen Van An" pattern
        name_m = re.match(r"(?:name|full\s*name)\s*:\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,3})", line_s, re.I)
        if name_m:
            name = name_m.group(1)
            idx = text.find(name)
            if idx != -1:
                spans.append((idx, idx + len(name), "PER"))
                per_found = True
            break
        # Plain name line: 2-4 Titlecase words, no punctuation, no digits
        m = re.match(r"^([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,3})$", line_s)
        if m and not re.search(r"\d|[@/]", line_s):
            idx = text.find(m.group(1))
            if idx != -1:
                spans.append((idx, idx + len(m.group(1)), "PER"))
                per_found = True
            break
        # Skip empty lines but stop after first non-empty non-name line
        if line_s:
            break

    # Resolve overlaps — prefer longer spans
    spans.sort(key=lambda s: (-(s[1] - s[0]), s[0]))
    result, occupied = [], set()
    for s, e, t in spans:
        r = set(range(s, e))
        if not r & occupied:
            result.append((s, e, t))
            occupied |= r
    result.sort(key=lambda x: x[0])
    return result


_LEVEL_PREFIX_RE = re.compile(
    r"^\s*(?:senior|sr\.?|junior|jr\.?|mid-?level|mid|principal|staff|lead|"
    r"associate|intern|fresher|entry[-\s]?level)\s+", re.I
)
_MONTH_RE = re.compile(
    r"\b(?:january|february|march|april|may|june|july|august|september|"
    r"october|november|december|jan|feb|mar|apr|jun|jul|aug|sep|oct|nov|dec)\.?\s*",
    re.I
)
_DATE_SEP_RE   = re.compile(r"\s*[-–—]\s*")
_YEAR_RE       = re.compile(r"\b(19|20)\d{2}\b")
_SUBWORD_RE    = re.compile(r"\s*##\s*")
_PUNCT_STRIP   = re.compile(r"^[\s\(\)\[\]{},;:\-\"']+|[\s\(\)\[\]{},;:\-\"']+$")
_SPACES_RE     = re.compile(r"\s+")


def normalize_entity(text: str, etype: str = "") -> str:
    """Semantic normalization before span matching.

    - Strip leading/trailing punctuation and whitespace
    - Remove ## subword artefacts
    - DATE  → extract year(s) only, canonical "YYYY" or "YYYY-YYYY"
    - JOB_TITLE → strip seniority prefix so "Senior BE Dev" ≈ "BE Dev"
    - All → lowercase, collapse spaces
    """
    # ## subword artefacts (from BERT tokenizer)
    text = _SUBWORD_RE.sub("", text)
    # strip outer punctuation
    text = _PUNCT_STRIP.sub("", text)
    text = _SPACES_RE.sub(" ", text).strip().lower()

    if etype == "DATE":
        # Remove month names, keep only years and separator
        text = _MONTH_RE.sub("", text).strip()
        years = _YEAR_RE.findall(text)
        if years:
            present_kw = bool(re.search(r"\b(present|current|now)\b", text, re.I))
            if len(years) == 1:
                text = years[0] + ("-present" if present_kw else "")
            else:
                text = years[0] + "-" + years[-1]
        # fallback: keep cleaned text

    elif etype == "JOB_TITLE":
        # Strip seniority prefix so "Senior Backend Developer" ≈ "Backend Developer"
        text = _LEVEL_PREFIX_RE.sub("", text).strip()

    return text


def spans_to_set(spans: list[tuple[int, int, str]], text: str) -> set[tuple[str, str]]:
    """Convert spans to (entity_type, normalized_text) pairs for matching."""
    result = set()
    for s, e, t in spans:
        raw = text[s:e]
        entity_text = normalize_entity(raw, t)
        if len(entity_text) >= 2:
            result.add((t, entity_text))
    return result


def evaluate_model(model_dir: str, data_file: str, count: int, show_errors: int):
    # Load data
    records = []
    with open(data_file) as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    if count > 0:
        records = records[:count]
    print(f"Loaded {len(records)} records from {data_file}")

    # Load model
    print(f"Loading NER model from {model_dir}...")
    device = 0 if torch.cuda.is_available() else -1
    ner_pipe = hf_pipeline(
        "ner", model=model_dir,
        aggregation_strategy="simple",
        device=device
    )
    print(f"  Device: {'GPU' if device == 0 else 'CPU'}")

    # Evaluate
    tp_per_type = Counter()
    fp_per_type = Counter()
    fn_per_type = Counter()
    errors = []
    ref_total = Counter()
    pred_total = Counter()

    print(f"\nEvaluating {len(records)} CVs...")
    for i, rec in enumerate(records):
        text = rec.get("text_clean") or rec.get("text", "")
        if not text.strip():
            continue

        # Reference spans (rule-based)
        ref_spans = get_reference_spans(text)
        ref_set = spans_to_set(ref_spans, text)

        # Predicted spans (model) — chunk to avoid 512-token truncation
        try:
            preds = []
            chunk_size = 400   # chars, safe under 512 WordPiece tokens
            overlap    = 50
            pos = 0
            while pos < len(text):
                chunk = text[pos:pos + chunk_size]
                preds.extend(ner_pipe(chunk))
                pos += chunk_size - overlap
        except Exception as e:
            print(f"  [SKIP] {i}: {e}")
            continue

        pred_set = set()
        for p in preds:
            etype = p["entity_group"]
            if etype not in ENTITY_TYPES:
                continue
            raw_word = p["word"]
            # Merge residual ## subword artefacts aggregation_strategy missed
            raw_word = re.sub(r"\s*##", "", raw_word).strip()
            # Drop very short single-char or punctuation-only predictions
            stripped = raw_word.strip("() ,.|:;-[]{}\"'")
            if len(stripped) < 2:
                continue
            word = normalize_entity(raw_word, etype)
            if len(word) < 2:
                continue
            # For CERT/ORG/JOB_TITLE: require at least 3 chars and 1 letter
            if etype in ("CERT", "ORG", "JOB_TITLE") and (len(word) < 3 or not re.search(r"[a-z]", word)):
                continue
            pred_set.add((etype, word))

        # Count TP/FP/FN per type
        for etype in ENTITY_TYPES:
            ref_t = {e for t, e in ref_set if t == etype}
            pred_t = {e for t, e in pred_set if t == etype}
            ref_total[etype] += len(ref_t)
            pred_total[etype] += len(pred_t)
            tp = len(ref_t & pred_t)
            fp = len(pred_t - ref_t)
            fn = len(ref_t - pred_t)
            tp_per_type[etype] += tp
            fp_per_type[etype] += fp
            fn_per_type[etype] += fn

            if fn > 0 and show_errors > 0 and len(errors) < show_errors:
                missed = list(ref_t - pred_t)[:2]
                for m in missed:
                    errors.append({
                        "id": rec.get("id", str(i)),
                        "role": rec.get("role", ""),
                        "type": etype,
                        "missed": m,
                    })

        if (i + 1) % 25 == 0:
            print(f"  {i+1}/{len(records)} done")

    # Compute metrics
    print("\n" + "=" * 70)
    print("  NER Span-Level Evaluation — Semi-Automatic (Rule-Based Reference)")
    print("=" * 70)
    print(f"\n  Model    : {model_dir}")
    print(f"  Dataset  : {data_file}")
    print(f"  Samples  : {len(records)}")
    print(f"  Device   : {'GPU' if device == 0 else 'CPU'}")
    print(f"  Method   : Span-level F1 (entity_type + normalized_text match)\n")

    header = f"  {'Entity':<12} {'Prec':>7} {'Rec':>7} {'F1':>7} {'Ref':>6} {'Pred':>6} {'TP':>5}"
    print(header)
    print("  " + "-" * 60)

    total_tp = total_fp = total_fn = 0
    for etype in ENTITY_TYPES:
        tp = tp_per_type[etype]
        fp = fp_per_type[etype]
        fn = fn_per_type[etype]
        total_tp += tp; total_fp += fp; total_fn += fn
        prec = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        rec  = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1   = 2 * prec * rec / (prec + rec) if (prec + rec) > 0 else 0.0
        ref  = ref_total[etype]
        pred = pred_total[etype]
        if ref > 0 or pred > 0:
            print(f"  {etype:<12} {prec:>7.4f} {rec:>7.4f} {f1:>7.4f} {ref:>6} {pred:>6} {tp:>5}")

    print("  " + "-" * 60)
    micro_p = total_tp / (total_tp + total_fp) if (total_tp + total_fp) > 0 else 0
    micro_r = total_tp / (total_tp + total_fn) if (total_tp + total_fn) > 0 else 0
    micro_f1 = 2 * micro_p * micro_r / (micro_p + micro_r) if (micro_p + micro_r) > 0 else 0
    print(f"  {'micro avg':<12} {micro_p:>7.4f} {micro_r:>7.4f} {micro_f1:>7.4f} "
          f"{sum(ref_total.values()):>6} {sum(pred_total.values()):>6} {total_tp:>5}")

    print(f"\n  Overall micro F1 : {micro_f1:.4f}")
    print(f"  Overall Precision: {micro_p:.4f}")
    print(f"  Overall Recall   : {micro_r:.4f}")

    if errors:
        print(f"\n  Sample missed entities (FN, first {len(errors)}):")
        for e in errors:
            print(f"    [{e['type']:<10}] '{e['missed']}'  (CV: {e['id']}, role: {e['role']})")

    # Save report
    out_path = Path("docs/reports/ner_span_evaluation.txt")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    lines_out = [
        "NER Span-Level Evaluation Report",
        f"Model   : {model_dir}",
        f"Dataset : {data_file}",
        f"Samples : {len(records)}",
        f"Method  : span-level F1 (entity_type + normalized text)",
        "",
        f"{'Entity':<12} {'Precision':>10} {'Recall':>8} {'F1':>8} {'Ref':>6} {'Pred':>6}",
        "-" * 58,
    ]
    for etype in ENTITY_TYPES:
        tp = tp_per_type[etype]
        fp = fp_per_type[etype]
        fn = fn_per_type[etype]
        prec = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        rec  = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1   = 2 * prec * rec / (prec + rec) if (prec + rec) > 0 else 0.0
        ref  = ref_total[etype]
        pred = pred_total[etype]
        if ref > 0 or pred > 0:
            lines_out.append(f"{etype:<12} {prec:>10.4f} {rec:>8.4f} {f1:>8.4f} {ref:>6} {pred:>6}")
    lines_out += ["-" * 58,
                  f"{'micro avg':<12} {micro_p:>10.4f} {micro_r:>8.4f} {micro_f1:>8.4f}"]
    with open(out_path, "w") as f:
        f.write("\n".join(lines_out))
    print(f"\n  Report saved to {out_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--model-dir", default="models/ner/final")
    parser.add_argument("--data-file", default="data/synthetic_cvs_groq100.jsonl")
    parser.add_argument("--count", type=int, default=100)
    parser.add_argument("--show-errors", type=int, default=15)
    args = parser.parse_args()
    evaluate_model(args.model_dir, args.data_file, args.count, args.show_errors)
