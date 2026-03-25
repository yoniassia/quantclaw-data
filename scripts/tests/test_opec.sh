#!/bin/bash
# Test script for OPEC Production Monitor (Phase 175)

set -e

echo "Testing OPEC Production Monitor CLI commands..."
echo ""

echo "1. Testing opec-monitor..."
python3 cli.py opec-monitor | head -20
echo "✅ opec-monitor passed"
echo ""

echo "2. Testing opec-summary..."
python3 cli.py opec-summary
echo "✅ opec-summary passed"
echo ""

echo "3. Testing opec-country..."
python3 cli.py opec-country "Saudi Arabia"
echo "✅ opec-country passed"
echo ""

echo "4. Testing opec-compliance..."
python3 cli.py opec-compliance | head -20
echo "✅ opec-compliance passed"
echo ""

echo "5. Testing opec-quota-history..."
python3 cli.py opec-quota-history
echo "✅ opec-quota-history passed"
echo ""

echo "6. Testing opec-dashboard..."
python3 cli.py opec-dashboard | head -40
echo "✅ opec-dashboard passed"
echo ""

echo "✅ All OPEC CLI tests passed!"
echo ""

# Test MCP server imports
echo "7. Testing MCP server imports..."
python3 -c "from opec import get_opec_production_latest, get_opec_summary, get_country_production, get_compliance_report, get_quota_changes; print('✅ All imports successful')"
echo ""

echo "✅✅✅ Phase 175 Complete! ✅✅✅"
