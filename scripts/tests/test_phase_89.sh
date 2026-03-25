#!/bin/bash
# Test Phase 89: Volatility Surface Modeling

echo "=== PHASE 89: Volatility Surface Modeling Tests ==="
echo ""

echo "Test 1: IV Smile Analysis (AAPL)"
python3 cli.py iv-smile AAPL --json | jq -r '.ticker, .smile_type, .skew, .interpretation' | head -10
echo ""

echo "Test 2: Volatility Arbitrage Scanner (TSLA)"
python3 cli.py vol-arbitrage TSLA --json | jq -r '.ticker, .opportunities_found' | head -5
echo ""

echo "Test 3: Straddle Scanner (SPY)"
python3 cli.py straddle-scan SPY --max-days 45 --json | jq -r '.ticker, .strategies_analyzed, .top_strategies[0].attractiveness_score' | head -5
echo ""

echo "Test 4: Direct Module Test (NVDA)"
python3 modules/volatility_surface.py iv-smile NVDA --json | jq -r '.ticker, .atm_iv, .smile_type' | head -5
echo ""

echo "=== All Phase 89 Tests Complete ==="
