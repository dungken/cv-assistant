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

Nghiên cứu và Xây dựng Hệ thống CV Health Intelligence cho Sinh viên CNTT Việt Nam: Đánh giá Đa tiêu chí, Tối ưu Lộ trình Học và Phân tích Thị trường Tuyển dụng

**II. Giới thiệu**

Thị trường tuyển dụng CNTT tại Việt Nam thay đổi rất nhanh, kỹ năng "hot" hôm nay có thể không còn được nhà tuyển dụng quan tâm sau vài tháng. Theo khảo sát của ITviec (2025), hơn 60% ứng viên CNTT không biết kỹ năng nào trên CV của mình đang mất giá, và hơn 70% không có lộ trình rõ ràng để cải thiện hồ sơ xin việc. Riêng với sinh viên CNTT chuẩn bị tốt nghiệp, khoảng cách giữa CV của bản thân và yêu cầu thực tế của thị trường còn lớn hơn do thiếu kinh nghiệm thực chiến và thiếu công cụ tự đánh giá khách quan.

Các công cụ hiện có như LinkedIn, TopCV hay ChatGPT, Gemini đều có hạn chế: ChatGPT/Gemini có thể phân tích CV nhưng không có dữ liệu thị trường Việt Nam, không theo dõi CV theo thời gian, và gợi ý học tập chỉ dựa trên "cảm tính" của model. LinkedIn có market insights nhưng không cá nhân hóa theo từng CV cụ thể và không tập trung vào nhóm sinh viên/fresher. Các báo cáo thị trường (TopDev, VietnamWorks) chỉ cung cấp số liệu tổng quát, không phân tích đa chiều hay đưa ra gợi ý cá nhân hóa. Chưa có công cụ nào cho sinh viên biết CV của họ đang "khỏe" hay "yếu" so với thị trường, đánh giá toàn diện trên nhiều tiêu chí (không chỉ skill mà còn project, education, achievement…), và chỉ ra con đường ngắn nhất để cải thiện.

Đề tài xây dựng hệ thống **CV Health Intelligence** trong 18 tuần (03/2026 – 07/2026), tập trung vào **bốn đóng góp chính**:

- **(1) Multi-criteria CV Freshness Score:** Đề xuất khung đánh giá CV đa tiêu chí gồm 8 dimension (Skill Freshness, Experience Depth, Project Quality, Education Strength, Achievement Signal, Language, CV Completeness, Market Alignment) với trọng số tinh chỉnh riêng cho audience sinh viên CNTT Việt Nam. Mỗi dimension có sub-metrics đo lường được, công thức tổng hợp tường minh.

- **(2) Learning Path Optimizer:** Hình thức hóa bài toán tìm lộ trình học kỹ năng tối ưu trên skill graph, so sánh 3 thuật toán Greedy (ROI-based), Dijkstra (state-space) và Dynamic Programming (Budgeted Maximum Coverage). Kết quả là gợi ý thứ tự học kỹ năng giúp người dùng mở khóa được nhiều JD nhất trong thời gian cho trước.

- **(3) NER song ngữ Việt-Anh fine-tuned cho CV/JD CNTT:** Mô hình BERT-base fine-tune cho 20+ entity labels chuyên biệt domain CV CNTT Việt Nam (PER, ORG, DATE, LOC, SKILL, DEGREE, MAJOR, JOB_TITLE, PROJECT, CERT,...). Đạt F1 = 0.86 trên test set thủ công, F1 = 0.74 trên span-level evaluation 100 CV synthetic.

- **(4) Market Intelligence Dashboard:** Tổng hợp 33 insight đa chiều từ ~1.500 JD thực thu thập từ ITviec và TopCV — bao gồm Skill Premium Index, Skill Velocity (14d), Hidden Gems Quadrant, Skill Clustering (Jaccard + Union-Find), English Premium, Career ROI Salary Curve, Skill Network Graph. Cung cấp bối cảnh thị trường để CV Freshness Score và Learning Path Optimizer hoạt động có ý nghĩa thực tiễn.

Mục tiêu cụ thể:

- Xây dựng pipeline crawl JD thực từ ITviec/TopCV, snapshot ~1.500 JD active trong 45 ngày, lưu trữ skill demand theo thời gian.
- Đề xuất và validate **Multi-criteria CV Freshness Framework** (8 dimension) cho audience sinh viên CNTT Việt Nam.
- Hình thức hóa bài toán **Learning Path Optimization** trên skill graph, so sánh 3 thuật toán trên bộ benchmark từ dữ liệu thực.
- Fine-tune mô hình **NER BERT** cho CV/JD CNTT song ngữ, đo F1 token-level + span-level trên test set thủ công.
- Xây dựng **CV Health Dashboard + Market Intelligence Dashboard** với 33 insight phân tích thị trường + per-user analytics.

Phạm vi: sinh viên/ứng viên CNTT năm 3–4 và fresher (0–1 năm kinh nghiệm) tại Việt Nam (Backend, Frontend, Data, DevOps, AI Engineer), dữ liệu từ ITviec và TopCV. Đề tài không bao gồm các ngành ngoài CNTT, không triển khai production công khai, và không bao gồm user study quy mô lớn (limitation tự nhiên của khung thời gian).

**III. Cơ sở lý thuyết**

**1. Multi-criteria Decision Making (MCDM) cho đánh giá CV**

Đánh giá CV là bài toán đa tiêu chí cố hữu — một CV có thể mạnh về kỹ năng nhưng yếu về kinh nghiệm, hoặc ngược lại. Các phương pháp MCDM kinh điển như Weighted Sum Model (Saaty, 1980) và Analytic Hierarchy Process (AHP) cung cấp khung lý thuyết để tổng hợp nhiều tiêu chí thành một chỉ số duy nhất với trọng số có thể tùy chỉnh theo audience. Đề tài đề xuất khung Multi-criteria CV Freshness Score gồm 8 dimension (Skill Freshness, Experience Depth, Project Quality, Education Strength, Achievement Signal, Language Proficiency, CV Completeness, Market Alignment) với trọng số tinh chỉnh riêng cho sinh viên CNTT Việt Nam (ưu tiên Project Quality và Skill Freshness, giảm Experience Depth do nhóm này ít kinh nghiệm thực chiến).

**2. Skill Graph và Learning Path Optimization**

Knowledge Graph (KG) là đồ thị có hướng biểu diễn tri thức, với các nút là thực thể và cạnh là quan hệ có nhãn. Trong bài toán kỹ năng nghề nghiệp, skill graph mô tả các quan hệ REQUIRES, LEADS_TO, RELATED_TO, PART_OF. Theo Murugavel & Bhuvaneswari (2023), gợi ý nghề nghiệp dựa trên KG cho kết quả tốt hơn collaborative filtering nhờ khả năng suy luận theo quan hệ. Bài toán tìm lộ trình học tối ưu trên skill graph quy về bài toán tối ưu tổ hợp với ràng buộc budget — biến thể của Knapsack Problem. Đề tài cài đặt và so sánh ba thuật toán: Greedy (ROI-based) với tỷ lệ xấp xỉ (1−1/e) ≈ 0.63 theo Khuller et al. (1999), Dijkstra trên state-space graph, và Dynamic Programming bitmask cho lời giải tối ưu (O(2^n) khi |candidates| ≤ 20).

**3. Named Entity Recognition (NER) song ngữ Việt-Anh**

NER là bài toán trích xuất các thực thể có tên (Named Entity) từ văn bản không cấu trúc. CV và JD CNTT Việt Nam có đặc thù song ngữ Việt-Anh, đan xen tự do (vd: "Có kinh nghiệm về React.js và NodeJS"), khiến các mô hình NER monolingual không phù hợp. Đề tài fine-tune mô hình BERT-base cho 20+ entity labels chuyên biệt domain CV CNTT (PER, ORG, DATE, LOC, SKILL, DEGREE, MAJOR, JOB_TITLE, PROJECT, CERT,...), train trên ~1.000 CV synthetic được auto-label, đạt F1 = 0.86 trên test set thủ công 71 entities và F1 = 0.74 trên span-level evaluation 100 CV. Đây là một trong những đóng góp chính của đề tài, có thể tái sử dụng cho các hệ thống CV/JD parsing tiếng Việt khác.

**4. Phân tích xu hướng kỹ năng và Market Intelligence**

Phân tích xu hướng kỹ năng từ dữ liệu tuyển dụng là hướng đang được quan tâm, nhờ dữ liệu JD ngày càng dồi dào. Đề tài mở rộng hướng này thành **Market Intelligence Dashboard** với 33 insight đa chiều, bao gồm các phân tích chuyên sâu: Skill Premium Index (skill nào trả lương cao hơn median thị trường), Skill Velocity (so sánh 14d vs 14d trước để phát hiện trend), Hidden Gems Quadrant (skill ít cạnh tranh nhưng lương cao), Skill Clustering bằng Jaccard similarity + Union-Find, English Premium (mức lương khi yêu cầu tiếng Anh), Career ROI Salary Curve theo bucket kinh nghiệm, Skill Network Graph (force-directed visualization). Các phân tích này được tính SQL-side trên ~1.500 JD thu thập, cache 5 phút, cung cấp bối cảnh thị trường để Freshness Score và Learning Path Optimizer hoạt động có ý nghĩa thực tiễn.

**5. Web Crawling và lưu trữ dữ liệu**

Web crawling là kỹ thuật thu thập dữ liệu tự động từ các trang web. Đề tài dùng cloudscraper để vượt qua Cloudflare challenge của ITviec và Selenium cho nội dung dynamic của TopCV, BeautifulSoup cho HTML parsing, tuân thủ robots.txt cho mục đích nghiên cứu học thuật. JD được làm giàu bằng pipeline rule-based extractor (regex VN+EN) kết hợp tùy chọn LLM overlay (Groq llama-3.1-8b, pluggable provider hỗ trợ Ollama local) để trích xuất 8 trường: seniority, min/max_exp, degree, work_mode, skills_required/preferred, salary range. ChromaDB lưu embedding vector JD; PostgreSQL lưu structured fields cho time-series analytics.

**6. Dashboard và Data Visualization**

Dashboard cần trực quan hóa nhiều loại dữ liệu: time-series chart cho skill trend, gauge chart cho Freshness Score, network graph cho skill clustering, scatter quadrant cho Hidden Gems, heatmap cho skill × role. Đề tài sử dụng Recharts (cho chart kinh điển) kết hợp custom SVG (cho Skill Network Graph và Hidden Gems Quadrant). Nguyên tắc thiết kế dashboard của Few (2006) được tham khảo, bổ sung 3 nguyên tắc riêng cho analytics dashboard: insight-first naming, progressive disclosure, compare mode.

**IV. Phương pháp nghiên cứu**

**Tìm hiểu tài liệu:** Đọc các bài báo, paper liên quan đến Multi-criteria Decision Making, skill graph, learning path recommendation, NER song ngữ, temporal skill analysis từ các nguồn như ACL, RecSys, KSE, IJCAI, EMNLP. Xem xu hướng nghiên cứu hiện tại và xác định hướng tiếp cận phù hợp cho thị trường CNTT Việt Nam và audience sinh viên.

**Thu thập dữ liệu:** Viết crawler lấy JD từ ITviec (cloudscraper vượt Cloudflare) và TopCV (Selenium dynamic content), snapshot ~1.500 JD active trong 45 ngày. JD được parse qua pipeline rule-based extractor (regex VN+EN) kết hợp LLM overlay tùy chọn để trích xuất 8 trường structured. Lưu vào PostgreSQL (structured + time-series) và ChromaDB (semantic embeddings).

**Multi-criteria CV Freshness Score:** Đề xuất khung đánh giá 8 dimension với trọng số tinh chỉnh cho sinh viên CNTT (ưu tiên Project Quality 22%, Skill Freshness 18%, Education 12%, giảm Experience Depth xuống 10%). Validate bằng: (1) so sánh score giữa CV "tốt" và CV "yếu" tạo thủ công; (2) ablation study — bỏ từng dimension và đo độ thay đổi score; (3) consistency check — cùng CV qua nhiều version phải có score nhất quán.

**Learning Path Optimizer:** Cài đặt 3 thuật toán Greedy (ROI-based), Dijkstra (state-space search), Dynamic Programming (bitmask brute-force cho |candidates| ≤ 20). Tạo bộ benchmark 50 test cases có lời giải tối ưu được pre-compute. So sánh các thuật toán về (a) số JD unlock sau N tuần, (b) wall-clock runtime, (c) optimality gap so với DP.

**NER fine-tune:** Generate 1.000 CV synthetic IT bằng LLM (Llama 3.2 1B trên Colab T4), auto-label bằng rule-based annotator dựa trên dictionary skill 474 entries và regex patterns. Train BERT-base 20+ entity labels (PER, ORG, DATE, LOC, SKILL, DEGREE, MAJOR, JOB_TITLE, PROJECT, CERT,…) trên Google Colab. Đánh giá ba mức: (i) token-level F1 trên silver labels 200 mẫu (phát hiện tokenization mismatch); (ii) token-level F1 trên manual annotation 71 entities — đạt 0.86; (iii) span-level F1 trên 100 CV thủ công — đạt 0.74.

**Market Intelligence Dashboard:** Tổng hợp 33 insight đa chiều bằng SQL aggregation trên jd_raw, gồm 5 nhóm: Overview KPIs, Demand Analytics, Salary Insights, Temporal & Trend, Relationship Insights. Triển khai cache TTL 5 phút server-side. Validate bằng so chiếu với các báo cáo thị trường công khai (TopDev, ITviec annual report) cho các insight cơ bản.

**Xây dựng hệ thống:** Phát triển theo từng tuần (sprint ngắn). Các module độc lập tích hợp qua kiến trúc microservices (crawler_service, skill_service, ner_service, api_gateway .NET, frontend React) để có thể làm song song và test riêng từng phần.

**Đánh giá hệ thống:** Do giới hạn thời gian, đề tài không thực hiện user study quy mô lớn (≥20 người) — limitation tự nhiên được nêu rõ trong báo cáo. Thay vào đó, đánh giá hệ thống dựa trên: (1) benchmark định lượng 3 thuật toán Learning Path trên 50 test cases; (2) F1 NER trên test set thủ công; (3) accuracy pipeline JD extraction trên 99 gold labels; (4) demo case study với 3-5 CV thật để minh họa workflow end-to-end.

**V. Kết quả dự kiến**

Hệ thống CV Health Intelligence chạy được end-to-end với các thành phần:

**Sản phẩm phần mềm:**
- Pipeline crawl JD ITviec + TopCV (snapshot ~1.500 JD trong 45 ngày, hỗ trợ cron daily idempotent với UPSERT theo URL key)
- CV Health Dashboard: Freshness Score 8 dimension, Learning Path visualization, Skill alerts, Opportunity Window
- Market Intelligence Dashboard: 33 insight đa chiều (KPIs, Skill Premium, Velocity, Hidden Gems, Clustering, English Premium, Salary Curve, Network Graph, …)
- NER service: BERT fine-tune CV/JD song ngữ với 20+ entity labels
- Pluggable LLM extractor (Rule mặc định, Ollama/Groq tùy chọn) cho JD enrichment

**Phần đóng góp đo được:**

1. **Multi-criteria CV Freshness Framework** — 8 dimension với trọng số tinh chỉnh cho sinh viên CNTT. Validate qua: (a) ablation study đo độ ảnh hưởng từng dimension; (b) consistency check trên các phiên bản CV; (c) 3-5 case study CV thật minh họa workflow end-to-end.

2. **Bảng benchmark 3 thuật toán Learning Path Optimization** trên 50 test cases: kỳ vọng Greedy đạt ≥ 80% lời giải tối ưu của DP với độ phức tạp O(n) so với O(2^n); Dijkstra cho lời giải tối ưu tương đương DP với độ phức tạp thấp hơn trên skill graph thưa.

3. **Mô hình NER fine-tune cho CV/JD CNTT Việt Nam** — đạt F1 ≈ 0.86 trên test set thủ công 71 entities, F1 ≈ 0.74 trên span-level evaluation 100 CV synthetic. Per-entity breakdown chi tiết cho 9 entity types phổ biến (SKILL, ORG, DATE, JOB_TITLE, LOC, DEGREE, MAJOR, PER, CERT).

4. **Bộ dữ liệu skill demand cho thị trường CNTT Việt Nam** — ~1.500 JD thực với 30+ structured fields, đính kèm pipeline reproduce được. Có thể tái sử dụng cho các nghiên cứu tiếp theo về labor market analytics.

5. **Báo cáo Data Quality** — Layer 1 (completeness) và Layer 2 (validity) cho jd_raw, đo coverage và sanity checks trên từng nguồn. Layer 3 đo accuracy pipeline trích xuất trên 99 gold labels manual với 95% Wilson CI.

**Lưu ý phạm vi đánh giá:** Do giới hạn khung thời gian, đề tài không bao gồm user study quy mô lớn (≥20 người dùng) — limitation được nêu rõ trong báo cáo. Đánh giá hệ thống dựa trên các metric định lượng (F1, accuracy, optimality gap, runtime) thay vì SUS/usefulness rating chủ quan.

**VI. Đóng góp của đề tài**

Về mặt khoa học, đề tài có ba đóng góp chính:

1. **Multi-criteria CV Freshness Framework** — đề xuất khung đánh giá CV theo 8 chiều (Skill, Experience, Project, Education, Achievement, Language, Completeness, Market Alignment) cùng công thức tổng hợp định lượng mức độ cập nhật của CV so với thị trường tuyển dụng CNTT Việt Nam.

2. **Learning Path Optimizer với benchmark 3 thuật toán** — hình thức hóa bài toán tối ưu lộ trình học trên skill graph và so sánh thực nghiệm Greedy, Dijkstra, Dynamic Programming trên 50 test cases sinh viên CNTT, đo các tiêu chí: số JD unlock được, runtime, optimality gap.

3. **Market Intelligence Dashboard** — xây dựng dashboard phân tích thị trường tuyển dụng với 33 insight (top skill, salary distribution, work-mode trend, role demand) dựa trên dữ liệu snapshot ~1500 JD crawl từ ITviec và TopCV, hỗ trợ cross-source deduplication qua `job_group_id` và filter switch giữa nguồn ITviec/TopCV/cả hai.

Hỗ trợ cho ba đóng góp trên, đề tài đồng thời xây dựng **Bilingual Skill Extraction & Matching Pipeline** (NER mBERT song ngữ Việt-Anh + Ontology IT 500 entries + Cascade matching 3 tầng Exact/Ontology/SBERT) — đóng vai trò thành phần tiền xử lý CV/JD, đảm bảo input chất lượng cho cả ba đóng góp khoa học. Pipeline được đánh giá đa tầng (span-level F1 trên 100 CV, end-to-end cascade trên test suite) và trình bày chi tiết trong Chương 3.

Về mặt thực tiễn, hệ thống giải quyết một vấn đề mà các công cụ hiện có (ChatGPT, LinkedIn, TopCV) chưa làm được: coi CV như một tài liệu sống cần cập nhật theo thị trường, không phải file tĩnh viết một lần rồi để đó. Hệ thống có thể được triển khai tại Career Center của các trường đại học để hỗ trợ sinh viên CNTT Việt Nam theo dõi, cải thiện CV và định hướng học tập trong suốt quá trình học và đi tìm việc.

**VII. Cấu trúc đồ án**

**CHƯƠNG 1: Tổng quan**

1.1. Tình hình nghiên cứu trong và ngoài nước về đánh giá CV, learning path và market intelligence cho thị trường tuyển dụng CNTT

1.2. Lý do chọn đề tài và bối cảnh thực tiễn

1.3. Mục tiêu, nội dung, phương pháp nghiên cứu

&nbsp;&nbsp;&nbsp;&nbsp;1.3.1. Mục tiêu đề tài

&nbsp;&nbsp;&nbsp;&nbsp;1.3.2. Nội dung đề tài

&nbsp;&nbsp;&nbsp;&nbsp;1.3.3. Phương pháp nghiên cứu

1.4. Đối tượng và phạm vi đề tài

1.5. Đóng góp của đề tài

**CHƯƠNG 2: Cơ sở lý thuyết**

2.1. Multi-Criteria Decision Making và đánh giá CV đa tiêu chí

&nbsp;&nbsp;&nbsp;&nbsp;2.1.1. Bài toán đánh giá đa tiêu chí và hạn chế của single-score

&nbsp;&nbsp;&nbsp;&nbsp;2.1.2. Các phương pháp MCDM kinh điển (Weighted Sum, AHP, TOPSIS)

&nbsp;&nbsp;&nbsp;&nbsp;2.1.3. Ứng dụng MCDM vào đánh giá CV trong HR

2.2. Skill Graph và Learning Path Optimization — cơ sở toán học và thuật toán

&nbsp;&nbsp;&nbsp;&nbsp;2.2.1. Skill Graph: cấu trúc, các loại quan hệ và metadata

&nbsp;&nbsp;&nbsp;&nbsp;2.2.2. Hình thức hóa Learning Path Optimization

&nbsp;&nbsp;&nbsp;&nbsp;2.2.3. Thuật toán Greedy (ROI-based) và Budgeted Maximum Coverage

&nbsp;&nbsp;&nbsp;&nbsp;2.2.4. Thuật toán Dijkstra trên weighted skill graph

&nbsp;&nbsp;&nbsp;&nbsp;2.2.5. Dynamic Programming và lời giải tối ưu

2.3. Market Intelligence và phân tích nhu cầu thị trường tuyển dụng

&nbsp;&nbsp;&nbsp;&nbsp;2.3.1. Các phương pháp phân tích JD theo thời gian

&nbsp;&nbsp;&nbsp;&nbsp;2.3.2. Cross-source deduplication: bài toán và giải pháp hash-based

&nbsp;&nbsp;&nbsp;&nbsp;2.3.3. Information Dashboard Design cho thị trường tuyển dụng

2.4. Web Crawling và xử lý JD thực tế

&nbsp;&nbsp;&nbsp;&nbsp;2.4.1. Các phương pháp crawl web (HTTP request, Selenium, AJAX endpoint)

&nbsp;&nbsp;&nbsp;&nbsp;2.4.2. Xử lý Cloudflare bot protection (cloudscraper)

&nbsp;&nbsp;&nbsp;&nbsp;2.4.3. Pipeline parse JD: listing + detail enrichment

2.5. Pipeline tiền xử lý CV/JD: NER bilingual, Ontology, Sentence-BERT cascade

&nbsp;&nbsp;&nbsp;&nbsp;2.5.1. Named Entity Recognition và mô hình BERT đa ngôn ngữ (mBERT)

&nbsp;&nbsp;&nbsp;&nbsp;2.5.2. Skill Ontology và các quan hệ chuẩn hóa kỹ năng

&nbsp;&nbsp;&nbsp;&nbsp;2.5.3. Sentence-BERT và semantic similarity matching

&nbsp;&nbsp;&nbsp;&nbsp;2.5.4. Cascade Matching nhiều tầng: thiết kế và trade-off

2.6. Các công nghệ và công cụ sử dụng

&nbsp;&nbsp;&nbsp;&nbsp;2.6.1. Backend: FastAPI, PostgreSQL, ChromaDB

&nbsp;&nbsp;&nbsp;&nbsp;2.6.2. NLP/ML: HuggingFace Transformers, Sentence-Transformers

&nbsp;&nbsp;&nbsp;&nbsp;2.6.3. Frontend: React, Recharts, TailwindCSS

&nbsp;&nbsp;&nbsp;&nbsp;2.6.4. DevOps: Docker Compose, cron, APScheduler

**CHƯƠNG 3: Phân tích và Thiết kế hệ thống**

3.1. Phân tích yêu cầu hệ thống

&nbsp;&nbsp;&nbsp;&nbsp;3.1.1. Yêu cầu chức năng

&nbsp;&nbsp;&nbsp;&nbsp;3.1.2. Yêu cầu phi chức năng (real-time, freshness, scalability)

&nbsp;&nbsp;&nbsp;&nbsp;3.1.3. Phân tích các bài toán cần giải quyết

3.2. Thiết kế Multi-criteria CV Freshness Framework

&nbsp;&nbsp;&nbsp;&nbsp;3.2.1. 8 chiều đánh giá CV (Skill, Experience, Project, Education, Achievement, Language, Completeness, Market Alignment)

&nbsp;&nbsp;&nbsp;&nbsp;3.2.2. Công thức tổng hợp Freshness Score và phương pháp validate

3.3. Thiết kế Learning Path Optimizer

&nbsp;&nbsp;&nbsp;&nbsp;3.3.1. Hình thức hóa bài toán tối ưu trên skill graph

&nbsp;&nbsp;&nbsp;&nbsp;3.3.2. Thuật toán Greedy, Dijkstra và Dynamic Programming

&nbsp;&nbsp;&nbsp;&nbsp;3.3.3. Thiết kế bộ benchmark 50 test cases

3.4. Thiết kế pipeline crawl JD và cross-source deduplication (`job_group_id`)

3.5. Thiết kế Market Intelligence Dashboard với 33 insight (filter switch ITviec/TopCV/all)

3.6. Thiết kế Skill Extraction & Matching Pipeline (NER mBERT + Ontology 500 entries + Cascade 3 tầng)

&nbsp;&nbsp;&nbsp;&nbsp;3.6.1. NER mBERT fine-tune cho CV/JD song ngữ Việt-Anh

&nbsp;&nbsp;&nbsp;&nbsp;3.6.2. Skill Ontology IT 500 entries (REQUIRES, LEADS_TO, RELATED_TO, PART_OF)

&nbsp;&nbsp;&nbsp;&nbsp;3.6.3. Cascade Matching: Exact → Ontology → Sentence-BERT cosine

3.7. Thiết kế kiến trúc tổng thể và cơ sở dữ liệu

**CHƯƠNG 4: Xây dựng và Thực nghiệm hệ thống**

4.1. Môi trường phát triển và triển khai

4.2. Xây dựng JD Crawler ITviec + TopCV và pipeline cross-source dedup

4.3. Xây dựng Skill Extraction & Matching Pipeline và đánh giá đa tầng

&nbsp;&nbsp;&nbsp;&nbsp;4.3.1. Fine-tune mBERT cho NER song ngữ Việt-Anh

&nbsp;&nbsp;&nbsp;&nbsp;4.3.2. Đánh giá span-level NER trên 100 CV (per-entity F1)

&nbsp;&nbsp;&nbsp;&nbsp;4.3.3. Đánh giá end-to-end Cascade Matching trên test suite

4.4. Xây dựng Multi-criteria CV Freshness Engine và kết quả validate

4.5. Xây dựng Learning Path Optimizer và kết quả benchmark 3 thuật toán

4.6. Xây dựng Market Intelligence Dashboard (33 insight, filter switch nguồn)

4.7. Tích hợp frontend CV Health Dashboard end-to-end

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
| Tuần 1 (02/03–08/03) | Nhận đề tài, gặp GVHD xác định mục tiêu và phạm vi. Khảo sát nhu cầu thực tế của sinh viên CNTT Việt Nam. Tổng hợp tài liệu nền về skill graph và learning path recommendation. | |
| Tuần 2 (09/03–15/03) | Xây dựng đề cương chi tiết. Tổng hợp tài liệu nâng cao về MCDM và NER bilingual. Thiết kế kiến trúc tổng thể của hệ thống. | Nộp đề cương GVHD |
| Tuần 3 (16/03–22/03) | Chuẩn bị nền dữ liệu: sinh corpus CV synthetic Việt-Anh có kiểm soát, gán nhãn BIO bằng rule-based silver standard. Khởi tạo schema database PostgreSQL và ChromaDB. | |
| Tuần 4 (23/03–29/03) | Fine-tune mBERT cho NER CV/JD song ngữ. Bắt đầu xây dựng Skill Ontology IT (REQUIRES, LEADS_TO, RELATED_TO, PART_OF). | Infrastructure |
| Tuần 5 (30/03–05/04) | Hoàn thiện ontology (~500 entries). Implement Cascade Matching Engine 3 tầng (Exact → Ontology → SBERT) để chuẩn hóa kỹ năng giữa CV và JD. | |
| Tuần 6 (06/04–12/04) | Tích hợp pipeline tiền xử lý (NER + Cascade Matching) thành dịch vụ chung. Đánh giá đa tầng: span-level F1 trên 100 CV, end-to-end cascade trên test suite. | |
| Tuần 7 (13/04–19/04) | Hoàn thiện nền dữ liệu, kiểm thử pipeline tiền xử lý trên CV và JD mẫu. Viết Chương 1 báo cáo (tổng quan). | |
| Tuần 8 (20/04–26/04) | Xây dựng JD Crawler cho ITviec và TopCV (cloudscraper + AJAX endpoint). Triển khai cross-source dedup qua `job_group_id`. | |
| Tuần 9 (27/04–03/05) | Hoàn thiện crawler. Snapshot ~1500 JD và xây dựng pipeline structured extraction (min_exp, seniority, work_mode, degree). Viết Chương 2 báo cáo (cơ sở lý thuyết). | Snapshot JD |
| Tuần 10 (04/05–10/05) | Thiết kế **Multi-criteria CV Freshness Framework** với 8 chiều đánh giá (Skill, Experience, Project, Education, Achievement, Language, Completeness, Market Alignment). Bắt đầu implement CVFreshnessEngine. | Mốc trọng tâm |
| Tuần 11 (11/05–17/05) | Hoàn thiện CVFreshnessEngine. Validate khung 8 chiều: so sánh giữa 10 CV "cập nhật" và 10 CV "lỗi thời" tạo thủ công. Thiết kế bộ benchmark 50 test cases cho Learning Path Optimizer. | |
| Tuần 12 (18/05–24/05) | Implement **Learning Path Optimizer**: thuật toán Greedy (ROI) và Dijkstra trên skill graph có trọng số. Chạy thử trên benchmark, đánh giá kết quả ban đầu. | |
| Tuần 13 (25/05–31/05) | Implement thuật toán Dynamic Programming. Chạy benchmark đầy đủ so sánh 3 thuật toán trên 50 test cases (số JD unlock, runtime, optimality gap). Viết Chương 3 báo cáo. | |
| Tuần 14 (01/06–07/06) | Xây dựng API endpoints (`/health-score`, `/skill-alerts`, `/learning-path`, `/opportunity-window`). BackgroundTask recompute Freshness khi CV thay đổi. Setup cron job crawler daily trong Docker Compose. | |
| Tuần 15 (08/06–14/06) | Xây dựng **CV Health Dashboard** frontend: Freshness gauge 8 chiều, Learning Path visualization, Skill alert cards, Opportunity Window. Tích hợp end-to-end toàn hệ thống. | |
| Tuần 16 (15/06–21/06) | Xây dựng **Market Intelligence Dashboard** với 33 insight (top skill, salary distribution, work-mode trend, role demand, company-level analytics qua `COUNT(DISTINCT job_group_id)`). | Mốc Market Intel |
| Tuần 17 (22/06–28/06) | Phân tích và tổng hợp kết quả thực nghiệm. Viết Chương 4 báo cáo. Hoàn thiện Kết luận, Tài liệu tham khảo, Phụ lục. Kiểm tra tỷ lệ trùng lặp (≤ 30%). Sửa theo phản hồi GVHD. | |
| Tuần 18 (29/06–05/07) | Duyệt đồ án với GVHD. Chuẩn bị slide thuyết trình và demo hệ thống end-to-end. Bảo vệ đồ án tốt nghiệp. | Bảo vệ |

|     |     |     |
| --- | --- | --- |
| **Trưởng Bộ Môn**<br><br>**\[Tên Trưởng BM\]** | **Ý kiến của GVHD**<br><br>**\[Tên GVHD\]** | ……ngày….tháng….năm 2026<br><br>**Sinh viên thực hiện**<br><br>**\[Họ và tên sinh viên\]** |
