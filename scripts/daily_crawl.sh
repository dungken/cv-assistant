#!/bin/bash
# Daily crawl wrapper — safe to call multiple times per day.
#
# Checks /tmp/cv_crawler_last_run for today's date. If already ran today, exits
# silently. Otherwise runs the crawler and stamps the file.
#
# Designed to be called from cron OR manually:
#   - cron @daily ... :  fires once a day at scheduled time
#   - cron @hourly ... : fires every hour, runs only the first time per day
#   - manual          :  re-runs on demand (delete stamp file to force)

set -euo pipefail

PROJECT_DIR="/home/dungken/Desktop/Workspace/utc2/cv_assistant"
STAMP_FILE="/tmp/cv_crawler_last_run"
LOG_FILE="/tmp/cv_crawler.log"

cd "$PROJECT_DIR"

today=$(date +%Y-%m-%d)
last_run=$(cat "$STAMP_FILE" 2>/dev/null || echo "never")

if [ "$last_run" = "$today" ]; then
    echo "[$(date +%H:%M:%S)] Already ran today ($today). Skipping." >> "$LOG_FILE"
    exit 0
fi

echo "===== Crawl start: $(date) =====" >> "$LOG_FILE"

# Crawler dependencies are in .venv at project root
export DATABASE_URL="postgresql://skill_user:skill_password@localhost:5434/skill_data"
export CHROMA_HOST="localhost"
export CHROMA_PORT="8003"

if .venv/bin/python -m services.crawler_service.scripts.run_once_crawl >> "$LOG_FILE" 2>&1; then
    echo "$today" > "$STAMP_FILE"
    echo "===== Crawl OK: $(date) =====" >> "$LOG_FILE"
else
    echo "===== Crawl FAILED: $(date) =====" >> "$LOG_FILE"
    exit 1
fi
