|     |     |
| --- | --- |
| **TRƯỜNG ĐH GIAO THÔNG VẬN TẢI PHÂN HIỆU TP.HCM Bộ Môn Công Nghệ Thông Tin** | **CỘNG HOÀ XÃ HỘI CHỦ NGHĨA VIỆT NAM Độc Lập - Tự Do - Hạnh Phúc** |

**ĐỀ CƯƠNG CHI TIẾT ĐỒ ÁN TỐT NGHIỆP**

**• Thông tin Sinh viên:**

|     |     |     |     |
| --- | --- | --- | --- |
| Họ tên: | \[Họ và tên sinh viên\] | Mã sinh viên: | \[Mã SV\] |
| Lớp: | CQ.XX.CNTT | Hệ: | Chính quy |
| Ngành đào tạo: | Công nghệ thông tin | Khoá: | \[Khóa\] |
| Email: | \[email@utc2.edu.vn\] | Số điện thoại: | \[SĐT\] |

**• Thông tin Giảng viên hướng dẫn:**

|     |     |     |     |
| --- | --- | --- | --- |
| Họ tên: | \[Tên GVHD\] | Học vị: | Thạc sĩ / Tiến sĩ |
| Email: | \[email@utc2.edu.vn\] | Số điện thoại: | \[SĐT\] |
| Đơn vị công tác: | Trường Đại học Giao thông Vận tải Phân hiệu tại TP. Hồ Chí Minh |     |     |

**NỘI DUNG**

**I. Tên đề tài**

Nghiên cứu và Xây dựng Hệ thống CV Health Intelligence — Theo dõi Sức khỏe CV Theo Thị trường Thực tế và Tối ưu Lộ trình Học Kỹ năng cho Ứng viên CNTT tại Việt Nam

**II. Giới thiệu**

Thị trường tuyển dụng CNTT tại Việt Nam thay đổi rất nhanh, kỹ năng "hot" hôm nay có thể không còn được nhà tuyển dụng quan tâm sau vài tháng. Theo khảo sát của ITviec (2025), hơn 60% ứng viên CNTT không biết kỹ năng nào trên CV của mình đang mất giá, và hơn 70% không có lộ trình rõ ràng để cải thiện hồ sơ xin việc.

Các công cụ hiện có như LinkedIn, TopCV hay ChatGPT, Gemini đều có hạn chế: ChatGPT/Gemini có thể phân tích CV nhưng không có dữ liệu thị trường Việt Nam, không theo dõi CV theo thời gian, và gợi ý học tập chỉ dựa trên "cảm tính" của model. LinkedIn có market insights nhưng không cá nhân hóa theo từng CV cụ thể. Chưa có công cụ nào cho người dùng biết CV của họ đang "khỏe" hay "yếu" so với thị trường, và chỉ ra con đường ngắn nhất để cải thiện.

Đề tài xây dựng hệ thống **CV Health Intelligence** trong 18 tuần (03/2026 – 07/2026), tập trung vào hai bài toán chính:

- **CV Freshness Score:** Công thức tính điểm "sức khỏe" CV dựa trên dữ liệu JD crawl hàng ngày từ ITviec/TopCV. Dashboard cho người dùng theo dõi điểm số theo thời gian và nhận cảnh báo khi kỹ năng tăng/giảm demand.

- **Learning Path Optimizer:** Bài toán tìm lộ trình học kỹ năng tối ưu trên skill graph, so sánh 3 thuật toán Greedy, Dijkstra và Dynamic Programming. Kết quả là gợi ý thứ tự học kỹ năng giúp người dùng mở khóa được nhiều JD nhất trong thời gian cho trước.

Để hai bài toán trên có thể vận hành, hệ thống cần một pipeline trích xuất và chuẩn hóa kỹ năng từ CV và JD, bao gồm NER song ngữ Việt-Anh, Skill Matching Engine và skill ontology. Các thành phần này được xây dựng như nền dữ liệu, không phải trọng tâm đóng góp của đề tài.

Mục tiêu cụ thể:

- Xây dựng pipeline crawl JD thực từ ITviec/TopCV và lưu trữ skill demand theo thời gian.
- Đề xuất và validate công thức **CV Freshness Score** — chỉ số định lượng mức độ cập nhật của CV theo thị trường.
- Hình thức hóa bài toán **Learning Path Optimization** trên skill graph, so sánh 3 thuật toán trên bộ benchmark từ dữ liệu thực.
- Xây dựng **CV Health Dashboard** hiển thị Freshness Score, skill alerts, learning path và opportunity window.
- Đánh giá hệ thống qua user study với 20–30 người dùng thực.

Phạm vi: ứng viên CNTT tại Việt Nam (Backend, Frontend, Data, DevOps, AI Engineer), dữ liệu từ ITviec và TopCV. Đề tài không bao gồm các ngành ngoài CNTT và không triển khai production công khai.

**III. Cơ sở lý thuyết**

**1. Skill Graph và Knowledge Graph**

Knowledge Graph (KG) là đồ thị có hướng biểu diễn tri thức, với các nút là thực thể và cạnh là quan hệ có nhãn. Trong bài toán kỹ năng nghề nghiệp, skill graph mô tả các quan hệ: REQUIRES (A là điều kiện tiên quyết của B), LEADS_TO (học A dẫn đến học B), RELATED_TO (A và B có thể thay thế nhau). Theo Murugavel & Bhuvaneswari (2023), gợi ý nghề nghiệp dựa trên KG cho kết quả tốt hơn collaborative filtering nhờ khả năng suy luận theo quan hệ. Đề tài xây dựng skill graph kỹ năng CNTT khoảng 500 nodes và 250+ edges, gắn thêm trọng số học tập để dùng cho thuật toán tối ưu lộ trình.

**2. Learning Path Optimization**

Bài toán tìm lộ trình học tối ưu có thể quy về bài toán tối ưu tổ hợp trên đồ thị có trọng số. Các thuật toán Dijkstra, A* và Dynamic Programming đã được dùng nhiều trong các hệ thống gợi ý lộ trình học. Bài toán maximize coverage với budget constraint là biến thể của Knapsack Problem, có nền tảng lý thuyết rõ ràng để so sánh thuật toán. Greedy thường cho giải pháp gần tối ưu trong thời gian ngắn, phù hợp với yêu cầu phản hồi nhanh của hệ thống.

**3. Phân tích xu hướng kỹ năng theo thời gian**

Phân tích xu hướng kỹ năng từ dữ liệu tuyển dụng là hướng đang được quan tâm, nhờ dữ liệu JD ngày càng dồi dào trên các nền tảng trực tuyến. Skill demand có thể thay đổi đáng kể trong 3–6 tháng ở ngành CNTT. Phân tích time-series trên tần suất skill xuất hiện trong JD cung cấp tín hiệu hữu ích về xu hướng thị trường. Đề tài áp dụng kỹ thuật này cho thị trường CNTT Việt Nam.

**4. NER và Skill Matching cho CV/JD (thành phần nền)**

Để Freshness Score và Learning Path Optimizer hoạt động, hệ thống cần một bước trích xuất và chuẩn hóa kỹ năng từ CV và JD. Đề tài dùng mBERT fine-tuned cho NER song ngữ Việt-Anh và Skill Matching Engine 3 tầng (exact match → ontology match → semantic match với Sentence-BERT) để xử lý phần này. Các kỹ thuật này không phải đóng góp mới của đề tài, được tham chiếu như công cụ tiền xử lý dữ liệu.

**5. Web Crawling và lưu trữ dữ liệu**

Web crawling là kỹ thuật thu thập dữ liệu tự động từ các trang web. Đề tài dùng Selenium cho nội dung dynamic và BeautifulSoup cho HTML parsing để crawl JD từ ITviec/TopCV cho mục đích nghiên cứu, có tuân thủ robots.txt. ChromaDB được dùng để lưu trữ embedding vector của JD theo thời gian, hỗ trợ truy vấn semantic.

**6. Dashboard và Data Visualization**

Dashboard cần trực quan hóa nhiều loại dữ liệu: time-series chart cho skill trend, gauge chart cho Freshness Score, graph visualization cho learning path. Recharts là thư viện chart cho React, có sẵn các component này. Nguyên tắc thiết kế dashboard của Few (2006) được tham khảo để dashboard truyền đạt thông tin hiệu quả.

**IV. Phương pháp nghiên cứu**

**Tìm hiểu tài liệu:** Đọc các bài báo, paper liên quan đến skill graph, learning path recommendation, temporal skill analysis từ các nguồn như ACL, RecSys, KSE, IJCAI. Xem xu hướng nghiên cứu hiện tại và xác định hướng tiếp cận phù hợp cho thị trường CNTT Việt Nam.

**Thu thập dữ liệu:** Viết crawler lấy JD từ ITviec và TopCV (~200 JD/ngày). JD được parse để lấy ra skills, role, mức lương, location. Lưu vào ChromaDB theo ngày để có dữ liệu time-series.

**CV Freshness Score:** Đề xuất công thức tính dựa trên trend_weight, recency và độ quan trọng của skill. Validate bằng cách: (1) so sánh score giữa CV "cập nhật" và CV "lỗi thời" tạo thủ công; (2) khảo sát 10 recruiter đánh giá xem score có hợp lý không.

**Learning Path Optimizer:** Cài đặt 3 thuật toán Greedy, Dijkstra, DP. Tạo bộ 50 test case có sẵn lời giải tối ưu. So sánh các thuật toán về số JD mở khóa được sau N tuần và thời gian chạy.

**Xây dựng hệ thống:** Phát triển theo từng tuần (sprint ngắn). Các module độc lập tích hợp qua kiến trúc microservices để có thể làm song song và test riêng từng phần.

**Đánh giá người dùng:** User study với 20–30 người (sinh viên CNTT năm 3–4 và kỹ sư 0–3 năm kinh nghiệm). Đo: (1) Freshness Score có hữu ích không (thang Likert 1–5); (2) lộ trình học được gợi ý có khả thi không; (3) SUS score; (4) người dùng có muốn quay lại sử dụng không.

**V. Kết quả dự kiến**

Hệ thống CV Health Intelligence chạy được end-to-end với các chức năng:
- Pipeline crawl JD tự động hàng ngày từ ITviec/TopCV (~200 JD/ngày)
- Dashboard hiển thị CV Freshness Score, trend chart và skill alerts
- Learning Path Optimizer với visualization lộ trình học
- Opportunity Window: JD mới phù hợp trong 7 ngày gần nhất
- Thông báo trong app khi market thay đổi đáng kể
- Email digest hàng tuần tóm tắt thay đổi

Phần đóng góp đo được:
- Công thức CV Freshness Score có validate và so sánh với baseline (score random, score chỉ dựa trên ATS)
- Bảng so sánh 3 thuật toán Learning Path Optimization trên 50 test case: kỳ vọng Greedy đạt ≥ 80% kết quả tối ưu của DP với thời gian O(n) so với O(2^n)
- Bộ dữ liệu skill demand time-series cho thị trường CNTT Việt Nam

Kết quả user study kỳ vọng: SUS score ≥ 68 (mức trên trung bình), usefulness rating ≥ 3.5/5.0, ≥ 70% người dùng thấy lộ trình học được gợi ý là khả thi và hữu ích.

**VI. Đóng góp của đề tài**

Về mặt khoa học, đề tài đề xuất công thức **CV Freshness Score** — một cách định lượng mức độ cập nhật của CV theo thị trường tuyển dụng. Bên cạnh đó, đề tài hình thức hóa bài toán **Learning Path Optimization trên skill graph** và so sánh thực nghiệm 3 thuật toán trên dữ liệu thị trường CNTT Việt Nam.

Về mặt thực tiễn, hệ thống giải quyết một vấn đề khá rõ mà các công cụ hiện có (ChatGPT, LinkedIn, TopCV) chưa làm được: coi CV như một tài liệu sống cần cập nhật theo thị trường, không phải file tĩnh viết một lần rồi để đó. Hệ thống có thể dùng tại Career Center của các trường đại học để hỗ trợ sinh viên CNTT theo dõi và cải thiện CV trong suốt quá trình học và đi tìm việc.

**VII. Cấu trúc đồ án**

**CHƯƠNG 1: Tổng quan**

1.1. Tình hình nghiên cứu trong và ngoài nước về career recommendation và skill analysis

1.2. Lý do chọn đề tài và bối cảnh thực tiễn

1.3. Mục tiêu, nội dung, phương pháp nghiên cứu

&nbsp;&nbsp;&nbsp;&nbsp;1.3.1. Mục tiêu đề tài

&nbsp;&nbsp;&nbsp;&nbsp;1.3.2. Nội dung đề tài

&nbsp;&nbsp;&nbsp;&nbsp;1.3.3. Phương pháp nghiên cứu

1.4. Đối tượng và phạm vi đề tài

**CHƯƠNG 2: Cơ sở lý thuyết**

2.1. Skill Graph và Knowledge Graph trong Career Intelligence

2.2. Learning Path Optimization — cơ sở toán học và thuật toán

2.3. Temporal Skill Demand Analysis từ dữ liệu tuyển dụng

2.4. Web Crawling và xử lý dữ liệu JD thực tế

2.5. Pipeline trích xuất và chuẩn hóa kỹ năng từ CV/JD (NER, Skill Matching)

2.6. Các công nghệ và công cụ sử dụng

**CHƯƠNG 3: Phân tích và Thiết kế hệ thống**

3.1. Phân tích yêu cầu hệ thống

&nbsp;&nbsp;&nbsp;&nbsp;3.1.1. Yêu cầu chức năng

&nbsp;&nbsp;&nbsp;&nbsp;3.1.2. Yêu cầu phi chức năng (real-time, freshness, scalability)

&nbsp;&nbsp;&nbsp;&nbsp;3.1.3. Phân tích các bài toán cần giải quyết

3.2. Thiết kế CV Freshness Score

&nbsp;&nbsp;&nbsp;&nbsp;3.2.1. Đề xuất công thức Freshness Score

&nbsp;&nbsp;&nbsp;&nbsp;3.2.2. Phương pháp validate công thức

3.3. Thiết kế Learning Path Optimizer

&nbsp;&nbsp;&nbsp;&nbsp;3.3.1. Hình thức hóa bài toán tối ưu trên skill graph

&nbsp;&nbsp;&nbsp;&nbsp;3.3.2. Thuật toán Greedy, Dijkstra và Dynamic Programming

&nbsp;&nbsp;&nbsp;&nbsp;3.3.3. Thiết kế bộ benchmark đánh giá

3.4. Thiết kế pipeline crawl JD và time-series database

3.5. Thiết kế CV Health Dashboard

3.6. Thiết kế kiến trúc tổng thể và cơ sở dữ liệu

**CHƯƠNG 4: Xây dựng và Thực nghiệm hệ thống**

4.1. Môi trường phát triển và triển khai

4.2. Xây dựng JD Crawler và time-series data pipeline

4.3. Xây dựng CV Freshness Engine và kết quả validate

4.4. Xây dựng Learning Path Optimizer và kết quả benchmark 3 thuật toán

4.5. Xây dựng CV Health Dashboard (Frontend)

4.6. Pipeline trích xuất kỹ năng (NER, Skill Matching) hỗ trợ hệ thống

4.7. Thiết kế và kết quả thực nghiệm người dùng

**Kết luận và Kiến nghị**

Kết quả đạt được

Hạn chế

Hướng phát triển

**Tài liệu tham khảo**

**VIII. Tài liệu tham khảo**

\[1\] Murugavel, M., Bhuvaneswari, T. (2023). "Knowledge Graph-Based Career Path Recommendation Using Machine Learning". Journal of Intelligent Systems, 32(1), pp. 1-18.

\[2\] Decorte, J.J. et al. (2021). "Jobbert: Understanding Job Titles through Skills". arXiv:2109.09605.

\[3\] Lewis, P. et al. (2020). "Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks". Proc. NeurIPS 2020, pp. 9459-9474.

\[4\] Devlin, J. et al. (2019). "BERT: Pre-training of Deep Bidirectional Transformers for Language Understanding". Proc. NAACL 2019, Minneapolis, pp. 4171-4186.

\[5\] Nguyen, D.Q., Nguyen, A.T. (2020). "PhoBERT: Pre-trained Language Models for Vietnamese". Findings of EMNLP 2020, pp. 1037-1042.

\[6\] Qian, K. et al. (2022). "Towards Automated Skills Extraction and Matching for Job Postings". Proc. EMNLP 2022, Abu Dhabi, pp. 5651-5663.

\[7\] Reimers, N., Gurevych, I. (2019). "Sentence-BERT: Sentence Embeddings using Siamese BERT-Networks". Proc. EMNLP 2019, Hong Kong, pp. 3982-3992.

\[8\] Khuller, S., Moss, A., Naor, J. (1999). "The Budgeted Maximum Coverage Problem". Information Processing Letters, 70(1), pp. 39-45.

\[9\] Few, S. (2006). Information Dashboard Design. O'Reilly Media, Sebastopol.

\[10\] Dijkstra, E.W. (1959). "A note on two problems in connexion with graphs". Numerische Mathematik, 1(1), pp. 269-271.

\[11\] ITviec. "Báo cáo Thị trường Tuyển dụng CNTT Việt Nam 2025". https://itviec.com/blog (truy cập 05/2026).

\[12\] TopCV. "Khảo sát Thị trường Nhân lực CNTT 2025". https://topcv.vn/research (truy cập 05/2026).

\[13\] Reimers, N. (2023). "all-MiniLM-L6-v2". HuggingFace Model Hub. https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2 (truy cập 05/2026).

\[14\] European Commission. "ESCO — European Skills, Competencies, Qualifications and Occupations". https://esco.ec.europa.eu (truy cập 05/2026).

\[15\] US Department of Labor. "O\*NET OnLine". https://www.onetonline.org (truy cập 05/2026).

**IX. Kế Hoạch thực hiện và tiến độ nghiên cứu**

Thời gian và nội dung công việc theo tuần:

Đề tài được thực hiện trong 18 tuần, từ đầu tháng 03/2026 đến đầu tháng 07/2026.

|     |     |     |
| --- | --- | --- |
| **Thời gian** | **Nội dung công việc** | **Ghi chú** |
| Tuần 1 (02/03–08/03) | Nhận đề tài, gặp GVHD xác định mục tiêu và phạm vi. Khảo sát nhu cầu thực tế của ứng viên CNTT Việt Nam. Tổng hợp tài liệu nền về skill graph và learning path recommendation. | |
| Tuần 2 (09/03–15/03) | Xây dựng đề cương chi tiết. Tổng hợp tài liệu nâng cao về temporal skill analysis. Thiết kế kiến trúc tổng thể của hệ thống. | Nộp đề cương GVHD |
| Tuần 3 (16/03–22/03) | Chuẩn bị nền dữ liệu: thu thập CV mẫu, xây dựng pipeline NER song ngữ Việt-Anh để trích xuất kỹ năng. Khởi tạo schema database PostgreSQL và ChromaDB. | |
| Tuần 4 (23/03–29/03) | Tiếp tục huấn luyện và đánh giá pipeline NER trên tập validation. Bắt đầu xây dựng skill ontology IT (REQUIRES, LEADS_TO, RELATED_TO, PART_OF). | |
| Tuần 5 (30/03–05/04) | Hoàn thiện ontology (~500 entries). Implement Skill Matching Engine để chuẩn hóa kỹ năng giữa CV và JD. | |
| Tuần 6 (06/04–12/04) | Tích hợp pipeline tiền xử lý (NER + Skill Matching) thành dịch vụ chung. Khởi tạo frontend React và các component upload CV cơ bản. | |
| Tuần 7 (13/04–19/04) | Hoàn thiện nền dữ liệu, kiểm thử pipeline tiền xử lý trên CV và JD mẫu. Viết Chương 1 báo cáo (tổng quan). | |
| Tuần 8 (20/04–26/04) | Xây dựng JD Crawler (Selenium + BeautifulSoup) cho ITviec và TopCV. Bắt đầu chạy crawler tích lũy dữ liệu. | Crawl ~200 JD/ngày |
| Tuần 9 (27/04–03/05) | Hoàn thiện crawler, chạy ổn định. Thiết kế schema time-series database (skill_trends, real_jds). Viết Chương 2 báo cáo (cơ sở lý thuyết). | |
| Tuần 10 (04/05–10/05) | Thiết kế công thức **CV Freshness Score** (trend_weight, recency, importance). Bổ sung trường `cost` (learning weeks) vào ontology. Bắt đầu implement CVFreshnessEngine. | Mốc trọng tâm |
| Tuần 11 (11/05–17/05) | Hoàn thiện CVFreshnessEngine. Validate công thức Freshness Score: so sánh giữa 10 CV "cập nhật" và 10 CV "lỗi thời" tạo thủ công. Thiết kế bộ benchmark 50 test cases cho Learning Path Optimizer. | |
| Tuần 12 (18/05–24/05) | Implement **Learning Path Optimizer**: thuật toán Greedy (ROI) và Dijkstra trên skill graph có trọng số. Chạy thử trên benchmark, đánh giá kết quả ban đầu. | |
| Tuần 13 (25/05–31/05) | Implement thuật toán Dynamic Programming. Chạy benchmark đầy đủ so sánh 3 thuật toán trên 50 test cases (số JD unlock, runtime, optimality gap). Viết Chương 3 báo cáo. | |
| Tuần 14 (01/06–07/06) | Xây dựng API endpoints (`/health-score`, `/skill-alerts`, `/learning-path`, `/opportunity-window`). BackgroundTask recompute Freshness khi CV thay đổi. Setup cron job crawler trong Docker Compose. | |
| Tuần 15 (08/06–14/06) | Xây dựng **CV Health Dashboard** frontend: Freshness gauge + time-series chart, Learning Path visualization, Skill alert cards, Opportunity Window. Tích hợp end-to-end toàn hệ thống. | |
| Tuần 16 (15/06–21/06) | Pilot test với 5 người dùng, thu feedback và fix bug. Khảo sát 10 recruiter đánh giá Freshness Score. Chạy user study chính thức với 20–30 người dùng. | User study chính |
| Tuần 17 (22/06–28/06) | Phân tích và tổng hợp kết quả thực nghiệm. Viết Chương 4 báo cáo. Hoàn thiện Kết luận, Tài liệu tham khảo, Phụ lục. Kiểm tra tỷ lệ trùng lặp (≤ 30%). Sửa theo phản hồi GVHD. | |
| Tuần 18 (29/06–05/07) | Duyệt đồ án với GVHD. Chuẩn bị slide thuyết trình và demo hệ thống end-to-end. Bảo vệ đồ án tốt nghiệp. | Bảo vệ |

|     |     |     |
| --- | --- | --- |
| **Trưởng Bộ Môn**<br><br>**\[Tên Trưởng BM\]** | **Ý kiến của GVHD**<br><br>**\[Tên GVHD\]** | ……ngày….tháng….năm 2026<br><br>**Sinh viên thực hiện**<br><br>**\[Họ và tên sinh viên\]** |
