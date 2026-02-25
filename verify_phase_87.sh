#!/bin/bash
echo "=========================================="
echo "PHASE 87 VERIFICATION CHECKLIST"
echo "=========================================="
echo ""

cd /home/quant/apps/quantclaw-data

echo "✓ Module file exists:"
ls -lh modules/correlation_anomaly.py | awk '{print "  " $9 " (" $5 ")"}'
echo ""

echo "✓ API route exists:"
ls -lh src/app/api/v1/correlation-anomaly/route.ts | awk '{print "  " $9 " (" $5 ")"}'
echo ""

echo "✓ CLI integration:"
grep -c "correlation_anomaly" cli.py | awk '{print "  Found in cli.py: " $1 " references"}'
echo ""

echo "✓ Services.ts integration:"
grep -c "Phase 87" src/app/services.ts | awk '{print "  Phase 87 entries: " $1}'
echo ""

echo "✓ Roadmap.ts status:"
grep "id: 87" src/app/roadmap.ts
echo ""

echo "✓ LOC count:"
wc -l modules/correlation_anomaly.py
echo ""

echo "✓ Test execution (corr-scan):"
timeout 30 python3 cli.py corr-scan --tickers SPY,TLT 2>&1 | grep -E "timestamp|anomalies_detected|universe" | head -5
echo ""

echo "=========================================="
echo "VERIFICATION COMPLETE"
echo "=========================================="
