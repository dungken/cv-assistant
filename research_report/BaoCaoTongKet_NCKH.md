# BÁO CÁO TỔNG KẾT ĐỀ TÀI NGHIÊN CỨU KHOA HỌC

**BỘ GIAO THÔNG VẬN TẢI**
**TRƯỜNG ĐẠI HỌC GIAO THÔNG VẬN TẢI**
**PHÂN HIỆU TẠI THÀNH PHỐ HỒ CHÍ MINH**

---

**BÁO CÁO TỔNG KẾT**
**ĐỀ TÀI NGHIÊN CỨU KHOA HỌC CẤP TRƯỜNG (SINH VIÊN)**

## NGHIÊN CỨU VÀ ỨNG DỤNG XỬ LÝ NGÔN NGỮ TỰ NHIÊN TRONG PHÁT TRIỂN HỆ THỐNG AI TẠO LẬP CV THÔNG MINH VÀ TƯ VẤN CÁ NHÂN HÓA LỘ TRÌNH NGHỀ NGHIỆP

---

**Chủ nhiệm đề tài:** _(Họ và tên)_
**Đơn vị:** Phân hiệu Trường Đại học Giao thông Vận tải tại TP. Hồ Chí Minh (UTC2)
**Giáo viên hướng dẫn:** _(Họ và tên)_

**TP. Hồ Chí Minh, năm 2026**

---

## LỜI CAM ĐOAN

Tôi xin cam đoan đây là công trình nghiên cứu của nhóm tác giả, được thực hiện dưới sự hướng dẫn khoa học của giáo viên hướng dẫn. Các số liệu, kết quả trình bày trong báo cáo là trung thực và chưa từng được công bố trong bất kỳ công trình nào khác.

Dữ liệu sử dụng trong nghiên cứu là **dữ liệu synthetic được sinh bằng mô hình ngôn ngữ lớn (LLM) theo template có kiểm soát**, không phải dữ liệu thu thập từ người dùng thật, đảm bảo tuân thủ quyền riêng tư và không vi phạm điều khoản sử dụng của các nền tảng tuyển dụng.

Tôi xin chịu trách nhiệm hoàn toàn về nội dung báo cáo này.

_TP. Hồ Chí Minh, tháng 04 năm 2026_

**Chủ nhiệm đề tài**
_(Ký và ghi rõ họ tên)_

---

## LỜI CẢM ƠN

Nhóm nghiên cứu xin gửi lời cảm ơn chân thành đến:

- **Giáo viên hướng dẫn** đã định hướng và hỗ trợ xuyên suốt quá trình thực hiện đề tài.
- **Phân hiệu UTC2** đã tạo điều kiện về cơ sở vật chất và học thuật.
- **Cộng đồng mã nguồn mở** HuggingFace, spaCy, VinAI Research đã công bố các mô hình và công cụ NLP mà đề tài sử dụng.

### Khai báo sử dụng công cụ AI

Trong quá trình thực hiện đề tài, nhóm có sử dụng các công cụ trí tuệ nhân tạo hỗ trợ các công việc sau:

| Công cụ                    | Phiên bản      | Mục đích sử dụng                                        |
| -------------------------- | -------------- | ------------------------------------------------------- |
| ChatGPT / GPT-4            | 4o (2024–2025) | Hỗ trợ soạn thảo văn bản; sinh dữ liệu CV/JD synthetic |
| Claude                     | Sonnet 4.6     | Hỗ trợ thiết kế kiến trúc hệ thống; review code        |
| GitHub Copilot             | v1.x           | Gợi ý hoàn thành code trong quá trình phát triển        |
| Qwen2.5-1.5B-Instruct      | 1.5B           | Sinh 600 CV synthetic trên Google Colab                 |
| Qwen2.5:3b (Ollama Local)  | 3B             | Chatbot tư vấn nghề nghiệp chạy local trong hệ thống   |
| Llama-3.3-70b (Groq Cloud) | 70B            | Chatbot tư vấn nghề nghiệp chạy trên Groq Cloud API    |

Các nội dung do AI sinh ra đều đã được tác giả kiểm tra, chỉnh sửa và chịu trách nhiệm về tính chính xác. Các kết quả khoa học (metrics, phân tích, kết luận) đều do nhóm nghiên cứu tự thực hiện và xác minh.

---

## DANH MỤC BẢNG BIỂU

| Số hiệu   | Tên bảng                                             | Trang |
| --------- | ---------------------------------------------------- | ----- |
| Bảng 1.1  | Tổng quan các công trình liên quan về NER tiếng Việt |       |
| Bảng 1.2  | So sánh các framework NLP phổ biến                   |       |
| Bảng 1.3  | Các bộ ontology kỹ năng tiêu biểu                    |       |
| Bảng 2.1  | Đặc tả các microservice trong hệ thống               |       |
| Bảng 2.2  | Thống kê tập dữ liệu CV/JD synthetic                 |       |
| Bảng 2.3  | Phân bố nhãn thực thể trong tập huấn luyện           |       |
| Bảng 3.1  | Môi trường thực nghiệm                               |       |
| Bảng 3.2  | Kết quả NER trên silver labels (token-level)         |       |
| Bảng 3.3  | Kết quả NER — manual annotation                      |       |
| Bảng 3.4  | Kết quả NER định tính trên 12 CV thực tế             |       |
| Bảng 3.5  | Kết quả NER bán tự động trên 100 CV Groq             |       |
| Bảng 3.6  | Kết quả Skill Matching trên 10 test case             |       |
| Bảng 3.7  | Output NER trực quan trên 2 CV mẫu                   |       |

---

## DANH MỤC HÌNH

| Số hiệu   | Tên hình                                               | Trang |
| --------- | ------------------------------------------------------ | ----- |
| Hình 1.1  | Kiến trúc tổng quát mô hình BERT                       |       |
| Hình 1.2  | Quy trình fine-tuning PhoBERT cho NER                  |       |
| Hình 1.3  | Minh họa BIO tagging scheme                            |       |
| Hình 2.1  | Kiến trúc microservices của hệ thống CV Assistant      |       |
| Hình 2.2  | Pipeline sinh dữ liệu synthetic                        |       |
| Hình 2.3  | Quy trình huấn luyện mô hình NER                       |       |
| Hình 2.4  | Kiến trúc Skill Matching Service                       |       |
| Hình 3.1  | CV01 — Kết quả NER trên giao diện (trang 1)            |       |
| Hình 3.2  | CV01 — Kết quả NER trên giao diện (trang 2)            |       |
| Hình 3.3  | CV01 — Kết quả NER trên giao diện (trang 3)            |       |
| Hình 3.4  | CV01 — Kết quả NER trên giao diện (trang 4)            |       |
| Hình 3.5  | CV02 — Kết quả NER trên giao diện (trang 1)            |       |
| Hình 3.6  | CV02 — Kết quả NER trên giao diện (trang 2)            |       |
| Hình 3.7  | CV02 — Kết quả NER trên giao diện (trang 3)            |       |
| Hình 3.8  | CV03 — Kết quả NER trên giao diện (trang 1)            |       |
| Hình 3.9  | CV03 — Kết quả NER trên giao diện (trang 2)            |       |
| Hình 3.10 | CV03 — Kết quả NER trên giao diện (trang 3)            |       |
| Hình 3.11 | Giao diện upload CV (dropzone)                         |       |
| Hình 3.12 | Nhập JD để phân tích Skill Gap                         |       |
| Hình 3.13 | Kết quả Skill Matrix matching                          |       |
| Hình 3.14 | ATS Score breakdown 8 tiêu chí                         |       |
| Hình 3.15 | Chatbot RAG với Knowledge Graph (1)                    |       |
| Hình 3.16 | Chatbot RAG với Knowledge Graph (2)                    |       |
| Hình 3.17 | CV Builder bước 1 — thông tin header                   |       |
| Hình 3.18 | CV Builder bước 2 — thu thập thông tin                 |       |
| Hình 3.19 | CV Builder bước 3 — form nhập liệu                     |       |
| Hình 3.20 | Tổng quan giao diện hệ thống CV Assistant              |       |

---

## DANH MỤC CHỮ VIẾT TẮT

| Viết tắt | Giải thích                                                       |
| -------- | ---------------------------------------------------------------- |
| AI       | Artificial Intelligence (Trí tuệ nhân tạo)                       |
| API      | Application Programming Interface                                |
| ATS      | Applicant Tracking System                                        |
| BERT     | Bidirectional Encoder Representations from Transformers          |
| BIO      | Beginning – Inside – Outside (scheme gán nhãn chuỗi)             |
| CV       | Curriculum Vitae (Hồ sơ xin việc)                                |
| ESCO     | European Skills, Competencies, Qualifications and Occupations    |
| F1       | F1-Score (chỉ số đánh giá mô hình)                               |
| JD       | Job Description (Mô tả công việc)                                |
| JWT      | JSON Web Token                                                   |
| KG       | Knowledge Graph (Đồ thị tri thức)                                |
| LLM      | Large Language Model (Mô hình ngôn ngữ lớn)                      |
| mBERT    | Multilingual BERT                                                |
| NER      | Named Entity Recognition (Nhận diện thực thể có tên)             |
| NLP      | Natural Language Processing (Xử lý ngôn ngữ tự nhiên)            |
| NCKH     | Nghiên cứu khoa học                                              |
| O\*NET   | Occupational Information Network                                 |
| RAG      | Retrieval-Augmented Generation                                   |
| REST     | Representational State Transfer                                  |
| TP.HCM   | Thành phố Hồ Chí Minh                                            |
| UTC2     | Phân hiệu Trường Đại học Giao thông Vận tải tại TP. Hồ Chí Minh |

---

## MỤC LỤC

### Mở đầu

- [1. Lý do chọn đề tài](./mo_dau.md)
- [2. Mục tiêu nghiên cứu](./mo_dau.md)
- [3. Nội dung nghiên cứu](./mo_dau.md)
- [4. Phương pháp nghiên cứu](./mo_dau.md)
- [5. Đối tượng và phạm vi nghiên cứu](./mo_dau.md)
- [6. Ý nghĩa khoa học và thực tiễn](./mo_dau.md)
- [7. Bố cục báo cáo](./mo_dau.md)

### Chương 1: Tổng quan và Cơ sở lý thuyết

- [1.1 Các công trình liên quan](./chuong1/1.1_cong_trinh_lien_quan.md)
- [1.2 Nền tảng NLP và BERT](./chuong1/1.2_nen_tang_NLP_BERT.md)
- [1.3 NER và BIO tagging scheme](./chuong1/1.3_NER_BIO.md)
- [1.4 Skill Ontology và Matching](./chuong1/1.4_skill_ontology_matching.md)
- [1.5 RAG và LLM](./chuong1/1.5_RAG_LLM.md)
- [1.6 Microservices và Synthetic Data](./chuong1/1.6_microservices_synthetic_data.md)

### Chương 2: Thiết kế hệ thống

- [2.1 Kiến trúc tổng thể](./chuong2/2.1_kien_truc_tong_the.md)
- [2.2 Dữ liệu Synthetic](./chuong2/2.2_du_lieu_synthetic.md)
- [2.3 NER Service](./chuong2/2.3_ner_service.md)
- [2.4 Skill Matching Service](./chuong2/2.4_skill_matching_service.md)
- [2.5 Chatbot Service](./chuong2/2.5_chatbot_service.md)
- [2.6 API Gateway và Frontend](./chuong2/2.6_api_gateway_frontend.md)

### Chương 3: Thực nghiệm và Kết quả

- [3.1 Môi trường thực nghiệm](./chuong3/3.1_moi_truong_thuc_nghiem.md)
- [3.2 Kết quả NER](./chuong3/3.2_ket_qua_ner.md)
- [3.3 Kết quả Skill Matching](./chuong3/3.3_ket_qua_skill_matching.md)
- [3.4 Demo hệ thống](./chuong3/3.4_demo_he_thong.md)
- [3.5 Thảo luận và đánh giá tổng thể](./chuong3/3.5_thao_luan.md)

### Kết luận và Kiến nghị

- [Kết luận](./ket_luan.md)

### Tài liệu tham khảo

- [Tài liệu tham khảo](./tai_lieu_tham_khao.md)

---

## [MỞ ĐẦU](./mo_dau.md)

---
