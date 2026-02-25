#!/bin/bash
# Test script for Order Book Depth Module (Phase 39)

echo "=== QUANTCLAW DATA - Order Book Depth Tests ==="
echo ""

echo "1. Bid-Ask Spread (AAPL):"
python3 cli.py bid-ask AAPL
echo ""

echo "2. Order Book Simulation (TSLA, 5 levels):"
python3 cli.py order-book TSLA --levels 5
echo ""

echo "3. Liquidity Score (SPY):"
python3 cli.py liquidity SPY
echo ""

echo "4. Order Imbalance (NVDA, 5 days):"
python3 cli.py imbalance NVDA --period 5d
echo ""

echo "5. Support/Resistance (AAPL, 6 months):"
python3 cli.py support-resistance AAPL --period 6mo
echo ""

echo "=== All Tests Complete ==="
