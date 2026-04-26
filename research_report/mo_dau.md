# Mở đầu

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

[→ Chương 1: Tổng quan và Cơ sở lý thuyết](./chuong1/1.1_cong_trinh_lien_quan.md)
