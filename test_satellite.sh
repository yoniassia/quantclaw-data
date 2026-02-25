#!/bin/bash

echo "=== PHASE 46: Satellite Imagery Proxies Test ==="
echo ""

echo "1. Testing shipping-index..."
python3 cli.py shipping-index | jq -r '.composite_shipping_index.signal' && echo "✓ Shipping index OK" || echo "✗ FAILED"
echo ""

echo "2. Testing construction-activity..."
python3 cli.py construction-activity | jq -r '.construction_activity.signal' && echo "✓ Construction activity OK" || echo "✗ FAILED"
echo ""

echo "3. Testing satellite-proxy WMT..."
python3 cli.py satellite-proxy WMT | jq -r '.ticker' && echo "✓ Satellite proxy OK" || echo "✗ FAILED"
echo ""

echo "4. Testing foot-traffic AAPL..."
python3 cli.py foot-traffic AAPL | jq -r '.keyword' && echo "✓ Foot traffic OK" || echo "✗ FAILED"
echo ""

echo "5. Testing economic-index..."
python3 cli.py economic-index | jq -r '.rating' && echo "✓ Economic index OK" || echo "✗ FAILED"
echo ""

echo "=== API Tests (port 3055) ==="
echo ""

echo "6. Testing API shipping endpoint..."
curl -s "http://localhost:3055/api/v1/satellite?action=shipping" | jq -r '.composite_shipping_index.signal' && echo "✓ API shipping OK" || echo "✗ FAILED"
echo ""

echo "7. Testing API proxy endpoint..."
curl -s "http://localhost:3055/api/v1/satellite?action=proxy&ticker=WMT" | jq -r '.ticker' && echo "✓ API proxy OK" || echo "✗ FAILED"
echo ""

echo "8. Testing API construction endpoint..."
curl -s "http://localhost:3055/api/v1/satellite?action=construction" | jq -r '.construction_activity.signal' && echo "✓ API construction OK" || echo "✗ FAILED"
echo ""

echo "=== All Tests Complete ==="
