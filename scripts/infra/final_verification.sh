#!/bin/bash
echo "=================================="
echo "FINAL MIGRATION VERIFICATION"
echo "=================================="
echo ""

echo "1. Checking api_config.py..."
python3 modules/api_config.py > /dev/null 2>&1 && echo "   ✓ api_config.py works" || echo "   ✗ api_config.py FAILED"

echo ""
echo "2. Testing module imports..."
python3 -c "from modules import fed_policy" > /dev/null 2>&1 && echo "   ✓ fed_policy imports" || echo "   ✗ fed_policy FAILED"
python3 -c "from modules import finnhub_ipo_calendar" > /dev/null 2>&1 && echo "   ✓ finnhub_ipo_calendar imports" || echo "   ✗ finnhub_ipo_calendar FAILED"
python3 -c "from modules import eia_energy" > /dev/null 2>&1 && echo "   ✓ eia_energy imports" || echo "   ✗ eia_energy FAILED"
python3 -c "from modules import bls" > /dev/null 2>&1 && echo "   ✓ bls imports" || echo "   ✗ bls FAILED"

echo ""
echo "3. Checking backup directory..."
if [ -d "backups_api_migration/20260304_213922" ]; then
    COUNT=$(ls backups_api_migration/20260304_213922/*.py 2>/dev/null | wc -l)
    echo "   ✓ Backup directory exists ($COUNT files)"
else
    echo "   ✗ Backup directory NOT FOUND"
fi

echo ""
echo "4. Checking key files..."
[ -f "patch_api_keys.py" ] && echo "   ✓ patch_api_keys.py" || echo "   ✗ patch_api_keys.py missing"
[ -f "test_api_keys.py" ] && echo "   ✓ test_api_keys.py" || echo "   ✗ test_api_keys.py missing"
[ -f "modules/api_config.py" ] && echo "   ✓ modules/api_config.py" || echo "   ✗ modules/api_config.py missing"
[ -f "api_migration.log" ] && echo "   ✓ api_migration.log" || echo "   ✗ api_migration.log missing"
[ -f "API_MIGRATION_COMPLETE.md" ] && echo "   ✓ API_MIGRATION_COMPLETE.md" || echo "   ✗ API_MIGRATION_COMPLETE.md missing"

echo ""
echo "5. Testing API key loading..."
python3 << 'PYEOF'
import sys
sys.path.insert(0, 'modules')
from api_config import is_configured, list_configured_services

configured = list_configured_services()
print(f"   ✓ {len(configured)} API services configured")
PYEOF

echo ""
echo "=================================="
echo "VERIFICATION COMPLETE"
echo "=================================="
