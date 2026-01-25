# 14. Feedback & Improvement - Phản Hồi và Cải Tiến

> **Document Version**: 1.0
> **Last Updated**: 2026-01-23
> **Status**: Approved
> **Related Documents**: [13_review_monitoring.md](./13_review_monitoring.md)

---

## 1. Feedback Collection Framework

### 1.1 Feedback Sources

```
Feedback Sources:
├── Internal Feedback
│   ├── Team retrospectives
│   ├── Self-reflection
│   └── Code review comments
│
├── External Feedback
│   ├── GVHD reviews
│   ├── Peer reviews
│   └── Final presentation feedback
│
└── Technical Feedback
    ├── Model metrics
    ├── Error analysis
    └── System performance
```

### 1.2 Feedback Collection Schedule

| Source | Frequency | Method | Owner |
|--------|-----------|--------|-------|
| Team Retrospective | End of each phase | Meeting | Leader |
| GVHD Feedback | Bi-weekly | Meeting/Email | Leader |
| Model Metrics | Per experiment | Automated logging | Leader |
| Error Analysis | After training | Manual review | Leader |

---

## 2. Retrospective Process

### 2.1 Sprint/Phase Retrospective

**When**: At the end of each major phase
**Duration**: 30-45 minutes
**Participants**: All team members

**Agenda:**
```
1. Review Phase (5 mins)
   - What was the goal?
   - What was achieved?

2. What Went Well (10 mins)
   - Successes to celebrate
   - Practices to continue

3. What Could Be Improved (10 mins)
   - Challenges faced
   - Things that didn't work

4. Action Items (10 mins)
   - Specific improvements for next phase
   - Assign owners and deadlines

5. Appreciation (5 mins)
   - Thank team members
   - Recognize contributions
```

### 2.2 Retrospective Template

```markdown
# Retrospective - Phase [X]: [Phase Name]
Date: [Date]
Participants: [Names]

## Phase Summary
- **Goal**: [What we aimed to achieve]
- **Result**: [What we actually achieved]
- **Status**: Met / Partially Met / Not Met

## What Went Well 👍
1. [Success 1]
2. [Success 2]
3. [Success 3]

## What Could Be Improved 🔧
1. [Challenge 1] → Proposed solution
2. [Challenge 2] → Proposed solution
3. [Challenge 3] → Proposed solution

## Action Items for Next Phase
| Action | Owner | Deadline | Status |
|--------|-------|----------|--------|
| Action 1 | Name | Date | Pending |
| Action 2 | Name | Date | Pending |

## Key Learnings
- Learning 1
- Learning 2

## Team Recognition
- [Name] for [contribution]
```

---

## 3. Lessons Learned

### 3.1 Lessons Learned Template

```markdown
# Lessons Learned Log

## Entry [Number]
**Date**: [Date]
**Phase**: [Phase name]
**Category**: [Technical / Process / Team / Tools]

### Context
[What was the situation?]

### What Happened
[What went well or what went wrong?]

### Root Cause (if applicable)
[Why did this happen?]

### Lesson
[What did we learn?]

### Recommendation
[What should we do differently in the future?]

### Applied To
[Where/when was this lesson applied?]
```

### 3.2 Expected Lessons Learned Categories

**Technical Lessons:**
```
├── Data Quality
│   ├── What annotation quality issues did we face?
│   ├── How did we improve annotation consistency?
│   └── What data preprocessing steps were critical?
│
├── NER Model Training
│   ├── What hyperparameters worked best?
│   ├── What common errors did the model make?
│   └── How did we handle overfitting/underfitting?
│
├── Chatbot & RAG
│   ├── How did we optimize LlamaIndex performance?
│   ├── What retrieval challenges did we face?
│   ├── How did we tune the ReAct agent?
│   └── What tool calling issues arose?
│
├── Microservices
│   ├── How did services communicate effectively?
│   ├── What API Gateway challenges arose?
│   └── How did we handle service failures?
│
└── Integration & Deployment
    ├── What Docker Compose issues encountered?
    ├── What frontend-backend integration challenges?
    └── How did we solve service discovery?
```

**Process Lessons:**
```
├── Planning
│   ├── Was the timeline realistic?
│   ├── What tasks took longer than expected?
│   └── What should have been planned differently?
│
├── Communication
│   ├── Were team meetings effective?
│   ├── How well did we communicate with GVHD?
│   └── What communication gaps existed?
│
└── Quality Assurance
    ├── Was our QC process effective?
    ├── What quality issues slipped through?
    └── How can we improve quality checks?
```

### 3.3 Pre-filled Lessons (Anticipated)

| Lesson | Category | Source | Status |
|--------|----------|--------|--------|
| Annotation guidelines need examples for edge cases | Data | Anticipated | Pending |
| Checkpoint every epoch to handle Colab timeouts | Technical | Anticipated | Pending |
| Weekly progress tracking prevents surprises | Process | Anticipated | Pending |
| IAA measurement catches quality issues early | Data | Anticipated | Pending |
| Simple baseline first, then optimize | Technical | Anticipated | Pending |
| Ollama requires sufficient RAM for smooth inference | Chatbot | Anticipated | Pending |
| RAG chunk size significantly affects retrieval quality | Chatbot | Anticipated | Pending |
| ReAct agent needs clear tool descriptions | Chatbot | Anticipated | Pending |
| Service health checks essential for microservices | Microservices | Anticipated | Pending |
| Docker Compose simplifies local development | Deployment | Anticipated | Pending |

---

## 4. Continuous Improvement

### 4.1 Improvement Areas

```
Improvement Focus Areas:

1. Model Performance
   ├── Track F1 over iterations
   ├── Identify weak entity types
   └── Targeted improvements

2. Annotation Process
   ├── Reduce annotation time
   ├── Improve consistency
   └── Better tooling

3. Development Workflow
   ├── Code organization
   ├── Testing practices
   └── Documentation

4. Team Collaboration
   ├── Meeting effectiveness
   ├── Task distribution
   └── Knowledge sharing
```

### 4.2 PDCA Cycle

```
Plan-Do-Check-Act for Improvements:

PLAN: Identify improvement opportunity
├── What is the current state?
├── What is the target state?
└── What actions will we take?

DO: Implement the improvement
├── Execute the plan
├── Document changes
└── Collect data

CHECK: Evaluate results
├── Did we achieve the target?
├── What worked, what didn't?
└── Any unintended consequences?

ACT: Standardize or adjust
├── If successful: Make it standard
├── If not: Try different approach
└── Document lessons
```

### 4.3 Improvement Tracking

```markdown
# Improvement Tracker

| ID | Area | Current State | Target State | Action | Status | Result |
|----|------|---------------|--------------|--------|--------|--------|
| I1 | Annotation | 2 CVs/hour | 3 CVs/hour | Better guidelines | Done | 2.5/hr |
| I2 | Model | F1 70% | F1 75% | Hyperparameter tuning | In Progress | - |
| I3 | Meeting | 60 min | 30 min | Better agenda | Done | 35 min |
```

---

## 5. Knowledge Documentation

### 5.1 Technical Documentation

**What to Document:**
```
1. Setup Instructions
   - Environment setup
   - Tool installation
   - Configuration

2. Data Pipeline
   - PDF parsing process
   - Anonymization steps
   - Annotation workflow

3. Model Training
   - Data preprocessing
   - Training configuration
   - Evaluation methods

4. Deployment
   - API setup
   - Frontend build
   - Running the demo
```

### 5.2 Decision Log

```markdown
# Decision Log

| Date | Decision | Context | Alternatives | Rationale | Outcome |
|------|----------|---------|--------------|-----------|---------|
| 1/26 | Use BERT-base-uncased | NER model selection | RoBERTa, DistilBERT | Balance of accuracy and resources | TBD |
| 1/28 | BIO tagging | Label scheme | BIOES | Simplicity | TBD |
| ... | ... | ... | ... | ... | ... |
```

### 5.3 FAQ Document

```markdown
# Project FAQ

## Data
**Q: Why did we choose UEH data?**
A: UEH provided official permission, and the data was already collected and accessible.

**Q: How did we handle PII?**
A: We anonymized all names, emails, phones, and addresses before annotation.

## Model
**Q: Why BERT instead of larger models?**
A: BERT-base fits in Colab T4 GPU and has sufficient capacity for our data size.

**Q: What if F1 < 75%?**
A: We would try more data, hyperparameter tuning, or fall back to CRF.

## Process
**Q: How was annotation quality ensured?**
A: Through clear guidelines, training, regular QC, and IAA measurement.

[Add more Q&A as they arise]
```

---

## 6. Post-Project Review

### 6.1 Final Retrospective

**When**: Week 12, after submission
**Duration**: 1-2 hours
**Format**: Comprehensive review

**Agenda:**
```
1. Project Overview (10 mins)
   - Original goals
   - Final outcomes

2. Success Analysis (20 mins)
   - What went well across all phases
   - Key achievements

3. Challenges Analysis (20 mins)
   - Major challenges faced
   - How they were resolved

4. Lessons Learned Summary (20 mins)
   - Technical lessons
   - Process lessons
   - Team lessons

5. Recommendations (15 mins)
   - For future similar projects
   - For team members' growth

6. Celebration (15 mins)
   - Recognize contributions
   - Celebrate completion
```

### 6.2 Project Summary Template

```markdown
# CV-NER Project - Final Summary

## Project Information
- **Title**: Nghiên cứu & Ứng dụng NLP trong phát triển hệ thống AI tạo lập CV thông minh
- **Duration**: 26/01/2026 - 19/04/2026 (12 weeks)
- **Team Size**: 5 members

## Objectives vs Outcomes

| Objective | Target | Actual | Status |
|-----------|--------|--------|--------|
| Annotate CVs | 200+ | [X] | ✓/✗ |
| NER F1 Score | ≥ 75% | [X%] | ✓/✗ |
| Web App Demo | Working | [Status] | ✓/✗ |
| NCKH Report | Submitted | [Status] | ✓/✗ |

## Key Achievements
1. [Achievement 1]
2. [Achievement 2]
3. [Achievement 3]

## Challenges Overcome
1. [Challenge 1] - [How resolved]
2. [Challenge 2] - [How resolved]

## Technical Metrics
- Model: [Model name]
- Overall F1: [X%]
- Best Entity F1: [Entity] - [X%]
- Worst Entity F1: [Entity] - [X%]
- Processing Time: [X] seconds/CV

## Team Contributions
| Member | Role | Key Contributions |
|--------|------|-------------------|
| Leader | Dev + ML | [Contributions] |
| Member 2 | Annotator | [Contributions] |
| ... | ... | ... |

## Top 5 Lessons Learned
1. [Lesson 1]
2. [Lesson 2]
3. [Lesson 3]
4. [Lesson 4]
5. [Lesson 5]

## Recommendations for Future Work
1. [Recommendation 1]
2. [Recommendation 2]
3. [Recommendation 3]

## Acknowledgments
- GVHD for guidance
- UEH for data access
- Team members for dedication
```

---

## 7. Feedback Integration

### 7.1 GVHD Feedback Tracking

```markdown
# GVHD Feedback Log

| Date | Feedback | Action Taken | Status |
|------|----------|--------------|--------|
| Week 2 | Clarify scope in report | Updated Section 1 | Done |
| Week 4 | Add more error analysis | Added Section 4.3 | Done |
| ... | ... | ... | ... |
```

### 7.2 Presentation Feedback

```markdown
# Presentation Feedback Log

## Pre-Final Presentation (Week 11)
| Feedback | From | Action | Status |
|----------|------|--------|--------|
| Demo too fast | GVHD | Slow down, add pauses | Applied |
| Need more metrics | GVHD | Add slides | Applied |

## Final Presentation (Week 12)
[To be filled after final presentation]
```

---

## 8. Future Improvements (Beyond Project Scope)

### 8.1 Potential Enhancements

```
If project continues or is extended:

Short-term (1-2 months):
├── Support Vietnamese CVs
├── Add more entity types
├── Improve matching algorithm
└── Better UI/UX

Medium-term (3-6 months):
├── Career path recommendation
├── JD parsing and analysis
├── Batch processing
└── User authentication

Long-term (6+ months):
├── Production deployment
├── API service
├── Mobile app
└── Integration with job platforms
```

### 8.2 Research Extensions

```
Potential research directions:

1. Multi-lingual NER
   - Vietnamese + English
   - Cross-lingual transfer

2. Domain Adaptation
   - Different CV styles
   - Industry-specific entities

3. Active Learning
   - Reduce annotation effort
   - Iterative improvement

4. Explainability
   - Why certain entities extracted
   - Confidence visualization
```

---

## 9. Continuous Learning

### 9.1 Resources for Team

**For Leader (Ongoing Learning):**
```
NLP:
- Hugging Face Course: https://huggingface.co/course
- Stanford CS224N (if time permits)

Web Development:
- FastAPI docs: https://fastapi.tiangolo.com
- React docs: https://react.dev

Research Skills:
- Paper reading practice
- Technical writing
```

**For Annotators (Skill Development):**
```
- Basic NLP concepts
- Data quality awareness
- Annotation best practices
```

### 9.2 Skills Gained

```markdown
# Skills Inventory

## Technical Skills
| Skill | Before | After | Notes |
|-------|--------|-------|-------|
| Python | Intermediate | Advanced | ML focus |
| NLP/BERT | Beginner | Intermediate | Fine-tuning |
| FastAPI | None | Basic | API development |
| React | None | Basic | Frontend |

## Soft Skills
| Skill | Development |
|-------|-------------|
| Project Management | Led 5-person team |
| Technical Writing | NCKH report |
| Presentation | Final defense |
| Team Coordination | 12-week project |
```

---

## 10. Closing Checklist

### 10.1 Project Closure

```
□ Technical Closure
  □ Code committed and pushed
  □ Model saved and documented
  □ Data archived securely
  □ Documentation complete

□ Administrative Closure
  □ Report submitted
  □ Presentation delivered
  □ Feedback collected
  □ Lessons learned documented

□ Team Closure
  □ Final retrospective held
  □ Contributions recognized
  □ Knowledge transferred
  □ Celebration done

□ Knowledge Preservation
  □ All docs in repository
  □ Decision log complete
  □ FAQ updated
  □ Future recommendations documented
```

### 10.2 Handover (If Applicable)

```
If project is continued by others:

□ Documentation
  □ README with setup instructions
  □ Architecture documentation
  □ API documentation
  □ Known issues list

□ Access
  □ Repository access granted
  □ Data access transferred
  □ Tool accounts handed over

□ Knowledge Transfer
  □ Walkthrough session conducted
  □ Q&A session held
  □ Contact info for questions
```

---

*Document created as part of CV Assistant Research Project documentation.*

---

## Document Index

Complete documentation for the CV Assistant Research Project:

**Phase 1: Requirements & Analysis**
1. [01_requirements_intake.md](./01_requirements_intake.md) - Nhận yêu cầu
2. [02_problem_understanding.md](./02_problem_understanding.md) - Hiểu bài toán
3. [03_feasibility_analysis.md](./03_feasibility_analysis.md) - Phân tích khả thi
4. [04_requirements_classification.md](./04_requirements_classification.md) - Phân loại yêu cầu
5. [05_problem_decomposition.md](./05_problem_decomposition.md) - Chia nhỏ bài toán

**Phase 2: Solution Design**
6. [06_solution_proposals.md](./06_solution_proposals.md) - Đề xuất phương án
7. [07_tradeoff_analysis.md](./07_tradeoff_analysis.md) - Phân tích đánh đổi
8. [08_optimal_solution.md](./08_optimal_solution.md) - Phương án tối ưu
9. [09_system_architecture.md](./09_system_architecture.md) - Kiến trúc hệ thống

**Phase 3: Planning & Decisions**
10. [10_risk_analysis.md](./10_risk_analysis.md) - Phân tích rủi ro
11. [11_adr_decisions.md](./11_adr_decisions.md) - Quyết định kiến trúc
12. [12_implementation_plan.md](./12_implementation_plan.md) - Kế hoạch triển khai
13. [13_review_monitoring.md](./13_review_monitoring.md) - Review & giám sát
14. [14_feedback_improvement.md](./14_feedback_improvement.md) - Phản hồi & cải tiến (This document)

**Phase 4: Technical Specifications**
15. [15_entity_types_specification.md](./15_entity_types_specification.md) - 10 Entity Types (21 BIO labels)
16. [16_annotation_guidelines.md](./16_annotation_guidelines.md) - Hướng dẫn annotation
17. [17_api_specifications.md](./17_api_specifications.md) - API Specifications
18. [18_data_models.md](./18_data_models.md) - Data Models
19. [19_docker_deployment.md](./19_docker_deployment.md) - Docker Deployment
20. [20_testing_strategy.md](./20_testing_strategy.md) - Testing Strategy
21. [21_chatbot_specification.md](./21_chatbot_specification.md) - Chatbot Specification
