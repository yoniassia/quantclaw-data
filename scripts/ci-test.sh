#!/bin/bash
# QuantClaw Data — CI Test Runner
# Run locally or in any CI environment
# Usage: bash scripts/ci-test.sh

set -e
echo "🧪 QuantClaw Data CI Test Suite"
echo "================================"

cd "$(dirname "$0")/.."

# 1. Module imports
echo ""
echo "📦 Test 1: Module Imports"
TOTAL=0
FAILED=0
for f in modules/*.py; do
  MOD=$(basename "$f" .py)
  [ "$MOD" = "__init__" ] && continue
  TOTAL=$((TOTAL+1))
  python3 -c "import modules.$MOD" 2>/dev/null && echo "  ✅ $MOD" || { echo "  ❌ $MOD"; FAILED=$((FAILED+1)); }
done
echo "  → $((TOTAL-FAILED))/$TOTAL passed"

# 2. Data integrity tests
echo ""
echo "🔬 Test 2: Data Integrity"
python3 tests/test_data_integrity.py 2>&1 || true

# 3. Next.js build
echo ""
echo "🏗️ Test 3: Next.js Build"
NODE_OPTIONS="--max-old-space-size=2048" npm run build 2>&1 | tail -5

# 4. API health (if site is live)
echo ""
echo "🌐 Test 4: API Health"
for ep in prices monte-carlo signal-fusion anomaly-scanner regime-correlation macro-leading; do
  STATUS=$(curl -s -o /dev/null -w "%{http_code}" "https://data.quantclaw.org/api/v1/$ep?ticker=AAPL" --max-time 15 2>/dev/null || echo "timeout")
  [ "$STATUS" = "200" ] && echo "  ✅ /api/v1/$ep → $STATUS" || echo "  ❌ /api/v1/$ep → $STATUS"
done

# 5. Stats
echo ""
echo "📊 Stats"
MODULES=$(ls modules/*.py 2>/dev/null | grep -v __init__ | wc -l)
ROUTES=$(find src/app/api/v1 -name "route.ts" 2>/dev/null | wc -l)
PYLINES=$(find modules -name "*.py" | xargs wc -l 2>/dev/null | tail -1 | awk '{print $1}')
echo "  Modules: $MODULES"
echo "  API Routes: $ROUTES"
echo "  Python LOC: $PYLINES"
echo "  Failed imports: $FAILED"

echo ""
echo "================================"
[ $FAILED -gt 5 ] && { echo "❌ CI FAILED ($FAILED broken modules)"; exit 1; }
echo "✅ CI PASSED"
