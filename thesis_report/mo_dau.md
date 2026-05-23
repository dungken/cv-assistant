# Mở đầu

### 1. Lý do chọn đề tài

Thị trường tuyển dụng công nghệ thông tin (CNTT) tại Việt Nam đang trải qua giai đoạn biến động mạnh, với tốc độ thay đổi yêu cầu kỹ năng nhanh chưa từng có. Theo báo cáo của ITviec (2025) [[11]](tai_lieu_tham_khao.md#ref-11) và TopCV (2025) [[12]](tai_lieu_tham_khao.md#ref-12), một kỹ năng "hot" trong nửa đầu năm có thể giảm 30–40% nhu cầu chỉ sau 6 tháng, đặc biệt trong các nhánh Frontend, AI/ML và DevOps. Khảo sát của ITviec cho thấy hơn 60% sinh viên CNTT tại Việt Nam **không biết kỹ năng nào trên CV của mình đang mất giá trên thị trường**, và hơn 70% **không có lộ trình rõ ràng** để cải thiện hồ sơ xin việc trước khi tốt nghiệp.

Các công cụ hỗ trợ sinh viên hiện có chưa giải quyết được vấn đề này. Hệ thống ATS truyền thống chỉ chấm điểm CV tại thời điểm nộp đơn theo tiêu chí đơn lẻ, không theo dõi sự cập nhật của CV theo thời gian và không tách rời được các chiều khác nhau. Các nền tảng tuyển dụng như LinkedIn hay TopCV cung cấp insight về thị trường ở dạng báo cáo đóng, không cá nhân hóa và không cho phép sinh viên tự khám phá theo nhu cầu. Các chatbot AI như ChatGPT, Gemini có thể tư vấn nhưng thiếu dữ liệu thị trường Việt Nam thực tế, không theo dõi CV liên tục, và gợi ý lộ trình học không dựa trên thuật toán tối ưu có thể tái lập.

Khoảng trống công cụ này dẫn đến tình trạng phổ biến: sinh viên viết CV một lần, gửi đi nhiều nơi, không biết tại sao bị từ chối, không biết kỹ năng nào của mình đã lỗi thời, và không biết nên học gì tiếp theo. CV trở thành một "tài liệu chết" thay vì một hồ sơ sống được cập nhật theo thị trường.

Từ thực tiễn trên, đề tài đề xuất xây dựng hệ thống **CV Health Intelligence cho Sinh viên CNTT Việt Nam** với hai đóng góp khoa học: (1) **Multi-criteria CV Freshness Framework** đánh giá CV theo 8 chiều, validate qua phân biệt fresh/stale, Cohen's d separation và monotonic build-up; (2) **Market Intelligence Dashboard** với 33 insight trên snapshot ~1500 JD crawl từ ITviec và TopCV có cross-source deduplication. Chi tiết các đóng góp được trình bày trong [Chương 1 — Tổng quan](./chuong1/1.1_tong_quan_cong_trinh.md).

### 2. Bố cục báo cáo

Ngoài phần Mở đầu, Kết luận và Tài liệu tham khảo, báo cáo được tổ chức thành 4 chương:

- **[Chương 1](./chuong1/1.1_tong_quan_cong_trinh.md): Tổng quan** — Tình hình nghiên cứu liên quan, bối cảnh thực tiễn, mục tiêu, đối tượng, phạm vi và đóng góp của đề tài.
- **[Chương 2](./chuong2/2.1_mcdm_danh_gia_cv.md): Cơ sở lý thuyết** — Multi-Criteria Decision Making, Market Intelligence, pipeline tiền xử lý CV/JD song ngữ.
- **[Chương 3](./chuong3/3.1_phan_tich_yeu_cau.md): Phân tích và Thiết kế hệ thống** — Phân tích yêu cầu, thiết kế hai đóng góp khoa học chính và infrastructure hỗ trợ.
- **Chương 4: Xây dựng và Thực nghiệm** — Cài đặt, đánh giá đa tầng và kết quả thực nghiệm.

---

[→ Chương 1: Tổng quan](./chuong1/1.1_tong_quan_cong_trinh.md)
