#!/bin/bash
# Test script for Activist Success Predictor (Phase 67)

echo "=== PHASE 67: Activist Success Predictor Tests ==="
echo ""

echo "1. Testing historical campaign analysis..."
python3 cli.py activist-historical | jq -r '.success_rate, .total_campaigns'
echo ""

echo "2. Testing 13D filing tracker (AAPL - 2 years)..."
python3 cli.py activist-13d --ticker AAPL --days 730 | jq -r '.ticker, .filings_count'
echo ""

echo "3. Testing 13D filing tracker (M - Macy's - likely to have filings)..."
python3 cli.py activist-13d --ticker M --days 730 | jq -r '.ticker, .filings_count'
echo ""

echo "4. Testing prediction (requires sklearn)..."
python3 cli.py activist-predict --ticker AAPL 2>&1 | head -5
echo ""

echo "5. Testing scan (requires sklearn)..."
python3 cli.py activist-scan --sector Technology --min-cap 5000 2>&1 | head -5
echo ""

echo "=== All tests completed ==="
