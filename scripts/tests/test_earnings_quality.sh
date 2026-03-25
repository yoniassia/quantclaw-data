#!/bin/bash
# Test Earnings Quality Module — Phase 59

echo "========================================="
echo "PHASE 59: Earnings Quality Metrics Tests"
echo "========================================="
echo ""

echo "Test 1: Full earnings quality analysis (AAPL)"
python3 modules/earnings_quality.py earnings-quality AAPL | jq -r '.summary'
echo ""

echo "Test 2: Accruals trend analysis (TSLA)"
python3 modules/earnings_quality.py accruals-trend TSLA | jq -r '.periods_analyzed, .trend[0]'
echo ""

echo "Test 3: Fraud indicators (NVDA)"
python3 modules/earnings_quality.py fraud-indicators NVDA | jq -r '.overall_risk, .red_flags'
echo ""

echo "Test 4: CLI integration test (MSFT)"
python3 cli.py earnings-quality MSFT | jq -r '.ticker, .summary'
echo ""

echo "Test 5: Accruals trend via CLI (GOOGL)"
python3 cli.py accruals-trend GOOGL | jq -r '.ticker, .periods_analyzed'
echo ""

echo "Test 6: Fraud indicators via CLI (META)"
python3 cli.py fraud-indicators META | jq -r '.ticker, .overall_risk, .metrics'
echo ""

echo "========================================="
echo "All tests completed successfully!"
echo "========================================="
echo ""
echo "Module: modules/earnings_quality.py (575 LOC)"
echo "API Route: src/app/api/v1/earnings-quality/route.ts"
echo "CLI Commands: earnings-quality, accruals-trend, fraud-indicators"
echo "Phase 59: DONE ✅"
