#!/bin/bash
# QuantClaw Data Platform — Overnight Pipeline Run
# Cron: 0 1 * * * /home/quant/apps/quantclaw-data/qcd_platform/scripts/overnight_run.sh
set -euo pipefail
export PATH="/home/linuxbrew/.linuxbrew/bin:$PATH"

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$(dirname "$SCRIPT_DIR")")"
LOG_DIR="$PROJECT_DIR/logs"
mkdir -p "$LOG_DIR"

DATE=$(date +%Y-%m-%d)
LOG_FILE="$LOG_DIR/pipeline_${DATE}.log"

echo "=== QuantClaw Data Pipeline — $DATE ===" >> "$LOG_FILE"
echo "Started: $(date -u '+%Y-%m-%d %H:%M:%S UTC')" >> "$LOG_FILE"

cd "$PROJECT_DIR"

# Run the batch
python3 qcd_platform/scripts/run_batch.py \
  --overnight \
  --workers 6 \
  >> "$LOG_FILE" 2>&1

echo "Completed: $(date -u '+%Y-%m-%d %H:%M:%S UTC')" >> "$LOG_FILE"

# Keep last 30 days of logs
find "$LOG_DIR" -name "pipeline_*.log" -mtime +30 -delete 2>/dev/null || true
