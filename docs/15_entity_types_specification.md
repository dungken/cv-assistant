# 15. Entity Types Specification

> **Document Version**: 1.0
> **Last Updated**: 2026-01-23
> **Status**: Approved
> **Product Name**: CV Assistant
> **Related Documents**: [04_requirements_classification.md](./04_requirements_classification.md), [16_annotation_guidelines.md](./16_annotation_guidelines.md)

---

## 1. Overview

CV Assistant uses Named Entity Recognition (NER) to extract structured information from CV documents. This document specifies the 10 entity types used in the system, following the BIO (Beginning-Inside-Outside) tagging scheme.

### 1.1 BIO Tagging Scheme

| Tag Prefix | Meaning | Example |
|------------|---------|---------|
| **B-** | Beginning of entity | `[John]B-PER` |
| **I-** | Inside/continuation of entity | `[Doe]I-PER` |
| **O** | Outside (not an entity) | `works` → `O` |

### 1.2 Entity Types Summary

| # | Entity Type | Tag | Description | Priority |
|---|-------------|-----|-------------|----------|
| 1 | Person | PER | Names of individuals | High |
| 2 | Organization | ORG | Company/institution names | High |
| 3 | Date | DATE | Dates, time periods | High |
| 4 | Location | LOC | Geographic locations | Medium |
| 5 | Skill | SKILL | Technical and soft skills | Critical |
| 6 | Degree | DEGREE | Academic degrees | High |
| 7 | Major | MAJOR | Fields of study | High |
| 8 | Job Title | JOB_TITLE | Professional titles | Critical |
| 9 | Project | PROJECT | Project names | Medium |
| 10 | Certification | CERT | Professional certifications | Medium |

---

## 2. Detailed Entity Specifications

### 2.1 PER (Person)

**Description**: Names of individuals mentioned in the CV.

| Aspect | Specification |
|--------|---------------|
| **B-Tag** | B-PER |
| **I-Tag** | I-PER |
| **Typical Location** | Header, References |
| **Expected F1** | ≥ 80% |

**Examples**:
```
"John Doe"           → [John]B-PER [Doe]I-PER
"Nguyen Van A"       → [Nguyen]B-PER [Van]I-PER [A]I-PER
"Dr. Jane Smith"     → [Dr.]B-PER [Jane]I-PER [Smith]I-PER
"J. Robert"          → [J.]B-PER [Robert]I-PER
```

**Annotation Rules**:
- Include titles (Dr., Mr., Mrs.) as part of the name
- Include middle names and initials
- Do NOT include email addresses (handled by regex)
- Do NOT include phone numbers (handled by regex)

**Edge Cases**:
```
"Contact: John"      → [John]B-PER (single name is valid)
"John@gmail.com"     → O (email, use regex)
"John's project"     → [John]B-PER 's project
```

---

### 2.2 ORG (Organization)

**Description**: Names of companies, institutions, universities, and organizations.

| Aspect | Specification |
|--------|---------------|
| **B-Tag** | B-ORG |
| **I-Tag** | I-ORG |
| **Typical Location** | Work Experience, Education |
| **Expected F1** | ≥ 75% |

**Examples**:
```
"Google Inc."                    → [Google]B-ORG [Inc.]I-ORG
"Massachusetts Institute of Technology" → [Massachusetts]B-ORG [Institute]I-ORG [of]I-ORG [Technology]I-ORG
"FPT Software"                   → [FPT]B-ORG [Software]I-ORG
"University of Economics"        → [University]B-ORG [of]I-ORG [Economics]I-ORG
"UEH"                           → [UEH]B-ORG
```

**Annotation Rules**:
- Include legal suffixes (Inc., LLC, Ltd., Corp.)
- Include full university names
- Acronyms alone are valid (e.g., "IBM", "UEH")
- Include "University of X" as single entity

**Edge Cases**:
```
"Google's office"    → [Google]B-ORG 's office
"at MIT and Harvard" → at [MIT]B-ORG and [Harvard]B-ORG
"ABC Company, XYZ Corp" → [ABC]B-ORG [Company]I-ORG , [XYZ]B-ORG [Corp]I-ORG
```

---

### 2.3 DATE (Date)

**Description**: Dates, time periods, durations, and years.

| Aspect | Specification |
|--------|---------------|
| **B-Tag** | B-DATE |
| **I-Tag** | I-DATE |
| **Typical Location** | Work Experience, Education |
| **Expected F1** | ≥ 80% |

**Examples**:
```
"January 2020"       → [January]B-DATE [2020]I-DATE
"Jan 2020"           → [Jan]B-DATE [2020]I-DATE
"2020-01"            → [2020-01]B-DATE
"2018 - 2022"        → [2018]B-DATE [-]I-DATE [2022]I-DATE
"2020 - Present"     → [2020]B-DATE [-]I-DATE [Present]I-DATE
"3 years"            → [3]B-DATE [years]I-DATE
"Q1 2023"            → [Q1]B-DATE [2023]I-DATE
```

**Annotation Rules**:
- Include month names (full or abbreviated)
- Include year ranges as single entity
- Include "Present", "Current", "Now"
- Include duration expressions

**Edge Cases**:
```
"from 2018 to 2022"  → from [2018]B-DATE to [2022]B-DATE (two separate dates)
"2020/01/15"         → [2020/01/15]B-DATE
"Summer 2019"        → [Summer]B-DATE [2019]I-DATE
```

---

### 2.4 LOC (Location)

**Description**: Geographic locations including cities, countries, and addresses.

| Aspect | Specification |
|--------|---------------|
| **B-Tag** | B-LOC |
| **I-Tag** | I-LOC |
| **Typical Location** | Header, Work Experience |
| **Expected F1** | ≥ 70% |

**Examples**:
```
"Ho Chi Minh City"   → [Ho]B-LOC [Chi]I-LOC [Minh]I-LOC [City]I-LOC
"Vietnam"            → [Vietnam]B-LOC
"New York, USA"      → [New]B-LOC [York]I-LOC , [USA]B-LOC
"District 1, HCMC"   → [District]B-LOC [1]I-LOC , [HCMC]B-LOC
"Remote"             → [Remote]B-LOC
```

**Annotation Rules**:
- Include city, state, country names
- "Remote" is a valid location
- Separate city and country with comma → two entities
- Include district/ward information

**Edge Cases**:
```
"123 Main St, NYC"   → 123 Main St , [NYC]B-LOC (address numbers excluded)
"Based in Singapore" → Based in [Singapore]B-LOC
```

---

### 2.5 SKILL (Skill)

**Description**: Technical skills, soft skills, programming languages, tools, and frameworks.

| Aspect | Specification |
|--------|---------------|
| **B-Tag** | B-SKILL |
| **I-Tag** | I-SKILL |
| **Typical Location** | Skills Section, Work Experience |
| **Expected F1** | ≥ 70% |

**Examples**:
```
"Python"             → [Python]B-SKILL
"Machine Learning"   → [Machine]B-SKILL [Learning]I-SKILL
"React.js"           → [React.js]B-SKILL
"Problem Solving"    → [Problem]B-SKILL [Solving]I-SKILL
"Microsoft Excel"    → [Microsoft]B-SKILL [Excel]I-SKILL
"CI/CD"              → [CI/CD]B-SKILL
"REST API"           → [REST]B-SKILL [API]I-SKILL
"English (Fluent)"   → [English]B-SKILL ([Fluent])
```

**Annotation Rules**:
- Include programming languages
- Include frameworks and libraries
- Include soft skills (communication, leadership)
- Include language skills (English, Vietnamese)
- Include tools (Git, Docker, AWS)
- Proficiency levels are NOT part of skill

**Edge Cases**:
```
"Python, Java, C++"  → [Python]B-SKILL , [Java]B-SKILL , [C++]B-SKILL
"3 years of Python"  → 3 years of [Python]B-SKILL
"Advanced Excel"     → Advanced [Excel]B-SKILL
```

---

### 2.6 DEGREE (Degree)

**Description**: Academic degrees and qualifications.

| Aspect | Specification |
|--------|---------------|
| **B-Tag** | B-DEGREE |
| **I-Tag** | I-DEGREE |
| **Typical Location** | Education Section |
| **Expected F1** | ≥ 75% |

**Examples**:
```
"Bachelor of Science"    → [Bachelor]B-DEGREE [of]I-DEGREE [Science]I-DEGREE
"B.S."                   → [B.S.]B-DEGREE
"Master's Degree"        → [Master's]B-DEGREE [Degree]I-DEGREE
"MBA"                    → [MBA]B-DEGREE
"Ph.D."                  → [Ph.D.]B-DEGREE
"Associate Degree"       → [Associate]B-DEGREE [Degree]I-DEGREE
"High School Diploma"    → [High]B-DEGREE [School]I-DEGREE [Diploma]I-DEGREE
```

**Annotation Rules**:
- Include full degree names
- Include abbreviations (B.S., M.S., MBA, Ph.D.)
- Do NOT include the major (separate entity)
- Do NOT include the institution (ORG entity)

**Edge Cases**:
```
"Bachelor of Science in Computer Science"
→ [Bachelor]B-DEGREE [of]I-DEGREE [Science]I-DEGREE in [Computer]B-MAJOR [Science]I-MAJOR

"MBA, Finance"
→ [MBA]B-DEGREE , [Finance]B-MAJOR
```

---

### 2.7 MAJOR (Major/Field of Study)

**Description**: Fields of study, majors, and specializations.

| Aspect | Specification |
|--------|---------------|
| **B-Tag** | B-MAJOR |
| **I-Tag** | I-MAJOR |
| **Typical Location** | Education Section |
| **Expected F1** | ≥ 70% |

**Examples**:
```
"Computer Science"       → [Computer]B-MAJOR [Science]I-MAJOR
"Information Technology" → [Information]B-MAJOR [Technology]I-MAJOR
"Business Administration"→ [Business]B-MAJOR [Administration]I-MAJOR
"Electrical Engineering" → [Electrical]B-MAJOR [Engineering]I-MAJOR
"Finance"                → [Finance]B-MAJOR
"Data Science"           → [Data]B-MAJOR [Science]I-MAJOR
```

**Annotation Rules**:
- Include full major names
- Include specializations
- Separate from degree (DEGREE entity)
- Usually follows "in", "major:", "specialization:"

**Edge Cases**:
```
"Major: CS" → Major: [CS]B-MAJOR
"Specializing in AI" → Specializing in [AI]B-MAJOR
```

---

### 2.8 JOB_TITLE (Job Title)

**Description**: Professional job titles and positions.

| Aspect | Specification |
|--------|---------------|
| **B-Tag** | B-JOB_TITLE |
| **I-Tag** | I-JOB_TITLE |
| **Typical Location** | Work Experience, Header |
| **Expected F1** | ≥ 75% |

**Examples**:
```
"Software Engineer"      → [Software]B-JOB_TITLE [Engineer]I-JOB_TITLE
"Senior Developer"       → [Senior]B-JOB_TITLE [Developer]I-JOB_TITLE
"Project Manager"        → [Project]B-JOB_TITLE [Manager]I-JOB_TITLE
"CEO"                    → [CEO]B-JOB_TITLE
"Data Analyst Intern"    → [Data]B-JOB_TITLE [Analyst]I-JOB_TITLE [Intern]I-JOB_TITLE
"Full Stack Developer"   → [Full]B-JOB_TITLE [Stack]I-JOB_TITLE [Developer]I-JOB_TITLE
```

**Annotation Rules**:
- Include seniority levels (Junior, Senior, Lead)
- Include "Intern" as part of title
- Include common abbreviations (CEO, CTO, PM)
- Do NOT include company name (ORG entity)

**Edge Cases**:
```
"Developer at Google" → [Developer]B-JOB_TITLE at [Google]B-ORG
"Acting Manager"      → [Acting]B-JOB_TITLE [Manager]I-JOB_TITLE
```

---

### 2.9 PROJECT (Project)

**Description**: Names of projects, products, or initiatives.

| Aspect | Specification |
|--------|---------------|
| **B-Tag** | B-PROJECT |
| **I-Tag** | I-PROJECT |
| **Typical Location** | Projects Section, Work Experience |
| **Expected F1** | ≥ 70% |

**Examples**:
```
"E-commerce Platform"    → [E-commerce]B-PROJECT [Platform]I-PROJECT
"Mobile Banking App"     → [Mobile]B-PROJECT [Banking]I-PROJECT [App]I-PROJECT
"Project Alpha"          → [Project]B-PROJECT [Alpha]I-PROJECT
"Customer Portal v2.0"   → [Customer]B-PROJECT [Portal]I-PROJECT [v2.0]I-PROJECT
"AI Chatbot System"      → [AI]B-PROJECT [Chatbot]I-PROJECT [System]I-PROJECT
```

**Annotation Rules**:
- Include project names as stated
- Include version numbers if part of name
- Usually appears after "Project:", in Projects section
- Do NOT include generic descriptions

**Edge Cases**:
```
"Led the XYZ project"    → Led the [XYZ]B-PROJECT project
"Built a web app"        → O (too generic, not a named project)
"Project: Sales Dashboard" → Project: [Sales]B-PROJECT [Dashboard]I-PROJECT
```

---

### 2.10 CERT (Certification)

**Description**: Professional certifications, licenses, and credentials.

| Aspect | Specification |
|--------|---------------|
| **B-Tag** | B-CERT |
| **I-Tag** | I-CERT |
| **Typical Location** | Certifications Section |
| **Expected F1** | ≥ 75% |

**Examples**:
```
"AWS Solutions Architect"        → [AWS]B-CERT [Solutions]I-CERT [Architect]I-CERT
"Google Cloud Professional"      → [Google]B-CERT [Cloud]I-CERT [Professional]I-CERT
"PMP"                           → [PMP]B-CERT
"Certified Scrum Master"        → [Certified]B-CERT [Scrum]I-CERT [Master]I-CERT
"CCNA"                          → [CCNA]B-CERT
"IELTS 7.5"                     → [IELTS]B-CERT [7.5]I-CERT
"Microsoft Azure Fundamentals"   → [Microsoft]B-CERT [Azure]I-CERT [Fundamentals]I-CERT
```

**Annotation Rules**:
- Include full certification names
- Include common abbreviations (PMP, CCNA, CFA)
- Include scores/levels if part of cert (IELTS 7.5)
- Include issuing organization as part of cert name

**Edge Cases**:
```
"AWS Certified - 2023"  → [AWS]B-CERT [Certified]I-CERT - 2023
"Certification: CCNA"   → Certification: [CCNA]B-CERT
```

---

## 3. Label Set for Model Training

### 3.1 Complete Label List (21 labels)

```python
LABELS = [
    "O",           # Outside (not an entity)
    "B-PER",       # Beginning of Person
    "I-PER",       # Inside Person
    "B-ORG",       # Beginning of Organization
    "I-ORG",       # Inside Organization
    "B-DATE",      # Beginning of Date
    "I-DATE",      # Inside Date
    "B-LOC",       # Beginning of Location
    "I-LOC",       # Inside Location
    "B-SKILL",     # Beginning of Skill
    "I-SKILL",     # Inside Skill
    "B-DEGREE",    # Beginning of Degree
    "I-DEGREE",    # Inside Degree
    "B-MAJOR",     # Beginning of Major
    "I-MAJOR",     # Inside Major
    "B-JOB_TITLE", # Beginning of Job Title
    "I-JOB_TITLE", # Inside Job Title
    "B-PROJECT",   # Beginning of Project
    "I-PROJECT",   # Inside Project
    "B-CERT",      # Beginning of Certification
    "I-CERT",      # Inside Certification
]

# Label to ID mapping
label2id = {label: idx for idx, label in enumerate(LABELS)}
id2label = {idx: label for idx, label in enumerate(LABELS)}
```

### 3.2 Classification Head Output

```
Classification Head: Linear(768 → 21)

Output for each token:
├── 21 logits (one per label)
├── Softmax → probabilities
└── Argmax → predicted label
```

---

## 4. Entity Distribution Guidelines

### 4.1 Expected Distribution in CV

| Entity | Frequency | Notes |
|--------|-----------|-------|
| SKILL | High (10-30) | Most frequent |
| DATE | Medium (5-15) | Work + Education |
| ORG | Medium (3-10) | Companies + Schools |
| JOB_TITLE | Medium (2-8) | Per job entry |
| PER | Low (1-3) | Usually just CV owner |
| LOC | Low (1-5) | Address + company locations |
| DEGREE | Low (1-3) | Education entries |
| MAJOR | Low (1-3) | Education entries |
| PROJECT | Variable (0-10) | If Projects section exists |
| CERT | Variable (0-5) | If Certifications section exists |

### 4.2 Quality Targets

| Metric | Target | Critical Entities |
|--------|--------|-------------------|
| Overall F1 | ≥ 75% | - |
| SKILL F1 | ≥ 70% | Primary for matching |
| JOB_TITLE F1 | ≥ 75% | Primary for career |
| ORG F1 | ≥ 75% | Work verification |
| DATE F1 | ≥ 80% | Timeline accuracy |

---

## 5. Integration with O*NET

### 5.1 Skill Mapping

Extracted SKILL entities are mapped to O*NET skill taxonomy:

```
CV Skill         → O*NET Skill Category
─────────────────────────────────────────
"Python"         → Programming Languages
"Leadership"     → Management Skills
"SQL"            → Database Skills
"Communication"  → Interpersonal Skills
"AWS"            → Cloud Computing
```

### 5.2 Job Title Mapping

Extracted JOB_TITLE entities are matched to O*NET occupation database:

```
CV Job Title            → O*NET Code
───────────────────────────────────────
"Software Engineer"     → 15-1252.00
"Data Scientist"        → 15-2051.00
"Project Manager"       → 11-9199.02
"Marketing Manager"     → 11-2021.00
```

---

*Document created as part of CV Assistant Research Project documentation.*
