# 06. Solution Proposals - Đề Xuất Phương Án

> **Document Version**: 1.0
> **Last Updated**: 2026-01-23
> **Status**: Approved
> **Related Documents**: [05_problem_decomposition.md](./05_problem_decomposition.md), [07_tradeoff_analysis.md](./07_tradeoff_analysis.md)

---

## 1. Executive Summary

Tài liệu này trình bày 4 phương án giải quyết bài toán NER cho CV:

| Option | Approach | Estimated F1 | Effort | Recommendation |
|--------|----------|--------------|--------|----------------|
| A | Rule-Based + Regex | 40-50% | 2 weeks | ❌ Not recommended |
| B | CRF + FastText | 55-65% | 4 weeks | ⚠️ Backup option |
| C | BERT Fine-tuning | 75-85% | 6 weeks | ✅ **Recommended** |
| D | LLM (GPT/Claude) | 60-70% | 1 week | ❌ Not suitable |

---

## 2. Option A: Rule-Based + Regex

### 2.1 Overview

```
Approach: Pattern matching using handcrafted rules and regular expressions

Architecture:
┌─────────────────────────────────────────────────────────────┐
│                    Rule-Based NER                            │
├─────────────────────────────────────────────────────────────┤
│  Input Text                                                  │
│      │                                                       │
│      ▼                                                       │
│  ┌────────────────┐                                         │
│  │  Regex Rules   │ ─────▶ Email, Phone, Date patterns      │
│  └────────────────┘                                         │
│      │                                                       │
│      ▼                                                       │
│  ┌────────────────┐                                         │
│  │  Keyword Lists │ ─────▶ Skills, Degrees, Job titles      │
│  └────────────────┘                                         │
│      │                                                       │
│      ▼                                                       │
│  ┌────────────────┐                                         │
│  │  Heuristics    │ ─────▶ Section headers, capitalization  │
│  └────────────────┘                                         │
│      │                                                       │
│      ▼                                                       │
│  Extracted Entities                                          │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 Technical Details

```python
# Example implementation
class RuleBasedNER:
    def __init__(self):
        self.email_pattern = r'[\w\.-]+@[\w\.-]+\.\w+'
        self.phone_pattern = r'[\+]?[(]?[0-9]{1,3}[)]?[-\s\.]?[0-9]{3,4}[-\s\.]?[0-9]{4,6}'
        self.date_pattern = r'\b(Jan|Feb|Mar|...|Dec)\s+\d{4}\b|\b\d{4}\s*-\s*\d{4}\b'
        self.skill_list = ['Python', 'Java', 'SQL', ...]
        self.degree_list = ['Bachelor', 'Master', 'PhD', ...]

    def extract(self, text):
        entities = []
        entities.extend(self.extract_emails(text))
        entities.extend(self.extract_phones(text))
        entities.extend(self.extract_dates(text))
        entities.extend(self.extract_skills(text))
        return entities
```

### 2.3 Evaluation

| Criterion | Assessment | Score (1-5) |
|-----------|------------|-------------|
| Accuracy | Low - Many false positives/negatives | 2 |
| Development Time | Fast - 2 weeks | 5 |
| Maintenance | Hard - Rules need constant updates | 1 |
| Scalability | Poor - Doesn't generalize | 1 |
| Scientific Value | Low - Not novel | 1 |

### 2.4 Pros & Cons

**Pros:**
- Simple to implement
- No training data needed
- Interpretable results
- Fast inference

**Cons:**
- Low accuracy (~40-50%)
- Cannot handle variations
- High maintenance burden
- Not suitable for research

### 2.5 Estimated Metrics

| Metric | Value |
|--------|-------|
| **F1-Score** | 40-50% |
| **Development Time** | 2 weeks |
| **Training Data** | 0 (not needed) |
| **Compute Cost** | $0 |

---

## 3. Option B: CRF + FastText

### 3.1 Overview

```
Approach: Traditional ML with Conditional Random Fields and word embeddings

Architecture:
┌─────────────────────────────────────────────────────────────┐
│                    CRF + FastText NER                        │
├─────────────────────────────────────────────────────────────┤
│  Input Text                                                  │
│      │                                                       │
│      ▼                                                       │
│  ┌────────────────┐                                         │
│  │   Tokenizer    │                                         │
│  └────────────────┘                                         │
│      │                                                       │
│      ▼                                                       │
│  ┌────────────────┐    ┌────────────────┐                   │
│  │ FastText       │ +  │ Handcrafted    │                   │
│  │ Embeddings     │    │ Features       │                   │
│  └────────────────┘    └────────────────┘                   │
│      │                        │                              │
│      └──────────┬─────────────┘                              │
│                 ▼                                            │
│         ┌────────────────┐                                  │
│         │      CRF       │                                  │
│         │    Decoder     │                                  │
│         └────────────────┘                                  │
│                 │                                            │
│                 ▼                                            │
│         BIO Labels                                           │
└─────────────────────────────────────────────────────────────┘
```

### 3.2 Technical Details

```python
# Feature extraction for CRF
def extract_features(sentence, i):
    word = sentence[i]
    features = {
        'word': word.lower(),
        'is_capitalized': word[0].isupper(),
        'is_all_caps': word.isupper(),
        'is_digit': word.isdigit(),
        'prefix_2': word[:2],
        'suffix_2': word[-2:],
        'prev_word': sentence[i-1].lower() if i > 0 else '<START>',
        'next_word': sentence[i+1].lower() if i < len(sentence)-1 else '<END>',
        'word_embedding': fasttext_model[word],  # 300-dim vector
    }
    return features

# CRF Model
from sklearn_crfsuite import CRF

crf = CRF(
    algorithm='lbfgs',
    c1=0.1,
    c2=0.1,
    max_iterations=100
)
crf.fit(X_train, y_train)
```

### 3.3 Evaluation

| Criterion | Assessment | Score (1-5) |
|-----------|------------|-------------|
| Accuracy | Medium - Better than rules | 3 |
| Development Time | Medium - 4 weeks | 3 |
| Maintenance | Medium - Feature engineering | 3 |
| Scalability | Medium - Limited by features | 3 |
| Scientific Value | Medium - Traditional approach | 2 |

### 3.4 Pros & Cons

**Pros:**
- Better than rule-based
- Less training data needed than deep learning
- Fast inference
- Interpretable features

**Cons:**
- Requires extensive feature engineering
- Cannot capture complex patterns
- Limited by predefined features
- F1 likely ~55-65%

### 3.5 Estimated Metrics

| Metric | Value |
|--------|-------|
| **F1-Score** | 55-65% |
| **Development Time** | 4 weeks |
| **Training Data** | 100+ annotated samples |
| **Compute Cost** | $0 |

---

## 4. Option C: BERT Fine-tuning ⭐ RECOMMENDED

### 4.1 Overview

```
Approach: Fine-tune pre-trained BERT model for token classification (NER)

Architecture:
┌─────────────────────────────────────────────────────────────┐
│                    BERT NER Model                            │
├─────────────────────────────────────────────────────────────┤
│  Input Text                                                  │
│      │                                                       │
│      ▼                                                       │
│  ┌────────────────────────────────────────────────────┐     │
│  │              BERT Tokenizer                         │     │
│  │         (WordPiece tokenization)                    │     │
│  └────────────────────────────────────────────────────┘     │
│      │                                                       │
│      ▼                                                       │
│  ┌────────────────────────────────────────────────────┐     │
│  │              BERT Encoder                           │     │
│  │         (12 layers, 768 hidden)                     │     │
│  │         Pre-trained on large corpus                 │     │
│  └────────────────────────────────────────────────────┘     │
│      │                                                       │
│      ▼                                                       │
│  ┌────────────────────────────────────────────────────┐     │
│  │           Classification Head                       │     │
│  │         (Linear: 768 → num_labels)                  │     │
│  └────────────────────────────────────────────────────┘     │
│      │                                                       │
│      ▼                                                       │
│  BIO Labels (per token)                                      │
└─────────────────────────────────────────────────────────────┘
```

### 4.2 Technical Details

```python
from transformers import BertForTokenClassification, BertTokenizer, Trainer

# Model setup
model_name = 'bert-base-uncased'
num_labels = 21  # 10 entity types × 2 (B/I) + 1 (O)

model = BertForTokenClassification.from_pretrained(
    model_name,
    num_labels=num_labels
)
tokenizer = BertTokenizer.from_pretrained(model_name)

# Training configuration
training_args = TrainingArguments(
    output_dir='./results',
    num_train_epochs=10,
    per_device_train_batch_size=16,
    per_device_eval_batch_size=16,
    learning_rate=2e-5,
    warmup_ratio=0.1,
    weight_decay=0.01,
    evaluation_strategy='epoch',
    save_strategy='epoch',
    load_best_model_at_end=True,
    metric_for_best_model='f1',
)

# Trainer
trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=train_dataset,
    eval_dataset=eval_dataset,
    compute_metrics=compute_ner_metrics,
)

trainer.train()
```

### 4.3 Label Configuration

```python
# BIO labels for 10 entity types
label_list = [
    'O',           # Outside any entity
    'B-PER',       # Beginning of Person
    'I-PER',       # Inside Person
    'B-ORG',       # Beginning of Organization
    'I-ORG',       # Inside Organization
    'B-DATE',      # Beginning of Date
    'I-DATE',      # Inside Date
    'B-LOC',       # Beginning of Location
    'I-LOC',       # Inside Location
    'B-SKILL',     # Beginning of Skill
    'I-SKILL',     # Inside Skill
    'B-DEGREE',    # Beginning of Degree
    'I-DEGREE',    # Inside Degree
    'B-MAJOR',     # Beginning of Major
    'I-MAJOR',     # Inside Major
    'B-JOB_TITLE', # Beginning of Job Title
    'I-JOB_TITLE', # Inside Job Title
    'B-PROJECT',   # Beginning of Project
    'I-PROJECT',   # Inside Project
    'B-CERT',      # Beginning of Certification
    'I-CERT',      # Inside Certification
]

label2id = {label: i for i, label in enumerate(label_list)}
id2label = {i: label for i, label in enumerate(label_list)}
```

### 4.4 Evaluation

| Criterion | Assessment | Score (1-5) |
|-----------|------------|-------------|
| Accuracy | High - State-of-the-art approach | 5 |
| Development Time | Medium - 6 weeks | 3 |
| Maintenance | Easy - Fine-tuning workflow | 4 |
| Scalability | Good - Transfer learning | 4 |
| Scientific Value | High - Modern NLP approach | 5 |

### 4.5 Pros & Cons

**Pros:**
- High accuracy (75-85% F1 expected)
- Transfer learning from large corpus
- Captures contextual information
- Modern, publishable approach
- Strong community support

**Cons:**
- Requires GPU for training
- Needs 200+ annotated samples
- Slower inference than CRF
- More complex implementation

### 4.6 Estimated Metrics

| Metric | Value |
|--------|-------|
| **F1-Score** | 75-85% |
| **Development Time** | 6 weeks |
| **Training Data** | 200+ annotated CVs |
| **Compute Cost** | $0 (Colab Free) |
| **Training Time** | ~2-4 hours on T4 |

### 4.7 Why BERT?

```
Advantages of BERT for CV-NER:

1. Pre-trained Knowledge
   └── BERT learned language patterns from huge corpus
   └── Can understand context, synonyms, variations

2. Transfer Learning
   └── Only need to fine-tune on small dataset
   └── 200 CVs is sufficient for good results

3. Contextual Embeddings
   └── Same word can have different representations
   └── "Python" as language vs programming language

4. Subword Tokenization
   └── Handles rare/unknown words
   └── "TensorFlow" → "Tensor" + "##Flow"

5. State-of-the-Art
   └── Proven on NER benchmarks
   └── CoNLL-2003 F1 > 92%
```

---

## 5. Option D: LLM (GPT/Claude)

### 5.1 Overview

```
Approach: Use large language models via API for zero-shot/few-shot NER

Architecture:
┌─────────────────────────────────────────────────────────────┐
│                    LLM-based NER                             │
├─────────────────────────────────────────────────────────────┤
│  Input: CV Text + Prompt                                     │
│      │                                                       │
│      ▼                                                       │
│  ┌────────────────────────────────────────────────────┐     │
│  │              Prompt Template                        │     │
│  │  "Extract the following entities from this CV:      │     │
│  │   - Person names                                    │     │
│  │   - Organizations                                   │     │
│  │   - Skills                                          │     │
│  │   ..."                                              │     │
│  └────────────────────────────────────────────────────┘     │
│      │                                                       │
│      ▼                                                       │
│  ┌────────────────────────────────────────────────────┐     │
│  │              LLM API                                │     │
│  │         (GPT-4 / Claude / etc.)                     │     │
│  └────────────────────────────────────────────────────┘     │
│      │                                                       │
│      ▼                                                       │
│  Structured JSON Output                                      │
└─────────────────────────────────────────────────────────────┘
```

### 5.2 Technical Details

```python
# Example with OpenAI API
import openai

def extract_entities_llm(cv_text):
    prompt = f"""
    Extract the following entities from this CV and return as JSON:
    - PER: Person names
    - ORG: Organizations (companies, universities)
    - DATE: Dates and date ranges
    - LOC: Locations
    - SKILL: Technical and soft skills
    - DEGREE: Academic degrees
    - MAJOR: Fields of study
    - JOB_TITLE: Job titles
    - PROJECT: Named projects
    - CERT: Professional certifications

    CV Text:
    {cv_text}

    Return format:
    {{
        "entities": [
            {{"text": "...", "type": "...", "start": ..., "end": ...}},
            ...
        ]
    }}
    """

    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
        temperature=0
    )

    return json.loads(response.choices[0].message.content)
```

### 5.3 Evaluation

| Criterion | Assessment | Score (1-5) |
|-----------|------------|-------------|
| Accuracy | Medium - Inconsistent | 3 |
| Development Time | Very Fast - 1 week | 5 |
| Maintenance | Easy - Just prompts | 4 |
| Scalability | Poor - API costs | 1 |
| Scientific Value | Low - Not research contribution | 1 |

### 5.4 Pros & Cons

**Pros:**
- Very fast to implement
- No training needed
- Flexible prompting
- Good for prototyping

**Cons:**
- API costs ($$ per CV)
- Inconsistent outputs
- Not scientifically rigorous
- No control over model
- Privacy concerns (sending data to API)
- Not suitable for NCKH

### 5.5 Estimated Metrics

| Metric | Value |
|--------|-------|
| **F1-Score** | 60-70% (inconsistent) |
| **Development Time** | 1 week |
| **Training Data** | 0 (zero-shot) |
| **Compute Cost** | $0.01-0.10 per CV |
| **Monthly Cost (1000 CVs)** | $10-100 |

### 5.6 Why NOT Suitable

```
Reasons to reject Option D for this project:

1. Budget Constraint
   └── $0 budget, API costs money

2. Scientific Rigor
   └── "We used GPT-4" is not research contribution
   └── Cannot publish as novel work

3. Reproducibility
   └── LLM outputs vary
   └── Model may change over time

4. Control
   └── No fine-tuning possible
   └── Prompt engineering is trial-and-error

5. Privacy
   └── Sending CV data to external API
   └── May violate data agreement
```

---

## 6. Comparison Matrix

### 6.1 Overall Comparison

| Criterion | Option A | Option B | Option C | Option D |
|-----------|----------|----------|----------|----------|
| **F1-Score** | 40-50% | 55-65% | 75-85% | 60-70% |
| **Dev Time** | 2 weeks | 4 weeks | 6 weeks | 1 week |
| **Cost** | $0 | $0 | $0 | $10-100/mo |
| **Scientific Value** | Low | Medium | High | Low |
| **Maintainability** | Hard | Medium | Easy | Easy |
| **Scalability** | Poor | Medium | Good | Poor |
| **Data Needed** | 0 | 100+ | 200+ | 0 |

### 6.2 Weighted Scoring

| Criterion | Weight | A | B | C | D |
|-----------|--------|---|---|---|---|
| Accuracy | 30% | 2 | 3 | 5 | 3 |
| Scientific Value | 25% | 1 | 2 | 5 | 1 |
| Cost | 20% | 5 | 5 | 5 | 2 |
| Feasibility | 15% | 5 | 4 | 4 | 5 |
| Maintainability | 10% | 1 | 3 | 4 | 4 |
| **Weighted Total** | **100%** | **2.45** | **3.15** | **4.75** | **2.55** |

### 6.3 Decision

```
┌─────────────────────────────────────────────────────────────┐
│                    RECOMMENDATION                            │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│   ✅ OPTION C: BERT Fine-tuning                             │
│                                                              │
│   Score: 4.75/5.00 (Highest)                                │
│                                                              │
│   Reasons:                                                   │
│   1. Highest expected accuracy (75-85% F1)                  │
│   2. Strong scientific value for NCKH                       │
│   3. Zero cost with Google Colab                            │
│   4. Modern, publishable approach                           │
│   5. Good community support                                  │
│                                                              │
│   Backup: Option B (CRF) if BERT fails                      │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## 7. Implementation Roadmap for Option C

### 7.1 Phase 1: Data Preparation (Week 1-6)
```
1. Setup Label Studio
2. Create annotation guidelines
3. Train annotators
4. Annotate 200+ CVs
5. QC and export data
```

### 7.2 Phase 2: Model Development (Week 7-9)
```
1. Preprocess annotated data
2. Create train/val/test splits (70/15/15)
3. Implement BERT NER model
4. Train on Google Colab
5. Evaluate and iterate
```

### 7.3 Phase 3: Integration (Week 10-11)
```
1. Wrap model in FastAPI
2. Build React frontend
3. Integration testing
4. Demo preparation
```

### 7.4 Phase 4: Finalization (Week 12)
```
1. Final evaluation
2. Write NCKH report
3. Prepare presentation
4. Submit
```

---

*Document created as part of CV-NER Research Project documentation.*
