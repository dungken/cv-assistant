# 13. Review & Monitoring - Quy Trình Review và Giám Sát

> **Document Version**: 1.0
> **Last Updated**: 2026-01-23
> **Status**: Approved
> **Related Documents**: [12_implementation_plan.md](./12_implementation_plan.md), [14_feedback_improvement.md](./14_feedback_improvement.md)

---

## 1. Review Framework

### 1.1 Review Types

```
Review Types:
├── Daily Reviews
│   ├── Personal progress check
│   └── Blocker identification
│
├── Weekly Reviews
│   ├── Team sync meeting
│   ├── Progress against plan
│   └── Risk assessment
│
├── Milestone Reviews
│   ├── Phase completion check
│   ├── Deliverable quality
│   └── Go/No-go decision
│
└── External Reviews
    ├── GVHD check-ins
    └── Final presentation
```

### 1.2 Review Responsibilities

| Role | Review Type | Frequency | Responsibilities |
|------|-------------|-----------|------------------|
| Leader | Daily self-review | Daily | Track own progress |
| Leader | Weekly team review | Weekly | Facilitate, track all progress |
| Leader | Milestone review | Per phase | Verify deliverables |
| All | Team sync | Weekly | Report progress, blockers |
| GVHD | Progress review | Bi-weekly | Guidance, feedback |

---

## 2. Daily Monitoring

### 2.1 Daily Standup (Self-Review)

**Time**: 5-10 minutes at start of work session

**Questions to Answer:**
```
1. What did I accomplish yesterday?
2. What will I work on today?
3. Are there any blockers?
4. Am I on track for weekly goals?
```

**Daily Log Template:**
```markdown
## Daily Log - [Date]

### Completed
- [ ] Task 1
- [ ] Task 2

### In Progress
- [ ] Task 3 (50% done)

### Planned for Today
- [ ] Task 4
- [ ] Task 5

### Blockers
- None / Description

### Notes
- Any observations or decisions made
```

### 2.2 Annotation Progress Tracking

**For Annotators (Week 3-6):**

| Metric | Daily Target | Weekly Target |
|--------|--------------|---------------|
| CVs annotated | 2-3 | 12-15 |
| Time spent | 2-3 hours | 10-15 hours |
| Quality issues | < 2 per CV | Track and improve |

**Tracking Spreadsheet:**
```
| Date | Annotator | CVs Done | Time (hrs) | Issues | Notes |
|------|-----------|----------|------------|--------|-------|
| 3/1  | A1        | 3        | 2.5        | 1      | ...   |
| 3/1  | A2        | 2        | 2.0        | 0      | ...   |
```

---

## 3. Weekly Review Process

### 3.1 Weekly Team Sync Meeting

**Schedule**: Every Friday, 30-45 minutes
**Participants**: All team members
**Mode**: Online (Google Meet / Zoom)

**Agenda:**
```
1. Progress Review (15 mins)
   - Each member reports progress
   - Compare with weekly targets

2. Blockers & Issues (10 mins)
   - Identify current blockers
   - Discuss solutions

3. Next Week Planning (10 mins)
   - Set targets for next week
   - Assign tasks

4. Risk Check (5 mins)
   - Review risk register
   - Update if needed

5. Q&A (5 mins)
```

### 3.2 Weekly Progress Report

**Template:**
```markdown
# Weekly Progress Report - Week [X]

## Summary
- **Overall Status**: On Track / At Risk / Behind
- **Completion**: X% of weekly goals

## Progress by Area

### Annotation (Week 3-6)
| Annotator | Target | Actual | % |
|-----------|--------|--------|---|
| A1        | 15     | 14     | 93% |
| A2        | 15     | 12     | 80% |
| ...       | ...    | ...    | ... |
| **Total** | **60** | **52** | **87%** |

### Development (Week 7-12)
| Task | Status | Notes |
|------|--------|-------|
| Task 1 | Done | - |
| Task 2 | In Progress | 70% complete |
| Task 3 | Blocked | Waiting for X |

## Blockers
1. Blocker description → Mitigation plan

## Risks Updated
- Risk X: Probability changed from Medium to High

## Next Week Goals
1. Goal 1
2. Goal 2
3. Goal 3

## Action Items
| Item | Owner | Deadline |
|------|-------|----------|
| Action 1 | Leader | Date |
```

### 3.3 Weekly Metrics Dashboard

```
┌─────────────────────────────────────────────────────────────────┐
│                    Weekly Dashboard - Week X                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ANNOTATION PROGRESS (Week 3-6)                                 │
│  ┌────────────────────────────────────────────┐                 │
│  │ ████████████████████░░░░░░░░░░  65%        │ Target: 200    │
│  │                                130 / 200   │                 │
│  └────────────────────────────────────────────┘                 │
│                                                                  │
│  MODEL PERFORMANCE (Week 7-9)                                   │
│  ┌────────────────────────────────────────────┐                 │
│  │ Current F1: 72%    Target: 75%             │                 │
│  │ ██████████████████████░░░░░░░░  72%        │                 │
│  └────────────────────────────────────────────┘                 │
│                                                                  │
│  TIMELINE STATUS                                                │
│  Week: 8 / 12                                                   │
│  Days Remaining: 28                                             │
│  Status: ● On Track                                             │
│                                                                  │
│  BLOCKERS: 0 active                                             │
│  RISKS: 2 high, 3 medium                                        │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 4. Milestone Reviews

### 4.1 Milestone Review Checklist

**M1: Setup Complete (Week 2)**
```
□ Environment
  □ Python environment working
  □ Label Studio running
  □ GitHub repository created
  □ All team members have access

□ Documentation
  □ Annotation guidelines finalized
  □ Technical docs drafted
  □ README updated

□ Data
  □ 100 CVs anonymized
  □ Sample CVs tested with parser

□ Team
  □ Annotators trained
  □ Practice annotation completed
```

**M2: Annotation 50% (Week 4)**
```
□ Quantity
  □ 100+ CVs annotated
  □ All annotators contributing

□ Quality
  □ IAA ≥ 80%
  □ QC review completed
  □ Common errors identified and addressed

□ Process
  □ Annotation rate sustainable
  □ No major blockers
```

**M3: Annotation Complete (Week 6)**
```
□ Quantity
  □ 200+ CVs annotated
  □ Data exported to CoNLL format

□ Quality
  □ Final QC pass completed
  □ IAA ≥ 80% maintained

□ Data Ready
  □ Train/Val/Test splits created (70/15/15)
  □ Data statistics documented
```

**M4: Baseline + Chatbot Setup (Week 7)**
```
□ NER Code
  □ Preprocessing pipeline working
  □ Training script running
  □ Evaluation code ready
  □ Baseline trained successfully
  □ Baseline F1 recorded

□ Chatbot Setup
  □ Ollama installed and running
  □ Llama 3.2 (3B) model downloaded
  □ LlamaIndex project initialized
  □ Basic chat functionality tested
```

**M5: NER + RAG Ready (Week 9)**
```
□ NER Performance
  □ F1 ≥ 75% on test set
  □ Per-entity metrics documented
  □ Error analysis completed
  □ Final model saved

□ RAG Pipeline
  □ ChromaDB connected to LlamaIndex
  □ Knowledge base indexed
  □ Retrieval returning relevant context
  □ ReAct agent working with tools
  □ Conversation memory implemented
```

**M6: Chatbot + Microservices (Week 10)**
```
□ Microservices
  □ NER Service (:5001) running
  □ Skill Matching Service (:5002) running
  □ Career Service (:5003) running
  □ Chatbot Service (:5004) running

□ API Gateway
  □ Spring Boot gateway (:8080) running
  □ JWT authentication working
  □ All routes configured

□ Integration
  □ Chatbot can call all tools
  □ Services communicate correctly
```

**M7: Full System Ready (Week 11)**
```
□ Frontend (ChatGPT-style)
  □ Login/Register working
  □ Chat interface working
  □ Sidebar thread list working
  □ CV upload integrated
  □ Results display working

□ Deployment
  □ Docker Compose configured
  □ All services containerized
  □ End-to-end test passed
  □ Demo rehearsed
```

**M8: Project Complete (Week 12)**
```
□ Deliverables
  □ NCKH report submitted
  □ Presentation ready
  □ Code documented and on GitHub
  □ Model artifacts saved

□ Quality
  □ Report reviewed
  □ Demo working
  □ All DoD criteria met
```

### 4.2 Go/No-Go Criteria

| Milestone | Go Criteria | No-Go Action |
|-----------|-------------|--------------|
| M1 | All setup items checked, KB initialized | Extend setup 2-3 days |
| M2 | ≥ 80 CVs, IAA ≥ 75% | Retrain annotators |
| M3 | ≥ 200 CVs, data exported | Extend annotation |
| M4 | Training runs, chatbot responds | Debug pipeline/Ollama |
| M5 | F1 ≥ 75%, RAG retrieves correctly | More tuning or CRF fallback |
| M6 | All services running, tools callable | Debug service integration |
| M7 | Full demo works end-to-end | Reduce scope (skip UI polish) |
| M8 | Report submitted, demo ready | Emergency finish |

---

## 5. Quality Assurance

### 5.1 Code Review Process

**When**: Before merging any significant code changes

**Checklist:**
```
□ Code Style
  □ Follows PEP 8 (Python)
  □ Meaningful variable names
  □ No commented-out code

□ Functionality
  □ Works as intended
  □ Handles edge cases
  □ No obvious bugs

□ Documentation
  □ Functions have docstrings
  □ Complex logic explained
  □ README updated if needed

□ Testing
  □ Basic tests pass
  □ Manual testing done
```

### 5.2 Annotation Quality Assurance

**QC Process:**
```
1. Sample Review (Daily)
   - Leader reviews 2-3 random CVs per annotator
   - Check for common errors

2. Double Annotation (Weekly)
   - 5-10 CVs annotated by 2 people
   - Calculate Cohen's Kappa

3. Error Tracking
   - Log errors by type and annotator
   - Provide feedback

4. Correction Loop
   - Annotators fix flagged errors
   - Re-review corrected CVs
```

**Error Categories:**
| Category | Example | Severity |
|----------|---------|----------|
| Wrong Type | ORG labeled as PER | High |
| Boundary Error | "Software" instead of "Software Engineer" | Medium |
| Missed Entity | Skill not annotated | Medium |
| False Positive | Non-entity labeled | Low |

### 5.3 Model Quality Metrics

**Track during training:**
```python
metrics_to_track = {
    'train_loss': [],      # Per epoch
    'val_loss': [],        # Per epoch
    'val_f1': [],          # Per epoch
    'val_precision': [],   # Per epoch
    'val_recall': [],      # Per epoch
    'per_entity_f1': {},   # Per entity type
}
```

**Quality Gates:**
| Metric | Minimum | Target | Stretch |
|--------|---------|--------|---------|
| Overall F1 | 70% | 75% | 80% |
| PER F1 | 75% | 80% | 85% |
| ORG F1 | 70% | 75% | 80% |
| SKILL F1 | 65% | 70% | 75% |

---

## 6. Communication Plan

### 6.1 Internal Communication

| Channel | Purpose | Frequency |
|---------|---------|-----------|
| Group Chat (Zalo/Telegram) | Quick questions, updates | As needed |
| Weekly Meeting | Sync, planning | Weekly |
| Email | Formal updates, documents | As needed |
| GitHub Issues | Technical discussions | As needed |

### 6.2 External Communication (GVHD)

| Type | Frequency | Content |
|------|-----------|---------|
| Progress Update | Bi-weekly | Summary email |
| Check-in Meeting | Monthly | Progress review |
| Milestone Report | Per milestone | Detailed report |
| Final Review | Week 12 | Full presentation |

**Progress Update Template:**
```markdown
Subject: CV-NER NCKH - Progress Update Week X

Dear [GVHD name],

## Summary
- Overall progress: X% complete
- Current phase: [Phase name]
- Status: On Track / At Risk

## Key Achievements
1. Achievement 1
2. Achievement 2

## Challenges
- Challenge (if any)

## Next Steps
1. Next step 1
2. Next step 2

## Questions/Support Needed
- Question (if any)

Best regards,
[Leader name]
```

---

## 7. Monitoring Tools

### 7.1 Progress Tracking

**Option 1: Simple Spreadsheet**
```
Google Sheets with tabs:
├── Weekly Progress
├── Annotation Tracking
├── Task List
├── Risk Register
└── Meeting Notes
```

**Option 2: GitHub Projects**
```
GitHub Project Board:
├── Backlog
├── To Do (This Week)
├── In Progress
├── In Review
└── Done
```

### 7.2 Model Training Monitoring

**Tools:**
- TensorBoard (built-in with Trainer)
- Weights & Biases (optional, free tier)
- Manual logging to CSV

**Key Visualizations:**
```
1. Training/Validation Loss Curves
2. F1 Score Over Epochs
3. Per-Entity F1 Comparison
4. Confusion Matrix
```

### 7.3 Time Tracking (Optional)

**Simple Log:**
```markdown
| Date | Hours | Activity | Notes |
|------|-------|----------|-------|
| 1/26 | 3     | Setup    | Completed |
| 1/27 | 4     | Docs     | In progress |
```

---

## 8. Escalation Process

### 8.1 Escalation Levels

```
Level 1: Self-Resolution
├── Try to solve independently
├── Search documentation/Stack Overflow
└── Time limit: 2-4 hours

Level 2: Team Help
├── Ask in group chat
├── Pair with teammate
└── Time limit: 1 day

Level 3: Leader Decision
├── Leader makes decision
├── May adjust scope/timeline
└── Time limit: 2 days

Level 4: GVHD Consultation
├── Major blockers or scope changes
├── Schedule meeting with GVHD
└── Time limit: 1 week
```

### 8.2 When to Escalate

| Situation | Escalate To | Timeline |
|-----------|-------------|----------|
| Technical question | Team chat | Immediate |
| Blocker > 1 day | Leader | Within 1 day |
| Behind schedule > 3 days | Leader | Immediately |
| Scope change needed | GVHD | Within 1 week |
| Major technical failure | Leader → GVHD | Immediately |

---

## 9. Review Calendar

### 9.1 Full Review Schedule

```
Week 1:  Setup review, knowledge base planning
Week 2:  M1 milestone review (Environment + KB), Annotator readiness
Week 3:  Annotation progress check
Week 4:  M2 milestone review (50% annotation)
Week 5:  Annotation progress check
Week 6:  M3 milestone review (annotation complete)
Week 7:  M4 milestone review (baseline model + chatbot setup)
Week 8:  Training + RAG progress check
Week 9:  M5 milestone review (NER + RAG ready)
Week 10: M6 milestone review (microservices + chatbot)
Week 11: M7 milestone review (full system ready)
Week 12: M8 final review, presentation prep
```

### 9.2 GVHD Meeting Schedule

| Meeting | Week | Purpose |
|---------|------|---------|
| Kickoff | 1 | Confirm scope, expectations |
| Mid-annotation | 4 | Check annotation progress |
| Pre-training | 7 | Review annotation results |
| Training complete | 9 | Review model performance |
| Pre-final | 11 | Demo preview |
| Final | 12 | Final presentation |

---

*Document created as part of CV Assistant Research Project documentation.*
