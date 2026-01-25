# 03. Feasibility Analysis - Phân Tích Tính Khả Thi

> **Document Version**: 1.0
> **Last Updated**: 2026-01-23
> **Status**: Approved
> **Related Documents**: [02_problem_understanding.md](./02_problem_understanding.md), [04_requirements_classification.md](./04_requirements_classification.md)

---

## 1. Executive Summary

| Dimension | Feasibility | Confidence | Notes |
|-----------|-------------|------------|-------|
| Technical | ✅ High | 85% | Proven tech stack |
| Resource | ✅ Medium-High | 75% | Tight but achievable |
| Data | ✅ High | 90% | Data available |
| Legal | ✅ High | 95% | Permission confirmed |
| Schedule | ⚠️ Medium | 65% | Aggressive timeline |

**Overall Assessment**: **FEASIBLE** với risk management cẩn thận.

---

## 2. Technical Feasibility

### 2.1 GPU Requirements

| Requirement | Available | Status |
|-------------|-----------|--------|
| GPU for BERT training | Google Colab T4 (16GB) | ✅ Sufficient |
| RAM | 12.7GB (Colab) | ✅ Sufficient |
| Storage | 100GB (Colab) | ✅ Sufficient |

**Analysis**:
```
BERT-base memory requirement:
├── Model parameters: ~110M × 4 bytes = ~440MB
├── Optimizer states: ~880MB (Adam)
├── Batch size 16: ~2GB per batch
├── Gradient accumulation: 4 steps
└── Total peak: ~8-10GB ✓ (T4 has 16GB)

Conclusion: Google Colab T4 ĐỦ cho BERT fine-tuning
```

### 2.2 Model Architecture Feasibility

| Component | Technology | Maturity | Risk |
|-----------|------------|----------|------|
| NER | bert-base-uncased | Production | Low |
| Tokenizer | BertTokenizer | Production | Low |
| Skill Matching | sentence-transformers | Production | Low |
| PDF Parsing | PyPDF2/pdfplumber | Stable | Medium |

**Evidence**:
- BERT NER đã được chứng minh hiệu quả qua nhiều papers
- CoNLL-2003 benchmark: F1 > 90% (English NER)
- Resume NER papers: F1 70-85% typical
- Our target F1 ≥ 75%: **Achievable**

### 2.3 Technology Stack Assessment

```
Frontend (React + Ant Design):
├── Maturity: Production-ready
├── Team familiarity: Need to learn
├── Alternative: Simple HTML/CSS
└── Risk: Low

API Gateway (Spring Boot + Spring Security):
├── Maturity: Production-ready
├── Team familiarity: Leader has Java experience
├── Reason: JWT auth, OpenAPI, enterprise patterns
└── Risk: Low

Python Microservices (FastAPI):
├── Services: NER, Skill, Career, Chatbot
├── Maturity: Production-ready
├── Reason: Async, auto docs, Python native
└── Risk: Low

Chatbot Stack (LlamaIndex + Ollama):
├── LlamaIndex: ReAct agent pattern for tool-using
├── Ollama: Local Llama 3.2 (3B) deployment
├── ChromaDB: Vector store for RAG
└── Risk: Medium (newer technology)

ML Stack (PyTorch + Transformers):
├── Maturity: Production-ready
├── Team familiarity: Learning
├── Community: Huge, many tutorials
└── Risk: Low-Medium

Database:
├── PostgreSQL: User data, threads, CVs
├── ChromaDB: Knowledge base, embeddings
└── Risk: Low

Annotation (Label Studio):
├── Maturity: Production-ready
├── Self-hosted: Free
├── NER support: Native (10 entity types)
└── Risk: Low

Deployment (Docker Compose):
├── All services containerized
├── Easy local deployment
└── Risk: Low
```

### 2.4 Technical Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Colab timeout during training | High | Medium | Checkpointing every epoch |
| PDF extraction fails | Medium | High | Test different parsers |
| Model overfitting | Medium | High | Regularization, more data |
| Low F1 score | Medium | High | Hyperparameter tuning |

---

## 3. Resource Feasibility

### 3.1 Human Resource Analysis

#### 3.1.1 Team Capacity

```
Leader (1 person):
├── Available: ~35 hrs/week
├── Coding: 20 hrs
├── Research: 10 hrs
├── Coordination: 5 hrs
└── Status: ✅ Sufficient for technical tasks

Annotators (4 people):
├── Available: ~10-15 hrs/week each
├── Total: ~50 hrs/week for annotation
├── Rate: ~2-3 CVs/hour (with QC)
└── Status: ✅ Sufficient for annotation target
```

#### 3.1.2 Annotation Capacity Calculation

```
Target: 200 CVs annotated

Assumptions:
├── Time per CV: 20-30 minutes (including QC)
├── Working rate: ~2.5 CVs/hour
├── Hours per week per annotator: 10 hrs
├── CVs per annotator per week: 25 CVs

Timeline calculation:
├── Total annotation weeks available: 4 weeks
├── 4 annotators × 25 CVs/week × 4 weeks = 400 CVs
├── Buffer for rework: 50%
└── Net capacity: ~200 CVs ✓

Conclusion: 200 CVs trong 4 tuần là ACHIEVABLE
```

### 3.2 Skill Gap Analysis

| Skill | Required Level | Current Level | Gap | Mitigation |
|-------|---------------|---------------|-----|------------|
| Python | Advanced | Intermediate | Medium | Self-study + tutorials |
| NLP/BERT | Intermediate | Beginner | High | Hugging Face course |
| React | Basic | Beginner | Low | Quick crash course |
| FastAPI | Basic | Beginner | Low | Official docs |
| Label Studio | Basic | None | Low | Quick setup guide |

### 3.3 Tool Availability

| Tool | Cost | Availability | Alternative |
|------|------|--------------|-------------|
| VS Code | Free | ✅ | PyCharm CE |
| Google Colab | Free | ✅ | Kaggle Notebooks |
| Label Studio | Free | ✅ | Doccano |
| GitHub | Free | ✅ | GitLab |
| PyTorch | Free | ✅ | TensorFlow |

---

## 4. Data Feasibility

### 4.1 Data Availability

| Aspect | Status | Details |
|--------|--------|---------|
| Source | ✅ Confirmed | UEH Job Portal (vieclam.ueh.edu.vn) |
| Quantity | ✅ Sufficient | 3,099 CVs raw |
| Format | ✅ Compatible | PDF files |
| Language | ✅ Suitable | Primarily English |
| Access | ✅ Granted | Official permission |

### 4.2 Data Quality Assessment

```
Expected data characteristics:
├── Format consistency: Low (varied templates)
├── Text extractability: High (digital PDFs)
├── Language: English (majority)
├── Completeness: Medium (some sections may be missing)
└── Noise level: Medium (headers, footers, formatting)

Data preprocessing needs:
├── PDF to text extraction
├── Text cleaning (remove noise)
├── Anonymization (PII removal)
└── Format normalization
```

### 4.3 Annotation Feasibility

| Factor | Assessment | Notes |
|--------|------------|-------|
| Complexity | Medium | 10 entity types, 21 BIO labels |
| Ambiguity | Low-Medium | Clear guidelines needed |
| Tools | Ready | Label Studio |
| Training | 1-2 hours | For annotators |

**Entity Types (10 total)**:
```
PER, ORG, DATE, LOC, SKILL, DEGREE, MAJOR, JOB_TITLE, PROJECT, CERT
```

**Annotation Guidelines Needed**:
```
1. Entity type definitions with examples
2. Boundary rules (what to include/exclude)
3. Handling edge cases
4. Examples for each of 10 entity types
5. QC checklist for BIO tagging
6. Inter-annotator agreement measurement
```

### 4.4 Data Volume Justification

```
Literature review on NER data requirements:

Small dataset (100-500 samples):
├── Fine-tuning pre-trained BERT: ✓ Feasible
├── Expected F1: 65-75%
└── Risk: Higher variance

Medium dataset (500-2000 samples):
├── More robust fine-tuning
├── Expected F1: 75-85%
└── Risk: Lower variance

Our target: 200 CVs
├── Sentences: ~200 CVs × 50 sentences = 10,000 sentences
├── Entities: ~200 CVs × 30 entities = 6,000 entity mentions
└── Assessment: ✓ SUFFICIENT for BERT fine-tuning
```

---

## 5. Legal Feasibility

### 5.1 Data Usage Rights

| Aspect | Status | Evidence |
|--------|--------|----------|
| Data source permission | ✅ Granted | UEH agreement |
| Research use | ✅ Allowed | Academic purpose |
| Commercial use | ❌ Not allowed | Non-commercial only |
| Redistribution | ❌ Not allowed | Internal use only |

### 5.2 Privacy Compliance

```
PII in CVs:
├── Name → MUST anonymize
├── Email → MUST anonymize
├── Phone → MUST anonymize
├── Address → MUST anonymize
├── Photo → MUST remove
└── ID numbers → MUST remove

Anonymization process:
├── Automated regex for emails, phones
├── Manual review for names
├── Replace with placeholders: [NAME], [EMAIL], etc.
└── Document anonymization log
```

### 5.3 Model Licensing

| Component | License | Commercial Use | Modification |
|-----------|---------|----------------|--------------|
| bert-base-uncased | Apache 2.0 | ✅ Yes | ✅ Yes |
| sentence-transformers | Apache 2.0 | ✅ Yes | ✅ Yes |
| Transformers library | Apache 2.0 | ✅ Yes | ✅ Yes |
| PyTorch | BSD-style | ✅ Yes | ✅ Yes |
| Label Studio | Apache 2.0 | ✅ Yes | ✅ Yes |

**Conclusion**: All components are **legally safe** for research use.

---

## 6. Schedule Feasibility

### 6.1 Timeline Analysis

```
Total duration: 12 weeks (84 days)

Phase breakdown:
├── Week 1-2: Setup + Documentation (14 days)
│   ├── Environment setup: 3 days
│   ├── Documentation: 7 days
│   └── Annotation guidelines: 4 days
│
├── Week 3-6: Data Annotation (28 days)
│   ├── Annotator training: 2 days
│   ├── Annotation: 22 days
│   └── QC + corrections: 4 days
│
├── Week 7-9: Model Training (21 days)
│   ├── Data preprocessing: 3 days
│   ├── Model experiments: 14 days
│   └── Evaluation: 4 days
│
├── Week 10-11: Web App (14 days)
│   ├── Backend API: 7 days
│   └── Frontend UI: 7 days
│
└── Week 12: Testing + Report (7 days)
    ├── Integration testing: 2 days
    ├── Final report: 4 days
    └── Presentation prep: 1 day
```

### 6.2 Critical Path

```
[Start] → [Setup] → [Annotation] → [Training] → [Evaluation] → [Report] → [End]
                         ↓
                    (Parallel)
                         ↓
              [Web App Development]

Critical path duration: 12 weeks
Parallel work: Web App can start Week 8 (after initial model ready)
```

### 6.3 Schedule Risks

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| Annotation delays | High | Medium | Start early, daily tracking |
| Training issues | High | Medium | Checkpoint frequently |
| Scope creep | High | Medium | Strict scope control |
| Team availability | Medium | Medium | Buffer time |

### 6.4 Schedule Confidence

```
Optimistic: 10 weeks (everything goes perfectly)
Realistic:  12 weeks (some minor issues)
Pessimistic: 14 weeks (major issues)

Current plan: 12 weeks
Buffer: None (deadline fixed)
Confidence: 65%

Recommendation:
├── Start immediately
├── Track daily progress
├── Cut scope if needed (prioritize NER over Web App)
└── Have contingency plan
```

---

## 7. Information Gaps

### 7.1 Identified Gaps

| ID | Gap | Impact | Owner | Status |
|----|-----|--------|-------|--------|
| G1 | GVHD tiêu chí cụ thể | High | Leader | 🔴 Pending |
| G2 | Template báo cáo NCKH | High | Leader | 🔴 Pending |
| G3 | Rubric chấm điểm | Medium | Leader | 🔴 Pending |
| G4 | Hội đồng requirements | Medium | Leader | 🔴 Pending |

### 7.2 Action Items

| Gap | Action | Deadline | Status |
|-----|--------|----------|--------|
| G1 | Email/meeting với GVHD | Week 1 | TODO |
| G2 | Xin template từ Khoa/Trường | Week 1 | TODO |
| G3 | Hỏi GVHD hoặc Khoa | Week 2 | TODO |
| G4 | Confirm với GVHD | Week 2 | TODO |

---

## 8. Feasibility Decision Matrix

### 8.1 Scoring Matrix

| Criterion | Weight | Score (1-5) | Weighted |
|-----------|--------|-------------|----------|
| Technical | 25% | 4 | 1.00 |
| Resource | 20% | 3.5 | 0.70 |
| Data | 20% | 4.5 | 0.90 |
| Legal | 15% | 5 | 0.75 |
| Schedule | 20% | 3 | 0.60 |
| **Total** | **100%** | - | **3.95/5** |

### 8.2 Go/No-Go Decision

```
Score: 3.95/5 = 79%

Decision thresholds:
├── ≥ 80%: Strong GO
├── 60-79%: Conditional GO
├── 40-59%: Needs major adjustments
└── < 40%: NO-GO

Decision: CONDITIONAL GO
├── Proceed with project
├── Monitor schedule closely
├── Have contingency plans ready
└── Weekly feasibility re-assessment
```

---

## 9. Recommendations

### 9.1 Immediate Actions
1. ✅ Confirm timeline với GVHD
2. ✅ Setup Label Studio environment
3. ✅ Begin annotator training
4. ✅ Start data anonymization pipeline

### 9.2 Risk Mitigations
1. Daily progress tracking cho annotation
2. Weekly model checkpoint
3. Bi-weekly GVHD check-in
4. Scope reduction plan ready

### 9.3 Success Enablers
1. Clear communication trong team
2. Strict deadline adherence
3. Focus on core features (NER > Web App)
4. Documentation as you go

---

## 10. Appendix: Reference Studies

| Study | Dataset Size | F1-Score | Model |
|-------|--------------|----------|-------|
| Resume Parser (2019) | 500 CVs | 82% | BERT |
| CV-NER (2020) | 300 CVs | 78% | BiLSTM-CRF |
| JobBERT (2021) | 1000 JDs | 85% | BERT |
| ResumeNER (2022) | 200 CVs | 75% | BERT-base |

**Conclusion**: Our target F1 ≥ 75% with 200 CVs is **realistic** based on literature.

---

*Document created as part of CV-NER Research Project documentation.*
