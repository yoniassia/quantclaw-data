#!/bin/bash
echo "=== QUANTCLAW DATA — Phase 43: Crypto On-Chain Analytics Test Suite ==="
echo ""

echo "1. Testing: onchain ETH"
python3 cli.py onchain ETH 2>&1 | head -10
echo ""

echo "2. Testing: whale-watch BTC"
python3 cli.py whale-watch BTC 2>&1 | head -10
echo ""

echo "3. Testing: dex-volume"
python3 cli.py dex-volume 2>&1 | head -15
echo ""

echo "4. Testing: gas-fees"
python3 cli.py gas-fees 2>&1 | head -10
echo ""

echo "5. Testing: whale-watch ETH"
python3 cli.py whale-watch ETH 2>&1 | head -10
echo ""

echo "=== ALL TESTS COMPLETE ==="
