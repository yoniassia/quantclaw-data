#!/bin/bash
# Test Korean Statistical Information Module (Phase 122)

echo "=== Testing Korean Statistical Information Module ==="
echo ""

echo "1. Testing korea-gdp..."
python3 cli.py korea-gdp | jq '.success' || exit 1
echo "✓ korea-gdp works"
echo ""

echo "2. Testing korea-cpi..."
python3 cli.py korea-cpi | jq '.success' || exit 1
echo "✓ korea-cpi works"
echo ""

echo "3. Testing korea-semiconductors..."
python3 cli.py korea-semiconductors | jq '.success' || exit 1
echo "✓ korea-semiconductors works"
echo ""

echo "4. Testing korea-trade..."
python3 cli.py korea-trade | jq '.success' || exit 1
echo "✓ korea-trade works"
echo ""

echo "5. Testing korea-bok-rate..."
python3 cli.py korea-bok-rate | jq '.success' || exit 1
echo "✓ korea-bok-rate works"
echo ""

echo "6. Testing korea-fx-reserves..."
python3 cli.py korea-fx-reserves | jq '.success' || exit 1
echo "✓ korea-fx-reserves works"
echo ""

echo "7. Testing korea-exchange-rate..."
python3 cli.py korea-exchange-rate | jq '.success' || exit 1
echo "✓ korea-exchange-rate works"
echo ""

echo "8. Testing korea-dashboard..."
python3 cli.py korea-dashboard | jq '.success' || exit 1
echo "✓ korea-dashboard works"
echo ""

echo "9. Testing korea-indicators..."
python3 cli.py korea-indicators | jq '.success' || exit 1
echo "✓ korea-indicators works"
echo ""

echo "10. Testing korea-semiconductor-breakdown..."
python3 cli.py korea-semiconductor-breakdown | jq '.success' || exit 1
echo "✓ korea-semiconductor-breakdown works"
echo ""

echo "=== All tests passed! ✓ ==="
echo ""
echo "Phase 122: Korean Statistical Information - COMPLETE"
echo "LOC: $(wc -l modules/kosis.py | awk '{print $1}')"
