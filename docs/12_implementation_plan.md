# 12. Implementation Plan - Kế Hoạch Triển Khai Chi Tiết

> **Document Version**: 2.0
> **Last Updated**: 2026-01-24
> **Status**: Approved
> **Product Name**: CV Assistant
> **Related Documents**: [08_optimal_solution.md](./08_optimal_solution.md), [13_review_monitoring.md](./13_review_monitoring.md)

---

## 1. Executive Summary

### 1.1 Project Overview

| Attribute | Value |
|-----------|-------|
| **Start Date** | 26/01/2026 (Chủ nhật) |
| **End Date** | 19/04/2026 (Chủ nhật) |
| **Duration** | 12 weeks (84 days) |
| **Team Size** | 5 people (1 Leader + 4 Annotators) |
| **Budget** | $0 (Free tier only) |

### 1.2 Master Timeline

```
╔═══════════════════════════════════════════════════════════════════════════════════╗
║                           CV ASSISTANT - 12 WEEK TIMELINE                          ║
╠═══════════════════════════════════════════════════════════════════════════════════╣
║ Week     │ 1 │ 2 │ 3 │ 4 │ 5 │ 6 │ 7 │ 8 │ 9 │10 │11 │12 │                       ║
║ ─────────┼───┼───┼───┼───┼───┼───┼───┼───┼───┼───┼───┼───┤                       ║
║ PHASE 1  │███│███│   │   │   │   │   │   │   │   │   │   │ Setup & Knowledge     ║
║ PHASE 2  │   │   │███│███│███│███│   │   │   │   │   │   │ Data Annotation       ║
║ PHASE 3  │   │   │   │   │   │   │███│███│███│   │   │   │ Model & Chatbot       ║
║ PHASE 4  │   │   │   │   │   │   │   │   │   │███│███│   │ Microservices & UI    ║
║ PHASE 5  │   │   │   │   │   │   │   │   │   │   │   │███│ Finalization          ║
║ ─────────┴───┴───┴───┴───┴───┴───┴───┴───┴───┴───┴───┴───┤                       ║
║          │M1 │M2 │   │M3 │   │M4 │M5 │   │M6 │M7 │M8 │M9 │ Milestones            ║
╚═══════════════════════════════════════════════════════════════════════════════════╝
```

### 1.3 Phase Summary với Success Metrics

| Phase | Weeks | Goal | Success Metric | Deliverables |
|-------|-------|------|----------------|--------------|
| **Phase 1** | 1-2 | Chuẩn bị môi trường | 100% tools ready | Environment, KB, Guidelines |
| **Phase 2** | 3-6 | Annotation data | 200+ CVs, IAA ≥ 80% | Annotated dataset |
| **Phase 3** | 7-9 | Train model + Chatbot | F1 ≥ 75%, Chatbot working | NER model, Chatbot core |
| **Phase 4** | 10-11 | Build system | All services integrated | Full application |
| **Phase 5** | 12 | Complete project | All deliverables submitted | Report, Demo |

---

## 2. PHASE 1: Setup & Knowledge Base (Week 1-2)

### 2.1 Phase 1 Overview

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              PHASE 1: SETUP & KB                                 │
│                              Duration: 2 weeks                                   │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│  GOALS:                                                                          │
│  ✓ Development environment fully configured                                     │
│  ✓ Label Studio running with annotation project                                 │
│  ✓ Knowledge Base initialized (O*NET + CV Guides)                              │
│  ✓ Annotation guidelines written and approved                                   │
│  ✓ Annotators trained and ready                                                │
│  ✓ 100 CVs anonymized for annotation                                           │
│                                                                                  │
│  MILESTONES:                                                                     │
│  M1 (End Week 1): Environment Ready                                             │
│  M2 (End Week 2): Annotation Ready to Start                                     │
│                                                                                  │
│  RISK: LOW - Mostly setup tasks, well-documented procedures                     │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

### 2.2 WEEK 1: Environment Setup (26/01 - 01/02/2026)

#### Week 1 Objectives
| # | Objective | Verification |
|---|-----------|--------------|
| 1 | Python environment with all ML libraries | `python -c "import torch; print(torch.__version__)"` works |
| 2 | Label Studio running locally | Access http://localhost:8080 |
| 3 | GitHub repository with proper structure | All folders created, README done |
| 4 | Annotation guidelines draft | Document exists, 10+ entity examples |
| 5 | PDF parsing tested | Successfully extract text from 5 sample CVs |

#### Day-by-Day Tasks

##### Day 1 (Chủ nhật 26/01): Kickoff + Python Setup
| Time | Task | Details | Verification |
|------|------|---------|--------------|
| 09:00-10:00 | Team Kickoff Meeting | Giới thiệu project, timeline, responsibilities | Meeting notes created |
| 10:00-12:00 | Install Python 3.10 | Use pyenv or conda | `python --version` = 3.10.x |
| 13:00-15:00 | Create virtual environment | `python -m venv cv_assistant_env` | Activate successful |
| 15:00-17:00 | Install core libraries | See requirements below | All imports work |

```bash
# Day 1 Commands
python -m venv cv_assistant_env
source cv_assistant_env/bin/activate  # Linux/Mac
# or: cv_assistant_env\Scripts\activate  # Windows

pip install torch==2.1.0 torchvision torchaudio
pip install transformers==4.35.0
pip install datasets seqeval
pip install pandas numpy scikit-learn
pip install pdfplumber PyPDF2
pip install fastapi uvicorn
pip install sentence-transformers
pip install chromadb
pip install llama-index
pip install jupyter notebook

# Verify
python -c "import torch; import transformers; import chromadb; print('OK')"
```

**Day 1 Deliverables:**
- [ ] Python 3.10 installed
- [ ] Virtual environment created
- [ ] All core libraries installed
- [ ] Verification script passes

---

##### Day 2 (Thứ 2, 27/01): GitHub + Project Structure
| Time | Task | Details | Verification |
|------|------|---------|--------------|
| 09:00-11:00 | Create GitHub repository | Name: `cv-assistant` | Repo accessible |
| 11:00-13:00 | Setup project structure | Create all folders | Structure matches below |
| 14:00-16:00 | Create README.md | Project description, setup instructions | README visible on GitHub |
| 16:00-18:00 | Setup .gitignore | Python, data, models | Sensitive files excluded |

```
cv-assistant/
├── README.md
├── requirements.txt
├── .gitignore
├── .env.example
│
├── data/
│   ├── raw/                    # Raw CVs (not in git)
│   ├── processed/              # Processed text
│   ├── annotated/              # Annotated data
│   └── splits/                 # train/val/test
│
├── models/
│   ├── ner/                    # NER model checkpoints
│   └── embeddings/             # Embedding cache
│
├── knowledge_base/
│   ├── onet/                   # O*NET data
│   ├── cv_guides/              # CV writing guides
│   └── chroma_db/              # ChromaDB storage
│
├── services/
│   ├── ner_service/            # FastAPI NER :5001
│   ├── skill_service/          # FastAPI Skill :5002
│   ├── career_service/         # FastAPI Career :5003
│   ├── chatbot_service/        # FastAPI Chatbot :5004
│   └── api_gateway/            # Spring Boot :8080
│
├── frontend/                   # React application
│
├── notebooks/                  # Jupyter notebooks
│   ├── 01_data_exploration.ipynb
│   ├── 02_preprocessing.ipynb
│   ├── 03_training.ipynb
│   └── 04_evaluation.ipynb
│
├── scripts/
│   ├── anonymize.py
│   ├── preprocess.py
│   ├── train.py
│   └── evaluate.py
│
├── docs/                       # Project documentation
│
├── docker-compose.yml
└── Makefile
```

**Day 2 Deliverables:**
- [ ] GitHub repository created
- [ ] Project structure complete
- [ ] README.md written
- [ ] First commit pushed

---

##### Day 3 (Thứ 3, 28/01): Label Studio Setup
| Time | Task | Details | Verification |
|------|------|---------|--------------|
| 09:00-11:00 | Install Label Studio | Docker or pip install | Container/process running |
| 11:00-13:00 | Create admin account | Setup credentials | Login successful |
| 14:00-16:00 | Create NER project | Configure 10 entity labels | Project visible |
| 16:00-18:00 | Test with sample data | Import 5 test CVs | Annotation UI works |

```bash
# Option 1: Docker (Recommended)
docker run -d -p 8080:8080 \
  -v label_studio_data:/label-studio/data \
  --name label-studio \
  heartexlabs/label-studio:latest

# Option 2: pip install
pip install label-studio
label-studio start --port 8080

# Access: http://localhost:8080
# Create account: admin / admin123 (change in production)
```

**Label Studio NER Configuration:**
```xml
<View>
  <Labels name="label" toName="text">
    <Label value="PER" background="#FF6B6B"/>
    <Label value="ORG" background="#4ECDC4"/>
    <Label value="DATE" background="#45B7D1"/>
    <Label value="LOC" background="#96CEB4"/>
    <Label value="SKILL" background="#FFEAA7"/>
    <Label value="DEGREE" background="#DDA0DD"/>
    <Label value="MAJOR" background="#98D8C8"/>
    <Label value="JOB_TITLE" background="#F7DC6F"/>
    <Label value="PROJECT" background="#BB8FCE"/>
    <Label value="CERT" background="#85C1E9"/>
  </Labels>
  <Text name="text" value="$text"/>
</View>
```

**Day 3 Deliverables:**
- [ ] Label Studio running on port 8080
- [ ] Admin account created
- [ ] NER project created with 10 labels
- [ ] Sample annotation tested

---

##### Day 4 (Thứ 4, 29/01): PDF Parsing + Data Preparation
| Time | Task | Details | Verification |
|------|------|---------|--------------|
| 09:00-11:00 | Download sample CVs | 50 CVs from raw data | 50 files in raw/ folder |
| 11:00-13:00 | Implement PDF parser | pdfplumber-based | Parse all 50 successfully |
| 14:00-16:00 | Test text extraction | Quality check | Readable text output |
| 16:00-18:00 | Document parser issues | Note edge cases | Issue log created |

```python
# scripts/pdf_parser.py
import pdfplumber
import os
from pathlib import Path

def parse_pdf(pdf_path: str) -> str:
    """Extract text from PDF file"""
    text = ""
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
    except Exception as e:
        print(f"Error parsing {pdf_path}: {e}")
        return None

    return clean_text(text)

def clean_text(text: str) -> str:
    """Clean extracted text"""
    # Remove multiple spaces
    text = ' '.join(text.split())
    # Remove multiple newlines
    text = '\n'.join(line.strip() for line in text.split('\n') if line.strip())
    return text

def batch_parse(input_dir: str, output_dir: str):
    """Parse all PDFs in directory"""
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    results = {"success": 0, "failed": 0, "failed_files": []}

    for pdf_file in input_path.glob("*.pdf"):
        text = parse_pdf(str(pdf_file))
        if text:
            output_file = output_path / f"{pdf_file.stem}.txt"
            output_file.write_text(text, encoding='utf-8')
            results["success"] += 1
        else:
            results["failed"] += 1
            results["failed_files"].append(pdf_file.name)

    return results

if __name__ == "__main__":
    results = batch_parse("data/raw/sample_50", "data/processed/sample_50")
    print(f"Parsed: {results['success']}, Failed: {results['failed']}")
    if results["failed_files"]:
        print(f"Failed files: {results['failed_files']}")
```

**Day 4 Deliverables:**
- [ ] 50 sample CVs downloaded
- [ ] PDF parser implemented
- [ ] All samples parsed successfully
- [ ] Issue log documented

---

##### Day 5 (Thứ 5, 30/01): Annotation Guidelines Draft
| Time | Task | Details | Verification |
|------|------|---------|--------------|
| 09:00-12:00 | Write guidelines intro | Purpose, 10 entity types | Section 1-2 complete |
| 13:00-16:00 | Write entity definitions | Each type with 5+ examples | All 10 types documented |
| 16:00-18:00 | Write edge cases | Common confusions | 10+ edge cases covered |

**Annotation Guidelines Structure:**
```markdown
# CV Annotation Guidelines v1.0

## 1. Overview
- Purpose of annotation
- What is NER
- What is BIO tagging

## 2. Entity Types (10 types, 21 labels)

### 2.1 PER (Person)
- Definition: Names of individuals
- Examples:
  - ✅ "John Smith" → B-PER I-PER
  - ✅ "Dr. Jane Doe" → B-PER I-PER I-PER
  - ❌ "the candidate" (generic, not specific name)

### 2.2 ORG (Organization)
- Definition: Company/institution names
- Examples:
  - ✅ "Google Inc." → B-ORG I-ORG
  - ✅ "MIT" → B-ORG
  - ❌ "the company" (generic)

[Continue for all 10 types...]

## 3. Edge Cases
- When skills overlap with tools
- Date format variations
- Multi-word job titles

## 4. Quality Checklist
- [ ] All entities tagged
- [ ] Correct entity boundaries
- [ ] No overlapping tags
```

**Day 5 Deliverables:**
- [ ] Guidelines document started
- [ ] All 10 entity types defined
- [ ] 5+ examples per type
- [ ] Edge cases documented

---

##### Day 6 (Thứ 6, 31/01): ChromaDB + Knowledge Base Setup
| Time | Task | Details | Verification |
|------|------|---------|--------------|
| 09:00-11:00 | Setup ChromaDB | Persistent storage | DB accessible |
| 11:00-13:00 | Download O*NET data | Jobs, skills, pathways | Files in knowledge_base/ |
| 14:00-16:00 | Ingest O*NET data | Create embeddings | Query returns results |
| 16:00-18:00 | Create CV guides | 10 basic guides | Guides indexed |

```python
# scripts/setup_knowledge_base.py
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
import json

def setup_chromadb():
    """Initialize ChromaDB with persistent storage"""
    client = chromadb.Client(Settings(
        chroma_db_impl="duckdb+parquet",
        persist_directory="./knowledge_base/chroma_db",
        anonymized_telemetry=False
    ))
    return client

def create_collection(client, name: str):
    """Create or get collection"""
    return client.get_or_create_collection(
        name=name,
        metadata={"hnsw:space": "cosine"}
    )

def ingest_onet_jobs(client):
    """Ingest O*NET occupation data"""
    collection = create_collection(client, "onet_jobs")

    # Load O*NET data (Real Text Database)
    # Using 'Occupation Data.txt' from db_28_1_text.zip
    # ... Implementation details in scripts/setup_knowledge_base.py ...

    # Documents created from Title + Description
    # ...


def test_retrieval(client):
    """Test knowledge base retrieval"""
    collection = client.get_collection("onet_jobs")
    results = collection.query(
        query_texts=["software developer python"],
        n_results=3
    )
    print("Test query results:")
    for doc in results['documents'][0]:
        print(f"- {doc[:100]}...")

if __name__ == "__main__":
    client = setup_chromadb()
    ingest_onet_jobs(client)
    test_retrieval(client)
    client.persist()
    print("Knowledge base setup complete!")
```

**Day 6 Deliverables:**
- [ ] ChromaDB installed and running
- [ ] O*NET data downloaded
- [ ] Data ingested into ChromaDB
- [ ] Test query successful

---

##### Day 7 (Thứ 7, 01/02): Week 1 Review + Buffer
| Time | Task | Details | Verification |
|------|------|---------|--------------|
| 09:00-11:00 | Review all setups | Run verification checklist | All checks pass |
| 11:00-13:00 | Fix any issues | Address problems found | Issues resolved |
| 14:00-16:00 | Document Week 1 | Update project docs | Docs updated |
| 16:00-17:00 | Plan Week 2 | Prepare training materials | Materials ready |

**Week 1 Verification Checklist:**
```bash
# Run all checks
echo "=== Python Environment ==="
python --version
python -c "import torch; import transformers; import chromadb; print('Libraries OK')"

echo "=== Label Studio ==="
curl -s http://localhost:8080/health | grep -q "ok" && echo "Label Studio OK"

echo "=== Project Structure ==="
ls -la cv-assistant/ | head -20

echo "=== Knowledge Base ==="
python -c "
import chromadb
client = chromadb.Client()
print(f'Collections: {client.list_collections()}')
"

echo "=== PDF Parser ==="
python scripts/pdf_parser.py --test

echo "=== All Week 1 Checks Complete ==="
```

---

### 2.3 WEEK 2: Annotation Preparation (02/02 - 08/02/2026)

#### Week 2 Objectives
| # | Objective | Verification |
|---|-----------|--------------|
| 1 | Finalize annotation guidelines | Document approved by team |
| 2 | Train all 4 annotators | Each can annotate 3 CVs correctly |
| 3 | Anonymize 100 CVs | 100 files in processed/ ready |
| 4 | Complete technical docs | All 15+ documents updated |
| 5 | Knowledge base enhanced | CV guides ingested |

#### Day-by-Day Tasks

##### Day 8 (Chủ nhật 02/02): Finalize Guidelines
| Time | Task | Details | Verification |
|------|------|---------|--------------|
| 09:00-12:00 | Review guidelines with examples | Add real CV examples | 20+ examples added |
| 13:00-15:00 | Create decision tree | For edge cases | Decision tree complete |
| 15:00-17:00 | Create annotation video | Screen recording tutorial | 10-min video ready |

**Day 8 Deliverables:**
- [ ] Guidelines v1.0 finalized
- [ ] Edge case decision tree
- [ ] Tutorial video created

---

##### Day 9 (Thứ 2, 03/02): Annotator Training Session 1
| Time | Task | Details | Verification |
|------|------|---------|--------------|
| 09:00-10:30 | Training session (All) | Present guidelines, demo | All attend |
| 10:30-12:00 | Hands-on practice | Annotate 2 CVs together | All complete |
| 13:00-15:00 | Q&A session | Address confusions | Questions logged |
| 15:00-17:00 | Individual practice | Each annotates 1 CV | 4 CVs annotated |

**Training Agenda:**
```
09:00 - 09:15: Welcome, project overview
09:15 - 09:45: What is NER? What is BIO tagging?
09:45 - 10:15: 10 Entity types with examples
10:15 - 10:30: Label Studio demo

10:30 - 11:30: Practice together (CV 1)
11:30 - 12:00: Practice together (CV 2)

13:00 - 14:00: Edge cases and common mistakes
14:00 - 15:00: Q&A

15:00 - 17:00: Individual practice
```

**Day 9 Deliverables:**
- [ ] All 4 annotators trained
- [ ] 6 practice CVs annotated (2 together + 4 individual)
- [ ] Q&A log created

---

##### Day 10 (Thứ 3, 04/02): Practice Review + Anonymization Script
| Time | Task | Details | Verification |
|------|------|---------|--------------|
| 09:00-11:00 | Review practice annotations | Compare, give feedback | Feedback given to each |
| 11:00-13:00 | Implement anonymization | Regex-based PII removal | Script works |
| 14:00-17:00 | Annotators practice more | 2 more CVs each | 8 more CVs done |

```python
# scripts/anonymize.py
import re
from pathlib import Path

def anonymize_text(text: str) -> str:
    """Remove PII from CV text"""

    # Email addresses
    text = re.sub(
        r'[\w\.-]+@[\w\.-]+\.\w+',
        '[EMAIL]',
        text
    )

    # Phone numbers (various formats)
    text = re.sub(
        r'(\+?\d{1,3}[-.\s]?)?\(?\d{2,4}\)?[-.\s]?\d{3,4}[-.\s]?\d{3,4}',
        '[PHONE]',
        text
    )

    # Specific addresses (street numbers)
    text = re.sub(
        r'\d+\s+[\w\s]+(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Lane|Ln|Drive|Dr)\b',
        '[ADDRESS]',
        text,
        flags=re.IGNORECASE
    )

    # ID numbers (passport, CMND, etc.)
    text = re.sub(
        r'\b\d{9,12}\b',
        '[ID_NUMBER]',
        text
    )

    return text

def anonymize_batch(input_dir: str, output_dir: str):
    """Anonymize all text files in directory"""
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    count = 0
    for txt_file in input_path.glob("*.txt"):
        text = txt_file.read_text(encoding='utf-8')
        anon_text = anonymize_text(text)

        output_file = output_path / txt_file.name
        output_file.write_text(anon_text, encoding='utf-8')
        count += 1

    print(f"Anonymized {count} files")
    return count

if __name__ == "__main__":
    anonymize_batch(
        "data/processed/parsed",
        "data/processed/anonymized"
    )
```

**Day 10 Deliverables:**
- [ ] Practice annotations reviewed
- [ ] Feedback given to each annotator
- [ ] Anonymization script working
- [ ] 8 more practice CVs annotated

---

##### Day 11 (Thứ 4, 05/02): Annotator Training Session 2 + IAA
| Time | Task | Details | Verification |
|------|------|---------|--------------|
| 09:00-10:00 | Address common errors | From Day 10 review | Errors understood |
| 10:00-12:00 | Double annotation | 5 CVs by 2 annotators each | 5 CVs × 2 annotations |
| 13:00-15:00 | Calculate IAA | Cohen's Kappa | IAA score computed |
| 15:00-17:00 | Resolve disagreements | Discuss, create rules | Rules documented |

```python
# scripts/calculate_iaa.py
from sklearn.metrics import cohen_kappa_score
import json

def load_annotations(file_path: str) -> list:
    """Load annotations from Label Studio export"""
    with open(file_path) as f:
        data = json.load(f)
    return data

def extract_labels(annotation: dict, text: str) -> list:
    """Convert annotations to token-level labels"""
    # Tokenize text
    tokens = text.split()
    labels = ['O'] * len(tokens)

    # Map character offsets to token indices
    for entity in annotation.get('result', []):
        start = entity['value']['start']
        end = entity['value']['end']
        label = entity['value']['labels'][0]

        # Find token indices (simplified)
        # ... implementation

    return labels

def calculate_iaa(annotations_a: list, annotations_b: list) -> float:
    """Calculate Inter-Annotator Agreement"""
    all_labels_a = []
    all_labels_b = []

    for ann_a, ann_b in zip(annotations_a, annotations_b):
        labels_a = extract_labels(ann_a, ann_a['text'])
        labels_b = extract_labels(ann_b, ann_b['text'])

        all_labels_a.extend(labels_a)
        all_labels_b.extend(labels_b)

    kappa = cohen_kappa_score(all_labels_a, all_labels_b)
    return kappa

if __name__ == "__main__":
    # Load double-annotated CVs
    ann_a = load_annotations("data/annotated/annotator_1.json")
    ann_b = load_annotations("data/annotated/annotator_2.json")

    iaa = calculate_iaa(ann_a, ann_b)
    print(f"Inter-Annotator Agreement (Kappa): {iaa:.2f}")

    if iaa >= 0.8:
        print("✅ IAA >= 80% - Ready to proceed")
    else:
        print("⚠️ IAA < 80% - Need more training")
```

**Day 11 Deliverables:**
- [ ] Common errors addressed
- [ ] 5 CVs double-annotated
- [ ] IAA calculated (target ≥ 80%)
- [ ] Disagreement rules documented

---

##### Day 12 (Thứ 5, 06/02): Anonymize 100 CVs
| Time | Task | Details | Verification |
|------|------|---------|--------------|
| 09:00-11:00 | Parse 100 raw CVs | PDF to text | 100 .txt files |
| 11:00-13:00 | Anonymize all | Run script | PII removed |
| 14:00-16:00 | Manual QC | Check 10 random files | No PII leakage |
| 16:00-18:00 | Import to Label Studio | Create tasks | 100 tasks visible |

**Day 12 Deliverables:**
- [ ] 100 CVs parsed
- [ ] 100 CVs anonymized
- [ ] QC passed (no PII)
- [ ] Imported to Label Studio

---

##### Day 13 (Thứ 6, 07/02): Complete Documentation + KB Enhancement
| Time | Task | Details | Verification |
|------|------|---------|--------------|
| 09:00-12:00 | Update all docs | 01-15 reviewed | Docs consistent |
| 13:00-15:00 | Create CV writing guides | 10 markdown files | Files in kb/ |
| 15:00-17:00 | Ingest guides to KB | Embed and index | Query returns guides |

**CV Writing Guides to Create:**
```
knowledge_base/cv_guides/
├── 01_contact_information.md
├── 02_professional_summary.md
├── 03_work_experience.md
├── 04_education.md
├── 05_skills_section.md
├── 06_projects.md
├── 07_certifications.md
├── 08_action_verbs.md
├── 09_quantifying_achievements.md
└── 10_common_mistakes.md
```

**Day 13 Deliverables:**
- [ ] All docs updated
- [ ] 10 CV guides created
- [ ] Guides ingested to ChromaDB

---

##### Day 14 (Thứ 7, 08/02): Week 2 Review + Phase 1 Completion
| Time | Task | Details | Verification |
|------|------|---------|--------------|
| 09:00-11:00 | Phase 1 review meeting | All team | Checklist complete |
| 11:00-13:00 | Fix any remaining issues | Blockers resolved | All issues closed |
| 14:00-16:00 | Prepare Phase 2 | Assign CV batches | Assignments ready |
| 16:00-17:00 | Week 3 kickoff prep | Communication plan | Plan documented |

**Phase 1 Completion Checklist:**
```
PHASE 1 SIGN-OFF CHECKLIST
══════════════════════════

Environment:
□ Python 3.10 + venv working
□ All ML libraries installed
□ Label Studio running
□ ChromaDB running
□ GitHub repo with proper structure

Knowledge Base:
□ O*NET data ingested (1000+ occupations)
□ CV guides ingested (10 documents)
□ Query retrieval working

Annotation Prep:
□ Guidelines v1.0 finalized
□ All 4 annotators trained
□ IAA ≥ 80% achieved
□ 100 CVs anonymized and imported

Documentation:
□ All technical docs updated
□ README complete
□ Annotation guidelines published

SIGN-OFF:
□ Leader: _____________ Date: _______
□ Ready to start Phase 2: YES / NO
```

---

## 3. PHASE 2: Data Annotation (Week 3-6)

### 3.1 Phase 2 Overview

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           PHASE 2: DATA ANNOTATION                               │
│                              Duration: 4 weeks                                   │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│  GOALS:                                                                          │
│  ✓ Annotate 200+ CVs with 10 entity types                                       │
│  ✓ Maintain IAA ≥ 80% throughout                                                │
│  ✓ Export data in CoNLL format                                                  │
│  ✓ Create train/val/test splits (70/15/15)                                     │
│                                                                                  │
│  WEEKLY TARGETS:                                                                 │
│  Week 3: 50-60 CVs (12-15 per annotator)                                        │
│  Week 4: 50-60 CVs (cumulative: 100-120)                                        │
│  Week 5: 50-60 CVs (cumulative: 150-180)                                        │
│  Week 6: 40-50 CVs (cumulative: 200+) + Export                                  │
│                                                                                  │
│  MILESTONES:                                                                     │
│  M3 (End Week 4): 100 CVs annotated, IAA verified                               │
│  M4 (End Week 6): 200+ CVs annotated, data exported                             │
│                                                                                  │
│  RISK: MEDIUM - Annotator availability, quality consistency                     │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### 3.2 Annotation Assignment Matrix

| Annotator | Week 3 | Week 4 | Week 5 | Week 6 | Total |
|-----------|--------|--------|--------|--------|-------|
| Annotator 1 | CV 001-015 | CV 051-065 | CV 101-115 | CV 151-162 | 52 |
| Annotator 2 | CV 016-030 | CV 066-080 | CV 116-130 | CV 163-174 | 52 |
| Annotator 3 | CV 031-045 | CV 081-095 | CV 131-145 | CV 175-186 | 52 |
| Annotator 4 | CV 046-050 + QC | CV 096-100 + QC | CV 146-150 + QC | CV 187-200 + QC | 44 |
| **Total** | **50** | **50** | **50** | **50** | **200** |

### 3.3 Weekly Annotation Template

#### WEEK 3 (09/02 - 15/02): First Batch

**Week 3 Goals:**
- [ ] 50 CVs annotated
- [ ] QC passed on 10% (5 CVs)
- [ ] IAA check on 5 CVs
- [ ] All issues logged

**Daily Schedule:**
| Day | Annotator 1 | Annotator 2 | Annotator 3 | Annotator 4 | Leader |
|-----|-------------|-------------|-------------|-------------|--------|
| Mon | 3 CVs | 3 CVs | 3 CVs | 2 CVs | QC setup |
| Tue | 3 CVs | 3 CVs | 3 CVs | 3 CVs | QC 2 CVs |
| Wed | 3 CVs | 3 CVs | 3 CVs | 3 CVs | QC 2 CVs |
| Thu | 3 CVs | 3 CVs | 3 CVs | 3 CVs | QC 2 CVs |
| Fri | 3 CVs | 3 CVs | 3 CVs | 3 CVs | IAA calc |
| Sat | Buffer | Buffer | Buffer | Buffer | Weekly sync |

**Week 3 QC Process:**
```
Daily QC:
1. Leader randomly selects 2 CVs from completed work
2. Reviews for:
   □ All entities tagged
   □ Correct entity types
   □ Correct boundaries
   □ No missed entities
3. Logs errors in QC spreadsheet
4. Sends feedback to annotator

Weekly IAA:
1. Select 5 CVs
2. Have 2 annotators annotate same CVs
3. Calculate Cohen's Kappa
4. Target: ≥ 0.80
```

**Week 3 Deliverables:**
- [ ] 50 CVs annotated
- [ ] QC report for Week 3
- [ ] IAA score: _____ (target ≥ 0.80)
- [ ] Error log updated

---

#### WEEK 4 (16/02 - 22/02): Second Batch

**Week 4 Goals:**
- [ ] 50 more CVs annotated (cumulative: 100)
- [ ] QC passed
- [ ] IAA maintained ≥ 80%
- [ ] Anonymize 100 more CVs

**Day 16 (Mon): Week 3 Review Meeting**
```
Agenda (30 mins):
1. Progress check (5 min)
2. Common errors from Week 3 QC (10 min)
3. Clarify guidelines (10 min)
4. Week 4 assignments (5 min)
```

**Week 4 Deliverables:**
- [ ] 100 total CVs annotated
- [ ] QC report for Week 4
- [ ] IAA verified
- [ ] 100 more CVs anonymized (total: 200 ready)

---

#### WEEK 5 (23/02 - 01/03): Third Batch

**Week 5 Goals:**
- [ ] 50 more CVs annotated (cumulative: 150)
- [ ] Start preprocessing code
- [ ] Prepare for final push

**Parallel Task (Leader):**
While annotators continue, leader starts preprocessing:
```python
# notebooks/02_preprocessing.ipynb
# Start developing preprocessing pipeline

1. Load CoNLL data
2. Tokenize with BERT tokenizer
3. Align labels with subword tokens
4. Create PyTorch Dataset
5. Verify with small sample
```

**Week 5 Deliverables:**
- [ ] 150 total CVs annotated
- [ ] Preprocessing code drafted
- [ ] Week 6 plan confirmed

---

#### WEEK 6 (02/03 - 08/03): Final Batch + Export

**Week 6 Goals:**
- [ ] Complete 200+ CVs
- [ ] Final QC pass
- [ ] Export to CoNLL format
- [ ] Create train/val/test splits

**Day 36 (Mon-Wed): Complete Annotation**
| Day | Task | Target |
|-----|------|--------|
| Mon | Annotate remaining | Reach 180 |
| Tue | Annotate remaining | Reach 190 |
| Wed | Annotate remaining | Reach 200+ |

**Day 39 (Thu): Final QC**
```
Final QC Process:
1. Export all annotations
2. Run consistency checks:
   □ All CVs have annotations
   □ No empty annotations
   □ Entity type distribution reasonable
3. Random sample 20 CVs for detailed review
4. Fix any issues found
```

**Day 40 (Fri): Export Data**
```python
# scripts/export_conll.py

def export_to_conll(annotations: list, output_file: str):
    """Export Label Studio annotations to CoNLL format"""
    with open(output_file, 'w') as f:
        for ann in annotations:
            text = ann['text']
            entities = ann['result']

            # Convert to CoNLL format
            tokens, labels = convert_to_bio(text, entities)

            for token, label in zip(tokens, labels):
                f.write(f"{token}\t{label}\n")
            f.write("\n")  # Sentence separator

def create_splits(conll_file: str, output_dir: str):
    """Create train/val/test splits (70/15/15)"""
    import random

    # Load all sentences
    sentences = load_conll(conll_file)
    random.shuffle(sentences)

    n = len(sentences)
    train_end = int(0.7 * n)
    val_end = int(0.85 * n)

    train = sentences[:train_end]
    val = sentences[train_end:val_end]
    test = sentences[val_end:]

    save_conll(train, f"{output_dir}/train.conll")
    save_conll(val, f"{output_dir}/val.conll")
    save_conll(test, f"{output_dir}/test.conll")

    print(f"Split: train={len(train)}, val={len(val)}, test={len(test)}")
```

**Day 41 (Sat): Phase 2 Completion**
```
PHASE 2 SIGN-OFF CHECKLIST
══════════════════════════

Annotation:
□ 200+ CVs annotated
□ Final count: _____ CVs

Quality:
□ Final IAA: _____ (target ≥ 0.80)
□ Final QC passed
□ No major issues remaining

Data Export:
□ CoNLL format exported
□ File: data/annotated/all_annotations.conll

Splits Created:
□ train.conll: _____ sentences
□ val.conll: _____ sentences
□ test.conll: _____ sentences

Statistics:
□ Total tokens: _____
□ Entity distribution documented
□ Annotation report created

SIGN-OFF:
□ Leader: _____________ Date: _______
□ Ready to start Phase 3: YES / NO
```

---

## 4. PHASE 3: Model & Chatbot Development (Week 7-9)

### 4.1 Phase 3 Overview

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                       PHASE 3: MODEL & CHATBOT DEVELOPMENT                       │
│                              Duration: 3 weeks                                   │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│  TRACK A - NER MODEL (Week 7-9):                                                │
│  ✓ Preprocess annotated data                                                    │
│  ✓ Train BERT-based NER model                                                   │
│  ✓ Hyperparameter tuning                                                        │
│  ✓ Achieve F1 ≥ 75%                                                             │
│  ✓ Error analysis and documentation                                             │
│                                                                                  │
│  TRACK B - CHATBOT (Week 7-9):                                                  │
│  ✓ Setup Ollama + Llama 3.2                                                     │
│  ✓ Setup LlamaIndex + RAG                                                       │
│  ✓ Implement ReAct agent                                                        │
│  ✓ Create tool calling for NER/Skill/Career                                    │
│  ✓ Implement conversation memory                                                │
│                                                                                  │
│  MILESTONES:                                                                     │
│  M5 (End Week 7): Baseline trained, Ollama running                              │
│  M6 (End Week 9): F1 ≥ 75%, Chatbot core functional                            │
│                                                                                  │
│  RISK: MEDIUM-HIGH - Model performance, GPU availability                        │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### 4.2 WEEK 7: Baseline Training + Chatbot Setup (09/03 - 15/03)

#### Week 7 Goals
| Track | Goal | Success Metric |
|-------|------|----------------|
| NER | Train baseline model | Training completes, F1 recorded |
| NER | Preprocessing pipeline | All data processed correctly |
| Chatbot | Ollama running | Llama 3.2 responds to queries |
| Chatbot | LlamaIndex basic | Simple chat working |

#### Day-by-Day Tasks

##### Day 42 (Mon 09/03): Data Preprocessing
| Time | Task | Details |
|------|------|---------|
| 09:00-12:00 | Load and validate CoNLL data | Check format, count entities |
| 13:00-15:00 | Implement BertTokenizer integration | Subword tokenization |
| 15:00-18:00 | Implement label alignment | Handle subword tokens |

```python
# scripts/preprocess.py

from transformers import BertTokenizer
from torch.utils.data import Dataset
import torch

class NERDataset(Dataset):
    def __init__(self, conll_file: str, tokenizer_name: str = 'bert-base-uncased'):
        self.tokenizer = BertTokenizer.from_pretrained(tokenizer_name)
        self.sentences, self.labels = self.load_conll(conll_file)
        self.label2id = self.create_label_map()

    def load_conll(self, file_path: str):
        sentences = []
        labels = []
        current_sent = []
        current_labels = []

        with open(file_path) as f:
            for line in f:
                line = line.strip()
                if line:
                    parts = line.split('\t')
                    current_sent.append(parts[0])
                    current_labels.append(parts[1])
                else:
                    if current_sent:
                        sentences.append(current_sent)
                        labels.append(current_labels)
                        current_sent = []
                        current_labels = []

        return sentences, labels

    def create_label_map(self):
        """Create label to ID mapping for 21 BIO labels"""
        labels = ['O',
                  'B-PER', 'I-PER',
                  'B-ORG', 'I-ORG',
                  'B-DATE', 'I-DATE',
                  'B-LOC', 'I-LOC',
                  'B-SKILL', 'I-SKILL',
                  'B-DEGREE', 'I-DEGREE',
                  'B-MAJOR', 'I-MAJOR',
                  'B-JOB_TITLE', 'I-JOB_TITLE',
                  'B-PROJECT', 'I-PROJECT',
                  'B-CERT', 'I-CERT']
        return {label: i for i, label in enumerate(labels)}

    def __len__(self):
        return len(self.sentences)

    def __getitem__(self, idx):
        tokens = self.sentences[idx]
        labels = self.labels[idx]

        # Tokenize
        encoding = self.tokenizer(
            tokens,
            is_split_into_words=True,
            padding='max_length',
            truncation=True,
            max_length=512,
            return_tensors='pt'
        )

        # Align labels
        aligned_labels = self.align_labels(encoding, labels)

        return {
            'input_ids': encoding['input_ids'].squeeze(),
            'attention_mask': encoding['attention_mask'].squeeze(),
            'labels': torch.tensor(aligned_labels)
        }

    def align_labels(self, encoding, labels):
        """Align labels with subword tokens"""
        word_ids = encoding.word_ids()
        aligned = []
        prev_word_id = None

        for word_id in word_ids:
            if word_id is None:
                aligned.append(-100)  # Special tokens
            elif word_id != prev_word_id:
                aligned.append(self.label2id[labels[word_id]])
            else:
                # Subword continuation
                label = labels[word_id]
                if label.startswith('B-'):
                    aligned.append(self.label2id['I-' + label[2:]])
                else:
                    aligned.append(self.label2id[label])
            prev_word_id = word_id

        return aligned

# Test
if __name__ == "__main__":
    dataset = NERDataset("data/splits/train.conll")
    print(f"Dataset size: {len(dataset)}")
    sample = dataset[0]
    print(f"Sample shape: input_ids={sample['input_ids'].shape}")
```

**Day 42 Deliverables:**
- [ ] CoNLL data loaded and validated
- [ ] NERDataset class implemented
- [ ] Label alignment working
- [ ] Test with sample data

---

##### Day 43 (Tue 10/03): Training Script Setup
| Time | Task | Details |
|------|------|---------|
| 09:00-12:00 | Setup Hugging Face Trainer | Configure training args |
| 13:00-15:00 | Implement metrics computation | F1, Precision, Recall |
| 15:00-18:00 | Test on small sample | Verify pipeline works |

```python
# scripts/train.py

from transformers import (
    BertForTokenClassification,
    TrainingArguments,
    Trainer,
    DataCollatorForTokenClassification
)
from datasets import load_metric
import numpy as np

def create_model(num_labels: int = 21):
    """Create BERT model for NER"""
    model = BertForTokenClassification.from_pretrained(
        'bert-base-uncased',
        num_labels=num_labels
    )
    return model

def compute_metrics(p):
    """Compute NER metrics"""
    predictions, labels = p
    predictions = np.argmax(predictions, axis=2)

    # Remove ignored index (-100)
    true_predictions = [
        [id2label[p] for (p, l) in zip(prediction, label) if l != -100]
        for prediction, label in zip(predictions, labels)
    ]
    true_labels = [
        [id2label[l] for (p, l) in zip(prediction, label) if l != -100]
        for prediction, label in zip(predictions, labels)
    ]

    metric = load_metric("seqeval")
    results = metric.compute(predictions=true_predictions, references=true_labels)

    return {
        "precision": results["overall_precision"],
        "recall": results["overall_recall"],
        "f1": results["overall_f1"],
    }

def train(train_dataset, val_dataset, output_dir: str = "./models/ner"):
    """Train NER model"""
    model = create_model()

    training_args = TrainingArguments(
        output_dir=output_dir,
        num_train_epochs=10,
        per_device_train_batch_size=16,
        per_device_eval_batch_size=16,
        warmup_ratio=0.1,
        weight_decay=0.01,
        learning_rate=2e-5,
        evaluation_strategy="epoch",
        save_strategy="epoch",
        load_best_model_at_end=True,
        metric_for_best_model="f1",
        logging_dir="./logs",
        logging_steps=100,
        save_total_limit=3,
    )

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=val_dataset,
        compute_metrics=compute_metrics,
        data_collator=DataCollatorForTokenClassification(tokenizer)
    )

    trainer.train()
    return trainer

if __name__ == "__main__":
    # Load datasets
    train_dataset = NERDataset("data/splits/train.conll")
    val_dataset = NERDataset("data/splits/val.conll")

    # Train
    trainer = train(train_dataset, val_dataset)

    # Save
    trainer.save_model("./models/ner/final")
    print("Training complete!")
```

**Day 43 Deliverables:**
- [ ] Training script complete
- [ ] Metrics computation working
- [ ] Small sample test passed

---

##### Day 44 (Wed 11/03): Train Baseline + Setup Ollama
| Time | Task | Details |
|------|------|---------|
| 09:00-12:00 | Train baseline on full data | Use Google Colab T4 |
| 13:00-15:00 | Install Ollama | Docker or native |
| 15:00-18:00 | Download Llama 3.2 (3B) | Pull model |

```bash
# Ollama Installation
# Option 1: Docker
docker run -d -v ollama:/root/.ollama -p 11434:11434 --name ollama ollama/ollama

# Option 2: Native (Linux)
curl -fsSL https://ollama.com/install.sh | sh

# Pull Llama 3.2 (3B) - smaller for local deployment
ollama pull llama3.2:3b

# Test
ollama run llama3.2:3b "Hello, how are you?"
```

**Day 44 Deliverables:**
- [ ] Baseline model trained
- [ ] Baseline F1 recorded: _____
- [ ] Ollama installed and running
- [ ] Llama 3.2 responding

---

##### Day 45 (Thu 12/03): Evaluate Baseline + Setup LlamaIndex
| Time | Task | Details |
|------|------|---------|
| 09:00-12:00 | Evaluate baseline on test set | Record metrics |
| 13:00-15:00 | Setup LlamaIndex | Connect to Ollama |
| 15:00-18:00 | Test basic chat | Simple query-response |

```python
# services/chatbot_service/llama_setup.py

from llama_index.core import Settings
from llama_index.llms.ollama import Ollama
from llama_index.embeddings.huggingface import HuggingFaceEmbedding

def setup_llama_index():
    """Configure LlamaIndex with Ollama"""

    # Setup LLM
    llm = Ollama(
        model="llama3.2:3b",
        base_url="http://localhost:11434",
        temperature=0.7,
        request_timeout=120.0
    )

    # Setup embedding model
    embed_model = HuggingFaceEmbedding(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )

    # Configure global settings
    Settings.llm = llm
    Settings.embed_model = embed_model
    Settings.chunk_size = 512
    Settings.chunk_overlap = 50

    return llm, embed_model

def test_chat():
    """Test basic chat functionality"""
    llm, _ = setup_llama_index()

    response = llm.complete("What skills should a software developer have?")
    print(f"Response: {response}")

    return response

if __name__ == "__main__":
    test_chat()
```

**Day 45 Deliverables:**
- [ ] Baseline test F1: _____
- [ ] LlamaIndex configured
- [ ] Basic chat working

---

##### Day 46 (Fri 13/03): Document Results + Plan Week 8
| Time | Task | Details |
|------|------|---------|
| 09:00-12:00 | Document baseline results | Create experiment log |
| 13:00-15:00 | Analyze baseline errors | Common mistakes |
| 15:00-17:00 | Plan Week 8 experiments | Learning rates, batch sizes |

**Experiment Log Template:**
```markdown
# Experiment Log - NER Model

## Experiment 1: Baseline
- **Date**: 11/03/2026
- **Config**: lr=2e-5, batch=16, epochs=10
- **Results**:
  - Train Loss: _____
  - Val F1: _____
  - Test F1: _____
- **Per-Entity F1**:
  - PER: _____
  - ORG: _____
  - SKILL: _____
  - ...
- **Notes**: [observations]
```

**Day 46 Deliverables:**
- [ ] Experiment log created
- [ ] Error analysis documented
- [ ] Week 8 experiment plan ready

---

##### Day 47-48 (Sat-Sun 14-15/03): Buffer / Catch-up

**Week 7 Completion Checklist:**
```
WEEK 7 SIGN-OFF
═══════════════

NER Track:
□ Preprocessing pipeline complete
□ Training script working
□ Baseline model trained
□ Baseline F1: _____ (record even if low)
□ Experiment log started

Chatbot Track:
□ Ollama installed and running
□ Llama 3.2 (3B) downloaded
□ LlamaIndex configured
□ Basic chat functional

Ready for Week 8: YES / NO
```

---

### 4.3 WEEK 8: Hyperparameter Tuning + RAG Pipeline (16/03 - 22/03)

#### Week 8 Goals
| Track | Goal | Success Metric |
|-------|------|----------------|
| NER | Find best hyperparameters | F1 improvement over baseline |
| NER | Try data augmentation | Additional experiments |
| Chatbot | RAG pipeline working | Retrieval returns relevant docs |
| Chatbot | ChromaDB integration | Knowledge base queryable |

#### Experiment Matrix

```
HYPERPARAMETER SEARCH GRID
══════════════════════════

Learning Rate × Batch Size × Epochs
───────────────────────────────────
Experiment 2:  lr=1e-5,  batch=16, epochs=10
Experiment 3:  lr=3e-5,  batch=16, epochs=10
Experiment 4:  lr=5e-5,  batch=16, epochs=10
Experiment 5:  lr=2e-5,  batch=8,  epochs=10
Experiment 6:  lr=2e-5,  batch=32, epochs=10
Experiment 7:  lr=2e-5,  batch=16, epochs=15
Experiment 8:  lr=2e-5,  batch=16, epochs=20

Best config from above → Experiment 9 with early stopping
Experiment 10: Best config + data augmentation (if time)

Target: Find config with F1 ≥ 75%
```

#### Day-by-Day Tasks

##### Day 49-51 (Mon-Wed): Run Experiments
| Day | Experiments | Notes |
|-----|-------------|-------|
| Mon | Exp 2, 3, 4 | Learning rate sweep |
| Tue | Exp 5, 6 | Batch size sweep |
| Wed | Exp 7, 8 | Epoch sweep |

**Google Colab Script:**
```python
# notebooks/03_training.ipynb

# Mount drive for checkpoints
from google.colab import drive
drive.mount('/content/drive')

# Run experiment
experiment_config = {
    'learning_rate': 2e-5,
    'batch_size': 16,
    'epochs': 10,
    'experiment_name': 'exp_02'
}

# Train
trainer = train_with_config(experiment_config)

# Log results
log_experiment_results(experiment_config, trainer)
```

---

##### Day 52-53 (Thu-Fri): RAG Pipeline Development
| Time | Task | Details |
|------|------|---------|
| Thu 09:00-12:00 | Connect LlamaIndex to ChromaDB | Vector store integration |
| Thu 13:00-18:00 | Create retrieval pipeline | Query → retrieve → context |
| Fri 09:00-12:00 | Test retrieval quality | Manual evaluation |
| Fri 13:00-17:00 | Tune chunk size and top_k | Optimize retrieval |

```python
# services/chatbot_service/rag_pipeline.py

from llama_index.core import VectorStoreIndex, StorageContext
from llama_index.vector_stores.chroma import ChromaVectorStore
import chromadb

class RAGPipeline:
    def __init__(self):
        # Connect to ChromaDB
        self.chroma_client = chromadb.PersistentClient(
            path="./knowledge_base/chroma_db"
        )
        self.collection = self.chroma_client.get_collection("cv_assistant_kb")

        # Create vector store
        self.vector_store = ChromaVectorStore(
            chroma_collection=self.collection
        )

        # Create index
        storage_context = StorageContext.from_defaults(
            vector_store=self.vector_store
        )
        self.index = VectorStoreIndex.from_vector_store(
            vector_store=self.vector_store,
            storage_context=storage_context
        )

        # Create retriever
        self.retriever = self.index.as_retriever(
            similarity_top_k=5
        )

    def retrieve(self, query: str) -> list:
        """Retrieve relevant documents"""
        nodes = self.retriever.retrieve(query)
        return [
            {
                "text": node.node.text,
                "score": node.score
            }
            for node in nodes
        ]

    def query_with_context(self, query: str) -> str:
        """Query with RAG context"""
        query_engine = self.index.as_query_engine()
        response = query_engine.query(query)
        return str(response)

# Test
if __name__ == "__main__":
    rag = RAGPipeline()

    # Test retrieval
    results = rag.retrieve("What skills does a software developer need?")
    for r in results:
        print(f"Score: {r['score']:.3f} - {r['text'][:100]}...")

    # Test query
    answer = rag.query_with_context("How should I write my professional summary?")
    print(f"\nAnswer: {answer}")
```

**Day 52-53 Deliverables:**
- [ ] RAG pipeline connected to ChromaDB
- [ ] Retrieval returning relevant results
- [ ] Query engine working

---

##### Day 54-55 (Sat-Sun): Week 8 Review + Best Model

**Week 8 Completion Checklist:**
```
WEEK 8 SIGN-OFF
═══════════════

Experiments Completed:
□ Experiment 2 (lr=1e-5): F1 = _____
□ Experiment 3 (lr=3e-5): F1 = _____
□ Experiment 4 (lr=5e-5): F1 = _____
□ Experiment 5 (batch=8): F1 = _____
□ Experiment 6 (batch=32): F1 = _____
□ Experiment 7 (epochs=15): F1 = _____
□ Experiment 8 (epochs=20): F1 = _____

Best Config: lr=_____, batch=_____, epochs=_____
Best Val F1: _____

RAG Pipeline:
□ ChromaDB integration complete
□ Retrieval quality verified
□ Query engine working

Ready for Week 9: YES / NO
```

---

### 4.4 WEEK 9: Final Model + ReAct Agent (23/03 - 29/03)

#### Week 9 Goals
| Track | Goal | Success Metric |
|-------|------|----------------|
| NER | Train final model | F1 ≥ 75% on test set |
| NER | Error analysis | Document common mistakes |
| Chatbot | ReAct agent | Tool calling working |
| Chatbot | NER tool | CV analysis via chatbot |
| Chatbot | Memory | Conversation context preserved |

#### Day-by-Day Tasks

##### Day 56-57 (Mon-Tue): Final NER Training
| Time | Task | Details |
|------|------|---------|
| Mon | Train final model | Best config from Week 8 |
| Tue 09:00-12:00 | Evaluate on test set | Final metrics |
| Tue 13:00-18:00 | Error analysis | Confusion matrix, per-entity |

```python
# scripts/evaluate.py

from seqeval.metrics import classification_report, f1_score
from sklearn.metrics import confusion_matrix
import matplotlib.pyplot as plt
import seaborn as sns

def evaluate_model(model, test_dataset, id2label):
    """Complete model evaluation"""

    predictions = []
    labels = []

    for batch in test_dataset:
        outputs = model(**batch)
        preds = outputs.logits.argmax(-1)
        predictions.extend(preds.tolist())
        labels.extend(batch['labels'].tolist())

    # Convert to labels
    true_preds = []
    true_labels = []
    for pred_seq, label_seq in zip(predictions, labels):
        true_preds.append([id2label[p] for p, l in zip(pred_seq, label_seq) if l != -100])
        true_labels.append([id2label[l] for p, l in zip(pred_seq, label_seq) if l != -100])

    # Classification report
    report = classification_report(true_labels, true_preds)
    print(report)

    # Overall F1
    f1 = f1_score(true_labels, true_preds)
    print(f"\nOverall F1: {f1:.4f}")

    return f1, report

def plot_confusion_matrix(true_labels, predictions, labels):
    """Plot confusion matrix"""
    flat_true = [l for seq in true_labels for l in seq]
    flat_pred = [p for seq in predictions for p in seq]

    cm = confusion_matrix(flat_true, flat_pred, labels=labels)

    plt.figure(figsize=(15, 12))
    sns.heatmap(cm, annot=True, fmt='d', xticklabels=labels, yticklabels=labels)
    plt.title('NER Confusion Matrix')
    plt.ylabel('True Label')
    plt.xlabel('Predicted Label')
    plt.savefig('results/confusion_matrix.png', dpi=300, bbox_inches='tight')
    plt.show()

def error_analysis(predictions, true_labels, texts):
    """Analyze common errors"""
    errors = {
        'false_positives': [],
        'false_negatives': [],
        'wrong_type': [],
        'boundary_errors': []
    }

    # Analyze each prediction
    for pred, true, text in zip(predictions, true_labels, texts):
        # ... detailed error analysis
        pass

    return errors
```

**Day 56-57 Deliverables:**
- [ ] Final model trained with best config
- [ ] Test F1: _____ (target ≥ 75%)
- [ ] Classification report saved
- [ ] Confusion matrix plotted
- [ ] Error analysis documented

---

##### Day 58-59 (Wed-Thu): ReAct Agent Implementation
| Time | Task | Details |
|------|------|---------|
| Wed 09:00-12:00 | Create NER tool | Wrap inference as tool |
| Wed 13:00-18:00 | Create Skill Matching tool | Embedding-based matching |
| Thu 09:00-12:00 | Create Career tool | O*NET-based recommendations |
| Thu 13:00-18:00 | Implement ReAct agent | Tool orchestration |

```python
# services/chatbot_service/tools.py

from llama_index.core.tools import FunctionTool
import requests

def create_ner_tool():
    """Create NER extraction tool"""

    def extract_entities(cv_text: str) -> dict:
        """Extract named entities from CV text using NER model.

        Args:
            cv_text: The CV text to analyze

        Returns:
            Dictionary with extracted entities
        """
        response = requests.post(
            "http://localhost:5001/extract",
            json={"text": cv_text}
        )
        return response.json()

    return FunctionTool.from_defaults(
        fn=extract_entities,
        name="ner_extraction",
        description="Extract information from CV text including skills, experience, education, etc."
    )

def create_skill_matching_tool():
    """Create skill matching tool"""

    def match_skills(cv_skills: list, job_description: str) -> dict:
        """Match CV skills with job description requirements.

        Args:
            cv_skills: List of skills from CV
            job_description: The job description to match against

        Returns:
            Match results with score
        """
        response = requests.post(
            "http://localhost:5002/match",
            json={"cv_skills": cv_skills, "jd_text": job_description}
        )
        return response.json()

    return FunctionTool.from_defaults(
        fn=match_skills,
        name="skill_matching",
        description="Match CV skills with job description to calculate compatibility score"
    )

def create_career_tool():
    """Create career recommendation tool"""

    def recommend_career_path(current_role: str, target_role: str) -> dict:
        """Generate career path recommendation.

        Args:
            current_role: Current job title
            target_role: Target/desired job title

        Returns:
            Career path with steps and skill gaps
        """
        response = requests.post(
            "http://localhost:5003/recommend",
            json={"current": current_role, "target": target_role}
        )
        return response.json()

    return FunctionTool.from_defaults(
        fn=recommend_career_path,
        name="career_recommendation",
        description="Generate career path from current role to target role with skill gaps"
    )
```

```python
# services/chatbot_service/agent.py

from llama_index.core.agent import ReActAgent
from llama_index.llms.ollama import Ollama
from .tools import create_ner_tool, create_skill_matching_tool, create_career_tool

class CVAssistantAgent:
    def __init__(self):
        # Setup LLM
        self.llm = Ollama(
            model="llama3.2:3b",
            temperature=0.7,
            request_timeout=120.0
        )

        # Create tools
        self.tools = [
            create_ner_tool(),
            create_skill_matching_tool(),
            create_career_tool()
        ]

        # Create ReAct agent
        self.agent = ReActAgent.from_tools(
            tools=self.tools,
            llm=self.llm,
            verbose=True,
            max_iterations=10
        )

        # Conversation memory
        self.memory = {}

    def chat(self, user_id: str, message: str) -> str:
        """Process user message"""

        # Get conversation history
        history = self.memory.get(user_id, [])

        # Build context
        context = "\n".join([
            f"{'User' if i % 2 == 0 else 'Assistant'}: {msg}"
            for i, msg in enumerate(history[-10:])  # Last 10 messages
        ])

        # Query agent
        full_query = f"{context}\nUser: {message}" if context else message
        response = self.agent.chat(full_query)

        # Update memory
        history.append(message)
        history.append(str(response))
        self.memory[user_id] = history

        return str(response)

# Test
if __name__ == "__main__":
    agent = CVAssistantAgent()

    # Test conversation
    print(agent.chat("user1", "What skills should I have as a software developer?"))
    print(agent.chat("user1", "Can you analyze my CV?"))
```

**Day 58-59 Deliverables:**
- [ ] NER tool created
- [ ] Skill matching tool created
- [ ] Career tool created
- [ ] ReAct agent working
- [ ] Tool calling tested

---

##### Day 60-61 (Fri-Sat): Conversation Memory + Integration
| Time | Task | Details |
|------|------|---------|
| Fri 09:00-12:00 | Implement ChromaDB memory | Persistent conversation |
| Fri 13:00-18:00 | Test end-to-end chatbot | Full flow testing |
| Sat 09:00-12:00 | Bug fixes | Address issues |
| Sat 13:00-17:00 | Document Phase 3 | Complete documentation |

```python
# services/chatbot_service/memory.py

import chromadb
from datetime import datetime
import uuid

class ConversationMemory:
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.client = chromadb.PersistentClient(path="./data/conversations")
        self.collection = self.client.get_or_create_collection(
            name=f"conv_{user_id}"
        )

    def add_message(self, role: str, content: str, metadata: dict = None):
        """Add message to memory"""
        self.collection.add(
            documents=[content],
            metadatas=[{
                "role": role,
                "timestamp": datetime.now().isoformat(),
                "user_id": self.user_id,
                **(metadata or {})
            }],
            ids=[str(uuid.uuid4())]
        )

    def get_recent_history(self, limit: int = 10) -> list:
        """Get recent conversation history"""
        results = self.collection.get(
            limit=limit,
            include=["documents", "metadatas"]
        )

        # Sort by timestamp and format
        messages = list(zip(results['documents'], results['metadatas']))
        messages.sort(key=lambda x: x[1]['timestamp'])

        return [
            {"role": m[1]['role'], "content": m[0]}
            for m in messages
        ]

    def search_context(self, query: str, top_k: int = 3) -> list:
        """Search for relevant context in history"""
        results = self.collection.query(
            query_texts=[query],
            n_results=top_k
        )

        return results['documents'][0] if results['documents'] else []
```

---

##### Day 62 (Sun 29/03): Phase 3 Completion

**Phase 3 Completion Checklist:**
```
PHASE 3 SIGN-OFF
════════════════

NER MODEL:
□ Final model trained
□ Test F1: _____ (target ≥ 75%)
□ Per-entity F1:
  - PER: _____
  - ORG: _____
  - SKILL: _____
  - DEGREE: _____
  - MAJOR: _____
  - JOB_TITLE: _____
  - DATE: _____
  - LOC: _____
  - PROJECT: _____
  - CERT: _____
□ Error analysis complete
□ Model saved to models/ner/final/
□ Inference script working

CHATBOT:
□ Ollama + Llama 3.2 running
□ LlamaIndex RAG working
□ ReAct agent functional
□ Tools created:
  □ NER extraction tool
  □ Skill matching tool
  □ Career recommendation tool
□ Conversation memory working
□ End-to-end test passed

READY FOR PHASE 4: YES / NO
```

---

## 5. PHASE 4: Microservices & UI (Week 10-11)

### 5.1 Phase 4 Overview

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                         PHASE 4: MICROSERVICES & UI                              │
│                              Duration: 2 weeks                                   │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│  WEEK 10 - BACKEND SERVICES:                                                    │
│  ✓ NER Service (FastAPI :5001)                                                 │
│  ✓ Skill Matching Service (FastAPI :5002)                                      │
│  ✓ Career Service (FastAPI :5003)                                              │
│  ✓ Chatbot Service (FastAPI :5004)                                             │
│  ✓ API Gateway (Spring Boot :8080)                                             │
│  ✓ JWT Authentication                                                           │
│                                                                                  │
│  WEEK 11 - FRONTEND:                                                            │
│  ✓ React 18 + Ant Design                                                       │
│  ✓ ChatGPT-style interface                                                     │
│  ✓ Authentication flow                                                          │
│  ✓ Docker Compose deployment                                                   │
│                                                                                  │
│  MILESTONES:                                                                     │
│  M7 (End Week 10): All services running                                         │
│  M8 (End Week 11): Full system integrated                                       │
│                                                                                  │
│  RISK: MEDIUM - Integration complexity                                          │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### 5.2 WEEK 10: Microservices Development (30/03 - 05/04)

#### Service Architecture

```
                        ┌─────────────────────┐
                        │   Frontend :3000    │
                        │   (React + Ant)     │
                        └──────────┬──────────┘
                                   │
                        ┌──────────▼──────────┐
                        │  API Gateway :8080  │
                        │   (Spring Boot)     │
                        │   - JWT Auth        │
                        │   - Rate Limiting   │
                        └──────────┬──────────┘
                                   │
        ┌──────────────┬───────────┼───────────┬──────────────┐
        │              │           │           │              │
┌───────▼───────┐ ┌────▼────┐ ┌────▼────┐ ┌────▼────┐ ┌───────▼───────┐
│ NER Service   │ │ Skill   │ │ Career  │ │ Chatbot │ │  PostgreSQL   │
│    :5001      │ │ :5002   │ │ :5003   │ │ :5004   │ │    :5432      │
│  (FastAPI)    │ │(FastAPI)│ │(FastAPI)│ │(FastAPI)│ │               │
└───────────────┘ └─────────┘ └─────────┘ └────┬────┘ └───────────────┘
                                               │
                                        ┌──────▼──────┐
                                        │  ChromaDB   │
                                        │   :8000     │
                                        └─────────────┘
```

#### Day-by-Day Tasks

##### Day 63-64 (Mon-Tue 30-31/03): Python Microservices
| Day | Service | Port | Details |
|-----|---------|------|---------|
| Mon AM | NER Service | 5001 | Load model, inference endpoint |
| Mon PM | Skill Service | 5002 | Embedding, matching logic |
| Tue AM | Career Service | 5003 | O*NET integration |
| Tue PM | Chatbot Service | 5004 | Agent, memory, routing |

```python
# services/ner_service/main.py

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from transformers import BertForTokenClassification, BertTokenizer
import torch

app = FastAPI(title="NER Service", version="1.0.0")

# Load model at startup
model = None
tokenizer = None

@app.on_event("startup")
async def load_model():
    global model, tokenizer
    model = BertForTokenClassification.from_pretrained("./models/ner/final")
    tokenizer = BertTokenizer.from_pretrained("./models/ner/final")
    model.eval()

class ExtractRequest(BaseModel):
    text: str

class Entity(BaseModel):
    text: str
    type: str
    start: int
    end: int

class ExtractResponse(BaseModel):
    entities: list[Entity]
    processing_time: float

@app.post("/extract", response_model=ExtractResponse)
async def extract_entities(request: ExtractRequest):
    """Extract named entities from text"""
    import time
    start = time.time()

    # Tokenize
    inputs = tokenizer(
        request.text,
        return_tensors="pt",
        truncation=True,
        max_length=512
    )

    # Predict
    with torch.no_grad():
        outputs = model(**inputs)
        predictions = torch.argmax(outputs.logits, dim=-1)

    # Convert to entities
    entities = convert_predictions_to_entities(
        predictions[0],
        tokenizer.convert_ids_to_tokens(inputs['input_ids'][0]),
        request.text
    )

    return ExtractResponse(
        entities=entities,
        processing_time=time.time() - start
    )

@app.get("/health")
async def health():
    return {"status": "ok", "model_loaded": model is not None}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5001)
```

**Day 63-64 Deliverables:**
- [ ] NER Service running on :5001
- [ ] Skill Service running on :5002
- [ ] Career Service running on :5003
- [ ] Chatbot Service running on :5004
- [ ] All health endpoints returning OK

---

##### Day 65-66 (Wed-Thu 01-02/04): API Gateway + Auth
| Time | Task | Details |
|------|------|---------|
| Wed 09:00-12:00 | Create Spring Boot project | Initialize with deps |
| Wed 13:00-18:00 | Implement JWT auth | Login, register, token validation |
| Thu 09:00-12:00 | Configure routing | Proxy to Python services |
| Thu 13:00-18:00 | Add rate limiting | Prevent abuse |

```java
// api_gateway/src/main/java/com/cvassistant/gateway/config/SecurityConfig.java

@Configuration
@EnableWebSecurity
public class SecurityConfig {

    @Bean
    public SecurityFilterChain filterChain(HttpSecurity http) throws Exception {
        http
            .csrf().disable()
            .cors().and()
            .sessionManagement()
                .sessionCreationPolicy(SessionCreationPolicy.STATELESS)
            .and()
            .authorizeHttpRequests()
                .requestMatchers("/api/auth/**").permitAll()
                .requestMatchers("/api/health").permitAll()
                .anyRequest().authenticated()
            .and()
            .addFilterBefore(jwtAuthFilter(), UsernamePasswordAuthenticationFilter.class);

        return http.build();
    }
}
```

```yaml
# api_gateway/src/main/resources/application.yml

spring:
  application:
    name: cv-assistant-gateway

  cloud:
    gateway:
      routes:
        - id: ner-service
          uri: http://localhost:5001
          predicates:
            - Path=/api/ner/**
          filters:
            - StripPrefix=2

        - id: skill-service
          uri: http://localhost:5002
          predicates:
            - Path=/api/skill/**
          filters:
            - StripPrefix=2

        - id: career-service
          uri: http://localhost:5003
          predicates:
            - Path=/api/career/**
          filters:
            - StripPrefix=2

        - id: chatbot-service
          uri: http://localhost:5004
          predicates:
            - Path=/api/chat/**
          filters:
            - StripPrefix=2

jwt:
  secret: ${JWT_SECRET:your-secret-key-here}
  expiration: 3600000
  refresh-expiration: 604800000
```

**Day 65-66 Deliverables:**
- [ ] Spring Boot API Gateway running on :8080
- [ ] JWT authentication working
- [ ] All routes configured
- [ ] Rate limiting implemented

---

##### Day 67-68 (Fri-Sat 03-04/04): Integration Testing
| Time | Task | Details |
|------|------|---------|
| Fri 09:00-12:00 | Test auth flow | Register → Login → Token |
| Fri 13:00-18:00 | Test service routing | All endpoints accessible |
| Sat 09:00-12:00 | Test chatbot flow | Full conversation |
| Sat 13:00-17:00 | Fix issues | Debug and resolve |

**Integration Test Script:**
```bash
#!/bin/bash
# scripts/test_integration.sh

BASE_URL="http://localhost:8080/api"

echo "=== Testing API Gateway Integration ==="

# 1. Health checks
echo -e "\n1. Health Checks:"
curl -s $BASE_URL/health && echo " [Gateway OK]"
curl -s http://localhost:5001/health && echo " [NER OK]"
curl -s http://localhost:5002/health && echo " [Skill OK]"
curl -s http://localhost:5003/health && echo " [Career OK]"
curl -s http://localhost:5004/health && echo " [Chatbot OK]"

# 2. Register user
echo -e "\n2. Register User:"
REGISTER=$(curl -s -X POST $BASE_URL/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"Test123!","name":"Test User"}')
echo $REGISTER

# 3. Login
echo -e "\n3. Login:"
LOGIN=$(curl -s -X POST $BASE_URL/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"Test123!"}')
TOKEN=$(echo $LOGIN | jq -r '.access_token')
echo "Token: ${TOKEN:0:50}..."

# 4. Test NER
echo -e "\n4. Test NER Service:"
curl -s -X POST $BASE_URL/ner/extract \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"text":"John Smith worked at Google as a Software Engineer"}' | jq

# 5. Test Chat
echo -e "\n5. Test Chat Service:"
curl -s -X POST $BASE_URL/chat \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"message":"What skills should a developer have?"}' | jq

echo -e "\n=== Integration Tests Complete ==="
```

**Day 67-68 Deliverables:**
- [ ] All health checks passing
- [ ] Auth flow working
- [ ] All services accessible through gateway
- [ ] Chatbot conversation working

---

### 5.3 WEEK 11: Frontend Development (06/04 - 12/04)

#### Day-by-Day Tasks

##### Day 69-70 (Mon-Tue 06-07/04): React Setup + Auth Pages
| Time | Task | Details |
|------|------|---------|
| Mon 09:00-12:00 | Create React project | Vite + TypeScript |
| Mon 13:00-18:00 | Setup Ant Design | Theme, layout |
| Tue 09:00-12:00 | Implement Login page | Form, validation |
| Tue 13:00-18:00 | Implement Register page | Form, API calls |

```bash
# Create React project
npm create vite@latest frontend -- --template react-ts
cd frontend

# Install dependencies
npm install antd @ant-design/icons
npm install axios react-router-dom
npm install @tanstack/react-query

# Project structure
frontend/
├── src/
│   ├── components/
│   │   ├── Chat/
│   │   │   ├── ChatMessage.tsx
│   │   │   ├── ChatInput.tsx
│   │   │   └── ChatWindow.tsx
│   │   ├── Sidebar/
│   │   │   ├── ThreadList.tsx
│   │   │   └── Sidebar.tsx
│   │   └── Layout/
│   │       └── AppLayout.tsx
│   ├── pages/
│   │   ├── Login.tsx
│   │   ├── Register.tsx
│   │   └── Chat.tsx
│   ├── services/
│   │   ├── api.ts
│   │   └── auth.ts
│   ├── hooks/
│   │   └── useAuth.ts
│   ├── context/
│   │   └── AuthContext.tsx
│   ├── App.tsx
│   └── main.tsx
├── package.json
└── vite.config.ts
```

**Day 69-70 Deliverables:**
- [ ] React project created
- [ ] Ant Design configured
- [ ] Login page working
- [ ] Register page working
- [ ] Auth context implemented

---

##### Day 71-72 (Wed-Thu 08-09/04): Chat Interface
| Time | Task | Details |
|------|------|---------|
| Wed 09:00-12:00 | Implement Sidebar | Thread list, new chat |
| Wed 13:00-18:00 | Implement ChatWindow | Message display |
| Thu 09:00-12:00 | Implement ChatInput | Message composer |
| Thu 13:00-18:00 | Implement CV upload | File upload + display |

```tsx
// src/pages/Chat.tsx

import React, { useState, useEffect } from 'react';
import { Layout } from 'antd';
import { Sidebar } from '../components/Sidebar/Sidebar';
import { ChatWindow } from '../components/Chat/ChatWindow';
import { ChatInput } from '../components/Chat/ChatInput';
import { useChatAPI } from '../hooks/useChatAPI';

const { Content, Sider } = Layout;

export const Chat: React.FC = () => {
  const [selectedThread, setSelectedThread] = useState<string | null>(null);
  const { messages, sendMessage, isLoading } = useChatAPI(selectedThread);

  return (
    <Layout style={{ height: '100vh' }}>
      <Sider width={280} theme="light">
        <Sidebar
          selectedThread={selectedThread}
          onSelectThread={setSelectedThread}
          onNewChat={() => setSelectedThread(null)}
        />
      </Sider>
      <Content style={{ display: 'flex', flexDirection: 'column' }}>
        <ChatWindow messages={messages} isLoading={isLoading} />
        <ChatInput onSend={sendMessage} disabled={isLoading} />
      </Content>
    </Layout>
  );
};
```

```tsx
// src/components/Chat/ChatMessage.tsx

import React from 'react';
import { Avatar, Card, Typography } from 'antd';
import { UserOutlined, RobotOutlined } from '@ant-design/icons';

interface ChatMessageProps {
  role: 'user' | 'assistant';
  content: string;
  entities?: Entity[];
}

export const ChatMessage: React.FC<ChatMessageProps> = ({ role, content, entities }) => {
  const isUser = role === 'user';

  return (
    <div style={{
      display: 'flex',
      justifyContent: isUser ? 'flex-end' : 'flex-start',
      marginBottom: 16
    }}>
      {!isUser && (
        <Avatar
          icon={<RobotOutlined />}
          style={{ backgroundColor: '#1890ff', marginRight: 8 }}
        />
      )}
      <Card
        style={{
          maxWidth: '70%',
          backgroundColor: isUser ? '#e6f7ff' : '#f5f5f5'
        }}
      >
        <Typography.Paragraph style={{ margin: 0 }}>
          {content}
        </Typography.Paragraph>
        {entities && entities.length > 0 && (
          <EntityDisplay entities={entities} />
        )}
      </Card>
      {isUser && (
        <Avatar
          icon={<UserOutlined />}
          style={{ backgroundColor: '#52c41a', marginLeft: 8 }}
        />
      )}
    </div>
  );
};
```

**Day 71-72 Deliverables:**
- [ ] Sidebar with thread list
- [ ] Chat message display
- [ ] Message input working
- [ ] CV upload functional

---

##### Day 73-74 (Fri-Sat 10-11/04): Integration + Docker
| Time | Task | Details |
|------|------|---------|
| Fri 09:00-12:00 | Connect frontend to backend | API integration |
| Fri 13:00-18:00 | Implement streaming | Real-time response |
| Sat 09:00-12:00 | Create Docker Compose | All services |
| Sat 13:00-17:00 | End-to-end testing | Full flow |

```yaml
# docker-compose.yml

version: '3.8'

services:
  # Frontend
  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    depends_on:
      - api-gateway
    environment:
      - VITE_API_URL=http://localhost:8080/api

  # API Gateway
  api-gateway:
    build: ./services/api_gateway
    ports:
      - "8080:8080"
    depends_on:
      - ner-service
      - skill-service
      - career-service
      - chatbot-service
      - postgres
    environment:
      - JWT_SECRET=${JWT_SECRET}
      - DATABASE_URL=postgresql://postgres:postgres@postgres:5432/cvassistant

  # NER Service
  ner-service:
    build: ./services/ner_service
    ports:
      - "5001:5001"
    volumes:
      - ./models:/app/models

  # Skill Service
  skill-service:
    build: ./services/skill_service
    ports:
      - "5002:5002"

  # Career Service
  career-service:
    build: ./services/career_service
    ports:
      - "5003:5003"
    volumes:
      - ./knowledge_base:/app/knowledge_base

  # Chatbot Service
  chatbot-service:
    build: ./services/chatbot_service
    ports:
      - "5004:5004"
    depends_on:
      - chromadb
      - ollama
    volumes:
      - ./knowledge_base:/app/knowledge_base

  # Ollama
  ollama:
    image: ollama/ollama
    ports:
      - "11434:11434"
    volumes:
      - ollama_data:/root/.ollama

  # ChromaDB
  chromadb:
    image: chromadb/chroma
    ports:
      - "8000:8000"
    volumes:
      - chroma_data:/chroma/chroma

  # PostgreSQL
  postgres:
    image: postgres:15
    ports:
      - "5432:5432"
    environment:
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=postgres
      - POSTGRES_DB=cvassistant
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  ollama_data:
  chroma_data:
  postgres_data:
```

**Startup Script:**
```bash
#!/bin/bash
# scripts/start.sh

echo "Starting CV Assistant..."

# 1. Pull Ollama model (first time only)
docker-compose exec ollama ollama pull llama3.2:3b

# 2. Start all services
docker-compose up -d

# 3. Wait for services
echo "Waiting for services to start..."
sleep 30

# 4. Health check
echo "Checking service health..."
curl -s http://localhost:8080/api/health
curl -s http://localhost:5001/health
curl -s http://localhost:5002/health
curl -s http://localhost:5003/health
curl -s http://localhost:5004/health

echo "CV Assistant is ready!"
echo "Frontend: http://localhost:3000"
echo "API Gateway: http://localhost:8080"
```

**Day 73-74 Deliverables:**
- [ ] Frontend connected to backend
- [ ] Streaming responses working
- [ ] Docker Compose configured
- [ ] All services start together

---

##### Day 75 (Sun 12/04): Phase 4 Completion

**Phase 4 Completion Checklist:**
```
PHASE 4 SIGN-OFF
════════════════

MICROSERVICES:
□ NER Service (:5001) running
□ Skill Service (:5002) running
□ Career Service (:5003) running
□ Chatbot Service (:5004) running
□ API Gateway (:8080) running
□ All health endpoints OK

AUTHENTICATION:
□ Register working
□ Login working
□ JWT validation working
□ Protected routes secured

FRONTEND:
□ Login page complete
□ Register page complete
□ Chat interface complete
□ Thread list working
□ CV upload working
□ Entity display working
□ Skill match display working

DOCKER:
□ All Dockerfiles created
□ docker-compose.yml complete
□ All services start together
□ Volumes configured

END-TO-END:
□ User can register
□ User can login
□ User can upload CV
□ User can chat with AI
□ AI can analyze CV
□ AI can match skills
□ AI can recommend career

READY FOR PHASE 5: YES / NO
```

---

## 6. PHASE 5: Finalization (Week 12)

### 6.1 Phase 5 Overview

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           PHASE 5: FINALIZATION                                  │
│                              Duration: 1 week                                    │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│  GOALS:                                                                          │
│  ✓ Complete integration testing                                                 │
│  ✓ Fix remaining bugs                                                           │
│  ✓ Write NCKH report                                                            │
│  ✓ Prepare presentation                                                         │
│  ✓ Demo rehearsal                                                               │
│  ✓ Submit all deliverables                                                      │
│                                                                                  │
│  MILESTONE:                                                                      │
│  M9 (19/04): Project complete, all deliverables submitted                       │
│                                                                                  │
│  RISK: LOW - Buffer week for unexpected issues                                  │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### 6.2 WEEK 12: Final Week (13/04 - 19/04)

#### Day-by-Day Tasks

##### Day 76-77 (Mon-Tue 13-14/04): Testing + Bug Fixes
| Time | Task | Details |
|------|------|---------|
| Mon 09:00-18:00 | Complete integration testing | All user flows |
| Tue 09:00-18:00 | Bug fixes | Prioritized by severity |

**Test Scenarios:**
```
1. New User Flow:
   □ Register with valid email
   □ Login with credentials
   □ Upload CV
   □ View extracted entities
   □ Ask chatbot about skills
   □ Match with job description
   □ Get career recommendations

2. Returning User Flow:
   □ Login
   □ View previous threads
   □ Continue conversation
   □ Upload new CV

3. Edge Cases:
   □ Invalid file upload (not PDF)
   □ Large CV (10+ pages)
   □ Empty CV
   □ Network errors
   □ Session timeout

4. Performance:
   □ CV analysis < 5 seconds
   □ Chat response < 3 seconds
   □ Page load < 2 seconds
```

---

##### Day 78-80 (Wed-Fri 15-17/04): Report + Presentation
| Day | Task | Details |
|-----|------|---------|
| Wed | Write NCKH report | Sections 1-4 |
| Thu | Write NCKH report | Sections 5-7 |
| Fri | Create presentation | 15-20 slides |

**NCKH Report Structure:**
```markdown
BÁO CÁO NGHIÊN CỨU KHOA HỌC
═══════════════════════════

1. TỔNG QUAN
   1.1 Đặt vấn đề
   1.2 Mục tiêu nghiên cứu
   1.3 Phạm vi nghiên cứu

2. CƠ SỞ LÝ THUYẾT
   2.1 Named Entity Recognition
   2.2 BERT và Transfer Learning
   2.3 Large Language Models
   2.4 RAG (Retrieval-Augmented Generation)

3. PHƯƠNG PHÁP NGHIÊN CỨU
   3.1 Thu thập và xử lý dữ liệu
   3.2 Phương pháp annotation
   3.3 Kiến trúc mô hình NER
   3.4 Kiến trúc hệ thống Chatbot

4. KẾT QUẢ VÀ THẢO LUẬN
   4.1 Kết quả annotation
   4.2 Kết quả huấn luyện NER
   4.3 Đánh giá hệ thống Chatbot
   4.4 So sánh với các nghiên cứu khác

5. DEMO HỆ THỐNG
   5.1 Giao diện người dùng
   5.2 Các tính năng chính
   5.3 Quy trình sử dụng

6. KẾT LUẬN VÀ HƯỚNG PHÁT TRIỂN
   6.1 Kết luận
   6.2 Đóng góp của nghiên cứu
   6.3 Hạn chế
   6.4 Hướng phát triển

7. TÀI LIỆU THAM KHẢO

PHỤ LỤC
A. Annotation Guidelines
B. Model Configuration
C. API Documentation
```

---

##### Day 81 (Sat 18/04): Demo Rehearsal
| Time | Task | Details |
|------|------|---------|
| 09:00-12:00 | Individual practice | Each person rehearses |
| 13:00-15:00 | Team rehearsal | Full demo run |
| 15:00-17:00 | Final adjustments | Fix any issues |

**Demo Script:**
```
DEMO FLOW (15 minutes)
══════════════════════

1. Introduction (2 min)
   - Show login page
   - Register new user

2. CV Upload (3 min)
   - Upload sample CV
   - Show entity extraction
   - Highlight different entity types

3. Skill Matching (3 min)
   - Paste job description
   - Show match analysis
   - Explain scoring

4. Career Recommendation (3 min)
   - Ask about career path
   - Show roadmap generation

5. General Chat (2 min)
   - Ask CV improvement tips
   - Show contextual responses

6. Technical Overview (2 min)
   - Show architecture diagram
   - Mention key technologies
```

---

##### Day 82 (Sun 19/04): Final Submission

**Final Deliverables Checklist:**
```
FINAL SUBMISSION CHECKLIST
══════════════════════════

DOCUMENTATION:
□ NCKH report (PDF)
□ Presentation slides (PPTX/PDF)
□ README.md updated
□ API documentation

CODE:
□ GitHub repository finalized
□ All code committed
□ Docker Compose tested
□ Setup instructions complete

MODELS:
□ NER model saved
□ Model card created
□ Training logs preserved

DATA:
□ Annotated dataset (anonymized)
□ Data statistics documented
□ Splits preserved

DEMO:
□ Demo video recorded (optional)
□ Live demo ready
□ Backup demo (screenshots/video)

SUBMISSION:
□ Upload to school portal
□ Email to GVHD
□ Backup copies saved

SIGN-OFF:
□ Leader: _____________ Date: 19/04/2026
□ PROJECT COMPLETE: YES
```

---

## 7. Risk Management

### 7.1 Risk Register

| ID | Risk | Probability | Impact | Mitigation | Contingency |
|----|------|-------------|--------|------------|-------------|
| R1 | Annotators unavailable | Medium | High | Weekly check-ins | Leader does more annotation |
| R2 | IAA < 80% | Medium | High | Clear guidelines, training | More training sessions |
| R3 | F1 < 75% | Medium | High | Hyperparameter tuning | Use CRF fallback |
| R4 | Colab timeout | High | Medium | Save checkpoints frequently | Use Kaggle as backup |
| R5 | Integration issues | Medium | Medium | Early integration testing | Simplify architecture |
| R6 | Time overrun | Medium | High | Weekly tracking | Scope reduction |

### 7.2 Scope Reduction Priority

If behind schedule, cut in this order:
```
1. Advanced UI styling (save 2-3 days)
2. Career recommendation depth (save 2 days)
3. Docker deployment (use local only)
4. Frontend → Simple HTML/CSS
5. Skip web app → Demo via Jupyter notebook
```

---

## 8. Success Criteria Summary

| Phase | Must Have | Nice to Have |
|-------|-----------|--------------|
| Phase 1 | Environment ready, 100 CVs anonymized | Knowledge base fully populated |
| Phase 2 | 200+ CVs annotated, IAA ≥ 80% | 250+ CVs |
| Phase 3 | F1 ≥ 75%, Chatbot responds | F1 ≥ 80%, Fast responses |
| Phase 4 | All services work, Basic UI | Polished UI, Streaming |
| Phase 5 | Report submitted, Demo works | Video demo, Perfect presentation |

---

## 9. Contact & Communication

### Weekly Meetings
- **Team Sync**: Every Friday 17:00-17:30
- **GVHD Check-in**: Bi-weekly (confirm schedule)

### Communication Channels
- **Quick questions**: Group Zalo/Telegram
- **Documentation**: GitHub Issues
- **Formal updates**: Email

---

*Document created as part of CV Assistant Research Project documentation.*
