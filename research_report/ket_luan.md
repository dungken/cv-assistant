# Kết luận và Kiến nghị

## Kết quả Đạt được

Đề tài nghiên cứu "Nghiên cứu và ứng dụng NLP trong phát triển hệ thống AI tạo lập CV thông minh và tư vấn cá nhân hóa lộ trình nghề nghiệp" đã hoàn thành các mục tiêu chính đề ra ban đầu, bao gồm xây dựng hệ thống end-to-end có khả năng phân tích CV, đánh giá mức độ phù hợp với JD, và cung cấp tư vấn nghề nghiệp cá nhân hóa cho sinh viên và kỹ sư CNTT Việt Nam.

Về mặt nghiên cứu NLP, đề tài đã thành công fine-tune mô hình mBERT cho bài toán NER CV song ngữ Việt-Anh với 21 nhãn BIO, đạt F1 = 0.8633 trên tập đánh giá ground truth thủ công — kết quả cạnh tranh trong bối cảnh dữ liệu huấn luyện hoàn toàn là synthetic và không có GPU chuyên dụng. Mô hình hoạt động đặc biệt tốt với thực thể SKILL (F1 = 0.9157) — loại thực thể quan trọng nhất và cũng khó nhất trong domain CV ngành CNTT. Hệ thống cũng triển khai thành công Skill Matching 3 tầng (exact → ontology → semantic) kết hợp ontology kỹ năng IT khoảng 500 entries với Sentence-BERT, đạt 100% accuracy trên bộ 10 test cases kiểm thử các tình huống matching thực tế.

Về mặt hệ thống, đề tài xây dựng thành công kiến trúc microservices 9 thành phần hoàn chỉnh: API Gateway ASP.NET Core 9 với JWT authentication và CV versioning, ba Python services cho NER/Skill/Career, Chatbot Service với RAG pipeline tích hợp LlamaIndex + ChromaDB + dual LLM (Ollama local và Groq Cloud), PostgreSQL cho relational data, và Frontend React 18 với giao diện two-panel layout. Toàn bộ hệ thống có thể được triển khai bằng một lệnh Docker Compose duy nhất, đảm bảo reproducibility và portability.

Về đóng góp học thuật và thực tiễn, đề tài đóng góp ba thứ có thể tái sử dụng cho cộng đồng nghiên cứu: bộ dữ liệu 600 CV synthetic song ngữ Việt-Anh với kiểm soát chất lượng (quality_score trung bình 0.97), ontology kỹ năng IT khoảng 500 entries cập nhật cho thị trường Việt Nam, và kiến trúc RAG cá nhân hóa với cơ chế tool-aware context prompt và User Memory Service — hai tính năng phân biệt hệ thống với chatbot RAG thông thường.

## Hạn chế

Bên cạnh các kết quả đạt được, đề tài thừa nhận một số hạn chế quan trọng. Mô hình NER được huấn luyện hoàn toàn trên dữ liệu synthetic, dẫn đến tiềm năng distribution shift khi gặp CV thực tế có phong cách viết đa dạng hơn. Training logs bị mất do không mount Google Drive khi huấn luyện trên Colab, khiến không thể phân tích quá trình hội tụ. Bộ test Skill Matching chỉ gồm 10 cases thủ công, chưa đủ đại diện cho toàn bộ phân phối thực tế. Chatbot chưa được đánh giá định lượng qua user study. Và hệ thống chưa được benchmark về latency và throughput trong môi trường production với GPU.

## Kiến nghị

Trên cơ sở các kết quả và hạn chế đã phân tích, đề tài đề xuất các hướng phát triển tiếp theo theo thứ tự ưu tiên.

**Ưu tiên cao nhất** là mở rộng dữ liệu huấn luyện với CV thực tế được gán nhãn thủ công, tổ chức annotation sprint với 50–100 CV sử dụng Label Studio. Kết hợp với đó là thiết lập MLflow hoặc Weights & Biases để logging đầy đủ mọi experiment trong tương lai, tránh lặp lại tình trạng mất training logs.

**Ưu tiên trung bình** là thực hiện user study với tối thiểu 30 sinh viên/kỹ sư CNTT để có đánh giá định lượng về chất lượng tư vấn của chatbot, khả năng sử dụng của giao diện, và mức độ hữu ích tổng thể của hệ thống. Kết quả user study sẽ cung cấp basis thực nghiệm vững chắc hơn cho các cải tiến tiếp theo.

**Ưu tiên dài hạn** là khám phá kiến trúc ensemble kết hợp mBERT và PhoBERT cho NER, xây dựng pipeline tự động cập nhật ontology từ dữ liệu tuyển dụng ITviec/TopCV, và tối ưu hóa hệ thống cho production deployment với GPU inference server và caching layer.

Về ứng dụng thực tiễn, hệ thống có tiềm năng được triển khai như một công cụ hỗ trợ Career Center tại các trường đại học CNTT Việt Nam, cung cấp dịch vụ review CV và tư vấn nghề nghiệp miễn phí cho sinh viên — một khoảng trống dịch vụ đáng kể tại thị trường hiện tại nơi các dịch vụ tương đương (LinkedIn Premium, TopCV Pro) đều có chi phí không phù hợp với sinh viên.

---

*[Tiếp theo: Tài liệu tham khảo]*
