# Mở đầu

### 1. Lý do chọn đề tài

Thị trường tuyển dụng công nghệ thông tin (CNTT) tại Việt Nam đang trải qua giai đoạn biến động mạnh, với tốc độ thay đổi yêu cầu kỹ năng nhanh chưa từng có. Theo báo cáo của ITviec (2025) [[11]](tai_lieu_tham_khao.md#ref-11) và TopCV (2025) [[12]](tai_lieu_tham_khao.md#ref-12), một kỹ năng "hot" trong nửa đầu năm có thể giảm 30–40% nhu cầu chỉ sau 6 tháng, đặc biệt trong các nhánh Frontend, AI/ML và DevOps. Khảo sát của ITviec cho thấy hơn 60% ứng viên CNTT tại Việt Nam **không biết kỹ năng nào trên CV của mình đang mất giá trên thị trường**, và hơn 70% **không có lộ trình rõ ràng** để cải thiện hồ sơ xin việc.

Các công cụ hỗ trợ ứng viên hiện có chưa giải quyết được vấn đề này. Hệ thống ATS truyền thống (Applicant Tracking System) chỉ chấm điểm CV tại thời điểm nộp đơn, không theo dõi sự cập nhật của CV theo thời gian. Các nền tảng tuyển dụng như LinkedIn hay TopCV có cung cấp insight về thị trường, nhưng không cá nhân hóa theo từng CV cụ thể của người dùng Việt Nam. Các chatbot AI như ChatGPT hay Gemini có thể phân tích CV theo yêu cầu, nhưng gặp ba hạn chế cơ bản: (1) không có dữ liệu thị trường tuyển dụng Việt Nam thực tế, gợi ý chỉ dựa trên kiến thức tổng quát của mô hình; (2) không có khả năng theo dõi CV liên tục theo thời gian; (3) gợi ý lộ trình học tập chỉ dựa trên "cảm tính" của mô hình, không có cơ sở toán học rõ ràng và không thể tái lập được.

Khoảng trống công cụ này dẫn đến tình trạng phổ biến: ứng viên viết CV một lần, gửi đi nhiều nơi, không biết tại sao bị từ chối, không biết kỹ năng nào của mình đã lỗi thời, và không biết nên học gì tiếp theo để cải thiện cơ hội. CV trở thành một "tài liệu chết" thay vì một hồ sơ sống được cập nhật theo thị trường.

Từ thực tiễn trên, đề tài đề xuất xây dựng hệ thống **CV Health Intelligence** — một hệ thống định lượng "sức khỏe" của CV theo thị trường tuyển dụng thực tế và gợi ý lộ trình học kỹ năng tối ưu cho ứng viên CNTT Việt Nam. Hai đóng góp cốt lõi của đề tài là (1) công thức **CV Freshness Score** tính từ dữ liệu JD crawl hàng ngày, và (2) bài toán **Learning Path Optimization** trên skill graph với so sánh thực nghiệm ba thuật toán Greedy, Dijkstra và Dynamic Programming.

### 2. Mục tiêu nghiên cứu

**Mục tiêu tổng quát:** Nghiên cứu và xây dựng hệ thống CV Health Intelligence cho phép theo dõi "sức khỏe" CV theo thị trường tuyển dụng thực tế và gợi ý lộ trình học kỹ năng tối ưu cho ứng viên CNTT tại Việt Nam.

**Mục tiêu cụ thể:**

1. Xây dựng pipeline thu thập dữ liệu JD thực từ các nền tảng tuyển dụng Việt Nam (ITviec, TopCV) và hệ thống lưu trữ time-series cho skill demand theo thời gian.
2. Đề xuất và đánh giá công thức **CV Freshness Score** — chỉ số định lượng mức độ phù hợp của CV với thị trường tại một thời điểm cho trước, dựa trên ba thành phần trend_weight, recency và skill importance.
3. Hình thức hóa bài toán **Learning Path Optimization** trên skill graph như một bài toán tối ưu tổ hợp, cài đặt và so sánh ba thuật toán Greedy, Dijkstra, Dynamic Programming trên bộ benchmark từ dữ liệu thực.
4. Xây dựng **CV Health Dashboard** trực quan hóa Freshness Score theo thời gian, skill trend alerts, learning path và opportunity window.
5. Đánh giá toàn bộ hệ thống thông qua user study với 20–30 sinh viên và kỹ sư CNTT, và khảo sát 10 recruiter về tính hợp lý của Freshness Score.

### 3. Nội dung nghiên cứu

- **Nội dung 1:** Tổng quan tài liệu về skill graph, learning path recommendation, temporal skill analysis và career intelligence; phân tích các công trình liên quan trong và ngoài nước.
- **Nội dung 2:** Xây dựng pipeline crawl JD thực từ ITviec và TopCV; thiết kế cơ sở dữ liệu time-series cho skill demand.
- **Nội dung 3:** Thiết kế công thức CV Freshness Score và phương pháp đánh giá; cài đặt CVFreshnessEngine.
- **Nội dung 4:** Hình thức hóa bài toán Learning Path Optimization trên skill graph; cài đặt ba thuật toán Greedy, Dijkstra, Dynamic Programming và benchmark trên 50 test cases.
- **Nội dung 5:** Xây dựng CV Health Dashboard và tích hợp end-to-end vào kiến trúc hệ thống.
- **Nội dung 6:** Thực nghiệm, đánh giá người dùng và phân tích kết quả.

### 4. Phương pháp nghiên cứu

- **Phương pháp nghiên cứu tài liệu:** Tổng quan các công trình liên quan đến knowledge graph, learning path recommendation và temporal skill analysis từ các tạp chí, hội nghị khoa học (ACL, RecSys, KSE, IJCAI).
- **Phương pháp thực nghiệm:** Cài đặt và đánh giá Freshness Score, ba thuật toán Learning Path Optimization trên dữ liệu JD thực thu thập trong giai đoạn 6 tuần.
- **Phương pháp thu thập dữ liệu:** Crawl JD từ ITviec và TopCV theo lịch hàng ngày, tuân thủ robots.txt cho mục đích nghiên cứu học thuật.
- **Phương pháp đánh giá người dùng:** User study với 20–30 người (sinh viên CNTT năm 3–4 và kỹ sư 0–3 năm kinh nghiệm), dùng thang Likert, System Usability Scale (SUS) và phỏng vấn định tính.

### 5. Đối tượng và phạm vi nghiên cứu

**Đối tượng nghiên cứu:**
- CV và JD trong lĩnh vực CNTT, được viết bằng tiếng Việt và tiếng Anh.
- Skill graph kỹ năng CNTT (~500 nodes) với các quan hệ REQUIRES, LEADS_TO, RELATED_TO, PART_OF.
- Các thuật toán tối ưu trên đồ thị: Greedy, Dijkstra, Dynamic Programming.
- Dữ liệu thị trường tuyển dụng CNTT Việt Nam.

**Phạm vi nghiên cứu:**
- **Lĩnh vực:** Ngành CNTT tại Việt Nam (Backend Developer, Frontend Developer, Data Scientist, DevOps Engineer, AI Engineer).
- **Dữ liệu:** JD thu thập từ ITviec và TopCV trong giai đoạn nghiên cứu (~200 JD/ngày).
- **Ngôn ngữ:** Tiếng Việt và tiếng Anh.
- **Giới hạn:** Đề tài không thu thập dữ liệu cá nhân thật của người dùng (CV trong demo do người dùng tự cung cấp); không triển khai lên môi trường production công khai; không phân phối lại dữ liệu thô đã crawl.

### 6. Ý nghĩa khoa học và thực tiễn

**Ý nghĩa khoa học:**
- Đề xuất công thức CV Freshness Score — một cách định lượng mức độ cập nhật của CV theo thị trường tuyển dụng có thể tái lập được.
- Hình thức hóa bài toán Learning Path Optimization trên skill graph và cung cấp so sánh thực nghiệm ba thuật toán trên dữ liệu thị trường CNTT Việt Nam.
- Đóng góp bộ dữ liệu skill demand time-series cho thị trường CNTT Việt Nam phục vụ các nghiên cứu tiếp theo.

**Ý nghĩa thực tiễn:**
- Hỗ trợ ứng viên CNTT theo dõi sức khỏe CV theo thời gian thực và nhận lộ trình học kỹ năng cụ thể, có thể chứng minh được bằng dữ liệu.
- Cung cấp công cụ có thể triển khai tại Career Center các trường đại học CNTT để hỗ trợ sinh viên trong quá trình học và tìm việc.

### 7. Bố cục báo cáo

Ngoài phần Mở đầu, Kết luận và Tài liệu tham khảo, báo cáo được tổ chức thành 4 chương:

- **[Chương 1](./chuong1/1.1_tong_quan_cong_trinh.md):** Tổng quan
- **[Chương 2](./chuong2/2.1_skill_graph_knowledge_graph.md):** Cơ sở lý thuyết
- **Chương 3:** Phân tích và Thiết kế hệ thống *(viết từ tuần 13)*
- **Chương 4:** Xây dựng và Thực nghiệm *(viết từ tuần 17)*

---

[→ Chương 1: Tổng quan](./chuong1/1.1_tong_quan_cong_trinh.md)
