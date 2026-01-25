# 25. Glossary - Thuật Ngữ

> **Document Version**: 1.0
> **Last Updated**: 2026-01-24
> **Status**: Approved
> **Product Name**: CV Assistant
> **Related Documents**: All project documents

---

## A

### Accuracy
**Vietnamese**: Độ chính xác
**Definition**: Tỷ lệ dự đoán đúng trên tổng số dự đoán trong machine learning.
**Formula**: `Accuracy = (TP + TN) / (TP + TN + FP + FN)`

### ADR (Architecture Decision Record)
**Vietnamese**: Bản ghi quyết định kiến trúc
**Definition**: Tài liệu ghi lại các quyết định quan trọng về kiến trúc hệ thống, bao gồm context, decision, và consequences.

### Agent (AI Agent)
**Vietnamese**: Tác tử AI
**Definition**: Hệ thống AI có khả năng tự động đưa ra quyết định và thực hiện actions để đạt được mục tiêu.

### Annotation
**Vietnamese**: Gán nhãn dữ liệu
**Definition**: Quá trình thêm labels/tags vào dữ liệu thô để tạo training data cho ML models.

### API (Application Programming Interface)
**Vietnamese**: Giao diện lập trình ứng dụng
**Definition**: Tập hợp các quy tắc và giao thức cho phép các ứng dụng giao tiếp với nhau.

### API Gateway
**Vietnamese**: Cổng API
**Definition**: Service đóng vai trò điểm vào duy nhất cho các microservices, xử lý authentication, routing, rate limiting.

---

## B

### BERT (Bidirectional Encoder Representations from Transformers)
**Vietnamese**: -
**Definition**: Pre-trained language model của Google, học ngữ cảnh hai chiều, được sử dụng làm nền tảng cho nhiều NLP tasks.

### BIO Tagging
**Vietnamese**: Gán nhãn BIO
**Definition**: Định dạng gán nhãn cho NER với B (Begin), I (Inside), O (Outside) để đánh dấu ranh giới entities.
**Example**: `B-PER I-PER O B-ORG` = "John Smith works at Google"

### Batch Size
**Vietnamese**: Kích thước batch
**Definition**: Số lượng training samples được xử lý cùng lúc trước khi cập nhật model weights.

---

## C

### Chatbot
**Vietnamese**: Robot trò chuyện
**Definition**: Chương trình AI có khả năng hội thoại với người dùng bằng ngôn ngữ tự nhiên.

### ChromaDB
**Vietnamese**: -
**Definition**: Vector database mã nguồn mở, lưu trữ và truy vấn embeddings cho RAG applications.

### Chunk
**Vietnamese**: Phân đoạn
**Definition**: Đoạn text được chia nhỏ từ tài liệu lớn để indexing và retrieval trong RAG systems.

### CoNLL Format
**Vietnamese**: Định dạng CoNLL
**Definition**: Định dạng dữ liệu cho NER với mỗi token trên một dòng, cột phân tách bằng tab/space.
**Example**:
```
John    B-PER
Smith   I-PER
works   O
at      O
Google  B-ORG
```

### Cosine Similarity
**Vietnamese**: Độ tương tự cosine
**Definition**: Thước đo độ tương tự giữa hai vectors, tính bằng cosine của góc giữa chúng. Range: [-1, 1].

### CORS (Cross-Origin Resource Sharing)
**Vietnamese**: Chia sẻ tài nguyên cross-origin
**Definition**: Cơ chế bảo mật cho phép/chặn requests từ different origins (domains).

### CV (Curriculum Vitae)
**Vietnamese**: Sơ yếu lý lịch
**Definition**: Tài liệu tóm tắt thông tin cá nhân, kinh nghiệm làm việc, học vấn, kỹ năng của ứng viên.

---

## D

### Docker
**Vietnamese**: -
**Definition**: Platform để containerize applications, đảm bảo consistency giữa các môi trường.

### Docker Compose
**Vietnamese**: -
**Definition**: Tool để define và run multi-container Docker applications với file YAML.

---

## E

### Embedding
**Vietnamese**: Vector nhúng
**Definition**: Biểu diễn số (vector) của text/data trong không gian nhiều chiều, capture semantic meaning.

### Entity
**Vietnamese**: Thực thể
**Definition**: Đối tượng được đặt tên trong text như người, tổ chức, địa điểm, ngày tháng.

### Epoch
**Vietnamese**: -
**Definition**: Một lần duyệt qua toàn bộ training dataset trong quá trình training.

---

## F

### F1 Score
**Vietnamese**: Điểm F1
**Definition**: Harmonic mean của Precision và Recall, metric chính cho NER evaluation.
**Formula**: `F1 = 2 * (Precision * Recall) / (Precision + Recall)`

### FastAPI
**Vietnamese**: -
**Definition**: Modern Python web framework cho building APIs với automatic documentation.

### Fine-tuning
**Vietnamese**: Tinh chỉnh
**Definition**: Quá trình train thêm pre-trained model trên domain-specific data.

---

## G

### GPU (Graphics Processing Unit)
**Vietnamese**: Bộ xử lý đồ họa
**Definition**: Phần cứng chuyên dụng cho parallel processing, essential cho deep learning training.

---

## H

### Hugging Face
**Vietnamese**: -
**Definition**: Platform và thư viện cho NLP, cung cấp pre-trained models và Transformers library.

---

## I

### IAA (Inter-Annotator Agreement)
**Vietnamese**: Độ đồng thuận giữa annotators
**Definition**: Thước đo mức độ nhất quán giữa các annotators khi gán nhãn cùng dữ liệu.
**Metric**: Cohen's Kappa, Fleiss' Kappa

### Inference
**Vietnamese**: Suy luận
**Definition**: Quá trình sử dụng trained model để dự đoán trên new/unseen data.

---

## J

### JWT (JSON Web Token)
**Vietnamese**: -
**Definition**: Standard để truyền thông tin xác thực giữa client và server một cách an toàn.

### JD (Job Description)
**Vietnamese**: Mô tả công việc
**Definition**: Tài liệu mô tả yêu cầu, trách nhiệm, và kỹ năng cần thiết cho một vị trí công việc.

---

## K

### Knowledge Base
**Vietnamese**: Cơ sở tri thức
**Definition**: Tập hợp thông tin có cấu trúc được sử dụng để cung cấp context cho AI systems.

---

## L

### Label Studio
**Vietnamese**: -
**Definition**: Open-source tool cho data annotation, hỗ trợ nhiều task types bao gồm NER.

### Learning Rate
**Vietnamese**: Tốc độ học
**Definition**: Hyperparameter kiểm soát kích thước bước khi cập nhật weights trong training.

### LLM (Large Language Model)
**Vietnamese**: Mô hình ngôn ngữ lớn
**Definition**: Neural network models với billions of parameters, được train trên massive text data.
**Examples**: GPT-4, Claude, Llama

### LlamaIndex
**Vietnamese**: -
**Definition**: Framework cho building LLM applications với data indexing và retrieval capabilities.

---

## M

### Microservices
**Vietnamese**: Vi dịch vụ
**Definition**: Architecture style chia ứng dụng thành các services nhỏ, độc lập, dễ scale và maintain.

### MiniLM
**Vietnamese**: -
**Definition**: Compact version của BERT, smaller và faster, thường dùng cho embedding generation.
**Model used**: `all-MiniLM-L6-v2` (384 dimensions)

---

## N

### NER (Named Entity Recognition)
**Vietnamese**: Nhận dạng thực thể có tên
**Definition**: NLP task xác định và phân loại entities (người, tổ chức, địa điểm...) trong text.

### NLP (Natural Language Processing)
**Vietnamese**: Xử lý ngôn ngữ tự nhiên
**Definition**: Lĩnh vực AI xử lý tương tác giữa máy tính và ngôn ngữ con người.

---

## O

### Ollama
**Vietnamese**: -
**Definition**: Tool để chạy LLMs locally, hỗ trợ nhiều models như Llama, Mistral.

### O*NET
**Vietnamese**: -
**Definition**: Occupational Information Network - cơ sở dữ liệu về jobs, skills, career paths của U.S. Department of Labor.

### Overfitting
**Vietnamese**: Quá khớp
**Definition**: Khi model học quá tốt trên training data nhưng generalize kém trên new data.

---

## P

### PDF (Portable Document Format)
**Vietnamese**: -
**Definition**: Format file document phổ biến, được sử dụng cho CVs trong project này.

### PII (Personally Identifiable Information)
**Vietnamese**: Thông tin định danh cá nhân
**Definition**: Thông tin có thể xác định một cá nhân: tên, email, số điện thoại, địa chỉ.

### PostgreSQL
**Vietnamese**: -
**Definition**: Open-source relational database, được sử dụng để lưu user data, threads, CVs.

### Precision
**Vietnamese**: Độ chính xác
**Definition**: Tỷ lệ dự đoán đúng trong tổng số positive predictions.
**Formula**: `Precision = TP / (TP + FP)`

### Pre-training
**Vietnamese**: Huấn luyện trước
**Definition**: Quá trình train model trên large, general dataset trước khi fine-tuning.

---

## Q

### QC (Quality Control)
**Vietnamese**: Kiểm soát chất lượng
**Definition**: Quy trình đảm bảo chất lượng annotation data và model outputs.

---

## R

### RAG (Retrieval-Augmented Generation)
**Vietnamese**: Sinh văn bản tăng cường bằng truy xuất
**Definition**: Technique kết hợp retrieval từ knowledge base với LLM generation để improve accuracy.

### React (Framework)
**Vietnamese**: -
**Definition**: JavaScript library cho building user interfaces, được sử dụng cho frontend.

### ReAct (Reasoning + Acting)
**Vietnamese**: -
**Definition**: Agent pattern kết hợp reasoning và action-taking, cho phép LLM suy luận và sử dụng tools.

### Recall
**Vietnamese**: Độ thu hồi
**Definition**: Tỷ lệ positive cases được detect đúng trong tổng số actual positives.
**Formula**: `Recall = TP / (TP + FN)`

### REST API
**Vietnamese**: -
**Definition**: Architectural style cho APIs sử dụng HTTP methods (GET, POST, PUT, DELETE).

---

## S

### Semantic Matching
**Vietnamese**: So khớp ngữ nghĩa
**Definition**: So khớp dựa trên meaning thay vì exact text matching, sử dụng embeddings.

### Sentence-BERT (SBERT)
**Vietnamese**: -
**Definition**: BERT modification cho sentence embeddings, efficient semantic similarity.

### Spring Boot
**Vietnamese**: -
**Definition**: Java framework cho building production-ready applications, được sử dụng cho API Gateway.

---

## T

### Token
**Vietnamese**: -
**Definition**: Đơn vị text nhỏ nhất (word, subword, character) được xử lý bởi NLP model.

### Tokenization
**Vietnamese**: Tách từ
**Definition**: Quá trình chia text thành tokens.

### Tool Calling
**Vietnamese**: Gọi công cụ
**Definition**: Khả năng của LLM agent gọi external functions/APIs để thực hiện tasks.

### Transformer
**Vietnamese**: -
**Definition**: Neural network architecture dựa trên attention mechanism, nền tảng của BERT, GPT.

---

## U

### Underfitting
**Vietnamese**: Chưa khớp đủ
**Definition**: Khi model không học đủ patterns từ training data, performance kém.

---

## V

### Validation Set
**Vietnamese**: Tập validation
**Definition**: Subset của data dùng để đánh giá model trong quá trình training, tuning hyperparameters.

### Vector Store
**Vietnamese**: Kho vector
**Definition**: Database chuyên dụng lưu trữ và truy vấn embedding vectors.
**Examples**: ChromaDB, Pinecone, FAISS

---

## W

### Warmup
**Vietnamese**: Khởi động
**Definition**: Giai đoạn đầu training với learning rate thấp, dần tăng lên để ổn định training.

### Weight Decay
**Vietnamese**: Suy giảm trọng số
**Definition**: Regularization technique giảm weights để prevent overfitting.

---

## Entity Types in CV Assistant

### 10 Entity Types (21 BIO Labels)

| Entity | Vietnamese | Example | BIO Labels |
|--------|------------|---------|------------|
| **PER** | Người | "John Smith" | B-PER, I-PER |
| **ORG** | Tổ chức | "Google Inc" | B-ORG, I-ORG |
| **DATE** | Ngày tháng | "2023-2024", "March 2021" | B-DATE, I-DATE |
| **LOC** | Địa điểm | "Ho Chi Minh City" | B-LOC, I-LOC |
| **SKILL** | Kỹ năng | "Python", "Machine Learning" | B-SKILL, I-SKILL |
| **DEGREE** | Bằng cấp | "Bachelor of Science" | B-DEGREE, I-DEGREE |
| **MAJOR** | Chuyên ngành | "Computer Science" | B-MAJOR, I-MAJOR |
| **JOB_TITLE** | Chức danh | "Software Engineer" | B-JOB_TITLE, I-JOB_TITLE |
| **PROJECT** | Dự án | "E-commerce Platform" | B-PROJECT, I-PROJECT |
| **CERT** | Chứng chỉ | "AWS Solutions Architect" | B-CERT, I-CERT |
| **O** | Bên ngoài | (không thuộc entity nào) | O |

---

## Abbreviations

| Abbreviation | Full Form | Vietnamese |
|--------------|-----------|------------|
| AI | Artificial Intelligence | Trí tuệ nhân tạo |
| API | Application Programming Interface | Giao diện lập trình ứng dụng |
| CV | Curriculum Vitae | Sơ yếu lý lịch |
| DoD | Definition of Done | Định nghĩa hoàn thành |
| GVHD | Giảng Viên Hướng Dẫn | Research Advisor |
| IAA | Inter-Annotator Agreement | Độ đồng thuận annotator |
| JD | Job Description | Mô tả công việc |
| JWT | JSON Web Token | - |
| KB | Knowledge Base | Cơ sở tri thức |
| LLM | Large Language Model | Mô hình ngôn ngữ lớn |
| ML | Machine Learning | Học máy |
| NER | Named Entity Recognition | Nhận dạng thực thể |
| NLP | Natural Language Processing | Xử lý ngôn ngữ tự nhiên |
| NCKH | Nghiên Cứu Khoa Học | Scientific Research |
| PII | Personally Identifiable Information | Thông tin cá nhân |
| QC | Quality Control | Kiểm soát chất lượng |
| RAG | Retrieval-Augmented Generation | Sinh văn bản tăng cường |

---

## Technology Stack Quick Reference

| Component | Technology | Purpose |
|-----------|------------|---------|
| Frontend | React 18 + Ant Design | ChatGPT-style UI |
| API Gateway | Spring Boot 3 | Auth, routing, JWT |
| NER Service | FastAPI + PyTorch | Entity extraction |
| Skill Service | FastAPI + Sentence-BERT | Skill matching |
| Career Service | FastAPI | Career recommendations |
| Chatbot | LlamaIndex + Ollama | Conversational AI |
| LLM | Llama 3.2 (3B) | Language generation |
| Vector Store | ChromaDB | Knowledge base |
| Database | PostgreSQL | User data, threads |
| Annotation | Label Studio | Data labeling |
| Deployment | Docker Compose | Containerization |

---

*Document created as part of CV Assistant Research Project documentation.*
