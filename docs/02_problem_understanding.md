# 02. Problem Understanding - Hiểu Bài Toán & Context

> **Document Version**: 1.0
> **Last Updated**: 2026-01-23
> **Status**: Approved
> **Related Documents**: [01_requirements_intake.md](./01_requirements_intake.md), [03_feasibility_analysis.md](./03_feasibility_analysis.md)

---

## 1. Executive Summary

Dự án nghiên cứu này nhằm giải quyết vấn đề **tự động hóa việc trích xuất thông tin từ CV** sử dụng kỹ thuật Named Entity Recognition (NER) và **so khớp kỹ năng** giữa CV và Job Description (JD). Đây là bài toán thuộc lĩnh vực Natural Language Processing (NLP), có ứng dụng thực tiễn cao trong tuyển dụng và quản lý nhân sự.

---

## 2. Pain Points Analysis

### 2.1 Vấn Đề Hiện Tại

#### Pain Point 1: HR mất nhiều thời gian đọc CV thủ công
```
Current State:
├── HR nhận hàng trăm CV cho 1 vị trí
├── Mỗi CV mất 3-5 phút để đọc và đánh giá
├── Dễ bỏ sót thông tin quan trọng
└── Mệt mỏi → đánh giá thiếu nhất quán

Impact:
├── Chi phí nhân sự cao
├── Time-to-hire kéo dài
├── Candidate experience kém
└── Có thể miss ứng viên tốt
```

#### Pain Point 2: Không có chuẩn format CV
```
Current State:
├── Mỗi ứng viên dùng format khác nhau
├── Thông tin nằm rải rác
├── Khó trích xuất tự động bằng rule-based
└── Một số CV thiếu thông tin quan trọng

Impact:
├── Khó so sánh ứng viên
├── Automation bằng regex không hiệu quả
├── Data entry thủ công tốn thời gian
└── Database không structured
```

#### Pain Point 3: Khó so sánh ứng viên với JD
```
Current State:
├── JD liệt kê requirements bằng text
├── CV mô tả skills/experience bằng text
├── HR phải mentally map giữa 2 bên
└── Không có metric khách quan

Impact:
├── Đánh giá chủ quan
├── Bias trong tuyển dụng
├── Ứng viên qualified bị reject
├── Ứng viên không phù hợp được chọn
```

### 2.2 Root Cause Analysis (5 Whys)

```
Problem: HR mất thời gian xử lý CV

Why 1: Vì phải đọc thủ công?
→ Vì không có tool tự động extract thông tin

Why 2: Tại sao không có tool?
→ Vì CV có nhiều format khác nhau, rule-based không hiệu quả

Why 3: Tại sao rule-based không hiệu quả?
→ Vì ngôn ngữ tự nhiên có nhiều cách diễn đạt

Why 4: Tại sao không dùng AI/ML?
→ Vì cần data + expertise + resources

Why 5: ROOT CAUSE:
→ Thiếu dataset annotated + model trained cho tiếng Anh trên CV Việt Nam
```

---

## 3. Stakeholder Analysis

### 3.1 Stakeholder Map

```
                    High Influence
                         │
         GVHD ───────────┼─────────── Hội đồng NCKH
         (Manage        │              (Monitor)
          Closely)       │
                        │
Low Interest ───────────┼─────────── High Interest
                        │
         End Users ─────┼─────────── Research Team
         (Keep          │              (Key Player)
          Informed)     │
                        │
                    Low Influence
```

### 3.2 Chi Tiết Stakeholders

#### A. Giảng Viên Hướng Dẫn (GVHD)
| Aspect | Detail |
|--------|--------|
| **Role** | Hướng dẫn + Đánh giá |
| **Interest** | Cao - Thành công của đề tài |
| **Influence** | Cao - Quyết định hướng nghiên cứu |
| **Expectation** | Báo cáo chất lượng, demo hoạt động |
| **Communication** | Meeting định kỳ, email |

#### B. Hội Đồng NCKH Trường
| Aspect | Detail |
|--------|--------|
| **Role** | Nghiệm thu, chấm điểm |
| **Interest** | Trung bình |
| **Influence** | Cao - Quyết định kết quả |
| **Expectation** | Tuân thủ quy định, đóng góp khoa học |
| **Communication** | Báo cáo, poster, presentation |

#### C. End Users (HR/Recruiters)
| Aspect | Detail |
|--------|--------|
| **Role** | Người dùng cuối (giả định) |
| **Interest** | Cao - Hưởng lợi từ giải pháp |
| **Influence** | Thấp - Không tham gia trực tiếp |
| **Expectation** | Tool dễ dùng, chính xác |
| **Communication** | User research (nếu có) |

#### D. Research Team
| Aspect | Detail |
|--------|--------|
| **Role** | Thực hiện nghiên cứu |
| **Interest** | Cao - Hoàn thành đề tài |
| **Influence** | Trung bình |
| **Expectation** | Hướng dẫn rõ ràng, resources đủ |
| **Communication** | Daily/Weekly sync |

---

## 4. KPIs & Success Metrics

### 4.1 Technical Metrics

| Metric | Target | Priority | Measurement |
|--------|--------|----------|-------------|
| **F1-Score NER** | ≥ 75% | Critical | Eval on test set |
| **Skill Matching Accuracy** | ≥ 70% | High | Manual evaluation |
| **Processing Time** | ≤ 5s/CV | Medium | Benchmark |
| **API Latency** | ≤ 2s | Medium | Load testing |

### 4.2 Research Metrics

| Metric | Target | Priority | Measurement |
|--------|--------|----------|-------------|
| **CVs Annotated** | ≥ 200 | Critical | Label Studio count |
| **Inter-annotator Agreement** | ≥ 80% | High | Cohen's Kappa |
| **Model Experiments** | ≥ 3 | Medium | Experiment tracking |
| **Documentation** | Complete | High | Checklist |

### 4.3 Deliverable Metrics

| Deliverable | Target | Priority | Deadline |
|-------------|--------|----------|----------|
| **Báo cáo NCKH** | Hoàn chỉnh | Critical | Week 12 |
| **Web App** | Demo được | High | Week 11 |
| **Trained Model** | F1 ≥ 75% | Critical | Week 10 |
| **Dataset** | 200+ CVs | Critical | Week 6 |

### 4.4 Success Criteria Summary

```
✓ SUCCESS = (F1-Score ≥ 75%)
          ∧ (200+ CVs annotated)
          ∧ (Web App works)
          ∧ (Báo cáo hoàn chỉnh)
          ∧ (GVHD approved)
          ∧ (Hội đồng pass)
```

---

## 5. Constraints Analysis

### 5.1 Time Constraints

```
Total: 12 weeks (84 days)

Distribution:
├── Setup & Docs:      2 weeks (16.7%)
├── Annotation:        4 weeks (33.3%)
├── Training:          3 weeks (25.0%)
├── Web App:           2 weeks (16.7%)
└── Testing & Report:  1 week  (8.3%)

Buffers: None (tight schedule)
```

### 5.2 Cost Constraints

| Category | Budget | Actual |
|----------|--------|--------|
| Cloud/GPU | $0 | Google Colab Free |
| API Costs | $0 | No external APIs |
| Tools | $0 | All open-source |
| Team | $0 | Volunteer |
| **Total** | **$0** | **$0** |

### 5.3 People Constraints

```
Team Capacity:
├── 1 Leader: Full-time equivalent (học + nghiên cứu)
│   ├── Coding: ~20 hrs/week
│   ├── Research: ~10 hrs/week
│   └── Coordination: ~5 hrs/week
│
└── 4 Annotators: Part-time
    ├── Annotation: ~10-15 hrs/week each
    └── Rate: ~10-15 CVs/person/week

Bottlenecks:
├── Leader: Single point of failure for technical tasks
├── Annotators: May have schedule conflicts
└── No backup for critical roles
```

### 5.4 Technical Constraints

| Constraint | Impact | Mitigation |
|------------|--------|------------|
| Colab session timeout | Training interruption | Checkpointing |
| T4 GPU memory (15GB) | Batch size limit | Gradient accumulation |
| No dedicated server | Can't host 24/7 | Local demo |
| Free tier limits | Queue wait times | Off-peak training |

### 5.5 Legal Constraints

```
Data Privacy:
├── MUST anonymize before use
├── MUST NOT publish raw CVs
├── MUST NOT use for commercial purposes
└── MUST credit UEH data source

Model Licensing:
├── BERT: Apache 2.0 ✓
├── Transformers: Apache 2.0 ✓
└── Sentence-BERT: Apache 2.0 ✓
```

---

## 6. Priority Matrix

### 6.1 MoSCoW Prioritization

#### MUST HAVE (Critical)
| ID | Requirement | Reason |
|----|-------------|--------|
| M1 | NER Model trained | Core of research |
| M2 | 200+ CVs annotated | Required for training |
| M3 | Evaluation metrics | Scientific rigor |
| M4 | Báo cáo NCKH | Deliverable |

#### SHOULD HAVE (High)
| ID | Requirement | Reason |
|----|-------------|--------|
| S1 | Skill Matching module | Part of scope |
| S2 | Web App demo | Visual proof |
| S3 | Good documentation | Reproducibility |

#### COULD HAVE (Medium)
| ID | Requirement | Reason |
|----|-------------|--------|
| C1 | PDF upload feature | User-friendly |
| C2 | Export results JSON/PDF | Utility |
| C3 | JD input interface | Demo completeness |

#### WON'T HAVE (Low/Excluded)
| ID | Requirement | Reason |
|----|-------------|--------|
| W1 | Multi-language support | Focus on English only |
| W2 | Production deployment | Only demo (Docker Compose local) |
| W3 | Mobile app | Not required for NCKH |
| W4 | Advanced analytics dashboard | Out of scope |

### 6.2 Priority Visualization

```
              ┌─────────────────────────────────┐
              │         CRITICAL                │
              │  NER Model, Annotation, Report  │
              ├─────────────────────────────────┤
              │           HIGH                  │
              │  Skill Matching, Web App, Docs  │
              ├─────────────────────────────────┤
              │          MEDIUM                 │
              │    PDF Upload, Export, UI       │
              ├─────────────────────────────────┤
              │           LOW                   │
              │  Career Path, Multi-lang, Prod  │
              └─────────────────────────────────┘
```

---

## 7. Domain Knowledge

### 7.1 CV Structure (Common Sections)

```
Typical CV Structure:
├── Personal Information
│   ├── Name
│   ├── Contact (email, phone)
│   └── Address
│
├── Summary/Objective
│
├── Work Experience
│   ├── Company name
│   ├── Job title
│   ├── Duration
│   └── Description
│
├── Education
│   ├── Institution
│   ├── Degree
│   ├── Major
│   └── GPA (optional)
│
├── Skills
│   ├── Technical skills
│   ├── Soft skills
│   └── Languages
│
├── Certifications
│
├── Projects
│
└── References (optional)
```

### 7.2 NER Entities for CV (10 Types, 21 BIO Labels)

| Entity Type | Examples | BIO Tags |
|-------------|----------|----------|
| PER (Person) | John Smith | B-PER, I-PER |
| ORG (Organization) | Google, MIT | B-ORG, I-ORG |
| DATE | 2020-2022, Jan 2021 | B-DATE, I-DATE |
| LOC (Location) | Ho Chi Minh City | B-LOC, I-LOC |
| SKILL | Python, Leadership | B-SKILL, I-SKILL |
| DEGREE | Bachelor, Master | B-DEGREE, I-DEGREE |
| MAJOR | Computer Science | B-MAJOR, I-MAJOR |
| JOB_TITLE | Software Engineer | B-JOB_TITLE, I-JOB_TITLE |
| PROJECT | E-commerce Platform | B-PROJECT, I-PROJECT |
| CERT (Certification) | AWS Solutions Architect, PMP | B-CERT, I-CERT |

### 7.3 Skill Matching Concepts

```
Matching Types:
├── Exact Match: "Python" = "Python"
├── Synonym Match: "JS" = "JavaScript"
├── Hierarchical: "React" ⊂ "Frontend" ⊂ "Web Development"
└── Semantic: "Machine Learning" ~ "Deep Learning"

Scoring Methods:
├── Hard Skills: Exact/Synonym matching
├── Soft Skills: Semantic similarity
└── Overall: Weighted average
```

---

## 8. Context Diagram

### 8.1 System Context

```
┌─────────────────────────────────────────────────────────────────┐
│                    CV Assistant System Context                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  User Interface (React)                                          │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  Chat Interface  │  CV Upload  │  Career Path View      │    │
│  └─────────────────────────────────────────────────────────┘    │
│                            │                                     │
│                            ▼                                     │
│              ┌─────────────────────────────┐                    │
│              │     API Gateway (Spring)    │                    │
│              │     Authentication + Routing │                    │
│              └─────────────────────────────┘                    │
│                            │                                     │
│     ┌──────────────────────┼──────────────────────┐             │
│     ▼                      ▼                      ▼             │
│  ┌────────┐  ┌────────┐  ┌────────┐  ┌────────┐               │
│  │Chatbot │  │  NER   │  │ Skill  │  │Career  │               │
│  │Service │  │Service │  │Matcher │  │Service │               │
│  │(RAG)   │  │(BERT)  │  │(SBERT) │  │(O*NET) │               │
│  └────────┘  └────────┘  └────────┘  └────────┘               │
│      │                                                          │
│      ▼                                                          │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │              Ollama (Llama 3.2)                          │    │
│  │              ChromaDB (Knowledge + Memory)                │    │
│  │              PostgreSQL (User + Threads)                  │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 8.2 Data Flow Overview

```
[PDF CV]
    │
    ▼
┌──────────────────┐
│   PDF Parser     │ ──────▶ [Plain Text]
│   (PyPDF2)       │
└──────────────────┘
    │
    ▼
┌──────────────────┐
│   Preprocessor   │ ──────▶ [Tokens]
│   (Tokenizer)    │
└──────────────────┘
    │
    ▼
┌──────────────────┐
│   NER Model      │ ──────▶ [BIO Labels]
│   (BERT)         │
└──────────────────┘
    │
    ▼
┌──────────────────┐
│   Post-process   │ ──────▶ [Structured JSON]
│   (Label2Entity) │
└──────────────────┘
    │
    ▼
┌──────────────────┐              ┌──────────────────┐
│   Skill Matcher  │◀─────────────│   JD Skills      │
│   (SBERT)        │              │   (Input)        │
└──────────────────┘              └──────────────────┘
    │
    ▼
[Match Score 0-100%]
```

---

## 9. Assumptions & Dependencies

### 9.1 Assumptions

| ID | Assumption | Risk if Wrong | Validation |
|----|------------|---------------|------------|
| A1 | CVs chủ yếu tiếng Anh | Model không work với tiếng Việt | Sample check |
| A2 | PDF có thể extract text (không phải scan) | OCR needed | Test PDF parser |
| A3 | Google Colab luôn available | Training delays | Backup plan |
| A4 | 200 CVs đủ cho fine-tuning | Low accuracy | Check literature |
| A5 | Annotators có thời gian | Annotation delays | Weekly check |

### 9.2 Dependencies

```
External Dependencies:
├── Hugging Face Transformers
│   ├── bert-base-uncased
│   └── sentence-transformers
├── Label Studio
│   └── Self-hosted annotation
├── Google Colab
│   └── GPU for training
└── UEH Server
    └── Download raw CVs

Internal Dependencies:
├── Annotation → Training (MUST complete first)
├── Training → Web App (Need model)
└── All modules → Report (Need results)
```

---

## 10. Glossary

| Term | Definition |
|------|------------|
| **NER** | Named Entity Recognition - Nhận dạng thực thể có tên |
| **BIO** | Begin-Inside-Outside tagging scheme |
| **CV** | Curriculum Vitae - Sơ yếu lý lịch |
| **JD** | Job Description - Mô tả công việc |
| **F1-Score** | Harmonic mean of Precision and Recall |
| **BERT** | Bidirectional Encoder Representations from Transformers |
| **Fine-tuning** | Tinh chỉnh pre-trained model trên task cụ thể |
| **Annotation** | Gán nhãn dữ liệu cho training |
| **PII** | Personally Identifiable Information |
| **GVHD** | Giảng viên hướng dẫn |

---

*Document created as part of CV-NER Research Project documentation.*
