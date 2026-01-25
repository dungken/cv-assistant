# 16. Annotation Guidelines

> **Document Version**: 1.1
> **Last Updated**: 2026-01-25
> **Status**: Final Draft
> **Product Name**: CV Assistant
> **Related Documents**: [15_entity_types_specification.md](./15_entity_types_specification.md)

---

## 1. Overview

This document provides comprehensive guidelines for annotating CV documents for the NER (Named Entity Recognition) task. Consistent annotation is critical for model performance.

### 1.1 Annotation Goals

| Goal | Description |
|------|-------------|
| **Consistency** | Same entity type across all annotators |
| **Completeness** | All entities annotated, no missing labels |
| **Accuracy** | Correct boundary identification |
| **Quality** | Inter-Annotator Agreement (IAA) ≥ 80% |

### 1.2 Data Summary

| Aspect | Value |
|--------|-------|
| **Raw CVs** | 3,099 PDFs from UEH |
| **Target Annotation** | 200+ CVs |
| **Entity Types** | **10 Types** (PER, ORG, DATE, LOC, SKILL, DEGREE, MAJOR, JOB_TITLE, PROJECT, CERT) |
| **BIO Labels** | **21 Tags** (10 B-tags + 10 I-tags + 1 O-tag) |
| **Sampling** | Stratified by field (IT, Business, etc.) |
| **Language** | English only |
| **Anonymization** | Required before annotation |

---

## 2. Annotation Tool Setup

### 2.1 Label Studio Configuration

```yaml
Project: CV-NER-Annotation
Task Type: Named Entity Recognition
Interface: NER Labeling

Labels:
  - PER (Person): #FF6B6B
  - ORG (Organization): #4ECDC4
  - DATE: #45B7D1
  - LOC (Location): #96CEB4
  - SKILL: #FFEAA7
  - DEGREE: #DDA0DD
  - MAJOR: #98D8C8
  - JOB_TITLE: #F7DC6F
  - PROJECT: #BB8FCE
  - CERT (Certification): #85C1E9
```

### 2.2 Annotator Setup

1. Access Label Studio at: `http://localhost:8080`
2. Login with assigned credentials
3. Select project: "CV-NER-Annotation"
4. Read guidelines before starting
5. Complete training samples first

---

## 3. General Annotation Rules

### 3.1 BIO Tagging Rules

```
Rule 1: Every entity starts with B- tag
Rule 2: Continuation tokens use I- tag
Rule 3: Non-entity tokens are O (Outside)
Rule 4: No entity can start with I- tag
Rule 5: I- tag must follow same entity type
```

**Correct Examples**:
```
"John Doe"     → [John]B-PER [Doe]I-PER ✓
"at Google"    → at [Google]B-ORG ✓
"Python, Java" → [Python]B-SKILL , [Java]B-SKILL ✓
```

**Incorrect Examples**:
```
"John Doe"     → [John]B-PER [Doe]B-PER ✗ (should be I-PER)
"at Google"    → [at]B-ORG [Google]I-ORG ✗ (at is not part of org)
"Python, Java" → [Python]B-SKILL [,]I-SKILL [Java]I-SKILL ✗
```

### 3.2 Boundary Rules

| Situation | Rule | Example |
|-----------|------|---------|
| **Include** | Full entity name | `[Massachusetts Institute of Technology]` |
| **Exclude** | Punctuation at edges | `[Google]B-ORG.` not `[Google.]B-ORG` |
| **Exclude** | Prepositions | `at [Google]` not `[at Google]` |
| **Include** | Compound names | `[Ho Chi Minh City]` |
| **Separate** | List items | `[Python]B-SKILL, [Java]B-SKILL` |

### 3.3 Decision Tree for Edge Cases

Use this decision logic when you are unsure about an entity type:

**Scenario A: Skill vs. Tool vs. Project**
1. Is it a specific software/technology name? (e.g., "JIRA", "Python") → **SKILL**
2. Is it a platform/infrastructure? (e.g., "AWS", "Azure") → **SKILL**
3. Is it a named initiative or product built by the candidate? (e.g., "E-commerce App") → **PROJECT**

**Scenario B: Organization vs. Location**
1. Is it a physical building/office? (e.g., "Building A") → **LOC**
2. Is it a legal entity employing people? (e.g., "Google Vietnam") → **ORG**
3. Is it a city/country? → **LOC**

**Scenario C: Job Title vs. Role in Project**
1. Is it the official employment title? (e.g., "Senior Developer") → **JOB_TITLE**
2. Is it a role described within a specific project description? (e.g., "Acted as Scrum Master") → Annotate "Scrum Master" as **JOB_TITLE** only if it capitalizes/stands out, otherwise treat as description (O).

**Scenario D: Overlapping Entities**
**Rule**: No overlapping entities allowed. Choose the most specific type.

```
Problem: "Google Developer" could be ORG + JOB_TITLE

Solution: Context determines type
├── "Works at Google Developer" → [Google]B-ORG [Developer]B-JOB_TITLE
├── "Google Developer certification" → [Google]B-CERT [Developer]I-CERT
└── If ambiguous, prefer more common interpretation
```

---

## 4. Entity-Specific Guidelines

### 4.1 PER (Person)

**When to annotate**:
- CV owner's name (header)
- Reference contacts
- Managers mentioned

**When NOT to annotate**:
- Email addresses (regex extraction)
- Company names with person's name
- Generic titles ("the manager")

```
Examples:
✓ "John Smith" → [John]B-PER [Smith]I-PER
✓ "Dr. Jane Doe" → [Dr.]B-PER [Jane]I-PER [Doe]I-PER
✗ "john.smith@gmail.com" → O (use regex)
✗ "Johnson & Johnson" → ORG, not PER
```

### 4.2 ORG (Organization)

**When to annotate**:
- Employer companies
- Universities/schools
- Professional organizations
- Clients (if named)

**When NOT to annotate**:
- Generic references ("the company")
- Locations used as org ("Vietnam office")

```
Examples:
✓ "Google Inc." → [Google]B-ORG [Inc.]I-ORG
✓ "MIT" → [MIT]B-ORG
✓ "FPT University" → [FPT]B-ORG [University]I-ORG
✗ "the company" → O
✗ "Google's Python team" → [Google]B-ORG 's [Python]B-SKILL team
```

### 4.3 DATE

**When to annotate**:
- Employment dates
- Education dates
- Project dates
- Certification dates

**Format handling**:
```
✓ "January 2020" → [January]B-DATE [2020]I-DATE
✓ "Jan 2020" → [Jan]B-DATE [2020]I-DATE
✓ "2020-01" → [2020-01]B-DATE
✓ "2018 - 2022" → [2018]B-DATE [-]I-DATE [2022]I-DATE
✓ "Present" → [Present]B-DATE
✓ "Q1 2023" → [Q1]B-DATE [2023]I-DATE
✓ "3 years" → [3]B-DATE [years]I-DATE
```

**Special cases**:
```
"from 2018 to 2022" → from [2018]B-DATE to [2022]B-DATE
(Two separate dates, not one range)

"Summer internship 2019" → Summer internship [2019]B-DATE
(Season alone without year is not annotated)
```

### 4.4 LOC (Location)

**When to annotate**:
- Cities, countries
- Office locations
- Remote work indication

```
✓ "Ho Chi Minh City, Vietnam" → [Ho]B-LOC [Chi]I-LOC [Minh]I-LOC [City]I-LOC , [Vietnam]B-LOC
✓ "Remote" → [Remote]B-LOC
✓ "New York" → [New]B-LOC [York]I-LOC
✗ "123 Main Street" → O (street addresses excluded)
```

### 4.5 SKILL

**When to annotate**:
- Technical skills (languages, frameworks)
- Soft skills (communication, leadership)
- Tools (Git, Docker, AWS)
- Language skills (English, Vietnamese)

```
✓ "Python" → [Python]B-SKILL
✓ "Machine Learning" → [Machine]B-SKILL [Learning]I-SKILL
✓ "Problem Solving" → [Problem]B-SKILL [Solving]I-SKILL
✓ "English (Fluent)" → [English]B-SKILL (Fluent)
✓ "AWS" → [AWS]B-SKILL
```

**Proficiency levels**: NOT part of skill
```
"Advanced Python" → Advanced [Python]B-SKILL
"Python (Expert)" → [Python]B-SKILL (Expert)
```

### 4.6 DEGREE

**When to annotate**:
- Academic degrees
- Abbreviations (B.S., M.S., Ph.D.)

```
✓ "Bachelor of Science" → [Bachelor]B-DEGREE [of]I-DEGREE [Science]I-DEGREE
✓ "MBA" → [MBA]B-DEGREE
✓ "Ph.D." → [Ph.D.]B-DEGREE
```

**Separate from MAJOR**:
```
"Bachelor of Science in Computer Science"
→ [Bachelor]B-DEGREE [of]I-DEGREE [Science]I-DEGREE in [Computer]B-MAJOR [Science]I-MAJOR
```

### 4.7 MAJOR

**When to annotate**:
- Fields of study
- Specializations

```
✓ "Computer Science" → [Computer]B-MAJOR [Science]I-MAJOR
✓ "Business Administration" → [Business]B-MAJOR [Administration]I-MAJOR
```

**Keywords to look for**:
- "Major:", "majoring in", "specialization:"
- After degree name following "in"

### 4.8 JOB_TITLE

**When to annotate**:
- All job positions
- Include seniority (Junior, Senior, Lead)
- Include "Intern"

```
✓ "Software Engineer" → [Software]B-JOB_TITLE [Engineer]I-JOB_TITLE
✓ "Senior Data Scientist" → [Senior]B-JOB_TITLE [Data]I-JOB_TITLE [Scientist]I-JOB_TITLE
✓ "Marketing Intern" → [Marketing]B-JOB_TITLE [Intern]I-JOB_TITLE
```

### 4.9 PROJECT

**When to annotate**:
- Named projects
- Product names
- Initiative names

```
✓ "E-commerce Platform" → [E-commerce]B-PROJECT [Platform]I-PROJECT
✓ "Project Apollo" → [Project]B-PROJECT [Apollo]I-PROJECT
✗ "Built a website" → O (not a named project)
```

### 4.10 CERT

**When to annotate**:
- Professional certifications
- Include scores if present

```
✓ "AWS Solutions Architect" → [AWS]B-CERT [Solutions]I-CERT [Architect]I-CERT
✓ "PMP" → [PMP]B-CERT
✓ "IELTS 7.5" → [IELTS]B-CERT [7.5]I-CERT
```

---

## 5. Quality Assurance

### 5.1 Inter-Annotator Agreement (IAA)

**Target**: IAA ≥ 80% (Cohen's Kappa or F1)

**Process**:
1. 10% of data annotated by 2+ annotators
2. Calculate agreement score
3. Discuss disagreements
4. Update guidelines if needed

### 5.2 Review Checklist

Before submitting annotation:

- [ ] All entities tagged (no missing)
- [ ] Correct B-/I- tags used
- [ ] No overlapping entities
- [ ] Consistent with guidelines
- [ ] Special cases handled correctly

### 5.3 Common Mistakes

| Mistake | Example | Correction |
|---------|---------|------------|
| Missing B- tag | `[Doe]I-PER` alone | Must have `[John]B-PER` first |
| Wrong boundary | `[at Google]B-ORG` | `at [Google]B-ORG` |
| Mixed types | `[Google Engineer]` as one | `[Google]B-ORG [Engineer]B-JOB_TITLE` |
| Over-annotation | Generic terms | Only named entities |

---

## 6. Anonymization Requirements

### 6.1 Before Annotation

All CVs must be anonymized:

| Data Type | Action | Replacement |
|-----------|--------|-------------|
| Real names | Replace | `[NAME]` or fake name |
| Email | Replace | `[EMAIL]` |
| Phone | Replace | `[PHONE]` |
| Address | Replace | Generic location |
| ID numbers | Remove | - |

### 6.2 Annotation After Anonymization

```
Original: "John Doe, john.doe@gmail.com"
Anonymized: "[NAME], [EMAIL]"
Annotation: "[NAME]" → Still annotate as B-PER
            "[EMAIL]" → O (handled by regex)
```

---

## 7. Export Format

### 7.1 CoNLL Format

```
John    B-PER
Doe     I-PER
works   O
at      O
Google  B-ORG
as      O
Software    B-JOB_TITLE
Engineer    I-JOB_TITLE
.       O

He      O
has     O
5       B-DATE
years   I-DATE
of      O
Python  B-SKILL
experience  O
.       O
```

### 7.2 JSON Format (Alternative)

```json
{
  "text": "John Doe works at Google as Software Engineer.",
  "entities": [
    {"start": 0, "end": 8, "label": "PER", "text": "John Doe"},
    {"start": 18, "end": 24, "label": "ORG", "text": "Google"},
    {"start": 28, "end": 45, "label": "JOB_TITLE", "text": "Software Engineer"}
  ]
}
```

---

## 8. Workflow

### 8.1 Daily Annotation Flow

```
1. Login to Label Studio
2. Select assigned batch
3. Read CV text
4. Annotate all entities
5. Review annotations
6. Submit
7. Move to next CV
```

### 8.2 Progress Tracking

| Annotator | Daily Target | Weekly Target |
|-----------|--------------|---------------|
| Annotator 1 | 5 CVs | 25 CVs |
| Annotator 2 | 5 CVs | 25 CVs |
| Annotator 3 | 5 CVs | 25 CVs |
| Annotator 4 | 5 CVs | 25 CVs |
| **Total** | 20 CVs | 100 CVs |

### 8.3 Timeline

| Week | Activity | Target |
|------|----------|--------|
| 1 | Training + Practice | 20 CVs |
| 2-3 | Main Annotation | 80 CVs |
| 4 | Review + Fix | 100 CVs |
| 5-6 | Remaining + QA | 200+ CVs |

---

*Document created as part of CV Assistant Research Project documentation.*
