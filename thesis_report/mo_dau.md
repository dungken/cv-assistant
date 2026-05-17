# Mở đầu

### 1. Lý do chọn đề tài

Thị trường tuyển dụng công nghệ thông tin (CNTT) tại Việt Nam đang trải qua giai đoạn biến động mạnh, với tốc độ thay đổi yêu cầu kỹ năng nhanh chưa từng có. Theo báo cáo của ITviec (2025) [[11]](tai_lieu_tham_khao.md#ref-11) và TopCV (2025) [[12]](tai_lieu_tham_khao.md#ref-12), một kỹ năng "hot" trong nửa đầu năm có thể giảm 30–40% nhu cầu chỉ sau 6 tháng, đặc biệt trong các nhánh Frontend, AI/ML và DevOps. Khảo sát của ITviec cho thấy hơn 60% sinh viên CNTT tại Việt Nam **không biết kỹ năng nào trên CV của mình đang mất giá trên thị trường**, và hơn 70% **không có lộ trình rõ ràng** để cải thiện hồ sơ xin việc trước khi tốt nghiệp.

Các công cụ hỗ trợ sinh viên hiện có chưa giải quyết được vấn đề này. Hệ thống ATS truyền thống (Applicant Tracking System) chỉ chấm điểm CV tại thời điểm nộp đơn, không theo dõi sự cập nhật của CV theo thời gian. Các nền tảng tuyển dụng như LinkedIn hay TopCV có cung cấp insight về thị trường, nhưng không cá nhân hóa theo từng CV cụ thể của sinh viên Việt Nam và chỉ đánh giá CV theo tiêu chí đơn lẻ (keyword match). Các chatbot AI như ChatGPT hay Gemini có thể phân tích CV theo yêu cầu, nhưng gặp ba hạn chế cơ bản: (1) không có dữ liệu thị trường tuyển dụng Việt Nam thực tế, gợi ý chỉ dựa trên kiến thức tổng quát của mô hình; (2) không có khả năng theo dõi CV liên tục theo thời gian; (3) gợi ý lộ trình học tập chỉ dựa trên "cảm tính" của mô hình, không có cơ sở toán học rõ ràng và không thể tái lập được.

Khoảng trống công cụ này dẫn đến tình trạng phổ biến: sinh viên viết CV một lần, gửi đi nhiều nơi, không biết tại sao bị từ chối, không biết kỹ năng nào của mình đã lỗi thời, và không biết nên học gì tiếp theo để cải thiện cơ hội. CV trở thành một "tài liệu chết" thay vì một hồ sơ sống được cập nhật theo thị trường.

Từ thực tiễn trên, đề tài đề xuất xây dựng hệ thống **CV Health Intelligence cho Sinh viên CNTT Việt Nam** — định lượng "sức khỏe" của CV theo nhiều tiêu chí, gợi ý lộ trình học kỹ năng tối ưu và cung cấp bức tranh thị trường tuyển dụng thực tế. Bốn đóng góp cốt lõi của đề tài là: (1) khung **Multi-criteria CV Freshness Framework 8 chiều** (Skill, Experience, Project, Education, Achievement, Language, Completeness, Market Alignment); (2) **Learning Path Optimizer** trên skill graph với so sánh thực nghiệm Greedy, Dijkstra và Dynamic Programming; (3) **NER fine-tuned BERT song ngữ Việt-Anh** cho CV/JD CNTT đạt F1 = 0.86 token-level và F1 = 0.74 span-level; (4) **Market Intelligence Dashboard 33 insight** xây dựng trên dữ liệu snapshot ~1500 JD crawl từ ITviec và TopCV.

### 2. Mục tiêu nghiên cứu

**Mục tiêu tổng quát:** Nghiên cứu và xây dựng hệ thống CV Health Intelligence cho sinh viên CNTT Việt Nam, tích hợp đánh giá CV đa tiêu chí, tối ưu lộ trình học và phân tích thị trường tuyển dụng.

**Mục tiêu cụ thể:**

1. Xây dựng pipeline thu thập dữ liệu JD thực từ các nền tảng tuyển dụng Việt Nam (ITviec, TopCV) với cross-source deduplication qua `job_group_id`, snapshot ~1500 JD và cron crawl hàng ngày để cập nhật.
2. Đề xuất và đánh giá khung **Multi-criteria CV Freshness Framework** đánh giá CV theo 8 chiều và công thức tổng hợp định lượng mức độ cập nhật của CV so với thị trường.
3. Hình thức hóa bài toán **Learning Path Optimization** trên skill graph như một bài toán tối ưu tổ hợp, cài đặt và so sánh ba thuật toán Greedy, Dijkstra, Dynamic Programming trên bộ benchmark 50 test cases.
4. Xây dựng pipeline **NER song ngữ Việt-Anh** fine-tune BERT cho CV/JD CNTT, đánh giá F1 ở mức token và mức span.
5. Xây dựng **Market Intelligence Dashboard** với 33 insight (top skill, salary distribution, work-mode trend, role demand) và **CV Health Dashboard** trực quan hóa Freshness 8 chiều, learning path, opportunity window.

### 3. Nội dung nghiên cứu

- **Nội dung 1:** Tổng quan tài liệu về Multi-Criteria Decision Making, skill graph, learning path recommendation, NER bilingual và career intelligence; phân tích các công trình liên quan trong và ngoài nước.
- **Nội dung 2:** Xây dựng pipeline crawl JD thực từ ITviec và TopCV (cloudscraper + AJAX endpoint), cross-source dedup qua `job_group_id`, cron daily.
- **Nội dung 3:** Fine-tune BERT cho NER song ngữ Việt-Anh; đánh giá F1 token-level và span-level trên gold corpus tự gán nhãn.
- **Nội dung 4:** Thiết kế Multi-criteria CV Freshness Framework với 8 chiều đánh giá; cài đặt CVFreshnessEngine và phương pháp validate.
- **Nội dung 5:** Hình thức hóa bài toán Learning Path Optimization trên skill graph; cài đặt ba thuật toán Greedy, Dijkstra, Dynamic Programming và benchmark trên 50 test cases.
- **Nội dung 6:** Xây dựng Market Intelligence Dashboard (33 insight) và CV Health Dashboard; tích hợp end-to-end vào kiến trúc hệ thống.

### 4. Phương pháp nghiên cứu

- **Phương pháp nghiên cứu tài liệu:** Tổng quan các công trình liên quan đến MCDM, knowledge graph, learning path recommendation, NER bilingual và market intelligence từ các tạp chí, hội nghị khoa học (ACL, EMNLP, RecSys, KSE, IJCAI).
- **Phương pháp thực nghiệm:** Cài đặt và đánh giá Multi-criteria Freshness Framework, ba thuật toán Learning Path Optimization, NER bilingual fine-tune BERT trên dữ liệu JD thực snapshot ~1500 JD và corpus CV/JD gán nhãn thủ công.
- **Phương pháp thu thập dữ liệu:** Crawl JD từ ITviec và TopCV (cloudscraper + AJAX endpoint), tuân thủ robots.txt cho mục đích nghiên cứu học thuật; cron daily để cập nhật snapshot.
- **Phương pháp đánh giá:** Đánh giá Multi-criteria Framework bằng cách so sánh giữa 10 CV "cập nhật" và 10 CV "lỗi thời" tạo thủ công; đánh giá Learning Path Optimizer bằng benchmark 50 test cases (số JD unlock, runtime, optimality gap); đánh giá NER bằng F1 token-level và span-level trên gold corpus.

### 5. Đối tượng và phạm vi nghiên cứu

**Đối tượng nghiên cứu:**
- CV và JD trong lĩnh vực CNTT, được viết bằng tiếng Việt và tiếng Anh.
- Skill graph kỹ năng CNTT (~500 nodes) với các quan hệ REQUIRES, LEADS_TO, RELATED_TO, PART_OF.
- Các thuật toán tối ưu trên đồ thị: Greedy, Dijkstra, Dynamic Programming.
- Mô hình BERT fine-tune cho NER song ngữ.
- Dữ liệu thị trường tuyển dụng CNTT Việt Nam.

**Phạm vi nghiên cứu:**
- **Đối tượng người dùng:** Sinh viên CNTT Việt Nam (năm 3–4, chuẩn bị thực tập hoặc tìm việc đầu sự nghiệp).
- **Lĩnh vực:** Ngành CNTT tại Việt Nam (Backend Developer, Frontend Developer, Data Scientist, DevOps Engineer, AI Engineer).
- **Dữ liệu:** Snapshot ~1500 JD thu thập từ ITviec và TopCV trong giai đoạn nghiên cứu, cập nhật hàng ngày qua cron crawl.
- **Ngôn ngữ:** Tiếng Việt và tiếng Anh.
- **Giới hạn:** Đề tài không thu thập dữ liệu cá nhân thật của người dùng (CV trong demo do người dùng tự cung cấp); không triển khai lên môi trường production công khai; không phân phối lại dữ liệu thô đã crawl; không thực hiện user study chính thức trong phạm vi đồ án.

### 6. Ý nghĩa khoa học và thực tiễn

**Ý nghĩa khoa học:**
- Đề xuất khung Multi-criteria CV Freshness Framework 8 chiều — phương pháp đánh giá CV đa tiêu chí định lượng và có thể tái lập được.
- Hình thức hóa bài toán Learning Path Optimization trên skill graph và cung cấp so sánh thực nghiệm ba thuật toán trên dữ liệu thị trường CNTT Việt Nam.
- Cung cấp pipeline NER song ngữ Việt-Anh fine-tune BERT cho CV/JD CNTT với báo cáo F1 token-level và span-level.
- Đóng góp bộ dữ liệu JD snapshot và các phân tích Market Intelligence cho thị trường CNTT Việt Nam phục vụ các nghiên cứu tiếp theo.

**Ý nghĩa thực tiễn:**
- Hỗ trợ sinh viên CNTT Việt Nam theo dõi sức khỏe CV theo 8 chiều và nhận lộ trình học kỹ năng cụ thể, có thể chứng minh được bằng dữ liệu thị trường.
- Cung cấp Market Intelligence Dashboard giúp sinh viên hiểu nhu cầu thực tế (top skill, salary, work-mode trend) khi định hướng nghề nghiệp.
- Cung cấp công cụ có thể triển khai tại Career Center các trường đại học CNTT để hỗ trợ sinh viên trong quá trình học và tìm việc.

### 7. Bố cục báo cáo

Ngoài phần Mở đầu, Kết luận và Tài liệu tham khảo, báo cáo được tổ chức thành 4 chương:

- **[Chương 1](./chuong1/1.1_tong_quan_cong_trinh.md):** Tổng quan
- **[Chương 2](./chuong2/2.1_skill_graph_knowledge_graph.md):** Cơ sở lý thuyết
- **[Chương 3](./chuong3/3.1_phan_tich_yeu_cau.md):** Phân tích và Thiết kế hệ thống
- **Chương 4:** Xây dựng và Thực nghiệm *(viết từ tuần 17)*

---

[→ Chương 1: Tổng quan](./chuong1/1.1_tong_quan_cong_trinh.md)
