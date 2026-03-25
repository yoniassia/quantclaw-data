#!/bin/bash
# Test script for Proxy Fight Tracker (Phase 69)

set -e
cd /home/quant/apps/quantclaw-data

echo "Testing Proxy Fight Tracker Module..."
echo ""

echo "1. Testing proxy-filings command:"
python3 cli.py proxy-filings AAPL --years 2
echo ""

echo "2. Testing proxy-contests command:"
python3 cli.py proxy-contests TSLA
echo ""

echo "3. Testing proxy-voting command:"
python3 cli.py proxy-voting GOOGL
echo ""

echo "4. Testing proxy-advisory command:"
python3 cli.py proxy-advisory META
echo ""

echo "5. Testing proxy-summary command:"
python3 cli.py proxy-summary AAPL
echo ""

echo "✅ All tests completed successfully!"
