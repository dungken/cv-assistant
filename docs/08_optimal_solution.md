# 08. Optimal Solution - Phương Án Tối Ưu

> **Document Version**: 1.0
> **Last Updated**: 2026-01-23
> **Status**: Approved
> **Related Documents**: [07_tradeoff_analysis.md](./07_tradeoff_analysis.md), [09_system_architecture.md](./09_system_architecture.md)

---

## 1. Decision Summary

### 1.1 Selected Solution

```
┌─────────────────────────────────────────────────────────────┐
│                    OPTIMAL SOLUTION                          │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│   ✅ OPTION C: BERT Fine-tuning for NER                     │
│                                                              │
│   Model: bert-base-uncased                                   │
│   Approach: Token Classification (NER)                       │
│   Framework: Hugging Face Transformers + PyTorch             │
│   Training: Google Colab (Free T4 GPU)                       │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### 1.2 Decision Rationale

| Criterion | Option C Score | Reason |
|-----------|----------------|--------|
| **Accuracy** | 5/5 | Expected F1 75-85%, meets target |
| **Scientific Value** | 5/5 | Modern NLP approach, publishable |
| **Cost** | 5/5 | $0 with Google Colab |
| **Feasibility** | 4/5 | Achievable with 200 CVs, 12 weeks |
| **Maintainability** | 4/5 | Standard fine-tuning workflow |
| **Total** | **4.75/5** | Highest among all options |

---

## 2. Solution Architecture

### 2.1 High-Level Design

```
┌─────────────────────────────────────────────────────────────────┐
│                    CV-NER Solution Architecture                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────┐     ┌─────────────┐     ┌─────────────┐       │
│  │   Input     │     │   Process   │     │   Output    │       │
│  │   (PDF)     │────▶│   (Model)   │────▶│   (JSON)    │       │
│  └─────────────┘     └─────────────┘     └─────────────┘       │
│                                                                  │
│  Details:                                                        │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ PDF Parser (pdfplumber)                                  │   │
│  │     ↓                                                    │   │
│  │ Text Preprocessor                                        │   │
│  │     ↓                                                    │   │
│  │ BERT Tokenizer (bert-base-uncased)                      │   │
│  │     ↓                                                    │   │
│  │ BERT Encoder (12 layers, 768 hidden)                    │   │
│  │     ↓                                                    │   │
│  │ NER Classification Head (768 → 21 labels)               │   │
│  │     ↓                                                    │   │
│  │ Post-processor (BIO → Entities)                         │   │
│  │     ↓                                                    │   │
│  │ Skill Matcher (Sentence-BERT)                           │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 Model Specification

| Component | Specification |
|-----------|---------------|
| **Base Model** | bert-base-uncased |
| **Parameters** | ~110M |
| **Hidden Size** | 768 |
| **Layers** | 12 |
| **Attention Heads** | 12 |
| **Max Sequence Length** | 512 tokens |
| **Output Labels** | 21 (10 entity types × 2 BIO + O) |

### 2.3 Label Schema

```python
LABEL_LIST = [
    'O',            # 0 - Outside
    'B-PER',        # 1 - Person (Begin)
    'I-PER',        # 2 - Person (Inside)
    'B-ORG',        # 3 - Organization (Begin)
    'I-ORG',        # 4 - Organization (Inside)
    'B-DATE',       # 5 - Date (Begin)
    'I-DATE',       # 6 - Date (Inside)
    'B-LOC',        # 7 - Location (Begin)
    'I-LOC',        # 8 - Location (Inside)
    'B-SKILL',      # 9 - Skill (Begin)
    'I-SKILL',      # 10 - Skill (Inside)
    'B-DEGREE',     # 11 - Degree (Begin)
    'I-DEGREE',     # 12 - Degree (Inside)
    'B-MAJOR',      # 13 - Major (Begin)
    'I-MAJOR',      # 14 - Major (Inside)
    'B-JOB_TITLE',  # 15 - Job Title (Begin)
    'I-JOB_TITLE',  # 16 - Job Title (Inside)
    'B-PROJECT',    # 17 - Project (Begin)
    'I-PROJECT',    # 18 - Project (Inside)
    'B-CERT',       # 19 - Certification (Begin)
    'I-CERT',       # 20 - Certification (Inside)
]

NUM_LABELS = 21
```

---

## 3. Technical Specifications

### 3.1 Training Configuration

```python
TRAINING_CONFIG = {
    # Model
    'model_name': 'bert-base-uncased',
    'num_labels': 21,

    # Data
    'max_seq_length': 512,
    'train_split': 0.7,
    'val_split': 0.15,
    'test_split': 0.15,

    # Training
    'num_epochs': 10,
    'batch_size': 16,
    'learning_rate': 2e-5,
    'weight_decay': 0.01,
    'warmup_ratio': 0.1,
    'gradient_accumulation_steps': 1,

    # Optimizer
    'optimizer': 'AdamW',
    'adam_epsilon': 1e-8,
    'max_grad_norm': 1.0,

    # Evaluation
    'evaluation_strategy': 'epoch',
    'save_strategy': 'epoch',
    'load_best_model_at_end': True,
    'metric_for_best_model': 'f1',

    # Misc
    'seed': 42,
    'fp16': True,  # Mixed precision for T4
}
```

### 3.2 Data Specification

| Aspect | Specification |
|--------|---------------|
| **Total CVs** | 200+ |
| **Train Set** | 140 CVs (70%) |
| **Validation Set** | 30 CVs (15%) |
| **Test Set** | 30 CVs (15%) |
| **Format** | CoNLL (BIO tagging) |
| **Annotation Tool** | Label Studio |

### 3.3 Expected Performance

| Metric | Target | Expected |
|--------|--------|----------|
| **Overall F1** | ≥ 75% | 75-85% |
| **PER F1** | ≥ 80% | 80-90% |
| **ORG F1** | ≥ 75% | 75-85% |
| **DATE F1** | ≥ 80% | 80-90% |
| **SKILL F1** | ≥ 70% | 70-80% |
| **JOB_TITLE F1** | ≥ 70% | 70-80% |
| **PROJECT F1** | ≥ 65% | 65-75% |
| **CERT F1** | ≥ 65% | 65-75% |
| **Inference Time** | ≤ 2s | 1-2s |

---

## 4. Technology Stack

### 4.1 Stack Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    Technology Stack                          │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Frontend         │  API Gateway     │  ML/AI Services      │
│  ────────────────│─────────────────│──────────────────     │
│  React 18        │  Spring Boot 3   │  PyTorch 2.0         │
│  Ant Design 5    │  Java 21         │  Transformers 4.30   │
│  Axios           │  JWT Auth        │  Sentence-BERT       │
│  TypeScript      │  OpenAPI/Swagger │  LlamaIndex          │
│                                                              │
│  Microservices   │  Infrastructure  │  Data                 │
│  ────────────────│─────────────────│──────────────────     │
│  NER Service     │  Docker Compose  │  PostgreSQL          │
│  Skill Service   │  Google Colab    │  ChromaDB            │
│  Career Service  │  Ollama          │  Label Studio        │
│  Chatbot Service │  Local Dev       │  pdfplumber          │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### 4.2 Microservices Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                 CV Assistant Microservices                   │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Frontend (React)  ────┐                                     │
│     :3000              │                                     │
│                        ▼                                     │
│              ┌──────────────────┐                           │
│              │  API Gateway     │                           │
│              │  (Spring Boot)   │                           │
│              │     :8080        │                           │
│              └────────┬─────────┘                           │
│                       │                                      │
│     ┌─────────┬───────┼───────┬─────────┐                   │
│     ▼         ▼       ▼       ▼         ▼                   │
│  ┌─────┐  ┌─────┐  ┌─────┐  ┌─────┐  ┌─────┐               │
│  │ NER │  │Skill│  │Career│ │Chat │  │Ollama│              │
│  │:5001│  │:5002│  │:5003 │ │:5004│  │:11434│              │
│  └─────┘  └─────┘  └─────┘  └─────┘  └─────┘               │
│                                                              │
│  Data Layer:                                                 │
│  ┌────────────┐  ┌────────────┐                             │
│  │ PostgreSQL │  │  ChromaDB  │                             │
│  │   :5432    │  │   :8000    │                             │
│  └────────────┘  └────────────┘                             │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### 4.3 Dependency List

```
# NER Service Dependencies (requirements-ner.txt)
torch>=2.0.0
transformers>=4.30.0
datasets>=2.12.0
accelerate>=0.20.0
evaluate>=0.4.0
seqeval>=1.2.0
fastapi>=0.100.0
uvicorn>=0.22.0
pydantic>=2.0.0
pdfplumber>=0.9.0

# Skill Service Dependencies (requirements-skill.txt)
sentence-transformers>=2.2.0
scikit-learn>=1.2.0
fastapi>=0.100.0
uvicorn>=0.22.0
numpy>=1.24.0

# Chatbot Service Dependencies (requirements-chatbot.txt)
llama-index>=0.10.0
llama-index-llms-ollama>=0.1.0
llama-index-embeddings-huggingface>=0.1.0
chromadb>=0.4.0
fastapi>=0.100.0
uvicorn>=0.22.0

# API Gateway Dependencies (pom.xml)
spring-boot-starter-web: 3.2.0
spring-boot-starter-security: 3.2.0
spring-boot-starter-data-jpa: 3.2.0
jjwt-api: 0.12.3
postgresql: 42.7.0
springdoc-openapi: 2.3.0

# Frontend Dependencies (package.json)
react: ^18.2.0
antd: ^5.0.0
axios: ^1.4.0
typescript: ^5.0.0
@ant-design/icons: ^5.0.0
```

---

## 5. Implementation Plan

### 5.1 Phase Overview

```
Timeline: 12 weeks

Phase 1: Setup & Data (Week 1-6)
├── Week 1-2: Environment setup, documentation
└── Week 3-6: Data annotation (200+ CVs)

Phase 2: Model Development (Week 7-9)
├── Week 7: Data preprocessing, baseline
├── Week 8: Training experiments
└── Week 9: Evaluation, optimization

Phase 3: Integration (Week 10-11)
├── Week 10: Backend API development
└── Week 11: Frontend development

Phase 4: Finalization (Week 12)
├── Integration testing
├── Report writing
└── Presentation preparation
```

### 5.2 Detailed Timeline

| Week | Tasks | Deliverables | Owner |
|------|-------|--------------|-------|
| 1 | Setup Label Studio, Create annotation guidelines | Environment ready | Leader |
| 2 | Train annotators, Start documentation | Guidelines + Docs | All |
| 3-4 | Annotate CVs (batch 1: 100 CVs) | 100 annotated CVs | Annotators |
| 5-6 | Annotate CVs (batch 2: 100 CVs), QC | 200+ annotated CVs | Annotators |
| 7 | Preprocess data, Train baseline | Baseline model | Leader |
| 8 | Hyperparameter tuning, Experiments | Best model | Leader |
| 9 | Evaluation, Error analysis | Evaluation report | Leader |
| 10 | Build FastAPI backend | API ready | Leader |
| 11 | Build React frontend | Web App ready | Leader |
| 12 | Testing, Report, Presentation | Final deliverables | All |

---

## 6. Success Criteria

### 6.1 Must-Have Criteria

| Criterion | Target | Measurement |
|-----------|--------|-------------|
| NER Model F1 | ≥ 75% | seqeval evaluation |
| Annotated CVs | ≥ 200 | Label Studio count |
| Web App Demo | Working | Manual testing |
| NCKH Report | Complete | Submission |

### 6.2 Should-Have Criteria

| Criterion | Target | Measurement |
|-----------|--------|-------------|
| Skill Matching | ≥ 70% accuracy | Manual evaluation |
| Processing Time | ≤ 5s/CV | Benchmark |
| Documentation | Complete | Review |

### 6.3 Could-Have Criteria

| Criterion | Target | Measurement |
|-----------|--------|-------------|
| Export PDF | Working | Manual testing |
| Multiple JD matching | Supported | Testing |

---

## 7. Risk Mitigation

### 7.1 Identified Risks & Mitigations

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| F1 < 75% | Medium | High | More data, hyperparameter tuning, ensemble |
| Colab timeout | High | Medium | Checkpoint every epoch, resume training |
| Annotation delays | Medium | High | Daily tracking, backup annotators |
| PDF parsing fails | Medium | Medium | Multiple parsers, manual fallback |

### 7.2 Contingency Plans

```
If F1 < 75%:
├── Step 1: More hyperparameter tuning
├── Step 2: Add more training data
├── Step 3: Try different BERT variants (RoBERTa, DistilBERT)
└── Step 4: Fall back to Option B (CRF) if severe

If timeline slips:
├── Step 1: Reduce Web App scope (simpler UI)
├── Step 2: Skip export feature
├── Step 3: Focus on NER + basic demo
└── Step 4: Request extension from GVHD

If Colab unavailable:
├── Step 1: Try Kaggle Notebooks
├── Step 2: Reduce batch size, train longer
└── Step 3: Request cloud credits
```

---

## 8. Validation Approach

### 8.1 Model Validation

```
Validation Strategy:
├── Train/Val/Test split: 70/15/15
├── Cross-validation: 5-fold (if time permits)
├── Metrics: Precision, Recall, F1 (seqeval)
├── Per-entity metrics for detailed analysis
└── Error analysis on test set

Evaluation Pipeline:
1. Train model on training set
2. Evaluate on validation set (hyperparameter selection)
3. Final evaluation on test set (reporting)
4. Error analysis (false positives, false negatives)
5. Confusion matrix for entity types
```

### 8.2 System Validation

```
Integration Testing:
├── Upload PDF → Extract text → NER → Display
├── Input JD → Match skills → Show score
├── Export JSON → Verify format
└── End-to-end latency test

User Acceptance Testing:
├── GVHD demo
├── Peer review
└── Final presentation
```

---

## 9. Resource Allocation

### 9.1 Team Allocation

| Role | Person | Allocation | Tasks |
|------|--------|------------|-------|
| Leader | 1 | 100% | Architecture, Training, API, Frontend, Report |
| Annotator 1 | 1 | 50% | Annotation, QA |
| Annotator 2 | 1 | 50% | Annotation, Taxonomy |
| Annotator 3 | 1 | 50% | Annotation |
| Annotator 4 | 1 | 50% | Annotation, Testing |

### 9.2 Compute Allocation

| Resource | Provider | Usage | Cost |
|----------|----------|-------|------|
| Training GPU | Google Colab T4 | ~20-30 hours | $0 |
| Development | Local machine | Continuous | $0 |
| Annotation | Label Studio (local) | Continuous | $0 |

---

## 10. Definition of Done

### 10.1 Project Definition of Done

```
The project is DONE when:
□ NER model achieves F1 ≥ 75% on test set
□ 200+ CVs are annotated and stored
□ Web App demo is working
□ NCKH report is submitted
□ Code is documented and on GitHub
□ Presentation is prepared
□ GVHD approves final deliverables
```

### 10.2 Model Definition of Done

```
The NER model is DONE when:
□ Trained on annotated dataset
□ Evaluated on held-out test set
□ F1 ≥ 75% achieved
□ Inference time ≤ 2s per CV
□ Model saved in Hugging Face format
□ Inference code documented
```

### 10.3 Web App Definition of Done

```
The Web App is DONE when:
□ Upload CV (PDF) works
□ Extracted entities displayed correctly
□ JD input and matching works
□ Match score calculated and shown
□ Basic responsive design
□ Demo-ready for presentation
```

---

*Document created as part of CV-NER Research Project documentation.*
