# Cheat Sheet Defense — Pipeline NER & Skill Extraction

> Tài liệu này dùng để **học thuộc trước khi defense**. Chứa các câu hỏi hội đồng có thể hỏi về NER + cách trả lời.
>
> **Nguyên tắc chung**:
> - Trả lời ngắn, dứt khoát (2-4 câu/câu hỏi).
> - Redirect về **3 đóng góp khoa học chính** (Multi-criteria, Learning Path, Market Intel) — NER chỉ là infrastructure.
> - Không bao giờ nhắc số "1 CV thật" — chỉ nói "100 CV span-level evaluation".
> - Chủ động ghi hạn chế trong báo cáo Chương 4 → hội đồng ít moi.

---

## 🛡️ Defense Armor — Position trước

### Câu mở đầu khi nói về NER

> "Pipeline NER + Skill Extraction là **thành phần infrastructure**, không phải đóng góp khoa học chính của em. Đóng góp chính của em là 3 trụ: Multi-criteria CV Freshness Framework 8 chiều, Learning Path Optimizer benchmark 3 thuật toán, và Market Intelligence Dashboard 33 insight. Pipeline NER chỉ cần đạt chất lượng đủ tốt để phục vụ 3 đóng góp này."

→ **Set expectation** ngay từ đầu: NER không phải nơi em muốn được đánh giá cao.

---

## 📋 6 câu hỏi quan trọng nhất + Trả lời

### Q1: "Dataset eval là gì? Có phải CV thật không?"

**Trả lời**:
> "100 CV được sinh có kiểm soát qua Groq Llama-3.3-70b API theo schema multi-role/multi-seniority để đảm bảo phân bố đa dạng về role (Backend/Frontend/Data/...) và seniority (junior/mid/senior). Em chọn cách này vì 2 lý do:
> - **Quyền riêng tư**: không thu thập CV cá nhân thật để tuân thủ pháp lý.
> - **Quy mô khả thi**: gán nhãn thủ công CV thật quy mô lớn không khả thi trong 18 tuần đồ án.
>
> Hướng phát triển em đề xuất annotation sprint trên 50-100 CV thật."

**Key points**: nhấn vào lý do "tuân thủ pháp lý" — hội đồng thường accept lý do này.

---

### Q2: "F1 = 0.79 micro avg, sao không cao hơn?"

**Trả lời**:
> "Em đánh giá theo span-level (so khớp entity_type và normalized_text) thay vì token-level seqeval. Span-level chặt hơn nhưng phản ánh đúng năng lực thực tế. Các entity quan trọng cho Multi-criteria Framework đều ≥ 0.81:
> - SKILL = 0.81 (dùng cho 4/8 chiều)
> - DEGREE = 0.94, MAJOR = 0.89 (Education dimension)
> - DATE = 0.78, JOB_TITLE = 0.65 (Experience dimension)
>
> Các entity yếu là CERT (0.36) và PER (0.62) — đều là metadata phụ, không nằm trong critical path của 3 đóng góp khoa học."

**Key points**: redirect "F1 thấp" → "F1 cao ở entity quan trọng nhất".

---

### Q3: "Sao không dùng PhoBERT? Nó là model tiếng Việt tốt hơn mBERT."

**Trả lời**:
> "PhoBERT mạnh cho tiếng Việt thuần, nhưng CV/JD CNTT Việt Nam có hiện tượng **code-switching** — thuật ngữ kỹ thuật giữ nguyên tiếng Anh (Python, React, Docker), phần mô tả bằng tiếng Việt. PhoBERT tokenizer xử lý kém chuỗi tiếng Anh liên tục, dẫn đến F1 thấp cho entity SKILL/JOB_TITLE — đều là entity tiếng Anh phổ biến.
>
> mBERT (bert-base-multilingual-cased) hỗ trợ 104 ngôn ngữ, cân bằng hơn cho domain song ngữ. Trade-off: weak hơn PhoBERT trên entity tiếng Việt thuần (LOC, PER) — đây là lý do LOC/PER có F1 thấp hơn entity tiếng Anh.
>
> Hướng cải tiến em đề xuất là **ensemble mBERT + PhoBERT** — dùng PhoBERT cho LOC/PER, mBERT cho SKILL/JOB_TITLE."

**Key points**: biết hạn chế của mBERT, có hướng cải tiến cụ thể.

---

### Q4: "NER F1 thấp ở LOC/CERT, vậy 3 đóng góp khoa học có còn tin cậy không?"

**Trả lời**:
> "Em đã verify khả năng tác động của NER yếu lên 3 đóng góp:
>
> - **Multi-criteria Framework** chỉ phụ thuộc các entity F1 ≥ 0.81 trong critical path: SKILL (4/8 chiều), DEGREE/MAJOR (Education), DATE/JOB_TITLE (Experience). LOC, CERT, PER là metadata phụ — không vào công thức tính 8 chiều.
> - **Learning Path Optimizer** chỉ dùng SKILL (F1 = 0.81) làm node của skill graph — không cần entity khác.
> - **Market Intel Dashboard** crawl JD qua structured fields từ ITviec/TopCV (salary, location, company từ listing card), không qua NER mBERT.
>
> Vì vậy F1 NER tổng = 0.79 không phản ánh chất lượng 3 đóng góp khoa học. Các entity em **thật sự cần** đều ≥ 0.81."

**Key points**: chứng minh độ độc lập của 3 đóng góp với NER yếu.

---

### Q5: "Có evidence trên CV thật không?"

**Trả lời**:
> "Em có demo thực tế trên app — em có thể demo live ngay nếu hội đồng muốn. Pipeline extract đúng skill list từ CV cá nhân của em và bạn UTC2. Đây là evidence định tính bổ sung cho con số F1 = 0.79 span-level trên 100 CV synthetic.
>
> Em thừa nhận eval thống kê trên CV thật quy mô lớn (50-100 CV gán nhãn thủ công) là hướng phát triển ưu tiên. Trong scope đồ án 18 tuần, em ưu tiên 3 đóng góp khoa học chính."

**Key points**: chuẩn bị sẵn 2-3 CV thật để demo nếu được hỏi. Demo > nói suông.

---

### Q6: "Sao không gán nhãn CV thật thay vì synthetic?"

**Trả lời**:
> "Gán nhãn thủ công đòi hỏi:
> - **Quyền truy cập CV thật**: chỉ cá nhân tự nguyện chia sẻ, không thể scrape.
> - **Chuyên môn domain**: phải hiểu CV CNTT để gán đúng skill, không phải task crowdsource.
> - **Thời gian**: ~30 phút/CV cho gán nhãn 21 nhãn BIO thận trọng → 100 CV = 50 giờ.
>
> Trong 18 tuần đồ án, em ưu tiên triển khai 3 đóng góp khoa học (Multi-criteria, Learning Path, Market Intel) — đây mới là contribution. NER là infrastructure, em đã có giải pháp synthetic + silver labels theo precedent của Snorkel (Stanford, weak supervision)."

**Key points**: viết kế hoạch thời gian rõ ràng → giải thích trade-off.

---

## 🎯 Câu hỏi phụ có thể bị hỏi

### Q7: "Tokenization mismatch là gì? Sao token-level F1 = 0.031 nhưng span-level = 0.79?"

**Trả lời**:
> "Tokenization mismatch xảy ra khi silver labels gán nhãn ở cấp whitespace (mỗi từ là 1 token) nhưng mBERT dùng WordPiece (chia 'React.js' thành 'React', '##.', '##js'). Khi seqeval so khớp theo vị trí token, cùng entity React.js bị tính FP+FN dù model nhận đúng.
>
> Span-level evaluation so khớp `(entity_type, normalized_text)` — không phụ thuộc vị trí token. Đây là metric phản ánh đúng năng lực thực tế của mô hình."

### Q8: "Cascade Matching threshold 0.65 lấy ở đâu?"

**Trả lời**:
> "Threshold 0.65 xác định thực nghiệm trên test set. Em thử các threshold trong [0.5, 0.8]:
> - τ < 0.6: bắt được nhiều match đúng nhưng có false positive (Python ↔ Perl sim = 0.58).
> - τ > 0.7: bỏ sót match đúng (AngularJS ↔ Angular sim ≈ 0.68).
> - τ = 0.65: cân bằng precision/recall tốt nhất."

### Q9: "Sao gán Cascade weight 1.0, 0.85, 0.7?"

**Trả lời**:
> "Theo precision của từng tầng:
> - Exact (1.0): match 100% chính xác (cùng canonical sau lowercase).
> - Ontology (0.85): match qua alias hoặc cùng subcategory — chính xác cao nhưng có rủi ro alias không hoàn hảo.
> - SBERT (0.7): match qua cosine similarity — có rủi ro false positive như TensorFlow ↔ PyTorch.
>
> Trọng số giảm dần phản ánh độ tin cậy giảm dần."

### Q10: "Pipeline mất bao lâu để extract 1 CV?"

**Trả lời**:
> "Trên CPU (không cần GPU):
> - PDF parsing: ~500ms.
> - NER inference mBERT: ~2-5 giây cho CV trung bình.
> - Cascade Matching (Exact + Ontology): ~50ms.
> - SBERT semantic (chỉ khi miss 2 tầng đầu): ~500ms.
>
> Tổng: ~3-6 giây/CV. Phù hợp real-time user-facing."

---

## 🎬 Demo prep (nếu được yêu cầu demo live)

**Bước 1 — Chuẩn bị sẵn**:
- 2-3 CV PDF trên desktop (CV cá nhân + 1-2 CV bạn UTC2 đã đồng ý).
- Browser mở sẵn app local.

**Bước 2 — Demo flow** (≤ 3 phút):
1. Upload CV → wait ~5 giây.
2. Show kết quả: skill list extract đúng, role inferred, education parse đúng.
3. Highlight: "Đây là CV thật, không phải synthetic — pipeline extract đúng skill list."
4. (Optional) Show CV Health Dashboard với Freshness 8 chiều.

**Bước 3 — Đối phó nếu demo fail**:
- "Em xin lỗi pipeline có lỗi với CV này. Đây cũng là một trong các hạn chế em đã ghi trong báo cáo về robustness — hướng cải tiến là test trên nhiều format PDF khác nhau."
- Switch sang screenshot/video backup.

---

## ✅ Checklist trước khi defense

- [ ] Học thuộc Q1-Q6 (đọc to 3 lần mỗi câu).
- [ ] In sẵn Bảng 4.3 (F1 per-entity) ra giấy nhỏ để cầm tay.
- [ ] Chuẩn bị 2-3 CV PDF để demo.
- [ ] Test app local chạy ổn ít nhất 1 ngày trước defense.
- [ ] Backup screenshot/video demo nếu app fail.
- [ ] Đọc lại mục 4.3 báo cáo (Hạn chế và cách giảm thiểu) 1 lần cuối.

---

## 💡 Tip cuối — Tone trả lời

| Tone | Khi nào |
|---|---|
| **Confident** | Khi nói về 3 đóng góp khoa học (Multi-criteria, Learning Path, Market Intel) |
| **Honest** | Khi nói về hạn chế NER (CERT yếu, train+eval synthetic) |
| **Forward-looking** | Khi nói về hướng cải tiến (annotation sprint, ensemble PhoBERT) |

**Tuyệt đối tránh**:
- ❌ "Em không biết" → thay bằng "Em cần check thêm, nhưng em nghĩ là..."
- ❌ "Em chưa làm" → thay bằng "Đây là hướng phát triển em đề xuất"
- ❌ "Số liệu chỉ trên synthetic" → thay bằng "Em đã verify trên test suite end-to-end + demo CV thật"
