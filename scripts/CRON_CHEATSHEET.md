# Cron Cheatsheet — Daily Crawler

Quick reference cho việc check / điều khiển cron job crawl JD hàng ngày.

## Hoạt động ra sao

| Trigger | Khi nào | Tác dụng |
|---|---|---|
| Cron `0 9 * * *` | 09:00 mỗi ngày (giờ VN) nếu máy đang bật | Crawl chính |
| Cron `@reboot` | 5 phút sau khi máy boot | Bảo hiểm — nếu hôm đó chưa crawl thì chạy |

Wrapper `scripts/daily_crawl.sh` kiểm tra **stamp file** `/tmp/cv_crawler_last_run`:
- Nếu stamp = hôm nay → skip (đã chạy)
- Nếu stamp khác → crawl + cập nhật stamp

→ Đảm bảo **1 lần / ngày**, dù cron bắn nhiều lần.

---

## Mỗi ngày — kiểm tra 30 giây

```bash
# 1. Log lần crawl gần nhất (xem có lỗi gì không)
tail -20 /tmp/cv_crawler.log

# 2. Ngày crawl cuối
cat /tmp/cv_crawler_last_run
```

**Kết quả mong đợi:** stamp = hôm nay; log có dòng `Crawl OK: ...`.

```bash
# 3. DB có data mới không
PGPASSWORD=skill_password psql -h localhost -p 5434 -U skill_user -d skill_data \
  -c "SELECT MAX(first_seen) AS last_crawl, COUNT(*) AS total_jds FROM jd_raw;"
```

`last_crawl` nên là hôm nay hoặc trong vòng 24h.

```bash
# 4. Time-series có tích lũy đúng không
PGPASSWORD=skill_password psql -h localhost -p 5434 -U skill_user -d skill_data \
  -c "SELECT snapshot_date, COUNT(*) FROM skill_trends GROUP BY snapshot_date ORDER BY snapshot_date DESC LIMIT 7;"
```

Mỗi ngày máy bật → có 1 row snapshot_date mới.

---

## Khi nghi ngờ cron không chạy

```bash
# Cron daemon còn sống không
systemctl is-active cron

# Crontab user còn entries không
crontab -l | grep -E "CV Assistant|daily_crawl"

# System log của cron (có thấy nó trigger không)
journalctl -u cron --since "today" | tail -20
```

---

## Force chạy thủ công

```bash
# Xóa stamp → wrapper sẽ crawl
rm -f /tmp/cv_crawler_last_run
bash /home/dungken/Desktop/Workspace/utc2/cv_assistant/scripts/daily_crawl.sh
```

Mất ~6 phút. Output đi vào `/tmp/cv_crawler.log` (append).

Hoặc dùng script Python trực tiếp:
```bash
cd /home/dungken/Desktop/Workspace/utc2/cv_assistant
DATABASE_URL="postgresql://skill_user:skill_password@localhost:5434/skill_data" \
CHROMA_HOST=localhost CHROMA_PORT=8003 \
.venv/bin/python -m services.crawler_service.scripts.run_once_crawl
```

---

## Tạm dừng / Bật lại

```bash
crontab -e
# Comment 2 dòng có "CV Assistant" bằng cách thêm # ở đầu
# Lưu (Ctrl+X, Y, Enter trong nano)
```

Bật lại: xoá `#` đi.

---

## Xoá hẳn cron

```bash
crontab -e
# Xoá 2 dòng "0 9 * * * ..." và "@reboot ..." và 2 dòng comment phía trên
```

---

## Đổi giờ

```bash
crontab -e
# Sửa "0 9 * * *" thành giờ khác
# Ví dụ 07:30: "30 7 * * *"
# Ví dụ 14:00: "0 14 * * *"
```

Cú pháp: `phút giờ ngày tháng thứ command`

---

## Files / paths quan trọng

| Path | Vai trò |
|---|---|
| `scripts/daily_crawl.sh` | Wrapper script (cron gọi cái này) |
| `services/crawler_service/scripts/run_once_crawl.py` | Python script crawl thật |
| `/tmp/cv_crawler.log` | Log append mọi lần crawl |
| `/tmp/cv_crawler_last_run` | Stamp file ngày crawl cuối |
| `crontab -l` | Xem lịch hiện tại |

---

## Troubleshooting nhanh

**"Stamp = hôm qua mà chưa crawl hôm nay"**
→ Máy có thể đã ngủ qua 09:00. Force chạy thủ công.

**"Log có Crawl FAILED"**
→ Kiểm tra cụ thể `tail -100 /tmp/cv_crawler.log` xem lỗi gì. Thường: postgres/chromadb chưa start, hoặc network down.

**"Postgres / ChromaDB chưa chạy"**
```bash
cd /home/dungken/Desktop/Workspace/utc2/cv_assistant
docker compose up -d skill_postgres skill_chromadb
```

**"Muốn xem số JD đã crawl theo ngày"**
```bash
PGPASSWORD=skill_password psql -h localhost -p 5434 -U skill_user -d skill_data \
  -c "SELECT DATE(first_seen) AS day, COUNT(*) FROM jd_raw GROUP BY day ORDER BY day DESC LIMIT 10;"
```
