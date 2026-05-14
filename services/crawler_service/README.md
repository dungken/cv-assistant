# Crawler Service

Crawls JDs from Vietnamese IT job boards (ITviec for now, TopCV planned),
deduplicates, normalizes skills, persists to PostgreSQL + ChromaDB, and
aggregates daily skill demand into the `skill_trends` time-series table.

Output of this service is the data backbone for **CV Freshness Score** and
**Learning Path Optimizer** (see thesis Chapters 3.2 and 3.3).

## Tables (PostgreSQL, db: `skill_data`)

- `jd_raw` — one row per unique JD (keyed by `jd_key`, dedupe across days/sources).
- `skill_trends` — daily aggregated demand, (skill, snapshot_date, window, role, location).
- `crawler_log` — audit log of every crawl run.

## Endpoints (port 5006)

| Method | Path | Purpose |
|---|---|---|
| GET | `/health` | Liveness + scheduler status |
| GET | `/crawler/health-check?source=itviec` | Verify source HTML still parses |
| POST | `/crawler/trigger?source=itviec&categories=backend,frontend` | Manual crawl |
| POST | `/crawler/aggregate?snapshot_date=2026-05-08&window_days=7` | Recompute skill_trends |

## Schedule

Default cron: **02:00 Asia/Ho_Chi_Minh daily**. Set `ENABLE_SCHEDULER=false`
to disable (useful for tests).

## Local run (outside Docker)

```bash
# from repo root
export DATABASE_URL="postgresql://skill_user:skill_password@localhost:5434/skill_data"
export CHROMA_HOST=localhost
export CHROMA_PORT=8003
export NER_SERVICE_URL=http://localhost:5005
export SKILL_SERVICE_URL=http://localhost:5002
export ENABLE_SCHEDULER=false  # don't run cron in dev

pip install -r services/crawler_service/requirements.txt
python services/crawler_service/main.py
```

Then test:
```bash
curl http://localhost:5006/health
curl http://localhost:5006/crawler/health-check?source=itviec
curl -X POST 'http://localhost:5006/crawler/trigger?source=itviec&categories=backend&max_pages=1&max_jds=5'
```

## Sources

| Source | Status | Notes |
|---|---|---|
| ITviec | ✅ Full | Listing cards expose all needed fields (title, company, location, skill tags, posted date). No login needed. Salary requires login → left null. |
| TopCV | ✅ Listing-only | Salary visible (USD/VND), location visible. **Skills not in listing cards** — recovered ~78% via ontology matching on titles. Detail pages are protected by Cloudflare Turnstile that blocks headless Chrome as of 2026-05; `fetch_details=True` is off by default. |

### TopCV detail page limitation

TopCV listing cards do not contain skill tags. Full skills live on the detail
page, which is gated by Cloudflare Turnstile. We tried:

1. `cloudscraper` — passes listing pages, **403** on detail pages.
2. `undetected-chromedriver` (headless) — passes listing pages, gets stuck on
   the "Just a moment…" interstitial on detail pages (Cloudflare detects
   headless mode and serves an unsolvable challenge).
3. Non-headless Chrome — would require Xvfb on headless server; deferred.

Practical mitigation (implemented): `SkillExtractor._extract_from_text`
matches the title against the ~500-entry skill ontology with word-boundary
regex. This recovers ~78% of TopCV JDs at avg 1.22 skills/JD — enough for
Freshness Score trend tracking, given ITviec already provides rich skill
data per JD.

## Compliance

- Honors `User-Agent` includes contact email (academic research).
- Random sleep 3–6s between requests.
- Default cap 250 JDs/run.
- **Does not redistribute raw scraped data** — only aggregated stats and
  metadata used internally for research per thesis scope (section 1.4.3).
