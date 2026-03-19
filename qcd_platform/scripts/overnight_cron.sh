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

# Refresh Platinum enriched records (all 200 symbols)
echo "$LOG_PREFIX Starting Platinum universe refresh..."
python3 -c "
from modules.platinum_enriched import refresh_universe
result = refresh_universe(max_workers=4)
print(f'Platinum refresh: {result[\"success\"]}/{result[\"total\"]} success, {result[\"elapsed_seconds\"]}s')
" 2>&1

# Refresh materialized views (cross-cadence joins, symbol snapshots, module health)
echo "$LOG_PREFIX Refreshing materialized views..."
sudo -u postgres psql -d quantclaw_data -c "SELECT refresh_all_matviews();" 2>&1

# Send any pending critical alerts to WhatsApp
python3 qcd_platform/scripts/alert_notifier.py 2>&1

echo "$LOG_PREFIX Overnight pipeline complete"
