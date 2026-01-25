# 05. Problem Decomposition - Chia Nhỏ Bài Toán

> **Document Version**: 2.0
> **Last Updated**: 2026-01-23
> **Status**: Approved
> **Product Name**: CV Assistant
> **Related Documents**: [04_requirements_classification.md](./04_requirements_classification.md), [06_solution_proposals.md](./06_solution_proposals.md)

---

## 1. System Overview

### 1.1 High-Level Module Breakdown

```
┌──────────────────────────────────────────────────────────────────────────────────────┐
│                               CV Assistant System                                      │
├──────────────┬──────────────┬──────────────┬───────────────┬────────────────────────┤
│ Data Module  │ NER Module   │ Matching     │ Career Module │ Chatbot Module (CORE)  │
├──────────────┼──────────────┼──────────────┼───────────────┼────────────────────────┤
│ • Crawler    │ • Preprocess │ • Taxonomy   │ • O*NET Data  │ • LlamaIndex Agent     │
│ • PDF Parser │ • Trainer    │ • Embedding  │ • Path Gen    │ • RAG Pipeline         │
│ • Anonymizer │ • Inference  │ • Scoring    │ • Roadmap     │ • Tool Calling         │
│ • Annotation │ • Evaluator  │              │               │ • Conversation Memory  │
└──────────────┴──────────────┴──────────────┴───────────────┴────────────────────────┘
                                      │
                                      ▼
                        ┌─────────────────────────────┐
                        │        Web App Module        │
                        │   (ChatGPT-style UI)         │
                        │ • Conversation Interface     │
                        │ • Results Display            │
                        │ • User Authentication        │
                        └─────────────────────────────┘
```

### 1.2 Module Responsibilities

| Module | Responsibility | Owner | Priority |
|--------|----------------|-------|----------|
| **Chatbot Module** | Conversational AI Core, RAG, Tool Calling | Leader | P0 (CORE) |
| **Data Module** | Thu thập, xử lý và chuẩn bị dữ liệu | Leader + Annotators | P0 |
| **NER Module** | Training và inference NER model | Leader | P0 |
| **Matching Module** | So khớp kỹ năng CV với JD | Leader | P1 |
| **Career Module** | Career path recommendation | Leader | P1 |
| **Web App Module** | ChatGPT-style UI | Leader | P1 |

---

## 2. Chatbot Module (P0 - CORE)

### 2.1 Sub-components

```
Chatbot Module (CORE)
├── 2.1.1 LlamaIndex Agent
│   ├── Input: User message + context
│   ├── Process: ReAct agent reasoning
│   └── Output: Structured response
│
├── 2.1.2 RAG Pipeline
│   ├── Input: Query
│   ├── Process: Vector search + retrieval
│   └── Output: Relevant context
│
├── 2.1.3 Tool Calling
│   ├── NER Tool
│   ├── Skill Matching Tool
│   └── Career Recommendation Tool
│
└── 2.1.4 Conversation Memory
    ├── Input: Conversation history
    ├── Storage: ChromaDB
    └── Output: Contextual responses
```

### 2.2 Chatbot Data Flow

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   User Query    │───▶│  LlamaIndex     │───▶│  Intent         │
│   (Natural      │    │  Agent          │    │  Detection      │
│   Language)     │    │                 │    │  (Auto)         │
└─────────────────┘    └─────────────────┘    └────────┬────────┘
                                                       │
                      ┌────────────────────────────────┼────────────────────┐
                      ▼                                ▼                    ▼
             ┌─────────────────┐           ┌─────────────────┐   ┌─────────────────┐
             │  RAG Retrieval  │           │  Tool Calling   │   │  Direct         │
             │  (Knowledge     │           │  (NER, Match,   │   │  Response       │
             │   Base Query)   │           │   Career)       │   │                 │
             └────────┬────────┘           └────────┬────────┘   └────────┬────────┘
                      │                             │                     │
                      └─────────────────────────────┼─────────────────────┘
                                                    │
                                                    ▼
                                           ┌─────────────────┐
                                           │  Response       │
                                           │  Synthesis      │
                                           │  (LLM)          │
                                           └────────┬────────┘
                                                    │
                                                    ▼
                                           ┌─────────────────┐
                                           │  Conversation   │
                                           │  Memory Update  │
                                           │  (ChromaDB)     │
                                           └────────┬────────┘
                                                    │
                                                    ▼
                                           ┌─────────────────┐
                                           │  User Response  │
                                           │  (ChatGPT-style)│
                                           └─────────────────┘
```

### 2.3 Component Details

#### 2.3.1 LlamaIndex Agent
```python
# Pseudo-code
class CVAssistantAgent:
    def __init__(self):
        self.llm = Ollama(model="llama3.2:3b")
        self.tools = [
            NERTool(),
            SkillMatchingTool(),
            CareerRecommendationTool()
        ]
        self.agent = ReActAgent.from_tools(
            tools=self.tools,
            llm=self.llm,
            verbose=True
        )

    def chat(self, user_message, conversation_history):
        """Process user message with context"""
        context = self.build_context(conversation_history)
        response = self.agent.chat(
            message=user_message,
            chat_history=context
        )
        return response

Technical Stack:
├── LLM: Llama 3.2 (3B) via Ollama
├── Framework: LlamaIndex
├── Agent Type: ReAct (Reasoning + Acting)
└── Hardware: CPU-only, 16GB RAM
```

#### 2.3.2 RAG Pipeline
```python
# Pseudo-code
class RAGPipeline:
    def __init__(self):
        self.vector_store = ChromaVectorStore(
            collection_name="cv_assistant_kb"
        )
        self.embed_model = HuggingFaceEmbedding(
            model_name="sentence-transformers/all-MiniLM-L6-v2"
        )

    def query(self, query_text, top_k=5):
        """Retrieve relevant context"""
        query_embedding = self.embed_model.embed(query_text)
        results = self.vector_store.query(
            embedding=query_embedding,
            top_k=top_k
        )
        return self.format_context(results)

Knowledge Base Sources:
├── O*NET Database (Jobs, Skills, Careers)
├── CV Writing Guides (Tips, Best Practices)
├── Job Market Info (Trends, Salary)
└── User's CV Data (Personalized)
```

#### 2.3.3 Tool Calling
```python
# Pseudo-code
class NERTool(BaseTool):
    name = "ner_extraction"
    description = "Extract information from CV text"

    def _run(self, cv_text: str) -> dict:
        # Call NER Service
        response = requests.post(
            "http://ner-service:5001/extract",
            json={"text": cv_text}
        )
        return response.json()

class SkillMatchingTool(BaseTool):
    name = "skill_matching"
    description = "Match CV skills with job description"

    def _run(self, cv_skills: list, jd_text: str) -> dict:
        # Call Skill Matching Service
        response = requests.post(
            "http://skill-service:5002/match",
            json={"cv_skills": cv_skills, "jd_text": jd_text}
        )
        return response.json()

class CareerRecommendationTool(BaseTool):
    name = "career_recommendation"
    description = "Generate career path recommendations"

    def _run(self, current_role: str, target_role: str) -> dict:
        # Call Career Service
        response = requests.post(
            "http://career-service:5003/recommend",
            json={"current": current_role, "target": target_role}
        )
        return response.json()
```

#### 2.3.4 Conversation Memory
```python
# Pseudo-code
class ConversationMemory:
    def __init__(self, user_id):
        self.user_id = user_id
        self.collection = chromadb.get_collection(
            name=f"conversations_{user_id}"
        )

    def add_message(self, role, content):
        """Store message in ChromaDB"""
        self.collection.add(
            documents=[content],
            metadatas=[{
                "role": role,
                "timestamp": datetime.now().isoformat(),
                "user_id": self.user_id
            }],
            ids=[str(uuid.uuid4())]
        )

    def get_history(self, limit=10):
        """Retrieve recent conversation history"""
        results = self.collection.query(
            query_texts=[""],
            n_results=limit
        )
        return self.format_history(results)

Storage:
├── Backend: ChromaDB
├── Persistence: Per user
├── Context: Conversation + CV data
└── Retention: Configurable
```

---

## 3. Data Module

### 3.1 Sub-components

```
Data Module
├── 3.1.1 Data Crawler
│   ├── Input: UEH portal access
│   ├── Process: Download PDFs
│   └── Output: Raw PDF files
│
├── 3.1.2 PDF Parser
│   ├── Input: Raw PDF files
│   ├── Process: Extract text
│   └── Output: Plain text
│
├── 3.1.3 Anonymizer
│   ├── Input: Plain text with PII
│   ├── Process: Remove/mask PII
│   └── Output: Anonymized text
│
└── 3.1.4 Annotation Pipeline
    ├── Input: Anonymized text
    ├── Process: Label entities
    └── Output: BIO-tagged data
```

### 3.2 Data Flow Diagram

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   UEH       │    │    Raw      │    │   Plain     │    │ Anonymized  │
│   Portal    │───▶│    PDFs     │───▶│   Text      │───▶│   Text      │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
                         │                  │                   │
                    [Crawler]          [Parser]           [Anonymizer]
                                                                │
                                                                ▼
                                                         ┌─────────────┐
                                                         │  Label      │
                                                         │  Studio     │
                                                         └──────┬──────┘
                                                                │
                                                                ▼
                                                         ┌─────────────┐
                                                         │  Annotated  │
                                                         │  Dataset    │
                                                         └─────────────┘
```

### 3.3 Component Details

#### 3.3.1 Data Crawler
```python
# Pseudo-code
class DataCrawler:
    def __init__(self, base_url, credentials):
        self.base_url = base_url
        self.session = create_session(credentials)

    def crawl(self, limit=None):
        """Download CV PDFs from portal"""
        cv_list = self.get_cv_list()
        for cv in cv_list[:limit]:
            pdf_content = self.download_cv(cv.id)
            self.save_pdf(pdf_content, f"cv_{cv.id}.pdf")

Input:  Portal URL, credentials
Output: Directory of PDF files
```

#### 3.3.2 PDF Parser
```python
# Pseudo-code
class PDFParser:
    def parse(self, pdf_path):
        """Extract text from PDF"""
        with pdfplumber.open(pdf_path) as pdf:
            text = ""
            for page in pdf.pages:
                text += page.extract_text() + "\n"
        return self.clean_text(text)

    def clean_text(self, text):
        """Remove noise from extracted text"""
        # Remove extra whitespace
        # Fix encoding issues
        # Normalize line breaks
        return cleaned_text

Input:  PDF file path
Output: Clean plain text
```

#### 3.3.3 Anonymizer
```python
# Pseudo-code
class Anonymizer:
    def anonymize(self, text):
        """Remove PII from text"""
        text = self.mask_emails(text)      # john@email.com → [EMAIL]
        text = self.mask_phones(text)      # +84 123 456 → [PHONE]
        text = self.mask_names(text)       # Manual/NER-based
        text = self.mask_addresses(text)   # Specific addresses
        return text

    def mask_emails(self, text):
        pattern = r'[\w\.-]+@[\w\.-]+\.\w+'
        return re.sub(pattern, '[EMAIL]', text)

Input:  Plain text with PII
Output: Anonymized text
```

#### 3.3.4 Annotation Pipeline
```
Label Studio Setup:
├── Project: CV-NER
├── Task type: Named Entity Recognition
├── Labels (10 types):
│   ├── PER (Person)
│   ├── ORG (Organization)
│   ├── DATE
│   ├── LOC (Location)
│   ├── SKILL
│   ├── DEGREE
│   ├── MAJOR
│   ├── JOB_TITLE
│   ├── PROJECT
│   └── CERT (Certification)
├── Interface: NER labeling
└── Export: CoNLL format

Workflow:
1. Import anonymized texts
2. Assign to annotators
3. Annotate entities
4. Review (IAA check)
5. Export to CoNLL
```

---

## 4. NER Module

### 4.1 Sub-components

```
NER Module
├── 4.1.1 Preprocessor
│   ├── Tokenization
│   ├── Alignment (tokens ↔ labels)
│   └── Dataset creation
│
├── 4.1.2 Model Trainer
│   ├── Model architecture
│   ├── Training loop
│   └── Checkpointing
│
├── 4.1.3 Inference Engine
│   ├── Load model
│   ├── Predict labels
│   └── Post-process
│
└── 4.1.4 Evaluator
    ├── Compute metrics
    ├── Error analysis
    └── Generate report
```

### 4.2 NER Data Flow

```
┌─────────────────┐
│ Annotated Data  │
│ (CoNLL format)  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐    ┌─────────────────┐
│  Preprocessor   │───▶│  Train/Val/Test │
│  (Tokenize)     │    │    Datasets     │
└─────────────────┘    └────────┬────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │  Model Trainer  │
                       │  (BERT + NER)   │
                       └────────┬────────┘
                                │
                    ┌───────────┴───────────┐
                    ▼                       ▼
           ┌─────────────────┐    ┌─────────────────┐
           │  Trained Model  │    │   Evaluation    │
           │   (checkpoint)  │    │    Metrics      │
           └────────┬────────┘    └─────────────────┘
                    │
                    ▼
           ┌─────────────────┐
           │ Inference Engine│
           │  (Production)   │
           └─────────────────┘
```

### 4.3 Component Details

#### 4.3.1 Preprocessor
```python
# Pseudo-code
class NERPreprocessor:
    def __init__(self, tokenizer_name='bert-base-uncased'):
        self.tokenizer = BertTokenizer.from_pretrained(tokenizer_name)
        self.label2id = {...}  # BIO labels to IDs

    def process(self, sentences, labels):
        """Convert sentences and labels to model input"""
        tokenized = self.tokenizer(
            sentences,
            padding=True,
            truncation=True,
            max_length=512,
            return_tensors='pt'
        )
        aligned_labels = self.align_labels(tokenized, labels)
        return tokenized, aligned_labels

    def align_labels(self, tokenized, labels):
        """Align BIO labels with subword tokens"""
        # Handle subword tokenization
        # -100 for special tokens (CLS, SEP, PAD)
        return aligned_labels

Input:  CoNLL format data
Output: PyTorch Dataset (input_ids, attention_mask, labels)
```

#### 4.3.2 Model Trainer
```python
# Pseudo-code
class NERTrainer:
    def __init__(self, model, train_data, val_data, config):
        self.model = model
        self.train_loader = DataLoader(train_data, ...)
        self.val_loader = DataLoader(val_data, ...)
        self.optimizer = AdamW(model.parameters(), lr=config.lr)
        self.scheduler = get_scheduler(...)

    def train(self, epochs):
        """Training loop"""
        for epoch in range(epochs):
            # Training
            self.model.train()
            for batch in self.train_loader:
                loss = self.model(**batch).loss
                loss.backward()
                self.optimizer.step()
                self.scheduler.step()
                self.optimizer.zero_grad()

            # Validation
            metrics = self.evaluate(self.val_loader)

            # Checkpoint
            self.save_checkpoint(epoch, metrics)

        return self.best_model

Training Config:
├── Learning rate: 2e-5
├── Batch size: 16
├── Epochs: 10
├── Warmup: 10%
└── Weight decay: 0.01
```

#### 4.3.3 Inference Engine
```python
# Pseudo-code
class NERInference:
    def __init__(self, model_path):
        self.model = load_model(model_path)
        self.tokenizer = load_tokenizer(model_path)
        self.id2label = {...}  # IDs to BIO labels

    def predict(self, text):
        """Predict entities in text"""
        # Tokenize
        inputs = self.tokenizer(text, return_tensors='pt')

        # Predict
        with torch.no_grad():
            outputs = self.model(**inputs)
            predictions = torch.argmax(outputs.logits, dim=-1)

        # Convert to entities
        entities = self.labels_to_entities(predictions, text)
        return entities

    def labels_to_entities(self, predictions, text):
        """Convert BIO labels to entity spans"""
        entities = []
        current_entity = None
        for idx, label_id in enumerate(predictions[0]):
            label = self.id2label[label_id.item()]
            if label.startswith('B-'):
                # Start new entity
                ...
            elif label.startswith('I-'):
                # Continue entity
                ...
            else:
                # End entity
                ...
        return entities

Output format:
[
  {"text": "Google", "type": "ORG", "start": 10, "end": 16},
  {"text": "Software Engineer", "type": "JOB_TITLE", "start": 20, "end": 37}
]
```

#### 4.3.4 Evaluator
```python
# Pseudo-code
class NERValidator:
    def evaluate(self, predictions, ground_truth):
        """Compute NER metrics"""
        metrics = {
            'precision': ...,
            'recall': ...,
            'f1': ...,
            'per_entity': {
                'PER': {'precision': ..., 'recall': ..., 'f1': ...},
                'ORG': {...},
                # ...
            }
        }
        return metrics

    def error_analysis(self, predictions, ground_truth):
        """Analyze common errors"""
        errors = {
            'false_positives': [...],
            'false_negatives': [...],
            'wrong_type': [...],
            'boundary_errors': [...]
        }
        return errors

Metrics:
├── Overall F1
├── Per-entity F1
├── Confusion matrix
└── Error breakdown
```

---

## 5. Matching Module

### 5.1 Sub-components

```
Matching Module
├── 5.1.1 Skill Taxonomy
│   ├── Technical skills hierarchy (O*NET)
│   ├── Soft skills list
│   └── Synonyms mapping
│
├── 5.1.2 Embedding Generator
│   ├── Sentence-BERT encoder
│   └── Skill embeddings cache
│
└── 5.1.3 Scorer
    ├── Exact matching
    ├── Semantic matching
    └── Score calculation
```

### 5.2 Matching Data Flow

```
┌─────────────────┐                    ┌─────────────────┐
│   CV Skills     │                    │   JD Skills     │
│   (from NER)    │                    │   (extracted)   │
└────────┬────────┘                    └────────┬────────┘
         │                                      │
         ▼                                      ▼
┌─────────────────┐                    ┌─────────────────┐
│    Normalize    │                    │    Normalize    │
│    (lowercase,  │                    │    (lowercase,  │
│     synonyms)   │                    │     synonyms)   │
└────────┬────────┘                    └────────┬────────┘
         │                                      │
         └──────────────┬───────────────────────┘
                        │
                        ▼
               ┌─────────────────┐
               │  Skill Matcher  │
               │  (Exact + SBERT)│
               └────────┬────────┘
                        │
                        ▼
               ┌─────────────────┐
               │   Match Score   │
               │    (0-100%)     │
               └─────────────────┘
```

### 5.3 Component Details

#### 5.3.1 Skill Taxonomy
```yaml
# skill_taxonomy.yaml
technical_skills:
  programming_languages:
    - python
    - java
    - javascript
    - c++
    synonyms:
      js: javascript
      py: python
      cpp: c++

  frameworks:
    - react
    - angular
    - vue
    - django
    - spring

  databases:
    - mysql
    - postgresql
    - mongodb
    synonyms:
      postgres: postgresql
      mongo: mongodb

soft_skills:
  - leadership
  - communication
  - teamwork
  - problem-solving
  synonyms:
    team player: teamwork
    problem solving: problem-solving

language_skills:
  - english
  - vietnamese
  - chinese
  - japanese
```

#### 5.3.2 Embedding Generator
```python
# Pseudo-code
class SkillEmbedder:
    def __init__(self):
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        self.cache = {}

    def embed(self, skill):
        """Get embedding for a skill"""
        if skill not in self.cache:
            self.cache[skill] = self.model.encode(skill)
        return self.cache[skill]

    def embed_batch(self, skills):
        """Get embeddings for multiple skills"""
        return self.model.encode(skills)

Output: 384-dimensional vectors (MiniLM)
```

#### 5.3.3 Scorer
```python
# Pseudo-code
class SkillMatcher:
    def __init__(self, taxonomy, embedder):
        self.taxonomy = taxonomy
        self.embedder = embedder
        self.threshold = 0.7  # Semantic match threshold

    def match(self, cv_skills, jd_skills):
        """Match CV skills with JD requirements"""
        results = {
            'exact_matches': [],
            'semantic_matches': [],
            'unmatched_jd': [],
            'unmatched_cv': []
        }

        # Normalize skills
        cv_normalized = [self.normalize(s) for s in cv_skills]
        jd_normalized = [self.normalize(s) for s in jd_skills]

        # Exact matching
        for jd_skill in jd_normalized:
            if jd_skill in cv_normalized:
                results['exact_matches'].append(jd_skill)
                jd_normalized.remove(jd_skill)
                cv_normalized.remove(jd_skill)

        # Semantic matching for remaining
        if jd_normalized and cv_normalized:
            cv_embeddings = self.embedder.embed_batch(cv_normalized)
            jd_embeddings = self.embedder.embed_batch(jd_normalized)

            # Compute cosine similarity
            similarities = cosine_similarity(cv_embeddings, jd_embeddings)

            for i, jd_skill in enumerate(jd_normalized):
                best_match_idx = similarities[:, i].argmax()
                best_similarity = similarities[best_match_idx, i]

                if best_similarity >= self.threshold:
                    results['semantic_matches'].append({
                        'cv_skill': cv_normalized[best_match_idx],
                        'jd_skill': jd_skill,
                        'similarity': float(best_similarity)
                    })

        return results

    def calculate_score(self, match_results, total_jd_skills):
        """Calculate overall match score"""
        exact_score = len(match_results['exact_matches']) * 1.0
        semantic_score = sum(m['similarity'] for m in match_results['semantic_matches'])
        total_score = (exact_score + semantic_score) / total_jd_skills * 100
        return min(total_score, 100)

Output:
{
  "exact_matches": ["python", "sql"],
  "semantic_matches": [
    {"cv_skill": "machine learning", "jd_skill": "deep learning", "similarity": 0.85}
  ],
  "score": 72.5
}
```

---

## 6. Career Recommendation Module

### 6.1 Sub-components

```
Career Module
├── 6.1.1 O*NET Data Loader
│   ├── Jobs database
│   ├── Skills database
│   └── Career relationships
│
├── 6.1.2 Path Generator
│   ├── Current role analysis
│   ├── Target role mapping
│   └── Gap analysis
│
└── 6.1.3 Roadmap Builder
    ├── Conservative path
    ├── Moderate path
    └── Ambitious path
```

### 6.2 Career Path Data Flow

```
┌─────────────────┐    ┌─────────────────┐
│  Current Role   │    │  Target Role    │
│  (from CV/User) │    │  (User input)   │
└────────┬────────┘    └────────┬────────┘
         │                      │
         └──────────┬───────────┘
                    │
                    ▼
           ┌─────────────────┐
           │  O*NET Database │
           │  (Jobs, Skills) │
           └────────┬────────┘
                    │
                    ▼
           ┌─────────────────┐
           │  Gap Analysis   │
           │  (Missing Skills│
           │   & Experience) │
           └────────┬────────┘
                    │
        ┌───────────┼───────────┐
        ▼           ▼           ▼
┌──────────┐ ┌──────────┐ ┌──────────┐
│Conserva- │ │ Moderate │ │Ambitious │
│   tive   │ │   Path   │ │   Path   │
│  Path    │ │          │ │          │
└────┬─────┘ └────┬─────┘ └────┬─────┘
     │            │            │
     └────────────┼────────────┘
                  │
                  ▼
         ┌─────────────────┐
         │  Roadmap JSON   │
         │  (Steps, Skills,│
         │   Timeframes)   │
         └─────────────────┘
```

### 6.3 Roadmap Output Structure

```json
{
  "current_role": "Junior Developer",
  "target_role": "Tech Lead",
  "paths": [
    {
      "type": "conservative",
      "total_time": "6-8 years",
      "steps": [
        {
          "step": 1,
          "target_role": "Mid-level Developer",
          "timeframe": "2-3 years",
          "skills_to_learn": ["System Design", "CI/CD"],
          "certifications": ["AWS Solutions Architect"],
          "experience_needed": "Lead small projects"
        },
        {
          "step": 2,
          "target_role": "Senior Developer",
          "timeframe": "2-3 years",
          "skills_to_learn": ["Architecture", "Mentoring"],
          "certifications": [],
          "experience_needed": "Lead team of 3-5"
        },
        {
          "step": 3,
          "target_role": "Tech Lead",
          "timeframe": "1-2 years",
          "skills_to_learn": ["Strategic Planning", "Stakeholder Management"],
          "certifications": [],
          "experience_needed": "Lead cross-functional projects"
        }
      ]
    }
  ]
}
```

---

## 7. Web App Module

### 7.1 Sub-components

```
Web App Module (ChatGPT-style)
├── 7.1.1 Frontend (React 18)
│   ├── Conversation Interface
│   ├── Message Components
│   ├── Sidebar (Threads)
│   ├── Results Display
│   └── User Auth
│
└── 7.1.2 API Gateway (Spring Boot)
    ├── Auth Endpoints
    ├── Chat Endpoints
    ├── User Management
    └── Request Routing
```

### 7.2 API Endpoints

```
API Gateway (Spring Boot :8080):
├── POST /api/auth/register
│   ├── Input: { email, password, name }
│   └── Output: { user_id, token }
│
├── POST /api/auth/login
│   ├── Input: { email, password }
│   └── Output: { token, user }
│
├── POST /api/chat
│   ├── Input: { message, thread_id? }
│   └── Output: { response, thread_id }
│
├── GET /api/threads
│   └── Output: [{ thread_id, title, created_at }]
│
├── GET /api/threads/{thread_id}
│   └── Output: { messages: [...] }
│
├── POST /api/upload
│   ├── Input: PDF file
│   └── Output: { cv_id, extracted_data }
│
└── GET /api/health
    └── Output: { status: "ok" }
```

### 7.3 Frontend Pages

```
Pages (ChatGPT-style UI):
├── / (Landing/Login)
│   ├── Login form
│   └── Register link
│
├── /chat (Main)
│   ├── Sidebar: Thread list
│   ├── Main: Conversation view
│   ├── Input: Message composer
│   └── Loading: Typing indicator
│
├── /chat/{thread_id}
│   ├── Load thread history
│   └── Continue conversation
│
└── /profile
    ├── User settings
    └── Uploaded CVs
```

---

## 8. Complete Data Flow

### 8.1 Chatbot-First Pipeline

```
[User sends message]
        │
        ▼
┌───────────────────┐
│  Frontend         │
│  (React Chat UI)  │
└─────────┬─────────┘
          │ POST /api/chat
          ▼
┌───────────────────┐
│  API Gateway      │
│  (Spring Boot)    │
└─────────┬─────────┘
          │ JWT validation
          ▼
┌───────────────────┐
│  Chatbot Service  │
│  (LlamaIndex)     │
└─────────┬─────────┘
          │
    ┌─────┴─────┬─────────────┬──────────────┐
    ▼           ▼             ▼              ▼
┌────────┐ ┌────────┐   ┌────────┐    ┌────────┐
│  RAG   │ │  NER   │   │ Skill  │    │ Career │
│Retrieval│ │Service │   │ Match  │    │ Recom  │
│(Chroma)│ │ :5001  │   │ :5002  │    │ :5003  │
└────────┘ └────────┘   └────────┘    └────────┘
    │           │             │              │
    └───────────┴─────────────┴──────────────┘
                        │
                        ▼
               ┌───────────────────┐
               │  LLM Response     │
               │  Synthesis        │
               │  (Llama 3.2)      │
               └─────────┬─────────┘
                         │
                         ▼
               ┌───────────────────┐
               │  Conversation     │
               │  Memory Update    │
               │  (ChromaDB)       │
               └─────────┬─────────┘
                         │
                         ▼
               [Display response to user]
```

### 8.2 Input/Output Summary

| Module | Input | Output |
|--------|-------|--------|
| Data Crawler | Portal access | PDF files |
| PDF Parser | PDF file | Plain text |
| Anonymizer | Plain text | Anonymized text |
| Annotation | Anonymized text | BIO-tagged data |
| Preprocessor | BIO data | PyTorch Dataset |
| Trainer | Dataset | Trained model |
| NER Service | Text | Entity list |
| Skill Matcher | Entities + JD | Match score |
| Career Service | Current + Target role | Career paths |
| Chatbot Service | User message | AI response |
| API Gateway | HTTP requests | Routed requests |
| Web Frontend | User actions | API calls |

---

## 9. Module Interaction Matrix

|  | Chatbot | Data | NER | Matching | Career | Web |
|--|---------|------|-----|----------|--------|-----|
| **Chatbot** | - | - | Calls | Calls | Calls | Called by |
| **Data** | - | - | Provides | - | - | - |
| **NER** | Tool | Uses data | - | Provides | - | - |
| **Matching** | Tool | - | Uses entities | - | - | - |
| **Career** | Tool | - | - | - | - | - |
| **Web** | Calls | - | - | - | - | - |

---

## 10. Development Priority

```
Phase 1 (Critical Path - Week 1-6):
├── Data Module
│   └── Annotation is bottleneck (200+ CVs)
└── Chatbot Infrastructure
    └── LlamaIndex + Ollama setup

Phase 2 (Parallel - Week 6-9):
├── NER Module
│   └── Model training with annotated data
├── RAG Knowledge Base
│   └── O*NET + CV Guides ingestion
└── Chatbot Integration
    └── Tool calling setup

Phase 3 (Services - Week 9-11):
├── Skill Matching Service
├── Career Recommendation Service
└── API Gateway (Spring Boot)

Phase 4 (Integration - Week 11-12):
├── Frontend (ChatGPT-style)
├── Full pipeline testing
└── Demo preparation
```

---

*Document created as part of CV Assistant Research Project documentation.*
