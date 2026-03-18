#!/bin/bash
# QuantClaw Data Platform — Overnight Pipeline Cron
# Runs at 01:00 UTC daily
# Add to crontab: 0 1 * * * /home/quant/apps/quantclaw-data/qcd_platform/scripts/overnight_cron.sh >> /var/log/quantclaw-pipeline.log 2>&1

set -euo pipefail

LOG_PREFIX="[$(date -u '+%Y-%m-%d %H:%M:%S UTC')]"
echo "$LOG_PREFIX Starting overnight pipeline run"

cd /home/quant/apps/quantclaw-data

# Run the pipeline
python3 qcd_platform/scripts/run_pipeline.py --overnight --workers 4 2>&1

echo "$LOG_PREFIX Overnight pipeline complete"
