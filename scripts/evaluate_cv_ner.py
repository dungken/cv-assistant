"""
Evaluate NER CV model on synthetic_cvs.jsonl.
Step 1: Auto-label CV text using rule-based annotator (creates silver test set).
Step 2: Run model inference and compute F1/P/R per entity type.

Usage:
    python scripts/evaluate_cv_ner.py                    # 200 samples
    python scripts/evaluate_cv_ner.py --max-samples 600  # full dataset
    python scripts/evaluate_cv_ner.py --max-samples 0    # all
"""

import re
import json
import argparse
from pathlib import Path
from collections import Counter

import torch
from transformers import AutoTokenizer, AutoModelForTokenClassification, pipeline
from seqeval.metrics import classification_report, f1_score, precision_score, recall_score

# ── Label set (must match model config) ──────────────────────────────────────
LABEL_LIST = [
    "O", "B-PER", "I-PER", "B-ORG", "I-ORG", "B-DATE", "I-DATE",
    "B-LOC", "I-LOC", "B-SKILL", "I-SKILL", "B-DEGREE", "I-DEGREE",
    "B-MAJOR", "I-MAJOR", "B-JOB_TITLE", "I-JOB_TITLE",
    "B-PROJECT", "I-PROJECT", "B-CERT", "I-CERT",
]

# ── Rule-based annotator ──────────────────────────────────────────────────────

SKILL_SET = {
    # Languages
    "Python", "Java", "JavaScript", "TypeScript", "Go", "Rust", "C++", "C#",
    "Swift", "Kotlin", "PHP", "Ruby", "Scala", "Bash", "Shell", "Perl",
    # Frontend
    "React", "Vue", "Angular", "Next.js", "Nuxt.js", "Svelte", "HTML", "CSS",
    "Tailwind", "Bootstrap", "Webpack", "Vite", "Redux",
    # Backend
    "Node.js", "Django", "Flask", "FastAPI", "Spring", "Express", "Laravel",
    "NestJS", ".NET", "Gin", "Echo", "Rails", "Fiber",
    # Data / AI
    "PyTorch", "TensorFlow", "scikit-learn", "MLflow", "LangChain",
    "Transformers", "Pandas", "NumPy", "Spark", "Kafka", "Airflow",
    "HuggingFace", "CUDA", "ONNX", "dbt",
    # DevOps / Cloud
    "Docker", "Kubernetes", "Terraform", "Ansible", "Helm", "ArgoCD",
    "AWS", "GCP", "Azure", "Jenkins", "GitLab", "CircleCI",
    "Prometheus", "Grafana", "Datadog",
    # Databases
    "PostgreSQL", "MySQL", "MongoDB", "Redis", "Elasticsearch", "Cassandra",
    "SQLite", "DynamoDB", "BigQuery", "Snowflake", "ClickHouse",
    # Mobile
    "Flutter", "SwiftUI",
    # Testing
    "Selenium", "Cypress", "Jest", "Pytest", "JUnit", "Postman", "Playwright",
    # Abbreviations that are unambiguous in CV context
    "K8s", "k8s", "CI/CD", "REST", "GraphQL", "gRPC", "Git",
}
# Multi-word skills (exact match, case-sensitive)
SKILL_PHRASES = {
    "React Native", "Node.js", "Next.js", "Nuxt.js", "GitHub Actions",
    "scikit-learn", "Apache Kafka", "Apache Spark", "Spring Boot",
}

# Only match inside EDUCATION section context
MAJOR_PHRASES = [
    "Computer Science", "Software Engineering", "Information Technology",
    "Data Science", "Artificial Intelligence", "Electrical Engineering",
    "Computer Engineering", "Information Systems", "Cybersecurity",
    "Information Security", "Network Engineering", "Computer Networks",
]

DEGREE_RE = re.compile(
    r"^(B\.?S\.?|M\.?S\.?|Ph\.?D\.?|MBA|BEng|MEng|"
    r"Bachelor(?:'?s)?|Master(?:'?s)?|Doctorate|"
    r"B\.?Sc\.?|M\.?Sc\.?|B\.?Eng\.?|M\.?Eng\.?)$", re.I
)

# Job title core pattern — we extract match then validate token count (≤ 5 words)
JOB_TITLE_RE = re.compile(
    r"\b(?:(?:Senior|Mid-?level|Junior|Lead|Principal|Staff|Sr\.|Jr\.)\s+)?"
    r"(?:Software|Backend|Frontend|Full[- ]?[Ss]tack|Data|DevOps|QA|"
    r"Platform|Cloud|ML|AI|Mobile|iOS|Android|Security|Embedded)\s+"
    r"(?:Engineer|Developer|Architect|Scientist|Analyst|Specialist)\b"
    r"|\bTech(?:nical)?\s+Lead\b|\bTeam\s+Lead\b|\bEngineering\s+Manager\b"
    r"|\bProduct\s+Manager\b|\bProject\s+Manager\b|\bScrum\s+Master\b"
    r"|\bSite\s+Reliability\s+Engineer\b|\bSRE\b",
    re.I
)

DATE_RE = re.compile(
    r"\b(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?"
    r"|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?"
    r"|Dec(?:ember)?)[,.]?\s+\d{4}"
    r"|\b\d{4}\s*[-–—]\s*(?:\d{4}|Present|Now|Current|present)\b"
    r"|\b(?:Present|Current)\b",
    re.I
)

LOC_RE = re.compile(
    r"\b(?:Ho\s+Chi\s+Minh\s+City|Hanoi|Da\s+Nang|Hai\s+Phong|Can\s+Tho"
    r"|HCMC|HCM|TP\.HCM|Singapore|Tokyo|Seoul|Remote|Hybrid)\b", re.I
)

# Known company names (exact, unambiguous)
ORG_NAMES = {
    "VNG Corporation", "VNG", "FPT Software", "FPT Education", "FPT",
    "Viettel Group", "Viettel", "VNPT", "MoMo", "Tiki", "Zalo", "VinAI",
    "Shopee", "Grab", "Lazada", "Bosch Vietnam", "Samsung Electronics",
    "Intel", "LG Electronics", "Microsoft", "Google", "Amazon", "Meta",
    "Got It Inc.", "Got It", "KMS Technology", "KMS", "NashTech",
    "Axon Active", "Manabie", "GHTK", "VPBank", "Techcombank",
    "Sea Limited", "ByteDance", "Stripe", "Appota", "Base.vn",
}
# Match "Xxx Corp/Inc/Ltd/..." patterns — require Titlecase start to reduce FP
ORG_SUFFIX_RE = re.compile(
    r"\b[A-Z][A-Za-z0-9\s\-&\.]{2,40}\s+"
    r"(?:Corporation|Corp\.|Company|Co\.|Ltd\.?|Limited|Group|Inc\.?|JSC)\b"
)

CERT_RE = re.compile(
    r"\b(?:AWS\s+Certified[\w\s]+|Google\s+(?:Professional|Associate)[\w\s]+"
    r"|Microsoft\s+Certified[\w\s]+|CKA|CKAD|PMP|CISSP|CCNA|CCNP"
    r"|Oracle\s+Certified[\w\s]+)\b",
    re.I
)

# Section headers used to detect context
SECTION_RE = re.compile(
    r"^#+\s*|^\*+\s*|\b(EXPERIENCE|EDUCATION|SKILLS?|SUMMARY|PROJECTS?|"
    r"CERTIFICATIONS?|WORK\s+HISTORY|EMPLOYMENT)\b",
    re.I
)
EDU_SECTION_RE = re.compile(
    r"\b(EDUCATION|ACADEMIC|QUALIFICATION|DEGREE|UNIVERSITY|SCHOOL)\b", re.I
)
SKILL_SECTION_RE = re.compile(r"\b(SKILLS?|TECH(?:NICAL)?|STACK|TOOLS?)\b", re.I)
EXP_SECTION_RE = re.compile(
    r"\b(EXPERIENCE|EMPLOYMENT|WORK\s+HISTORY|CAREER|POSITION)\b", re.I
)


def split_into_sections(text: str) -> dict[str, str]:
    """Return dict mapping section_name -> text for context-aware labeling."""
    lines = text.splitlines()
    sections = {"header": [], "current": "header"}
    result = {"header": []}

    for line in lines:
        stripped = line.strip(" #*-|")
        if SECTION_RE.search(stripped) and len(stripped) < 60:
            key = stripped.lower().strip()
            result[key] = []
            sections["current"] = key
        else:
            result.setdefault(sections["current"], []).append(line)

    return {k: "\n".join(v) for k, v in result.items()}


def rule_based_label(text: str) -> tuple[list[str], list[str]]:
    """Context-aware BIO labeling using section detection."""
    tokens = text.split()
    tags = ["O"] * len(tokens)

    # Build char offsets by finding each token in the original text sequentially.
    # This handles multi-space, tabs, newlines correctly.
    char_offsets: list[tuple[int, int]] = []
    search_from = 0
    for tok in tokens:
        idx = text.find(tok, search_from)
        if idx == -1:
            # fallback: append dummy offset so lengths stay aligned
            char_offsets.append((search_from, search_from))
        else:
            char_offsets.append((idx, idx + len(tok)))
            search_from = idx + len(tok)

    def mark_span(start_char: int, end_char: int, entity: str):
        """Mark only tokens whose start falls inside [start_char, end_char).

        Uses token start position (not overlap) to avoid marking separators
        like '-', '|' that sit between a match and the next word.
        Skips tokens that already have a tag (no overwrite).
        """
        first = True
        for i, (cs, ce) in enumerate(char_offsets):
            if cs >= end_char:
                break
            if cs >= start_char:  # token starts inside the span
                if tags[i] == "O":
                    tags[i] = f"B-{entity}" if first else f"I-{entity}"
                first = False

    # ── Detect section boundaries in the text ────────────────────────────────
    # Map each char position → section type
    lines = text.split("\n")
    char_section: list[str] = []
    current_section = "header"
    for line in lines:
        stripped = line.strip(" #*-|")
        if SECTION_RE.search(stripped) and len(stripped) < 60:
            if EDU_SECTION_RE.search(stripped):
                current_section = "education"
            elif SKILL_SECTION_RE.search(stripped):
                current_section = "skills"
            elif EXP_SECTION_RE.search(stripped):
                current_section = "experience"
            else:
                current_section = "other"
        # +1 for the newline char
        char_section.extend([current_section] * (len(line) + 1))

    def section_at(char_pos: int) -> str:
        if char_pos < len(char_section):
            return char_section[char_pos]
        return "other"

    # ── Pass 1: Multi-word, high-precision patterns ───────────────────────────

    # CERT (global, very specific)
    for m in CERT_RE.finditer(text):
        mark_span(m.start(), m.end(), "CERT")

    # Known ORG names (whitelist) — skip if touching email/url chars
    for name in sorted(ORG_NAMES, key=len, reverse=True):
        for m in re.finditer(r"\b" + re.escape(name) + r"\b", text, re.I):
            before = text[max(0, m.start() - 1):m.start()]
            after = text[m.end():m.end() + 1]
            if re.search(r"[@/\.]", before + after):
                continue
            mark_span(m.start(), m.end(), "ORG")

    # ORG with suffix — reject email/url/digit patterns
    for m in ORG_SUFFIX_RE.finditer(text):
        matched = m.group()
        if re.search(r"[@/\.]com|http|www|\d{3,}", matched, re.I):
            continue
        if len(matched.split()) <= 5:
            mark_span(m.start(), m.end(), "ORG")

    # JOB_TITLE — header/experience only
    for m in JOB_TITLE_RE.finditer(text):
        if section_at(m.start()) in ("header", "experience", "other"):
            mark_span(m.start(), m.end(), "JOB_TITLE")

    # MAJOR — education section only, exact phrase
    for phrase in sorted(MAJOR_PHRASES, key=len, reverse=True):
        pattern = r"(?<!\w)" + re.escape(phrase) + r"(?!\w)"
        for m in re.finditer(pattern, text, re.I):
            if section_at(m.start()) == "education":
                mark_span(m.start(), m.end(), "MAJOR")

    # Multi-word SKILL phrases (global, exact)
    for phrase in sorted(SKILL_PHRASES, key=len, reverse=True):
        for m in re.finditer(r"\b" + re.escape(phrase) + r"\b", text):
            mark_span(m.start(), m.end(), "SKILL")

    # DATE (global)
    for m in DATE_RE.finditer(text):
        mark_span(m.start(), m.end(), "DATE")

    # LOC (global)
    for m in LOC_RE.finditer(text):
        mark_span(m.start(), m.end(), "LOC")

    # ── Pass 2: Token-level ───────────────────────────────────────────────────
    for i, (tok, (cs, _)) in enumerate(zip(tokens, char_offsets)):
        if tags[i] != "O":
            continue
        clean = re.sub(r"[*#\[\](){}<>|]", "", tok).strip(".,;:\"'")
        if not clean:
            continue
        sec = section_at(cs)

        if clean in SKILL_SET:
            tags[i] = "B-SKILL"
        elif DEGREE_RE.match(clean):
            # DEGREE only plausible in education or header
            if sec in ("education", "header", "other"):
                tags[i] = "B-DEGREE"
        elif DATE_RE.search(clean):
            tags[i] = "B-DATE"
        elif LOC_RE.search(clean):
            tags[i] = "B-LOC"

    # ── Pass 3: PER — bold name in first 8 lines, looks like a person name ──
    # Strategy: match **Name** in header only if it has 2-4 words, no digits,
    # no job title words, no email/url chars
    header_text = "\n".join(lines[:8])
    per_match = re.search(
        r"\*\*([A-ZÀÁẠẢÃÂẦẤẬẨẪĂẰẮẶẲẴĐÈÉẸẺẼÊỀẾỆỂỄÌÍỊỈĨ"
        r"òóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹ"
        r"A-Za-zÀ-ỹ][A-Za-zÀ-ỹ\s\-\.]{3,35})\*\*",
        header_text
    )
    if per_match:
        name_text = per_match.group(1).strip()
        words = name_text.split()
        is_name = (
            2 <= len(words) <= 5
            and not re.search(r"[@/\d]", name_text)
            and not JOB_TITLE_RE.search(name_text)
            and not re.search(r"\b(CV|Summary|Profile|Developer|Engineer|"
                              r"Analyst|Manager|Intern|SUMMARY)\b", name_text, re.I)
        )
        if is_name:
            for m in re.finditer(re.escape(per_match.group(0)), text):
                mark_span(m.start() + 2, m.end() - 2, "PER")
                break

    # Clean tokens (strip markdown chars)
    clean_tokens = [
        re.sub(r"[*#\[\](){}<>|]", "", t).strip(".,;:\"'") or t
        for t in tokens
    ]
    return clean_tokens, tags


def align_pipeline_output(predictions, tokens, char_offsets):
    """Map HuggingFace pipeline output back to token-level BIO tags."""
    pred_tags = ["O"] * len(tokens)
    for pred in predictions:
        ps, pe = pred["start"], pred["end"]
        label = pred["entity_group"]
        first = True
        for j, (cs, ce) in enumerate(char_offsets):
            if cs >= pe:
                break
            if ce > ps and cs < pe:
                pred_tags[j] = f"B-{label}" if first else f"I-{label}"
                first = False
    return [t if t in LABEL_LIST else "O" for t in pred_tags]


def build_char_offsets(tokens):
    offsets = []
    pos = 0
    for tok in tokens:
        offsets.append((pos, pos + len(tok)))
        pos += len(tok) + 1
    return offsets


def evaluate(model_dir: str, data_file: str, max_samples: int, output_file: str):
    # ── Load data ────────────────────────────────────────────────────────────
    records = []
    with open(data_file) as f:
        for line in f:
            if line.strip():
                records.append(json.loads(line))
    if max_samples > 0:
        records = records[:max_samples]
    print(f"Loaded {len(records)} CV records")

    # ── Auto-label (rule-based silver test set) ───────────────────────────────
    print("Auto-labeling with rule-based annotator...")
    labeled = []
    for rec in records:
        text = rec.get("text_clean") or rec.get("text", "")
        tokens, tags = rule_based_label(text)
        if tokens:
            labeled.append({"tokens": tokens, "tags": tags, "text": text,
                             "role": rec.get("role", ""), "id": rec.get("id")})

    entity_counts = Counter(
        t.split("-")[1] for s in labeled for t in s["tags"] if t.startswith("B-")
    )
    print(f"Silver labels — entity distribution: {dict(entity_counts)}")
    has_labels = sum(entity_counts.values())
    if has_labels < 10:
        print("WARNING: very few entities found — rule-based labeling may be too sparse")

    # ── Load model ────────────────────────────────────────────────────────────
    print(f"\nLoading model from {model_dir}...")
    tokenizer = AutoTokenizer.from_pretrained(model_dir)
    model = AutoModelForTokenClassification.from_pretrained(model_dir)
    device = 0 if torch.cuda.is_available() else -1
    ner_pipe = pipeline("ner", model=model, tokenizer=tokenizer,
                        aggregation_strategy="simple", device=device)
    print(f"  Device: {'GPU' if device == 0 else 'CPU'}")

    # ── Inference ─────────────────────────────────────────────────────────────
    print(f"\nRunning inference on {len(labeled)} samples...")
    true_all, pred_all, errors = [], [], []

    for i, sample in enumerate(labeled):
        tokens = sample["tokens"]
        true_tags = sample["tags"]
        text = sample["text"]

        try:
            preds = ner_pipe(text[:512])  # truncate for safety
        except Exception as e:
            print(f"  [SKIP] sample {i}: {e}")
            continue

        char_offsets = build_char_offsets(tokens)
        pred_tags = align_pipeline_output(preds, tokens, char_offsets)

        # Align lengths
        min_len = min(len(true_tags), len(pred_tags))
        true_all.append(true_tags[:min_len])
        pred_all.append(pred_tags[:min_len])

        for j, (tt, pt) in enumerate(zip(true_tags[:min_len], pred_tags[:min_len])):
            if tt != pt and (tt != "O" or pt != "O"):
                errors.append({
                    "token": tokens[j] if j < len(tokens) else "?",
                    "true": tt, "pred": pt,
                    "role": sample["role"],
                    "context": " ".join(tokens[max(0, j-3):j+4]),
                })

        if (i + 1) % 50 == 0:
            print(f"  {i+1}/{len(labeled)} done")

    # ── Metrics ───────────────────────────────────────────────────────────────
    if not true_all:
        print("ERROR: no samples evaluated")
        return

    overall_p = precision_score(true_all, pred_all)
    overall_r = recall_score(true_all, pred_all)
    overall_f1 = f1_score(true_all, pred_all)
    report = classification_report(true_all, pred_all, digits=4)

    lines = []
    lines.append("=" * 70)
    lines.append("  NER CV Model — Evaluation on synthetic_cvs.jsonl")
    lines.append("=" * 70)
    lines.append(f"\nSamples evaluated : {len(true_all)}")
    lines.append(f"Labeling method   : rule-based silver standard\n")
    lines.append(f"Overall Metrics:")
    lines.append(f"  Precision : {overall_p:.4f}")
    lines.append(f"  Recall    : {overall_r:.4f}")
    lines.append(f"  F1-Score  : {overall_f1:.4f}")
    lines.append(f"\nPer-Entity Classification Report:")
    lines.append(report)

    lines.append("\nEntity Distribution (silver labels):")
    for ent, cnt in sorted(entity_counts.items(), key=lambda x: -x[1]):
        lines.append(f"  {ent:15s}: {cnt:5d}")

    if errors:
        lines.append(f"\nTop Error Patterns:")
        error_types = Counter(f"{e['true']} -> {e['pred']}" for e in errors)
        for pattern, cnt in error_types.most_common(15):
            lines.append(f"  {pattern:35s}: {cnt:4d}")

        lines.append(f"\nExample Errors (first 10):")
        for e in errors[:10]:
            lines.append(
                f"  [{e['role']:<20}] '{e['token']}' | true={e['true']} pred={e['pred']}"
                f" | ...{e['context']}..."
            )

    text = "\n".join(lines)
    print("\n" + text)

    Path(output_file).parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, "w") as f:
        f.write(text)
    print(f"\nReport saved to {output_file}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--model-dir", default="models/ner/final")
    parser.add_argument("--data-file", default="data/synthetic_cvs.jsonl")
    parser.add_argument("--max-samples", type=int, default=200)
    parser.add_argument("--output", default="docs/reports/ner_cv_evaluation.txt")
    args = parser.parse_args()

    evaluate(args.model_dir, args.data_file, args.max_samples, args.output)
