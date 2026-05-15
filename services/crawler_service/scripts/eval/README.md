# JD Extraction Eval Workflow

End-to-end workflow để đo độ chính xác của pipeline trích xuất JD trên một
eval set 100 JD label tay. Output: per-field accuracy với 95% Wilson CI,
đủ cho thesis defense và quyết định ship/no-ship cho production.

## Mục tiêu

- Có **số liệu thật** thay vì estimate cho 8 hard fields:
  `seniority`, `min_exp`, `max_exp`, `degree_required`, `work_mode`,
  `skills_required`, `skills_preferred`, `salary_*`
- So sánh hai backend: **rule-only** vs **rule + Groq LLM**
- Sample stratified theo (language × role) để cover EN/VI/Mixed JDs

## Time estimate

| Phase | Time | Cost |
|---|---|---|
| Crawl ~300 JD with `--fetch-details` | 2-3h auto | $0 |
| Sample 100 JD pre-filled | 1 phút | $0 |
| Manual labeling (Streamlit UI) | **5-6h human** | $0 |
| Run eval rule-only | 1 phút | $0 |
| Run eval rule+LLM | 5-15 phút (Groq rate limit) | ~$0 (free tier) |
| **Total** | **~6-8h work** | **$0** |

## Prerequisites

```bash
# 1. Postgres + Chroma running (option 1 trong dev_native.sh)
./scripts/dev_native.sh   # → 1
```

```bash
# 2. Streamlit installed (cho labeling UI)
.venv/bin/pip install streamlit
```

```bash
# 3. (Optional) CHAT_GROQ_API_KEY trong .env nếu muốn eval LLM stack
grep CHAT_GROQ /home/dungken/Desktop/Workspace/utc2/cv_assistant/.env
```

## Step 1 — Crawl 300 JD diverse

Cần đủ JD trong DB để stratified sample. Re-crawl 300 JD ITviec với
`--fetch-details` (lấy description full):

```bash
cd /home/dungken/Desktop/Workspace/utc2/cv_assistant
PGPASSWORD=skill_password psql -h localhost -p 5434 -U skill_user -d skill_data \
  -c "TRUNCATE jd_raw; TRUNCATE skill_trends;"

DATABASE_URL="postgresql://skill_user:skill_password@localhost:5434/skill_data" \
CHROMA_HOST=localhost CHROMA_PORT=8003 \
.venv/bin/python -m services.crawler_service.scripts.run_once_crawl \
  --fetch-details --max-jds-itviec 300 --max-jds-topcv 0
```

Mất ~2-3h. Có thể chạy qua đêm.

## Step 2 — Stratified sample 100 JD

```bash
PYTHONPATH=. .venv/bin/python -m services.crawler_service.scripts.eval.sample_for_labeling \
  --n 100 \
  --out services/crawler_service/data/eval/label_pool.jsonl
```

Output:
- `label_pool.jsonl`: 100 JDs với pre-filled labels từ rule-based extractor
- Console log: distribution theo (language × role) để verify diversity

## Step 3 — Label bằng Streamlit UI

```bash
.venv/bin/streamlit run services/crawler_service/scripts/eval/label_ui.py -- \
  --pool services/crawler_service/data/eval/label_pool.jsonl \
  --gold services/crawler_service/data/eval/gold_labels.jsonl
```

UI sẽ mở browser. Workflow:
1. Đọc description JD bên trái
2. Verify form bên phải (đã pre-filled)
3. Sửa các field sai
4. Click **"💾 Save & Next"** → JD tiếp theo
5. UI tự skip JD đã label → resume từ chỗ dừng

**Tips để label nhanh:**
- 5 fields easy (`title`, `company`, `location`, `posted_date`, `url`) đã ẩn — chỉ verify visual nếu nghi ngờ
- Pre-fill từ rule-based ~75% đúng → bạn thường chỉ "Save & Next"
- Skill radios: chỉ click những skill cần đổi bucket
- `salary` để 0 nếu hidden

Time: **~3-5 phút/JD trung bình** = **5-8h cho 100 JD**

## Step 4 — Run eval

### Rule-only:
```bash
PYTHONPATH=. .venv/bin/python -m services.crawler_service.scripts.eval.run_eval \
  --gold services/crawler_service/data/eval/gold_labels.jsonl \
  --report services/crawler_service/data/eval/report_rule.md
```

### Rule + LLM:
```bash
export $(grep -v '^#' /home/dungken/Desktop/Workspace/utc2/cv_assistant/.env | xargs)
PYTHONPATH=. .venv/bin/python -m services.crawler_service.scripts.eval.run_eval \
  --gold services/crawler_service/data/eval/gold_labels.jsonl \
  --report services/crawler_service/data/eval/report_llm.md \
  --use-llm
```

## Output diễn giải

Report markdown chứa:

1. **Per-field accuracy + 95% Wilson CI** — bảng với confidence interval. Wilson CI vì N=100 nên ±5-7%, không trust point estimate.
2. **Skill Jaccard similarity** — measure skills tổng (required + preferred) bao phủ bao nhiêu của gold
3. **Bucket accuracy** — tỷ lệ skill được put vào đúng required/preferred
4. **Error samples** — 3 lỗi đầu cho mỗi field để debug

## Decision matrix (sau khi có kết quả)

| Overall accuracy | Action |
|---|---|
| ≥ 85% | Ship pipeline cho dashboard. Document trong báo cáo. |
| 75-85% | Ship rule-only, mark LLM as future improvement. |
| < 75% | Cần fine-tune (Path 2). Build dataset 500 JD lên. |

## Files structure

```
services/crawler_service/
├── data/eval/
│   ├── label_pool.jsonl       # output of sample_for_labeling.py
│   ├── gold_labels.jsonl      # output of label_ui.py (your manual labels)
│   ├── report_rule.md         # output of run_eval.py
│   └── report_llm.md          # output of run_eval.py --use-llm
└── scripts/eval/
    ├── README.md              # this file
    ├── sample_for_labeling.py # Step 2
    ├── label_ui.py            # Step 3
    └── run_eval.py            # Step 4
```

## Tips để giảm time labeling thêm 20-30%

1. **Label theo session** — không làm 100 JD 1 lèo. Chia 2-3 session 2-3h.
2. **Skip khi không chắc** — click "Skip" cho JD ambiguous, label lại sau khi đã warm up.
3. **Group theo stratum** — UI sort theo stratum nên các JD cùng role/lang nằm gần → context switching ít.