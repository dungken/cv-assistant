# Câu hỏi Hội đồng và Gợi ý Trả lời

> Đề tài: **"Nghiên cứu và ứng dụng NLP trong phát triển hệ thống AI tạo lập CV thông minh và tư vấn cá nhân hóa lộ trình nghề nghiệp"**

---

## I. Câu hỏi về Tổng quan và Động lực đề tài

---

**Q1. Tại sao chọn mBERT thay vì PhoBERT — vốn được thiết kế riêng cho tiếng Việt?**

**Trả lời:**
CV trong đề tài là **song ngữ Việt-Anh** — phần SKILL, JOB_TITLE, công nghệ thường viết bằng tiếng Anh; phần ORG, DEGREE, LOC hay viết bằng tiếng Việt. PhoBERT chỉ hỗ trợ tiếng Việt, tokenizer của nó không xử lý tốt chuỗi tiếng Anh liên tục. mBERT với vocabulary 119 ngôn ngữ xử lý tốt cả hai. Đây là lựa chọn pragmatic phù hợp với domain. Tuy nhiên, đề tài cũng nhận thấy hạn chế: với thực thể tiếng Việt thuần (địa danh, tên người), PhoBERT hoặc ensemble mBERT+PhoBERT sẽ tốt hơn — đây là hướng cải tiến đề xuất trong kết luận.

---

**Q2. Bộ dữ liệu hoàn toàn synthetic thì tính tin cậy của kết quả đến đâu?**

**Trả lời:**
Đây là hạn chế được nhóm thừa nhận rõ ràng trong báo cáo. Mô hình huấn luyện trên 480 CV synthetic và test trên dữ liệu synthetic tương tự — nên số F1 = 0.8633 phản ánh độ chính xác trên phân phối synthetic, không hoàn toàn là phân phối thực tế. Để đánh giá trung thực hơn, nhóm đã bổ sung hai đánh giá định tính: test thủ công trên 12 CV thực tế (ground truth annotated thủ công) và test bán tự động trên 100 CV qua Groq. Cả hai cho kết quả khả quan với SKILL đạt mức tốt. Hướng khắc phục là annotation sprint với 50–100 CV thực dùng Label Studio — được đề xuất là ưu tiên cao nhất trong kiến nghị.

---

**Q3. Hệ thống giải quyết bài toán gì mà các tool hiện có (LinkedIn, TopCV) chưa làm được?**

**Trả lời:**
Ba điểm khác biệt chính:
1. **Tiếng Việt native**: các ATS thương mại tối ưu cho tiếng Anh, CV tiếng Việt thường bị parse sai cấu trúc.
2. **Tích hợp end-to-end miễn phí**: LinkedIn Premium và TopCV Pro tính phí; hệ thống này có thể deploy tại Career Center trường đại học phục vụ sinh viên miễn phí.
3. **Cá nhân hóa theo profile**: chatbot nhận diện CV của từng user (qua User Memory Service) và đưa ra gợi ý cụ thể theo gap kỹ năng — không phải gợi ý generic.

---

## II. Câu hỏi về Kỹ thuật NER

---

**Q4. F1 = 0.031 trên silver labels mà F1 = 0.8633 trên manual annotation — chênh lệch quá lớn, giải thích thế nào?**

**Trả lời:**
Silver labels được tạo bằng **rule-based annotator ở cấp word** (phân tách theo whitespace). mBERT dùng **WordPiece tokenizer ở cấp subword** — cùng văn bản nhưng tạo ra chuỗi token hoàn toàn khác nhau về độ dài và ranh giới. seqeval dùng exact span match theo vị trí token, nên dù mô hình nhận diện đúng thực thể (ví dụ `React.js`) nhưng span boundary lệch vài character là tính FP+FN. Đây là **tokenization mismatch**, không phải mô hình kém. Manual annotation khắc phục bằng cách so sánh `(entity_type, normalized_text)` thay vì vị trí token — kết quả phản ánh đúng năng lực thực sự của mô hình.

---

**Q5. Tại sao LOC có F1 = 0.0 — địa danh tưởng đơn giản?**

**Trả lời:**
Hai nguyên nhân cộng hưởng:
1. **Nhầm lẫn PER ↔ LOC**: mBERT không có ngữ cảnh section, một số tên người Việt (ví dụ "An", "Bình") giống tên địa danh, mô hình bị confused.
2. **Tập test thủ công nhỏ** (chỉ ~20 instance LOC) — chỉ cần vài false positive là F1 về 0. Đây là vấn đề phổ biến trong NER tiếng Việt, được ghi nhận trong nghiên cứu VLSP.

Giải pháp: thêm dữ liệu gán nhãn thực tế, hoặc dùng PhoBERT vốn được pre-train trên văn bản tiếng Việt phong phú hơn cho thực thể địa danh.

---

**Q6. BIO tagging là gì, tại sao dùng BIO mà không dùng IO hoặc BIOES?**

**Trả lời:**
- **IO**: chỉ có Inside/Outside — không phân biệt được hai thực thể liền kề cùng loại.
- **BIO**: thêm B (Beginning) — phân biệt được ranh giới đầu span. Đây là chuẩn phổ biến nhất, cân bằng giữa đơn giản và hiệu quả.
- **BIOES**: thêm E (End) và S (Single) — phân biệt tốt hơn nhưng tăng số lớp gấp đôi, cần nhiều dữ liệu hơn để học.

Với bộ dữ liệu 600 CV synthetic và domain CV/JD nơi phần lớn span ngắn (1–3 token), BIO là lựa chọn hợp lý. Nhóm dùng 21 nhãn BIO (7 loại thực thể × B/I/O).

---

**Q7. Training logs bị mất — làm sao biết mô hình không bị overfit?**

**Trả lời:**
Đây là hạn chế được thừa nhận trong báo cáo. Không có loss curve để phân tích. Bằng chứng gián tiếp về việc không overfit nghiêm trọng:
1. Model được test trên 12 CV thực tế (domain shift so với synthetic training data) và vẫn hoạt động tốt với SKILL.
2. Test bán tự động trên 100 CV qua Groq cũng cho kết quả consistent.

Tuy nhiên, nhóm không thể khẳng định chắc chắn. Giải pháp đề xuất là dùng MLflow/Weights&Biases cho mọi experiment về sau — bài học rút ra về MLOps.

---

## III. Câu hỏi về Skill Matching

---

**Q8. Tại sao Skill Matching đạt 100% accuracy — có phải bộ test quá dễ không?**

**Trả lời:**
100% trên 10 test cases thủ công xác nhận logic cascade hoạt động đúng đắn, nhưng nhóm thừa nhận đây chưa phải bằng chứng thuyết phục về accuracy trên phân phối thực tế. Bộ test được thiết kế để cover các tình huống quan trọng nhất: exact match, synonym trong ontology, semantic match qua SBERT. 10 cases chỉ là smoke test. Đây là hạn chế được ghi rõ, hướng cải thiện là xây dựng bộ test lớn hơn và đa dạng hơn từ dữ liệu tuyển dụng thực.

---

**Q9. Cascade matching 3 tầng hoạt động thế nào? Tại sao không dùng semantic matching ngay từ đầu?**

**Trả lời:**
Ba tầng theo thứ tự ưu tiên:
1. **Exact match**: so khớp string chính xác sau lowercase và normalize — nhanh nhất, chính xác nhất.
2. **Ontology match**: tra cứu trong bảng synonym ~500 entries (ví dụ `JS` → `JavaScript`, `ReactJS` → `React`) — xử lý được alias phổ biến.
3. **Semantic match (SBERT)**: encode cả skill CV và skill JD thành vector, cosine similarity > threshold — bắt được các diễn đạt khác nhau về cùng khái niệm.

Không dùng semantic ngay từ đầu vì: (1) SBERT inference chậm hơn lookup O(1); (2) semantic matching có false positive — "Python" và "Perl" có thể có cosine similarity cao vì đều là programming language. Cascade ưu tiên độ chính xác cao, chỉ fallback semantic khi cần.

---

**Q10. Ontology 500 entries — lấy từ đâu và cập nhật thế nào?**

**Trả lời:**
Ontology được xây dựng bằng cách kết hợp ba nguồn: ESCO (European Skills framework), O\*NET (US occupational database), và dữ liệu tuyển dụng từ ITviec/TopCV để bổ sung các term đặc thù thị trường Việt Nam (ví dụ cách viết tắt tiếng Việt của các framework). Hiện tại cập nhật thủ công — đây là hạn chế. Hướng cải tiến là pipeline tự động: crawl JD mới → extract term tần suất cao → human review → merge vào ontology.

---

## IV. Câu hỏi về Chatbot RAG

---

**Q11. RAG khác gì so với chỉ dùng LLM thông thường? Tại sao cần RAG?**

**Trả lời:**
LLM thuần (như GPT-4) trả lời dựa trên kiến thức training — **không biết** thông tin trong CV của user cụ thể và có thể **hallucinate** thông tin nghề nghiệp không chính xác. RAG (Retrieval-Augmented Generation) giải quyết bằng cách:
1. **Retrieval**: trước khi generate, tìm kiếm trong knowledge base (ChromaDB vector store) các đoạn văn bản liên quan nhất đến câu hỏi.
2. **Augmentation**: đưa các đoạn retrieved này vào prompt cùng với CV của user.
3. **Generation**: LLM generate câu trả lời dựa trên context cụ thể — có grounding, ít hallucinate.

Trong hệ thống này, knowledge base gồm career guides từ O\*NET và thông tin profile CV của user — đảm bảo tư vấn cá nhân hóa và có cơ sở thực tế.

---

**Q12. Tại sao dùng cả Ollama local lẫn Groq Cloud — hai LLM để làm gì?**

**Trả lời:**
Dual LLM phục vụ hai mục đích khác nhau:
- **Ollama local (Qwen2.5:3b)**: chạy offline, không cần internet, không tốn API cost — phù hợp cho development và demo môi trường không có kết nối.
- **Groq Cloud (Llama-3.3-70b)**: inference cực nhanh (token/s cao gấp 10–20 lần), mô hình lớn hơn nhiều → câu trả lời chất lượng cao hơn — phù hợp cho production và demo chính thức.

Kiến trúc cho phép switch giữa hai backend qua config, không cần thay code.

---

**Q13. Làm sao đánh giá chất lượng chatbot nếu không có user study?**

**Trả lời:**
Hiện tại chỉ có đánh giá định tính qua demo — đây là hạn chế được thừa nhận. Để đánh giá định lượng đúng nghĩa cần:
1. **RAGAS framework**: đo faithfulness (câu trả lời có bám vào retrieved context không?), answer relevancy, context precision/recall.
2. **User study**: ít nhất 30 người dùng thực (sinh viên/kỹ sư CNTT) rating chất lượng câu trả lời theo thang Likert.

Đây là hướng cải tiến ưu tiên cao trong kiến nghị. Demo định tính cho thấy hệ thống cung cấp câu trả lời được cá nhân hóa và có grounding từ knowledge base — nhưng chưa đủ để là bằng chứng khoa học.

---

## V. Câu hỏi về Kiến trúc Hệ thống

---

**Q14. Tại sao chọn microservices thay vì monolith — hệ thống nghiên cứu cần gì?**

**Trả lời:**
Ba lý do cụ thể cho domain này:
1. **Ngôn ngữ khác nhau**: AI/ML services cần Python (PyTorch, HuggingFace); API Gateway phù hợp ASP.NET Core C# cho auth và routing; Frontend React. Microservices cho phép mỗi service dùng ngôn ngữ tối ưu.
2. **Scale độc lập**: NER service nặng hơn (cần GPU) có thể scale riêng mà không scale toàn bộ hệ thống.
3. **Fault isolation**: chatbot service chậm không kéo chết NER service.

Nhược điểm là phức tạp hơn monolith. Nhưng vì đây cũng là nghiên cứu về kiến trúc hệ thống AI, microservices là lựa chọn phù hợp với mục tiêu học thuật.

---

**Q15. API Gateway dùng JWT authentication — cơ chế bảo mật thế nào?**

**Trả lời:**
JWT (JSON Web Token) hoạt động như sau:
1. User đăng nhập → API Gateway xác thực credential → issue JWT token có chữ ký (HMAC-SHA256).
2. Mọi request tiếp theo gửi kèm JWT trong Authorization header.
3. API Gateway verify signature và expiry trước khi forward request đến internal services.
4. Internal services (NER, Skill, Chatbot) không cần xác thực lại — chỉ API Gateway là điểm vào duy nhất.

Pattern này là **single point of security** — đơn giản hơn việc mỗi service tự xác thực.

---

**Q16. Docker Compose deploy một lệnh — thực tế có hoạt động không, latency thế nào?**

**Trả lời:**
Có, toàn bộ 9 services (API Gateway, NER, Skill Matching, Chatbot, Career, User Memory, ChromaDB, PostgreSQL, Frontend) được định nghĩa trong `docker-compose.yml` và deploy bằng `docker compose up`. Đã test thành công trên môi trường development.

Về latency trong môi trường không có GPU:
- NER inference: ~2–5 giây (mBERT trên CPU).
- Skill Matching: < 500ms (ontology lookup + SBERT).
- Chatbot với Ollama local: 10–30 giây (LLM 3B trên CPU) — chưa đạt production-ready.
- Chatbot với Groq Cloud: ~2–3 giây — chấp nhận được.

---

## VI. Câu hỏi về Dữ liệu

---

**Q17. Sinh 600 CV synthetic bằng Qwen2.5-1.5B — quality control thế nào?**

**Trả lời:**
Pipeline sinh dữ liệu có 3 lớp quality control:
1. **Template có cấu trúc**: prompt yêu cầu output JSON với các field bắt buộc (SKILL, JOB_TITLE, EDUCATION, EXPERIENCE) — đảm bảo schema nhất quán.
2. **Scoring tự động**: mỗi CV được tính `quality_score` dựa trên số section đầy đủ, số kỹ năng, độ dài — CV dưới ngưỡng bị loại. Kết quả: quality_score trung bình 0.97/1.0.
3. **Manual spot-check**: nhóm review ngẫu nhiên ~50 CV để verify văn phong và tính hợp lý.

Không có CV nào trong training data là CV thực của người thật — đảm bảo privacy.

---

**Q18. Tại sao không crawl CV thực từ LinkedIn hay TopCV?**

**Trả lời:**
Ba lý do:
1. **Terms of Service**: LinkedIn và TopCV cấm scraping trong ToS — vi phạm có thể dẫn đến legal issues.
2. **Privacy**: CV chứa thông tin cá nhân nhạy cảm — thu thập mà không có consent vi phạm quyền riêng tư và có thể vi phạm PDPD (Nghị định bảo vệ dữ liệu cá nhân của Việt Nam).
3. **Annotation cost**: 600 CV thực cần ~300 giờ annotation thủ công — không khả thi trong phạm vi đề tài sinh viên.

Synthetic data là giải pháp thực tế và hợp pháp cho nghiên cứu học thuật.

---

## VII. Câu hỏi về Kết quả và Đánh giá

---

**Q19. So với các công trình quốc tế, kết quả của đề tài đứng ở đâu?**

**Trả lời:**
So sánh trực tiếp:
- **ResumeNet** (BERT, CV tiếng Anh, dataset lớn hơn): F1 = 0.90
- **Đề tài** (mBERT, CV song ngữ Việt-Anh, 480 CV synthetic): F1 = 0.8633

Chênh lệch 0.04 F1 trên bài toán khó hơn (song ngữ, dữ liệu ít hơn, không GPU chuyên dụng) — là kết quả cạnh tranh và hợp lý. Quan trọng hơn, thực thể SKILL đạt F1 = 0.9157 — cao hơn cả ResumeNet trên thực thể quan trọng nhất của domain.

---

**Q20. ATS score 8 tiêu chí — cách tính thế nào, có cơ sở khoa học không?**

**Trả lời:**
8 tiêu chí ATS được thiết kế dựa trên tổng hợp từ tài liệu HR và các ATS thương mại phổ biến (Greenhouse, Lever, Workday). Các tiêu chí gồm: skill match rate, keyword density, format compliance, section completeness, experience level match, education match, certification bonus, và length score. Mỗi tiêu chí có trọng số, tổng hợp thành điểm 0–100.

Hạn chế: trọng số được set theo heuristic, chưa được calibrate qua dữ liệu thực từ nhà tuyển dụng. Đây là điểm cần cải thiện — ideally nên train regression model trên feedback của recruiter thực.

---

**Q21. Hệ thống xử lý CV tiếng Anh tốt hơn hay tiếng Việt tốt hơn?**

**Trả lời:**
Tiếng Anh tốt hơn, đặc biệt với SKILL. Lý do: phần lớn CV trong tập training là tiếng Anh hoặc code-switching Anh-Việt với SKILL viết bằng tiếng Anh. mBERT cũng có vocabulary tiếng Anh phong phú hơn tiếng Việt. Thực thể LOC (tiếng Việt) và PER (tên Việt) là hai điểm yếu nhất — consistent với hạn chế của mBERT trên tiếng Việt so với PhoBERT.

---

## VIII. Câu hỏi về Hướng phát triển

---

**Q22. Nếu có thêm 6 tháng, nhóm sẽ cải tiến gì trước tiên?**

**Trả lời:**
Theo thứ tự ưu tiên:
1. **Annotation sprint** (1–2 tháng): thu thập 50–100 CV thực với consent, gán nhãn thủ công bằng Label Studio — cải thiện NER đặc biệt với LOC/ORG.
2. **User study** (1 tháng): 30+ sinh viên/kỹ sư đánh giá chatbot và giao diện — có evidence định lượng.
3. **RAGAS evaluation pipeline** (2 tuần): tự động đánh giá chatbot mỗi khi thay đổi knowledge base hoặc LLM.
4. **PhoBERT ensemble** (1 tháng): kết hợp mBERT và PhoBERT cho NER, đặc biệt cải thiện thực thể tiếng Việt.

---

**Q23. Hệ thống có thể mở rộng sang domain khác (y tế, luật) không?**

**Trả lời:**
Kiến trúc có thể mở rộng nhưng cần effort đáng kể:
- **NER model**: phải fine-tune lại với dữ liệu domain mới — nhãn thực thể khác nhau hoàn toàn.
- **Skill ontology**: phải xây dựng lại cho domain mới.
- **Knowledge base**: phải thay thế career guides CNTT bằng tài liệu domain mới.

API Gateway và kiến trúc microservices có thể tái sử dụng. Về mặt nghiên cứu, pipeline NER → Matching → RAG là pattern tổng quát áp dụng được cho nhiều domain — đây là đóng góp về mặt kiến trúc của đề tài.

---

**Q24. Hệ thống có phụ thuộc vào internet không — nếu Groq API down thì sao?**

**Trả lời:**
Hệ thống được thiết kế có fallback:
- **Chatbot**: primary là Groq Cloud, fallback tự động về Ollama local khi Groq không khả dụng.
- **NER và Skill Matching**: chạy hoàn toàn local, không phụ thuộc internet.
- **ATS Scoring**: tính toán local dựa trên output của NER và Skill Matching.

Chỉ CV Builder (gọi LLM để rewrite bullet points) mới phụ thuộc vào Groq. Với Ollama local, hệ thống có thể vận hành hoàn toàn offline — phù hợp cho deploy tại trường đại học không muốn phụ thuộc cloud.

---

## IX. Câu hỏi Phản biện Thường gặp

---

**Q25. Đây chỉ là ghép nhiều thư viện có sẵn lại — đóng góp mới của đề tài là gì?**

**Trả lời:**
Đóng góp không nằm ở việc inventing thuật toán mới mà ở ba thứ:
1. **Bộ dữ liệu**: 600 CV/JD synthetic song ngữ Việt-Anh với quality_score 0.97 — chưa có bộ dữ liệu public tương đương cho CNTT Việt Nam. Có thể release cho cộng đồng nghiên cứu.
2. **Ontology kỹ năng IT Việt Nam**: ~500 entries được curate cho thị trường Việt Nam — tài nguyên không tồn tại trước đó.
3. **Hệ thống end-to-end**: tích hợp NER + Skill Matching + RAG thành pipeline hoàn chỉnh với kiến trúc production-ready — các công trình liên quan thường chỉ giải quyết một trong ba bài toán này.

Trong nghiên cứu kỹ thuật ứng dụng, "ghép tốt" các công cụ có sẵn thành hệ thống hoạt động được và có đóng góp thực tiễn là perfectly valid contribution.

---

**Q26. Kết quả 100% Skill Matching trên 10 test cases có ý nghĩa gì khi sample quá nhỏ?**

**Trả lời:**
Đồng ý với nhận xét của hội đồng — 10 test cases là quá nhỏ để kết luận tổng quát. Nhóm trình bày kết quả này như **proof of concept** rằng logic cascade hoạt động đúng đắn trên các tình huống thiết kế, không phải như bằng chứng statistical significance. Báo cáo cũng ghi rõ hạn chế này. Để có con số có ý nghĩa thống kê, cần ít nhất 200–500 test cases từ dữ liệu tuyển dụng thực — đây là hướng kiến nghị ưu tiên.

---

**Q27. Tại sao không dùng spaCy pipeline đã được tối ưu sẵn cho NER thay vì fine-tune mBERT?**

**Trả lời:**
spaCy có NER model tốt cho tiếng Anh, nhưng model tiếng Việt của spaCy hạn chế và không có model cho CV domain. mBERT fine-tuned trên CV data cho phép:
1. **Domain adaptation**: học các pattern đặc thù CV (ví dụ "5+ years experience in React" — spaCy generic NER có thể miss "React" là SKILL).
2. **Custom entity types**: nhóm cần 7 entity types đặc thù (SKILL, JOB_TITLE, CERT...) mà spaCy generic không có.
3. **Song ngữ**: mBERT xử lý Việt-Anh tốt hơn spaCy Vietnamese model.

spaCy phù hợp cho production NLP pipeline generic, mBERT fine-tune phù hợp cho domain-specific research — đây là đúng lựa chọn.

---

*Tài liệu này được tổng hợp từ nội dung báo cáo nghiên cứu khoa học. Các con số và số liệu trích dẫn từ báo cáo gốc.*
