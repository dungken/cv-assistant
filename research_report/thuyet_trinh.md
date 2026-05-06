# Script Thuyết Trình — NCKH 2025–2026

> **Đề tài:** Nghiên cứu và ứng dụng xử lý ngôn ngữ tự nhiên trong phát triển hệ thống AI tạo lập CV thông minh và tư vấn cá nhân hóa lộ trình nghề nghiệp
> **Giảng viên hướng dẫn:** KS. Trần Quốc Khánh

---

## SLIDE 1 — Trang bìa

> *(Người trình bày chào hội đồng, giới thiệu nhóm)*

Kính thưa hội đồng, thưa thầy Trần Quốc Khánh cùng quý thầy cô.

Hôm nay nhóm chúng em xin được báo cáo tổng kết đề tài nghiên cứu khoa học sinh viên năm học 2025–2026 với tên đề tài: **"Nghiên cứu và ứng dụng xử lý ngôn ngữ tự nhiên trong phát triển hệ thống AI tạo lập CV thông minh và tư vấn cá nhân hóa lộ trình nghề nghiệp"**.

Thời gian trình bày của nhóm là khoảng 15–20 phút, sau đó xin kính mời hội đồng đặt câu hỏi.

---

## SLIDE 2 — Danh sách thành viên

> *(Điểm tên từng thành viên và phân công nhiệm vụ)*

Nhóm nghiên cứu gồm các thành viên. Mỗi người phụ trách một mảng kỹ thuật riêng, nhưng toàn bộ nhóm đều tham gia thảo luận kiến trúc và phân tích kết quả chung.

---

## SLIDE 3 — Đặt vấn đề & Lý do chọn đề tài

> *(Trình bày bức tranh thực trạng, dẫn dắt vào vấn đề)*

Thưa hội đồng, chúng ta hãy bắt đầu bằng một bức tranh thực tế.

Theo báo cáo của TopCV và ITviec năm 2025, Việt Nam cần bổ sung hơn **150.000 nhân lực CNTT mỗi năm** trong giai đoạn 2025–2027. Tuy nhiên, nghịch lý là dù thị trường thiếu hụt nhân lực, rất nhiều ứng viên vẫn không thể vượt qua vòng lọc hồ sơ đầu tiên.

Nguyên nhân cốt lõi là **hạn chế của các hệ thống ATS hiện tại**. Các công cụ ATS phổ biến như Workday hay Greenhouse được tối ưu hoàn toàn cho tiếng Anh. Khi xử lý CV tiếng Việt hoặc CV song ngữ — kiểu CV rất phổ biến của lập trình viên Việt Nam viết tên công nghệ bằng tiếng Anh xen lẫn mô tả bằng tiếng Việt — các hệ thống này hầu như không hiểu được ngữ nghĩa, dẫn đến lọc sai ứng viên phù hợp.

Bên cạnh đó, ứng viên không có công cụ để tự đánh giá mức độ phù hợp giữa CV của mình với yêu cầu tuyển dụng, và không có hệ thống tư vấn lộ trình nghề nghiệp cá nhân hóa phù hợp với thị trường Việt Nam.

**Giải pháp mà nhóm đề xuất** là ứng dụng NLP và mô hình ngôn ngữ lớn để giải quyết đồng thời ba bài toán này trong một hệ thống thống nhất.

---

## SLIDE 4 — Mục tiêu nghiên cứu

> *(Nêu rõ 3 mục tiêu cụ thể, liên kết với từng module hệ thống)*

Từ bài toán đặt ra, nhóm xác định ba mục tiêu cụ thể.

**Mục tiêu thứ nhất:** Xây dựng mô hình NER — Named Entity Recognition — để trích xuất thông tin từ CV và JD song ngữ. Cụ thể là nhận diện các thực thể như kỹ năng, vị trí công việc, học vấn, tổ chức, thời gian và địa điểm.

**Mục tiêu thứ hai:** Phát triển công cụ so khớp kỹ năng — Skill Matching — để tính điểm ATS và chỉ ra các kỹ năng còn thiếu khi so sánh CV với JD.

**Mục tiêu thứ ba:** Triển khai Chatbot tư vấn nghề nghiệp sử dụng kiến trúc RAG, cung cấp gợi ý cá nhân hóa dựa trên thông tin CV và JD của từng người dùng cụ thể, thay vì tư vấn chung chung.

Ba mục tiêu này cũng chính là ba tầng của pipeline hệ thống: trích xuất — phân tích — tư vấn.

---

## SLIDE 5 — Cơ sở công nghệ & Kiến trúc hệ thống *(phần văn bản)*

> *(Giới thiệu stack công nghệ trước khi sang slide sơ đồ)*

Để hiện thực hóa ba mục tiêu trên, nhóm lựa chọn các công nghệ sau.

Về **mô hình NLP**, nhóm sử dụng mBERT — mô hình BERT đa ngữ — cho bài toán NER, và Sentence-BERT cho bài toán so khớp ngữ nghĩa kỹ năng. Lý do chọn mBERT thay vì PhoBERT là vì CV ngành CNTT thường là song ngữ Việt-Anh, mBERT xử lý đồng thời cả hai ngôn ngữ mà không cần dữ liệu đơn ngữ riêng.

Về **LLM**, nhóm tích hợp hai lựa chọn: Qwen2.5 chạy local qua Ollama cho chế độ offline, và Llama 3.3 70B qua Groq Cloud cho chế độ cloud có hiệu năng cao hơn. Người dùng có thể chuyển đổi giữa hai chế độ tùy điều kiện.

Về **RAG Framework**, nhóm dùng LlamaIndex để quản lý pipeline retrieval và ChromaDB làm vector database lưu trữ knowledge base nghề nghiệp.

Về **kiến trúc tổng thể**, hệ thống được xây dựng theo mô hình **microservices gồm 9 thành phần độc lập**: API Gateway bằng ASP.NET Core 9, Frontend bằng React 18, và 4 Python services phục vụ NER, Skill Matching, Career, và Chatbot.

---

## SLIDE 6 — Cơ sở công nghệ & Kiến trúc hệ thống *(sơ đồ)*

> *(Chỉ vào từng thành phần trên sơ đồ kiến trúc microservices)*

Đây là sơ đồ kiến trúc toàn bộ hệ thống.

Mọi request từ Frontend React đều đi qua **API Gateway ASP.NET Core** — đây là điểm vào duy nhất, chịu trách nhiệm xác thực JWT, routing, và rate limiting. Từ đây, API Gateway proxy request đến đúng service phù hợp.

**NER Service** trên cổng 5001 nhận file CV và trả về danh sách thực thể. **Skill Service** trên cổng 5002 thực hiện matching và tính ATS score. **Career Service** trên cổng 5003 cung cấp thông tin lộ trình nghề nghiệp từ O*NET. **Chatbot Service** trên cổng 5004 là service phức tạp nhất, tích hợp RAG với LlamaIndex và ChromaDB.

Toàn bộ hệ thống được container hóa bằng Docker và có thể khởi động bằng một lệnh `docker-compose up` duy nhất.

---

## SLIDE 7 — Sinh dữ liệu & Huấn luyện mô hình NER *(vấn đề & giải pháp)*

> *(Giải thích rõ vì sao phải sinh dữ liệu tổng hợp)*

Thưa hội đồng, một trong những thách thức lớn nhất của đề tài là **bài toán dữ liệu**.

Để huấn luyện mô hình NER cần có văn bản CV đã được gán nhãn ở cấp độ token. Nhưng không tồn tại bộ dữ liệu CV tiếng Việt có nhãn NER nào được công bố công khai. Và việc thu thập CV thực tế vừa vi phạm Nghị định 13/2023 về bảo vệ dữ liệu cá nhân, vừa đòi hỏi chi phí gán nhãn thủ công vượt xa nguồn lực của nhóm nghiên cứu.

**Giải pháp nhóm đề xuất** gồm ba bước:

**Bước 1 — Sinh dữ liệu tổng hợp:** Sử dụng LLM Qwen2.5-1.5B-Instruct chạy trên Google Colab GPU T4 để sinh bộ 600 CV synthetic cho ngành IT. Mỗi CV được kiểm soát qua schema metadata định nghĩa role, seniority, danh sách kỹ năng, và phong cách viết. Đặc biệt, nhóm kiểm soát `edge_type` để tạo ra CV ngắn, CV dài, CV song ngữ — phản ánh sự đa dạng thực tế của CV lập trình viên Việt Nam. Bộ dữ liệu đạt `quality_score` trung bình 0.97.

**Bước 2 — Gán nhãn tự động theo phương pháp Silver Standard:** Xây dựng rule-based annotator để tự động gán nhãn BIO ở cấp token, sử dụng ontology kỹ năng, regex ngày tháng, và danh sách từ khóa. Đây là phương pháp "gán nhãn bạc" — nhanh và đủ tốt để huấn luyện mô hình ban đầu.

**Bước 3 — Fine-tune mBERT:** Huấn luyện lại mô hình mBERT trên bộ dữ liệu đã gán nhãn để xử lý văn bản song ngữ với nhiều thuật ngữ kỹ thuật IT.

---

## SLIDE 8 — Sinh dữ liệu & Huấn luyện NER *(bảng thống kê dataset)*

> *(Đọc qua bảng, nhấn mạnh điểm nổi bật)*

Bảng này tóm tắt thống kê bộ dữ liệu 600 CV synthetic.

Nhóm phân bố đều qua **10 vai trò nghề nghiệp** trong ngành IT, mỗi vai trò 59–61 CV. Tất cả các vai trò đều đạt `quality_score` trung bình 0.997, cho thấy Qwen2.5-1.5B-Instruct sinh CV chất lượng cao nhất quán khi được cung cấp metadata đầu vào rõ ràng.

Về phân bố seniority: Junior chiếm 36%, Mid chiếm 39%, Senior 19%, Lead 4%, và Principal 2%. Phân bố này được thiết kế để phản ánh thực tế thị trường tuyển dụng IT Việt Nam, nơi nhóm mid-level chiếm đa số.

Trung bình mỗi CV dài khoảng 285 từ — đủ để mô hình NER có ngữ cảnh tốt mà không quá dài gây tốn tài nguyên tính toán.

---

## SLIDE 9 — Sinh dữ liệu & Huấn luyện NER *(phân bố nhãn & kết quả)*

> *(Giải thích phân bố nhãn, sau đó nêu kết quả NER)*

**Phân bố nhãn thực thể** trên 200 mẫu cho thấy SKILL là thực thể chiếm ưu thế tuyệt đối với 3.799 instances, tương đương gần 59% tổng số thực thể. Điều này hoàn toàn hợp lý với đặc thù của CV ngành CNTT — phần Skills thường liệt kê rất nhiều công nghệ.

DATE và JOB_TITLE chiếm lần lượt 10.7% và 8.7%. Các thực thể như CERT chỉ chiếm 0.5%, phản ánh thực tế có ít ứng viên liệt kê chứng chỉ cụ thể trong CV.

**Về kết quả đánh giá NER:** Nhóm thực hiện hai phương pháp đánh giá. Khi đánh giá trên silver labels, điểm F1 rất thấp (0.03) — nhưng nguyên nhân không phải mô hình kém mà là do **tokenization mismatch**: silver labeler dùng whitespace tokenization còn mBERT dùng WordPiece tokenization, hai hệ thống này không thể so sánh trực tiếp theo vị trí token. Đây là một phát hiện kỹ thuật quan trọng của nhóm.

Khi đánh giá trên **tập ground truth thủ công** — 71 thực thể được gán nhãn tay trên 1 CV thực — mô hình đạt **F1 tổng thể 0.8633**, trong đó SKILL đạt F1 = 0.9157, DATE và JOB_TITLE đạt F1 = 1.000. Kết quả này nhất quán với đánh giá bán tự động trên 100 CV với Recall = 0.85 cho SKILL.

---

## SLIDE 10 — Giải pháp so khớp kỹ năng — Skill Matching *(văn bản)*

> *(Giới thiệu bài toán và giải pháp 3 tầng)*

Thưa hội đồng, sau khi NER trích xuất được danh sách kỹ năng từ CV và JD, bước tiếp theo là so khớp để tính ATS score.

Thách thức của bài toán này là **sự đa dạng trong cách viết tên kỹ năng**: một ứng viên viết "ReactJS" nhưng JD yêu cầu "React.js"; một người viết "Postgres" nhưng JD ghi "PostgreSQL". So khớp chuỗi đơn thuần sẽ bỏ sót rất nhiều kỹ năng thực sự tương đương.

Nhóm giải quyết bằng **logic so khớp 3 tầng theo thứ tự từ chính xác đến tổng quát**:

**Tầng 1 — Exact match:** So sánh chuỗi ký tự sau khi chuẩn hóa lowercase. Cho điểm 1.0.

**Tầng 2 — Ontology match:** Sử dụng ontology kỹ năng IT với khoảng 500 entries để nhận diện các aliases và thuật ngữ tương đương. Ví dụ: Postgres = PostgreSQL, ReactJS = React.js, k8s = Kubernetes. Cho điểm 0.85.

**Tầng 3 — Semantic match:** Khi không tìm được match chính xác hay ontology, dùng vector embedding Sentence-BERT để tính cosine similarity. Ngưỡng 0.65 được chọn qua thực nghiệm: TensorFlow và PyTorch có similarity ≈ 0.79 (nên match), Python và Java có similarity ≈ 0.58 (không nên match). Điểm trả về chính là giá trị similarity.

Nếu không tầng nào tìm được match, kỹ năng được ghi vào danh sách "missing" — đây chính là gap analysis cho người dùng.

---

## SLIDE 11 — Giải pháp Skill Matching *(sơ đồ)*

> *(Chỉ vào flowchart, giải thích luồng cascade)*

Đây là sơ đồ luồng của SkillMatcher.

Với mỗi kỹ năng trong JD, hệ thống lần lượt thử Tầng 1, nếu không được thì thử Tầng 2, nếu không được thì thử Tầng 3. Đây là cách tiếp cận "cascade" — đảm bảo kết quả luôn có precision cao nhất có thể, chỉ dùng tầng tổng quát hơn khi tầng chính xác hơn không tìm được kết quả.

Ontology kỹ năng được xây dựng từ ba nguồn: ESCO, O*NET cho các kỹ năng universal, và bổ sung các công nghệ đặc thù thị trường Việt Nam như Laravel, Flutter, .NET Core, Spring Boot — những công nghệ phổ biến ở Việt Nam nhưng ít xuất hiện trong các ontology quốc tế.

---

## SLIDE 12 — Chatbot RAG — Tư vấn cá nhân hóa *(văn bản)*

> *(Giải thích cơ chế RAG và điểm khác biệt cá nhân hóa)*

Module thứ ba và cũng là module phức tạp nhất của hệ thống là **Chatbot tư vấn nghề nghiệp**.

Vấn đề cốt lõi của LLM thuần là hiện tượng **"ảo giác" (hallucination)** — mô hình có thể đưa ra câu trả lời tự tin nhưng sai về các thông tin cụ thể như lộ trình học kỹ năng, mức lương hay yêu cầu công việc. Kiến trúc **RAG — Retrieval-Augmented Generation** giải quyết vấn đề này bằng cách bắt buộc LLM trả lời dựa trên các document được truy xuất từ knowledge base đáng tin cậy.

Knowledge base của chatbot được xây dựng từ dữ liệu O*NET (mô tả nghề nghiệp chuẩn), Career guides tự viết về 10 vai trò IT chính trong thị trường Việt Nam, và mô tả kỹ năng từ O*NET taxonomy.

Điểm **phân biệt lớn nhất** so với chatbot RAG thông thường là cơ chế **cá nhân hóa sâu**: khi xây dựng prompt gửi cho LLM, chatbot tổng hợp đồng thời 6 nguồn context: System prompt định nghĩa vai trò chuyên gia; Tool Context — chatbot biết tool nào đang active trên giao diện và điều chỉnh hành vi proactive; Retrieved Context — 3 chunks liên quan nhất từ ChromaDB; User Memory — thông tin về vị trí hiện tại, mục tiêu và kinh nghiệm của người dùng đã lưu từ session trước; CV/JD Context — kết quả phân tích CV và gap analysis cụ thể của người dùng này; và Conversation History — 10 tin nhắn gần nhất.

Nhờ cơ chế này, chatbot không chỉ trả lời câu hỏi mà còn nhận biết từng người dùng đang ở đâu trong hành trình nghề nghiệp của họ.

---

## SLIDE 13 — Chatbot RAG — Kiến trúc chi tiết *(sơ đồ)*

> *(Chỉ vào hai giai đoạn: Indexing và Querying)*

Kiến trúc RAG chia làm hai giai đoạn rõ ràng.

**Giai đoạn Indexing** chạy một lần khi setup hệ thống: tất cả documents được chia chunk 512 tokens với overlap 50 tokens, encode thành embedding bằng Sentence-BERT, và lưu vào ChromaDB thành 3 collections riêng biệt.

**Giai đoạn Querying** chạy với mỗi câu hỏi của người dùng: câu hỏi được encode thành embedding, ChromaDB tìm top-3 chunks gần nhất, các chunks này được tổng hợp cùng User Memory và CV Context thành prompt cuối cùng, rồi LLM sinh response dưới dạng SSE stream — người dùng thấy chữ xuất hiện từng token một giống ChatGPT.

---

## SLIDE 14 — Kết quả thực nghiệm *(tóm tắt)*

> *(Trình bày nhanh 3 kết quả chính)*

Thưa hội đồng, về kết quả thực nghiệm.

**Kết quả NER:** Mô hình mBERT fine-tune đạt **F1 = 0.8633** trên tập ground truth thủ công, trong đó thực thể SKILL — quan trọng nhất trong domain CV — đạt **F1 = 0.9157**. DATE và JOB_TITLE đạt F1 = 1.000 trên tập này. Kết quả bán tự động trên 100 CV đạt micro F1 = 0.7883.

**Kết quả Skill Matching:** Đạt **100% accuracy** trên bộ 10 test cases kiểm thử các tình huống matching đặc thù của ngành tuyển dụng IT, bao gồm alias (Postgres ↔ PostgreSQL), semantic (TensorFlow ≈ PyTorch), và exact match.

**Demo hệ thống:** Hoàn thiện và vận hành ổn định **4 luồng chức năng** trên giao diện thực tế: Phân tích CV từ file upload, ATS Score và Skill Gap Analysis, RAG Chatbot tư vấn cá nhân hóa, và CV Builder xuất file PDF chuẩn ATS.

---

## SLIDE 15 — Kết quả thực nghiệm *(bảng NER ground truth)*

> *(Đọc qua bảng, giải thích ngắn gọn)*

Đây là bảng kết quả chi tiết trên tập ground truth thủ công với 71 entities.

Cần lưu ý thực thể **LOC đạt F1 = 0.0** trên tập này — không phải mô hình không nhận diện được địa danh mà do mô hình nhầm "Hai Thuat VietNam" thành tên người (PER) thay vì địa danh. Đây là lỗi phổ biến trong NER tiếng Việt vì tên người và tên địa danh có cùng cấu trúc viết hoa. ORG đạt F1 = 0.667 do mô hình có xu hướng mở rộng span sang các từ liền kề không phải tên tổ chức.

Nhìn tổng thể, F1 = 0.8633 là kết quả cạnh tranh trong bối cảnh **toàn bộ dữ liệu huấn luyện là synthetic** và không có GPU chuyên dụng — mô hình được huấn luyện hoàn toàn trên Google Colab T4 miễn phí.

---

## SLIDE 16 — Kết luận & Định hướng phát triển

> *(Tổng kết đóng góp, thừa nhận hạn chế, nêu hướng tương lai)*

Kính thưa hội đồng, để kết luận.

**Về đóng góp của đề tài:** Nhóm đã xây dựng thành công hệ thống AI end-to-end gồm 9 microservices hoàn chỉnh, vận hành ổn định. Đặc biệt, đề tài đóng góp cho cộng đồng nghiên cứu ba tài nguyên có giá trị tái sử dụng: bộ **600 CV synthetic song ngữ** chất lượng cao với quality_score trung bình 0.97; **ontology kỹ năng IT 500 entries** cập nhật cho thị trường Việt Nam; và kiến trúc **RAG cá nhân hóa** với cơ chế tool-aware context và User Memory Service.

**Về hạn chế:** Nhóm thành thật nhận ra rằng mô hình NER được huấn luyện hoàn toàn trên dữ liệu synthetic, nên có thể có distribution shift khi gặp CV thực tế với phong cách viết đa dạng hơn. Bộ test Skill Matching chỉ gồm 10 cases thủ công, chưa đủ đại diện cho toàn bộ phân phối thực tế. Chatbot chưa được đánh giá định lượng qua user study.

**Về định hướng phát triển:** Ưu tiên cao nhất là mở rộng dữ liệu huấn luyện với CV thực tế gán nhãn thủ công — nhóm đề xuất tổ chức annotation sprint với 50–100 CV dùng Label Studio. Tiếp theo là nâng cấp mô hình NER từ mBERT lên **PhoBERT** để tận dụng lợi thế hiểu tiếng Việt sâu hơn. Về dài hạn, hệ thống có tiềm năng triển khai tại Career Center của các trường đại học CNTT Việt Nam — cung cấp dịch vụ review CV và tư vấn nghề nghiệp miễn phí cho sinh viên, lấp đầy khoảng trống dịch vụ mà các nền tảng như LinkedIn Premium hay TopCV Pro tính phí quá cao để sinh viên có thể tiếp cận.

---

## SLIDE 17 — Demo

> *(Chuyển sang demo trực tiếp hệ thống)*

Thưa hội đồng, nhóm xin được demo trực tiếp hệ thống.

Nhóm sẽ demo 4 luồng chức năng chính theo thứ tự:

1. **Upload CV và phân tích NER** — upload file CV thực và xem kết quả trích xuất thực thể.
2. **ATS Score và Skill Gap** — paste JD vào để xem điểm ATS và danh sách kỹ năng còn thiếu.
3. **RAG Chatbot tư vấn** — đặt câu hỏi về lộ trình nghề nghiệp và xem chatbot trả lời cá nhân hóa.
4. **CV Builder xuất PDF** — tạo và xuất CV chuẩn ATS dưới dạng file PDF.

*(Tiến hành demo — sau khi demo xong)*

---

> **Kết thúc trình bày**

Cảm ơn hội đồng đã lắng nghe. Nhóm xin kính mời quý thầy cô đặt câu hỏi.