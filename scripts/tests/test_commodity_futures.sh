#!/bin/bash
# Test suite for Commodity Futures Curves Module (Phase 44)

echo "========================================="
echo "QUANTCLAW DATA - Phase 44 Test Suite"
echo "Commodity Futures Curves Module"
echo "========================================="
echo ""

echo "Test 1: Futures Curve for Corn (ZC)"
echo "-------------------------------------"
python3 cli.py futures-curve ZC --limit 4
echo ""

echo "Test 2: Contango/Backwardation Scanner"
echo "---------------------------------------"
python3 cli.py contango
echo ""

echo "Test 3: Roll Yield Analysis for Corn"
echo "-------------------------------------"
python3 cli.py roll-yield ZC --lookback 90
echo ""

echo "Test 4: Term Structure Analysis for Soybeans"
echo "---------------------------------------------"
python3 cli.py term-structure ZS
echo ""

echo "Test 5: Futures Curve for Gold (GC)"
echo "-------------------------------------"
python3 cli.py futures-curve GC --limit 3
echo ""

echo "========================================="
echo "All tests completed!"
echo "========================================="
