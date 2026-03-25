#!/bin/bash
# Phase 75 — Transaction Cost Analysis — Final Verification Test

echo "=== Phase 75: Transaction Cost Analysis — Verification ==="
echo ""

PASS=0
FAIL=0

# Test 1: Bid-Ask Spread
echo "Test 1: Bid-Ask Spread Analysis"
RESULT=$(python3 cli.py tca-spread AAPL 2>&1)
if echo "$RESULT" | grep -q '"ticker": "AAPL"'; then
    echo "✓ PASS: Bid-ask spread working"
    ((PASS++))
else
    echo "✗ FAIL: Bid-ask spread failed"
    ((FAIL++))
fi

# Test 2: Market Impact
echo "Test 2: Market Impact Estimation"
RESULT=$(python3 cli.py tca-impact AAPL --trade-size 5000000 2>&1)
if echo "$RESULT" | grep -q '"market_impact"'; then
    echo "✓ PASS: Market impact estimation working"
    ((PASS++))
else
    echo "✗ FAIL: Market impact estimation failed"
    ((FAIL++))
fi

# Test 3: Strategy Comparison
echo "Test 3: Execution Strategy Comparison"
RESULT=$(python3 cli.py tca-compare AAPL --trade-size 10000000 2>&1)
if echo "$RESULT" | grep -q '"recommended_strategy"'; then
    echo "✓ PASS: Strategy comparison working"
    ((PASS++))
else
    echo "✗ FAIL: Strategy comparison failed"
    ((FAIL++))
fi

# Test 4: Execution Optimization
echo "Test 4: Execution Schedule Optimization"
RESULT=$(python3 cli.py tca-optimize AAPL --total-shares 50000 --window 240 --strategy vwap 2>&1)
if echo "$RESULT" | grep -q '"schedule"'; then
    echo "✓ PASS: Execution optimization working"
    ((PASS++))
else
    echo "✗ FAIL: Execution optimization failed"
    ((FAIL++))
fi

# Test 5: Implementation Shortfall
echo "Test 5: Implementation Shortfall"
RESULT=$(python3 cli.py tca-shortfall AAPL --decision-price 270.00 --exec-prices 270.10 270.15 270.25 --exec-sizes 1000 1500 2000 --side buy 2>&1)
if echo "$RESULT" | grep -q '"implementation_shortfall"'; then
    echo "✓ PASS: Implementation shortfall working"
    ((PASS++))
else
    echo "✗ FAIL: Implementation shortfall failed"
    ((FAIL++))
fi

# Test 6: Module file exists
echo "Test 6: Module file verification"
if [ -f "modules/transaction_cost.py" ]; then
    LOC=$(wc -l < modules/transaction_cost.py)
    echo "✓ PASS: Module exists ($LOC lines)"
    ((PASS++))
else
    echo "✗ FAIL: Module file not found"
    ((FAIL++))
fi

# Test 7: API route exists
echo "Test 7: API route verification"
if [ -f "src/app/api/v1/tca/route.ts" ]; then
    echo "✓ PASS: API route exists"
    ((PASS++))
else
    echo "✗ FAIL: API route not found"
    ((FAIL++))
fi

# Test 8: Roadmap updated
echo "Test 8: Roadmap status check"
if grep -q 'id: 75.*status: "done".*loc: 610' src/app/roadmap.ts; then
    echo "✓ PASS: Roadmap updated with Phase 75 completion"
    ((PASS++))
else
    echo "✗ FAIL: Roadmap not updated correctly"
    ((FAIL++))
fi

# Test 9: Services registered
echo "Test 9: Services registration check"
if grep -q 'tca_spread.*phase: 75' src/app/services.ts; then
    echo "✓ PASS: Services registered in services.ts"
    ((PASS++))
else
    echo "✗ FAIL: Services not registered"
    ((FAIL++))
fi

# Summary
echo ""
echo "=== Summary ==="
echo "PASSED: $PASS/9"
echo "FAILED: $FAIL/9"
echo ""

if [ $FAIL -eq 0 ]; then
    echo "✅ Phase 75 — Transaction Cost Analysis — COMPLETE"
    exit 0
else
    echo "❌ Phase 75 — Some tests failed"
    exit 1
fi
