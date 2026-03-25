#!/bin/bash

# Climate Risk Scoring Test Suite (Phase 72)

echo "=== CLIMATE RISK SCORING TEST ==="
echo ""

# Test 1: Composite Climate Risk
echo "1. Testing composite climate risk for AAPL (Tech company in CA)..."
python3 cli.py climate-risk AAPL
echo ""

# Test 2: Physical Risk - Energy company in TX
echo "2. Testing physical risk for XOM (Energy company in TX - high hurricane/heat exposure)..."
python3 cli.py physical-risk XOM
echo ""

# Test 3: Transition Risk - Oil company
echo "3. Testing transition risk for BP (High carbon transition risk)..."
python3 cli.py transition-risk BP
echo ""

# Test 4: Carbon Scenario Analysis
echo "4. Testing carbon scenario analysis for TSLA..."
python3 cli.py carbon-scenario TSLA
echo ""

# Test 5: Low-risk comparison (Healthcare)
echo "5. Testing climate risk for JNJ (Healthcare - should show lower risk)..."
python3 cli.py climate-risk JNJ
echo ""

# Test 6: High-risk energy sector
echo "6. Testing climate risk for CVX (Energy - should show high risk)..."
python3 cli.py climate-risk CVX
echo ""

echo "=== ALL TESTS COMPLETE ==="
