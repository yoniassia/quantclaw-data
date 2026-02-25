#!/bin/bash
# Test script for Phase 58: Institutional Ownership

set -e

echo "=== PHASE 58: INSTITUTIONAL OWNERSHIP TEST ==="
echo

echo "1. Testing top-holders command (Yahoo Finance data)..."
python3 cli.py top-holders AAPL --limit 10
echo

echo "2. Testing whale-accumulation command (trend analysis)..."
python3 cli.py whale-accumulation TSLA
echo

echo "3. Testing smart-money command (famous investors)..."
python3 cli.py smart-money GOOGL
echo

echo "4. Testing 13f-changes command (institutional flow)..."
python3 cli.py 13f-changes MSFT
echo

echo "=== ALL TESTS PASSED ==="
