# 01. Requirements Intake - Nhận Yêu Cầu

> **Document Version**: 1.0
> **Last Updated**: 2026-01-23
> **Status**: Approved
> **Related Documents**: [02_problem_understanding.md](./02_problem_understanding.md)

---

## 1. Thông Tin Đề Tài

### 1.1 Tên Đề Tài
**Nghiên cứu & Ứng dụng NLP trong phát triển hệ thống AI tạo lập CV thông minh và tư vấn cá nhân hóa lộ trình nghề nghiệp**

### 1.2 Thông Tin Cơ Bản

| Thuộc tính | Chi tiết |
|------------|----------|
| **Cấp độ** | NCKH sinh viên cấp trường |
| **Đơn vị** | Trường Đại học Giao thông Vận tải TP.HCM (UTC2) |
| **Khoa** | Công nghệ Thông tin |
| **Năm học** | 2025-2026 |
| **Nguồn yêu cầu** | Tự đề xuất, được GVHD phê duyệt |

### 1.3 Scope Focus
- **Core Feature (P0)**: Chatbot AI tư vấn CV và nghề nghiệp (LlamaIndex + Llama 3.2)
- **Core Feature (P0)**: Named Entity Recognition (NER) cho CV (10 entity types)
- **High Priority (P1)**: Skill Matching - So khớp kỹ năng CV với JD
- **High Priority (P1)**: Career Recommendation - Đề xuất lộ trình nghề nghiệp

---

## 2. Timeline Dự Án

| Mốc | Thời gian | Ghi chú |
|-----|-----------|---------|
| **Start Date** | 26/01/2026 | Bắt đầu chính thức |
| **End Date** | 19/04/2026 | Deadline nghiệm thu |
| **Duration** | 12 tuần | ~84 ngày |
| **Current Status** | Tuần 1 | Mới bắt đầu |

### 2.1 Major Milestones
```
Week 1-2:   Setup + Documentation + Knowledge Base
Week 3-6:   Data Annotation (200+ CVs)
Week 7-9:   NER Model Training + Chatbot Development
Week 10-11: Microservices Integration + Frontend
Week 12:    Testing + Final Report + Demo
```

---

## 3. Nguồn Yêu Cầu

### 3.1 Primary Stakeholder: Giảng Viên Hướng Dẫn
- **Vai trò**: Phê duyệt đề tài, hướng dẫn nghiên cứu
- **Trạng thái hiện tại**: Đã duyệt đề tài, chưa hướng dẫn chi tiết
- **Kỳ vọng**: Báo cáo NCKH chất lượng + Demo sản phẩm

### 3.2 Secondary Stakeholder: Hội Đồng NCKH Trường
- **Vai trò**: Nghiệm thu, chấm điểm
- **Tiêu chí đánh giá**: Theo quy định của nhà trường (cần xác nhận)

### 3.3 End Users (Đối tượng hưởng lợi)
- HR / Recruiters
- Job seekers
- Career consultants

---

## 4. Tài Liệu Requirements Hiện Có

### 4.1 Danh Sách Tài Liệu
Nhóm nghiên cứu tự biên soạn các tài liệu yêu cầu sau:

| File | Nội dung | Trạng thái |
|------|----------|------------|
| `requirement01.md` | Initial requirements | Draft |
| `requirement02.md` | Refined requirements | Draft |

### 4.2 Gaps Cần Bổ Sung
- [ ] Template báo cáo NCKH từ trường
- [ ] Tiêu chí đánh giá chi tiết từ GVHD
- [ ] Rubric chấm điểm từ Hội đồng

---

## 5. Team Structure

### 5.1 Team Composition

| Role | Số lượng | Nhiệm vụ chính |
|------|----------|----------------|
| **Leader** | 1 | Backend Java Dev + Learning AI/ML |
| **Annotator** | 4 | Data annotation + QA |

### 5.2 Chi Tiết Từng Thành Viên

| # | Vai trò | Skill Set | Responsibilities |
|---|---------|-----------|------------------|
| 1 | Leader | Java, Spring Boot, Learning Python/ML | Architecture, Training, Report, Coordination |
| 2 | Member | - | Data annotation, Quality Assurance |
| 3 | Member | - | Data annotation, Skill taxonomy building |
| 4 | Member | - | Data annotation |
| 5 | Member | - | Data annotation, Testing |

### 5.3 Workload Distribution
```
Leader:     Architecture (20%) + Training (30%) + Report (30%) + Coordination (20%)
Annotators: Annotation (80%) + QA/Testing (20%)
```

---

## 6. Data Resources

### 6.1 Data Source
| Thuộc tính | Chi tiết |
|------------|----------|
| **Nguồn** | UEH Job Portal (vieclam.ueh.edu.vn) |
| **Loại dữ liệu** | CV sinh viên/cựu sinh viên |
| **Số lượng raw** | 3,099 CVs |
| **Format** | PDF |
| **Ngôn ngữ** | Chủ yếu tiếng Anh |

### 6.2 Data Rights
- **Permission**: Có quyền sử dụng chính thức
- **Source Agreement**: Đã được UEH đồng ý
- **Usage Scope**: Nghiên cứu khoa học, không thương mại

### 6.3 Data Privacy Requirements
| Yêu cầu | Hành động |
|---------|-----------|
| Anonymization | Xóa tên, email, phone, địa chỉ cụ thể |
| PII Removal | Loại bỏ thông tin định danh cá nhân |
| Storage | Lưu trữ an toàn, không public |

### 6.4 Target Annotation
- **Target**: 200+ CVs được annotated
- **Annotation Format**: BIO tagging
- **Tool**: Label Studio

---

## 7. Technical Resources

### 7.1 Budget
| Item | Amount |
|------|--------|
| **Total Budget** | $0 |
| **Strategy** | Free tier only |

### 7.2 Training Environment
| Resource | Specification |
|----------|---------------|
| **Platform** | Google Colab |
| **GPU** | T4 (Free tier) |
| **Limitation** | Session timeout, queue wait |

### 7.3 Development Tools
| Purpose | Tool | Cost |
|---------|------|------|
| Annotation | Label Studio (self-hosted) | Free |
| Code | VS Code / PyCharm | Free |
| Version Control | GitHub | Free |
| Documentation | Markdown | Free |

---

## 8. Output Expectations

### 8.1 Primary Deliverables
| Deliverable | Format | Deadline |
|-------------|--------|----------|
| **Báo cáo NCKH** | Word/PDF theo template trường | Week 12 |
| **CV Assistant Web App** | Working prototype (React + Microservices) | Week 11 |
| **Source Code** | GitHub repository (monorepo) | Week 12 |
| **NER Model** | Hugging Face format (21 labels) | Week 10 |
| **Chatbot Service** | LlamaIndex + Ollama deployment | Week 10 |
| **Knowledge Base** | ChromaDB collections | Week 9 |
| **Annotated Dataset** | Label Studio export (CoNLL format) | Week 6 |
| **Docker Compose** | All services containerized | Week 11 |

### 8.2 Documentation Level
- **Level**: Chi tiết - Enterprise level
- **Reason**: Phục vụ báo cáo NCKH + reference sau này
- **Language**: Vietnamese + English (technical terms)

---

## 9. Questions & Clarifications Needed

### 9.1 Từ GVHD
- [ ] Tiêu chí đánh giá cụ thể cho đề tài?
- [ ] Frequency của buổi meeting hướng dẫn?
- [ ] Có template báo cáo NCKH không?

### 9.2 Từ Khoa/Trường
- [ ] Rubric chấm điểm NCKH?
- [ ] Thời gian bảo vệ dự kiến?
- [ ] Yêu cầu poster/presentation?

---

## 10. Approval & Sign-off

| Stakeholder | Status | Date | Notes |
|-------------|--------|------|-------|
| GVHD | ✅ Approved (Đề tài) | 01/2026 | Chờ hướng dẫn chi tiết |
| Team Leader | ✅ Committed | 26/01/2026 | - |
| Team Members | ✅ Committed | 26/01/2026 | - |

---

## Appendix A: Checklist Nhận Yêu Cầu

- [x] Tên đề tài rõ ràng
- [x] Scope xác định (NER + Skill Matching)
- [x] Timeline xác định (12 tuần)
- [x] Team đầy đủ (5 người)
- [x] Data source có sẵn (3,099 CVs)
- [x] Data rights confirmed
- [ ] GVHD criteria pending
- [ ] Report template pending

---

*Document created as part of CV-NER Research Project documentation.*
