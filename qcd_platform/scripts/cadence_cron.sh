#!/bin/bash
# QuantClaw Data Platform — Cadence-Aware Pipeline Cron
#
# Usage:
#   cadence_cron.sh daily    → Tier 1 price-sensitive (rankings, valuations) — weekdays
#   cadence_cron.sh weekly   → fundamentals + composites — Sundays
#   cadence_cron.sh monthly  → segments + universe — 1st of month
#
# Crontab:
#   0 1 * * 1-5  .../cadence_cron.sh daily   >> /var/log/quantclaw-pipeline.log 2>&1
#   0 1 * * 0    .../cadence_cron.sh weekly   >> /var/log/quantclaw-pipeline.log 2>&1
#   0 1 1 * *    .../cadence_cron.sh monthly  >> /var/log/quantclaw-pipeline.log 2>&1

set -euo pipefail
export PATH="/home/linuxbrew/.linuxbrew/bin:$PATH"

CADENCE="${1:-daily}"
PROJECT_DIR="/home/quant/apps/quantclaw-data"
LOG_PREFIX="[$(date -u '+%Y-%m-%d %H:%M:%S UTC')] [${CADENCE}]"

cd "$PROJECT_DIR"

export GURUFOCUS_DATA_API_KEY=$(python3 -c "import json; print(json.load(open('/home/quant/.openclaw/workspace/.credentials/gurufocus.json'))['api_key'])")

echo "$LOG_PREFIX Starting ${CADENCE} pipeline"

case "$CADENCE" in
  daily)
    # Price-sensitive data — shifts with daily price moves
    echo "$LOG_PREFIX GuruFocus: rankings, valuations"
    python3 scripts/infra/run_gurufocus.py --module rankings 2>&1 || echo "$LOG_PREFIX rankings had errors (continuing)"
    python3 scripts/infra/run_gurufocus.py --module valuations 2>&1 || echo "$LOG_PREFIX valuations had errors (continuing)"

    echo "$LOG_PREFIX Gold Transformer (rankings + valuations)"
    python3 modules_v2/gf_gold_transformer.py --category rankings 2>&1 || echo "$LOG_PREFIX Gold transformer (rankings) had errors (continuing)"
    python3 modules_v2/gf_gold_transformer.py --category valuations 2>&1 || echo "$LOG_PREFIX Gold transformer (valuations) had errors (continuing)"
    ;;

  weekly)
    # Quarterly filings + derived composites — weekly is plenty
    echo "$LOG_PREFIX GuruFocus: fundamentals"
    python3 scripts/infra/run_gurufocus.py --module fundamentals 2>&1 || echo "$LOG_PREFIX fundamentals had errors (continuing)"

    echo "$LOG_PREFIX Gold Transformer (fundamentals)"
    python3 modules_v2/gf_gold_transformer.py --category fundamentals 2>&1 || echo "$LOG_PREFIX Gold transformer had errors (continuing)"

    echo "$LOG_PREFIX GuruFocus Tier 3: composites"
    python3 scripts/infra/run_gurufocus.py --tier 3 2>&1 || echo "$LOG_PREFIX Tier 3 composites had errors (continuing)"
    ;;

  monthly)
    # Rarely-changing structural data
    echo "$LOG_PREFIX GuruFocus: segments, universe"
    python3 scripts/infra/run_gurufocus.py --tier 2 2>&1 || echo "$LOG_PREFIX Tier 2 had errors (continuing)"

    echo "$LOG_PREFIX Gold Transformer (all — monthly full refresh)"
    python3 modules_v2/gf_gold_transformer.py --category all 2>&1 || echo "$LOG_PREFIX Gold transformer had errors (continuing)"
    ;;

  *)
    echo "$LOG_PREFIX Unknown cadence: $CADENCE (expected daily|weekly|monthly)"
    exit 1
    ;;
esac

# Common tail: pipeline, Platinum, matviews
echo "$LOG_PREFIX Running pipeline..."
python3 qcd_platform/scripts/run_pipeline.py --overnight --workers 4 2>&1

echo "$LOG_PREFIX Platinum universe refresh..."
python3 -c "
from modules.platinum_enriched import refresh_universe
result = refresh_universe(max_workers=4)
print(f'Platinum refresh: {result[\"success\"]}/{result[\"total\"]} success, {result[\"elapsed_seconds\"]}s')
" 2>&1

echo "$LOG_PREFIX Refreshing materialized views..."
sudo -u postgres psql -d quantclaw_data -c "SELECT refresh_all_matviews();" 2>&1

echo "$LOG_PREFIX Sending alerts..."
python3 qcd_platform/scripts/alert_notifier.py 2>&1

echo "$LOG_PREFIX ${CADENCE} pipeline complete"
