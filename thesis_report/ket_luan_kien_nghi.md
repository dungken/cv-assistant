# Kết luận và Kiến nghị

## 1. Kết quả đạt được

Đề tài đã hoàn thành mục tiêu xây dựng hệ thống **CV Health Intelligence cho Sinh viên CNTT Việt Nam** trong khung thời gian 18 tuần với hai đóng góp khoa học chính cùng infrastructure pipeline hỗ trợ. Cụ thể:

### 1.1 Hai đóng góp khoa học chính

**Đóng góp 1 — Multi-criteria CV Freshness Framework** ([Chương 3.2](./chuong3/3.2_thiet_ke_freshness_score.md) + [Chương 4.4](./chuong4/4.4_multi_criteria_freshness.md)):
- Đề xuất khung đánh giá CV theo **8 chiều độc lập** (Skill, Experience, Project, Education, Achievement, Language, Completeness, Market Alignment) tổng hợp bằng Weighted Sum Model với trọng số theo seniority (junior/mid/senior).
- Cài đặt `MultiCriteriaFreshnessEngine` với đầy đủ 8 dim + Weighted Sum aggregation + API endpoint `/cv/freshness-multi` end-to-end.
- **Validate định lượng PASS cả 3 phương pháp** theo §3.2.5:
  - **PP1 — Fresh vs Stale**: $\Delta = +57.73$ điểm (vượt ngưỡng yêu cầu $\geq 20$), per-role separation PASS trên cả 5 role (Backend, Frontend, Data, DevOps, AI Engineer).
  - **PP2 — Cohen's d separation**: Multi-criteria 8 chiều đạt $d = 11.93$, vượt baseline Single Skill-only (9.47) và Random (0.08).
  - **PP3 — Monotonic build-up**: score đơn điệu tăng qua 8 bước thêm thành phần (16.28 → 69.44), không vi phạm tính chất T2.

**Đóng góp 2 — Market Intelligence Dashboard** ([Chương 3.4](./chuong3/3.4_thiet_ke_market_intel.md) + [Chương 4.5](./chuong4/4.5_market_intel.md)):
- Xây dựng dashboard với **34 insight** (vượt mục tiêu 33) trên snapshot **1.604 JD** thực crawl từ ITviec (974) và TopCV (630), tích lũy qua cron daily trong 43 ngày.
- **Cross-source deduplication** chặt qua `job_group_id = SHA1(lowercase_company|lowercase_title)` đảm bảo các số liệu company-level chính xác (`COUNT(DISTINCT job_group_id)`).
- **Filter switch** giữa nguồn ITviec/TopCV/cả hai + filter role group + seniority cho phép sinh viên tự khám phá.
- Performance < 200ms first call, < 1ms cached, đáp ứng yêu cầu real-time.

### 1.2 Infrastructure — Bilingual Skill Extraction & Matching Pipeline

Pipeline tiền xử lý CV/JD song ngữ ([Chương 3.5](./chuong3/3.5_thiet_ke_skill_extraction_pipeline.md) + [Chương 4.3](./chuong4/4.3_skill_extraction_eval.md)):
- **NER mBERT** fine-tune cho 21 nhãn BIO domain CV/JD CNTT, đạt **span-level F1 = 0.79** trên 100 CV evaluation (SKILL = 0.81, DEGREE = 0.94, MAJOR = 0.89 — các entity quan trọng trong critical path đều ≥ 0.81).
- **Skill Ontology IT 460 entries** thuộc 15 category với 4 quan hệ (REQUIRES, LEADS_TO, RELATED_TO, PART_OF) cho domain CNTT Việt Nam.
- **Cascade Matching 3 tầng** (Exact → Ontology → Sentence-BERT cosine, threshold $\tau = 0.65$) — nhanh, chính xác, fallback ngữ nghĩa khi cần.

### 1.3 Sản phẩm phần mềm end-to-end

- **2 Dashboard end-user** ([Chương 4.6](./chuong4/4.6_cv_health_dashboard.md)):
  - **CV Health Dashboard**: Freshness gauge 8 chiều, time-series chart, skill alerts, opportunity window — 4 widget song song, latency 600–900ms.
  - **Market Intelligence Dashboard**: 34 insight với filter switch nguồn.
- **5 microservices** ([Chương 3.6](./chuong3/3.6_thiet_ke_kien_truc.md)): API Gateway .NET 9, NER FastAPI, Skill FastAPI, Crawler FastAPI, Frontend React 19 + Vite + Tailwind + Recharts.
- **Crawler ổn định** với cron `@reboot` + daily 09:00 + stamp file idempotent, snapshot ~1.500 JD trong 43 ngày.
- **Reproducibility full**: 7 bước setup trên máy mới ([§4.1.7](./chuong4/4.1_moi_truong.md)) + 2 script validate (`validate_multi_freshness.py`, `dump_market_intel_stats.py`) tái lập mọi số liệu.

### 1.4 Đóng góp dữ liệu

- **Bộ dữ liệu skill demand cho thị trường CNTT Việt Nam** — 1.604 JD thực với 30+ structured fields, cross-source dedup, có thể tái sử dụng cho các nghiên cứu labor market analytics tiếp theo.
- **Báo cáo Data Quality 3 layer** ([Chương 4.2](./chuong4/4.2_jd_crawler.md)): completeness coverage (8/9 trường ≥ 45%, 6/9 ≥ 86%) + validity sanity checks + accuracy 99 gold labels với 95% Wilson CI.

## 2. Hạn chế của đề tài

Đề tài thẳng thắn nhận các hạn chế sau, đặt khung tham chiếu phù hợp cho hội đồng và người đọc:

**H1 — Không thực hiện user study chính thức.** Do hạn chế thời gian 18 tuần với nhân lực 1 sinh viên, đề tài tập trung đánh giá định lượng các thành phần kỹ thuật (Δ Fresh-Stale, Cohen's d, F1 NER, data quality) thay vì khảo sát người dùng quy mô lớn (≥ 20 người). User study là hạn chế tự nhiên của khung thời gian, không phải lựa chọn phương pháp.

**H2 — Validate Multi-criteria trên 20 CV synthetic, chưa có CV thật quy mô lớn.** Bộ 10 fresh + 10 stale do nhóm tự gán nhãn — đảm bảo control nhưng không đại diện đầy đủ độ đa dạng CV thật. Cohen's d = 11.93 trên synthetic không bằng chứng định lượng trên CV thật.

**H3 — NER train + eval trên CV synthetic.** 100 CV span-level evaluation do nhóm sinh có kiểm soát qua LLM (Groq Llama-3.3-70b), không phải CV thật của sinh viên. Lý do: quyền riêng tư + chi phí gán nhãn thủ công ~30 phút/CV cho 21 nhãn BIO. Demo trên CV thật (cá nhân + bạn UTC2) cho thấy pipeline hoạt động — nhưng đây là evidence định tính.

**H4 — Snapshot JD 43 ngày, chưa có time-series dài.** Đủ cho velocity 14d window nhưng chưa đủ phát hiện seasonal pattern (Tết, mùa tuyển sinh viên ra trường). Một số insight (skill_clusters = 1 cluster, outdated_skills = 0) chưa đủ tín hiệu vì window ngắn.

**H5 — Trọng số $\omega_d$ chưa khảo sát chuyên gia AHP.** Bảng 3.2 dựa intuition + hiệu chỉnh trên 20 CV, chưa qua pairwise comparison của recruiter chuyên nghiệp. Validate hiện đảm bảo framework phân biệt được fresh/stale, nhưng chưa đảm bảo trọng số phản ánh đúng góc nhìn nhà tuyển dụng.

**H6 — Salary coverage thấp (~28%).** Nhiều JD ẩn lương ("Sign in to view salary", "Thỏa thuận"). Đây là đặc thù dữ liệu nguồn, không phải lỗi pipeline. Hệ quả: một số insight salary-based (Skill Premium, English Premium) có $n$ mẫu nhỏ hơn ideal — đã ghi rõ trong từng insight.

**H7 — Cross-source dedup strict, có thể miss fuzzy match.** `job_group_id` dùng `(lowercase_company, lowercase_title)` exact — nếu công ty viết khác chính tả ("FPT" vs "FPT Software") sẽ không gộp. Trong snapshot hiện tại chỉ ~5 dup pair phát hiện được — số nhỏ vì đa số công ty đăng tập trung 1 nền tảng.

**H8 — Frontend test thủ công, không Jest/Playwright.** Trong scope DATN ưu tiên test backend (pytest) vì rủi ro chính nằm ở logic algorithm. Frontend được test thủ công qua browser.

**H9 — Authentication chưa hoàn thiện.** Hiện dùng `user_id` truyền trực tiếp qua query param thay vì JWT từ API Gateway. Ưu tiên backend logic trong scope DATN, OAuth flow đầy đủ chưa được wire.

## 3. Hướng phát triển

Các hướng phát triển dưới đây trực tiếp giải quyết hạn chế ở mục 2 hoặc mở rộng đề tài sang giai đoạn tiếp theo:

### 3.1 Mở rộng validate

- **HP1 — Annotation sprint 50-100 CV thật**: phối hợp với Career Center UTC2 thu thập CV tự nguyện từ sinh viên năm 3-4, gán nhãn thủ công 8 dim Freshness và 21 nhãn BIO NER → giải quyết H2 + H3 đồng thời.
- **HP2 — Validate Multi-criteria bằng AHP với chuyên gia**: khảo sát 20-30 recruiter CNTT Việt Nam, dùng pairwise comparison để re-estimate trọng số $\omega_d$ → giải quyết H5.
- **HP3 — User study 30-50 sinh viên**: đo SUS (System Usability Scale) + Task Success Rate cho 2 dashboard, A/B test 2 phiên bản trọng số → giải quyết H1.

### 3.2 Cải tiến pipeline kỹ thuật

- **HP4 — Ensemble mBERT + PhoBERT cho NER**: dùng PhoBERT cho LOC/PER (entity tiếng Việt thuần), mBERT cho SKILL/JOB_TITLE (code-switching) → cải thiện F1 toàn pipeline lên ~0.85+.
- **HP5 — LLM-based salary extractor**: dùng LLM (Groq, Ollama local) parse salary từ description khi structured field missing → nâng salary coverage từ 28% lên ~50%+.
- **HP6 — Fuzzy match cho cross-source dedup**: thêm canonicalization layer cho company name (alias mapping + Levenshtein distance threshold) → bắt thêm các dup pair với chính tả khác → giải quyết H7.
- **HP7 — Skill recommendation engine** (đề xuất thay thế Learning Path Optimizer): build simple ranking *"top 5 skill nên học tiếp"* dựa trên (coverage trong JD × trend × ROI / cost) thay vì NP-hard optimization. Phù hợp workflow học thực tế của sinh viên (1 skill tại 1 thời điểm, không cần "path 12 tuần").

### 3.3 Mở rộng scope

- **HP8 — Tích lũy time-series 12 tháng**: tiếp tục crawl 1 năm để phát hiện seasonal pattern (Tết, ra trường, năm tài chính) → giải quyết H4. Một số insight (skill clustering, outdated alert) tự động phong phú lên khi data tích lũy.
- **HP9 — Thêm nguồn JD mới**: VietnamWorks, Glassdoor VN, LinkedIn Jobs API → tăng diversity dataset và cross-validate insight. Architecture adapter pattern cho phép thêm nguồn dễ dàng.
- **HP10 — JD matching feature**: bổ sung endpoint `/jd-matching` chia JD active thành 3 nhóm theo ATS score (apply-ready ≥ 0.85 / near-ready 0.5–0.85 / far ≥ 0.5) — feature thực dụng cao cho sinh viên, complement Multi-criteria Freshness.
- **HP11 — Email digest hàng tuần**: tích hợp `EmailService.cs` (scaffold đã có ở API Gateway) gửi tóm tắt Freshness change + JD mới + skill alerts qua email — pattern push notification phổ biến của LinkedIn/Coursera.

### 3.4 Production-readiness

- **HP12 — JWT authentication full**: wire OAuth flow đầy đủ từ Gateway → tất cả services → giải quyết H9. Cho phép multi-user thật, không phải `user_id` truyền tay.
- **HP13 — Frontend test suite**: Jest cho component test + Playwright cho E2E flow upload-CV → dashboard render → giải quyết H8.
- **HP14 — Triển khai pilot tại Career Center UTC2**: deploy production cho 50-100 sinh viên trong 1 học kỳ → thu thập feedback thực + log behavior để hiệu chỉnh trọng số dashboard.

## 4. Lời cảm ơn

Đề tài hoàn thành nhờ sự hướng dẫn tận tình của Giảng viên hướng dẫn, sự hỗ trợ của Bộ môn Công nghệ Thông tin — Phân hiệu TP.HCM Trường Đại học Giao thông Vận tải, cùng các bạn UTC2 tình nguyện chia sẻ CV cá nhân cho mục đích demo. Em xin chân thành cảm ơn.

---

[← Chương 4: Xây dựng và Thực nghiệm](./chuong4/4.6_cv_health_dashboard.md) | [→ Tài liệu tham khảo](./tai_lieu_tham_khao.md)
