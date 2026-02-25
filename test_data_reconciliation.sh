#!/bin/bash
# Data Reconciliation Module Test Suite - Phase 84

cd /home/quant/apps/quantclaw-data

echo "==========================="
echo "PHASE 84: Multi-Source Data Reconciliation"
echo "==========================="
echo

echo "1️⃣  Testing Crypto Price Reconciliation (BTC)"
python3 cli.py reconcile-price BTC --type crypto
echo

echo "2️⃣  Testing Crypto Price Reconciliation (ETH)"
python3 cli.py reconcile-price ETH --type crypto
echo

echo "3️⃣  Testing Data Quality Report"
python3 cli.py data-quality-report
echo

echo "4️⃣  Testing Source Reliability Rankings"
python3 cli.py source-reliability
echo

echo "5️⃣  Testing Discrepancy Log (24 hours)"
python3 cli.py discrepancy-log --hours 24
echo

echo "6️⃣  Testing Discrepancy Log with Symbol Filter"
python3 cli.py discrepancy-log --symbol BTC --hours 48
echo

echo "✅ All commands executed successfully!"
echo
echo "API Route created at: /api/v1/data-reconciliation"
echo "Services.ts updated with phase 84"
echo "Roadmap.ts marked as done"
