# 10. Risk Analysis - Phân Tích Rủi Ro

> **Document Version**: 1.0
> **Last Updated**: 2026-01-23
> **Status**: Approved
> **Related Documents**: [09_system_architecture.md](./09_system_architecture.md), [11_adr_decisions.md](./11_adr_decisions.md)

---

## 1. Risk Assessment Overview

### 1.1 Risk Categories

```
Risk Categories:
├── Technical Risks
│   ├── Model performance
│   ├── Infrastructure reliability
│   └── Integration challenges
│
├── Data Risks
│   ├── Data quality
│   ├── Annotation consistency
│   └── Privacy concerns
│
├── Resource Risks
│   ├── Team availability
│   ├── Skill gaps
│   └── Time constraints
│
└── External Risks
    ├── Dependencies on third-party services
    ├── Requirement changes
    └── Stakeholder availability
```

### 1.2 Risk Matrix

```
           │ Low Impact │ Medium Impact │ High Impact │
───────────┼────────────┼───────────────┼─────────────┤
High Prob  │   Medium   │     High      │  Critical   │
───────────┼────────────┼───────────────┼─────────────┤
Med Prob   │    Low     │    Medium     │    High     │
───────────┼────────────┼───────────────┼─────────────┤
Low Prob   │ Negligible │     Low       │   Medium    │
───────────┴────────────┴───────────────┴─────────────┘
```

---

## 2. Technical Risks

### 2.1 Risk T1: NER Model Performance Below Target

| Aspect | Details |
|--------|---------|
| **Risk ID** | T1 |
| **Category** | Technical - Model |
| **Description** | NER model fails to achieve F1-score ≥ 75% |
| **Probability** | Medium (30-50%) |
| **Impact** | High |
| **Risk Level** | HIGH |

**Root Causes:**
- Insufficient training data
- Poor annotation quality
- Suboptimal hyperparameters
- Model architecture not suitable

**Indicators:**
- Validation F1 consistently below 70% during training
- High variance between runs
- Overfitting on training data

**Mitigation Strategies:**
```
Strategy 1: More Data (Prevention)
├── Action: Annotate more CVs if F1 < 70%
├── Trigger: Val F1 < 70% after 5 epochs
├── Owner: Leader
└── Effort: +2 weeks annotation

Strategy 2: Hyperparameter Tuning (Prevention)
├── Action: Grid search over learning rates, batch sizes
├── Trigger: Val F1 plateaus
├── Owner: Leader
└── Effort: +1 week

Strategy 3: Alternative Models (Contingency)
├── Action: Try RoBERTa, DistilBERT, or CRF fallback
├── Trigger: F1 < 70% after all tuning
├── Owner: Leader
└── Effort: +1-2 weeks

Strategy 4: Ensemble (Contingency)
├── Action: Combine multiple models
├── Trigger: Single model F1 insufficient
├── Owner: Leader
└── Effort: +1 week
```

**Monitoring:**
- Track F1 score after each epoch
- Log all experiment results
- Compare with baseline

---

### 2.2 Risk T2: Google Colab Unavailability

| Aspect | Details |
|--------|---------|
| **Risk ID** | T2 |
| **Category** | Technical - Infrastructure |
| **Description** | Google Colab GPU unavailable or session timeouts |
| **Probability** | High (60-80%) |
| **Impact** | Medium |
| **Risk Level** | HIGH |

**Root Causes:**
- High demand for free GPUs
- Session timeout (12 hours max)
- Google policy changes

**Indicators:**
- Long wait times for GPU
- Frequent disconnections
- "GPU not available" errors

**Mitigation Strategies:**
```
Strategy 1: Checkpointing (Prevention)
├── Action: Save model every epoch
├── Trigger: Always
├── Implementation:
│   └── trainer.save_model(f"checkpoint-{epoch}")
└── Effort: Minimal

Strategy 2: Off-Peak Training (Prevention)
├── Action: Train during low-usage hours (night/early morning)
├── Trigger: GPU wait time > 30 mins
├── Schedule: 10 PM - 8 AM UTC+7
└── Effort: Minimal

Strategy 3: Kaggle Notebooks (Contingency)
├── Action: Use Kaggle as backup
├── Trigger: Colab unavailable for >2 days
├── Note: 30 hours/week GPU limit
└── Effort: 2-4 hours setup

Strategy 4: Reduce Training Time (Contingency)
├── Action: Use smaller model (DistilBERT) or fewer epochs
├── Trigger: Persistent availability issues
└── Effort: Configuration change only
```

---

### 2.3 Risk T3: PDF Parsing Failures

| Aspect | Details |
|--------|---------|
| **Risk ID** | T3 |
| **Category** | Technical - Data Processing |
| **Description** | PDF text extraction fails or produces poor quality text |
| **Probability** | Medium (40-60%) |
| **Impact** | Medium |
| **Risk Level** | MEDIUM |

**Root Causes:**
- Scanned PDFs (images)
- Complex layouts
- Non-standard fonts
- Encrypted PDFs

**Indicators:**
- Empty text output
- Garbled characters
- Missing sections

**Mitigation Strategies:**
```
Strategy 1: Multiple Parsers (Prevention)
├── Primary: pdfplumber
├── Fallback 1: PyPDF2
├── Fallback 2: pdf2image + pytesseract (OCR)
└── Implementation: Try in sequence

Strategy 2: Pre-filtering (Prevention)
├── Action: Test sample of CVs before annotation
├── Criteria: Remove unparseable CVs
├── Target: 95% parseable rate
└── Effort: 1-2 hours

Strategy 3: Manual Override (Contingency)
├── Action: Allow manual text input for failed PDFs
├── Trigger: Parser fails completely
└── UI: Textarea for copy-paste
```

---

## 3. Data Risks

### 3.1 Risk D1: Poor Annotation Quality

| Aspect | Details |
|--------|---------|
| **Risk ID** | D1 |
| **Category** | Data - Quality |
| **Description** | Inconsistent or incorrect annotations from annotators |
| **Probability** | Medium (40-60%) |
| **Impact** | High |
| **Risk Level** | HIGH |

**Root Causes:**
- Unclear annotation guidelines
- Insufficient training
- Annotator fatigue
- Ambiguous entity boundaries

**Indicators:**
- Low inter-annotator agreement (IAA < 80%)
- High revision rate during QC
- Model confusion on certain entity types

**Mitigation Strategies:**
```
Strategy 1: Clear Guidelines (Prevention)
├── Action: Create detailed annotation manual
├── Contents:
│   ├── Entity type definitions
│   ├── Boundary rules
│   ├── Edge case examples
│   └── QC checklist
└── Effort: 1 week

Strategy 2: Training Session (Prevention)
├── Action: Train all annotators before starting
├── Duration: 2-3 hours
├── Include: Practice annotations + feedback
└── Effort: 1 day

Strategy 3: Regular QC (Detection)
├── Action: Review 10% of annotations daily
├── Reviewer: Leader
├── Track: Error rate per annotator
└── Effort: 30 mins/day

Strategy 4: IAA Measurement (Detection)
├── Action: Double-annotate 10% of CVs
├── Metric: Cohen's Kappa ≥ 0.8
├── Frequency: Weekly
└── Effort: 1 hour/week

Strategy 5: Feedback Loop (Correction)
├── Action: Provide feedback on common errors
├── Frequency: Weekly team meeting
└── Effort: 30 mins/week
```

---

### 3.2 Risk D2: Data Privacy Breach

| Aspect | Details |
|--------|---------|
| **Risk ID** | D2 |
| **Category** | Data - Privacy |
| **Description** | PII exposure or misuse of CV data |
| **Probability** | Low (10-20%) |
| **Impact** | Critical |
| **Risk Level** | HIGH |

**Root Causes:**
- Incomplete anonymization
- Accidental data sharing
- Unauthorized access

**Indicators:**
- PII found in processed data
- Data shared outside team
- Complaints from data subjects

**Mitigation Strategies:**
```
Strategy 1: Anonymization Pipeline (Prevention)
├── Action: Automated PII removal before annotation
├── Targets: Name, email, phone, address, photo
├── Method: Regex + manual review
└── Verification: 100% review of first 50 CVs

Strategy 2: Access Control (Prevention)
├── Action: Restrict data access to team only
├── Storage: Local machines only
├── No cloud uploads
└── .gitignore data folders

Strategy 3: Data Agreement (Prevention)
├── Action: Team signs data handling agreement
├── Contents: No sharing, no commercial use
└── Compliance with UEH agreement

Strategy 4: Incident Response (Contingency)
├── Action: Report to GVHD immediately
├── Steps: Identify, contain, notify, remediate
└── Document lessons learned
```

---

## 4. Resource Risks

### 4.1 Risk R1: Annotator Unavailability

| Aspect | Details |
|--------|---------|
| **Risk ID** | R1 |
| **Category** | Resource - People |
| **Description** | Annotators unavailable due to personal/academic reasons |
| **Probability** | Medium (40-60%) |
| **Impact** | High |
| **Risk Level** | HIGH |

**Root Causes:**
- Academic workload
- Personal emergencies
- Schedule conflicts
- Loss of interest

**Indicators:**
- Declining annotation rate
- Missed deadlines
- Lack of communication

**Mitigation Strategies:**
```
Strategy 1: Buffer in Schedule (Prevention)
├── Action: Plan for 80% availability
├── Target: 200 CVs / 4 people / 5 weeks
├── Reality: Expect 160 CVs from 4, leader picks up rest
└── Effort: Planning only

Strategy 2: Weekly Check-ins (Detection)
├── Action: Weekly progress meeting
├── Duration: 15-30 mins
├── Track: CVs completed, blockers
└── Effort: 30 mins/week

Strategy 3: Leader Backup (Contingency)
├── Action: Leader annotates if behind
├── Capacity: ~20-30 CVs in emergency
└── Trade-off: Less time for development

Strategy 4: Deadline Flexibility (Contingency)
├── Action: Request extension from GVHD
├── Trigger: 2+ weeks behind schedule
├── Risk: May affect final deadline
└── Effort: Communication
```

---

### 4.2 Risk R2: Technical Skill Gaps

| Aspect | Details |
|--------|---------|
| **Risk ID** | R2 |
| **Category** | Resource - Skills |
| **Description** | Leader lacks skills in NLP/ML/Web development |
| **Probability** | Medium (30-50%) |
| **Impact** | Medium |
| **Risk Level** | MEDIUM |

**Root Causes:**
- Learning curve for new technologies
- Limited prior experience
- Time constraints for learning

**Indicators:**
- Slow progress
- Frequent errors
- Need for external help

**Mitigation Strategies:**
```
Strategy 1: Learning Plan (Prevention)
├── Week 1: Hugging Face NLP course (8 hours)
├── Week 2: FastAPI tutorial (4 hours)
├── Week 3: React basics (4 hours)
└── Total: ~16 hours before heavy coding

Strategy 2: Community Resources (Prevention)
├── Hugging Face forums
├── Stack Overflow
├── GitHub issues
└── Discord communities

Strategy 3: Simplify Architecture (Contingency)
├── Action: Use simpler alternatives
├── FastAPI → Flask (if needed)
├── React → Simple HTML/JS
└── Trade-off: Less polished UI

Strategy 4: External Help (Contingency)
├── Action: Consult with peers or mentors
├── Sources: Classmates, online forums
└── Risk: Time dependency on others
```

---

## 5. Microservices & Chatbot Risks

### 5.1 Risk M1: Ollama/LLM Performance Issues

| Aspect | Details |
|--------|---------|
| **Risk ID** | M1 |
| **Category** | Technical - Chatbot |
| **Description** | Llama 3.2 3B model produces poor quality or slow responses |
| **Probability** | Medium (30-50%) |
| **Impact** | High |
| **Risk Level** | HIGH |

**Root Causes:**
- Model too small for complex queries
- Slow inference on CPU
- Context window limitations
- Poor Vietnamese support

**Mitigation Strategies:**
```
Strategy 1: Prompt Engineering (Prevention)
├── Action: Carefully craft system prompts
├── Include: CV domain context, examples
└── Effort: 1-2 days

Strategy 2: RAG Enhancement (Prevention)
├── Action: Improve knowledge base quality
├── Sources: O*NET, CV guides, best practices
└── Effort: 1 week

Strategy 3: Larger Model (Contingency)
├── Action: Switch to Llama 3.2 8B or Mistral 7B
├── Requirement: More RAM/GPU
└── Trade-off: Slower inference

Strategy 4: Response Caching (Prevention)
├── Action: Cache common queries
├── Storage: ChromaDB
└── Benefit: Faster repeated queries
```

---

### 5.2 Risk M2: Microservices Integration Failures

| Aspect | Details |
|--------|---------|
| **Risk ID** | M2 |
| **Category** | Technical - Architecture |
| **Description** | Services fail to communicate or data inconsistency |
| **Probability** | Medium (40-60%) |
| **Impact** | High |
| **Risk Level** | HIGH |

**Root Causes:**
- Network issues between containers
- API contract mismatches
- Timeout issues
- Service discovery problems

**Mitigation Strategies:**
```
Strategy 1: Docker Compose Network (Prevention)
├── Action: All services on same network
├── Configuration: docker-compose.yml
└── Testing: Health checks

Strategy 2: API Contract Testing (Prevention)
├── Action: Define and validate OpenAPI specs
├── Tools: Swagger validation
└── Effort: 2-3 hours per service

Strategy 3: Circuit Breaker Pattern (Prevention)
├── Action: Implement fallbacks for service failures
├── Chatbot: Gracefully handle tool call failures
└── Effort: 1 day

Strategy 4: Monolith Fallback (Contingency)
├── Action: Merge services if integration too complex
├── Trigger: >1 week debugging integration
└── Trade-off: Less clean architecture
```

---

### 5.3 Risk M3: ChromaDB Data Loss

| Aspect | Details |
|--------|---------|
| **Risk ID** | M3 |
| **Category** | Technical - Data |
| **Description** | Vector store data corruption or loss |
| **Probability** | Low (10-20%) |
| **Impact** | High |
| **Risk Level** | MEDIUM |

**Mitigation Strategies:**
```
Strategy 1: Persistent Volume (Prevention)
├── Action: Mount ChromaDB data to host
├── Docker: volumes: - ./chroma_data:/data
└── Backup: Regular copies

Strategy 2: Re-indexing Script (Recovery)
├── Action: Script to rebuild from source documents
├── Time: 30 mins to rebuild
└── Keep source documents safe
```

---

## 6. External Risks

### 6.1 Risk E1: Requirement Changes from GVHD

| Aspect | Details |
|--------|---------|
| **Risk ID** | E1 |
| **Category** | External - Stakeholder |
| **Description** | GVHD requests changes to scope or approach |
| **Probability** | Medium (30-50%) |
| **Impact** | Medium-High |
| **Risk Level** | MEDIUM |

**Root Causes:**
- Initial requirements unclear
- New ideas during review
- Academic requirements change

**Mitigation Strategies:**
```
Strategy 1: Early Alignment (Prevention)
├── Action: Meeting with GVHD in Week 1
├── Topics: Scope, expectations, timeline
├── Output: Written confirmation
└── Effort: 1-2 hours

Strategy 2: Regular Updates (Prevention)
├── Action: Bi-weekly progress report
├── Contents: Progress, blockers, next steps
├── Channel: Email + meeting if needed
└── Effort: 30 mins bi-weekly

Strategy 3: Change Buffer (Prevention)
├── Action: Keep 10% buffer in timeline
├── Use: Absorb small scope changes
└── Visible: Week 12 buffer

Strategy 4: Scope Negotiation (Contingency)
├── Action: Negotiate if major changes requested
├── Options: Trade features, extend timeline
└── Document: All agreed changes
```

---

## 7. Risk Register Summary

| ID | Risk | Prob | Impact | Level | Owner | Status |
|----|------|------|--------|-------|-------|--------|
| T1 | Model performance below target | Med | High | HIGH | Leader | Monitoring |
| T2 | Colab unavailability | High | Med | HIGH | Leader | Mitigated |
| T3 | PDF parsing failures | Med | Med | MEDIUM | Leader | Mitigated |
| D1 | Poor annotation quality | Med | High | HIGH | Leader | Mitigated |
| D2 | Data privacy breach | Low | Critical | HIGH | All | Mitigated |
| M1 | Ollama/LLM performance issues | Med | High | HIGH | Leader | Monitoring |
| M2 | Microservices integration failures | Med | High | HIGH | Leader | Monitoring |
| M3 | ChromaDB data loss | Low | High | MEDIUM | Leader | Mitigated |
| R1 | Annotator unavailability | Med | High | HIGH | Leader | Monitoring |
| R2 | Technical skill gaps | Med | Med | MEDIUM | Leader | Mitigating |
| E1 | Requirement changes | Med | Med | MEDIUM | Leader | Monitoring |

---

## 8. Risk Monitoring Plan

### 8.1 Monitoring Schedule

| Risk | Metric | Threshold | Frequency | Action |
|------|--------|-----------|-----------|--------|
| T1 | Val F1 | < 70% | Per epoch | Tuning |
| T2 | GPU wait time | > 1 hour | Per session | Switch time |
| T3 | Parse success rate | < 90% | Weekly | Fix parser |
| D1 | IAA | < 0.8 | Weekly | Re-train |
| D2 | PII found | Any | Daily | Immediate fix |
| M1 | LLM response quality | Poor answers | Daily test | Prompt tuning |
| M2 | Service health | Any failure | Per deploy | Debug/fix |
| M3 | ChromaDB status | Connection error | Daily | Restart/recover |
| R1 | CVs completed | < 80% target | Weekly | Escalate |
| R2 | Progress vs plan | > 3 days behind | Weekly | Get help |
| E1 | Scope changes | Any major | Per meeting | Negotiate |

### 8.2 Risk Review Meetings

```
Weekly Risk Review (15 mins):
├── Review current risk status
├── Update risk levels if changed
├── Trigger contingency plans if needed
└── Document in meeting notes

Participants: Leader (required), Annotators (optional)
```

---

## 9. Contingency Budget

### 9.1 Time Contingency

| Phase | Planned | Buffer | Contingency Use |
|-------|---------|--------|-----------------|
| Setup | 2 weeks | 0 | - |
| Annotation | 4 weeks | 0.5 weeks | D1, R1 recovery |
| Training | 3 weeks | 0.5 weeks | T1, T2 recovery |
| Web App | 2 weeks | 0.5 weeks | R2 recovery |
| Final | 1 week | 0.5 weeks | E1, general buffer |
| **Total** | **12 weeks** | **2 weeks** | Absorbed in phases |

### 9.2 Scope Contingency

```
If behind schedule, cut in this order:
├── Level 1: Reduce UI polish (1-2 days saved)
├── Level 2: Skip export PDF feature (2-3 days saved)
├── Level 3: Simplify matching (3-5 days saved)
├── Level 4: Minimal Web App (1 week saved)
└── Level 5: Focus only on NER model + report (2 weeks saved)

Never cut:
├── NER model development
├── 200 CV annotation target
└── Final report
```

---

*Document created as part of CV-NER Research Project documentation.*
