#!/bin/bash
echo "=== Testing Share Buyback Analysis Module ==="
echo ""
echo "1. Testing buyback-yield for GOOGL..."
python3 cli.py buyback-yield GOOGL | python3 -m json.tool | head -15
echo ""
echo "2. Testing share-count-trend for MSFT..."
python3 cli.py share-count-trend MSFT | python3 -m json.tool | head -20
echo ""
echo "3. Testing dilution-impact for META..."
python3 cli.py dilution-impact META | python3 -m json.tool
echo ""
echo "4. Testing full buyback-analysis for AAPL (summary only)..."
python3 cli.py buyback-analysis AAPL 2>&1 | python3 -c "import json, sys; d=json.load(sys.stdin); print(json.dumps(d['summary'], indent=2))"
echo ""
echo "=== All tests completed successfully! ==="
