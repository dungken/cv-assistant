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

- [1. Lý do chọn đề tài](#mở-đầu)
- [2. Mục tiêu nghiên cứu](#mở-đầu)
- [3. Nội dung nghiên cứu](#mở-đầu)
- [4. Phương pháp nghiên cứu](#mở-đầu)
- [5. Đối tượng và phạm vi nghiên cứu](#mở-đầu)
- [6. Ý nghĩa khoa học và thực tiễn](#mở-đầu)
- [7. Bố cục báo cáo](#mở-đầu)

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

## MỞ ĐẦU

### 1. Lý do chọn đề tài

Trong bối cảnh thị trường lao động công nghệ thông tin (CNTT) tại Việt Nam phát triển mạnh mẽ, nhu cầu tuyển dụng và tìm kiếm việc làm ngày càng gia tăng về số lượng lẫn độ phức tạp. Theo báo cáo của TopCV và ITviec (2025), Việt Nam cần bổ sung hơn 150.000 nhân lực CNTT mỗi năm trong giai đoạn 2025–2027, trong khi hầu hết ứng viên gặp khó khăn trong việc trình bày hồ sơ xin việc (CV) đúng chuẩn và xác định lộ trình nghề nghiệp phù hợp.

Một trong những rào cản lớn nhất là **sự thiếu hụt công cụ hỗ trợ thông minh bằng tiếng Việt**: các hệ thống ATS (Applicant Tracking System) phổ biến trên thị trường chủ yếu được tối ưu cho tiếng Anh, trong khi CV tiếng Việt có cấu trúc và từ vựng đặc thù riêng. Theo khảo sát thị trường tuyển dụng CNTT Việt Nam từ ITviec [[36]](tai_lieu_tham_khao.md#ref-36) và TopCV [[37]](tai_lieu_tham_khao.md#ref-37), ứng viên thường không có đủ thông tin để tự đánh giá mức độ phù hợp (ATS score) giữa CV của mình và yêu cầu từ nhà tuyển dụng.

Xử lý ngôn ngữ tự nhiên (NLP) và các mô hình ngôn ngữ lớn (LLM) đã chứng minh hiệu quả vượt trội trong các bài toán hiểu ngữ nghĩa văn bản [[2]](tai_lieu_tham_khao.md#ref-2) [[16]](tai_lieu_tham_khao.md#ref-16). Đặc biệt, mô hình PhoBERT [[11]](tai_lieu_tham_khao.md#ref-11) — mô hình BERT tiền huấn luyện đầu tiên cho tiếng Việt — đã đạt kết quả state-of-the-art trên nhiều tác vụ NLP tiếng Việt, mở ra cơ hội ứng dụng vào bài toán phân tích CV/JD tiếng Việt.

Từ những thực tiễn trên, nhóm nghiên cứu đề xuất đề tài: **"Nghiên cứu và ứng dụng xử lý ngôn ngữ tự nhiên trong phát triển hệ thống AI tạo lập CV thông minh và tư vấn cá nhân hóa lộ trình nghề nghiệp"** với mong muốn xây dựng một hệ thống toàn diện, hỗ trợ ứng viên CNTT tại Việt Nam trong toàn bộ vòng đời xin việc.

### 2. Mục tiêu nghiên cứu

**Mục tiêu tổng quát:** Nghiên cứu và xây dựng hệ thống AI ứng dụng NLP để hỗ trợ tạo lập CV thông minh và tư vấn lộ trình nghề nghiệp cá nhân hóa cho ứng viên ngành CNTT tại Việt Nam.

**Mục tiêu cụ thể:**

1. Xây dựng mô hình **NER (Named Entity Recognition)** cho CV và JD tiếng Việt/tiếng Anh, trích xuất các thực thể: kỹ năng (SKILL), vị trí công việc (JOB_TITLE), tổ chức (ORG), trình độ học vấn (DEGREE, MAJOR), thời gian (DATE), địa điểm (LOC).
2. Phát triển **Skill Matching Engine** so khớp kỹ năng giữa CV và JD dựa trên ontology kỹ năng IT, tính toán ATS score và gợi ý kỹ năng còn thiếu.
3. Xây dựng **Chatbot tư vấn nghề nghiệp** sử dụng kiến trúc RAG (Retrieval-Augmented Generation) kết hợp LLM, cung cấp gợi ý cá nhân hóa về CV và lộ trình phát triển kỹ năng.
4. Thiết kế và triển khai **kiến trúc microservices** hoàn chỉnh, tích hợp các thành phần AI vào một hệ thống web end-to-end có khả năng mở rộng.
5. Tạo lập **bộ dữ liệu CV/JD synthetic** chất lượng cao cho ngành CNTT Việt Nam, phục vụ huấn luyện và đánh giá mô hình.

### 3. Nội dung nghiên cứu

- **Nội dung 1:** Tổng quan tài liệu về NER, CV parsing, ATS, career recommendation và các kỹ thuật sinh dữ liệu synthetic bằng LLM.
- **Nội dung 2:** Thu thập, sinh và tiền xử lý dữ liệu CV/JD synthetic tiếng Việt/tiếng Anh cho ngành CNTT.
- **Nội dung 3:** Huấn luyện và đánh giá mô hình NER cho CV và JD sử dụng mBERT.
- **Nội dung 4:** Xây dựng Skill Matching Engine dựa trên ontology kỹ năng IT và Sentence-BERT embeddings.
- **Nội dung 5:** Phát triển Chatbot RAG sử dụng LlamaIndex, ChromaDB và Llama 3.2.
- **Nội dung 6:** Thiết kế kiến trúc microservices và tích hợp toàn bộ hệ thống.
- **Nội dung 7:** Thực nghiệm, đánh giá và phân tích kết quả.

### 4. Phương pháp nghiên cứu

- **Phương pháp nghiên cứu tài liệu:** Tổng quan các công trình trong và ngoài nước về NER, CV parsing, ATS, career recommendation, knowledge graph và LLM.
- **Phương pháp thực nghiệm:** Huấn luyện và đánh giá mô hình NLP trên bộ dữ liệu synthetic; so sánh với các baseline.
- **Phương pháp sinh dữ liệu tổng hợp (Synthetic Data Generation):** Sử dụng LLM (Qwen2.5-1.5B-Instruct) để sinh dữ liệu CV/JD có kiểm soát chất lượng.
- **Phương pháp thiết kế hệ thống:** Áp dụng kiến trúc microservices, domain-driven design và các nguyên tắc API-first.

### 5. Đối tượng và phạm vi nghiên cứu

**Đối tượng nghiên cứu:**
- CV và JD trong lĩnh vực CNTT, được viết bằng tiếng Việt và tiếng Anh.
- Các mô hình NLP: mBERT, Sentence-BERT, LLM (Llama 3.2) áp dụng cho bài toán phân tích CV/JD.
- Kiến trúc microservices cho hệ thống AI.

**Phạm vi nghiên cứu:**
- **Lĩnh vực:** Ngành CNTT tại Việt Nam (Backend Developer, Frontend Developer, Data Scientist, DevOps Engineer, AI Engineer, v.v.).
- **Dữ liệu:** Bộ dữ liệu synthetic gồm ~1.000 CV và ~100 JD được sinh bằng LLM; CV thực tế dùng để demo định tính.
- **Ngôn ngữ:** Tiếng Anh (chủ yếu) và tiếng Việt.
- **Giới hạn:** Đề tài không thu thập dữ liệu cá nhân thật; không triển khai lên môi trường production công khai.

### 6. Ý nghĩa khoa học và thực tiễn

**Ý nghĩa khoa học:**
- Đóng góp bộ dữ liệu CV/JD synthetic chất lượng cao cho ngành CNTT Việt Nam.
- Đề xuất pipeline tích hợp NER → Skill Matching → RAG Chatbot cho bài toán tư vấn nghề nghiệp.
- Nghiên cứu thực tiễn về ứng dụng kiến trúc microservices cho hệ thống AI.

**Ý nghĩa thực tiễn:**
- Hỗ trợ ứng viên CNTT tạo lập CV chuyên nghiệp, đánh giá mức độ phù hợp với JD và nhận tư vấn lộ trình phát triển kỹ năng.
- Cung cấp công cụ có thể tích hợp vào các nền tảng tuyển dụng hoặc hệ thống đào tạo nội bộ.

### 7. Bố cục báo cáo

Ngoài phần Mở đầu, Kết luận và Tài liệu tham khảo, báo cáo được tổ chức thành 3 chương:

- **[Chương 1](./chuong1/1.1_cong_trinh_lien_quan.md):** Tổng quan và Cơ sở lý thuyết
- **[Chương 2](./chuong2/2.1_kien_truc_tong_the.md):** Thiết kế hệ thống
- **[Chương 3](./chuong3/3.1_moi_truong_thuc_nghiem.md):** Thực nghiệm và Kết quả

---
