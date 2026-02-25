#!/bin/bash
set -e

echo "========================================="
echo "Phase 107: Global Government Bond Yields"
echo "========================================="
echo ""

echo "Test 1: List available countries"
echo "---------------------------------"
python cli.py list-countries
echo ""

echo "Test 2: Get US 10Y yield"
echo "------------------------"
python cli.py yield US
echo ""

echo "Test 3: Compare G7 yields"
echo "------------------------"
python cli.py compare US DE JP GB FR IT CA
echo ""

echo "Test 4: Calculate spreads vs US"
echo "-------------------------------"
python cli.py spreads US
echo ""

echo "Test 5: US Treasury yield curve"
echo "-------------------------------"
python cli.py us-curve
echo ""

echo "Test 6: US real yields (TIPS)"
echo "-----------------------------"
python cli.py us-real
echo ""

echo "Test 7: US breakeven inflation"
echo "------------------------------"
python cli.py us-breakeven
echo ""

echo "Test 8: Comprehensive US data"
echo "-----------------------------"
python cli.py comprehensive US
echo ""

echo "========================================="
echo "All Phase 107 tests completed!"
echo "========================================="
