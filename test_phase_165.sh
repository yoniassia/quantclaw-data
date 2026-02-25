#!/bin/bash
# Test script for Phase 165: Bond New Issue Calendar

echo "=========================================="
echo "Phase 165: Bond New Issue Calendar"
echo "Testing CLI commands"
echo "=========================================="
echo ""

echo "1. Testing bond-upcoming (30 days)..."
python3 cli.py bond-upcoming 30 | head -20
echo ""

echo "2. Testing bond-company (Apple Inc.)..."
python3 cli.py bond-company 0000320193 5
echo ""

echo "3. Testing bond-issuer (JPMorgan Chase, 1 year)..."
python3 cli.py bond-issuer 0000019617 1 | head -30
echo ""

echo "4. Testing bond-dashboard..."
python3 cli.py bond-dashboard | head -40
echo ""

echo "=========================================="
echo "Phase 165: All tests completed!"
echo "=========================================="
