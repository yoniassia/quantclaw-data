#!/bin/bash
# Test Monte Carlo module Phase 34

echo "=========================================="
echo "PHASE 34: MONTE CARLO SIMULATION TESTS"
echo "=========================================="
echo ""

echo "Test 1: Monte Carlo GBM simulation"
echo "-----------------------------------"
python3 cli.py monte-carlo AAPL --simulations 100 --days 30 --seed 42 | jq '.ticker, .method, .statistics.expected_return_pct, .tail_risk'
echo ""

echo "Test 2: Monte Carlo Bootstrap simulation"
echo "----------------------------------------"
python3 cli.py monte-carlo TSLA --simulations 100 --days 21 --method bootstrap --seed 42 | jq '.ticker, .method, .statistics.probability_profit'
echo ""

echo "Test 3: VaR/CVaR calculation"
echo "---------------------------"
python3 cli.py var NVDA --confidence 0.95 0.99 --days 252 --simulations 100 | jq '.ticker, .risk_metrics'
echo ""

echo "Test 4: Scenario analysis"
echo "------------------------"
python3 cli.py scenario AAPL --days 90 | jq '.ticker, .scenarios | keys'
echo ""

echo "Test 5: CLI help"
echo "---------------"
python3 cli.py --help 2>&1 | grep -A 3 "Monte Carlo"
echo ""

echo "=========================================="
echo "All tests completed!"
echo "=========================================="
