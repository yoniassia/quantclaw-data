#!/bin/bash
# Test script for Finnhub IPO Calendar module

set -e

echo "======================================"
echo "Finnhub IPO Calendar Module Test"
echo "======================================"
echo ""

cd /home/quant/apps/quantclaw-data

# Check if module exists
if [ ! -f "modules/finnhub_ipo_calendar.py" ]; then
    echo "❌ ERROR: Module file not found!"
    exit 1
fi
echo "✅ Module file exists"

# Run comprehensive test
echo ""
echo "Running module tests..."
python3 modules/finnhub_ipo_calendar.py test

echo ""
echo "======================================"
echo "Test: Upcoming IPOs"
echo "======================================"
python3 modules/finnhub_ipo_calendar.py upcoming | head -50

echo ""
echo "======================================"
echo "Test: Recent IPOs"
echo "======================================"
python3 modules/finnhub_ipo_calendar.py recent | head -50

echo ""
echo "======================================"
echo "✅ All tests completed!"
echo "======================================"
