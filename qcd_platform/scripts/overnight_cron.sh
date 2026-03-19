#!/bin/bash
# QuantClaw Data Platform — Overnight Pipeline Cron
# Runs at 01:00 UTC daily
# Add to crontab: 0 1 * * * /home/quant/apps/quantclaw-data/qcd_platform/scripts/overnight_cron.sh >> /var/log/quantclaw-pipeline.log 2>&1

set -euo pipefail
export PATH="/home/linuxbrew/.linuxbrew/bin:$PATH"

LOG_PREFIX="[$(date -u '+%Y-%m-%d %H:%M:%S UTC')]"
echo "$LOG_PREFIX Starting overnight pipeline run"

cd /home/quant/apps/quantclaw-data

# Load GuruFocus API key
export GURUFOCUS_DATA_API_KEY=$(python3 -c "import json; print(json.load(open('/home/quant/.openclaw/workspace/.credentials/gurufocus.json'))['api_key'])")

# GuruFocus daily refresh — Tier 1 (rankings, valuations, fundamentals from API)
echo "$LOG_PREFIX Starting GuruFocus Tier 1 (API fetch)..."
python3 scripts/run_gurufocus.py --tier 1 2>&1 || echo "$LOG_PREFIX GuruFocus Tier 1 had errors (continuing)"

# GuruFocus Tier 2 — segments + universe (weekly data, safe to run daily)
echo "$LOG_PREFIX Starting GuruFocus Tier 2 (segments, universe)..."
python3 scripts/run_gurufocus.py --tier 2 2>&1 || echo "$LOG_PREFIX GuruFocus Tier 2 had errors (continuing)"

# GuruFocus Gold Transformer — transform pre-fetched JSON to Gold tables
echo "$LOG_PREFIX Running GuruFocus Gold Transformer..."
python3 modules_v2/gf_gold_transformer.py --category all 2>&1 || echo "$LOG_PREFIX Gold transformer had errors (continuing)"

# GuruFocus Tier 3 — composite modules (fair_value_gap, quality_factor, value_screener, segment_momentum)
echo "$LOG_PREFIX Starting GuruFocus Tier 3 (composite analytics)..."
python3 scripts/run_gurufocus.py --tier 3 2>&1 || echo "$LOG_PREFIX GuruFocus Tier 3 had errors (continuing)"
echo "$LOG_PREFIX GuruFocus pipeline complete"

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
